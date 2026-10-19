# models.py
# This file defines valid choices, schema constraints, and data validation
# for subscriptions according to the project specifications.

from datetime import datetime, date

# Allowed option values (Enums)
BILLING_CYCLES = ["Monthly", "Yearly", "Quarterly"]
CATEGORIES = ["Dev Tools", "Cloud/Host", "Streaming", "Productivity", "Education", "Other"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI / AutoPay", "PayPal", "NetBanking"]
STATUSES = ["Active", "Paused", "Cancelled"]


def validate_subscription_data(data):
    """
    Validates form input data before inserting or updating in MongoDB.
    Returns: (is_valid: bool, error_message: str)
    """
    # 1. Validate service name
    service_name = data.get("service_name", "").strip()
    if not service_name:
        return False, "Service Name cannot be empty."

    # 2. Validate cost (must be a positive number)
    try:
        cost = float(data.get("cost", 0))
        if cost <= 0:
            return False, "Cost must be a positive number greater than 0."
    except (ValueError, TypeError):
        return False, "Cost must be a valid decimal number (e.g., 9.99)."

    # 3. Validate billing cycle
    billing_cycle = data.get("billing_cycle", "")
    if billing_cycle not in BILLING_CYCLES:
        return False, f"Billing cycle must be one of: {', '.join(BILLING_CYCLES)}"

    # 4. Validate category
    category = data.get("category", "")
    if category not in CATEGORIES:
        return False, f"Category must be one of: {', '.join(CATEGORIES)}"

    # 5. Validate next_renewal date (must be YYYY-MM-DD)
    renewal_str = data.get("next_renewal", "").strip()
    if not renewal_str:
        return False, "Next renewal date is required."
    try:
        datetime.strptime(renewal_str, "%Y-%m-%d")
    except ValueError:
        return False, "Next renewal date must be in YYYY-MM-DD format (e.g. 2026-11-20)."

    # 6. Validate payment method
    payment_method = data.get("payment_method", "")
    if payment_method not in PAYMENT_METHODS:
        return False, f"Payment method must be one of: {', '.join(PAYMENT_METHODS)}"

    # 7. Validate status
    status = data.get("status", "")
    if status not in STATUSES:
        return False, f"Status must be one of: {', '.join(STATUSES)}"

    return True, "Valid"


def calculate_days_left(renewal_date_str):
    """
    Calculates how many days remain until the renewal date.
    Returns: integer (negative if overdue, 0 if today, positive if future)
    """
    try:
        target_date = datetime.strptime(renewal_date_str, "%Y-%m-%d").date()
        today = date.today()
        difference = (target_date - today).days
        return difference
    except Exception:
        return 9999
