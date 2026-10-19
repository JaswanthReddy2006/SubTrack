# gui_analytics.py
# Clean analytics dashboard displaying metrics calculated directly
# via MongoDB aggregation pipelines (Monthly spend, category breakdown, status).

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import os
from config import ICON_PATH
from analytics import (
    get_monthly_total_spend,
    get_spending_by_category,
    get_status_counts,
    get_payment_method_distribution
)


class AnalyticsWindow(ctk.CTkToplevel):
    """
    Analytics & Aggregations Dashboard Window.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.configure(fg_color="#12141A")
        self.title("Analytics & MongoDB Aggregation Pipelines")
        self.geometry("780x680")
        self.resizable(False, False)

        # Set dialog icon
        if os.path.exists(ICON_PATH):
            try:
                self.after(100, lambda: self.iconbitmap(ICON_PATH))
            except Exception:
                pass

        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # Header
        lbl_title = ctk.CTkLabel(
            self,
            text="Analytics & MongoDB Aggregations",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F9FAFB"
        )
        lbl_title.pack(anchor="w", padx=24, pady=(20, 2))

        lbl_desc = ctk.CTkLabel(
            self,
            text="Real-time metrics computed directly inside MongoDB via aggregation stages.",
            font=ctk.CTkFont(size=12),
            text_color="#9CA3AF"
        )
        lbl_desc.pack(anchor="w", padx=24, pady=(0, 14))

        # 1. Summary Metric Cards
        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", padx=24, pady=(0, 12))

        self.card_monthly = self._create_card(cards_row, "Monthly Burn Rate", "$0.00 / mo", 0)
        self.card_yearly = self._create_card(cards_row, "Projected Annual", "$0.00 / yr", 1)
        self.card_active = self._create_card(cards_row, "Active Services", "0 active", 2)

        # 2. Main Container Panel
        panel = ctk.CTkFrame(self, fg_color="#1B1E28", corner_radius=10)
        panel.pack(fill="both", expand=True, padx=24, pady=(0, 12))

        ctk.CTkLabel(
            panel,
            text="Category Spending Breakdown ($group by category)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F9FAFB"
        ).pack(anchor="w", padx=16, pady=(14, 6))

        # Styled Table for Categories
        tree_frame = ctk.CTkFrame(panel, fg_color="transparent")
        tree_frame.pack(fill="x", padx=16, pady=(0, 10))

        columns = ("category", "total_spend", "count", "avg_cost")
        self.tree_cat = ttk.Treeview(tree_frame, columns=columns, show="headings", height=5)
        self.tree_cat.heading("category", text="Category")
        self.tree_cat.heading("total_spend", text="Total Spend ($)")
        self.tree_cat.heading("count", text="Services")
        self.tree_cat.heading("avg_cost", text="Average Cost ($)")

        self.tree_cat.column("category", width=180, anchor="w")
        self.tree_cat.column("total_spend", width=120, anchor="center")
        self.tree_cat.column("count", width=80, anchor="center")
        self.tree_cat.column("avg_cost", width=120, anchor="center")
        self.tree_cat.pack(fill="x")

        # Status and Payment Summary Row
        split_row = ctk.CTkFrame(panel, fg_color="transparent")
        split_row.pack(fill="x", padx=16, pady=(0, 12))

        # Status distribution box
        box_status = ctk.CTkFrame(split_row, fg_color="#12141A", corner_radius=8)
        box_status.pack(side="left", fill="both", expand=True, padx=(0, 6), pady=4)

        ctk.CTkLabel(
            box_status, text="Status Counts",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#9CA3AF"
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_status_details = ctk.CTkLabel(
            box_status, text="Loading...",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#10B981"
        )
        self.lbl_status_details.pack(anchor="w", padx=12, pady=(0, 8))

        # Payment methods box
        box_pay = ctk.CTkFrame(split_row, fg_color="#12141A", corner_radius=8)
        box_pay.pack(side="right", fill="both", expand=True, padx=(6, 0), pady=4)

        ctk.CTkLabel(
            box_pay, text="Payment Methods",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#9CA3AF"
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_pay_details = ctk.CTkLabel(
            box_pay, text="Loading...",
            font=ctk.CTkFont(size=11), text_color="#F9FAFB"
        )
        self.lbl_pay_details.pack(anchor="w", padx=12, pady=(0, 8))

        # 3. Viva Reference Note
        viva_card = ctk.CTkFrame(self, fg_color="#1B1E28", corner_radius=10)
        viva_card.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(
            viva_card,
            text="🎓 CSE Viva Reference — MongoDB Aggregation Stages Used:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#818CF8"
        ).pack(anchor="w", padx=16, pady=(10, 2))

        viva_text = (
            "• Stage 1 ($match): Filters documents with status = 'Active'\n"
            "• Stage 2 ($project): Uses $switch to divide Yearly costs by 12 and Quarterly by 3\n"
            "• Stage 3 ($group): Uses $sum and $avg to aggregate totals per category\n"
            "• Stage 4 ($sort): Orders categories descending by total spend"
        )
        ctk.CTkLabel(
            viva_card, text=viva_text,
            font=ctk.CTkFont(size=10), justify="left", text_color="#9CA3AF"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # Close button
        btn_close = ctk.CTkButton(
            self,
            text="Close Dashboard",
            width=120,
            height=34,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        )
        btn_close.pack(pady=(0, 16))

    def _create_card(self, parent, title, initial_val, col_index):
        card = ctk.CTkFrame(parent, fg_color="#1B1E28", corner_radius=10)
        card.grid(row=0, column=col_index, padx=4, sticky="nsew")
        parent.grid_columnconfigure(col_index, weight=1)

        ctk.CTkLabel(
            card, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color="#9CA3AF"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        lbl_val = ctk.CTkLabel(
            card, text=initial_val, font=ctk.CTkFont(size=18, weight="bold"), text_color="#F9FAFB"
        )
        lbl_val.pack(anchor="w", padx=14, pady=(0, 10))

        return lbl_val

    def _load_data(self):
        """Loads and formats aggregation pipeline results."""
        spend = get_monthly_total_spend()
        monthly = spend.get("monthly_total", 0.0)
        yearly = spend.get("yearly_total", 0.0)
        active_cnt = spend.get("active_count", 0)

        self.card_monthly.configure(text=f"${monthly:,.2f} / mo")
        self.card_yearly.configure(text=f"${yearly:,.2f} / yr")
        self.card_active.configure(text=f"{active_cnt} active")

        # Category table
        for item in self.tree_cat.get_children():
            self.tree_cat.delete(item)

        categories = get_spending_by_category()
        for cat in categories:
            self.tree_cat.insert(
                "",
                "end",
                values=(
                    cat["category"],
                    f"${cat['total_spend']:,.2f}",
                    cat["count"],
                    f"${cat['avg_cost']:,.2f}"
                )
            )

        # Status distribution
        status_map = get_status_counts()
        self.lbl_status_details.configure(
            text=f"Active: {status_map.get('Active', 0)}   |   "
                 f"Paused: {status_map.get('Paused', 0)}   |   "
                 f"Cancelled: {status_map.get('Cancelled', 0)}"
        )

        # Payment method distribution
        pay_methods = get_payment_method_distribution()
        if pay_methods:
            summary = " • ".join([f"{p['method']} ({p['count']})" for p in pay_methods[:3]])
            self.lbl_pay_details.configure(text=summary)
        else:
            self.lbl_pay_details.configure(text="None recorded yet")
