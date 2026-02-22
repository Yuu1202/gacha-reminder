import os
from plyer import notification


def send_notification(title: str, message: str, icon_path: str = None):
    """Send a Windows toast notification."""
    # plyer on Windows only supports .ico for app_icon
    ico = icon_path if (icon_path and icon_path.lower().endswith(".ico") and os.path.exists(icon_path)) else None
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Gacha Reminder",
            app_icon=ico,
            timeout=8,
        )
    except Exception as e:
        print(f"[Notifier] Failed to send notification: {e}")