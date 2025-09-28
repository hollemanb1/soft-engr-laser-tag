"""
db_helper.py
------------
PostgreSQL helper for Photon project.
Stores permanent list of players (id + codename).
Scores/teams/hardware IDs are managed in-engine only.
"""

import psycopg2

# Adjust connection parameters to your VM setup
DB_CONFIG = {
    "dbname": "photon",
    "user": "student",
    # "password": "student",  # add if required
    # "host": "localhost",
    # "port": 5432,
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    """Ensure the players table exists."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            codename TEXT UNIQUE NOT NULL
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def add_player(codename: str) -> int:
    """
    Insert a new player into DB.
    Returns the assigned id.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO players (codename)
        VALUES (%s)
        ON CONFLICT (codename) DO NOTHING
        RETURNING id;
        """,
        (codename,),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if row:
        return row[0]

    # If codename already existed, fetch its ID
    existing = get_player_by_name(codename)
    return existing["id"] if existing else None


def search_player(player_id: int):
    """
    Look up a player by ID.
    Returns dict {id, codename} or None.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, codename FROM players WHERE id = %s;",
        (player_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return {"id": row[0], "codename": row[1]}
    return None


def get_player_by_name(codename: str):
    """
    Look up a player by codename.
    Returns dict {id, codename} or None.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, codename FROM players WHERE codename = %s;",
        (codename,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return {"id": row[0], "codename": row[1]}
    return None


def delete_player(player_id: int) -> None:
    """Delete a player by ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM players WHERE id = %s;", (player_id,))
    conn.commit()
    cur.close()
    conn.close()
