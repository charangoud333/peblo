
"""
A quiz question generated from a ContentChunk.
Options are stored as JSON to support MCQ, T/F, and fill-in-the-blank.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id            = Column(Integer, primary_key=True, index=True)
    chunk_id      = Column(Integer, ForeignKey("content_chunks.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)   # MCQ | TrueFalse | FillBlank
    options       = Column(JSON, nullable=True)           # None for fill-in-the-blank
    correct_answer= Column(String(255), nullable=False)
    difficulty    = Column(String(20), nullable=False, default="easy")  # easy|medium|hard

    chunk = relationship("ContentChunk", back_populates="questions")