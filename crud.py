# crud.py
# This file handles all Database CRUD (Create, Read, Update, Delete) operations
# on the 'subscriptions' MongoDB collection.

from datetime import datetime, timezone
from bson import ObjectId
from database import get_collection


def create_subscription(data):
    """
    Inserts a new subscription document into MongoDB.
    Automatically attaches a created_at ISODate timestamp.
    Returns: (success: bool, result_or_id: str)
    """
    collection = get_collection()
    if collection is None:
        return False, "Database is not connected."

    try:
        # Create a copy so we don't mutate input
        doc = dict(data)
        # Ensure cost is stored as a float number
        doc["cost"] = float(doc["cost"])
        # Add timestamp
        doc["created_at"] = datetime.now(timezone.utc)

        result = collection.insert_one(doc)
        return True, str(result.inserted_id)
    except Exception as error:
        return False, f"Failed to insert subscription: {error}"


def read_subscriptions(search_text=None, category=None, status=None):
    """
    Reads subscriptions from MongoDB matching optional search and filter criteria.
    Results are sorted by next_renewal date in ascending order.
    Returns: (success: bool, list_of_docs)
    """
    collection = get_collection()
    if collection is None:
        return False, []

    try:
        query = {}

        # 1. Search filter: matches service_name or notes (case-insensitive)
        if search_text and search_text.strip():
            text = search_text.strip()
            query["$or"] = [
                {"service_name": {"$regex": text, "$options": "i"}},
                {"notes": {"$regex": text, "$options": "i"}}
            ]

        # 2. Category filter
        if category and category != "All Categories":
            query["category"] = category

        # 3. Status filter
        if status and status != "All Statuses":
            query["status"] = status

        # Query MongoDB and sort by renewal date
        cursor = collection.find(query).sort("next_renewal", 1)

        subscriptions = []
        for doc in cursor:
            # Convert ObjectId to string for easy display in GUI
            doc["_id"] = str(doc["_id"])
            subscriptions.append(doc)

        return True, subscriptions
    except Exception as error:
        print("Error reading subscriptions:", error)
        return False, []


def read_subscription_by_id(sub_id):
    """
    Finds a single subscription document by its MongoDB ObjectId string.
    Returns: doc or None
    """
    collection = get_collection()
    if collection is None:
        return None

    try:
        doc = collection.find_one({"_id": ObjectId(sub_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    except Exception as error:
        print(f"Error fetching subscription {sub_id}:", error)
        return None


def update_subscription(sub_id, updated_fields):
    """
    Updates an existing subscription document in MongoDB by ObjectId.
    Returns: (success: bool, message: str)
    """
    collection = get_collection()
    if collection is None:
        return False, "Database is not connected."

    try:
        fields = dict(updated_fields)
        # Convert cost to float if present
        if "cost" in fields:
            fields["cost"] = float(fields["cost"])

        # Never update the _id field
        if "_id" in fields:
            del fields["_id"]

        result = collection.update_one(
            {"_id": ObjectId(sub_id)},
            {"$set": fields}
        )

        if result.matched_count > 0:
            return True, "Subscription updated successfully."
        else:
            return False, "Subscription not found."
    except Exception as error:
        return False, f"Failed to update subscription: {error}"


def delete_subscription(sub_id):
    """
    Deletes a subscription document from MongoDB by ObjectId.
    Returns: (success: bool, message: str)
    """
    collection = get_collection()
    if collection is None:
        return False, "Database is not connected."

    try:
        result = collection.delete_one({"_id": ObjectId(sub_id)})
        if result.deleted_count > 0:
            return True, "Subscription deleted successfully."
        else:
            return False, "Subscription not found."
    except Exception as error:
        return False, f"Failed to delete subscription: {error}"
