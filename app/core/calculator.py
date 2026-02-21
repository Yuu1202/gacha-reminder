from datetime import datetime, timedelta
from app.core.reminder import StaminaReminder, TicketReminder


def get_current_stamina(reminder: StaminaReminder) -> float:
    """Calculate current stamina based on elapsed time since last update."""
    last_updated = datetime.fromisoformat(reminder.last_updated)
    elapsed_minutes = (datetime.now() - last_updated).total_seconds() / 60
    current = reminder.last_known_value + (elapsed_minutes * reminder.regen_per_minute)
    return min(current, reminder.max_value)


def get_time_until_full(reminder: StaminaReminder) -> timedelta:
    """How long until stamina hits max."""
    current = get_current_stamina(reminder)
    if current >= reminder.max_value:
        return timedelta(0)
    remaining = reminder.max_value - current
    minutes_needed = remaining / reminder.regen_per_minute
    return timedelta(minutes=minutes_needed)


def get_time_until_threshold(reminder: StaminaReminder, threshold: float) -> timedelta:
    """How long until stamina hits a specific threshold."""
    current = get_current_stamina(reminder)
    if current >= threshold:
        return timedelta(0)
    remaining = threshold - current
    minutes_needed = remaining / reminder.regen_per_minute
    return timedelta(minutes=minutes_needed)


def get_next_reset(reminder: TicketReminder) -> datetime:
    """Calculate the next reset datetime for a ticket reminder."""
    now = datetime.now()
    reset_hour, reset_minute = map(int, reminder.reset_time.split(":"))

    if reminder.reset_schedule == "daily":
        candidate = now.replace(hour=reset_hour, minute=reset_minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    elif reminder.reset_schedule == "weekly":
        days_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        target_weekday = days_map[reminder.reset_day.lower()]
        days_ahead = target_weekday - now.weekday()
        if days_ahead < 0:
            days_ahead += 7
        candidate = (now + timedelta(days=days_ahead)).replace(
            hour=reset_hour, minute=reset_minute, second=0, microsecond=0
        )
        if candidate <= now:
            candidate += timedelta(weeks=1)
        return candidate

    elif reminder.reset_schedule == "interval":
        if reminder.last_reset:
            last = datetime.fromisoformat(reminder.last_reset)
            candidate = last + timedelta(days=reminder.reset_interval_days)
            candidate = candidate.replace(hour=reset_hour, minute=reset_minute, second=0, microsecond=0)
            while candidate <= now:
                candidate += timedelta(days=reminder.reset_interval_days)
            return candidate
        else:
            # No last reset recorded, next reset is today at reset_time or tomorrow
            candidate = now.replace(hour=reset_hour, minute=reset_minute, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=reminder.reset_interval_days or 1)
            return candidate


def get_time_until_reset(reminder: TicketReminder) -> timedelta:
    """How long until the next reset."""
    return get_next_reset(reminder) - datetime.now()


def format_timedelta(td: timedelta) -> str:
    """Convert timedelta to readable string like '2h 30m' or '1d 4h'."""
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return "Now"
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")
    return " ".join(parts)