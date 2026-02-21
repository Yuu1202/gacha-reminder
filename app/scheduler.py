import threading
import time
from datetime import datetime
from app.core.calculator import (
    get_current_stamina, get_next_reset, get_time_until_threshold
)
from app.core.notifier import send_notification
from app.core.reminder import StaminaReminder, TicketReminder
import app.storage as storage


class ReminderScheduler:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._check_all()
            except Exception as e:
                print(f"[Scheduler] Error: {e}")
            self._stop_event.wait(60)  # sleep 60 seconds, but stop immediately if flagged

    def _check_all(self):
        reminders = storage.load_reminders()
        changed = False

        for reminder in reminders:
            if isinstance(reminder, StaminaReminder):
                changed |= self._check_stamina(reminder)
            elif isinstance(reminder, TicketReminder):
                changed |= self._check_ticket(reminder)

        if changed:
            storage.save_reminders(reminders)

    def _check_stamina(self, reminder: StaminaReminder) -> bool:
        current = get_current_stamina(reminder)
        changed = False

        for notif in reminder.notifications:
            if notif.type == "at_value":
                if current >= notif.value and not notif.fired:
                    send_notification(
                        title=f"{reminder.name} — {int(notif.value)} reached!",
                        message=f"Current {reminder.name}: {int(current)} / {int(reminder.max_value)}",
                        icon_path=reminder.icon_path
                    )
                    notif.fired = True
                    changed = True
                elif current < notif.value and notif.fired:
                    # Reset fired state when stamina drops below threshold again
                    notif.fired = False
                    changed = True

        return changed

    def _check_ticket(self, reminder: TicketReminder) -> bool:
        now = datetime.now()
        next_reset = get_next_reset(reminder)
        changed = False

        # Check if reset has passed — reset the ticket status
        if reminder.last_reset:
            last_reset_dt = datetime.fromisoformat(reminder.last_reset)
            if now >= next_reset and next_reset > last_reset_dt:
                reminder.is_used = False
                reminder.last_reset = now.isoformat()
                # Also reset all notification fired states
                for notif in reminder.notifications:
                    notif.fired = False
                changed = True
        else:
            reminder.last_reset = now.isoformat()
            changed = True

        if reminder.is_used:
            return changed

        for notif in reminder.notifications:
            if notif.type == "before_reset":
                seconds_until_reset = (next_reset - now).total_seconds()
                trigger_seconds = notif.hours * 3600
                if seconds_until_reset <= trigger_seconds and not notif.fired:
                    hours_left = int(seconds_until_reset // 3600)
                    minutes_left = int((seconds_until_reset % 3600) // 60)
                    time_str = f"{hours_left}h {minutes_left}m" if hours_left else f"{minutes_left}m"
                    send_notification(
                        title=f"{reminder.name} — Don't forget!",
                        message=f"Resets in {time_str}. You haven't used it yet!",
                        icon_path=reminder.icon_path
                    )
                    notif.fired = True
                    changed = True

        return changed