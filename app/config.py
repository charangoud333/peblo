# app/config.py
"""
Centralized settings loaded from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str
    llm_model: str = "gemini-2.5-flash"   
    chunk_word_limit: int = 400

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()