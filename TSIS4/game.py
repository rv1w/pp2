# game.py — Game entities: Snake, Food, PowerUp, Obstacle, HUD

import math
import random
import pygame

from config import (
    CELL, COLS, ROWS, HUD_H, SCREEN_W, SCREEN_H,
    BLACK, WHITE, GRAY, MID_GRAY, LT_GRAY, GOLD, YELLOW,
    BLUE_HEAD, BLUE_BODY, GRID_GREEN, GREEN_BG, DARK_GREEN,
    POISON_COL, POISON_HL,
    OBSTACLE_COL, OBSTACLE_HL,
    FOOD_TYPES, FOOD_WEIGHTS,
    POWERUP_TYPES,
    UI_ACCENT, UI_ACCENT2, UI_TEXT, UI_MUTED,
    UP, DOWN, LEFT, RIGHT, OPPOSITE,
    BASE_FPS, FPS_PER_LEVEL, FOODS_PER_LEVEL,
    OBSTACLES_PER_LEVEL, MAX_OBSTACLES,
    SPEED_BOOST_EXTRA, SPEED_SLOW_REDUCE,
)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def random_cell(blocked: set) -> tuple:
    """Return a random (col, row) not in blocked, away from borders."""
    attempts = 0
    while True:
        c = random.randint(1, COLS - 2)
        r = random.randint(1, ROWS - 2)
        if (c, r) not in blocked:
            return (c, r)
        attempts += 1
        if attempts > 2000:
            return None   # grid too full (fallback)


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ──────────────────────────────────────────────────────────────────────────────
# Snake
# ──────────────────────────────────────────────────────────────────────────────

class Snake:
    def __init__(self, body_color=(60, 120, 255), head_color=(30, 80, 210)):
        cx, cy = COLS // 2, ROWS // 2
        self.body       = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction  = RIGHT
        self._queued    = RIGHT
        self._grow      = 0       # segments to grow (int, +ve → grow)
        self._shrink    = 0       # segments to remove
        self.body_color = body_color
        self.head_color = head_color

    def queue_direction(self, new_dir):
        if new_dir != OPPOSITE.get(self.direction):
            self._queued = new_dir

    def move(self):
        self.direction = self._queued
        hx, hy   = self.body[0]
        new_head = (hx + self.direction[0], hy + self.direction[1])
        self.body.insert(0, new_head)

        if self._grow > 0:
            self._grow -= 1        # grow: keep tail
        elif self._shrink > 0:
            self.body.pop()        # normal removal
            self.body.pop()        # extra removal (shrink)
            self._shrink -= 1
        else:
            self.body.pop()        # normal

    def eat(self):
        self._grow += 1

    def eat_poison(self):
        self._shrink += 1

    def hit_wall(self) -> bool:
        hx, hy = self.body[0]
        return not (0 <= hx < COLS and 0 <= hy < ROWS)

    def hit_self(self) -> bool:
        return self.body[0] in self.body[1:]

    def hit_obstacle(self, obstacles: set) -> bool:
        return self.body[0] in obstacles

    def dead_from_poison(self) -> bool:
        return len(self.body) <= 1

    def draw(self, surface, shield_active=False):
        n = len(self.body)
        for i, (c, r) in enumerate(self.body):
            x = c * CELL
            y = r * CELL + HUD_H

            if i == 0:
                col = self.head_color
            else:
                t   = i / max(n - 1, 1)
                col = lerp_color(self.body_color, tuple(max(0, v - 60) for v in self.body_color), t * 0.5)

            pygame.draw.rect(
                surface, col,
                (x + 2, y + 2, CELL - 4, CELL - 4),
                border_radius=4
            )

            if i == 0:
                # Shield glow
                if shield_active:
                    glow = pygame.Surface((CELL + 8, CELL + 8), pygame.SRCALPHA)
                    pygame.draw.rect(glow, (0, 200, 160, 90),
                                     (0, 0, CELL + 8, CELL + 8), border_radius=6)
                    surface.blit(glow, (x - 4, y - 4))

                # Eyes
                pygame.draw.circle(surface, WHITE,  (x + 5,  y + 6), 3)
                pygame.draw.circle(surface, WHITE,  (x + 14, y + 6), 3)
                pygame.draw.circle(surface, BLACK,  (x + 5,  y + 6), 1)
                pygame.draw.circle(surface, BLACK,  (x + 14, y + 6), 1)

    @property
    def cells(self) -> set:
        return set(self.body)


# ──────────────────────────────────────────────────────────────────────────────
# Food
# ──────────────────────────────────────────────────────────────────────────────

