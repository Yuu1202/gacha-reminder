import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime
import shutil, os
from app.core.reminder import StaminaReminder, TicketReminder, Notification
import app.storage as storage

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets")


class EditDialog(ctk.CTkToplevel):
    def __init__(self, parent, reminder=None, on_save=None):
        super().__init__(parent)
        self.reminder = reminder
        self.on_save = on_save
        self.is_edit = reminder is not None
        self.title("Edit Reminder" if self.is_edit else "Add Reminder")
        self.geometry("480x640")
        self.resizable(False, True)
        self.grab_set()

        self._icon_path = self.reminder.icon_path if self.is_edit else None
        self._notif_rows = []

        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)
        self._scroll = scroll

        # Type selector (only when adding)
        if not self.is_edit:
            ctk.CTkLabel(scroll, text="Type", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            self._type_var = ctk.StringVar(value="stamina")
            type_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            type_frame.pack(fill="x", pady=(4, 12))
            ctk.CTkRadioButton(type_frame, text="Stamina", variable=self._type_var, value="stamina", command=self._rebuild_fields).pack(side="left", padx=(0, 16))
            ctk.CTkRadioButton(type_frame, text="Ticket", variable=self._type_var, value="ticket", command=self._rebuild_fields).pack(side="left")
        else:
            self._type_var = ctk.StringVar(value=self.reminder.type)

        # Name
        ctk.CTkLabel(scroll, text="Name", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self._name_entry = ctk.CTkEntry(scroll, placeholder_text="e.g. Resin, Stamina, Weekly Boss")
        self._name_entry.pack(fill="x", pady=(4, 12))
        if self.is_edit:
            self._name_entry.insert(0, self.reminder.name)

        # Icon
        ctk.CTkLabel(scroll, text="Icon (optional)", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        icon_row = ctk.CTkFrame(scroll, fg_color="transparent")
        icon_row.pack(fill="x", pady=(4, 12))
        self._icon_label = ctk.CTkLabel(icon_row, text=self._icon_path or "No icon selected", text_color="gray", anchor="w")
        self._icon_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(icon_row, text="Browse", width=72, command=self._pick_icon).pack(side="right")

        # Dynamic fields container
        self._fields_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._fields_frame.pack(fill="x")

        self._rebuild_fields()

        # Notifications
        ctk.CTkLabel(scroll, text="Notifications", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(12, 4))
        self._notif_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._notif_frame.pack(fill="x")
        ctk.CTkButton(scroll, text="+ Add Notification", command=self._add_notif_row).pack(anchor="w", pady=(4, 12))

        if self.is_edit:
            for notif in self.reminder.notifications:
                self._add_notif_row(notif)

        # Buttons
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(btn_frame, text="Save", command=self._save).pack(side="left", padx=(0, 8))
        if self.is_edit:
            ctk.CTkButton(btn_frame, text="Delete", fg_color="#c0392b", hover_color="#96281b", command=self._delete).pack(side="left")
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, command=self.destroy).pack(side="right")

    def _rebuild_fields(self):
        for w in self._fields_frame.winfo_children():
            w.destroy()
        t = self._type_var.get()
        if t == "stamina":
            self._build_stamina_fields()
        else:
            self._build_ticket_fields()

    def _build_stamina_fields(self):
        f = self._fields_frame
        r = self.reminder

        ctk.CTkLabel(f, text="Maximum Value", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self._max_entry = ctk.CTkEntry(f, placeholder_text="e.g. 180")
        self._max_entry.pack(fill="x", pady=(4, 12))
        if self.is_edit and isinstance(r, StaminaReminder):
            self._max_entry.insert(0, str(int(r.max_value)))

        ctk.CTkLabel(f, text="Regeneration Rate", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        regen_row = ctk.CTkFrame(f, fg_color="transparent")
        regen_row.pack(fill="x", pady=(4, 12))
        ctk.CTkLabel(regen_row, text="+1 every").pack(side="left")
        self._regen_entry = ctk.CTkEntry(regen_row, width=60, placeholder_text="8")
        self._regen_entry.pack(side="left", padx=6)
        ctk.CTkLabel(regen_row, text="minutes").pack(side="left")
        if self.is_edit and isinstance(r, StaminaReminder):
            minutes_per_one = 1 / r.regen_per_minute
            self._regen_entry.insert(0, str(round(minutes_per_one, 2)))

        ctk.CTkLabel(f, text="Current Value", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self._current_entry = ctk.CTkEntry(f, placeholder_text="How much stamina right now?")
        self._current_entry.pack(fill="x", pady=(4, 12))
        if self.is_edit and isinstance(r, StaminaReminder):
            from app.core.calculator import get_current_stamina
            self._current_entry.insert(0, str(int(get_current_stamina(r))))

    def _build_ticket_fields(self):
        f = self._fields_frame
        r = self.reminder

        ctk.CTkLabel(f, text="Reset Schedule", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self._schedule_var = ctk.StringVar(value="weekly")
        sched_frame = ctk.CTkFrame(f, fg_color="transparent")
        sched_frame.pack(fill="x", pady=(4, 8))
        for val, label in [("daily", "Daily"), ("weekly", "Weekly"), ("interval", "Every X days")]:
            ctk.CTkRadioButton(sched_frame, text=label, variable=self._schedule_var, value=val, command=self._rebuild_schedule_detail).pack(side="left", padx=(0, 12))
        if self.is_edit and isinstance(r, TicketReminder):
            self._schedule_var.set(r.reset_schedule)

        self._schedule_detail_frame = ctk.CTkFrame(f, fg_color="transparent")
        self._schedule_detail_frame.pack(fill="x", pady=(0, 12))
        self._rebuild_schedule_detail()

        ctk.CTkLabel(f, text="Reset Time (HH:MM)", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self._reset_time_entry = ctk.CTkEntry(f, placeholder_text="04:00")
        self._reset_time_entry.pack(fill="x", pady=(4, 12))
        if self.is_edit and isinstance(r, TicketReminder):
            self._reset_time_entry.insert(0, r.reset_time)

    def _rebuild_schedule_detail(self):
        for w in self._schedule_detail_frame.winfo_children():
            w.destroy()
        s = self._schedule_var.get()
        r = self.reminder

        if s == "weekly":
            ctk.CTkLabel(self._schedule_detail_frame, text="Reset Day").pack(side="left", padx=(0, 8))
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            self._day_var = ctk.StringVar(value="Monday")
            if self.is_edit and isinstance(r, TicketReminder) and r.reset_day:
                self._day_var.set(r.reset_day.capitalize())
            ctk.CTkOptionMenu(self._schedule_detail_frame, values=days, variable=self._day_var, width=120).pack(side="left")

        elif s == "interval":
            ctk.CTkLabel(self._schedule_detail_frame, text="Every").pack(side="left", padx=(0, 8))
            self._interval_entry = ctk.CTkEntry(self._schedule_detail_frame, width=50, placeholder_text="7")
            self._interval_entry.pack(side="left")
            ctk.CTkLabel(self._schedule_detail_frame, text="days").pack(side="left", padx=(8, 0))
            if self.is_edit and isinstance(r, TicketReminder) and r.reset_interval_days:
                self._interval_entry.insert(0, str(r.reset_interval_days))

    def _add_notif_row(self, notif=None):
        row_frame = ctk.CTkFrame(self._notif_frame, fg_color=("gray90", "gray20"), corner_radius=8)
        row_frame.pack(fill="x", pady=4)

        type_var = ctk.StringVar(value=notif.type if notif else ("at_value" if self._type_var.get() == "stamina" else "before_reset"))
        value_var = ctk.StringVar(value=str(notif.value if notif else ""))
        hours_var = ctk.StringVar(value=str(notif.hours if notif else ""))

        inner = ctk.CTkFrame(row_frame, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=6)

        if self._type_var.get() == "stamina":
            ctk.CTkLabel(inner, text="Notify when at").pack(side="left")
            ctk.CTkEntry(inner, width=70, textvariable=value_var, placeholder_text="120").pack(side="left", padx=6)
        else:
            ctk.CTkLabel(inner, text="Notify").pack(side="left")
            ctk.CTkEntry(inner, width=50, textvariable=hours_var, placeholder_text="48").pack(side="left", padx=6)
            ctk.CTkLabel(inner, text="hours before reset").pack(side="left")

        def remove():
            row_frame.destroy()
            self._notif_rows.remove(row_data)

        ctk.CTkButton(inner, text="✕", width=28, height=28, fg_color="transparent", command=remove).pack(side="right")

        row_data = {"type": type_var, "value": value_var, "hours": hours_var, "frame": row_frame}
        self._notif_rows.append(row_data)

    def _pick_icon(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.ico *.gif")])
        if path:
            os.makedirs(ASSETS_DIR, exist_ok=True)
            dest = os.path.join(ASSETS_DIR, os.path.basename(path))
            shutil.copy2(path, dest)
            self._icon_path = dest
            self._icon_label.configure(text=os.path.basename(dest), text_color="white")

    def _collect_notifications(self):
        notifs = []
        for row in self._notif_rows:
            try:
                if self._type_var.get() == "stamina":
                    val = float(row["value"].get())
                    notifs.append(Notification(type="at_value", value=val))
                else:
                    hrs = float(row["hours"].get())
                    notifs.append(Notification(type="before_reset", hours=hrs))
            except ValueError:
                continue
        return notifs

    def _save(self):
        name = self._name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required.")
            return

        notifs = self._collect_notifications()
        reminders = storage.load_reminders()

        if self._type_var.get() == "stamina":
            try:
                max_val = float(self._max_entry.get())
                regen_minutes = float(self._regen_entry.get())
                current = float(self._current_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Please fill in all stamina fields with valid numbers.")
                return

            if self.is_edit:
                for r in reminders:
                    if r.id == self.reminder.id:
                        r.name = name
                        r.max_value = max_val
                        r.regen_per_minute = 1 / regen_minutes
                        r.last_known_value = current
                        r.last_updated = datetime.now().isoformat()
                        r.notifications = notifs
                        r.icon_path = self._icon_path
                        break
            else:
                reminders.append(StaminaReminder(
                    name=name,
                    max_value=max_val,
                    regen_per_minute=1 / regen_minutes,
                    last_known_value=current,
                    last_updated=datetime.now().isoformat(),
                    notifications=notifs,
                    icon_path=self._icon_path
                ))

        else:  # ticket
            try:
                reset_time = self._reset_time_entry.get().strip()
                datetime.strptime(reset_time, "%H:%M")
            except ValueError:
                messagebox.showerror("Error", "Reset time must be in HH:MM format.")
                return

            sched = self._schedule_var.get()
            reset_day = None
            interval_days = None

            if sched == "weekly":
                reset_day = self._day_var.get().lower()
            elif sched == "interval":
                try:
                    interval_days = int(self._interval_entry.get())
                except ValueError:
                    messagebox.showerror("Error", "Interval must be a whole number.")
                    return

            if self.is_edit:
                for r in reminders:
                    if r.id == self.reminder.id:
                        r.name = name
                        r.reset_schedule = sched
                        r.reset_time = reset_time
                        r.reset_day = reset_day
                        r.reset_interval_days = interval_days
                        r.notifications = notifs
                        r.icon_path = self._icon_path
                        break
            else:
                reminders.append(TicketReminder(
                    name=name,
                    reset_schedule=sched,
                    reset_time=reset_time,
                    reset_day=reset_day,
                    reset_interval_days=interval_days,
                    notifications=notifs,
                    icon_path=self._icon_path
                ))

        storage.save_reminders(reminders)
        if self.on_save:
            self.on_save()
        self.destroy()

    def _delete(self):
        if not messagebox.askyesno("Delete", f"Delete '{self.reminder.name}'?"):
            return
        reminders = storage.load_reminders()
        reminders = [r for r in reminders if r.id != self.reminder.id]
        storage.save_reminders(reminders)
        if self.on_save:
            self.on_save()
        self.destroy()