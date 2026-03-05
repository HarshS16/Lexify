import json
import asyncio
import logging
import time
from typing import Optional
from collections import OrderedDict
import httpx
from fastapi import HTTPException
from app.core.config import get_settings
from app.models.schemas import (
    EmotionAnalysis,
    WordAlternative,
    WordSuggestionResult,
    RewriteResult,
    WordOfTheDayResponse,
)
from datetime import date

logger = logging.getLogger(__name__)
settings = get_settings()

# Ordered by typical response speed (fastest first)
RACE_MODELS = [
    "google/gemma-3-4b-it:free",
    "google/gemma-3n-e4b-it:free",
    "arcee-ai/trinity-mini:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "stepfun/step-3.5-flash:free",
    "z-ai/glm-4.5-air:free",
    "arcee-ai/trinity-large-preview:free",
    "google/gemma-3-12b-it:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


# ── Simple TTL Cache ──
class TTLCache:
    """In-memory cache with TTL expiry. Max 200 entries."""

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 200):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: OrderedDict[str, tuple[float, object]] = OrderedDict()

    def get(self, key: str):
        if key in self._cache:
            ts, value = self._cache[key]
            if time.time() - ts < self.ttl:
                self._cache.move_to_end(key)
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: object):
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        self._cache[key] = (time.time(), value)


class AIService:
    """OpenRouter AI service — single-call pipeline with parallel model racing."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://lexify.harshjsx.dev",
            "X-Title": "Lexify",
        }
        # Persistent HTTP client — 20s timeout (drop slow models fast)
        self._client = httpx.AsyncClient(timeout=20.0, headers=self.headers)
        # Cache for repeated queries
        self._cache = TTLCache(ttl_seconds=3600)

    def _parse_json_response(self, text: str) -> dict:
        """Extract JSON from LLM response, handling markdown blocks, trailing text,
        and truncated / malformed output from the model."""
        if not text:
            raise ValueError("AI returned an empty response")

        cleaned = text.strip()

        # 1. Try markdown code blocks
        if "```" in cleaned:
            parts = cleaned.split("```")
            for i in range(1, len(parts), 2):
                inner = parts[i].strip()
                if inner.lower().startswith("json"):
                    inner = inner[4:].strip()
                result = self._try_parse(inner)
                if result is not None:
                    return result

        # 2. Direct parse
        result = self._try_parse(cleaned)
        if result is not None:
            return result

        # 3. Extract first JSON object between { ... }
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            result = self._try_parse(cleaned[start:end])
            if result is not None:
                return result

        # 4. Try array
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start != -1 and end > start:
            result = self._try_parse(cleaned[start:end])
            if result is not None:
                return result

        logger.error(f"JSON parse failed. Raw response: {text[:500]}")
        raise ValueError(f"Could not parse AI response as JSON: {text[:200]}")

    @staticmethod
    def _try_parse(text: str) -> dict | None:
        """Try multiple strategies to get valid JSON from potentially malformed text."""
        # Strategy 1: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: raw_decode — extracts just the first complete JSON value,
        # ignoring any trailing text that causes "Extra data" errors
        try:
            decoder = json.JSONDecoder()
            # Find the first { or [ to start decoding from
            for i, ch in enumerate(text):
                if ch in "{[":
                    obj, _ = decoder.raw_decode(text, i)
                    if isinstance(obj, (dict, list)):
                        return obj
        except json.JSONDecodeError:
            pass

        # Strategy 3: Repair truncated JSON (model cut off mid-string)
        # Close any unterminated strings and braces/brackets
        repaired = text.rstrip()
        # If ending mid-string, close the string
        quote_count = repaired.count('"') - repaired.count('\\"')
        if quote_count % 2 == 1:
            repaired += '"'

        # Count open braces/brackets and close them
        open_braces = repaired.count("{") - repaired.count("}")
        open_brackets = repaired.count("[") - repaired.count("]")
        repaired += "]" * max(0, open_brackets)
        repaired += "}" * max(0, open_braces)

        try:
            decoder = json.JSONDecoder()
            for i, ch in enumerate(repaired):
                if ch in "{[":
                    obj, _ = decoder.raw_decode(repaired, i)
                    if isinstance(obj, (dict, list)):
                        return obj
        except json.JSONDecodeError:
            pass

        return None

    async def _call_model(self, model: str, prompt: str) -> str:
        """Call a single model via OpenRouter using the persistent client."""
        response = await self._client.post(
            OPENROUTER_BASE_URL,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1800,
            },
        )

        if response.status_code != 200:
            raise Exception(f"{model}: HTTP {response.status_code}")

        data = response.json()
        if "error" in data:
            msg = data["error"].get("message", str(data["error"]))
            raise Exception(f"{model}: {msg}")

        content = data.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            raise Exception(f"{model}: empty response")

        logger.info(f"✅ {model} responded")
        return content

    async def _generate(self, prompt: str) -> str:
        """Race multiple models in parallel — first successful response wins."""

        async def try_model(model: str) -> str:
            try:
                return await self._call_model(model, prompt)
            except Exception as e:
                logger.warning(f"❌ {model}: {e}")
                raise

        tasks = [asyncio.create_task(try_model(m)) for m in RACE_MODELS]
        pending = set(tasks)
        last_error = None

        while pending:
            finished, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            for task in finished:
                try:
                    result = task.result()
                    for p in pending:
                        p.cancel()
                    return result
                except Exception as e:
                    last_error = e
                    continue

        raise HTTPException(
            status_code=503,
            detail="All AI models are currently unavailable. Please try again in a moment."
        )

    # ── Single-Call Word Search Pipeline ──────────────────

    async def find_better_words(
        self, user_input: str, tone: str = "neutral", intent: str = "general expression"
    ) -> WordSuggestionResult:
        """Single AI call that returns emotion analysis + words + explanations."""

        # Check cache first
        cache_key = f"search:{user_input}:{tone}:{intent}"
        cached = self._cache.get(cache_key)
        if cached:
            logger.info("📦 Cache hit")
            return cached

        prompt = f"""Expert linguist. Find better words for the input below.

