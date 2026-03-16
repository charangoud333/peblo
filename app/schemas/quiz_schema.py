
"""
Pydantic schemas for quiz-related API requests and responses.

"""

from pydantic import BaseModel
from typing import Optional


class IngestResponse(BaseModel):
    source_id: int
    title: str
    chunks_created: int
    message: str


class QuestionOut(BaseModel):
    id: int
    chunk_id: int
    question_text: str
    question_type: str
    options: Optional[list[str]]
    correct_answer: str
    difficulty: str

    class Config:
        from_attributes = True


class QuizResponse(BaseModel):
    total: int
    questions: list[QuestionOut]


