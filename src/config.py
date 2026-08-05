from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]
    ENVIRONMENT: str = "development"

    # Data Paths
    DATASET_NAME: str = "ManikaSaini/zomato-restaurant-recommendation"
    DATA_CACHE_PATH: str = "data/processed/restaurants.parquet"
    METADATA_DIR: str = "data/metadata"

    # LLM Configuration
    LLM_PROVIDER: str = "groq"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    MAX_CANDIDATES_FOR_LLM: int = 25
    DEFAULT_TOP_K: int = 5



@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
