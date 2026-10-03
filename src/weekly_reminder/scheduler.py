from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from telegram import Bot

from .repository import ReminderRepository
from .scheduling import is_due

logger = logging.getLogger(__name__)


class ReminderScheduler:
    def __init__(self, bot: Bot, repository: ReminderRepository, interval_seconds: int) -> None:
        self.bot = bot
        self.repository = repository
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()

    def start(self) -> None:
        self._stopped.clear()
        self._task = asyncio.create_task(self.run(), name="reminder-scheduler")

    async def stop(self) -> None:
        self._stopped.set()
        if self._task:
            await self._task
            self._task = None

    async def run(self) -> None:
        while not self._stopped.is_set():
            await self.tick()
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=self.interval_seconds)
            except asyncio.TimeoutError:
                pass

    async def tick(self, now: datetime | None = None) -> None:
        current = now or datetime.now(timezone.utc)
        for config in await self.repository.list_enabled_groups():
            due, occurrence = is_due(config, current)
            if not due or occurrence is None:
                continue
            claimed = await self.repository.claim_occurrence(config.chat_id, occurrence)
            if not claimed:
                continue
            try:
                await asyncio.wait_for(
                    self.bot.send_message(chat_id=config.chat_id, text=config.message),
                    timeout=30,
                )
            except Exception:
                await self.repository.release_occurrence(config.chat_id, occurrence)
                logger.exception("Scheduled delivery failed for chat_id=%s", config.chat_id)
