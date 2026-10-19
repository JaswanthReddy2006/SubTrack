# database.py
# Manages MongoDB connection, server pinging, database existence checking,
# and database initialization using PyMongo.

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import load_settings, DB_NAME

# Global database connection instances
client = None
db = None


def get_client(mongo_uri=None):
    """
    Returns an active MongoClient instance.
    """
    global client

    if client is None or mongo_uri is not None:
        if mongo_uri is None:
            settings = load_settings()
            mongo_uri = settings.get("mongo_uri", "mongodb://localhost:27017/")

        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            # Verify server is alive
            client.admin.command("ping")
        except Exception as error:
            print(f"[Database Error] Could not connect to MongoDB: {error}")
            return None

    return client


def get_db():
    """
    Returns the database instance for the hardcoded DB_NAME ('subtrack_db').
    """
    global db

    if db is None:
        active_client = get_client()
        if active_client is not None:
            db = active_client[DB_NAME]

    return db


def get_collection():
    """
    Returns the 'subscriptions' collection from subtrack_db.
    """
    active_db = get_db()
    if active_db is not None:
        return active_db["subscriptions"]
    return None


def test_connection(mongo_uri):
    """
    Pings MongoDB at the specified URI to test connectivity.
    Returns: (is_connected: bool, message: str)
    """
    try:
        temp_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        temp_client.admin.command("ping")
        server_info = temp_client.server_info()
        version = server_info.get("version", "Unknown")
        temp_client.close()
        return True, f"Connected to MongoDB v{version}"
    except (ConnectionFailure, ServerSelectionTimeoutError) as error:
        return False, f"Connection timed out: {error}"
    except Exception as error:
        return False, f"Connection failed: {error}"


def check_db_exists(mongo_uri=None):
    """
    Checks if the hardcoded database ('subtrack_db') already exists
    on the connected MongoDB instance.
    Returns: True if subtrack_db exists, False otherwise.
    """
    active_client = get_client(mongo_uri)
    if active_client is None:
        return False

    try:
        existing_databases = active_client.list_database_names()
        return DB_NAME in existing_databases
    except Exception as error:
        print(f"[Database Error] Could not list database names: {error}")
        return False


def create_new_database(mongo_uri=None):
    """
    Explicitly creates and initializes the hardcoded 'subtrack_db'
    by creating its 'subscriptions' collection.
    Returns: (success: bool, message: str)
    """
    global db
    active_client = get_client(mongo_uri)
    if active_client is None:
        return False, "Could not connect to MongoDB server."

    try:
        db = active_client[DB_NAME]
        # Creating a collection makes MongoDB allocate the database physically
        if "subscriptions" not in db.list_collection_names():
            db.create_collection("subscriptions")
        return True, f"Database '{DB_NAME}' initialized successfully!"
    except Exception as error:
        return False, f"Failed to initialize database: {error}"


def reconnect(mongo_uri):
    """
    Closes any existing connection and reconnects to a new MongoDB URI.
    The database name remains constant as DB_NAME ('subtrack_db').
    """
    global client, db

    close_connection()

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        db = client[DB_NAME]
        return True, "Reconnected successfully."
    except Exception as error:
        client = None
        db = None
        return False, str(error)


def close_connection():
    """
    Closes the global MongoDB client connection cleanly.
    """
    global client, db
    if client is not None:
        try:
            client.close()
        except Exception:
            pass
        client = None
        db = None
