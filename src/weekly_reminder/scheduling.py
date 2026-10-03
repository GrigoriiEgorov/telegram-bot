from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import GroupConfig


class TimezoneValidationError(ValueError):
    """Raised for an unknown IANA timezone."""


def validate_timezone(name: str) -> str:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise TimezoneValidationError(f"Unknown timezone: {name}") from exc
    return name


def is_due(config: GroupConfig, now: datetime) -> tuple[bool, date | None]:
    """Return whether the current local date has reached this week's occurrence.

    We deliberately do not catch up occurrences from an earlier date after a long
    outage. This prevents a stale reminder arriving days after its intended time.
    """
    if not config.enabled:
        return False, None
    local_now = now.astimezone(ZoneInfo(config.timezone))
    local_time = local_now.time().replace(tzinfo=None)
    if local_now.weekday() != config.weekday or local_time < config.local_time:
        return False, None
    return True, local_now.date()


def next_occurrence(config: GroupConfig, now: datetime) -> datetime:
    local_now = now.astimezone(ZoneInfo(config.timezone))
    days_ahead = (config.weekday - local_now.weekday()) % 7
    if days_ahead == 0 and local_now.time().replace(tzinfo=None) >= config.local_time:
        days_ahead = 7
    target_date = local_now.date()
    from datetime import timedelta

    target_date += timedelta(days=days_ahead)
    return datetime.combine(target_date, config.local_time, ZoneInfo(config.timezone))