Input: "{user_input}"
Tone: {tone}
Intent: {intent}

Return ONLY this JSON:
{{
  "analysis": {{
    "primary_emotion": "main emotion",
    "secondary_emotion": "secondary or null",
    "intensity": "low|medium|high",
    "context_summary": "1 sentence"
  }},
  "best_fit": "best word",
  "best_fit_explanation": "why (1-2 sentences)",
  "best_fit_example_sentence": "a natural example sentence using the best fit word",
  "best_fit_categories": ["emotional"|"professional"|"creative"|"formal"|"informal"],
  "alternatives": [
    {{"word": "word", "strength": "low|medium|high", "categories": [], "explanation": "1 sentence", "example_sentence": "a natural example sentence using this word"}}
  ]
}}

5-8 alternatives. Emotionally precise, not generic synonyms. Each example_sentence must be a natural, realistic sentence demonstrating how the word is used. ONLY valid JSON."""

        raw = await self._generate(prompt)
        data = self._parse_json_response(raw)

        # Normalize analysis
        analysis_data = data.get("analysis", {})
        analysis = EmotionAnalysis(
            primary_emotion=analysis_data.get("primary_emotion", "neutral"),
            secondary_emotion=analysis_data.get("secondary_emotion"),
            intensity=analysis_data.get("intensity", "medium"),
            context_summary=analysis_data.get("context_summary", ""),
        )

        # Normalize alternatives
        raw_alts = data.get("alternatives", [])
        best_fit_word = data.get("best_fit", "").lower().strip()
        seen_words: set[str] = set()
        if best_fit_word:
            seen_words.add(best_fit_word)

        alternatives = []
        for alt in raw_alts:
            if isinstance(alt, str):
                key = alt.lower().strip()
                if key and key not in seen_words:
                    seen_words.add(key)
                    alternatives.append(WordAlternative(
                        word=alt, strength="medium", categories=[], explanation=""
                    ))
            elif isinstance(alt, dict):
                key = alt.get("word", "").lower().strip()
                if key and key not in seen_words:
                    seen_words.add(key)
                    alternatives.append(WordAlternative(
                        word=alt.get("word", ""),
                        strength=alt.get("strength", "medium"),
                        categories=alt.get("categories", []),
                        explanation=alt.get("explanation", ""),
                        example_sentence=alt.get("example_sentence", ""),
                    ))

        result = WordSuggestionResult(
            best_fit=data.get("best_fit", ""),
            best_fit_explanation=data.get("best_fit_explanation", ""),
            best_fit_example_sentence=data.get("best_fit_example_sentence", ""),
            best_fit_categories=data.get("best_fit_categories", []),
            alternatives=alternatives,
            analysis=analysis,
        )

        # Cache the result
        self._cache.set(cache_key, result)
        return result

    # ── Rewrite Mode ───────────────────────────────────────

    async def rewrite_sentence(
        self, input_text: str, goal: str, tone: str = "neutral"
    ) -> RewriteResult:

        cache_key = f"rewrite:{input_text}:{goal}:{tone}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        prompt = f"""Expert writing coach. Rewrite the sentence to match the goal. List every word change with a reason.

Sentence: "{input_text}"
Goal: {goal}
Tone: {tone}

Return ONLY this JSON:
{{
  "original": "original sentence",
  "rewritten": "rewritten sentence",
  "changes": [
    {{"original_word": "old", "new_word": "new", "reason": "why"}}
  ]
}}

ONLY valid JSON."""

        raw = await self._generate(prompt)
        data = self._parse_json_response(raw)
        data["goal"] = goal
        result = RewriteResult(**data)

        self._cache.set(cache_key, result)
        return result

    # ── Word of the Day ────────────────────────────────────

    async def generate_word_of_the_day(self) -> WordOfTheDayResponse:

        cache_key = f"wotd:{date.today()}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        prompt = """Vocabulary curator. Pick one interesting, nuanced, underused word.

Return ONLY this JSON:
{
  "word": "the word",
  "meaning": "1-2 sentences",
  "emotional_range": "what emotions it expresses",
  "example_usage": "natural sentence",
  "when_to_use": "1 sentence",
  "when_to_avoid": "1 sentence"
}

ONLY valid JSON."""

        raw = await self._generate(prompt)
        data = self._parse_json_response(raw)
        data["date"] = date.today()
        result = WordOfTheDayResponse(**data)

        self._cache.set(cache_key, result)
        return result


# Singleton
ai_service = AIService() if settings.OPENROUTER_API_KEY else None


def get_ai_service() -> AIService:
    if ai_service is None:
        raise HTTPException(
            status_code=503,
            detail="AI service not configured. Set OPENROUTER_API_KEY in environment."
        )
    return ai_service
