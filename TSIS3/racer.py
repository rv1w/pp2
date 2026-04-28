"""
racer.py – Core gameplay module for TSIS3 Racer.

New features (on top of Practice 10/11 base):
  • Lane hazards: oil spills, potholes, slow-zones
  • Road events: speed bumps, nitro strips, moving barriers
  • Three power-ups: Nitro, Shield, Repair
  • Difficulty scaling
  • Score = dodged enemies + coin value + distance bonus + power-up bonus
  • Distance meter (pixels → metres)
  • Proper safe-spawn logic (never on top of player)
"""

import pygame
import random
import math

# ── Colours ────────────────────────────────────────────────────────────────────
WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)
GRAY    = (90,  90,  90)
DKGRAY  = (50,  50,  50)
YELLOW  = (255, 215,   0)
GOLD    = (200, 160,   0)
RED     = (210,  30,  30)
BLUE    = (30,   90, 210)
LT_BLU  = (160, 210, 255)
GRASS   = (45,  120,  45)
GREEN   = (0,   180,   0)
ORANGE  = (230, 120,   0)
PURPLE  = (160,   0, 200)
CYAN    = (0,   210, 210)
TRANS_Y = (255, 215,   0, 180)

# ── Road geometry ──────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 400, 600
ROAD_LEFT  = 60
ROAD_RIGHT = 340
LANE_W     = (ROAD_RIGHT - ROAD_LEFT) // 3

# ── Coin type definitions ──────────────────────────────────────────────────────
COIN_TYPES = [
    ("bronze", (205, 127,  50), (160,  90,  20), GOLD,   "$",  1, 60),
    ("silver", (192, 192, 192), (140, 140, 140), WHITE,  "S",  3, 30),
    ("gold",   (255, 215,   0), (200, 160,   0), GOLD,   "G",  5, 10),
]
COIN_WEIGHTS = [ct[6] for ct in COIN_TYPES]

COIN_MILESTONE    = 10
ENEMY_SPEED_BOOST = 0.8

# ── Car colour palette ─────────────────────────────────────────────────────────
CAR_COLORS = {
    "blue":   ((30,  90,  210), (160, 210, 255)),
    "red":    ((210,  30,   30), (255, 160, 160)),
    "green":  ((20,  180,   50), (160, 255, 180)),
    "purple": ((160,   0,  200), (220, 160, 255)),
}

# ── Difficulty presets ─────────────────────────────────────────────────────────
DIFF = {
    "easy":   {"base_speed": 3, "enemy_int": (90, 160), "hazard_chance": 0.002},
    "normal": {"base_speed": 4, "enemy_int": (55, 110), "hazard_chance": 0.004},
    "hard":   {"base_speed": 6, "enemy_int": (35,  75), "hazard_chance": 0.007},
}

# ── Pixels-to-metres conversion (cosmetic) ────────────────────────────────────
PX_PER_METRE = 8


# ── Helpers ────────────────────────────────────────────────────────────────────

def lane_x(lane: int, obj_w: int) -> int:
    return ROAD_LEFT + lane * LANE_W + (LANE_W - obj_w) // 2


def random_lane_x(obj_w: int) -> int:
    return lane_x(random.randint(0, 2), obj_w)


def pick_coin_type() -> dict:
    chosen = random.choices(COIN_TYPES, weights=COIN_WEIGHTS, k=1)[0]
    name, body, rim, label_col, label_text, value, _ = chosen
    return {"name": name, "body": body, "rim": rim,
            "label_col": label_col, "label_text": label_text, "value": value}


