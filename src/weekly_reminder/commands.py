from __future__ import annotations

from datetime import time
from typing import Awaitable, Callable

from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes

from .models import MAX_MESSAGE_LENGTH, GroupConfig
from .repository import ReminderRepository
from .scheduling import TimezoneValidationError, validate_timezone

DAY_NAMES = {
    "monday": 0,
    "понедельник": 0,
    "mon": 0,
    "вт": 1,
    "вторник": 1,
    "tuesday": 1,
    "среда": 2,
    "ср": 2,
    "wednesday": 2,
    "четверг": 3,
    "чт": 3,
    "thursday": 3,
    "пятница": 4,
    "пт": 4,
    "friday": 4,
    "суббота": 5,
    "сб": 5,
    "saturday": 5,
    "воскресенье": 6,
    "вс": 6,
    "sunday": 6,
}
DAY_LABELS = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")


def _repository(context: ContextTypes.DEFAULT_TYPE) -> ReminderRepository:
    return context.application.bot_data["repository"]


async def _group_and_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or chat.type not in {"group", "supergroup"} or not user:
        if update.effective_message:
            await update.effective_message.reply_text("Эта команда доступна только в группе.")
        return False
    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
        await update.effective_message.reply_text(
            "Изменять настройки могут только администраторы группы."
        )
        return False
    return True


async def _ensure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> GroupConfig:
    return await _repository(context).ensure_group(update.effective_chat.id)


def _format_status(config: GroupConfig) -> str:
    state = "включены" if config.enabled else "выключены"
    return (
        f"Расписание: {DAY_LABELS[config.weekday]}, {config.local_time.strftime('%H:%M')}\n"
        f"Часовой пояс: {config.timezone}\n"
        f"Статус: {state}\n"
        f"Текст: {config.message}"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Команды администратора:\n"
        "/schedule <день> <ЧЧ:ММ> — установить расписание\n"
        "/timezone <IANA timezone> — установить часовой пояс\n"
        "/message <текст> — изменить текст\n"
        "/on и /off — включить или выключить напоминания\n"
        "/status — показать настройки\n"
        "/test — отправить напоминание сейчас\n"
        "/help — показать эту справку"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _group_and_admin(update, context):
        return
    await update.effective_message.reply_text(_format_status(await _ensure(update, context)))


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _group_and_admin(update, context):
        return
    if len(context.args) != 2:
        await update.effective_message.reply_text("Использование: /schedule <день> <ЧЧ:ММ>")
        return
    weekday = DAY_NAMES.get(context.args[0].lower())
    try:
        parsed_time = time.fromisoformat(context.args[1])
    except ValueError:
        parsed_time = None
    if weekday is None or parsed_time is None or parsed_time.second or parsed_time.microsecond:
        await update.effective_message.reply_text(
            "День или время указаны неверно. Пример: /schedule sunday 20:00"
        )
        return
    current = await _ensure(update, context)
    updated = await _repository(context).update_schedule(
        current.chat_id, weekday, parsed_time, current.timezone
    )
    await update.effective_message.reply_text(f"Расписание обновлено.\n{_format_status(updated)}")


async def timezone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _group_and_admin(update, context):
        return
    if len(context.args) != 1:
        await update.effective_message.reply_text("Использование: /timezone Europe/Moscow")
        return
    try:
        timezone = validate_timezone(context.args[0])
    except TimezoneValidationError:
        await update.effective_message.reply_text(
            "Неизвестный часовой пояс. Используйте IANA timezone."
        )
        return
    current = await _ensure(update, context)
    updated = await _repository(context).update_schedule(
        current.chat_id, current.weekday, current.local_time, timezone
    )
    await update.effective_message.reply_text(f"Часовой пояс обновлён.\n{_format_status(updated)}")


async def message_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _group_and_admin(update, context):
        return
    message = " ".join(context.args).strip()
    if not message or len(message) > MAX_MESSAGE_LENGTH:
        await update.effective_message.reply_text(
            f"Текст должен быть от 1 до {MAX_MESSAGE_LENGTH} символов."
        )
        return
    updated = await _repository(context).update_message(update.effective_chat.id, message)
    await update.effective_message.reply_text(f"Текст обновлён.\n{_format_status(updated)}")


async def set_enabled(update: Update, context: ContextTypes.DEFAULT_TYPE, enabled: bool) -> None:
    if not await _group_and_admin(update, context):
        return
    updated = await _repository(context).set_enabled(update.effective_chat.id, enabled)
    state = "включены" if updated.enabled else "выключены"
    await update.effective_message.reply_text(f"Напоминания {state}.")


async def on_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_enabled(update, context, True)


async def off_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_enabled(update, context, False)


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _group_and_admin(update, context):
        return
    config = await _ensure(update, context)
    await context.bot.send_message(chat_id=config.chat_id, text=config.message)


def register_handlers(application: object) -> None:
    from telegram.ext import CommandHandler

    handlers: list[tuple[str, Callable[..., Awaitable[None]]]] = [
        ("help", help_command),
        ("status", status_command),
        ("schedule", schedule_command),
        ("timezone", timezone_command),
        ("message", message_command),
        ("on", on_command),
        ("off", off_command),
        ("test", test_command),
    ]
    for command, callback in handlers:
        application.add_handler(CommandHandler(command, callback))
