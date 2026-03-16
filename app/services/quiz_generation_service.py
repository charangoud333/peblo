
"""
Orchestrates quiz generation across all chunks of a source document.

Flow:
  Fetch chunks from DB → call LLM per chunk → persist Questions to DB
"""

import logging

from sqlalchemy.orm import Session

from app.models.chunk import ContentChunk
from app.models.question import Question
from app.llm.llm_generator import generate_questions_for_chunk

logger = logging.getLogger(__name__)


# Public entry point

def generate_quiz_for_source(source_id: int, db: Session) -> int:
    """
    Generates quiz questions for every chunk belonging to the given source_id.

    Skips chunks that already have questions to avoid duplicates
    on repeated calls.

    Returns the total number of questions created.
    """
    chunks = (
        db.query(ContentChunk)
        .filter(ContentChunk.source_id == source_id)
        .order_by(ContentChunk.chunk_index)
        .all()
    )

    if not chunks:
        raise ValueError(f"No chunks found for source_id={source_id}")

    logger.info(f"Generating questions for {len(chunks)} chunks (source_id={source_id})")

    total_created = 0

    for chunk in chunks:
        if _chunk_already_has_questions(chunk.id, db):
            logger.debug(f"Skipping chunk {chunk.id} — questions already exist")
            continue

        try:
            questions_data = generate_questions_for_chunk(chunk.text)
            created = _save_questions(questions_data, chunk.id, db)
            total_created += created
            logger.info(f"Chunk {chunk.id}: {created} questions saved")
        except Exception as e: # Log and continue — one bad chunk shouldn't abort the whole job
            logger.error(f"Failed to generate questions for chunk {chunk.id}: {e}")
            continue

    logger.info(f"Quiz generation complete. Total questions created: {total_created}")
    return total_created

# Internal helpers

def _chunk_already_has_questions(chunk_id: int, db: Session) -> bool:
    """
    Checks whether questions already exist for a given chunk.
    Prevents duplicate generation on repeated /generate-quiz calls.
    """
    return db.query(Question).filter(Question.chunk_id == chunk_id).first() is not None


def _save_questions(
    questions_data: list[dict],
    chunk_id: int,
    db: Session,
) -> int:
    """
    Persists a list of validated question dicts to the database.
    Returns the count of rows inserted.
    """
    rows = [
        Question(
            chunk_id=chunk_id,
            question_text=q["question"],
            question_type=q["type"],
            options=q.get("options"),
            correct_answer=q["answer"],
            difficulty=q["difficulty"],
        )
        for q in questions_data
    ]

    db.add_all(rows)
    db.commit()
    return len(rows)


## How LLM Output Maps to the DB

# LLM JSON object

# {                              Question row
#   "question": "..."    →       question_text
#   "type": "MCQ"        →       question_type
#   "options": [...]     →       options (JSON)
#   "answer": "3"        →       correct_answer
#   "difficulty": "easy" →       difficulty
# }                              chunk_id  ← injected by _save_questions()