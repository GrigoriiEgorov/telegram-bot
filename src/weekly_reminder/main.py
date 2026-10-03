from __future__ import annotations

import logging
import os

from telegram.ext import Application

from .commands import register_handlers
from .config import Settings
from .db import apply_migrations, create_pool
from .repository import ReminderRepository
from .scheduler import ReminderScheduler

logger = logging.getLogger(__name__)


class Runtime:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.pool = None
        self.scheduler = None

    async def start(self, application: Application) -> None:
        self.pool = await create_pool(self.settings.database_url)
        await apply_migrations(self.pool)
        repository = ReminderRepository(self.pool)
        application.bot_data["repository"] = repository
        self.scheduler = ReminderScheduler(
            application.bot, repository, self.settings.scheduler_interval_seconds
        )
        self.scheduler.start()
        logger.info("Weekly reminder bot started")

    async def stop(self, application: Application) -> None:
        if self.scheduler:
            await self.scheduler.stop()
        if self.pool:
            await self.pool.close()
        logger.info("Weekly reminder bot stopped")


def build_application(settings: Settings) -> Application:
    runtime = Runtime(settings)
    application = (
        Application.builder()
        .token(settings.telegram_token)
        .post_init(runtime.start)
        .post_shutdown(runtime.stop)
        .build()
    )
    register_handlers(application)
    return application


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    print(
        "TELEGRAM_BOT_TOKEN configured:",
        bool(os.getenv("TELEGRAM_BOT_TOKEN")),
    )
    settings = Settings.from_env()
    application = build_application(settings)
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
