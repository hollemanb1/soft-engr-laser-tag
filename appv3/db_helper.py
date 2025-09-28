"""
db_helper.py
------------
PostgreSQL helper for Photon project.
Stores permanent list of users (user_id + username).
Scores/teams/hardware IDs are managed in-engine only.
"""

import psycopg2
from psycopg2 import sql

# Adjust connection parameters to your environment
DB_CONFIG = {
    "dbname": "photon",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": 5432,
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    """Ensure the users table exists."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def add_user(username: str) -> int:
    """
    Insert a new user into DB.
    Returns the assigned user_id.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (username)
        VALUES (%s)
        ON CONFLICT (username) DO NOTHING
        RETURNING user_id;
        """,
        (username,),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if row:
        return row[0]

    # If username already existed, fetch its ID
    existing = search_user(username)
    return existing["user_id"] if existing else None


def search_user(username: str):
    """
    Look up a user by username.
    Returns dict {user_id, username} or None.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, username FROM users WHERE username = %s;",
        (username,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return {"user_id": row[0], "username": row[1]}
    return None


def delete_user(user_id: int) -> None:
    """Delete a user by ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = %s;", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
