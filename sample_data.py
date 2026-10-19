# sample_data.py
# This script populates sample subscription data into MongoDB for demonstration,
# testing, and CSE lab/viva presentations.

from datetime import date, timedelta
from crud import create_subscription, read_subscriptions


SAMPLE_RECORDS = [
    {
        "service_name": "GitHub Copilot",
        "cost": 10.00,
        "billing_cycle": "Monthly",
        "category": "Dev Tools",
        "next_renewal_offset_days": 2,  # Renews in 2 days (triggers alert!)
        "payment_method": "Credit Card",
        "status": "Active",
        "notes": "Student/developer AI pair programming tool."
    },
    {
        "service_name": "Netflix Premium 4K",
        "cost": 19.99,
        "billing_cycle": "Monthly",
        "category": "Streaming",
        "next_renewal_offset_days": 0,  # Renews TODAY (triggers alert!)
        "payment_method": "UPI / AutoPay",
        "status": "Active",
        "notes": "4-screen family streaming plan."
    },
    {
        "service_name": "AWS Cloud Hosting",
        "cost": 45.50,
        "billing_cycle": "Monthly",
        "category": "Cloud/Host",
        "next_renewal_offset_days": 18,
        "payment_method": "Credit Card",
        "status": "Active",
        "notes": "EC2 t3.medium instance & S3 backup storage."
    },
    {
        "service_name": "Spotify Duo",
        "cost": 14.99,
        "billing_cycle": "Monthly",
        "category": "Streaming",
        "next_renewal_offset_days": 4,  # Renews in 4 days
        "payment_method": "Debit Card",
        "status": "Active",
        "notes": "Music streaming for 2 accounts."
    },
    {
        "service_name": "Coursera Plus",
        "cost": 399.00,
        "billing_cycle": "Yearly",
        "category": "Education",
        "next_renewal_offset_days": 60,
        "payment_method": "PayPal",
        "status": "Active",
        "notes": "Annual pass for computer science certifications."
    },
    {
        "service_name": "Notion Plus & AI",
        "cost": 10.00,
        "billing_cycle": "Monthly",
        "category": "Productivity",
        "next_renewal_offset_days": 25,
        "payment_method": "Credit Card",
        "status": "Paused",
        "notes": "Paused during semester exam break."
    },
    {
        "service_name": "DigitalOcean Droplet",
        "cost": 12.00,
        "billing_cycle": "Monthly",
        "category": "Cloud/Host",
        "next_renewal_offset_days": 10,
        "payment_method": "PayPal",
        "status": "Cancelled",
        "notes": "Migrated database to local cluster; service cancelled."
    }
]


def seed_sample_data():
    """
    Seeds mock subscription records into MongoDB.
    Returns: count of newly added records.
    """
    today = date.today()
    added_count = 0

    # Fetch existing to avoid duplicate service names
    _, existing_docs = read_subscriptions()
    existing_names = {doc.get("service_name", "").lower() for doc in existing_docs}

    for item in SAMPLE_RECORDS:
        if item["service_name"].lower() in existing_names:
            continue

        offset = item.pop("next_renewal_offset_days")
        item["next_renewal"] = (today + timedelta(days=offset)).isoformat()

        success, _ = create_subscription(item)
        if success:
            added_count += 1

    return added_count


if __name__ == "__main__":
    print("Seeding sample subscription data...")
    count = seed_sample_data()
    print(f"Successfully seeded {count} new subscriptions into MongoDB!")
