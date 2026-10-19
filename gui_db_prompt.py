# gui_db_prompt.py
# Modal dialog displayed on application startup if 'subtrack_db' is not found
# on the connected MongoDB instance (detecting a new/empty MongoDB account).
# Gives user 2 clear choices:
# Option 1: Create and initialize 'subtrack_db' now
# Option 2: Change Database URI / Settings

import os
import customtkinter as ctk
from tkinter import messagebox
from config import DB_NAME, ICON_PATH
from database import create_new_database


class NewDatabasePromptWindow(ctk.CTkToplevel):
    """
    Prompt window shown when subtrack_db is not found on MongoDB server.
    """

    def __init__(self, parent, on_created_callback=None, on_change_uri_callback=None):
        super().__init__(parent)

        self.on_created_callback = on_created_callback
        self.on_change_uri_callback = on_change_uri_callback

        self.configure(fg_color="#12141A")
        self.title("New MongoDB Account Detected")
        self.geometry("500x320")
        self.resizable(False, False)

        # Set dialog icon
        if os.path.exists(ICON_PATH):
            try:
                self.after(100, lambda: self.iconbitmap(ICON_PATH))
            except Exception:
                pass

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        # Header title
        lbl_title = ctk.CTkLabel(
            self,
            text="✨ New MongoDB Account Detected",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#F9FAFB"
        )
        lbl_title.pack(anchor="w", padx=24, pady=(20, 4))

        # Description Card Panel
        card = ctk.CTkFrame(self, fg_color="#1B1E28", corner_radius=10)
        card.pack(fill="both", expand=True, padx=24, pady=(6, 16))

        msg = (
            f"The application database '{DB_NAME}' was not found on your\n"
            f"connected MongoDB instance.\n\n"
            f"If this is a fresh MongoDB account, SubTrack can automatically\n"
            f"create and initialize '{DB_NAME}' for you.\n\n"
            f"Or, you can change your MongoDB URI if you meant to connect\n"
            f"to a different account or cluster (e.g. MongoDB Atlas)."
        )

        lbl_msg = ctk.CTkLabel(
            card,
            text=msg,
            font=ctk.CTkFont(size=12),
            text_color="#9CA3AF",
            justify="left"
        )
        lbl_msg.pack(anchor="w", padx=16, pady=16)

        # Two Options Action Buttons
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=24, pady=(0, 20))

        # Option 2: Change Database URI
        btn_change_uri = ctk.CTkButton(
            btn_box,
            text="⚙️ Change Database URI",
            height=38,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.handle_change_uri
        )
        btn_change_uri.pack(side="left")

        # Option 1: Create New Database
        btn_create = ctk.CTkButton(
            btn_box,
            text=f"✨ Create '{DB_NAME}'",
            height=38,
            fg_color="#4F46E5",
            hover_color="#4338CA",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.handle_create_db
        )
        btn_create.pack(side="right")

    def handle_create_db(self):
        """Creates the new database and subscriptions collection."""
        success, msg = create_new_database()
        if success:
            messagebox.showinfo(
                "Database Created",
                f"Successfully initialized '{DB_NAME}' on your MongoDB instance!\n"
                f"You can now start adding your subscriptions.",
                parent=self
            )
            if self.on_created_callback:
                self.on_created_callback()
            self.destroy()
        else:
            messagebox.showerror("Error", f"Failed to create database: {msg}", parent=self)

    def handle_change_uri(self):
        """Closes prompt and opens settings window to change URI."""
        self.destroy()
        if self.on_change_uri_callback:
            self.on_change_uri_callback()
