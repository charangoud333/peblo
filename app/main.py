# app/main.py
"""
Application entry point.
Registers all routers and initializes the database schema on startup.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
import app.models  # Registers all ORM models with Base.metadata

from app.routes.ingest_routes import router as ingest_router
from app.routes.quiz_routes import router as quiz_router
from app.routes.answer_routes import router as answer_router


# Logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

# App setup


app = FastAPI(
    title="Peblo Quiz Engine",
    description="AI-powered quiz generation platform for educational content.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

Base.metadata.create_all(bind=engine)


# Router registration


app.include_router(ingest_router)
app.include_router(quiz_router)
app.include_router(answer_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "peblo-quiz-engine"}