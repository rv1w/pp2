# config.py — central constants for Snake TSIS 4

import os

# ── Grid / window ──────────────────────────────────────────────────────────────
CELL     = 20
COLS     = 25
ROWS     = 22
HUD_H    = 60
SCREEN_W = CELL * COLS
SCREEN_H = CELL * ROWS + HUD_H

# ── Speed ──────────────────────────────────────────────────────────────────────
BASE_FPS        = 8
FPS_PER_LEVEL   = 2
FOODS_PER_LEVEL = 5

# ── Colours ────────────────────────────────────────────────────────────────────
BLACK        = (0,   0,   0)
WHITE        = (255, 255, 255)
GREEN_BG     = (28,  120, 28)
DARK_GREEN   = (20,  90,  20)
GRAY         = (25,  25,  25)
DARK_GRAY    = (18,  18,  18)
MID_GRAY     = (50,  50,  50)
LT_GRAY      = (80,  80,  80)
GOLD         = (255, 200,  0)
YELLOW       = (255, 215,  0)
BLUE_HEAD    = (30,  80,  210)
BLUE_BODY    = (60, 120, 255)
GRID_GREEN   = (24, 100, 24)
POISON_COL   = (130,  0,  40)
POISON_HL    = (200, 60,  80)
OBSTACLE_COL = (90,  60,  30)
OBSTACLE_HL  = (130, 95,  50)

# Power-up colours
PU_SPEED_COL  = (255, 140,  0)
PU_SPEED_HL   = (255, 200, 100)
PU_SLOW_COL   = (100, 60,  200)
PU_SLOW_HL    = (180, 140, 255)
PU_SHIELD_COL = (0,  200, 160)
PU_SHIELD_HL  = (140, 255, 230)

# UI palette
UI_BG         = (12,  12,  18)
UI_PANEL      = (20,  22,  34)
UI_BORDER     = (45,  50,  80)
UI_ACCENT     = (80, 180, 120)
UI_ACCENT2    = (255, 200,  0)
UI_TEXT       = (220, 225, 235)
UI_MUTED      = (110, 115, 130)
UI_DANGER     = (220,  60,  60)
UI_BTN        = (30,  35,  55)
UI_BTN_HOV    = (50,  58,  90)
UI_BTN_ACT    = (70,  80, 120)

# ── Food type definitions ──────────────────────────────────────────────────────
# (name, colour, highlight, multiplier, weight, ttl_seconds)
FOOD_TYPES = [
    ("normal", (220,  40,  40), (255, 120, 120), 1, 60, 9),
    ("bonus",  (255, 200,   0), (255, 240, 140), 2, 30, 7),
    ("super",  ( 40, 220, 220), (160, 255, 255), 3, 10, 5),
]
FOOD_WEIGHTS = [ft[4] for ft in FOOD_TYPES]

# ── Power-up definitions ───────────────────────────────────────────────────────
# (name, colour, highlight, field_ttl_seconds, effect_duration_seconds)
POWERUP_TYPES = [
    ("speed",  PU_SPEED_COL,  PU_SPEED_HL,  8, 5),
    ("slow",   PU_SLOW_COL,   PU_SLOW_HL,   8, 5),
    ("shield", PU_SHIELD_COL, PU_SHIELD_HL, 8, 0),  # effect_duration 0 = one-shot
]

# ── Speed modifiers for power-ups ─────────────────────────────────────────────
SPEED_BOOST_EXTRA = 4   # +FPS while active
SPEED_SLOW_REDUCE = 4   # -FPS while active (min 2)

# ── Obstacles ─────────────────────────────────────────────────────────────────
OBSTACLES_PER_LEVEL = 3   # extra blocks added each level >= 3
MAX_OBSTACLES       = 24

# ── Database ──────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("PGHOST",     "localhost"),
    "port":     int(os.getenv("PGPORT", "5432")),
    "dbname":   os.getenv("PGDATABASE", "snake_game"),
    "user":     os.getenv("PGUSER",     "postgres"),
    "password": os.getenv("PGPASSWORD", ""),
}

# ── Directions ────────────────────────────────────────────────────────────────
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}