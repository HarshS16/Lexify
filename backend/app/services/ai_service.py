import json
import asyncio
import logging
from typing import Optional
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

# ── Models to race (verified working free models on OpenRouter) ──
RACE_MODELS = [
    "arcee-ai/trinity-large-preview:free",
    "arcee-ai/trinity-mini:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-4b-it:free",
    "google/gemma-3n-e4b-it:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "stepfun/step-3.5-flash:free",
    "z-ai/glm-4.5-air:free",
]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


class AIService:
    """OpenRouter-based AI service with parallel model racing."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://betterwordfor.app",
            "X-Title": "Better Word For",
        }

    def _parse_json_response(self, text: str) -> dict:
        """Extract JSON from LLM response, handling markdown blocks and trailing text."""
        if not text:
            raise ValueError("AI returned an empty response")
        
        cleaned = text.strip()
        
        # 1. Try to find content within markdown code blocks first
        if "```" in cleaned:
            parts = cleaned.split("```")
            for i in range(1, len(parts), 2):
                inner = parts[i].strip()
                if inner.lower().startswith("json"):
                    inner = inner[4:].strip()
                try:
                    return json.loads(inner)
                except json.JSONDecodeError as e:
                    # If it's 'extra data', try to fix it by finding the last '}'
                    if "extra data" in str(e).lower():
                        end_idx = inner.rfind("}") + 1
                        try:
                            return json.loads(inner[:end_idx])
                        except:
                            continue
                    continue

        # 2. Try parsing the whole string directly
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # 3. Handle 'extra data' (AI talked after the JSON)
            if "extra data" in str(e).lower():
                end_idx = cleaned.rfind("}") + 1
                try:
                    return json.loads(cleaned[:end_idx])
                except:
                    pass

            # 4. Last resort: Extract everything between the first '{' and last '}'
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(cleaned[start:end])
                except json.JSONDecodeError:
                    pass
            
            # If everything fails, log the raw text to help us debug
            logger.error(f"Failed to parse AI response: {text[:500]}...")
            raise

    async def _call_model(self, model: str, system_prompt: str, user_prompt: str) -> str:
        """Call a single model via OpenRouter."""
        # Combine system + user into one message for maximum model compatibility
        combined_prompt = f"""### Instructions ###
{system_prompt}

### User Input ###
{user_prompt}"""

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                OPENROUTER_BASE_URL,
                headers=self.headers,
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": combined_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2048,
                },
            )

            if response.status_code != 200:
                error_text = response.text[:200]
                raise Exception(f"Model {model} returned {response.status_code}: {error_text}")

            data = response.json()

            if "error" in data:
                raise Exception(f"Model {model} error: {data['error'].get('message', str(data['error']))}")

            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if not content:
                raise Exception(f"Model {model} returned empty content")
            logger.info(f"✅ Model {model} responded successfully")
            return content

    async def _generate(self, system_prompt: str, user_prompt: str) -> str:
        """Race multiple models in parallel — first successful response wins."""

        async def try_model(model: str) -> str:
            try:
                return await self._call_model(model, system_prompt, user_prompt)
            except Exception as e:
                logger.warning(f"❌ Model {model} failed: {e}")
                raise

        # Create tasks for all models
        tasks = [asyncio.create_task(try_model(m)) for m in RACE_MODELS]

        # Wait for the first successful result
        done = set()
        pending = set(tasks)
        last_error = None

        while pending:
            finished, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            for task in finished:
                try:
                    result = task.result()
                    # Cancel remaining tasks
                    for p in pending:
                        p.cancel()
                    return result
                except Exception as e:
                    last_error = e
                    continue

        # All models failed
        logger.error(f"All models failed. Last error: {last_error}")
        raise HTTPException(
            status_code=503,
            detail=f"All AI models failed. Last error: {str(last_error)[:200]}"
        )

    # ── Step 1: Context and Emotion Detection ──────────────

    async def analyze_emotion(
        self, user_input: str, tone: str = "neutral", intent: str = "general expression"
    ) -> EmotionAnalysis:
        system_prompt = """You are a linguistic analysis engine.
Analyze the user input to extract emotional and contextual intent.
Do not generate words.
Respond strictly in valid JSON with these keys:
- primary_emotion (string)
- secondary_emotion (string or null)
- intensity (one of: "low", "medium", "high")
- context_summary (string, 1-2 sentences)"""

        user_prompt = f"""Input: "{user_input}"
Tone preference: "{tone}"
Intent: "{intent}"

Return ONLY valid JSON, no other text."""

        raw = await self._generate(system_prompt, user_prompt)
        data = self._parse_json_response(raw)
        return EmotionAnalysis(**data)

    # ── Step 2: Word Generation ────────────────────────────

    async def generate_words(self, analysis: EmotionAnalysis) -> dict:
        system_prompt = """You are an expert lexicographer and writer.
Generate emotionally precise words based on the analysis.
Avoid generic synonyms. Prioritize nuanced, contextually accurate words.
Rank words by contextual accuracy.
Respond strictly in valid JSON with these keys:
- best_fit (string: the single best word)
- alternatives (array of objects with keys: word, strength)
  - strength is one of: "low", "medium", "high"
