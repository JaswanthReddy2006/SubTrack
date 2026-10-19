# notifier.py
# Simple desktop push notification module using plyer.
# Checks upcoming renewals once on startup or when manually triggered.

import threading
from datetime import date, timedelta
import os
from plyer import notification
from config import load_settings, ICON_PATH
from database import get_collection
from models import calculate_days_left

# Suppress unhandled exceptions originating inside plyer's internal balloon_tip thread on Windows
def _safe_thread_excepthook(args):
    exc_str = str(args.exc_value)
    if "Shell_NotifyIconW" in exc_str or "balloon_tip" in str(args.exc_traceback):
        return
    if hasattr(threading, "__excepthook__"):
        threading.__excepthook__(args)

threading.excepthook = _safe_thread_excepthook


def send_desktop_notification(title, message):
    """
    Sends an OS desktop push notification using plyer with application icon.
    Safely wrapped in try/except so missing drivers never crash the app.
    """
    try:
        kwargs = {
            "title": title,
            "message": message,
            "app_name": "SubTrack",
            "timeout": 5
        }
        if os.path.exists(ICON_PATH):
            kwargs["app_icon"] = ICON_PATH
        notification.notify(**kwargs)
        return True
    except Exception:
        return False


def get_due_subscriptions(days_ahead=None):
    """
    Queries MongoDB for Active subscriptions renewing within the next few days.
    If days_ahead is not passed, it reads reminder_days from settings.json.
    """
    collection = get_collection()
    if collection is None:
        return []

    # Get reminder days threshold from settings (default = 3 days)
    if days_ahead is None:
        settings = load_settings()
        days_ahead = int(settings.get("reminder_days", 3))

    today_str = date.today().isoformat()
    cutoff_str = (date.today() + timedelta(days=days_ahead)).isoformat()

    try:
        # Find active subscriptions where next_renewal is between today and cutoff
        query = {
            "status": "Active",
            "next_renewal": {"$lte": cutoff_str}
        }

        due_list = []
        for doc in collection.find(query).sort("next_renewal", 1):
            doc["_id"] = str(doc["_id"])
            doc["days_left"] = calculate_days_left(doc.get("next_renewal", ""))
            due_list.append(doc)

        return due_list
    except Exception as error:
        print(f"[Notifier Error] Failed to query renewals: {error}")
        return []


def check_and_notify_renewals(manual=False):
    """
    Checks for upcoming renewals and sends a desktop push notification.
    Called once on startup and whenever the user clicks 'Check Renewals Now'.
    """
    due_items = get_due_subscriptions()

    if not due_items:
        if manual:
            print("[Notifier] No upcoming renewals found.")
        return []

    # Build simple notification title and message
    count = len(due_items)
    if count == 1:
        sub = due_items[0]
        name = sub.get("service_name", "Subscription")
        cost = sub.get("cost", 0.0)
        days = sub.get("days_left", 0)

        if days <= 0:
            title = f"SubTrack: {name} Renews Today!"
            msg = f"{name} (${cost:.2f}) is due for renewal today."
        else:
            title = f"SubTrack: {name} Renews Soon"
            msg = f"{name} (${cost:.2f}) renews in {days} day(s)."
    else:
        title = f"SubTrack: {count} Renewals Due Soon"
        names = ", ".join([item.get("service_name", "") for item in due_items[:3]])
        if count > 3:
            names += f" and {count - 3} more"
        msg = f"{names} have renewals coming up within 3 days."

    # Trigger OS desktop notification
    send_desktop_notification(title, msg)
    return due_items
