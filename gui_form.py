# gui_form.py
# Clean and modern Add / Edit Subscription modal dialog.
# Designed with a deep slate theme, direct field-above-label spacing, and simple actions.

from datetime import date, timedelta
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

import os
from config import ICON_PATH
from models import (
    BILLING_CYCLES,
    CATEGORIES,
    PAYMENT_METHODS,
    STATUSES,
    validate_subscription_data
)
from crud import create_subscription, update_subscription


class SubscriptionFormWindow(ctk.CTkToplevel):
    """
    Modal dialog window for creating or editing a subscription.
    """

    def __init__(self, parent, subscription_doc=None, on_saved_callback=None):
        super().__init__(parent)

        self.subscription_doc = subscription_doc
        self.is_edit_mode = subscription_doc is not None
        self.on_saved_callback = on_saved_callback

        # Window styling
        self.configure(fg_color="#12141A")
        self.title("Edit Subscription" if self.is_edit_mode else "Add Subscription")
        self.geometry("520x620")
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
        if self.is_edit_mode:
            self._prefill_fields()

    def _build_ui(self):
        # Header title
        title_text = "Edit Subscription" if self.is_edit_mode else "New Subscription"
        lbl_title = ctk.CTkLabel(
            self,
            text=title_text,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F9FAFB"
        )
        lbl_title.pack(anchor="w", padx=24, pady=(20, 2))

        lbl_desc = ctk.CTkLabel(
            self,
            text="Enter service pricing and renewal schedule details.",
            font=ctk.CTkFont(size=12),
            text_color="#9CA3AF"
        )
        lbl_desc.pack(anchor="w", padx=24, pady=(0, 14))

        # Main Form Container Card
        card = ctk.CTkFrame(self, fg_color="#1B1E28", corner_radius=10)
        card.pack(fill="both", expand=True, padx=24, pady=0)

        # 1. Service Name
        self._create_label(card, "Service Name *").pack(anchor="w", padx=16, pady=(14, 4))
        self.entry_name = self._create_entry(card, placeholder="e.g. GitHub Copilot, Netflix, AWS")
        self.entry_name.pack(fill="x", padx=16, pady=(0, 10))

        # 2. Cost and Billing Cycle side-by-side
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 10))

        # Cost field
        col_cost = ctk.CTkFrame(row1, fg_color="transparent")
        col_cost.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._create_label(col_cost, "Cost ($) *").pack(anchor="w", pady=(0, 4))
        self.entry_cost = self._create_entry(col_cost, placeholder="e.g. 10.00")
        self.entry_cost.pack(fill="x")

        # Billing cycle field
        col_cycle = ctk.CTkFrame(row1, fg_color="transparent")
        col_cycle.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self._create_label(col_cycle, "Billing Cycle *").pack(anchor="w", pady=(0, 4))
        self.combo_cycle = self._create_option_menu(col_cycle, values=BILLING_CYCLES)
        self.combo_cycle.pack(fill="x")

        # 3. Category and Status side-by-side
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 10))

        col_cat = ctk.CTkFrame(row2, fg_color="transparent")
        col_cat.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._create_label(col_cat, "Category *").pack(anchor="w", pady=(0, 4))
        self.combo_cat = self._create_option_menu(col_cat, values=CATEGORIES)
        self.combo_cat.pack(fill="x")

        col_status = ctk.CTkFrame(row2, fg_color="transparent")
        col_status.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self._create_label(col_status, "Status *").pack(anchor="w", pady=(0, 4))
        self.combo_status = self._create_option_menu(col_status, values=STATUSES)
        self.combo_status.pack(fill="x")

        # 4. Next Renewal Date and Payment Method
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=(0, 10))

        col_date = ctk.CTkFrame(row3, fg_color="transparent")
        col_date.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._create_label(col_date, "Next Renewal (YYYY-MM-DD) *").pack(anchor="w", pady=(0, 4))

        date_inner = ctk.CTkFrame(col_date, fg_color="transparent")
        date_inner.pack(fill="x")

        self.entry_renewal = self._create_entry(date_inner, placeholder="YYYY-MM-DD")
        self.entry_renewal.pack(side="left", fill="x", expand=True)

        btn_today = ctk.CTkButton(
            date_inner, text="Today", width=42, height=32,
            fg_color="#374151", hover_color="#4B5563", text_color="#F9FAFB",
            font=ctk.CTkFont(size=11), command=self._set_today
        )
        btn_today.pack(side="left", padx=3)

        btn_plus1m = ctk.CTkButton(
            date_inner, text="+1M", width=38, height=32,
            fg_color="#374151", hover_color="#4B5563", text_color="#F9FAFB",
            font=ctk.CTkFont(size=11), command=self._set_month_ahead
        )
        btn_plus1m.pack(side="left")

        col_pay = ctk.CTkFrame(row3, fg_color="transparent")
        col_pay.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self._create_label(col_pay, "Payment Method *").pack(anchor="w", pady=(0, 4))
        self.combo_pay = self._create_option_menu(col_pay, values=PAYMENT_METHODS)
        self.combo_pay.pack(fill="x")

        # 5. Optional Notes
        self._create_label(card, "Notes (Optional remarks, plan tier, email)").pack(anchor="w", padx=16, pady=(0, 4))
        self.entry_notes = self._create_entry(card, placeholder="e.g. Pro tier, billed to work card")
        self.entry_notes.pack(fill="x", padx=16, pady=(0, 16))

        # Bottom Action Buttons
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=24, pady=16)

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

        save_title = "Update Plan" if self.is_edit_mode else "Save Plan"
        btn_save = ctk.CTkButton(
            btn_box,
            text=save_title,
            width=110,
            height=36,
            fg_color="#4F46E5",
            hover_color="#4338CA",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.handle_save
        )
        btn_save.pack(side="right")

        # Default renewal date = 30 days from now if adding
        if not self.is_edit_mode:
            default_date = (date.today() + timedelta(days=30)).isoformat()
            self.entry_renewal.insert(0, default_date)

    def _create_label(self, parent, text):
        return ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9CA3AF"
        )

    def _create_entry(self, parent, placeholder=""):
        return ctk.CTkEntry(
            parent,
            height=34,
            placeholder_text=placeholder,
            fg_color="#12141A",
            border_color="#374151",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12)
        )

    def _create_option_menu(self, parent, values):
        menu = ctk.CTkOptionMenu(
            parent,
            values=values,
            height=34,
            fg_color="#12141A",
            button_color="#374151",
            button_hover_color="#4B5563",
            text_color="#F9FAFB",
            dropdown_fg_color="#1B1E28",
            dropdown_text_color="#F9FAFB",
            font=ctk.CTkFont(size=12)
        )
        menu.set(values[0])
        return menu

    def _set_today(self):
        self.entry_renewal.delete(0, "end")
        self.entry_renewal.insert(0, date.today().isoformat())

    def _set_month_ahead(self):
        self.entry_renewal.delete(0, "end")
        self.entry_renewal.insert(0, (date.today() + timedelta(days=30)).isoformat())

    def _prefill_fields(self):
        """Pre-populates inputs with existing subscription document values."""
        doc = self.subscription_doc
        self.entry_name.insert(0, doc.get("service_name", ""))
        self.entry_cost.insert(0, str(doc.get("cost", "")))

        if doc.get("billing_cycle") in BILLING_CYCLES:
            self.combo_cycle.set(doc["billing_cycle"])

        if doc.get("category") in CATEGORIES:
            self.combo_cat.set(doc["category"])

        if doc.get("status") in STATUSES:
            self.combo_status.set(doc["status"])

        if doc.get("payment_method") in PAYMENT_METHODS:
            self.combo_pay.set(doc["payment_method"])

        self.entry_renewal.delete(0, "end")
        self.entry_renewal.insert(0, doc.get("next_renewal", ""))

        self.entry_notes.insert(0, doc.get("notes", ""))

    def handle_save(self):
        """Validates inputs and commits changes to MongoDB."""
        data = {
            "service_name": self.entry_name.get().strip(),
            "cost": self.entry_cost.get().strip(),
            "billing_cycle": self.combo_cycle.get(),
            "category": self.combo_cat.get(),
            "next_renewal": self.entry_renewal.get().strip(),
            "payment_method": self.combo_pay.get(),
            "status": self.combo_status.get(),
            "notes": self.entry_notes.get().strip()
        }

        # Validate with models.py
        is_valid, error_msg = validate_subscription_data(data)
        if not is_valid:
            messagebox.showwarning("Validation Error", error_msg, parent=self)
            return

        # Create or Update in MongoDB
        if self.is_edit_mode:
            sub_id = self.subscription_doc["_id"]
            success, msg = update_subscription(sub_id, data)
        else:
            success, msg = create_subscription(data)

        if success:
            if self.on_saved_callback:
                self.on_saved_callback()
            self.destroy()
        else:
            messagebox.showerror("Database Error", f"Operation failed: {msg}", parent=self)
