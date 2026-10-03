from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Raised when required runtime configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_token: str
    database_url: str
    scheduler_interval_seconds: int = 30

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not token:
            raise ConfigurationError("TELEGRAM_BOT_TOKEN is required")
        if not database_url:
            raise ConfigurationError("DATABASE_URL is required")

        raw_interval = os.getenv("SCHEDULER_INTERVAL_SECONDS", "30").strip()
        try:
            interval = int(raw_interval)
        except ValueError as exc:
            raise ConfigurationError("SCHEDULER_INTERVAL_SECONDS must be an integer") from exc
        if interval < 5:
            raise ConfigurationError("SCHEDULER_INTERVAL_SECONDS must be at least 5")

        return cls(
            telegram_token=token,
            database_url=database_url,
            scheduler_interval_seconds=interval,
        )
