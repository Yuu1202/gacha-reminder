import sys
import customtkinter as ctk
from PIL import Image, ImageTk
import os
from app.core.reminder import StaminaReminder, TicketReminder
from app.core.calculator import (
    get_current_stamina, get_time_until_full, format_timedelta, get_time_until_reset
)
import app.storage as storage


def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


class MainWindow(ctk.CTk):
    def __init__(self, on_hide=None):
        super().__init__()
        self.on_hide = on_hide
        self.title("Gacha Reminder")
        self.geometry("460x580")
        self.resizable(False, True)

     # Taskbar + title bar icon
        ico_path = os.path.join(get_base_path(), "assets", "icon.ico")
        png_path = os.path.join(get_base_path(), "assets", "icon.png")
        if os.path.exists(ico_path):
            self.after(200, lambda: self.iconbitmap(ico_path))
        elif os.path.exists(png_path):
            self._icon_img = ImageTk.PhotoImage(Image.open(png_path))
            self.after(200, lambda: self.iconphoto(True, self._icon_img))

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Unmap>", self._on_minimize)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._build_ui()
        self._refresh()
        self._start_auto_refresh()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(header, text="Gacha Reminder", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="+ Add", width=72, command=self._open_add).pack(side="right")

        # Scrollable reminder list
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _refresh(self):
        # Clear existing cards
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        reminders = storage.load_reminders()
        if not reminders:
            ctk.CTkLabel(
                self.scroll_frame,
                text="No reminders yet.\nClick '+ Add' to get started.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            ).pack(pady=40)
            return

        for reminder in reminders:
            self._build_card(reminder)

    def _build_card(self, reminder):
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=12)
        card.pack(fill="x", pady=6, padx=2)

        # Top row: icon + name + edit button
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))

        # Icon
        if reminder.icon_path and os.path.exists(reminder.icon_path):
            try:
                img = ctk.CTkImage(Image.open(reminder.icon_path), size=(32, 32))
                ctk.CTkLabel(top, image=img, text="").pack(side="left", padx=(0, 8))
            except Exception:
                pass

        # Name + type badge
        name_frame = ctk.CTkFrame(top, fg_color="transparent")
        name_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(name_frame, text=reminder.name, font=ctk.CTkFont(size=15, weight="bold"), anchor="w").pack(anchor="w")
        badge_color = "#1f6aa5" if reminder.type == "stamina" else "#5a3e8c"
        badge_text = "STAMINA" if reminder.type == "stamina" else "TICKET"
        ctk.CTkLabel(name_frame, text=badge_text, font=ctk.CTkFont(size=10), text_color=badge_color, anchor="w").pack(anchor="w")

        ctk.CTkButton(top, text="Edit", width=52, height=28, command=lambda r=reminder: self._open_edit(r)).pack(side="right")

        # Content row
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=12, pady=(0, 10))

        if isinstance(reminder, StaminaReminder):
            self._build_stamina_content(content, reminder)
        elif isinstance(reminder, TicketReminder):
            self._build_ticket_content(content, reminder)

    def _build_stamina_content(self, parent, reminder: StaminaReminder):
        current = get_current_stamina(reminder)
        percent = current / reminder.max_value

        # Value display
        ctk.CTkLabel(
            parent,
            text=f"{int(current)} / {int(reminder.max_value)}",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w")

        # Progress bar
        bar = ctk.CTkProgressBar(parent, width=380, height=10)
        bar.set(min(percent, 1.0))
        bar.pack(anchor="w", pady=(4, 2))

        # Time until full
        if current >= reminder.max_value:
            status = "⚠ FULL — use it now!"
            color = "#ff6b6b"
        else:
            td = get_time_until_full(reminder)
            status = f"Full in {format_timedelta(td)}"
            color = "gray"

        ctk.CTkLabel(parent, text=status, font=ctk.CTkFont(size=12), text_color=color).pack(anchor="w")

    def _build_ticket_content(self, parent, reminder: TicketReminder):
        if reminder.is_used:
            status_text = "✓ Used"
            status_color = "#4caf50"
        else:
            td = get_time_until_reset(reminder)
            status_text = f"⚠ Not used — resets in {format_timedelta(td)}"
            status_color = "#ff9800"

        ctk.CTkLabel(parent, text=status_text, font=ctk.CTkFont(size=15, weight="bold"), text_color=status_color).pack(anchor="w")

        # Quick toggle button
        toggle_text = "Mark as unused" if reminder.is_used else "Mark as used"
        ctk.CTkButton(
            parent, text=toggle_text, width=130, height=28,
            command=lambda r=reminder: self._toggle_ticket(r)
        ).pack(anchor="w", pady=(6, 0))

    def _toggle_ticket(self, reminder: TicketReminder):
        reminders = storage.load_reminders()
        for r in reminders:
            if r.id == reminder.id:
                r.is_used = not r.is_used
                break
        storage.save_reminders(reminders)
        self._refresh()

    def _open_add(self):
        from app.ui.edit_dialog import EditDialog
        EditDialog(self, on_save=self._refresh)

    def _open_edit(self, reminder):
        from app.ui.edit_dialog import EditDialog
        EditDialog(self, reminder=reminder, on_save=self._refresh)

    def _start_auto_refresh(self):
        self._refresh()
        self.after(60000, self._start_auto_refresh)  # refresh UI every minute
        
        
    def _on_close(self):
        # Tombol X -> exit total
        scheduler_ref = None  # exit langsung
        self.destroy()

    def _on_minimize(self, event=None):
        # Tombol minimize -> masuk tray
        if self.on_hide:
            self.on_hide()
        return "break"
            
    def show(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self._refresh()