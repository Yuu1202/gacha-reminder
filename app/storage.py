import json
import os
import sys
import dataclasses
from app.core.reminder import StaminaReminder, TicketReminder, Notification


def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DATA_FILE = os.path.join(get_app_dir(), "data", "reminders.json")


def _ensure_file():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({"reminders": []}, f)


def _filter_fields(cls, data: dict) -> dict:
    """Only keep keys that exist in the dataclass, ignore unknown fields."""
    valid_keys = {f.name for f in dataclasses.fields(cls)}
    return {k: v for k, v in data.items() if k in valid_keys}


def load_reminders() -> list:
    _ensure_file()
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    reminders = []
    for r in data.get("reminders", []):
        notifs = [Notification(**n) for n in r.get("notifications", [])]
        r["notifications"] = notifs

        # Backward compatibility defaults
        r.setdefault("group", None)
        r.setdefault("max_quantity", 1)
        r.setdefault("current_quantity", r.get("max_quantity", 1))

        rtype = r.pop("type")
        if rtype == "stamina":
            reminders.append(StaminaReminder(**_filter_fields(StaminaReminder, r)))
        elif rtype == "ticket":
            reminders.append(TicketReminder(**_filter_fields(TicketReminder, r)))
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