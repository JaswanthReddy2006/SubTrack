# gui_settings.py
# Settings window providing the 2 configurable application options:
# 1. MongoDB Connection URI
# 2. Reminder Alert Threshold
# (Database name 'subtrack_db' is fixed and hardcoded)

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import os
from config import load_settings, save_settings, DB_NAME, ICON_PATH
from database import test_connection, reconnect


class SettingsWindow(ctk.CTkToplevel):
    """
    Settings modal dialog for configuring the 2 main options.
    """

    def __init__(self, parent, on_save_callback=None):
        super().__init__(parent)

        self.configure(fg_color="#12141A")
        self.title("SubTrack — Settings")
        self.geometry("520x430")
        self.resizable(False, False)

        # Set dialog icon
        if os.path.exists(ICON_PATH):
            try:
                self.after(100, lambda: self.iconbitmap(ICON_PATH))
            except Exception:
                pass

        self.transient(parent)
        self.grab_set()

        self.on_save_callback = on_save_callback
        self.settings = load_settings()

        self._build_ui()

    def _build_ui(self):
        # Header
        lbl_title = ctk.CTkLabel(
            self,
            text="Application Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F9FAFB"
        )
        lbl_title.pack(anchor="w", padx=24, pady=(20, 2))

        lbl_desc = ctk.CTkLabel(
            self,
            text=f"Configure your connection parameters. Database is fixed to '{DB_NAME}'.",
            font=ctk.CTkFont(size=12),
            text_color="#9CA3AF"
        )
        lbl_desc.pack(anchor="w", padx=24, pady=(0, 14))

        # Main Card Container
        card = ctk.CTkFrame(self, fg_color="#1B1E28", corner_radius=10)
        card.pack(fill="both", expand=True, padx=24, pady=0)

        # Constant Database Indicator Banner
        banner = ctk.CTkFrame(card, fg_color="#12141A", corner_radius=6)
        banner.pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkLabel(
            banner,
            text=f"📌 Database Name:  {DB_NAME}  (Constant)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#818CF8"
        ).pack(anchor="w", padx=12, pady=8)

        # Option 1: MongoDB Connection URI
        ctk.CTkLabel(
            card,
            text="1. MongoDB Connection URI *",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9CA3AF"
        ).pack(anchor="w", padx=16, pady=(0, 4))

        self.entry_uri = ctk.CTkEntry(
            card,
            height=34,
            placeholder_text="e.g. mongodb://localhost:27017/ or Atlas URI",
            fg_color="#12141A",
            border_color="#374151",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12)
        )
        self.entry_uri.insert(0, self.settings.get("mongo_uri", "mongodb://localhost:27017/"))
        self.entry_uri.pack(fill="x", padx=16, pady=(0, 12))

        # Option 2: Reminder Days Threshold
        ctk.CTkLabel(
            card,
            text="2. Reminder Alert Threshold (Days in advance) *",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9CA3AF"
        ).pack(anchor="w", padx=16, pady=(0, 4))

        self.entry_reminder = ctk.CTkEntry(
            card,
            width=120,
            height=34,
            placeholder_text="3",
            fg_color="#12141A",
            border_color="#374151",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12)
        )
        self.entry_reminder.insert(0, str(self.settings.get("reminder_days", 3)))
        self.entry_reminder.pack(anchor="w", padx=16, pady=(0, 8))

        # Status feedback text for connection test
        self.lbl_status = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11))
        self.lbl_status.pack(anchor="w", padx=16, pady=(0, 8))

        # Bottom Action Buttons
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=24, pady=16)

        btn_test = ctk.CTkButton(
            btn_box,
            text="Test Connection",
            height=36,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.handle_test_connection
        )
        btn_test.pack(side="left")

        btn_cancel = ctk.CTkButton(
            btn_box,
            text="Cancel",
            width=90,
            height=36,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        btn_save = ctk.CTkButton(
            btn_box,
            text="Save Settings",
            width=110,
            height=36,
            fg_color="#4F46E5",
            hover_color="#4338CA",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.handle_save
        )
        btn_save.pack(side="right")

    def handle_test_connection(self):
        """Pings the MongoDB server at the entered URI."""
        uri = self.entry_uri.get().strip()
        if not uri:
            self.lbl_status.configure(text="Please enter a MongoDB URI.", text_color="#EF4444")
            return

        self.lbl_status.configure(text="Pinging server...", text_color="#F59E0B")
        self.update_idletasks()

        success, msg = test_connection(uri)
        if success:
            self.lbl_status.configure(text=f"✓ {msg}", text_color="#10B981")
        else:
            self.lbl_status.configure(text=f"✗ {msg}", text_color="#EF4444")

    def handle_save(self):
        """Validates input, saves settings.json, and reconnects."""
        uri = self.entry_uri.get().strip()
        reminder_str = self.entry_reminder.get().strip()

        if not uri:
            messagebox.showwarning("Validation Error", "MongoDB URI cannot be empty.", parent=self)
            return

        try:
            reminder_days = int(reminder_str)
            if reminder_days < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validation Error", "Reminder threshold must be a whole number (e.g. 3).", parent=self)
            return

        # Prepare settings dictionary
        new_settings = {
            "mongo_uri": uri,
            "reminder_days": reminder_days
        }

        if not save_settings(new_settings):
            messagebox.showerror("Error", "Failed to save configuration.", parent=self)
            return

        # Reconnect with constant DB_NAME
        ok, msg = reconnect(uri)
        if not ok:
            messagebox.showwarning("Connection Warning", f"Settings saved, but connection error:\n{msg}", parent=self)
        else:
            messagebox.showinfo("Saved", "Settings saved successfully!", parent=self)

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()
