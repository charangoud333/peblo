
"""
A single text chunk extracted from a SourceDocument.

"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id          = Column(Integer, primary_key=True, index=True)
    source_id   = Column(Integer, ForeignKey("source_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)   
    topic       = Column(String(255), nullable=True)
    text        = Column(Text, nullable=False)

    source    = relationship("SourceDocument", backref="chunks")
    questions = relationship("Question", back_populates="chunk")