from __future__ import annotations

from dataclasses import dataclass
from datetime import time

DEFAULT_WEEKDAY = 6  # Python weekday: Sunday
DEFAULT_TIME = time(20, 0)
DEFAULT_TIMEZONE = "Europe/Moscow"
DEFAULT_MESSAGE = "Время делиться фотографиями своей недели 📸"
MAX_MESSAGE_LENGTH = 4096


@dataclass(frozen=True, slots=True)
class GroupConfig:
    chat_id: int
    weekday: int
    local_time: time
    timezone: str
    message: str
    enabled: bool
