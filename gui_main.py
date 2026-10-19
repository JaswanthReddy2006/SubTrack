# gui_main.py
# Clean, modern desktop GUI for SubTrack — Digital Subscription & Renewal Watcher.
# Built with CustomTkinter and styled ttk.Treeview using a deep slate theme.

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

import os
from config import load_settings, DB_NAME, ICON_PATH
from database import test_connection, check_db_exists
from crud import (
    read_subscriptions,
    read_subscription_by_id,
    delete_subscription
)
from models import calculate_days_left, CATEGORIES, STATUSES
from analytics import get_monthly_total_spend, get_upcoming_renewals
from notifier import check_and_notify_renewals
from gui_settings import SettingsWindow
from gui_form import SubscriptionFormWindow
from gui_analytics import AnalyticsWindow
from gui_db_prompt import NewDatabasePromptWindow
from sample_data import seed_sample_data


class SubTrackApp(ctk.CTk):
    """
    Main Desktop Window for SubTrack.
    """

    def __init__(self):
        super().__init__()

        # Deep slate theme palette
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#12141A")

        self.title("SubTrack — Digital Subscription & Renewal Watcher")
        self.geometry("1120x720")
        self.minsize(980, 600)

        # Set application window and taskbar icon
        if os.path.exists(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except Exception:
                pass

        # Configure comfortable ttk.Treeview styling
        self._setup_table_style()

        # Build UI Sections
        self._build_top_nav()
        self._build_kpi_cards()
        self._build_filter_bar()
        self._build_table_view()
        self._build_bottom_actions()

        # Initial data load
        self.refresh_all_data()

        # Automatically check if subtrack_db exists on the connected MongoDB instance
        self.after(350, self._check_database_on_startup)

    def _check_database_on_startup(self):
        """
        Runs on app startup:
        Checks if 'subtrack_db' exists on the server. If not (new account),
        prompts the user with 2 choices: Create New DB or Change URI.
        """
        settings = load_settings()
        uri = settings.get("mongo_uri", "mongodb://localhost:27017/")

        connected, _ = test_connection(uri)
        if connected:
            exists = check_db_exists(uri)
            if not exists:
                # Open modal asking user to create DB or change URI
                NewDatabasePromptWindow(
                    self,
                    on_created_callback=self.refresh_all_data,
                    on_change_uri_callback=self.open_settings_window
                )

    def _setup_table_style(self):
        """Sets up ttk.Treeview with comfortable row height and deep dark colors."""
        style = ttk.Style()
        style.theme_use("default")

        # Table rows: comfortable 30px rowheight and no harsh borders
        style.configure(
            "Modern.Treeview",
            background="#1B1E28",
            foreground="#F9FAFB",
            rowheight=30,
            fieldbackground="#1B1E28",
            font=("Segoe UI", 10),
            borderwidth=0
        )
        style.map(
            "Modern.Treeview",
            background=[("selected", "#4F46E5")],
            foreground=[("selected", "#FFFFFF")]
        )

        # Table column headings
        style.configure(
            "Modern.Treeview.Heading",
            background="#161922",
            foreground="#9CA3AF",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=(6, 8)
        )
        style.map(
            "Modern.Treeview.Heading",
            background=[("active", "#1E222D")]
        )

    def _build_top_nav(self):
        """Top navigation bar with logo, title, and utility actions."""
        nav = ctk.CTkFrame(self, fg_color="#1B1E28", corner_radius=0, height=56)
        nav.pack(fill="x", side="top")

        # Brand Title
        brand_box = ctk.CTkFrame(nav, fg_color="transparent")
        brand_box.pack(side="left", padx=24, pady=10)

        lbl_logo = ctk.CTkLabel(
            brand_box,
            text="SubTrack",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color="#F9FAFB"
        )
        lbl_logo.pack(side="left")

        lbl_sub = ctk.CTkLabel(
            brand_box,
            text=" • Digital Subscription & Renewal Watcher",
            font=ctk.CTkFont(size=13),
            text_color="#9CA3AF"
        )
        lbl_sub.pack(side="left", padx=4)

        # Right utility controls: Status chip, Analytics, Settings
        right_box = ctk.CTkFrame(nav, fg_color="transparent")
        right_box.pack(side="right", padx=24, pady=10)

        self.lbl_db_badge = ctk.CTkLabel(
            right_box,
            text="🟢 Connected",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#10B981"
        )
        self.lbl_db_badge.pack(side="left", padx=(0, 12))

        btn_analytics = ctk.CTkButton(
            right_box,
            text="📊 Analytics",
            width=96,
            height=32,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.open_analytics_window
        )
        btn_analytics.pack(side="left", padx=4)

        btn_settings = ctk.CTkButton(
            right_box,
            text="⚙️ Settings",
            width=86,
            height=32,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.open_settings_window
        )
        btn_settings.pack(side="left", padx=(4, 0))

    def _build_kpi_cards(self):
        """Header summary cards displaying monthly spend, active count, and upcoming renewals."""
        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", padx=24, pady=(16, 12))

        # 1. Normalized Monthly Spend Card
        self.card_monthly = self._create_card(
            cards_row, "Monthly Spend", "$0.00 / mo", "Normalized via MongoDB pipeline", 0
        )
        # 2. Active Subscriptions Count Card
        self.card_active = self._create_card(
            cards_row, "Active Subscriptions", "0 active", "Currently active services", 1
        )
        # 3. Renewals Due Soon Card
        self.card_renewals = self._create_card(
            cards_row, "Upcoming Renewals", "0 due soon", "Within the next 7 days", 2
        )

    def _create_card(self, parent, label, initial_val, subtext, col_index):
        card = ctk.CTkFrame(parent, fg_color="#1B1E28", corner_radius=10)
        card.grid(row=0, column=col_index, padx=6, sticky="nsew")
        parent.grid_columnconfigure(col_index, weight=1)

        lbl_top = ctk.CTkLabel(
            card, text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#9CA3AF"
        )
        lbl_top.pack(anchor="w", padx=16, pady=(12, 2))

        val_label = ctk.CTkLabel(
            card, text=initial_val,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F9FAFB"
        )
        val_label.pack(anchor="w", padx=16, pady=(0, 2))

        lbl_sub = ctk.CTkLabel(
            card, text=subtext,
            font=ctk.CTkFont(size=11),
            text_color="#6B7280"
        )
        lbl_sub.pack(anchor="w", padx=16, pady=(0, 12))

        return val_label

    def _build_filter_bar(self):
        """Clean search box and category/status filter toolbar."""
        bar = ctk.CTkFrame(self, fg_color="#1B1E28", corner_radius=10)
        bar.pack(fill="x", padx=24, pady=(0, 10))

        # Search field
        lbl_s = ctk.CTkLabel(bar, text="Search:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9CA3AF")
        lbl_s.pack(side="left", padx=(16, 6), pady=10)

        self.entry_search = ctk.CTkEntry(
            bar,
            width=220,
            height=32,
            placeholder_text="Filter name or notes...",
            fg_color="#12141A",
            border_color="#374151",
            text_color="#F9FAFB"
        )
        self.entry_search.pack(side="left", padx=(0, 14), pady=10)
        self.entry_search.bind("<KeyRelease>", lambda event: self.filter_table())

        # Category dropdown
        lbl_c = ctk.CTkLabel(bar, text="Category:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9CA3AF")
        lbl_c.pack(side="left", padx=(0, 6), pady=10)

        self.combo_cat = ctk.CTkOptionMenu(
            bar,
            values=["All Categories"] + CATEGORIES,
            width=140,
            height=32,
            fg_color="#12141A",
            button_color="#374151",
            button_hover_color="#4B5563",
            text_color="#F9FAFB",
            dropdown_fg_color="#1B1E28",
            dropdown_text_color="#F9FAFB",
            command=lambda val: self.filter_table()
        )
        self.combo_cat.set("All Categories")
        self.combo_cat.pack(side="left", padx=(0, 14), pady=10)

        # Status dropdown
        lbl_st = ctk.CTkLabel(bar, text="Status:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9CA3AF")
        lbl_st.pack(side="left", padx=(0, 6), pady=10)

        self.combo_status = ctk.CTkOptionMenu(
            bar,
            values=["All Statuses"] + STATUSES,
            width=130,
            height=32,
            fg_color="#12141A",
            button_color="#374151",
            button_hover_color="#4B5563",
            text_color="#F9FAFB",
            dropdown_fg_color="#1B1E28",
            dropdown_text_color="#F9FAFB",
            command=lambda val: self.filter_table()
        )
        self.combo_status.set("All Statuses")
        self.combo_status.pack(side="left", padx=(0, 14), pady=10)

        # Reset button
        btn_reset = ctk.CTkButton(
            bar,
            text="Reset",
            width=70,
            height=32,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.reset_filters
        )
        btn_reset.pack(side="left", pady=10)

        # Live Demo Push Notification Trigger
        btn_notify_now = ctk.CTkButton(
            bar,
            text="🔔 Check Renewals Now",
            width=165,
            height=32,
            fg_color="#4F46E5",
            hover_color="#4338CA",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.handle_check_renewals_now
        )
        btn_notify_now.pack(side="right", padx=16, pady=10)

    def _build_table_view(self):
        """Table panel containing comfortable ttk.Treeview with aligned columns."""
        panel = ctk.CTkFrame(self, fg_color="#1B1E28", corner_radius=10)
        panel.pack(fill="both", expand=True, padx=24, pady=(0, 10))

        columns = (
            "_id",
            "service_name",
            "cost",
            "billing_cycle",
            "category",
            "next_renewal",
            "days_left",
            "payment_method",
            "status"
        )

        self.tree = ttk.Treeview(
            panel,
            columns=columns,
            show="headings",
            style="Modern.Treeview",
            selectmode="browse"
        )

        # Set Column Headers
        self.tree.heading("_id", text="ID")
        self.tree.heading("service_name", text="Service")
        self.tree.heading("cost", text="Cost")
        self.tree.heading("billing_cycle", text="Cycle")
        self.tree.heading("category", text="Category")
        self.tree.heading("next_renewal", text="Next Renewal")
        self.tree.heading("days_left", text="Days Left")
        self.tree.heading("payment_method", text="Payment Method")
        self.tree.heading("status", text="Status")

        # Column alignments and readable widths
        self.tree.column("_id", width=0, stretch=False)
        self.tree.column("service_name", width=200, anchor="w")
        self.tree.column("cost", width=90, anchor="center")
        self.tree.column("billing_cycle", width=100, anchor="center")
        self.tree.column("category", width=130, anchor="w")
        self.tree.column("next_renewal", width=110, anchor="center")
        self.tree.column("days_left", width=110, anchor="center")
        self.tree.column("payment_method", width=120, anchor="center")
        self.tree.column("status", width=90, anchor="center")

        # Vertical scrollbar
        scrollbar_y = ttk.Scrollbar(panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar_y.pack(side="right", fill="y", pady=8, padx=(0, 6))

        # Color-coded status tags
        self.tree.tag_configure("due_today", foreground="#EF4444", font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("due_soon", foreground="#F59E0B")
        self.tree.tag_configure("active", foreground="#10B981")
        self.tree.tag_configure("paused", foreground="#9CA3AF")
        self.tree.tag_configure("cancelled", foreground="#6B7280")

        # Double click to edit
        self.tree.bind("<Double-1>", lambda event: self.handle_edit())

    def _build_bottom_actions(self):
        """Action toolbar with Add, Edit, Delete, Seed, and Refresh buttons."""
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=24, pady=(0, 16))

        # Main Action: New Subscription
        btn_add = ctk.CTkButton(
            action_bar,
            text="+ New Subscription",
            width=150,
            height=36,
            fg_color="#4F46E5",
            hover_color="#4338CA",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.handle_add
        )
        btn_add.pack(side="left", padx=(0, 8))

        btn_edit = ctk.CTkButton(
            action_bar,
            text="Edit",
            width=80,
            height=36,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.handle_edit
        )
        btn_edit.pack(side="left", padx=4)

        btn_delete = ctk.CTkButton(
            action_bar,
            text="Delete",
            width=80,
            height=36,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.handle_delete
        )
        btn_delete.pack(side="left", padx=4)

        # Right side: Seed Demo Data and Refresh
        btn_refresh = ctk.CTkButton(
            action_bar,
            text="Refresh",
            width=80,
            height=36,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.refresh_all_data
        )
        btn_refresh.pack(side="right")

        btn_seed = ctk.CTkButton(
            action_bar,
            text="🌱 Seed Demo Data",
            width=135,
            height=36,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F9FAFB",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.handle_seed_sample_data
        )
        btn_seed.pack(side="right", padx=8)

        # Status text
        self.lbl_record_count = ctk.CTkLabel(
            action_bar,
            text="0 subscriptions",
            font=ctk.CTkFont(size=12),
            text_color="#6B7280"
        )
        self.lbl_record_count.pack(side="right", padx=16)

    def refresh_all_data(self):
        """Fetches data from MongoDB and updates cards, table, and connection chip."""
        settings = load_settings()
        uri = settings.get("mongo_uri", "mongodb://localhost:27017/")
        # Verify DB connection
        connected, _ = test_connection(uri)
        if connected:
            self.lbl_db_badge.configure(text=f"🟢 {DB_NAME}", text_color="#10B981")
        else:
            self.lbl_db_badge.configure(text="🔴 Offline", text_color="#EF4444")

        # Reload subscription rows
        self.filter_table()

        # Update KPI Summary Cards via Aggregation Pipelines
        spend_data = get_monthly_total_spend()
        monthly_val = spend_data.get("monthly_total", 0.0)
        active_cnt = spend_data.get("active_count", 0)

        upcoming = get_upcoming_renewals(days_ahead=7)

        self.card_monthly.configure(text=f"${monthly_val:,.2f} / mo")
        self.card_active.configure(text=f"{active_cnt} active")
        self.card_renewals.configure(text=f"{len(upcoming)} due soon")

        # Record count
        _, all_subs = read_subscriptions()
        count = len(all_subs)
        self.lbl_record_count.configure(text=f"{count} subscription(s) total")

    def filter_table(self):
        """Filters subscriptions based on search query, category, and status."""
        query = self.entry_search.get().strip()
        cat = self.combo_cat.get()
        stat = self.combo_status.get()

        success, subscriptions = read_subscriptions(query, cat, stat)

        for item in self.tree.get_children():
            self.tree.delete(item)

        if not success:
            return

        settings = load_settings()
        reminder_days = int(settings.get("reminder_days", 3))

        for sub in subscriptions:
            days_left = calculate_days_left(sub.get("next_renewal", ""))

            # Format days left text & tags
            if days_left < 0:
                days_str = f"⚠️ {abs(days_left)}d overdue"
                tag = "due_today"
            elif days_left == 0:
                days_str = "🔔 Today"
                tag = "due_today"
            elif days_left <= reminder_days:
                days_str = f"In {days_left} days"
                tag = "due_soon"
            else:
                days_str = f"{days_left} days"
                tag = "active"

            # Status override for non-active
            if sub.get("status") == "Paused":
                tag = "paused"
            elif sub.get("status") == "Cancelled":
                tag = "cancelled"

            self.tree.insert(
                "",
                "end",
                values=(
                    sub["_id"],
                    sub.get("service_name", ""),
                    f"${float(sub.get('cost', 0)):.2f}",
                    sub.get("billing_cycle", ""),
                    sub.get("category", ""),
                    sub.get("next_renewal", ""),
                    days_str,
                    sub.get("payment_method", ""),
                    sub.get("status", "")
                ),
                tags=(tag,)
            )

    def reset_filters(self):
        """Resets filter values to default and reloads."""
        self.entry_search.delete(0, "end")
        self.combo_cat.set("All Categories")
        self.combo_status.set("All Statuses")
        self.filter_table()

    def _get_selected_sub_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a row in the table first.", parent=self)
            return None
        values = self.tree.item(selected[0], "values")
        return values[0]

    def handle_add(self):
        SubscriptionFormWindow(self, subscription_doc=None, on_saved_callback=self.refresh_all_data)

    def handle_edit(self):
        sub_id = self._get_selected_sub_id()
        if not sub_id:
            return
        doc = read_subscription_by_id(sub_id)
        if not doc:
            messagebox.showerror("Error", "Subscription record not found.", parent=self)
            return
        SubscriptionFormWindow(self, subscription_doc=doc, on_saved_callback=self.refresh_all_data)

    def handle_delete(self):
        sub_id = self._get_selected_sub_id()
        if not sub_id:
            return
        doc = read_subscription_by_id(sub_id)
        name = doc.get("service_name", "this subscription") if doc else "this subscription"

        if messagebox.askyesno("Confirm Delete", f"Delete subscription for '{name}'?", parent=self):
            success, msg = delete_subscription(sub_id)
            if success:
                self.refresh_all_data()
            else:
                messagebox.showerror("Error", msg, parent=self)

    def handle_seed_sample_data(self):
        count = seed_sample_data()
        if count > 0:
            messagebox.showinfo("Demo Data", f"Added {count} sample subscriptions to MongoDB!", parent=self)
        else:
            messagebox.showinfo("Demo Data", "Sample records already exist in your database.", parent=self)
        self.refresh_all_data()

    def handle_check_renewals_now(self):
        """Triggers the notification check immediately for demonstration."""
        due_items = check_and_notify_renewals(manual=True)
        if due_items:
            names = [f"• {item['service_name']} (${item.get('cost', 0):.2f}) - Due: {item.get('next_renewal')}" for item in due_items]
            msg = f"Found {len(due_items)} subscription(s) due soon:\n\n" + "\n".join(names)
            messagebox.showinfo("Renewal Alert Sent", msg, parent=self)
        else:
            messagebox.showinfo("Renewals Check", "No active subscriptions are due within your alert window.", parent=self)

    def open_settings_window(self):
        SettingsWindow(self, on_save_callback=self.refresh_all_data)

    def open_analytics_window(self):
        AnalyticsWindow(self)
