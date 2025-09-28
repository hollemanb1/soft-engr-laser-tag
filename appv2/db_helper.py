"""
db_helper.py
------------
Temporary JSON-backed DB helper for testing.

Stores:
{
    "001": {"user_id": "001", "username": "Alice"},
    "002": {"user_id": "002", "username": "Bob"}
}

Only tracks user_id + username.
Health and score are managed in-engine only.
"""

import json
import os

DB_FILE = "database.json"


# --- Internal helpers ---
def _load():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def _save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ===============================
# ADD USER
# ===============================
def add_user(user_id: str, username: str) -> None:
    data = _load()
    data[user_id] = {"user_id": user_id, "username": username}
    _save(data)
    print(f"[DB] Added user {username} ({user_id})")


# ===============================
# SEARCH USER
# ===============================
def search_user(username: str):
    data = _load()
    for uid, info in data.items():
        if info["username"] == username:
            return {"user_id": uid, "username": info["username"]}
    return None


# ===============================
# DELETE USER
# ===============================
def delete_user(user_id: str) -> None:
    data = _load()
    if user_id in data:
        uname = data[user_id]["username"]
        del data[user_id]
        _save(data)
        print(f"[DB] Deleted user {uname} ({user_id})")
