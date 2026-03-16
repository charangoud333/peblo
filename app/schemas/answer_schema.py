# app/schemas/answer_schema.py
"""
Pydantic schemas for answer submission and result responses.
"""

from pydantic import BaseModel


class AnswerIn(BaseModel):
    student_id: str
    question_id: int
    selected_answer: str


class AnswerResult(BaseModel):
    student_id: str
    question_id: int
    selected_answer: str
    is_correct: bool
    correct_answer: str
    next_difficulty: str
    message: str