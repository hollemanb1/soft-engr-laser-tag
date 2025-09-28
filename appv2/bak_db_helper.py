"""
db_helper.py
------------
Database interface layer.
These functions are called by the engine or UI to interact with the database.

Mark: You can hand this to your DB teammate.
They just need to implement each function with real database logic
(Postgres now, JSON fallback if needed).
"""

# ===============================
# ADD USER
# ===============================
def add_user(user_id: str, username: str) -> None:
    """
    Called by: Engine (when a "join" event is processed).
    Input: user_id (string), username (string).
    Action: Insert new user into DB with default score=0, health=100.
    Returns: nothing (but should raise/log errors if insert fails).
    """


# ===============================
# SEARCH USER
# ===============================
def search_user(username: str) -> dict | None:
    """
    Called by: UI (settings screen "Search" button).
    Input: username (string).
    Action: Look up a user in the DB.
    Returns: dict with {"user_id": ..., "username": ..., "score": ..., "health": ...}
             OR None if not found.
    """


# ===============================
# GET SCORES (FOR SCOREBOARD)
# ===============================
def get_all_scores() -> list[dict]:
    """
    Called by: UI (scoreboard refresh).
    Input: none.
    Action: Query DB for all current players and their scores.
    Returns: list of dicts, each like:
             { "user_id": "001", "username": "Alice", "score": 50, "health": 80 }
    """


# ===============================
# DELETE USER
# ===============================
def delete_user(user_id: str) -> None:
    """
    Called by: Engine (when a "delete" event is processed).
    Input: user_id (string).
    Action: Remove this user from the DB.
    Returns: nothing.
    """


# ===============================
# UPDATE SCORE / HEALTH
# ===============================
def update_score(id1: str, id2: str, score_update: int, health_update: int) -> None:
    """
    Called by: Engine (when a "hit" event is processed).
    Input:
      id1 = attacker (string user_id),
      id2 = defender (string user_id),
      score_update = how many points attacker gains,
      health_update = how many HP defender loses.
    Action:
      - Increase id1's score by score_update.
      - Decrease id2's score by score_update.
      - Decrease id2's health by health_update.
    Returns: nothing.
    """
