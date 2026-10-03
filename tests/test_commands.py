from datetime import time
from types import SimpleNamespace

import pytest
from telegram.constants import ChatMemberStatus

from weekly_reminder import commands
from weekly_reminder.models import GroupConfig


class FakeMessage:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text):
        self.replies.append(text)


class FakeBot:
    def __init__(self, status=ChatMemberStatus.ADMINISTRATOR):
        self.status = status
        self.sent = []

    async def get_chat_member(self, chat_id, user_id):
        return SimpleNamespace(status=self.status)

    async def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))


class FakeRepository:
    def __init__(self):
        self.config = GroupConfig(1, 6, time(20), "Europe/Moscow", "default", True)
        self.updates = []

    async def ensure_group(self, chat_id):
        return self.config

    async def update_schedule(self, chat_id, weekday, local_time, timezone):
        self.config = GroupConfig(
            chat_id, weekday, local_time, timezone, self.config.message, self.config.enabled
        )
        self.updates.append("schedule")
        return self.config

    async def update_message(self, chat_id, message):
        self.config = GroupConfig(
            chat_id,
            self.config.weekday,
            self.config.local_time,
            self.config.timezone,
            message,
            self.config.enabled,
        )
        self.updates.append("message")
        return self.config

    async def set_enabled(self, chat_id, enabled):
        self.config = GroupConfig(
            chat_id,
            self.config.weekday,
            self.config.local_time,
            self.config.timezone,
            self.config.message,
            enabled,
        )
        self.updates.append("enabled")
        return self.config


def context(repo, bot, args):
    return SimpleNamespace(
        args=args,
        bot=bot,
        application=SimpleNamespace(bot_data={"repository": repo}),
    )


def update(message, chat_type="group"):
    return SimpleNamespace(
        effective_chat=SimpleNamespace(id=1, type=chat_type),
        effective_user=SimpleNamespace(id=10),
        effective_message=message,
    )


@pytest.mark.asyncio
async def test_schedule_command_updates_group_configuration():
    repo = FakeRepository()
    message = FakeMessage()

    await commands.schedule_command(update(message), context(repo, FakeBot(), ["sunday", "21:30"]))

    assert repo.config.local_time == time(21, 30)
    assert repo.config.weekday == 6
    assert repo.updates == ["schedule"]
    assert "Расписание обновлено" in message.replies[0]


@pytest.mark.asyncio
async def test_invalid_message_does_not_change_configuration():
    repo = FakeRepository()
    message = FakeMessage()

    await commands.message_command(update(message), context(repo, FakeBot(), []))

    assert repo.updates == []
    assert "от 1" in message.replies[0]


@pytest.mark.asyncio
async def test_invalid_schedule_does_not_change_configuration():
    repo = FakeRepository()
    message = FakeMessage()

    await commands.schedule_command(update(message), context(repo, FakeBot(), ["sunday", "25:00"]))

    assert repo.updates == []
    assert "указаны неверно" in message.replies[0]


@pytest.mark.asyncio
async def test_timezone_command_validates_and_updates_timezone():
    repo = FakeRepository()
    message = FakeMessage()

    await commands.timezone_command(update(message), context(repo, FakeBot(), ["Europe/London"]))

    assert repo.config.timezone == "Europe/London"


@pytest.mark.asyncio
async def test_help_command_describes_supported_commands():
    message = FakeMessage()

    await commands.help_command(update(message), context(FakeRepository(), FakeBot(), []))

    assert "/schedule" in message.replies[0]
    assert "/test" in message.replies[0]


@pytest.mark.asyncio
async def test_non_admin_cannot_change_schedule():
    repo = FakeRepository()
    message = FakeMessage()

    await commands.schedule_command(
        update(message), context(repo, FakeBot(ChatMemberStatus.MEMBER), ["sunday", "21:30"])
    )

    assert repo.updates == []
    assert "только администраторы" in message.replies[0]


@pytest.mark.asyncio
async def test_lifecycle_commands_and_test_delivery():
    repo = FakeRepository()
    bot = FakeBot()
    message = FakeMessage()
    ctx = context(repo, bot, [])

    await commands.off_command(update(message), ctx)
    await commands.on_command(update(message), ctx)
    await commands.test_command(update(message), ctx)

    assert repo.config.enabled is True
    assert bot.sent == [(1, "default")]
