"""Application settings loaded from environment / .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_chat_model: str = Field(
        default="claude-sonnet-4-6", alias="ANTHROPIC_CHAT_MODEL"
    )
    anthropic_fast_model: str = Field(
        default="claude-haiku-4-5-20251001", alias="ANTHROPIC_FAST_MODEL"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_tokens_per_paper: int = Field(default=100_000, alias="MAX_TOKENS_PER_PAPER")
    cors_allowed_origins: str = Field(
        default="http://localhost:3000", alias="CORS_ALLOWED_ORIGINS"
    )
    app_api_key: str = Field(default="", alias="APP_API_KEY")
    rate_limit_per_minute: int = Field(default=10, alias="RATE_LIMIT_PER_MINUTE")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    max_tokens_per_request: int = Field(
        default=2_000_000, alias="MAX_TOKENS_PER_REQUEST"
    )
    result_cache_size: int = Field(default=64, alias="RESULT_CACHE_SIZE")
    enable_prompt_cache: bool = Field(default=True, alias="ENABLE_PROMPT_CACHE")
    data_dir: str = Field(default="./data", alias="DATA_DIR")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