# ══════════════════════════════════════════════════════════════════════════════
# Road
# ══════════════════════════════════════════════════════════════════════════════
class Road:
    LINE_H   = 55
    LINE_GAP = 35
    SEGMENT  = LINE_H + LINE_GAP

    def __init__(self):
        self.offset = 0
        self.speed  = 5

    def update(self):
        self.offset = (self.offset + self.speed) % self.SEGMENT

    def draw(self, surface):
        surface.fill(GRASS)
        pygame.draw.rect(surface, GRAY, (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_H))
        pygame.draw.rect(surface, WHITE, (ROAD_LEFT - 4, 0, 4, SCREEN_H))
        pygame.draw.rect(surface, WHITE, (ROAD_RIGHT,    0, 4, SCREEN_H))
        for lane in range(1, 3):
            x = ROAD_LEFT + LANE_W * lane - 2
            y = self.offset - self.SEGMENT
            while y < SCREEN_H:
                pygame.draw.rect(surface, WHITE, (x, y, 4, self.LINE_H))
                y += self.SEGMENT


# ══════════════════════════════════════════════════════════════════════════════
# Player car
# ══════════════════════════════════════════════════════════════════════════════
class PlayerCar:
    W, H = 38, 68

    def __init__(self, car_color: str = "blue"):
        self.x        = SCREEN_W // 2 - self.W // 2
        self.y        = SCREEN_H - 110
        self.spd      = 5
        self.body_col, self.win_col = CAR_COLORS.get(car_color, CAR_COLORS["blue"])

        # Power-up state
        self.nitro_active   = False
        self.nitro_timer    = 0      # frames remaining
        self.shield_active  = False
        self.repair_used    = False

        # Visual flash on shield hit
        self.flash_timer = 0

    def draw(self, surface):
        x, y, w, h = self.x, self.y, self.W, self.H
        col = self.body_col
        # Flash white when shield absorbs a hit
        if self.flash_timer > 0:
            col = WHITE; self.flash_timer -= 1

        pygame.draw.rect(surface, col, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, self.win_col, (x+5, y+8,      w-10, 18))
        pygame.draw.rect(surface, self.win_col, (x+5, y+h-22,   w-10, 12))
        for wx, wy in [(x-6, y+6), (x+w-2, y+6), (x-6, y+h-22), (x+w-2, y+h-22)]:
            pygame.draw.rect(surface, BLACK, (wx, wy, 8, 14), border_radius=2)

        # Nitro flame
        if self.nitro_active:
            flame_x = x + w // 2
            flame_y = y + h + 4
            for i, fc in enumerate([(255,80,0),(255,200,0),(255,240,200)]):
                r = 6 - i*2
                pygame.draw.circle(surface, fc, (flame_x, flame_y + i*4), r)

        # Shield aura
        if self.shield_active:
            aura = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(aura, (0, 200, 255, 60), aura.get_rect())
            pygame.draw.ellipse(aura, (0, 200, 255, 140), aura.get_rect(), 3)
            surface.blit(aura, (x - 10, y - 10))

    def move(self, keys):
        spd = self.spd * (1.8 if self.nitro_active else 1.0)
        if keys[pygame.K_a] and self.x > ROAD_LEFT:             self.x -= spd
        if keys[pygame.K_d] and self.x + self.W < ROAD_RIGHT:   self.x += spd
        if keys[pygame.K_w] and self.y > 0:                     self.y -= spd
        if keys[pygame.K_s] and self.y + self.H < SCREEN_H:     self.y += spd

    def tick_powerups(self):
        if self.nitro_active:
            self.nitro_timer -= 1
            if self.nitro_timer <= 0:
                self.nitro_active = False

    def absorb_collision(self) -> bool:
        """
        Returns True if the car is destroyed (game over), False if shield
        absorbed the hit.
        """
        if self.shield_active:
            self.shield_active = False
            self.flash_timer   = 12
            return False   # survived
        return True        # game over

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x + 4, self.y + 4, self.W - 8, self.H - 8)


