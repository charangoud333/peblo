
"""
Handles quiz generation and quiz retrieval endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chunk import ContentChunk
from app.models.question import Question
from app.schemas.quiz_schema import QuizResponse, QuestionOut
from app.services.quiz_generation_service import generate_quiz_for_source

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Quiz"])


# --------------------------
# POST /generate-quiz
# --------------------------

@router.post("/generate-quiz")
def generate_quiz(
    source_id: int,
    db: Session = Depends(get_db),
):
    """
    Triggers LLM-based quiz generation for all chunks of a source document.
    Skips chunks that already have questions.
    Returns total questions created.
    """
    try:
        total = generate_quiz_for_source(source_id=source_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Quiz generation failed")
        raise HTTPException(status_code=500, detail="Quiz generation failed. Check server logs.")

    return {
        "source_id": source_id,
        "questions_created": total,
        "message": f"Generated {total} questions for source_id={source_id}.",
    }


# ------------------
# GET /quiz
#--------------------

@router.get("/quiz", response_model=QuizResponse)
def get_quiz(
    topic: Optional[str] = Query(default=None, description="Filter by topic keyword"),
    difficulty: Optional[str] = Query(default=None, description="easy | medium | hard"),
    source_id: Optional[int] = Query(default=None, description="Filter by source document"),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """
    Returns a filtered list of quiz questions.

    All filters are optional and combinable:
      ?topic=photosynthesis&difficulty=easy&source_id=1

    Fix: ContentChunk is joined only once regardless of how many
    chunk-level filters are active. Previously each filter block
    added its own .join(ContentChunk), causing a DuplicateAlias
    error in PostgreSQL when two or more filters were combined.
    """
    if difficulty:
        allowed = {"easy", "medium", "hard"}
        if difficulty not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"difficulty must be one of: {allowed}"
            )

    query = db.query(Question)

    needs_chunk_join = source_id is not None or topic is not None
    if needs_chunk_join:
        query = query.join(ContentChunk, ContentChunk.id == Question.chunk_id)

    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    if source_id:
        query = query.filter(ContentChunk.source_id == source_id)

    if topic:
        query = query.filter(ContentChunk.topic.ilike(f"%{topic}%"))

    questions = query.limit(limit).all()

    return QuizResponse(
        total=len(questions),
        questions=[QuestionOut.model_validate(q) for q in questions],
    )