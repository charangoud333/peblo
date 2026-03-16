
"""
Responsible for splitting cleaned text into manageable chunks.

"""

from app.config import settings


def split_into_chunks(text: str) -> list[str]:
    """
    Splits text into chunks of roughly `chunk_word_limit` words.
    Splits on word boundaries to avoid cutting mid-sentence where possible.
    """
    words = text.split()
    limit = settings.chunk_word_limit

    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= limit:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def infer_topic(chunk_text: str) -> str:
    """
    Extracts a rough topic label from the first sentence of a chunk.
    This is a lightweight heuristic — no LLM call needed here.
    Good enough for filtering; quiz generation adds more context.
    """
    first_sentence = chunk_text.split(".")[0].strip()
    return first_sentence[:80] if first_sentence else "General"