# ══════════════════════════════════════════════════════════════════════════════
# Enemy car
# ══════════════════════════════════════════════════════════════════════════════
class EnemyCar:
    W, H = 38, 68
    ENEMY_COLS = [(200, 40, 40), (180, 90, 0), (140, 0, 140), (0, 130, 180)]

    def __init__(self, speed: float):
        self.x   = random_lane_x(self.W)
        self.y   = -self.H - random.randint(0, 60)
        self.spd = speed
        self.col = random.choice(self.ENEMY_COLS)

    def draw(self, surface):
        x, y, w, h = self.x, self.y, self.W, self.H
        pygame.draw.rect(surface, self.col, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, LT_BLU, (x+5, y+h-22, w-10, 12))
        for wx, wy in [(x-6, y+6), (x+w-2, y+6), (x-6, y+h-22), (x+w-2, y+h-22)]:
            pygame.draw.rect(surface, BLACK, (wx, wy, 8, 14), border_radius=2)

    def update(self): self.y += self.spd
    def off_screen(self): return self.y > SCREEN_H
    def rect(self): return pygame.Rect(self.x + 4, self.y + 4, self.W - 8, self.H - 8)


# ══════════════════════════════════════════════════════════════════════════════
# Coin
# ══════════════════════════════════════════════════════════════════════════════
class Coin:
    R = 11

    def __init__(self, speed: float):
        self.x   = random.randint(ROAD_LEFT + self.R + 2, ROAD_RIGHT - self.R - 2)
        self.y   = -self.R
        self.spd = speed
        props          = pick_coin_type()
        self.name      = props["name"]
        self.body_col  = props["body"]
        self.rim_col   = props["rim"]
        self.label_col = props["label_col"]
        self.label_text = props["label_text"]
        self.value      = props["value"]
        self._small     = pygame.font.SysFont("Arial", 14, bold=True)

    def draw(self, surface):
        pygame.draw.circle(surface, self.body_col, (self.x, self.y), self.R)
        pygame.draw.circle(surface, self.rim_col,  (self.x, self.y), self.R, 2)
        lbl = self._small.render(self.label_text, True, self.label_col)
        surface.blit(lbl, (self.x - lbl.get_width()//2, self.y - lbl.get_height()//2))

    def update(self): self.y += self.spd
    def off_screen(self): return self.y - self.R > SCREEN_H
    def rect(self): return pygame.Rect(self.x - self.R, self.y - self.R, self.R*2, self.R*2)


# ══════════════════════════════════════════════════════════════════════════════
# Lane Hazards
# ══════════════════════════════════════════════════════════════════════════════
class OilSpill:
    """Slows player by 60 % while overlapping. Does NOT destroy."""
    W, H = LANE_W - 8, 28

    def __init__(self, speed: float):
        lane    = random.randint(0, 2)
        self.x  = ROAD_LEFT + lane * LANE_W + 4
        self.y  = -self.H
        self.spd = speed
        self.alpha = 200
        self._surf = self._make_surf()

    def _make_surf(self):
        s = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for i in range(self.H):
            t   = i / self.H
            col = (int(20+30*t), int(10+20*t), int(30+60*t), int(200*(1 - abs(t-0.5)*1.2)))
            pygame.draw.line(s, col, (0, i), (self.W, i))
        # rainbow shimmer dots
        for _ in range(12):
            rx, ry = random.randint(2, self.W-2), random.randint(2, self.H-2)
            pygame.draw.circle(s, (random.randint(150,255), random.randint(50,200),
                                   random.randint(100,255), 160), (rx, ry), 3)
        return s

    def draw(self, surface):
        surface.blit(self._surf, (self.x, int(self.y)))

    def update(self): self.y += self.spd
    def off_screen(self): return self.y > SCREEN_H
    def rect(self): return pygame.Rect(self.x, self.y, self.W, self.H)


class Pothole:
    """Destroys car on contact (unless shield)."""
    R = 14

    def __init__(self, speed: float):
        lane   = random.randint(0, 2)
        cx     = ROAD_LEFT + lane * LANE_W + LANE_W // 2
        self.x = cx
        self.y = -self.R
        self.spd = speed

    def draw(self, surface):
        pygame.draw.circle(surface, (30, 20, 20), (self.x, int(self.y)), self.R)
        pygame.draw.circle(surface, (60, 40, 40), (self.x, int(self.y)), self.R, 3)
        # cracks
        for angle in (30, 100, 200, 300):
            rad = math.radians(angle)
            ex  = int(self.x + math.cos(rad) * (self.R + 5))
            ey  = int(self.y + math.sin(rad) * (self.R + 5))
            pygame.draw.line(surface, (50, 35, 35),
                             (self.x, int(self.y)), (ex, ey), 2)

    def update(self): self.y += self.spd
    def off_screen(self): return self.y - self.R > SCREEN_H
    def rect(self): return pygame.Rect(self.x - self.R, self.y - self.R, self.R*2, self.R*2)


# ══════════════════════════════════════════════════════════════════════════════
# Road Events
# ══════════════════════════════════════════════════════════════════════════════
class SpeedBump:
    """Slow-zone strip across one lane — reduces speed, safe to drive over."""
    W  = LANE_W - 4
    H  = 12

    def __init__(self, speed: float):
        lane   = random.randint(0, 2)
        self.x = ROAD_LEFT + lane * LANE_W + 2
        self.y = -self.H
        self.spd = speed

    def draw(self, surface):
        pygame.draw.rect(surface, YELLOW, (self.x, int(self.y), self.W, self.H), border_radius=4)
        # hatching
        for i in range(0, self.W, 12):
            pygame.draw.line(surface, BLACK,
                             (self.x + i,       int(self.y)),
                             (self.x + i + 6,   int(self.y + self.H)), 3)

    def update(self): self.y += self.spd
    def off_screen(self): return self.y > SCREEN_H
    def rect(self): return pygame.Rect(self.x, self.y, self.W, self.H)


class NitroStrip:
    """Green boost strip across one lane — gives a free nitro if no powerup active."""
    W  = LANE_W - 4
    H  = 16
    TIMEOUT = 300   # frames before disappearing if not collected

    def __init__(self, speed: float):
        lane   = random.randint(0, 2)
        self.x = ROAD_LEFT + lane * LANE_W + 2
        self.y = -self.H
        self.spd   = speed
        self.timer = self.TIMEOUT
        self._pulse = 0

    def draw(self, surface):
        self._pulse = (self._pulse + 4) % 360
        alpha = int(180 + 60 * math.sin(math.radians(self._pulse)))
        s = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 255, 100, alpha), (0, 0, self.W, self.H), border_radius=4)
        surface.blit(s, (self.x, int(self.y)))
        # "N" label
        fnt = pygame.font.SysFont("Arial", 11, bold=True)
        lbl = fnt.render("NITRO", True, WHITE)
        surface.blit(lbl, (self.x + (self.W - lbl.get_width())//2,
                            int(self.y) + (self.H - lbl.get_height())//2))

    def update(self):
        self.y += self.spd
        self.timer -= 1

    def off_screen(self): return self.y > SCREEN_H or self.timer <= 0
    def rect(self): return pygame.Rect(self.x, self.y, self.W, self.H)


class MovingBarrier:
    """A barrier that moves across the road horizontally."""
    W, H = 80, 18

    def __init__(self, speed: float):
        self.y    = -self.H - random.randint(0, 40)
        self.spd  = speed
        self.hspd = random.choice([-2, -1, 1, 2])
        start_edge = ROAD_LEFT if self.hspd > 0 else ROAD_RIGHT - self.W
        self.x    = float(start_edge)

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        pygame.draw.rect(surface, ORANGE, (x, y, self.W, self.H), border_radius=4)
        pygame.draw.rect(surface, WHITE,  (x, y, self.W, self.H), 2, border_radius=4)
        for i in range(0, self.W, 18):
            col = (255, 80, 0) if (i // 18) % 2 == 0 else ORANGE
            pygame.draw.rect(surface, col, (x + i, y, min(18, self.W - i), self.H))
        pygame.draw.rect(surface, WHITE,  (x, y, self.W, self.H), 2, border_radius=4)

    def update(self):
        self.y += self.spd
        self.x += self.hspd
        # Bounce inside road
        if self.x < ROAD_LEFT or self.x + self.W > ROAD_RIGHT:
            self.hspd *= -1

    def off_screen(self): return self.y > SCREEN_H
    def rect(self): return pygame.Rect(int(self.x)+2, int(self.y)+2, self.W-4, self.H-4)


# ══════════════════════════════════════════════════════════════════════════════
# Power-ups
# ══════════════════════════════════════════════════════════════════════════════
POWERUP_TIMEOUT = 360   # frames before a floating power-up disappears

class PowerUp:
    R = 14
    KINDS = [
        ("nitro",  (0,  230,  80), "N"),
        ("shield", (0,  180, 255), "S"),
        ("repair", (255, 200,  0), "R"),
    ]

    def __init__(self, speed: float, kind: str = None):
        self.x     = random.randint(ROAD_LEFT + self.R + 4, ROAD_RIGHT - self.R - 4)
        self.y     = -self.R
        self.spd   = speed
        self.timer = POWERUP_TIMEOUT
        info       = next((k for k in self.KINDS if k[0] == kind), None) or random.choice(self.KINDS)
        self.kind, self.col, self.label = info
        self._pulse = 0
        self._font  = pygame.font.SysFont("Arial", 14, bold=True)

    def draw(self, surface):
        self._pulse = (self._pulse + 5) % 360
        r_off = int(3 * math.sin(math.radians(self._pulse)))
        # glow
        glow = pygame.Surface((self.R*4, self.R*4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.col, 50), (self.R*2, self.R*2), self.R*2)
        surface.blit(glow, (self.x - self.R*2, int(self.y) - self.R*2))
        # body
        pygame.draw.circle(surface, self.col, (self.x, int(self.y) + r_off), self.R)
        pygame.draw.circle(surface, WHITE,    (self.x, int(self.y) + r_off), self.R, 2)
        lbl = self._font.render(self.label, True, BLACK)
        surface.blit(lbl, (self.x - lbl.get_width()//2,
                            int(self.y) + r_off - lbl.get_height()//2))

    def update(self):
        self.y += self.spd
        self.timer -= 1

    def off_screen(self): return self.y - self.R > SCREEN_H or self.timer <= 0
    def rect(self): return pygame.Rect(self.x-self.R, self.y-self.R, self.R*2, self.R*2)


# ══════════════════════════════════════════════════════════════════════════════
# HUD
# ══════════════════════════════════════════════════════════════════════════════
def draw_hud(surface, score, coin_value, enemy_bonus, distance_m,
             active_pu, nitro_frames):
    font  = pygame.font.SysFont("Arial", 20, bold=True)
    small = pygame.font.SysFont("Arial", 14, bold=True)

    # Semi-transparent HUD bar
    bar = pygame.Surface((SCREEN_W, 48), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 140))
    surface.blit(bar, (0, 0))

    surface.blit(font.render(f"Score: {score}", True, WHITE), (8, 6))
    c_surf = font.render(f"Coins: {coin_value}", True, YELLOW)
    surface.blit(c_surf, (SCREEN_W - c_surf.get_width() - 8, 6))
    dist_s = small.render(f"{distance_m} m", True, (0, 210, 210))
    surface.blit(dist_s, (SCREEN_W//2 - dist_s.get_width()//2, 10))

    # Speed boost indicator
    if enemy_bonus > 0:
        b = small.render(f"Enemy +{enemy_bonus:.1f}", True, RED)
        surface.blit(b, (8, 30))

    # Active power-up indicator
    if active_pu:
        pu_col = {"nitro": (0,230,80), "shield": (0,180,255), "repair": YELLOW}.get(active_pu, WHITE)
        label  = active_pu.upper()
        if active_pu == "nitro" and nitro_frames > 0:
            secs = nitro_frames / 60
            label += f" {secs:.1f}s"
        pu_s = font.render(f"[{label}]", True, pu_col)
        surface.blit(pu_s, (SCREEN_W//2 - pu_s.get_width()//2, 28))