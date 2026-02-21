from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class Notification:
    """A single notification rule."""
    type: str          # "at_value" or "before_reset"
    value: float = 0   # for at_value: the stamina threshold
    hours: float = 0   # for before_reset: hours before reset
    fired: bool = False  # has this been fired in current cycle?


@dataclass
class StaminaReminder:
    name: str
    max_value: float
    regen_per_minute: float
    last_known_value: float
    last_updated: str          # ISO format datetime string
    notifications: list[Notification] = field(default_factory=list)
    icon_path: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "stamina"


@dataclass
class TicketReminder:
    name: str
    reset_schedule: str        # "daily", "weekly", "interval"
    reset_time: str            # "HH:MM"
    notifications: list[Notification] = field(default_factory=list)
    reset_day: Optional[str] = None    # "monday", "tuesday", etc. (for weekly)
    reset_interval_days: Optional[int] = None  # for interval type
    is_used: bool = False
    icon_path: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "ticket"
    last_reset: Optional[str] = None   # ISO format, to track cycle