Generate 5 to 10 alternatives."""

        user_prompt = f"""Emotional analysis:
{json.dumps(analysis.model_dump(), indent=2)}

Generate:
- One best-fit word
- 5-10 alternative words ranked by contextual accuracy

Return ONLY valid JSON, no other text."""

        raw = await self._generate(system_prompt, user_prompt)
        return self._parse_json_response(raw)

    # ── Step 3: Explanation and Categorization ─────────────

    async def explain_words(self, words_data: dict, context_summary: str) -> list:
        word_list = [words_data["best_fit"]] + [
            alt["word"] for alt in words_data.get("alternatives", [])
        ]

        system_prompt = """Explain word choices clearly and concisely.
Categorize each word into one or more of: emotional, professional, creative, formal, informal.
Avoid dictionary-style definitions. Focus on emotional nuance and when to use each word.
Respond strictly in valid JSON: an array of objects with keys:
- word (string)
- categories (array of strings)
- explanation (string, 1-2 sentences)"""

        user_prompt = f"""Words: {json.dumps(word_list)}

Context: {context_summary}

Return ONLY valid JSON array, no other text."""

        raw = await self._generate(system_prompt, user_prompt)
        return self._parse_json_response(raw)

    # ── Full Pipeline ──────────────────────────────────────

    async def find_better_words(
        self, user_input: str, tone: str = "neutral", intent: str = "general expression"
    ) -> WordSuggestionResult:
        """Execute the full 3-step prompt-chained workflow."""

        # Step 1: Analyze emotion
        analysis = await self.analyze_emotion(user_input, tone, intent)

        # Step 2: Generate words
        words_data = await self.generate_words(analysis)

        # Normalize alternatives (AI might return strings instead of dicts)
        raw_alts = words_data.get("alternatives", [])
        normalized_alts = []
        for alt in raw_alts:
            if isinstance(alt, str):
                normalized_alts.append({"word": alt, "strength": "medium"})
            elif isinstance(alt, dict):
                normalized_alts.append(alt)
        words_data["alternatives"] = normalized_alts

        # Step 3: Explain and categorize
        explanations = await self.explain_words(words_data, analysis.context_summary)

        # Normalize explanations (AI might return strings instead of dicts)
        explanation_map = {}
        if isinstance(explanations, list):
            for e in explanations:
                if isinstance(e, dict) and "word" in e:
                    explanation_map[e["word"]] = e
                elif isinstance(e, str):
                    explanation_map[e] = {"word": e, "categories": [], "explanation": ""}

        # Build best_fit info
        best_fit_info = explanation_map.get(words_data["best_fit"], {})

        # Build alternatives with explanations
        alternatives = []
        for alt in words_data.get("alternatives", []):
            word = alt.get("word", "") if isinstance(alt, dict) else str(alt)
            exp = explanation_map.get(word, {})
            alternatives.append(
                WordAlternative(
                    word=word,
                    strength=alt.get("strength", "medium") if isinstance(alt, dict) else "medium",
                    categories=exp.get("categories", []),
                    explanation=exp.get("explanation", ""),
                )
            )

        return WordSuggestionResult(
            best_fit=words_data["best_fit"],
            best_fit_explanation=best_fit_info.get("explanation", ""),
            best_fit_categories=best_fit_info.get("categories", []),
            alternatives=alternatives,
            analysis=analysis,
        )

    # ── Rewrite Mode ───────────────────────────────────────

    async def rewrite_sentence(
        self, input_text: str, goal: str, tone: str = "neutral"
    ) -> RewriteResult:
        system_prompt = """You are an expert writing coach.
Rewrite the sentence to match the user's goal.
Highlight every word change with a reason.
Respond strictly in valid JSON with keys:
- original (string)
- rewritten (string)
- changes (array of objects: {original_word, new_word, reason})"""

        user_prompt = f"""Sentence: "{input_text}"
Goal: "{goal}"
Tone: "{tone}"

Return ONLY valid JSON, no other text."""

        raw = await self._generate(system_prompt, user_prompt)
        data = self._parse_json_response(raw)
        data["goal"] = goal
        return RewriteResult(**data)

    # ── Word of the Day ────────────────────────────────────

    async def generate_word_of_the_day(self) -> WordOfTheDayResponse:
        system_prompt = """You are an AI vocabulary curator.
Generate one interesting, nuanced word that most people don't use enough.
Do not pick common words. Pick words that are expressive, emotionally rich, or beautifully specific.
Respond strictly in valid JSON with keys:
- word (string)
- meaning (string, 1-2 sentences, not dictionary-style)
- emotional_range (string, what emotions this word can express)
- example_usage (string, a natural sentence using the word)
- when_to_use (string, 1 sentence)
- when_to_avoid (string, 1 sentence)"""

        user_prompt = "Generate today's Word of the Day. Return ONLY valid JSON, no other text."

        raw = await self._generate(system_prompt, user_prompt)
        data = self._parse_json_response(raw)
        data["date"] = date.today()
        return WordOfTheDayResponse(**data)


# Singleton
ai_service = AIService() if settings.OPENROUTER_API_KEY else None


def get_ai_service() -> AIService:
    if ai_service is None:
        raise RuntimeError("OPENROUTER_API_KEY not configured. Set it in .env file.")
    return ai_service
