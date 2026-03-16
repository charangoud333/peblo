
"""
Records every answer a student submits.
Drives the adaptive difficulty logic.
"""

import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.database import Base


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id              = Column(Integer, primary_key=True, index=True)
    student_id      = Column(String(100), nullable=False, index=True)
    question_id     = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_answer = Column(String(255), nullable=False)
    is_correct      = Column(Boolean, nullable=False)
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)