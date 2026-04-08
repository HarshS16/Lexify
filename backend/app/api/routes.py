import uuid
import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
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
from app.services.ai_service import get_ai_service, get_suggestions, get_word_of_the_day

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}

# ── Word Search ────────────────────────────────────────────

@router.post("/search", response_model=SearchResponse)
async def search_words(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Main endpoint: find better words for user input."""
    if not is_safe(request.input_text):
        raise HTTPException(status_code=400, detail=BLOCKED_RESPONSE)

    ai = get_ai_service()

    # Run AI pipeline (single call)
    result = await ai.find_better_words(
        user_input=request.input_text,
        tone=request.tone or "neutral",
        intent=request.intent or "general expression",
    )

    # Store in DB — non-blocking (don't fail the response if DB errors)
    search_id = uuid.uuid4()
    try:
        search = Search(
            id=search_id,
            input_text=request.input_text,
            tone=request.tone,
            intent=request.intent,
            analysis_json=result.analysis.model_dump(),
        )
        db.add(search)

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
        await db.commit()
    except Exception as e:
        logger.warning(f"DB write failed (search still returned): {e}")
        await db.rollback()

    return SearchResponse(search_id=search_id, result=result)


# ── Rewrite Mode ───────────────────────────────────────────

@router.post("/rewrite", response_model=RewriteResult)
async def rewrite_sentence(request: RewriteRequest):
    """Rewrite a sentence with a specific goal."""
    if not is_safe(request.input_text):
        raise HTTPException(status_code=400, detail=BLOCKED_RESPONSE)

    ai = get_ai_service()
    return await ai.rewrite_sentence(
        input_text=request.input_text,
        goal=request.goal,
        tone=request.tone or "neutral",
    )


# ── Word of the Day ───────────────────────────────────────

@router.get("/word-of-the-day", response_model=WordOfTheDayResponse)
async def get_word_of_the_day(db: AsyncSession = Depends(get_db)):
    """Get today's Word of the Day (cached in DB)."""
    today = date.today()

    # Check DB cache first
    try:
        stmt = select(WordOfTheDay).where(WordOfTheDay.date == today)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return WordOfTheDayResponse(
                date=existing.date,
                word=existing.word,
                **(existing.data_json or {}),
            )
    except Exception as e:
        logger.warning(f"DB read failed for WOTD: {e}")

    # Generate new word
    ai = get_ai_service()
    wotd = await ai.generate_word_of_the_day()

    # Store in DB — non-blocking
    try:
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
        await db.commit()
    except Exception as e:
        logger.warning(f"DB write failed for WOTD: {e}")
        await db.rollback()

    return wotd


# ── Saved Words ──────────────────────────────────────

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
    await db.commit()

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
    await db.commit()
    return {"message": "Word deleted"}


# ── Feedback ───────────────────────────────────────────────

@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback (like/dislike) for a word."""
    try:
        fb = Feedback(
            id=uuid.uuid4(),
            search_id=request.search_id,
            word=request.word,
            rating=request.rating,
        )
        db.add(fb)
        await db.commit()
    except Exception as e:
        logger.warning(f"Feedback DB write failed: {e}")
        await db.rollback()
    return {"message": "Feedback submitted"}


# ── History ────────────────────────────────────────────────

@router.get("/history", response_model=HistoryResponse)
async def get_history(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get search history."""
    count_stmt = select(func.count()).select_from(Search)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

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


# ── Speech-to-Text (Brave fallback) ────────────────────────

@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio using Groq Whisper — fallback for browsers that block Web Speech API."""
    settings = get_settings()
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="Speech-to-text service not configured.")

    # Read the uploaded audio
    audio_bytes = await audio.read()
    if len(audio_bytes) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=413, detail="Audio file too large (max 5MB).")

    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file.")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                files={"file": (audio.filename or "audio.webm", audio_bytes, audio.content_type or "audio/webm")},
                data={"model": "whisper-large-v3", "language": "en"},
            )

        if response.status_code != 200:
            logger.error(f"Groq Whisper error: {response.status_code} {response.text[:200]}")
            raise HTTPException(status_code=502, detail="Transcription service error.")

        data = response.json()
        text = data.get("text", "").strip()
        if not text:
            raise HTTPException(status_code=422, detail="No speech detected in audio.")

        return {"text": text}

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Transcription timed out. Please try again.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed.")
