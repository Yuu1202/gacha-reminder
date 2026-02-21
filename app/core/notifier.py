from plyer import notification


def send_notification(title: str, message: str, icon_path: str = None):
    """Send a Windows toast notification."""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Gacha Reminder",
            app_icon=icon_path,
            timeout=8,
        )
    except Exception as e:
        print(f"[Notifier] Failed to send notification: {e}")