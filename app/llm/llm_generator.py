# app/llm/llm_generator.py
"""
All LLM interaction isolated here.
Uses Google Gemini API .
"""

import json
import logging
import re
from typing import Any

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(model_name=settings.llm_model)


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

QUIZ_PROMPT_TEMPLATE = """You are an educational quiz generator.

Generate exactly 3 quiz questions from the text below.
Output ONLY a raw JSON array. No markdown. No code fences. No explanation.

You MUST generate exactly one of each type — no exceptions:
- Question 1: type must be "MCQ" (4 options)
- Question 2: type must be "TrueFalse" (options must be exactly ["True", "False"])
- Question 3: type must be "FillBlank" (options must be null, use _____ in question text)

Output this exact structure:
[
  {{
    "question": "What is the capital of France?",
    "type": "MCQ",
    "options": ["Paris", "London", "Berlin", "Rome"],
    "answer": "Paris",
    "difficulty": "easy"
  }},
  {{
    "question": "The capital of France is Paris.",
    "type": "TrueFalse",
    "options": ["True", "False"],
    "answer": "True",
    "difficulty": "easy"
  }},
  {{
    "question": "The capital of France is _____.",
    "type": "FillBlank",
    "options": null,
    "answer": "Paris",
    "difficulty": "easy"
  }}
]

Rules:
- Base all questions strictly on the provided text
- MCQ must have exactly 4 options
- TrueFalse options must be exactly ["True", "False"]
- FillBlank must use _____ in the question and options must be null
- answer must match one of the options exactly (or the blank word for FillBlank)
- Vary difficulty across the 3 questions: one easy, one medium, one hard

Text:
{chunk_text}"""


# ---------------------------------------------------------------------------
# Generation config
# ---------------------------------------------------------------------------

GENERATION_CONFIG = genai.types.GenerationConfig(
    temperature=0.4,
    max_output_tokens=2048,
)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def generate_questions_for_chunk(chunk_text: str) -> list[dict[str, Any]]:
    """
    Sends a chunk of educational text to Gemini and returns
    a list of structured question dictionaries.
    """
    trimmed_text = _trim_chunk(chunk_text, max_words=600)
    prompt = QUIZ_PROMPT_TEMPLATE.format(chunk_text=trimmed_text)

    logger.debug("Sending chunk to Gemini for question generation")

    try:
        response = model.generate_content(
            prompt,
            generation_config=GENERATION_CONFIG,
        )
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise

    raw_output = response.text.strip()

    logger.info(f"Raw Gemini response:\n{raw_output}")

    return _parse_llm_response(raw_output)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_llm_response(raw: str) -> list[dict[str, Any]]:
    """
    Aggressively cleans and parses Gemini output.
    Handles markdown fences, extra prose, and truncation.
    """
    cleaned = _clean_raw_response(raw)
    logger.info(f"Cleaned response:\n{cleaned}")

    # Attempt 1 — clean parse
    try:
        parsed = json.loads(cleaned)
        return _validate_all(parsed)
    except json.JSONDecodeError as e:
        logger.warning(f"Clean parse failed: {e} — trying array extraction")

    # Attempt 2 — extract the JSON array substring directly
    extracted = _extract_json_array(cleaned)
    if extracted:
        try:
            parsed = json.loads(extracted)
            return _validate_all(parsed)
        except json.JSONDecodeError as e:
            logger.warning(f"Array extraction parse failed: {e} — trying object recovery")

    # Attempt 3 — recover individual complete objects
    recovered = _recover_objects(cleaned)
    if recovered:
        logger.info(f"Recovered {len(recovered)} question(s) from malformed response")
        return recovered

    logger.error(f"All parse attempts failed. Raw output was:\n{raw}")
    raise ValueError(f"Could not parse Gemini response: {raw[:200]}")


def _clean_raw_response(raw: str) -> str:
    """
    Strips everything that isn't the JSON array.
    Handles markdown code fences, language tags, and leading prose.
    """
   
    raw = re.sub(r"```(?:json)?\s*", "", raw)
    raw = re.sub(r"```", "", raw)

    bracket_pos = raw.find("[")
    if bracket_pos > 0:
        raw = raw[bracket_pos:]

    last_bracket = raw.rfind("]")
    if last_bracket != -1:
        raw = raw[:last_bracket + 1]

    return raw.strip()


def _extract_json_array(text: str) -> str | None:
   
    start = text.find("[")
    if start == -1:
        return None

    depth = 0
    for i, char in enumerate(text[start:], start=start):
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return None


def _recover_objects(text: str) -> list[dict[str, Any]]:
    """
    Scans for complete {...} objects and validates each one individually.
    Last resort when the outer array structure is broken.
    """
    recovered = []
    depth = 0
    start = -1

    for i, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start != -1:
                candidate = text[start:i + 1]
                try:
                    obj = json.loads(candidate)
                    validated = _validate_question(obj, index=len(recovered))
                    recovered.append(validated)
                except (json.JSONDecodeError, AssertionError, KeyError) as e:
                    logger.warning(f"Skipping unrecoverable object: {e}")
                start = -1

    return recovered


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_all(parsed: Any) -> list[dict[str, Any]]:
    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON array, got {type(parsed)}")

    validated = []
    for i, item in enumerate(parsed):
        try:
            validated.append(_validate_question(item, index=i))
        except (KeyError, AssertionError) as e:
            logger.warning(f"Skipping malformed question at index {i}: {e}")

    return validated


def _validate_question(item: dict, index: int) -> dict:
    """
    Ensures a question object has all required fields with acceptable values.
    """
    required_fields = {"question", "type", "answer", "difficulty"}
    missing = required_fields - item.keys()
    assert not missing, f"Question {index} missing fields: {missing}"

    assert item["type"] in {"MCQ", "TrueFalse", "FillBlank"}, \
        f"Invalid question type: {item['type']}"

    assert item["difficulty"] in {"easy", "medium", "hard"}, \
        f"Invalid difficulty: {item['difficulty']}"

    if item["type"] == "TrueFalse":
        assert item.get("options") == ["True", "False"], \
            "TrueFalse options must be exactly ['True', 'False']"

    if item["type"] == "FillBlank":
        item["options"] = None

    return item


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _trim_chunk(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    logger.debug(f"Chunk trimmed from {len(words)} to {max_words} words")
    return " ".join(words[:max_words])