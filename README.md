# SubTrack — Digital Subscription & Renewal Watcher 🔖
> **A Comprehensive, Modern NoSQL Desktop Application for Computer Science & Engineering (CSE)**  
> Built with **Python 3**, **CustomTkinter & ttk**, **PyMongo**, **MongoDB**, and **Plyer**.

---

## 📑 Table of Contents
1. [Project Overview & Problem Statement](#-project-overview--problem-statement)
2. [Technology Stack & System Architecture](#-technology-stack--system-architecture)
3. [End-to-End Execution Flow Logic](#-end-to-end-execution-flow-logic)
4. [Complete File-by-File & Function-by-Function Reference](#-complete-file-by-file--function-by-function-reference)
   - [config.py](#1-configpy)
   - [database.py](#2-databasepy)
   - [models.py](#3-modelspy)
   - [crud.py](#4-crudpy)
   - [analytics.py](#5-analyticspy)
   - [notifier.py](#6-notifierpy)
   - [sample_data.py](#7-sample_datapy)
   - [gui_main.py](#8-gui_mainpy)
   - [gui_form.py](#9-gui_formpy)
   - [gui_analytics.py](#10-gui_analyticspy)
   - [gui_settings.py](#11-gui_settingspy)
   - [gui_db_prompt.py](#12-gui_db_promptpy)
   - [main.py](#13-mainpy)
5. [Database Schema & BSON Specifications](#-database-schema--bson-specifications)
6. [Deep Dive: MongoDB Aggregation Pipelines](#-deep-dive-mongodb-aggregation-pipelines)
7. [Configuration & Local Persistence Architecture](#-configuration--local-persistence-architecture)
8. [Setup, Installation & Demonstration Guide](#-setup-installation--demonstration-guide)
9. [Standalone Windows Executable (.exe) Build & Distribution](#-standalone-windows-executable-exe-build--distribution)

---

## 📌 Project Overview & Problem Statement

Modern users and developers manage dozens of cloud services, SaaS tools, developer environments, and digital streaming platforms. Because these services bill across disparate cycles (Monthly, Quarterly, Annual), calculating realistic monthly burn rates, tracking renewal deadlines, and avoiding unwanted auto-charges is difficult.

**SubTrack** is an enterprise-grade desktop management system providing:
- **Centralized Document Storage:** Eliminates rigid relational tables in favor of flexible, document-based NoSQL storage using MongoDB.
- **Server-Side Aggregations:** Computes monthly equivalent costs and spending breakdowns directly inside the database engine via multi-stage pipelines (`$switch`, `$divide`, `$group`).
- **Resource-Efficient Renewal Alerts:** Employs an on-startup and on-demand push notification dispatch model without background thread polling or CPU-wasting loops.
- **Adaptive Database Detection:** Automatically senses whether the target MongoDB instance (local or MongoDB Atlas Cloud) possesses the required database, offering one-click initialization for new accounts.

---

## 🛠️ Technology Stack & System Architecture

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Programming Language** | Python 3.10+ | Clean syntax, robust standard library, cross-platform stability. |
| **Database Engine** | MongoDB (Local or Atlas) | High-performance document NoSQL database with native aggregation pipelines. |
| **Database Driver** | PyMongo (`MongoClient`) | Official, thread-safe Python MongoDB client driver. |
| **GUI Framework** | CustomTkinter + ttk | Modern Dark-Slate styled interface with rounded panels, custom inputs, and styled Treeviews. |
| **Desktop Notifications** | Plyer (`plyer.notification`) | OS-native push notification dispatch without heavy external daemon dependencies. |
| **Local Config Storage** | JSON (`settings.json`) | Persistent client configuration independent of database state. |

---

## 🔄 End-to-End Execution Flow Logic

```
+-----------------------------------------------------------------------------------+
|                                  python main.py                                   |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 1. Config Loading: load_settings() reads settings.json (URI & reminder threshold) |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 2. Connection Ping: database.test_connection(mongo_uri) pings MongoDB via PyMongo |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 3. Startup Notification: check_and_notify_renewals() queries active subscriptions |
|    due within reminder_days. If matches exist, sends OS desktop notification.     |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 4. GUI Launch: SubTrackApp initializes window, layout, and modern ttk.Treeview.   |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 5. Database Existence Check: after(350ms), checks if 'subtrack_db' exists on host |
|    - If NOT found (new account): Displays NewDatabasePromptWindow modal.          |
|    - If found: Silently continues and populates records.                          |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 6. Main Dashboard State:                                                          |
|    - Computes Monthly Spend card via MongoDB $switch aggregation.                 |
|    - Computes Active Count & Upcoming Renewals (next 7 days).                     |
|    - Loads filtered subscription rows into Treeview with color-coded tags.        |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 7. User Event Loop: Add / Edit / Delete / Search / Filter / Analytics / Settings   |
+-----------------------------------------------------------------------------------+
```

---

## 📂 Complete File-by-File & Function-by-Function Reference

### 1. `config.py`
**Purpose:** Handles loading, creation, and saving of local client configuration settings into `settings.json`. Enforces a permanent constant database name (`subtrack_db`).

* **Constants:**
  * `DB_NAME = "subtrack_db"`: Immutable database name string used globally across all database calls.
  * `CONFIG_FILE = "settings.json"`: Path to the local configuration file.
  * `DEFAULT_SETTINGS = {"mongo_uri": "mongodb://localhost:27017/", "reminder_days": 3}`: Factory default fallback values.
* **Functions:**
  * `load_settings() -> dict`:
    * *Logic:* Checks if `settings.json` exists on disk. If absent, writes `DEFAULT_SETTINGS` to disk and returns a copy. If present, parses JSON; for any missing default key, backfills it with the default value and returns the dictionary. On parse failure, logs error and returns defaults.
  * `save_settings(settings_dict: dict) -> bool`:
    * *Logic:* Accepts a settings dictionary, serializes it with 4-space indentation, and writes it directly to `settings.json`. Returns `True` on success, `False` on exception.

---

### 2. `database.py`
**Purpose:** Manages the low-level MongoDB connection lifecycle, connection pooling, client caching, database existence verification, and database creation.

* **Module Globals:**
  * `client`: Global `MongoClient` instance cache.
  * `db`: Global `Database` object cache.
* **Functions:**
  * `get_client(mongo_uri: str = None) -> MongoClient | None`:
    * *Logic:* Returns an active `MongoClient`. If `client` is `None` or a new URI is supplied, reads URI from `load_settings()`, creates `MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)`, and immediately runs `client.admin.command("ping")` to verify server availability.
  * `get_db() -> Database | None`:
    * *Logic:* Returns the cached database instance `client[DB_NAME]`. If `db` is uninitialized, calls `get_client()` first.
  * `get_collection() -> Collection | None`:
    * *Logic:* Returns the `subscriptions` collection object from `subtrack_db`. Returns `None` if the database is unreachable.
  * `test_connection(mongo_uri: str) -> tuple[bool, str]`:
    * *Logic:* Creates an isolated temporary `MongoClient` with a 2-second timeout, runs `ping`, extracts the server version via `temp_client.server_info()["version"]`, closes the client, and returns `(True, "Connected to MongoDB v<version>")`. Catches timeouts and connection errors to return clean error strings.
  * `check_db_exists(mongo_uri: str = None) -> bool`:
    * *Logic:* Acquires `active_client`, executes `active_client.list_database_names()`, and returns `True` if `DB_NAME` (`"subtrack_db"`) is in the resulting list.
  * `create_new_database(mongo_uri: str = None) -> tuple[bool, str]`:
    * *Logic:* Acquires client, accesses `active_client[DB_NAME]`, inspects `db.list_collection_names()`, and explicitly invokes `db.create_collection("subscriptions")`. This forces MongoDB to allocate physical storage on disk for the database immediately. Sets the global `db` variable.
  * `reconnect(mongo_uri: str) -> tuple[bool, str]`:
    * *Logic:* Calls `close_connection()`, creates a new `MongoClient` with 2-second timeout, tests `ping`, updates global `client` and `db`, and returns `(True, "Reconnected successfully.")`.
  * `close_connection() -> None`:
    * *Logic:* Closes `client.close()` if active, resetting global `client = None` and `db = None`.

---

### 3. `models.py`
**Purpose:** Defines schema choices, allowed values (enums), data validation logic, and date arithmetic.

* **Constants:**
  * `BILLING_CYCLES = ["Monthly", "Yearly", "Quarterly"]`
  * `CATEGORIES = ["Dev Tools", "Cloud/Host", "Streaming", "Productivity", "Education", "Other"]`
  * `PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI / AutoPay", "PayPal", "NetBanking"]`
  * `STATUSES = ["Active", "Paused", "Cancelled"]`
* **Functions:**
  * `validate_subscription_data(data: dict) -> tuple[bool, str]`:
    * *Logic:* Validates subscription dictionaries prior to MongoDB insertion or update:
      1. `service_name`: Must be non-empty after whitespace stripping.
      2. `cost`: Must parse to a float strictly greater than 0.
      3. `billing_cycle`: Must exist within `BILLING_CYCLES`.
      4. `category`: Must exist within `CATEGORIES`.
      5. `next_renewal`: Must parse into valid `datetime` using format `%Y-%m-%d`.
      6. `payment_method`: Must exist within `PAYMENT_METHODS`.
      7. `status`: Must exist within `STATUSES`.
    * Returns `(True, "Valid")` if all rules pass, or `(False, "<Reason>")` on first violation.
  * `calculate_days_left(renewal_date_str: str) -> int`:
    * *Logic:* Parses `renewal_date_str` (`YYYY-MM-DD`) into a date object, subtracts `date.today()`, and returns integer days (`diff.days`). Returns negative numbers for overdue renewals, 0 for today, and 9999 if parsing fails.

---

### 4. `crud.py`
**Purpose:** Implements all Create, Read, Update, and Delete operations interfacing with MongoDB's `subscriptions` collection.

* **Functions:**
  * `create_subscription(data: dict) -> tuple[bool, str]`:
    * *Logic:* Clones input dictionary, converts `cost` to float, injects `created_at = datetime.now(timezone.utc)`, and executes `collection.insert_one(doc)`. Returns `(True, str(inserted_id))` or `(False, error_message)`.
  * `read_subscriptions(search_text: str = None, category: str = None, status: str = None) -> tuple[bool, list]`:
    * *Logic:* Builds a dynamic MongoDB query dictionary:
      - If `search_text` is non-empty: Constructs `$or` with `$regex` (case-insensitive `$options: "i"`) matching either `service_name` or `notes`.
      - If `category` is supplied and not `"All Categories"`: Sets `query["category"] = category`.
      - If `status` is supplied and not `"All Statuses"`: Sets `query["status"] = status`.
      - Executes `collection.find(query).sort("next_renewal", 1)`.
      - Iterates cursor, converts BSON `ObjectId` to string (`doc["_id"] = str(doc["_id"])`), and returns `(True, subscriptions)`.
  * `read_subscription_by_id(sub_id: str) -> dict | None`:
    * *Logic:* Converts string `sub_id` to BSON `ObjectId(sub_id)` and runs `collection.find_one({"_id": ObjectId(sub_id)})`. Converts `_id` to string before returning.
  * `update_subscription(sub_id: str, updated_fields: dict) -> tuple[bool, str]`:
    * *Logic:* Clones fields, converts `cost` to float if present, strips `_id` to prevent immutable field errors, and calls `collection.update_one({"_id": ObjectId(sub_id)}, {"$set": fields})`. Checks `matched_count > 0`. Returns `(True, "Subscription updated successfully.")` or failure message.
  * `delete_subscription(sub_id: str) -> tuple[bool, str]`:
    * *Logic:* Executes `collection.delete_one({"_id": ObjectId(sub_id)})`. Verifies `deleted_count > 0` and returns success status.

---

### 5. `analytics.py`
**Purpose:** Implements MongoDB Aggregation Pipelines to perform server-side financial calculations, category group sums, run rates, and renewal forecasting.

* **Functions:**
  * `get_spending_by_category() -> list[dict]`:
    * *Logic:* Runs a 3-stage aggregation pipeline:
      1. `$match`: Filters `{ "status": "Active" }`.
      2. `$group`: Groups by `_id: "$category"`, computing `total_spend: {"$sum": "$cost"}`, `count: {"$sum": 1}`, and `avg_cost: {"$avg": "$cost"}`.
      3. `$sort`: Orders by `total_spend: -1`.
      - Formats and rounds currency values to 2 decimal places.
  * `get_monthly_total_spend() -> dict`:
    * *Logic:* Runs a 3-stage aggregation pipeline calculating normalized monthly costs:
      1. `$match`: Filters `{ "status": "Active" }`.
      2. `$project`: Evaluates `$switch` branches:
         - If `billing_cycle == "Monthly"` -> `cost`
         - If `billing_cycle == "Quarterly"` -> `cost / 3`
         - If `billing_cycle == "Yearly"` -> `cost / 12`
         - Default -> `cost`
      3. `$group`: Groups with `_id: None`, computing `monthly_total: {"$sum": "$monthly_cost"}` and `active_count: {"$sum": 1}`.
      - Returns `{"monthly_total": float, "yearly_total": float, "active_count": int}` where `yearly_total = monthly_total * 12`.
  * `get_status_counts() -> dict`:
    * *Logic:* Aggregation pipeline grouping documents by `_id: "$status"`, summing occurrences. Returns dictionary with counts for `Active`, `Paused`, and `Cancelled`.
  * `get_upcoming_renewals(days_ahead: int = 7) -> list[dict]`:
    * *Logic:* Matches subscriptions where `status == "Active"` and `next_renewal` is between today's ISO date string and `(today + days_ahead)` ISO date string (`$gte` and `$lte`). Sorts ascending by `next_renewal`.
  * `get_payment_method_distribution() -> list[dict]`:
    * *Logic:* Matches active records, groups by `_id: "$payment_method"`, calculates total cost and count per method, and sorts descending by count.

---

### 6. `notifier.py`
**Purpose:** Dispatches desktop notifications using `plyer` on startup and on user demand. Contains thread excepthooks to prevent OS balloon tip crashes.

* **Helper Logic:**
  * `_safe_thread_excepthook(args)`: Suppresses unhandled Windows-internal shell notification exceptions (`Shell_NotifyIconW`) originating from plyer's asynchronous balloon-tip thread.
* **Functions:**
  * `send_desktop_notification(title: str, message: str) -> bool`:
    * *Logic:* Invokes `plyer.notification.notify(title=title, message=message, app_name="SubTrack", timeout=5)`. Wrapped in `try/except` so absent OS notification daemons never terminate the main process.
  * `get_due_subscriptions(days_ahead: int = None) -> list[dict]`:
    * *Logic:* If `days_ahead` is unspecified, loads `reminder_days` from `settings.json`. Queries MongoDB for active documents where `next_renewal <= cutoff_date`. Computes `days_left` for each document and returns the sorted list.
  * `check_and_notify_renewals(manual: bool = False) -> list[dict]`:
    * *Logic:* Calls `get_due_subscriptions()`. If due records exist:
      - For 1 record: Constructs customized message indicating whether it renews today or in *N* days.
      - For multiple records: Lists the first 3 service names and total count.
      - Calls `send_desktop_notification()`. Returns list of due items.

---

### 7. `sample_data.py`
**Purpose:** Contains realistic mock subscription records for CSE lab demonstrations, testing, and viva presentations.

* **Records:** Includes GitHub Copilot (due in 2 days), Netflix 4K (due today), AWS Cloud Hosting, Spotify Duo, Coursera Plus (Yearly), Notion (Paused), and DigitalOcean (Cancelled).
* **Functions:**
  * `seed_sample_data() -> int`:
    * *Logic:* Reads existing subscriptions via `read_subscriptions()` to avoid duplicate service names. Computes dynamic renewal dates based on `today + timedelta(days=offset)`. Inserts missing records using `create_subscription()`. Returns the count of newly inserted records.

---

### 8. `gui_main.py`
**Purpose:** The central graphical dashboard window. Built with CustomTkinter and modern `ttk.Treeview`.

* **Class: `SubTrackApp(ctk.CTk)`**
  * **Methods:**
    * `__init__()`: Configures `#12141A` dark background, sets title, window geometry (1120x720), initializes styles, constructs UI sections, loads initial data, and schedules database existence check via `self.after(350, self._check_database_on_startup)`.
    * `_check_database_on_startup()`: Pings server; if connected and `check_db_exists()` returns `False`, opens `NewDatabasePromptWindow`.
    * `_setup_table_style()`: Customizes `ttk.Style` for `Modern.Treeview` (`rowheight=30`, font, field background `#1B1E28`, indigo selection `#4F46E5`).
    * `_build_top_nav()`: Renders title, subtitle, database connection pill indicator, "🔔 Check Renewals Now", and "⚙️ Settings" buttons.
    * `_build_kpi_cards()`: Creates 3 top KPI summary cards for Monthly Spend, Active Subscriptions, and Upcoming Renewals.
    * `_build_filter_bar()`: Renders search input entry, Category filter dropdown, Status filter dropdown, and Reset Filters button.
    * `_build_table_view()`: Assembles the `ttk.Treeview` table with columns: Service Name, Category, Cost, Billing Cycle, Next Renewal, Days Left, Status, and Payment Method.
    * `_build_bottom_actions()`: Renders "+ Add Subscription", "✏️ Edit", "🗑️ Delete", "📊 View Analytics", and "🌱 Seed Demo Data" buttons.
    * `refresh_all_data()`: Re-executes `refresh_kpi_cards()` and `refresh_table()`.
    * `refresh_kpi_cards()`: Fetches aggregation results from `get_monthly_total_spend()` and `get_upcoming_renewals()`, updating the card labels.
    * `refresh_table()`: Reads active filter inputs, calls `read_subscriptions()`, formats cost and renewal strings, computes days-left tags, and repopulates the Treeview rows.
    * `open_add_window()`: Instantiates `SubscriptionFormWindow(self, on_saved_callback=self.refresh_all_data)`.
    * `open_edit_window()`: Validates that a row is selected, fetches full document via `read_subscription_by_id()`, and opens `SubscriptionFormWindow` in edit mode.
    * `handle_delete()`: Validates selection, prompts confirmation modal (`messagebox.askyesno`), calls `delete_subscription(sub_id)`, and refreshes data.
    * `open_analytics_window()`: Instantiates `AnalyticsWindow(self)`.
    * `open_settings_window()`: Instantiates `SettingsWindow(self, on_save_callback=self.refresh_all_data)`.
    * `handle_manual_renewal_check()`: Calls `check_and_notify_renewals(manual=True)` and displays an on-screen dialog indicating how many renewals were detected.
    * `handle_seed_sample_data()`: Calls `seed_sample_data()`, alerts the user with the added count, and refreshes the dashboard.
    * `on_filter_changed(*args)`: Event callback triggered when typing in search or changing dropdowns; calls `refresh_table()`.
    * `reset_filters()`: Clears search entry and resets dropdowns to defaults.
    * `update_db_indicator(connected: bool)`: Toggles top-bar badge between green (`Connected to subtrack_db`) and red (`Disconnected`).

---

### 9. `gui_form.py`
**Purpose:** Modal form dialog for adding and editing subscription documents.

* **Class: `SubscriptionFormWindow(ctk.CTkToplevel)`**
  * **Methods:**
    * `__init__(parent, subscription_doc=None, on_saved_callback=None)`: Configures modal state (`transient`, `grab_set`), detects mode (Add vs Edit), constructs form fields, and prefills values if in edit mode.
    * `_build_ui()`: Renders label-above-field input widgets for: Service Name, Cost, Billing Cycle, Category, Next Renewal Date (with quick-select buttons "+1 Mo", "+1 Yr"), Payment Method, Status, and Notes.
    * `_prefill_fields()`: Populates form entries with values from `self.subscription_doc`.
    * `_set_quick_date(days: int)`: Calculates `date.today() + timedelta(days=days)` and writes it into the renewal entry field.
    * `handle_save()`: Collects values from widgets into a dictionary, validates via `validate_subscription_data(data)`. If valid:
      - Calls `update_subscription(sub_id, data)` if editing.
      - Calls `create_subscription(data)` if creating.
      - Executes `on_saved_callback()`, displays feedback, and closes dialog.

---

### 10. `gui_analytics.py`
**Purpose:** Modal dashboard window displaying visual analytics, KPI metrics, category breakdowns, payment methods, and an educational explanation of the MongoDB aggregation pipelines.

* **Class: `AnalyticsWindow(ctk.CTkToplevel)`**
  * **Methods:**
    * `__init__(parent)`: Sets window size (880x640), dark slate background, and initializes tabs/views.
    * `_build_ui()`: Coordinates assembly of the KPI row, spending table, payment methods, and technical pipeline explanations.
    * `_build_summary_row(parent)`: Calls `get_monthly_total_spend()` and `get_status_counts()`, rendering 4 metrics: Monthly Run Rate, Projected Yearly Spend, Active Subscriptions, and Paused/Cancelled counts.
    * `_build_category_table(parent)`: Calls `get_spending_by_category()` and populates a styled breakdown table showing Category, Service Count, Average Cost, and Total Spend.
    * `_build_payment_methods(parent)`: Calls `get_payment_method_distribution()` and displays method badges with counts and total expenditures.
    * `_build_pipeline_info(parent)`: Renders an embedded code panel displaying the exact MongoDB `$switch` pipeline stages to demonstrate server-side data processing.

---

### 11. `gui_settings.py`
**Purpose:** Modal configuration window providing configuration for the two core options (MongoDB Connection URI & Reminder Alert Threshold), with connection testing and instant reconnection.

* **Class: `SettingsWindow(ctk.CTkToplevel)`**
  * **Methods:**
    * `__init__(parent, on_save_callback=None)`: Initializes modal dialog, loads current settings from `load_settings()`, and constructs the UI.
    * `_build_ui()`: Renders immutable database banner (`subtrack_db`), MongoDB URI entry, Reminder Days entry, Test Connection button, Cancel button, and Save Settings button.
    * `handle_test_connection()`: Reads URI entry, invokes `test_connection(uri)` in [database.py](file:///d:/nosql/database.py#L60-L76), and displays a live green success or red failure status label.
    * `handle_save()`: Validates that URI is non-empty and reminder days is a positive integer. Calls `save_settings(new_settings)` to update `settings.json` permanently. Calls `reconnect(uri)` to switch live connections without restarting. Executes callback and closes dialog.

---

### 12. `gui_db_prompt.py`
**Purpose:** Adaptive startup prompt displayed if `subtrack_db` is not detected on the connected MongoDB instance.

* **Class: `NewDatabasePromptWindow(ctk.CTkToplevel)`**
  * **Methods:**
    * `__init__(parent, on_created_callback=None, on_change_uri_callback=None)`: Initializes modal dialog explaining that `subtrack_db` was not found.
    * `_build_ui()`: Renders informational message and 2 clear action buttons:
      1. **"✨ Create 'subtrack_db'"**
      2. **"⚙️ Change Database URI"**
    * `handle_create_db()`: Calls `create_new_database()`, creates the `subscriptions` collection, notifies the user, triggers `on_created_callback()`, and closes the prompt.
    * `handle_change_uri()`: Closes the prompt and opens `SettingsWindow` so the user can point to their desired MongoDB host or Atlas cluster.

---

### 13. `main.py`
**Purpose:** The main application entry point. Coordinates boot sequence, configuration loading, initial health checks, startup notifications, and Tkinter main loop execution.

* **Functions:**
  * `main() -> None`:
    1. Loads configuration via `load_settings()`.
    2. Tests connection via `test_connection(mongo_uri)` and prints status.
    3. Runs single startup renewal check via `check_and_notify_renewals(manual=False)`.
    4. Initializes `SubTrackApp()` desktop window.
    5. Brings window forward using `lift()` and `attributes("-topmost", True)`.
    6. Attaches `WM_DELETE_WINDOW` protocol handler calling `close_connection()`.
    7. Starts Tkinter event loop with `app.mainloop()` inside a safe `KeyboardInterrupt` wrapper.

---

## 🗃️ Database Schema & BSON Specifications

* **Database:** `subtrack_db`
* **Collection:** `subscriptions`

### Document Structure:
```json
{
  "_id": ObjectId("6713dc25a4f1289b4f8a12e4"),
  "service_name": "GitHub Copilot",
  "cost": 10.00,
  "billing_cycle": "Monthly",
  "category": "Dev Tools",
  "next_renewal": "2026-10-21",
  "payment_method": "Credit Card",
  "status": "Active",
  "notes": "Developer AI pair programmer license.",
  "created_at": ISODate("2026-10-19T05:00:00.000Z")
}
```

### Field Definitions & Type Constraints:
| Field Name | BSON Type | Python Type | Constraints / Valid Choices |
| :--- | :--- | :--- | :--- |
| `_id` | `ObjectId` | `str` (in UI) | 12-byte unique BSON identifier generated by MongoDB. |
| `service_name` | `string` | `str` | Required; non-empty string. |
| `cost` | `double` | `float` | Required; strictly greater than `0.0`. |
| `billing_cycle`| `string` | `str` | Must be `"Monthly"`, `"Quarterly"`, or `"Yearly"`. |
| `category` | `string` | `str` | `"Dev Tools"`, `"Cloud/Host"`, `"Streaming"`, `"Productivity"`, `"Education"`, `"Other"`. |
| `next_renewal` | `string` | `str` | ISO date format: `YYYY-MM-DD`. Indexed for sorting. |
| `payment_method`| `string` | `str` | `"Credit Card"`, `"Debit Card"`, `"UPI / AutoPay"`, `"PayPal"`, `"NetBanking"`. |
| `status` | `string` | `str` | `"Active"`, `"Paused"`, or `"Cancelled"`. |
| `notes` | `string` | `str` | Optional descriptive notes (indexed in `$regex` search). |
| `created_at` | `date` | `datetime` | UTC timestamp automatically stamped at creation. |

---

## 🔬 Deep Dive: MongoDB Aggregation Pipelines

### 1. Normalized Monthly Burn Rate Pipeline
Because subscriptions bill at varying frequencies, accurate financial forecasting requires normalizing quarterly costs (divide by 3) and yearly costs (divide by 12) down to monthly equivalents:

```python
[
    # Stage 1: Filter active subscriptions only
    { "$match": { "status": "Active" } },
    
    # Stage 2: Calculate normalized monthly equivalent using $switch & $divide
    {
        "$project": {
            "service_name": 1,
            "cost": 1,
            "billing_cycle": 1,
            "monthly_cost": {
                "$switch": {
                    "branches": [
                        { "case": { "$eq": ["$billing_cycle", "Monthly"] }, "then": "$cost" },
                        { "case": { "$eq": ["$billing_cycle", "Quarterly"] }, "then": { "$divide": ["$cost", 3] } },
                        { "case": { "$eq": ["$billing_cycle", "Yearly"] }, "then": { "$divide": ["$cost", 12] } }
                    ],
                    "default": "$cost"
                }
            }
        }
    },
    
    # Stage 3: Sum normalized costs and count total active items
    {
        "$group": {
            "_id": None,
            "monthly_total": { "$sum": "$monthly_cost" },
            "active_count": { "$sum": 1 }
        }
    }
]
```

### 2. Category Spending Breakdown Pipeline
Groups expenditures by category to show where money is concentrated:
```python
[
    { "$match": { "status": "Active" } },
    {
        "$group": {
            "_id": "$category",
            "total_spend": { "$sum": "$cost" },
            "count": { "$sum": 1 },
            "avg_cost": { "$avg": "$cost" }
        }
    },
    { "$sort": { "total_spend": -1 } }
]
```

---

## ⚙️ Configuration & Local Persistence Architecture

SubTrack maintains a clean architectural separation between **Client Configuration** and **Business Data**:

1. **Client Configuration (`settings.json`):**
   * Stored on the local file system.
   * Preserves:
     - `mongo_uri`: The connection target (allows pointing to local MongoDB or cloud clusters like MongoDB Atlas).
     - `reminder_days`: The alert threshold window (default `3` days).
   * **Persistence:** When changed in the **Settings** dialog, `save_settings()` writes directly to `settings.json` using `json.dump()`. It remains saved permanently across app restarts.
2. **Business Data (`subtrack_db`):**
   * Stored inside MongoDB collections.
   * Subscription records are independent of local client settings and fully centralized.

---

## 🚀 Setup, Installation & Demonstration Guide

### 1. Prerequisites
- **Python 3.10+** installed and added to system PATH.
- **MongoDB Community Server** running locally on port `27017` **OR** a **MongoDB Atlas Cloud Connection URI**.

### 2. Install Dependencies
Open terminal/PowerShell in the project folder and run:
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
python main.py
```

### 4. Step-by-Step Viva & Presentation Demonstration Sequence
1. **Show Startup Flow:** Launch the app from terminal. Point out the terminal log displaying config loading, MongoDB ping, and startup renewal check.
2. **Seed Mock Data:** Click **"🌱 Seed Demo Data"** to automatically insert realistic test records.
3. **Show Header Summary Cards:** Point out the **Monthly Spend** KPI card computing normalized monthly costs.
4. **Demonstrate Dynamic Search & Filtering:** Type in the search box to demonstrate real-time case-insensitive regex search. Filter by Category (`Dev Tools`) or Status (`Active`).
5. **Demonstrate CRUD Operations:**
   - Click **"+ Add Subscription"** to add a record with validation.
   - Double-click a row to edit it.
   - Click **"🗑️ Delete"** to delete a record with confirmation.
6. **Showcase MongoDB Aggregations:** Click **"📊 View Analytics"** to present category totals, average costs, payment method distribution, and the visible `$switch` pipeline.
7. **Demonstrate Desktop Notifications:** Click **"🔔 Check Renewals Now"** to trigger an on-demand OS desktop alert banner.
8. **Demonstrate Settings & Persistence:** Click **"⚙️ Settings"**, test connection, change URI or alert threshold, and demonstrate permanent persistence in `settings.json`.

---

## 📦 Standalone Windows Executable (.exe) Build & Distribution

SubTrack is fully packaged as a self-contained, standalone Windows executable that can be launched directly without needing Python or manual pip package installations on the host system.

### 1. Ready-to-Run Executable Location
The pre-compiled single-file executable is located at:
```
d:\nosql\dist\SubTrack.exe
```

### 2. How to Run the Executable
- **Via File Explorer:** Double-click `SubTrack.exe` located inside the `dist\` folder.
- **Via PowerShell / Command Prompt:**
  ```powershell
  cd d:\nosql
  .\dist\SubTrack.exe
  ```

### 3. Executable Architecture Highlights
- **Application Icon Integration:** Bundles `clipboard.ico` directly into the binary's Windows metadata (`--icon`) and runtime assets (`--add-data`), displaying the icon on window title bars, dialogs, and OS notifications.
- **Single-File Bundling (`--onefile`):** Combines Python runtime 3.13, PyMongo, BSON, CustomTkinter UI themes, and Plyer into a single ~39 MB binary.
- **Windowed No-Console Mode (`--noconsole`):** Runs cleanly as a native desktop GUI app without opening an extraneous black command prompt window.
- **Relocatable Configuration Handling:** [config.py](file:///d:/nosql/config.py) automatically identifies `sys.frozen` execution and maps `settings.json` directly alongside `SubTrack.exe`, preserving custom MongoDB URIs across runs.

### 4. How to Rebuild the Executable (Developer Instructions)
To recompile the `.exe` from source code at any time with the icon:
```bash
python -m PyInstaller --noconsole --onefile --name SubTrack --icon clipboard.ico --add-data "clipboard.ico;." --collect-all customtkinter --collect-all plyer --collect-all pymongo --hidden-import dns main.py
```
The compiled output binary will be regenerated inside the `dist/` directory as `dist\SubTrack.exe`.

