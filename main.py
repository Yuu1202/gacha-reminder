import sys
import os
import threading
from app.scheduler import ReminderScheduler
from app.tray import create_tray, run_tray
from app.ui.main_window import MainWindow


def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def ensure_single_instance():
    """Prevent multiple instances using a lock file."""
    lock_path = os.path.join(get_app_dir(), "gacha.lock")
    
    if os.path.exists(lock_path):
        # Check if the PID in the lock file is still running
        try:
            with open(lock_path, "r") as f:
                old_pid = int(f.read().strip())
            # Try to signal the process - if it exists, abort
            import psutil
            if psutil.pid_exists(old_pid):
                print(f"App already running (PID {old_pid}). Exiting.")
                sys.exit(0)
        except Exception:
            pass  # Lock file is stale, continue

    # Write our PID
    with open(lock_path, "w") as f:
        f.write(str(os.getpid()))

    return lock_path


def cleanup_lock(lock_path):
    try:
        os.remove(lock_path)
    except Exception:
        pass


def main():
    # Single instance check
    try:
        import psutil
        lock_path = ensure_single_instance()
    except ImportError:
        # psutil not available, skip single instance check
        lock_path = None

    # Start background scheduler
    scheduler = ReminderScheduler()
    scheduler.start()

    window = None

    def on_hide():
        window.withdraw()

    def on_show(icon=None, item=None):
        window.after(0, window.show)

    def on_exit(icon=None, item=None):
        scheduler.stop()
        tray_icon.stop()
        if lock_path:
            cleanup_lock(lock_path)
        window.after(0, window.destroy)

    tray_icon = create_tray(on_show=on_show, on_exit=on_exit)
    run_tray(tray_icon)

    window = MainWindow(on_hide=on_hide)
    window.mainloop()

    scheduler.stop()
    tray_icon.stop()
    if lock_path:
        cleanup_lock(lock_path)


if __name__ == "__main__":
    main()