from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


# ── Input Schemas ──────────────────────────────────────────

class SearchRequest(BaseModel):
    input_text: str = Field(..., min_length=1, max_length=1000)
    tone: Optional[str] = "neutral"
    intent: Optional[str] = "general expression"


class RewriteRequest(BaseModel):
    input_text: str = Field(..., min_length=1, max_length=2000)
    goal: str = Field(..., description="e.g. more confident, more polite, more professional")
    tone: Optional[str] = "neutral"


class SaveWordRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)
    notes: Optional[str] = None
    tags: Optional[List[str]] = []


class FeedbackRequest(BaseModel):
    search_id: Optional[UUID] = None
    word: str
    rating: int = Field(..., ge=-1, le=1)  # -1 dislike, 0 neutral, 1 like


# ── AI Output Schemas ──────────────────────────────────────

class EmotionAnalysis(BaseModel):
    primary_emotion: str
    secondary_emotion: Optional[str] = None
    intensity: str  # low / medium / high
    context_summary: str


class WordAlternative(BaseModel):
    word: str
    strength: str  # low / medium / high
    categories: Optional[List[str]] = []
    explanation: Optional[str] = None
    example_sentence: Optional[str] = None


class WordSuggestionResult(BaseModel):
    best_fit: str
    best_fit_explanation: Optional[str] = None
    best_fit_example_sentence: Optional[str] = None
    best_fit_categories: Optional[List[str]] = []
    alternatives: List[WordAlternative]
    analysis: EmotionAnalysis


class RewriteResult(BaseModel):
    original: str
    rewritten: str
    changes: List[dict]  # [{original_word, new_word, reason}]
    goal: str


class WordOfTheDayResponse(BaseModel):
    date: date
    word: str
    meaning: Optional[str] = None
    emotional_range: Optional[str] = None
    example_usage: Optional[str] = None
    when_to_use: Optional[str] = None
    when_to_avoid: Optional[str] = None


# ── Response Schemas ───────────────────────────────────────

class SearchResponse(BaseModel):
    search_id: UUID
    result: WordSuggestionResult


class SavedWordResponse(BaseModel):
    id: UUID
    word: str
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    created_at: datetime


class HistoryItem(BaseModel):
    search_id: UUID
    input_text: str
    tone: Optional[str]
    intent: Optional[str]
    best_fit_word: Optional[str]
    created_at: datetime


class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int
