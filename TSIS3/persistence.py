import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
LEADERBOARD_FILE = os.path.join(BASE_DIR, "leaderboard.json")

# ── Default values ─────────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "sound":       True,
    "car_color":   "blue",      # "blue" | "red" | "green" | "purple"
    "difficulty":  "normal",    # "easy" | "normal" | "hard"
}


# ── Settings ───────────────────────────────────────────────────────────────────

def load_settings() -> dict:
    """Load settings from disk; fall back to defaults for any missing keys."""
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        # merge so new keys added in DEFAULT_SETTINGS always appear
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Persist settings dict to disk."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(settings, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        print(f"[persistence] Could not save settings: {exc}")


# ── Leaderboard ────────────────────────────────────────────────────────────────

def load_leaderboard() -> list:
    if not os.path.exists(LEADERBOARD_FILE):
        return []

    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        if not isinstance(data, list):
            return []

        return data[:10]

    except (json.JSONDecodeError, OSError):
        return []
    
def save_leaderboard(entries: list) -> None:
    sorted_entries = sorted(
        entries,
        key=lambda e: e.get("score", 0),
        reverse=True
    )[:10]

    try:
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as fh:
            json.dump(sorted_entries, fh, indent=2, ensure_ascii=False)

    except OSError as exc:
        print(f"[persistence] Could not save leaderboard: {exc}")

def add_leaderboard_entry(name: str, score: int, distance: int) -> list:
    """
    Append a new entry, re-sort, cap at 10, save and return the updated list.
    """
    entries = load_leaderboard()
    entries.append({"name": name, "score": score, "distance": distance})
    save_leaderboard(entries)
    return load_leaderboard()