
"""
Handles student answer submission, correctness evaluation,
and adaptive difficulty recommendation.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.question import Question
from app.models.student_answer import StudentAnswer
from app.schemas.answer_schema import AnswerIn, AnswerResult
from app.services.adaptive_difficulty_service import get_next_difficulty

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submit-answer", tags=["Answers"])


@router.post("", response_model=AnswerResult)
def submit_answer(
    payload: AnswerIn,
    db: Session = Depends(get_db),
):
    """
    Accepts a student's answer, evaluates correctness,
    persists the result, and returns the next recommended difficulty.

    Request body:
      {
        "student_id": "S001",
        "question_id": 12,
        "selected_answer": "3"
      }
    """
    question = db.query(Question).filter(Question.id == payload.question_id).first()
    if not question:
        raise HTTPException(
            status_code=404,
            detail=f"Question id={payload.question_id} not found."
        )

    is_correct = (
        payload.selected_answer.strip().lower()
        == question.correct_answer.strip().lower()
    )

    # Persist the student's answer record
    answer_record = StudentAnswer(
        student_id=payload.student_id,
        question_id=payload.question_id,
        selected_answer=payload.selected_answer,
        is_correct=is_correct,
    )
    db.add(answer_record)
    db.commit()

    next_difficulty = get_next_difficulty(
        current_difficulty=question.difficulty,
        is_correct=is_correct,
    )

    logger.info(
        f"Student {payload.student_id} answered question {payload.question_id} "
        f"— correct={is_correct}, next_difficulty={next_difficulty}"
    )

    return AnswerResult(
        student_id=payload.student_id,
        question_id=payload.question_id,
        selected_answer=payload.selected_answer,
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        next_difficulty=next_difficulty,
        message="Correct! Keep it up." if is_correct else "Incorrect. Review the material and try again.",
    )

  

from app.services.adaptive_difficulty_service import get_student_performance


@router.get("/student/{student_id}/performance", tags=["Answers"])
def student_performance(
    student_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns a performance summary for a given student.

    Useful for dashboards and adaptive learning flows.

    Example response:
      {
        "total_answered": 10,
        "total_correct": 7,
        "accuracy_pct": 70.0,
        "current_difficulty": "medium",
        "breakdown": {
          "easy":   { "answered": 4, "correct": 4 },
          "medium": { "answered": 4, "correct": 3 },
          "hard":   { "answered": 2, "correct": 0 }
        }
      }
    """
    return get_student_performance(student_id=student_id, db=db)
# ```

# ---

# ## How the Difficulty Ladder Works
# ```
#                     CORRECT         INCORRECT
#                        │                │
#           ┌────────────▼────┐      ┌────▼────────────┐
#           │                 │      │                  │
#    easy ──┼──► medium ──────┼──────┼──► easy          │
#           │                 │      │                  │
#           │   medium ───────┼──────┼──► easy          │
#           │         └───────┼──────┼──► medium ───────┤
#           │                 │      │                  │
#           │   hard  ────────┼──────┼──► medium        │
#           │   (stays hard)  │      │   (stays easy)   │
#           └─────────────────┘      └──────────────────┘


#   easy  ──[correct]──►  medium  ──[correct]──►  hard
#   hard  ──[wrong]──►    medium  ──[wrong]──►    easy
# ```

# ---

# ## Full Adaptive Flow End-to-End
# ```
# Student answers question (difficulty=medium)
#             │
#             ▼
#     submit_answer route
#             │
#             ▼
#     is_correct = compare selected vs correct_answer
#             │
#             ├── correct  → get_next_difficulty("medium", True)  → "hard"
#             │
#             └── incorrect → get_next_difficulty("medium", False) → "easy"
#             │
#             ▼
#     AnswerResult returned with next_difficulty
#             │
#             ▼
#     Client uses next_difficulty to call:
#     GET /quiz?difficulty=hard   ← next question served at right level