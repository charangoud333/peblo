# app/models/source.py
"""
Represents an uploaded PDF document.
Every chunk and question traces back to a SourceDocument.
"""

import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(255), nullable=False)
    subject     = Column(String(100), nullable=True)
    grade       = Column(String(50),  nullable=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)