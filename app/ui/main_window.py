import customtkinter as ctk
from PIL import Image, ImageTk
import os, sys
from datetime import datetime
from app.core.reminder import StaminaReminder, TicketReminder
from app.core.calculator import (
    get_current_stamina, get_time_until_full, format_timedelta, get_time_until_reset
)
import app.storage as storage


def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class MainWindow(ctk.CTk):
    def __init__(self, on_hide=None):
        super().__init__()
        self.on_hide = on_hide
        self.title("Gacha Reminder")
        self.geometry("460x600")
        self.resizable(False, True)

        ico_path = os.path.join(get_base_path(), "assets", "icon.ico")
        png_path = os.path.join(get_base_path(), "assets", "icon.png")
        if os.path.exists(ico_path):
            self.after(200, lambda: self.iconbitmap(ico_path))
        elif os.path.exists(png_path):
            self._icon_img = ImageTk.PhotoImage(Image.open(png_path))
            self.after(200, lambda: self.iconphoto(True, self._icon_img))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Fix: only minimize to tray on actual iconify, not on child window open
        self.bind("<Unmap>", self._on_unmap)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._collapsed = {}
        self._build_ui()
        self._refresh()
        self._start_auto_refresh()

    def _on_unmap(self, event):
        # Only trigger if the event is on the main window itself, not a child
        if event.widget is self:
            if self.state() == "iconic":
                if self.on_hide:
                    self.on_hide()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(header, text="Gacha Reminder", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="+ Add", width=72, command=self._open_add).pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _refresh(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        reminders = storage.load_reminders()
        if not reminders:
            ctk.CTkLabel(
                self.scroll_frame,
                text="No reminders yet.\nClick '+ Add' to get started.",
                font=ctk.CTkFont(size=14), text_color="gray"
            ).pack(pady=40)
            return

        groups = {}
        for r in reminders:
            key = r.group or "Ungrouped"
            groups.setdefault(key, []).append(r)

        sorted_keys = sorted([k for k in groups if k != "Ungrouped"]) + (["Ungrouped"] if "Ungrouped" in groups else [])
        for group_name in sorted_keys:
            self._build_group(group_name, groups[group_name])

    def _build_group(self, group_name, reminders):
        is_collapsed = self._collapsed.get(group_name, False)

        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color=("gray80", "gray25"), corner_radius=8)
        header_frame.pack(fill="x", pady=(8, 2))

        arrow = "▶" if is_collapsed else "▼"
        ctk.CTkButton(
            header_frame,
            text=f"{arrow}  {group_name}  ({len(reminders)})",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=lambda g=group_name: self._toggle_group(g)
        ).pack(fill="x", padx=8, pady=4)

        if not is_collapsed:
            cards_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            cards_frame.pack(fill="x", padx=8)
            for reminder in reminders:
                self._build_card(cards_frame, reminder)

    def _toggle_group(self, group_name):
        self._collapsed[group_name] = not self._collapsed.get(group_name, False)
        self._refresh()

    def _build_card(self, parent, reminder):
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(fill="x", pady=4)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))

        if reminder.icon_path and os.path.exists(reminder.icon_path):
            try:
                img = ctk.CTkImage(Image.open(reminder.icon_path), size=(32, 32))
                ctk.CTkLabel(top, image=img, text="").pack(side="left", padx=(0, 8))
            except Exception:
                pass

        name_frame = ctk.CTkFrame(top, fg_color="transparent")
        name_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(name_frame, text=reminder.name, font=ctk.CTkFont(size=15, weight="bold"), anchor="w").pack(anchor="w")
        badge_color = "#1f6aa5" if reminder.type == "stamina" else "#5a3e8c"
        badge_text = "STAMINA" if reminder.type == "stamina" else "TICKET"
        ctk.CTkLabel(name_frame, text=badge_text, font=ctk.CTkFont(size=10), text_color=badge_color, anchor="w").pack(anchor="w")

        ctk.CTkButton(top, text="Edit", width=52, height=28, command=lambda r=reminder: self._open_edit(r)).pack(side="right")

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=12, pady=(0, 10))

        if isinstance(reminder, StaminaReminder):
            self._build_stamina_content(content, reminder)
        elif isinstance(reminder, TicketReminder):
            self._build_ticket_content(content, reminder)

    # ── STAMINA ──────────────────────────────────────────────────────────────

    def _build_stamina_content(self, parent, reminder: StaminaReminder):
        current = get_current_stamina(reminder)
        percent = current / reminder.max_value

        val_row = ctk.CTkFrame(parent, fg_color="transparent")
        val_row.pack(fill="x")

        val_label = ctk.CTkLabel(
            val_row,
            text=f"{int(current)} / {int(reminder.max_value)}",
            font=ctk.CTkFont(size=22, weight="bold"),
            cursor="hand2"
        )
        val_label.pack(side="left")

        hint = ctk.CTkLabel(val_row, text="  ✎ click to edit", font=ctk.CTkFont(size=11), text_color="gray")
        hint.pack(side="left")

        val_label.bind("<Button-1>", lambda e, r=reminder, p=parent, vl=val_label, h=hint: self._inline_stamina_edit(r, p, vl, h))

        bar = ctk.CTkProgressBar(parent, width=380, height=10)
        bar.set(min(percent, 1.0))
        bar.pack(anchor="w", pady=(4, 2))

        if current >= reminder.max_value:
            status, color = "⚠ FULL — use it now!", "#ff6b6b"
        else:
            status, color = f"Full in {format_timedelta(get_time_until_full(reminder))}", "gray"

        ctk.CTkLabel(parent, text=status, font=ctk.CTkFont(size=12), text_color=color).pack(anchor="w")

    def _inline_stamina_edit(self, reminder, parent, val_label, hint):
        val_label.pack_forget()
        hint.pack_forget()

        row = ctk.CTkFrame(parent, fg_color="transparent")
        # Insert before the progress bar (first child after val_row)
        children = parent.winfo_children()
        if children:
            row.pack(fill="x", before=children[0])
        else:
            row.pack(fill="x")

        entry = ctk.CTkEntry(row, width=80, font=ctk.CTkFont(size=18))
        entry.pack(side="left")
        entry.insert(0, str(int(get_current_stamina(reminder))))
        entry.focus()

        ctk.CTkLabel(row, text=f" / {int(reminder.max_value)}", font=ctk.CTkFont(size=18)).pack(side="left")

        def confirm(event=None):
            try:
                new_val = float(entry.get())
                new_val = max(0, min(new_val, reminder.max_value))
            except ValueError:
                cancel()
                return

            reminders = storage.load_reminders()
            for r in reminders:
                if r.id == reminder.id:
                    r.last_known_value = new_val
                    r.last_updated = datetime.now().isoformat()
                    for notif in r.notifications:
                        if notif.type == "at_value" and new_val < notif.value:
                            notif.fired = False
                    break
            storage.save_reminders(reminders)
            row.destroy()
            self._refresh()

        def cancel(event=None):
            row.destroy()
            val_label.pack(side="left")
            hint.pack(side="left")

        entry.bind("<Return>", confirm)
        entry.bind("<Escape>", cancel)

        ctk.CTkButton(row, text="✓", width=32, height=28, command=confirm).pack(side="left", padx=(6, 2))
        ctk.CTkButton(row, text="✕", width=32, height=28, fg_color="transparent", border_width=1, command=cancel).pack(side="left")

    # ── TICKET ───────────────────────────────────────────────────────────────

    def _build_ticket_content(self, parent, reminder: TicketReminder):
        td = get_time_until_reset(reminder)
        all_used = reminder.current_quantity == 0

        qty_row = ctk.CTkFrame(parent, fg_color="transparent")
        qty_row.pack(fill="x", pady=(0, 4))

        qty_color = "#ff6b6b" if all_used else ("#ff9800" if reminder.current_quantity < reminder.max_quantity else "#4caf50")
        ctk.CTkLabel(
            qty_row,
            text=f"{reminder.current_quantity} / {reminder.max_quantity}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=qty_color
        ).pack(side="left")

        ctk.CTkLabel(qty_row, text=f"  resets in {format_timedelta(td)}", font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")

        if all_used:
            status_text, status_color = "✓ All used", "#4caf50"
        else:
            status_text, status_color = f"⚠ {reminder.current_quantity} remaining — don't forget!", "#ff9800"

        ctk.CTkLabel(parent, text=status_text, font=ctk.CTkFont(size=12), text_color=status_color).pack(anchor="w")

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(anchor="w", pady=(6, 0))

        if not all_used:
            ctk.CTkButton(btn_row, text="Use  −1", width=90, height=28, command=lambda r=reminder: self._use_ticket(r)).pack(side="left", padx=(0, 6))

        if reminder.current_quantity < reminder.max_quantity:
            ctk.CTkButton(btn_row, text="Undo", width=70, height=28, fg_color="transparent", border_width=1, command=lambda r=reminder: self._undo_ticket(r)).pack(side="left")

    def _use_ticket(self, reminder: TicketReminder):
        reminders = storage.load_reminders()
        for r in reminders:
            if r.id == reminder.id:
                if r.current_quantity > 0:
                    r.current_quantity -= 1
                    r.is_used = r.current_quantity == 0
                break
        storage.save_reminders(reminders)
        self._refresh()

    def _undo_ticket(self, reminder: TicketReminder):
        reminders = storage.load_reminders()
        for r in reminders:
            if r.id == reminder.id:
                if r.current_quantity < r.max_quantity:
                    r.current_quantity += 1
                    r.is_used = False
                break
        storage.save_reminders(reminders)
        self._refresh()

    # ── MISC ─────────────────────────────────────────────────────────────────

    def _open_add(self):
        from app.ui.edit_dialog import EditDialog
        EditDialog(self, on_save=self._refresh)

    def _open_edit(self, reminder):
        from app.ui.edit_dialog import EditDialog
        EditDialog(self, reminder=reminder, on_save=self._refresh)

    def _start_auto_refresh(self):
        self._refresh()
        self.after(60000, self._start_auto_refresh)

    def _on_close(self):
        self.destroy()

    def show(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self._refresh()