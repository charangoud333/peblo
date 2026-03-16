# 🎓 Peblo Quiz Engine

> AI-powered quiz generation backend for educational platforms.
> Ingests PDF content, generates structured quiz questions using Google Gemini,
> and serves them through a REST API with adaptive difficulty.

---

## 📄 Full Documentation

For complete architecture details, data flow diagrams, and API reference with
example responses, see the detailed documentation:

👉 **[Peblo Quiz Engine — Backend Documentation (PDF/Docs)](https://docs.google.com/document/d/1d8suMCO7koqm4Hck3Hg2BZAQqh-FCj5l/edit?usp=sharing&ouid=117118106256679832045&rtpof=true&sd=true)**

**[watch demo video](https://drive.google.com/file/d/1moPepEf8ap5jV2z51aDIgcbdae8Wnh03/view?usp=sharing)**
---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Adaptive Difficulty Logic](#adaptive-difficulty-logic)
- [Data Flow](#data-flow)

---

## Overview

Peblo Quiz Engine is a production-style backend service that:

1. Accepts PDF uploads and extracts clean text using `pdfplumber`
2. Splits content into structured chunks of ~400 words
3. Uses **Google Gemini** to generate MCQ, True/False, and Fill-in-the-blank questions
4. Stores all data in **PostgreSQL** with full traceability from answer back to source PDF
5. Exposes a **FastAPI** REST API for quiz retrieval and answer submission
6. Adjusts question difficulty **adaptively** based on student performance history

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI |
| Database | PostgreSQL + SQLAlchemy |
| PDF processing | pdfplumber |
| LLM | Google Gemini 2.5 |
| Config management | pydantic-settings |
| Server | Uvicorn |

---

## Project Structure
```
peblo-quiz-engine/
│
├── app/
│   ├── main.py                        # App entry point, router registration
│   ├── config.py                      # Environment variable loading
│   ├── database.py                    # Engine, SessionLocal, get_db
│   │
│   ├── models/
│   │   ├── source.py                  # SourceDocument
│   │   ├── chunk.py                   # ContentChunk
│   │   ├── question.py                # Question
│   │   └── student_answer.py          # StudentAnswer
│   │
│   ├── schemas/
│   │   ├── quiz_schema.py
│   │   └── answer_schema.py
│   │
│   ├── services/
│   │   ├── ingestion_service.py
│   │   ├── chunk_service.py
│   │   ├── quiz_generation_service.py
│   │   └── adaptive_difficulty_service.py
│   │
│   ├── llm/
│   │   └── llm_generator.py           # All Gemini API interaction
│   │
│   └── routes/
│       ├── ingest_routes.py
│       ├── quiz_routes.py
│       └── answer_routes.py
│
├── static/
│   └── index.html                     # Developer test UI
│
├── sample_outputs/
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/your-username/peblo-quiz-engine.git
cd peblo-quiz-engine
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create the PostgreSQL database
```sql
CREATE DATABASE peblo_quiz;
CREATE USER peblo_user WITH PASSWORD 'peblo_pass';
GRANT ALL PRIVILEGES ON DATABASE peblo_quiz TO peblo_user;
```

### 5. Configure environment variables
```bash
cp .env.example .env
```

Fill in your values — see [Environment Variables](#environment-variables) below.

### 6. Start the server
```bash
uvicorn app.main:app --reload
```

Tables are created automatically on first startup.

### 7. Open the test UI
```
http://localhost:8000/static/index.html
```

### 8. Explore the API docs
```
http://localhost:8000/docs      ← Swagger UI
http://localhost:8000/redoc     ← ReDoc
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `LLM_MODEL` | No | `gemini-2.5-flash` | Gemini model name |
| `CHUNK_WORD_LIMIT` | No | `400` | Target words per chunk |

`.env.example`:
```bash
DATABASE_URL=postgresql://peblo_user:peblo_pass@localhost:5432/peblo_quiz
GEMINI_API_KEY=YOUR_API_KEY
LLM_MODEL=YOUR_LLM_MODEL
CHUNK_WORD_LIMIT=400
```

> Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com)

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/ingest` | Upload PDF, run ingestion pipeline |
| `POST` | `/generate-quiz` | Generate LLM questions for a source document |
| `GET` | `/quiz` | Retrieve filtered list of questions |
| `POST` | `/submit-answer` | Evaluate answer, store result, return next difficulty |
| `GET` | `/student/{id}/performance` | Performance summary for a student |
| `GET` | `/health` | Service liveness check |

### POST /ingest
```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@biology.pdf" \
  -F "title=Introduction to Photosynthesis" \
  -F "subject=Biology" \
  -F "grade=Grade 9"
```
```json
{
  "source_id": 1,
  "title": "Introduction to Photosynthesis",
  "chunks_created": 5,
  "message": "Successfully ingested 'Introduction to Photosynthesis' into 5 chunks."
}
```

### POST /generate-quiz
```bash
curl -X POST "http://localhost:8000/generate-quiz?source_id=1"
```
```json
{
  "source_id": 1,
  "questions_created": 15,
  "message": "Generated 15 questions for source_id=1."
}
```

### GET /quiz
```bash
curl "http://localhost:8000/quiz?difficulty=easy&source_id=1&limit=3"
```
```json
{
  "total": 3,
  "questions": [
    {
      "id": 1,
      "chunk_id": 1,
      "question_text": "What is the primary purpose of photosynthesis?",
      "question_type": "MCQ",
      "options": ["Absorb water", "Convert sunlight to energy", "Release CO2", "Produce oxygen only"],
      "correct_answer": "Convert sunlight to energy",
      "difficulty": "easy"
    },
    {
      "id": 2,
      "chunk_id": 1,
      "question_text": "Photosynthesis occurs in the chloroplasts of plant cells.",
      "question_type": "TrueFalse",
      "options": ["True", "False"],
      "correct_answer": "True",
      "difficulty": "easy"
    },
    {
      "id": 3,
      "chunk_id": 1,
      "question_text": "Plants use _____ and water to produce glucose during photosynthesis.",
      "question_type": "FillBlank",
      "options": null,
      "correct_answer": "sunlight",
      "difficulty": "easy"
    }
  ]
}
```

### POST /submit-answer
```bash
curl -X POST http://localhost:8000/submit-answer \
  -H "Content-Type: application/json" \
  -d '{"student_id": "S001", "question_id": 1, "selected_answer": "Convert sunlight to energy"}'
```
```json
{
  "student_id": "S001",
  "question_id": 1,
  "selected_answer": "Convert sunlight to energy",
  "is_correct": true,
  "correct_answer": "Convert sunlight to energy",
  "next_difficulty": "medium",
  "message": "Correct! Keep it up."
}
```

### GET /student/{id}/performance
```bash
curl http://localhost:8000/student/S001/performance
```
```json
{
  "total_answered": 10,
  "total_correct": 7,
  "accuracy_pct": 70.0,
  "current_difficulty": "medium",
  "breakdown": {
    "easy":   { "answered": 4, "correct": 4 },
    "medium": { "answered": 4, "correct": 3 },
    "hard":   { "answered": 2, "correct": 0 }
  }
}
```

---

## Adaptive Difficulty Logic

The system uses a simple three-level ladder:
```
easy ──[correct]──► medium ──[correct]──► hard
hard ──[wrong]──►  medium ──[wrong]──►   easy
```

| Current Level | Result | Next Level |
|---|---|---|
| easy | Correct | medium |
| easy | Incorrect | easy (floor) |
| medium | Correct | hard |
| medium | Incorrect | easy |
| hard | Correct | hard (ceiling) |
| hard | Incorrect | medium |

`next_difficulty` is returned with every `/submit-answer` response.
Use it to filter the next question: `GET /quiz?difficulty={next_difficulty}`

---

## Data Flow
```
PDF Upload (POST /ingest)
    │
    ▼  pdfplumber extracts raw text
    ▼  _clean_text() removes artifacts
    ▼  split_into_chunks() → ~400 word segments
    ▼  DB: SourceDocument + ContentChunk rows saved

POST /generate-quiz
    │
    ▼  Fetch chunks for source_id
    ▼  Send each chunk to Gemini with structured prompt
    ▼  Parse and validate JSON response
    ▼  DB: Question rows saved with chunk_id reference

POST /submit-answer
    │
    ▼  Evaluate correctness
    ▼  DB: StudentAnswer saved
    ▼  Return result + next_difficulty
```

---

## Notes

- Table creation is handled automatically via `Base.metadata.create_all` on startup.
  For production, replace with Alembic migrations.
- CORS is set to `allow_origins=["*"]` for development.
  Restrict this before deploying.
- The LLM module is isolated in `app/llm/llm_generator.py`.
  Switching providers only requires changes there.

---
