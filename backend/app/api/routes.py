import uuid
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.core.database import get_db
from app.models.models import Search, WordResult, SavedWord, WordOfTheDay, Feedback
from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    RewriteRequest,
    RewriteResult,
    SaveWordRequest,
    SavedWordResponse,
    FeedbackRequest,
    HistoryItem,
    HistoryResponse,
    WordOfTheDayResponse,
)
from app.services.ai_service import get_ai_service, AIService

router = APIRouter()


# ── Word Search ────────────────────────────────────────────

@router.post("/search", response_model=SearchResponse)
async def search_words(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Main endpoint: find better words for user input."""
    ai = get_ai_service()

    # Run AI pipeline
    result = await ai.find_better_words(
        user_input=request.input_text,
        tone=request.tone or "neutral",
        intent=request.intent or "general expression",
    )

    # Store search in DB
    search = Search(
        id=uuid.uuid4(),
        input_text=request.input_text,
        tone=request.tone,
        intent=request.intent,
        analysis_json=result.analysis.model_dump(),
    )
    db.add(search)

    # Store word result
    word_result = WordResult(
        id=uuid.uuid4(),
        search_id=search.id,
        best_fit_word=result.best_fit,
        alternatives_json=[alt.model_dump() for alt in result.alternatives],
        explanations_json={
            "best_fit_explanation": result.best_fit_explanation,
            "best_fit_categories": result.best_fit_categories,
        },
    )
    db.add(word_result)
    await db.flush()

    return SearchResponse(search_id=search.id, result=result)


# ── Rewrite Mode ───────────────────────────────────────────

@router.post("/rewrite", response_model=RewriteResult)
async def rewrite_sentence(request: RewriteRequest):
    """Rewrite a sentence with a specific goal."""
    ai = get_ai_service()
    return await ai.rewrite_sentence(
        input_text=request.input_text,
        goal=request.goal,
        tone=request.tone or "neutral",
    )


# ── Word of the Day ───────────────────────────────────────

@router.get("/word-of-the-day", response_model=WordOfTheDayResponse)
async def get_word_of_the_day(db: AsyncSession = Depends(get_db)):
    """Get today's Word of the Day (cached in DB for 24h)."""
    today = date.today()

    # Check if we already have today's word
    stmt = select(WordOfTheDay).where(WordOfTheDay.date == today)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        return WordOfTheDayResponse(
            date=existing.date,
            word=existing.word,
            **(existing.data_json or {}),
        )

    # Generate new word
    ai = get_ai_service()
    wotd = await ai.generate_word_of_the_day()

    # Store in DB
    db_wotd = WordOfTheDay(
        date=today,
        word=wotd.word,
        data_json={
            "meaning": wotd.meaning,
            "emotional_range": wotd.emotional_range,
            "example_usage": wotd.example_usage,
            "when_to_use": wotd.when_to_use,
            "when_to_avoid": wotd.when_to_avoid,
        },
    )
    db.add(db_wotd)
    await db.flush()

    return wotd


# ── Saved Words (Vocabulary Bank) ──────────────────────────

@router.post("/saved-words", response_model=SavedWordResponse)
async def save_word(
    request: SaveWordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Save a word to the vocabulary bank."""
    saved = SavedWord(
        id=uuid.uuid4(),
        word=request.word,
        notes=request.notes,
        tags=request.tags or [],
    )
    db.add(saved)
    await db.flush()

    return SavedWordResponse(
        id=saved.id,
        word=saved.word,
        notes=saved.notes,
        tags=saved.tags,
        created_at=saved.created_at,
    )


@router.get("/saved-words", response_model=list[SavedWordResponse])
async def get_saved_words(db: AsyncSession = Depends(get_db)):
    """Get all saved words."""
    stmt = select(SavedWord).order_by(desc(SavedWord.created_at))
    result = await db.execute(stmt)
    words = result.scalars().all()

    return [
        SavedWordResponse(
            id=w.id,
            word=w.word,
            notes=w.notes,
            tags=w.tags,
            created_at=w.created_at,
        )
        for w in words
    ]


@router.delete("/saved-words/{word_id}")
async def delete_saved_word(
    word_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a saved word."""
    stmt = select(SavedWord).where(SavedWord.id == word_id)
    result = await db.execute(stmt)
    word = result.scalar_one_or_none()
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    await db.delete(word)
    return {"message": "Word deleted"}


# ── Feedback ───────────────────────────────────────────────

@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback (like/dislike) for a word."""
    fb = Feedback(
        id=uuid.uuid4(),
        search_id=request.search_id,
        word=request.word,
        rating=request.rating,
    )
    db.add(fb)
    await db.flush()
    return {"message": "Feedback submitted"}


# ── History ────────────────────────────────────────────────

@router.get("/history", response_model=HistoryResponse)
async def get_history(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get search history."""
    # Count total
    count_stmt = select(func.count()).select_from(Search)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Fetch history items
    stmt = (
        select(Search, WordResult)
        .outerjoin(WordResult, Search.id == WordResult.search_id)
        .order_by(desc(Search.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = [
        HistoryItem(
            search_id=search.id,
            input_text=search.input_text,
            tone=search.tone,
            intent=search.intent,
            best_fit_word=wr.best_fit_word if wr else None,
            created_at=search.created_at,
        )
        for search, wr in rows
    ]

    return HistoryResponse(items=items, total=total)
