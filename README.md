# 🎮 Gacha Reminder

A lightweight Windows system tray app to track your gacha game resources — so your stamina never overflows and your tickets never expire unused.

> **No game integration. No automation. Just you telling the app your current values, and the app doing the math and reminding you at the right time.**

---

## Why This Exists

Most gacha/live-service games have two types of resources that punish inattentive players:

- **Stamina** — regenerates over time, but *stops* once it hits the cap. Every minute you ignore it past full is wasted regen.
- **Tickets / Weekly content** — must be used before a scheduled reset or they're gone forever.

This app tracks both and notifies you before it's too late.

---

## Features

- ⚡ **Stamina tracker** — set your current value, max, and regen rate. App calculates in real time.
- 🎟️ **Ticket tracker** — set reset schedule (daily / weekly / every X days). App reminds you before it resets.
- 🔔 **Custom notifications** — set your own thresholds. "Notify me at 120", "notify me 2 days before reset", etc. Multiple rules per reminder.
- 🖼️ **Custom icons** — upload an icon per reminder so you know at a glance which game it's for.
- 📐 **Auto-recalculate on open** — close the app, come back later, it already knows how much stamina you have now.
- 🗂️ **System tray** — lives quietly in your tray, out of the way.
- 💾 **Local only** — all data stored in a simple JSON file. No internet, no account, no cloud.

---

## How It Works

1. Add a reminder and fill in your resource details
2. App saves your current value + timestamp
3. While the app is open or in the tray, it checks every minute
4. When a threshold is hit → Windows notification pops up
5. When you use your stamina/ticket, open the app and update the value manually

> Notifications only fire while the app is running or minimized to tray. If you fully close it, no notifications — by design, to keep it lightweight.

---

## Reminder Types

### Stamina
For resources that regenerate over time up to a cap.

| Field | Description |
|---|---|
| Name | e.g. "Resin", "AP", "Stamina" |
| Max value | The cap (e.g. 180) |
| Regen rate | +1 every X minutes (e.g. every 8 min) |
| Current value | How much you have right now |
| Notifications | Notify when value reaches X (can add multiple) |

### Ticket
For resources that must be used before a scheduled reset.

| Field | Description |
|---|---|
| Name | e.g. "Weekly Boss", "Arena Ticket" |
| Reset schedule | Daily / Weekly (pick day) / Every X days |
| Reset time | Time of day the reset happens (HH:MM) |
| Notifications | Notify X hours before reset (can add multiple) |

---

## Installation

### Option A — Run from source

**Requirements:** Python 3.10+

```bash
pip install customtkinter pystray plyer pillow
```

```bash
python main.py
```

### Option B — Standalone EXE (Windows)

Download `GachaReminder.exe` from [Releases](#) and double-click. No installation needed.

---

## Build EXE Yourself

```bash
pip install pyinstaller
```

```bash
pyinstaller --onefile --windowed --hidden-import=plyer.platforms.win.notification --hidden-import=pystray._win32 --icon=assets/icon.png --name="GachaReminder" main.py
```

Output will be in the `dist/` folder.

---

## Project Structure

```
gacha-reminder/
├── main.py                   # Entry point
├── app/
│   ├── scheduler.py          # Background thread, checks every 60s
│   ├── storage.py            # Read/write reminders.json
│   ├── tray.py               # System tray icon + menu
│   ├── core/
│   │   ├── reminder.py       # Data models (StaminaReminder, TicketReminder)
│   │   ├── calculator.py     # Time calculations
│   │   └── notifier.py       # Windows notifications via plyer
│   └── ui/
│       ├── main_window.py    # Main window (reminder list)
│       └── edit_dialog.py    # Add/edit reminder dialog
├── data/
│   └── reminders.json        # Your data (auto-created)
└── assets/
    └── icon.png              # App icon (optional)
```

---

## Data Format

All reminders are stored locally in `data/reminders.json`. Example:

```json
{
  "reminders": [
    {
      "type": "stamina",
      "name": "Resin",
      "max_value": 200,
      "regen_per_minute": 0.125,
      "last_known_value": 60,
      "last_updated": "2024-01-15T08:30:00",
      "notifications": [
        { "type": "at_value", "value": 160, "fired": false },
        { "type": "at_value", "value": 200, "fired": false }
      ]
    },
    {
      "type": "ticket",
      "name": "Weekly Boss",
      "reset_schedule": "weekly",
      "reset_day": "monday",
      "reset_time": "04:00",
      "is_used": false,
      "notifications": [
        { "type": "before_reset", "hours": 48, "fired": false }
      ]
    }
  ]
}
```

---

## Performance

| Metric | Value |
|---|---|
| CPU usage (idle) | ~0% |
| RAM usage | ~20–35 MB |
| Check interval | Every 60 seconds |
| Network calls | None |

---

## Platform

Windows only. Tested on Windows 10/11.

---

## Tech Stack

| Component | Library |
|---|---|
| UI | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| System tray | [pystray](https://github.com/moses-palmer/pystray) |
| Notifications | [plyer](https://github.com/kivy/plyer) |
| Images | [Pillow](https://python-pillow.org/) |
| Storage | JSON (built-in) |
| Packaging | [PyInstaller](https://pyinstaller.org/) |

---

## License

Do whatever you want with it. Personal project.
