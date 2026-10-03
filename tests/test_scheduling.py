from datetime import datetime, time, timezone

from weekly_reminder.models import GroupConfig
from weekly_reminder.scheduling import is_due, next_occurrence, validate_timezone


def config(**changes):
    values = dict(
        chat_id=1,
        weekday=6,
        local_time=time(20, 0),
        timezone="Europe/Moscow",
        message="test",
        enabled=True,
    )
    values.update(changes)
    return GroupConfig(**values)


def test_moscow_sunday_schedule_is_due():
    due, occurrence = is_due(config(), datetime(2026, 10, 4, 17, 5, tzinfo=timezone.utc))

    assert due is True
    assert occurrence.isoformat() == "2026-10-04"


def test_schedule_before_time_is_not_due():
    due, occurrence = is_due(config(), datetime(2026, 10, 4, 16, 59, tzinfo=timezone.utc))

    assert due is False
    assert occurrence is None


def test_old_occurrence_is_not_caught_up_on_monday():
    due, occurrence = is_due(config(), datetime(2026, 10, 5, 17, 0, tzinfo=timezone.utc))

    assert due is False
    assert occurrence is None


def test_disabled_group_is_not_due():
    due, occurrence = is_due(
        config(enabled=False), datetime(2026, 10, 4, 17, 5, tzinfo=timezone.utc)
    )

    assert due is False
    assert occurrence is None


def test_next_occurrence_uses_group_timezone():
    result = next_occurrence(config(), datetime(2026, 10, 4, 16, 0, tzinfo=timezone.utc))

    assert result.isoformat() == "2026-10-04T20:00:00+03:00"


def test_timezone_validation():
    assert validate_timezone("Europe/Moscow") == "Europe/Moscow"
