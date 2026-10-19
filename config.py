# config.py
# Application configuration settings.
# The database name 'subtrack_db' is hardcoded as a constant across the entire app.

import json
import os

import sys

# Hardcoded database name constant (remains fixed across the application)
DB_NAME = "subtrack_db"

# Determine application base directory (supports both standalone .exe and Python script)
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# File where settings are saved (always alongside the executable or script)
CONFIG_FILE = os.path.join(BASE_DIR, "settings.json")


def get_resource_path(relative_path):
    """
    Returns the absolute path to a bundled resource or asset.
    Handles PyInstaller temp extraction (_MEIPASS) and standard execution.
    """
    if hasattr(sys, "_MEIPASS"):
        bundle_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundle_path):
            return bundle_path

    # Check directory of running executable/script
    direct_path = os.path.join(BASE_DIR, relative_path)
    if os.path.exists(direct_path):
        return direct_path

    # Fallback to source directory
    src_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(src_dir, relative_path)


# Path to application icon
ICON_PATH = get_resource_path("clipboard.ico")

# Default configuration values (2 core configurable options)
DEFAULT_SETTINGS = {
    "mongo_uri": "mongodb://localhost:27017/",
    "reminder_days": 3  # Alert days threshold before renewal
}


def load_settings():
    """
    Loads user settings from settings.json.
    Creates default file if it doesn't exist.
    """
    if not os.path.exists(CONFIG_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(CONFIG_FILE, "r") as file:
            data = json.load(file)
            for key, val in DEFAULT_SETTINGS.items():
                if key not in data:
                    data[key] = val
            return data
    except Exception as error:
        print("[Config] Error loading settings.json, using defaults:", error)
        return DEFAULT_SETTINGS.copy()


def save_settings(settings_dict):
    """
    Saves the settings dictionary to settings.json.
    """
    try:
        with open(CONFIG_FILE, "w") as file:
            json.dump(settings_dict, file, indent=4)
        return True
    except Exception as error:
        print("[Config] Error saving settings.json:", error)
        return False
