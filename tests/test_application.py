from weekly_reminder.config import Settings
from weekly_reminder.main import build_application


def test_application_registers_bot_handlers(monkeypatch):
    proxy_vars = (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    )
    for name in proxy_vars:
        monkeypatch.delenv(name, raising=False)

    application = build_application(
        Settings(
            telegram_token="test-token",
            database_url="postgresql://localhost/test",
            scheduler_interval_seconds=30,
        )
    )

    commands = {
        command
        for handlers in application.handlers.values()
        for handler in handlers
        if hasattr(handler, "commands")
        for command in handler.commands
    }
    assert {"help", "schedule", "timezone", "message", "on", "off", "status", "test"} <= commands