class Food:
    def __init__(self, blocked: set):
        pos = random_cell(blocked)
        self.pos = pos if pos else (1, 1)

        chosen = random.choices(FOOD_TYPES, weights=FOOD_WEIGHTS, k=1)[0]
        name, colour, highlight, multiplier, _, ttl = chosen
        self.name       = name
        self.colour     = colour
        self.highlight  = highlight
        self.multiplier = multiplier
        self.ttl        = ttl
        self.age        = 0.0
        self.is_poison  = False

    @classmethod
    def poison(cls, blocked: set):
        inst = cls.__new__(cls)
        pos  = random_cell(blocked)
        inst.pos       = pos if pos else (2, 2)
        inst.name      = "poison"
        inst.colour    = POISON_COL
        inst.highlight = POISON_HL
        inst.multiplier = 0
        inst.ttl        = 10.0
        inst.age        = 0.0
        inst.is_poison  = True
        return inst

    def update(self, dt: float) -> bool:
        self.age += dt
        return self.age >= self.ttl

    @property
    def fraction_remaining(self):
        return max(0.0, 1.0 - self.age / self.ttl)

    def draw(self, surface):
        c, r   = self.pos
        cx     = c * CELL + CELL // 2
        cy     = r * CELL + CELL // 2 + HUD_H
        radius = CELL // 2 - 2

        pygame.draw.circle(surface, self.colour, (cx, cy), radius)
        pygame.draw.circle(surface, self.highlight, (cx - 3, cy - 3), 3)

        if self.is_poison:
            # Skull-ish cross
            pygame.draw.line(surface, (255, 255, 255),
                             (cx - 4, cy - 4), (cx + 4, cy + 4), 2)
            pygame.draw.line(surface, (255, 255, 255),
                             (cx + 4, cy - 4), (cx - 4, cy + 4), 2)

        # Timer arc
        frac = self.fraction_remaining
        if frac > 0.5:
            arc_col = (int(255 * (1 - frac) * 2), 200, 0)
        else:
            arc_col = (200, int(200 * frac * 2), 0)

        arc_rect = pygame.Rect(
            c * CELL + 1,
            r * CELL + HUD_H + 1,
            CELL - 2,
            CELL - 2,
        )
        start_angle = -math.pi / 2
        end_angle   = start_angle + 2 * math.pi * frac
        if frac > 0.01:
            pygame.draw.arc(surface, arc_col, arc_rect, start_angle, end_angle, 2)


# ──────────────────────────────────────────────────────────────────────────────
# Power-up
# ──────────────────────────────────────────────────────────────────────────────

