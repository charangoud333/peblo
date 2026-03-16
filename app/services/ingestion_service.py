
"""
Orchestrates the full PDF ingestion pipeline:
  
"""

import logging
import re

import pdfplumber
from sqlalchemy.orm import Session

from app.models.source import SourceDocument
from app.models.chunk import ContentChunk
from app.services.chunk_service import split_into_chunks, infer_topic

logger = logging.getLogger(__name__)


# Public entry point

def ingest_pdf(
    file_path: str,
    title: str,
    subject: str,
    grade: str,
    db: Session,
) -> SourceDocument:
    """
    Full ingestion pipeline for a single PDF file.

    Steps:
      1. Extract raw text from all pages
      2. Clean and normalize the text
      3. Split into chunks
      4. Persist SourceDocument + ContentChunks to the database

    Returns the saved SourceDocument instance.
    """
    logger.info(f"Starting ingestion for: {title}")

    raw_text = _extract_text(file_path)
    if not raw_text.strip():
        raise ValueError(f"No extractable text found in PDF: {file_path}")

    clean_text = _clean_text(raw_text)
    chunks = split_into_chunks(clean_text)

    logger.info(f"Extracted {len(chunks)} chunks from '{title}'")

    source_doc = _save_source_document(title, subject, grade, db)
    _save_chunks(chunks, source_doc.id, db)

    logger.info(f"Ingestion complete. SourceDocument id={source_doc.id}")
    return source_doc



def _extract_text(file_path: str) -> str:
    """
    Uses pdfplumber to extract text from every page of the PDF.
    Pages are joined with a newline separator.
    """
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
            else:
                logger.debug(f"Page {page_num} yielded no text (possibly a scan or image)")

    return "\n".join(pages)


def _clean_text(text: str) -> str:
    """
    Normalizes raw extracted text for downstream processing.

    and Cleans.
      
    """
    # Replace non-breaking spaces and similar unicode whitespace
    text = text.replace("\xa0", " ").replace("\u200b", "")

    # Strip form feed characters (common in PDFs)
    text = text.replace("\f", "\n")

    # Collapse runs of whitespace within a line
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse more than two consecutive newlines into two
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove lines that are just dashes or underscores (PDF rule lines)
    text = re.sub(r"^[-_]{3,}\s*$", "", text, flags=re.MULTILINE)

    return text.strip()


def _save_source_document(
    title: str,
    subject: str,
    grade: str,
    db: Session,
) -> SourceDocument:
    """
    Persists a new SourceDocument row and returns it with its generated id.
    """
    source_doc = SourceDocument(
        title=title,
        subject=subject,
        grade=grade,
    )
    db.add(source_doc)
    db.commit()
    db.refresh(source_doc)
    return source_doc


def _save_chunks(
    chunks: list[str],
    source_id: int,
    db: Session,
) -> None:
    """
    Bulk-inserts ContentChunk rows for all chunks belonging to a source document.
    Uses add_all for a single round-trip instead of N individual inserts.
    """
    chunk_rows = [
        ContentChunk(
            source_id=source_id,
            chunk_index=index,
            topic=infer_topic(chunk_text),
            text=chunk_text,
        )
        for index, chunk_text in enumerate(chunks)
    ]

    db.add_all(chunk_rows)
    db.commit()