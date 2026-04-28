# db.py — PostgreSQL persistence layer (psycopg2)

import psycopg2
import psycopg2.extras
from config import DB_CONFIG

# ──────────────────────────────────────────────────────────────────────────────
# Connection helper
# ──────────────────────────────────────────────────────────────────────────────

def get_conn():
    """Open and return a new psycopg2 connection."""
    return psycopg2.connect(**DB_CONFIG)


# ──────────────────────────────────────────────────────────────────────────────
# Schema bootstrap
# ──────────────────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS players (
    id       SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS game_sessions (
    id            SERIAL PRIMARY KEY,
    player_id     INTEGER REFERENCES players(id),
    score         INTEGER   NOT NULL,
    level_reached INTEGER   NOT NULL,
    played_at     TIMESTAMP DEFAULT NOW()
);
"""

def ensure_schema():
    """Create tables if they do not already exist."""
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Schema init failed: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Player operations
# ──────────────────────────────────────────────────────────────────────────────

def get_or_create_player(username: str) -> int | None:
    """
    Return the player id for *username*, creating the row if necessary.
    Returns None on error.
    """
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO players (username) VALUES (%s) "
                    "ON CONFLICT (username) DO NOTHING;",
                    (username,)
                )
                cur.execute(
                    "SELECT id FROM players WHERE username = %s;",
                    (username,)
                )
                row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"[DB] get_or_create_player failed: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Session operations
# ──────────────────────────────────────────────────────────────────────────────

def save_session(player_id: int, score: int, level_reached: int) -> bool:
    """Insert a finished game session. Returns True on success."""
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO game_sessions (player_id, score, level_reached) "
                    "VALUES (%s, %s, %s);",
                    (player_id, score, level_reached)
                )
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] save_session failed: {e}")
        return False


def get_personal_best(player_id: int) -> int:
    """Return the highest score ever achieved by this player (0 if none)."""
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COALESCE(MAX(score), 0) "
                    "FROM game_sessions WHERE player_id = %s;",
                    (player_id,)
                )
                val = cur.fetchone()[0]
        conn.close()
        return int(val)
    except Exception as e:
        print(f"[DB] get_personal_best failed: {e}")
        return 0


def get_leaderboard(limit: int = 10) -> list[dict]:
    """
    Return the top *limit* scores, each as a dict with keys:
    rank, username, score, level_reached, played_at.
    """
    try:
        conn = get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        ROW_NUMBER() OVER (ORDER BY gs.score DESC) AS rank,
                        p.username,
                        gs.score,
                        gs.level_reached,
                        gs.played_at
                    FROM game_sessions gs
                    JOIN players p ON p.id = gs.player_id
                    ORDER BY gs.score DESC
                    LIMIT %s;
                    """,
                    (limit,)
                )
                rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[DB] get_leaderboard failed: {e}")
        return []