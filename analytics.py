# analytics.py
# This file implements MongoDB Aggregation Pipelines to perform analytics,
# spending calculations, and renewal forecasts.

from datetime import date, timedelta
from database import get_collection


def get_spending_by_category():
    """
    MongoDB Aggregation Pipeline:
    Groups all active subscriptions by 'category' and calculates:
    - total spend in that category
    - number of services
    - average cost per service
    """
    collection = get_collection()
    if collection is None:
        return []

    pipeline = [
        # Stage 1: Filter only 'Active' subscriptions
        {
            "$match": {
                "status": "Active"
            }
        },
        # Stage 2: Group by category and compute metrics
        {
            "$group": {
                "_id": "$category",
                "total_spend": {"$sum": "$cost"},
                "count": {"$sum": 1},
                "avg_cost": {"$avg": "$cost"}
            }
        },
        # Stage 3: Sort by total spending descending
        {
            "$sort": {
                "total_spend": -1
            }
        }
    ]

    try:
        results = list(collection.aggregate(pipeline))
        formatted = []
        for doc in results:
            formatted.append({
                "category": doc["_id"],
                "total_spend": round(doc.get("total_spend", 0.0), 2),
                "count": doc.get("count", 0),
                "avg_cost": round(doc.get("avg_cost", 0.0), 2)
            })
        return formatted
    except Exception as error:
        print("Aggregation error (spending by category):", error)
        return []


def get_monthly_total_spend():
    """
    MongoDB Aggregation Pipeline:
    Normalizes different billing cycles into a uniform Monthly Equivalent Cost:
    - Monthly: cost / 1
    - Quarterly: cost / 3
    - Yearly: cost / 12
    Then sums up the total monthly burn rate.
    """
    collection = get_collection()
    if collection is None:
        return {"monthly_total": 0.0, "yearly_total": 0.0, "active_count": 0}

    pipeline = [
        # Stage 1: Only consider Active subscriptions
        {
            "$match": {
                "status": "Active"
            }
        },
        # Stage 2: Project normalized monthly cost using $switch
        {
            "$project": {
                "service_name": 1,
                "cost": 1,
                "billing_cycle": 1,
                "monthly_cost": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$billing_cycle", "Monthly"]}, "then": "$cost"},
                            {"case": {"$eq": ["$billing_cycle", "Quarterly"]}, "then": {"$divide": ["$cost", 3]}},
                            {"case": {"$eq": ["$billing_cycle", "Yearly"]}, "then": {"$divide": ["$cost", 12]}}
                        ],
                        "default": "$cost"
                    }
                }
            }
        },
        # Stage 3: Sum total monthly cost and count
        {
            "$group": {
                "_id": None,
                "monthly_total": {"$sum": "$monthly_cost"},
                "active_count": {"$sum": 1}
            }
        }
    ]

    try:
        results = list(collection.aggregate(pipeline))
        if results:
            monthly = round(results[0].get("monthly_total", 0.0), 2)
            active_count = results[0].get("active_count", 0)
            yearly = round(monthly * 12, 2)
            return {
                "monthly_total": monthly,
                "yearly_total": yearly,
                "active_count": active_count
            }
        return {"monthly_total": 0.0, "yearly_total": 0.0, "active_count": 0}
    except Exception as error:
        print("Aggregation error (monthly spend):", error)
        return {"monthly_total": 0.0, "yearly_total": 0.0, "active_count": 0}


def get_status_counts():
    """
    MongoDB Aggregation Pipeline:
    Counts how many subscriptions are Active, Paused, or Cancelled.
    """
    collection = get_collection()
    if collection is None:
        return {"Active": 0, "Paused": 0, "Cancelled": 0}

    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        }
    ]

    counts = {"Active": 0, "Paused": 0, "Cancelled": 0}
    try:
        results = list(collection.aggregate(pipeline))
        for item in results:
            status_name = item["_id"]
            if status_name in counts:
                counts[status_name] = item["count"]
        return counts
    except Exception as error:
        print("Aggregation error (status counts):", error)
        return counts


def get_upcoming_renewals(days_ahead=7):
    """
    Finds active subscriptions whose next_renewal falls between today
    and (today + days_ahead).
    """
    collection = get_collection()
    if collection is None:
        return []

    today_str = date.today().isoformat()
    future_str = (date.today() + timedelta(days=days_ahead)).isoformat()

    pipeline = [
        {
            "$match": {
                "status": "Active",
                "next_renewal": {
                    "$gte": today_str,
                    "$lte": future_str
                }
            }
        },
        {
            "$sort": {
                "next_renewal": 1
            }
        }
    ]

    try:
        results = list(collection.aggregate(pipeline))
        for doc in results:
            doc["_id"] = str(doc["_id"])
        return results
    except Exception as error:
        print("Aggregation error (upcoming renewals):", error)
        return []


def get_payment_method_distribution():
    """
    MongoDB Aggregation Pipeline:
    Groups active subscriptions by payment method.
    """
    collection = get_collection()
    if collection is None:
        return []

    pipeline = [
        {"$match": {"status": "Active"}},
        {
            "$group": {
                "_id": "$payment_method",
                "total_spend": {"$sum": "$cost"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]

    try:
        results = list(collection.aggregate(pipeline))
        return [
            {
                "method": doc["_id"],
                "count": doc["count"],
                "total_spend": round(doc["total_spend"], 2)
            }
            for doc in results
        ]
    except Exception as error:
        print("Aggregation error (payment methods):", error)
        return []
