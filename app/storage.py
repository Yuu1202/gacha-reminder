import json
import os
import sys
from app.core.reminder import StaminaReminder, TicketReminder, Notification


def get_app_dir():
    """Get the directory where the exe (or main.py) lives."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DATA_FILE = os.path.join(get_app_dir(), "data", "reminders.json")


def _ensure_file():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({"reminders": []}, f)


def load_reminders() -> list:
    _ensure_file()
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    reminders = []
    for r in data.get("reminders", []):
        notifs = [Notification(**n) for n in r.get("notifications", [])]
        r["notifications"] = notifs
        if r["type"] == "stamina":
            r.pop("type")
            reminders.append(StaminaReminder(**r))
        elif r["type"] == "ticket":
            r.pop("type")
            reminders.append(TicketReminder(**r))
    return reminders


def save_reminders(reminders: list):
    _ensure_file()
    data = {"reminders": []}
    for r in reminders:
        r_dict = r.__dict__.copy()
        r_dict["notifications"] = [n.__dict__.copy() for n in r.notifications]
        data["reminders"].append(r_dict)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)