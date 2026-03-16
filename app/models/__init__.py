# app/models/__init__.py
# Import all models so Alembic and Base.metadata can discover them
from app.models.source import SourceDocument
from app.models.chunk import ContentChunk
from app.models.question import Question
from app.models.student_answer import StudentAnswer