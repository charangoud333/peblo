
"""
Handles PDF upload and ingestion pipeline trigger.
Saves the uploaded file temporarily, runs ingestion, then cleans up.
"""

import os
import shutil
import logging
import tempfile

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.quiz_schema import IngestResponse
from app.services.ingestion_service import ingest_pdf
from app.models.chunk import ContentChunk

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: str = Form(default="General"),
    grade: str = Form(default="Unknown"),
    db: Session = Depends(get_db),
):
    """
    Accepts a PDF upload and runs the full ingestion pipeline.

    - Saves file to a temp location
    - Extracts and cleans text
    - Splits into chunks
    - Persists SourceDocument + ContentChunks to DB

    Returns the source_id and chunk count for use in /generate-quiz.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        source_doc = ingest_pdf(
            file_path=tmp_path,
            title=title,
            subject=subject,
            grade=grade,
            db=db,
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during ingestion")
        raise HTTPException(status_code=500, detail="Ingestion failed. Check server logs.")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    chunk_count = (
        db.query(ContentChunk)
        .filter(ContentChunk.source_id == source_doc.id)
        .count()
    )

    return IngestResponse(
        source_id=source_doc.id,
        title=source_doc.title,
        chunks_created=chunk_count,
        message=f"Successfully ingested '{title}' into {chunk_count} chunks.",
    )