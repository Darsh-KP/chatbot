# Central configuration for the chatbot backend. Every setting can be overridden with an
# environment variable (or a line in chatbot-backend/.env).

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent  # chatbot-backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    
    llm_provider: Literal["ollama", "fake"] = "ollama"
    llm_model: str = "llama3.2:3b"
    llm_temperature: float = 0.1  # subject to change
    llm_max_tokens: int = 512
    llm_timeout_seconds: float = 120.0
    ollama_base_url: str = "http://localhost:11434"
    rag_collection: str = "spring_docs"
    rag_top_k: int = 4  
    rag_max_distance: float | None = None


settings = Settings()