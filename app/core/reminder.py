from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class Notification:
    """A single notification rule."""
    type: str          # "at_value" or "before_reset"
    value: float = 0   # for at_value: the stamina threshold
    hours: float = 0   # for before_reset: hours before reset
    fired: bool = False


@dataclass
class StaminaReminder:
    name: str
    max_value: float
    regen_per_minute: float
    last_known_value: float
    last_updated: str
    notifications: list[Notification] = field(default_factory=list)
    icon_path: Optional[str] = None
    group: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "stamina"


@dataclass
class TicketReminder:
    name: str
    reset_schedule: str
    reset_time: str
    notifications: list[Notification] = field(default_factory=list)
    reset_day: Optional[str] = None
    reset_interval_days: Optional[int] = None
    max_quantity: int = 1
    current_quantity: int = 1
    is_used: bool = False          # True when current_quantity == 0
    icon_path: Optional[str] = None
    group: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "ticket"
    last_reset: Optional[str] = None