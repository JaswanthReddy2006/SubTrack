# main.py
# Application entry point for SubTrack — Digital Subscription & Renewal Watcher.
# Connects to MongoDB, checks upcoming renewals once on startup, and launches the GUI.

import sys
import os

# Redirect stdout and stderr if None (prevents crashes when running as a windowed/noconsole executable)
if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w")
    except Exception:
        pass
if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w")
    except Exception:
        pass

from config import load_settings, DB_NAME
from database import test_connection, close_connection
from notifier import check_and_notify_renewals
from gui_main import SubTrackApp


def main():
    print("=" * 60)
    print("  SubTrack — Digital Subscription & Renewal Watcher")
    print("  CSE Database Management Project (Python + Tkinter + MongoDB)")
    print("=" * 60)

    # 1. Load application configuration
    settings = load_settings()
    mongo_uri = settings.get("mongo_uri", "mongodb://localhost:27017/")
    print(f"[*] MongoDB URI: {mongo_uri}")
    print(f"[*] Database:    {DB_NAME} (Constant)")

    # 2. Check initial MongoDB connection health
    is_connected, msg = test_connection(mongo_uri)
    if is_connected:
        print(f"[+] {msg}")
    else:
        print(f"[-] MongoDB Warning: {msg}")
        print("    You can update the database URI anytime via the Settings window.")

    # 3. Check upcoming renewals once on startup (due within 3 days)
    print("[*] Checking upcoming renewals on startup...")
    due_items = check_and_notify_renewals(manual=False)
    if due_items:
        print(f"[+] Notification dispatched for {len(due_items)} upcoming renewal(s).")
    else:
        print("[+] No renewals due in the immediate alert window.")

    # 4. Initialize and launch main GUI desktop window
    app = SubTrackApp()

    # Bring window to front
    app.lift()
    app.attributes("-topmost", True)
    app.after_idle(app.attributes, "-topmost", False)
    app.focus_force()

    # Clean shutdown when user closes the window
    def on_closing():
        print("[*] Closing SubTrack...")
        close_connection()
        try:
            app.destroy()
        except Exception:
            pass
        sys.exit(0)

    app.protocol("WM_DELETE_WINDOW", on_closing)

    # Start Tkinter event loop with clean KeyboardInterrupt handling
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[*] Application closed.")
        close_connection()
        sys.exit(0)


if __name__ == "__main__":
    main()
