from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str
    TELEGRAM_MESSAGE_THREAD_ID: int | None = None

    API_BASE_URL: str
    API_TOKEN: str
    API_TIMEOUT_SECONDS: float = 10.0
    API_RETRIES: int = 3
    API_RETRY_DELAY_SECONDS: float = 1.0

    EXCLUDED_TAGS: Annotated[list[str], NoDecode] = Field(default_factory=list)

    DATABASE_PATH: str = "data/online_advisor.sqlite3"
    POLL_INTERVAL_SECONDS: int = 30

    REPORT_TIMEZONE: str = "Europe/Moscow"
    REPORT_HOUR: int = 23
    REPORT_MINUTE: int = 59

    LOG_LEVEL: str = "INFO"


    @field_validator("TELEGRAM_MESSAGE_THREAD_ID", mode="before")
    @classmethod
    def parse_optional_thread_id(cls, value: Any) -> int | None:
        if value is None or value == "":
            return None
        return int(value)

    @field_validator("API_BASE_URL")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("EXCLUDED_TAGS", mode="before")
    @classmethod
    def parse_excluded_tags(cls, value: Any) -> list[str]:
        """Accept EXCLUDED_TAGS as JSON array or comma-separated string."""
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(tag).strip() for tag in value if str(tag).strip()]
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    raise ValueError("EXCLUDED_TAGS JSON value must be a list")
                return [str(tag).strip() for tag in parsed if str(tag).strip()]
            return [tag.strip() for tag in raw.split(",") if tag.strip()]
        raise TypeError("EXCLUDED_TAGS must be a list, JSON array or comma-separated string")

    @property
    def authorization_header(self) -> str:
        """Standard Bearer authorization header value."""
        token = self.API_TOKEN.strip()
        if token.lower().startswith("bearer "):
            return token
        return f"Bearer {token}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
