from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables or a `.env` file.

    Nothing here is required to *start* the server: without OPENAI_API_KEY the
    chat endpoints answer with a clear "not configured" message, while crisis
    detection (which never needs the AI) keeps working.
    """

    PROJECT_NAME: str = "Robin Chatbot API"
    VERSION: str = "1.1.0"

    OPENAI_API_KEY: str = ""
    # Optional: point at any OpenAI-compatible API (e.g. https://api.groq.com/openai/v1)
    OPENAI_BASE_URL: str = ""
    OPENAI_MODEL_MAIN: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE_EMPATHY: float = 0.7

    # Comma-separated list in .env, e.g. CORS_ORIGINS=http://localhost:3000,https://myapp.com
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    MAX_MESSAGE_CHARS: int = 2000
    MAX_HISTORY_MESSAGES: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str) and not v.strip().startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


settings = Settings()
