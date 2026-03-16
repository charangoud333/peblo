# app/services/adaptive_difficulty_service.py
"""
Implements adaptive difficulty logic for the quiz engine.

The difficulty ladder has three levels:
  easy → medium → hard

Rules:
  - Correct answer   → move up one level (or stay at hard)
  - Incorrect answer → move down one level (or stay at easy)

This module is intentionally stateless — it receives the current
difficulty and a correctness flag, and returns the next difficulty.
All state lives in the database (StudentAnswer records).
"""

from sqlalchemy.orm import Session

from app.models.student_answer import StudentAnswer
from app.models.question import Question


# Difficulty ladder


DIFFICULTY_LEVELS = ["easy", "medium", "hard"]


def get_next_difficulty(current_difficulty: str, is_correct: bool) -> str:
    """
    Returns the recommended difficulty for the student's next question.

    Args:
        current_difficulty: The difficulty of the question just answered.
        is_correct:         Whether the student answered correctly.

    Returns:
        A difficulty string: 'easy', 'medium', or 'hard'.
    """
    if current_difficulty not in DIFFICULTY_LEVELS:
       
        current_difficulty = "easy"

    current_index = DIFFICULTY_LEVELS.index(current_difficulty)

    if is_correct:
        
        next_index = min(current_index + 1, len(DIFFICULTY_LEVELS) - 1)
    else:
        
        next_index = max(current_index - 1, 0)

    return DIFFICULTY_LEVELS[next_index]


# Performance summary (used for analytics / future dashboard)

def get_student_performance(student_id: str, db: Session) -> dict:
    """
    Aggregates a student's answer history into a performance summary.

    Returns:
        {
            total_answered: int,
            total_correct: int,
            accuracy_pct: float,
            current_difficulty: str,   ← based on most recent answer
            breakdown: {
                easy:   { answered: int, correct: int },
                medium: { answered: int, correct: int },
                hard:   { answered: int, correct: int },
            }
        }
    """
    answers = (
        db.query(StudentAnswer)
        .filter(StudentAnswer.student_id == student_id)
        .order_by(StudentAnswer.created_at.asc())
        .all()
    )

    if not answers:
        return {
            "total_answered": 0,
            "total_correct": 0,
            "accuracy_pct": 0.0,
            "current_difficulty": "easy",
            "breakdown": _empty_breakdown(),
        }

    total = len(answers)
    correct = sum(1 for a in answers if a.is_correct)

    breakdown = _empty_breakdown()
    for answer in answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if question:
            level = question.difficulty
            breakdown[level]["answered"] += 1
            if answer.is_correct:
                breakdown[level]["correct"] += 1

    last_answer = answers[-1]
    last_question = db.query(Question).filter(
        Question.id == last_answer.question_id
    ).first()

    current_difficulty = get_next_difficulty(
        current_difficulty=last_question.difficulty if last_question else "easy",
        is_correct=last_answer.is_correct,
    )

    return {
        "total_answered": total,
        "total_correct": correct,
        "accuracy_pct": round((correct / total) * 100, 2),
        "current_difficulty": current_difficulty,
        "breakdown": breakdown,
    }



def _empty_breakdown() -> dict:
    """Returns a zeroed-out breakdown structure for all difficulty levels."""
    return {
        level: {"answered": 0, "correct": 0}
        for level in DIFFICULTY_LEVELS
    }