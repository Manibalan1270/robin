from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Robin Chatbot API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL_MAIN: str = "gpt-4o"
    OPENAI_MODEL_FALLBACK: str = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE_EMPATHY: float = 0.7
    OPENAI_TEMPERATURE_CRISIS: float = 0.2

    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
