import pytest

from weekly_reminder.config import ConfigurationError, Settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("SCHEDULER_INTERVAL_SECONDS", "15")

    settings = Settings.from_env()

    assert settings.telegram_token == "test-token"
    assert settings.database_url.endswith("/test")
    assert settings.scheduler_interval_seconds == 15


def test_settings_require_secrets(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")

    with pytest.raises(ConfigurationError, match="TELEGRAM_BOT_TOKEN"):
        Settings.from_env()


def test_settings_reject_short_scheduler_interval(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("SCHEDULER_INTERVAL_SECONDS", "1")

    with pytest.raises(ConfigurationError, match="at least 5"):
        Settings.from_env()