class PowerUp:
    def __init__(self, blocked: set):
        chosen = random.choice(POWERUP_TYPES)
        self.name, self.colour, self.highlight, self.field_ttl, self.effect_dur = chosen
        pos = random_cell(blocked)
        self.pos = pos if pos else (3, 3)
        self.age = 0.0

    def update(self, dt: float) -> bool:
        self.age += dt
        return self.age >= self.field_ttl

    @property
    def fraction_remaining(self):
        return max(0.0, 1.0 - self.age / self.field_ttl)

    def symbol(self) -> str:
        return {"speed": "⚡", "slow": "❄", "shield": "🛡"}.get(self.name, "?")

    def draw(self, surface):
        c, r   = self.pos
        cx     = c * CELL + CELL // 2
        cy     = r * CELL + CELL // 2 + HUD_H
        radius = CELL // 2 - 1

        # Pulsing outer ring
        pulse = abs(math.sin(pygame.time.get_ticks() / 300.0))
        ring_r = int(radius + 2 + pulse * 3)
        ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (*self.colour, 80),
                           (ring_r + 2, ring_r + 2), ring_r, 2)
        surface.blit(ring_surf, (cx - ring_r - 2, cy - ring_r - 2))

        pygame.draw.circle(surface, self.colour,    (cx, cy), radius)
        pygame.draw.circle(surface, self.highlight, (cx - 2, cy - 2), 3)

        # Label letter
        tiny = pygame.font.SysFont("Arial", 10, bold=True)
        lbl  = {"speed": "S", "slow": "Z", "shield": "X"}.get(self.name, "?")
        ts   = tiny.render(lbl, True, WHITE)
        surface.blit(ts, (cx - ts.get_width() // 2, cy - ts.get_height() // 2))

        # Timer arc
        frac = self.fraction_remaining
        arc_col = (200, int(200 * frac), 0) if frac < 0.5 else (int(255 * (1 - frac) * 2), 200, 0)
        arc_rect = pygame.Rect(c * CELL + 1, r * CELL + HUD_H + 1, CELL - 2, CELL - 2)
        start = -math.pi / 2
        if frac > 0.01:
            pygame.draw.arc(surface, arc_col, arc_rect, start, start + 2 * math.pi * frac, 2)


# ──────────────────────────────────────────────────────────────────────────────
# Obstacle block
# ──────────────────────────────────────────────────────────────────────────────

def generate_obstacles(snake_cells: set, food_cells: set, count: int) -> set:
    """
    Place *count* obstacle blocks avoiding snake, food, and borders.
    Returns a set of (col, row) tuples.
    """
    blocked = snake_cells | food_cells
    # Also keep a ring of safe space around the snake head
    hx, hy  = list(snake_cells)[0]
    for dc in range(-3, 4):
        for dr in range(-3, 4):
            blocked.add((hx + dc, hy + dr))

    obstacles = set()
    for _ in range(count * 20):         # many attempts
        if len(obstacles) >= count:
            break
        c = random.randint(1, COLS - 2)
        r = random.randint(1, ROWS - 2)
        if (c, r) not in blocked:
            obstacles.add((c, r))
            blocked.add((c, r))
    return obstacles


def draw_obstacles(surface, obstacles: set):
    for (c, r) in obstacles:
        x = c * CELL
        y = r * CELL + HUD_H
        pygame.draw.rect(surface, OBSTACLE_COL, (x + 1, y + 1, CELL - 2, CELL - 2), border_radius=2)
        # Bevel highlight
        pygame.draw.line(surface, OBSTACLE_HL,
                         (x + 2, y + 2), (x + CELL - 3, y + 2), 1)
        pygame.draw.line(surface, OBSTACLE_HL,
                         (x + 2, y + 2), (x + 2, y + CELL - 3), 1)


# ──────────────────────────────────────────────────────────────────────────────
# HUD
# ──────────────────────────────────────────────────────────────────────────────

_font_hud   = None
_font_small = None

def _init_fonts():
    global _font_hud, _font_small
    if _font_hud is None:
        _font_hud   = pygame.font.SysFont("Arial", 20, bold=True)
        _font_small = pygame.font.SysFont("Arial", 14)


def draw_hud(surface, score: int, level: int, foods_this_level: int,
             personal_best: int, active_pu: str | None, pu_remaining: float,
             shield_active: bool):
    _init_fonts()

    # Background bar
    pygame.draw.rect(surface, (15, 18, 30), (0, 0, SCREEN_W, HUD_H))
    pygame.draw.line(surface, (50, 55, 80), (0, HUD_H - 1), (SCREEN_W, HUD_H - 1), 1)

    # Score
    sc_surf = _font_hud.render(f"Score: {score}", True, WHITE)
    surface.blit(sc_surf, (10, HUD_H // 2 - sc_surf.get_height() // 2))

    # Personal best
    pb_surf = _font_small.render(f"Best: {personal_best}", True, (160, 200, 160))
    surface.blit(pb_surf, (10, HUD_H // 2 + sc_surf.get_height() // 2 - 2))

    # Level (centre)
    lv_surf = _font_hud.render(f"Level {level}", True, GOLD)
    surface.blit(lv_surf,
                 (SCREEN_W // 2 - lv_surf.get_width() // 2,
                  HUD_H // 2 - lv_surf.get_height() // 2))

    # Next-level progress bar (just below level text)
    bar_w  = 80
    bar_h  = 5
    bar_x  = SCREEN_W // 2 - bar_w // 2
    bar_y  = HUD_H // 2 + lv_surf.get_height() // 2 + 2
    filled = int(bar_w * (foods_this_level / FOODS_PER_LEVEL))
    pygame.draw.rect(surface, MID_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=2)
    pygame.draw.rect(surface, UI_ACCENT, (bar_x, bar_y, filled, bar_h), border_radius=2)

    # Power-up indicator (right side)
    pu_x = SCREEN_W - 130
    if active_pu:
        pu_label = {"speed": "⚡SPEED", "slow": "❄SLOW", "shield": "🛡SHIELD"}.get(active_pu, active_pu.upper())
        pu_col   = {"speed": (255, 140, 0), "slow": (150, 100, 255), "shield": (0, 200, 160)}.get(active_pu, WHITE)
        pu_surf  = _font_small.render(pu_label, True, pu_col)
        surface.blit(pu_surf, (pu_x, HUD_H // 2 - pu_surf.get_height() // 2 - 6))

        if pu_remaining > 0:
            bar_w2  = 100
            bar_x2  = pu_x
            bar_y2  = HUD_H // 2 + 2
            filled2 = int(bar_w2 * pu_remaining)
            pygame.draw.rect(surface, MID_GRAY, (bar_x2, bar_y2, bar_w2, 4), border_radius=2)
            pygame.draw.rect(surface, pu_col,   (bar_x2, bar_y2, filled2, 4), border_radius=2)
    elif shield_active:
        sh_surf = _font_small.render("🛡 SHIELD READY", True, (0, 200, 160))
        surface.blit(sh_surf, (pu_x, HUD_H // 2 - sh_surf.get_height() // 2))


def draw_grid(surface):
    for c in range(COLS):
        for r in range(ROWS):
            pygame.draw.rect(surface, GRID_GREEN,
                             (c * CELL, r * CELL + HUD_H, CELL, CELL), 1)


def draw_border(surface):
    pygame.draw.rect(surface, LT_GRAY,
                     (0, HUD_H, SCREEN_W, CELL * ROWS), 2)