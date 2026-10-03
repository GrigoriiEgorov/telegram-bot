from datetime import datetime, time, timezone

import pytest

from weekly_reminder.models import GroupConfig
from weekly_reminder.scheduler import ReminderScheduler


class FakeRepository:
    def __init__(self, configs):
        self.configs = configs
        self.claimed = set()
        self.released = []

    async def list_enabled_groups(self):
        return self.configs

    async def claim_occurrence(self, chat_id, occurrence):
        key = (chat_id, occurrence)
        if key in self.claimed:
            return False
        self.claimed.add(key)
        return True

    async def release_occurrence(self, chat_id, occurrence):
        self.released.append((chat_id, occurrence))
        self.claimed.remove((chat_id, occurrence))


class FakeBot:
    def __init__(self, fail=False, failing_chat_id=None):
        self.fail = fail
        self.failing_chat_id = failing_chat_id
        self.sent = []

    async def send_message(self, chat_id, text):
        if self.fail or chat_id == self.failing_chat_id:
            raise RuntimeError("temporary failure")
        self.sent.append((chat_id, text))


def config(chat_id=1):
    return GroupConfig(chat_id, 6, time(20), "Europe/Moscow", "weekly", True)


@pytest.mark.asyncio
async def test_scheduler_sends_once_for_repeated_ticks():
    repository = FakeRepository([config()])
    bot = FakeBot()
    scheduler = ReminderScheduler(bot, repository, 30)
    now = datetime(2026, 10, 4, 17, 5, tzinfo=timezone.utc)

    await scheduler.tick(now)
    await scheduler.tick(now)

    assert bot.sent == [(1, "weekly")]


@pytest.mark.asyncio
async def test_scheduler_releases_occurrence_after_delivery_failure():
    repository = FakeRepository([config()])
    bot = FakeBot(fail=True)
    scheduler = ReminderScheduler(bot, repository, 30)

    await scheduler.tick(datetime(2026, 10, 4, 17, 5, tzinfo=timezone.utc))

    assert repository.released == [(1, datetime(2026, 10, 4).date())]


@pytest.mark.asyncio
async def test_delivery_failure_does_not_stop_other_groups():
    repository = FakeRepository([config(1), config(2)])
    bot = FakeBot(failing_chat_id=1)
    scheduler = ReminderScheduler(bot, repository, 30)

    await scheduler.tick(datetime(2026, 10, 4, 17, 5, tzinfo=timezone.utc))

    assert bot.sent == [(2, "weekly")]
