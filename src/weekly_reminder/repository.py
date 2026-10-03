from __future__ import annotations

from datetime import date, time

import asyncpg

from .models import (
    DEFAULT_MESSAGE,
    DEFAULT_TIME,
    DEFAULT_TIMEZONE,
    DEFAULT_WEEKDAY,
    GroupConfig,
)


def _to_config(record: asyncpg.Record) -> GroupConfig:
    return GroupConfig(
        chat_id=record["chat_id"],
        weekday=record["weekday"],
        local_time=record["local_time"],
        timezone=record["timezone"],
        message=record["message"],
        enabled=record["enabled"],
    )


class ReminderRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def ensure_group(self, chat_id: int) -> GroupConfig:
        record = await self.pool.fetchrow(
            """
            INSERT INTO group_reminder_configs
                (chat_id, weekday, local_time, timezone, message)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (chat_id) DO UPDATE SET updated_at = NOW()
            RETURNING chat_id, weekday, local_time, timezone, message, enabled
            """,
            chat_id,
            DEFAULT_WEEKDAY,
            DEFAULT_TIME,
            DEFAULT_TIMEZONE,
            DEFAULT_MESSAGE,
        )
        return _to_config(record)

    async def get_group(self, chat_id: int) -> GroupConfig | None:
        record = await self.pool.fetchrow(
            """SELECT chat_id, weekday, local_time, timezone, message, enabled
               FROM group_reminder_configs WHERE chat_id = $1""",
            chat_id,
        )
        return _to_config(record) if record else None

    async def list_enabled_groups(self) -> list[GroupConfig]:
        records = await self.pool.fetch(
            """SELECT chat_id, weekday, local_time, timezone, message, enabled
               FROM group_reminder_configs WHERE enabled = TRUE"""
        )
        return [_to_config(record) for record in records]

    async def update_schedule(
        self, chat_id: int, weekday: int, local_time: time, timezone: str
    ) -> GroupConfig:
        record = await self.pool.fetchrow(
            """
            UPDATE group_reminder_configs
            SET weekday = $2, local_time = $3, timezone = $4, updated_at = NOW()
            WHERE chat_id = $1
            RETURNING chat_id, weekday, local_time, timezone, message, enabled
            """,
            chat_id,
            weekday,
            local_time,
            timezone,
        )
        if not record:
            return await self.ensure_group(chat_id)
        return _to_config(record)

    async def update_message(self, chat_id: int, message: str) -> GroupConfig:
        record = await self.pool.fetchrow(
            """
            UPDATE group_reminder_configs SET message = $2, updated_at = NOW()
            WHERE chat_id = $1
            RETURNING chat_id, weekday, local_time, timezone, message, enabled
            """,
            chat_id,
            message,
        )
        if not record:
            await self.ensure_group(chat_id)
            return await self.update_message(chat_id, message)
        return _to_config(record)

    async def set_enabled(self, chat_id: int, enabled: bool) -> GroupConfig:
        record = await self.pool.fetchrow(
            """
            UPDATE group_reminder_configs SET enabled = $2, updated_at = NOW()
            WHERE chat_id = $1
            RETURNING chat_id, weekday, local_time, timezone, message, enabled
            """,
            chat_id,
            enabled,
        )
        if not record:
            await self.ensure_group(chat_id)
            return await self.set_enabled(chat_id, enabled)
        return _to_config(record)

    async def claim_occurrence(self, chat_id: int, occurrence: date) -> bool:
        record = await self.pool.fetchrow(
            """
            INSERT INTO reminder_occurrences (chat_id, occurrence_key)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            RETURNING chat_id
            """,
            chat_id,
            occurrence,
        )
        return record is not None

    async def release_occurrence(self, chat_id: int, occurrence: date) -> None:
        await self.pool.execute(
            "DELETE FROM reminder_occurrences WHERE chat_id = $1 AND occurrence_key = $2",
            chat_id,
            occurrence,
        )
