"""Application settings using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: Literal["development", "staging", "production"] = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/safelytold"
    app_name: str = "HELP ME Platform API"

    class Config:
        env_file = ".env"
        env_prefix = "HELP_ME_"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
