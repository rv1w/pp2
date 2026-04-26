import pygame
import random
import sys

pygame.init()

# ── Window / display constants ─────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 400, 600
FPS = 60

# ── Road geometry ──────────────────────────────────────────────────────────────
ROAD_LEFT  = 60
ROAD_RIGHT = 340
LANE_W     = (ROAD_RIGHT - ROAD_LEFT) // 3   # width of each of the 3 lanes

# ── Colour palette ─────────────────────────────────────────────────────────────
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
GRAY   = (90,  90,  90)
DKGRAY = (50,  50,  50)
YELLOW = (255, 215, 0)
GOLD   = (200, 160, 0)
RED    = (210, 30,  30)
BLUE   = (30,  90,  210)
LT_BLU = (160, 210, 255)
GRASS  = (45,  120, 45)
GREEN  = (0,   180, 0)
PURPLE = (160, 0,   200)
CYAN   = (0,   210, 210)

# ── Coin type definitions ──────────────────────────────────────────────────────
# Each tuple: (name, body_colour, rim_colour, label_colour, label_text,
#              value, spawn_weight)
COIN_TYPES = [
    ("bronze", (205, 127,  50), (160,  90,  20), GOLD,   "$",  1, 60),  # common
    ("silver", (192, 192, 192), (140, 140, 140), WHITE,  "S",  3, 30),  # uncommon
    ("gold",   (255, 215,   0), (200, 160,   0), GOLD,   "G",  5, 10),  # rare – but big payoff
]
COIN_WEIGHTS = [ct[6] for ct in COIN_TYPES]   # parallel list of spawn weights

# ── Enemy speed milestone ──────────────────────────────────────────────────────
# Every time the player collects this many total coin-value points,
# the base enemy speed increases by ENEMY_SPEED_BOOST.
COIN_MILESTONE      = 10   # e.g. every 10 coin-value points
ENEMY_SPEED_BOOST   = 1    # extra pixels/frame added to enemy speed

# ── Pygame singletons ──────────────────────────────────────────────────────────
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Racer")
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("Arial", 22, bold=True)
big    = pygame.font.SysFont("Arial", 48, bold=True)
small  = pygame.font.SysFont("Arial", 14, bold=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────

def random_lane_x(obj_width: int) -> int:
    """Return the x-coordinate that centres *obj_width* inside a random lane."""
    lane = random.randint(0, 2)
    return ROAD_LEFT + lane * LANE_W + (LANE_W - obj_width) // 2


def pick_coin_type() -> dict:
    """
    Randomly select a coin type using COIN_WEIGHTS.
    Bronze is most common (~60 %), silver uncommon (~30 %), gold rare (~10 %).
    Returns a dict with all relevant properties.
    """
    chosen = random.choices(COIN_TYPES, weights=COIN_WEIGHTS, k=1)[0]
    name, body, rim, label_col, label_text, value, _ = chosen
    return {
        "name":       name,
        "body":       body,
        "rim":        rim,
        "label_col":  label_col,
        "label_text": label_text,
        "value":      value,   # coin-value points awarded on collection
    }


# ──────────────────────────────────────────────────────────────────────────────
# Road
# ──────────────────────────────────────────────────────────────────────────────

class Road:
    LINE_H   = 55   # painted dashed-line height (px)
    LINE_GAP = 35   # gap between dashes
    SEGMENT  = LINE_H + LINE_GAP   # total repeating unit

    def __init__(self):
        self.offset = 0   # scroll position within one SEGMENT
        self.speed  = 5   # scroll speed (px/frame); adjusted from main loop

    def update(self):
        """Advance the scroll offset, wrapping within one segment."""
        self.offset = (self.offset + self.speed) % self.SEGMENT

    def draw(self, surface):
        """Draw grass, tarmac, kerb lines, and scrolling lane dashes."""
        surface.fill(GRASS)
        pygame.draw.rect(surface, GRAY, (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_H))
        # Solid white kerb lines at road edges
        pygame.draw.rect(surface, WHITE, (ROAD_LEFT - 4, 0, 4, SCREEN_H))
        pygame.draw.rect(surface, WHITE, (ROAD_RIGHT,    0, 4, SCREEN_H))
        # Dashed centre-lane dividers (lanes 1 and 2)
        for lane in range(1, 3):
            x = ROAD_LEFT + LANE_W * lane - 2
            y = self.offset - self.SEGMENT   # start one segment above screen
            while y < SCREEN_H:
                pygame.draw.rect(surface, WHITE, (x, y, 4, self.LINE_H))
                y += self.SEGMENT


# ──────────────────────────────────────────────────────────────────────────────
# Player car
# ──────────────────────────────────────────────────────────────────────────────

class PlayerCar:
    W, H = 38, 68   # car bounding box (pixels)

    def __init__(self):
        self.x   = SCREEN_W // 2 - self.W // 2
        self.y   = SCREEN_H - 110
        self.spd = 5   # movement speed (px/frame)

    def draw(self, surface):
        """Render a simple top-down blue car with windscreens and wheels."""
        x, y, w, h = self.x, self.y, self.W, self.H
        pygame.draw.rect(surface, BLUE,   (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, LT_BLU, (x + 5, y + 8,      w - 10, 18))  # front screen
        pygame.draw.rect(surface, LT_BLU, (x + 5, y + h - 22, w - 10, 12))  # rear screen
        for wx, wy in [(x-6, y+6), (x+w-2, y+6), (x-6, y+h-22), (x+w-2, y+h-22)]:
            pygame.draw.rect(surface, BLACK, (wx, wy, 8, 14), border_radius=2)

    def move(self, keys):
        """Move the car with WASD, clamped to road boundaries."""
        if keys[pygame.K_a] and self.x > ROAD_LEFT:              self.x -= self.spd
        if keys[pygame.K_d] and self.x + self.W < ROAD_RIGHT:    self.x += self.spd
        if keys[pygame.K_w] and self.y > 0:                      self.y -= self.spd
        if keys[pygame.K_s] and self.y + self.H < SCREEN_H:      self.y += self.spd

    def rect(self) -> pygame.Rect:
        """Collision rect (inset 4 px on all sides to avoid pixel-perfect frustration)."""
        return pygame.Rect(self.x + 4, self.y + 4, self.W - 8, self.H - 8)


# ──────────────────────────────────────────────────────────────────────────────
# Enemy car
# ──────────────────────────────────────────────────────────────────────────────

class EnemyCar:
    W, H = 38, 68

    def __init__(self, speed: float):
        self.x   = random_lane_x(self.W)
        self.y   = -self.H - random.randint(0, 60)   # spawn above the screen
        self.spd = speed
        self.col = random.choice([(200, 40, 40), (180, 90, 0), (140, 0, 140)])

    def draw(self, surface):
        x, y, w, h = self.x, self.y, self.W, self.H
        pygame.draw.rect(surface, self.col, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, LT_BLU, (x+5, y+h-22, w-10, 12))   # windscreen
        for wx, wy in [(x-6, y+6), (x+w-2, y+6), (x-6, y+h-22), (x+w-2, y+h-22)]:
            pygame.draw.rect(surface, BLACK, (wx, wy, 8, 14), border_radius=2)

    def update(self):
        """Move the enemy car down by its speed each frame."""
        self.y += self.spd

    def off_screen(self) -> bool:
        """True once the car has fully scrolled below the visible area."""
        return self.y > SCREEN_H

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x + 4, self.y + 4, self.W - 8, self.H - 8)


# ──────────────────────────────────────────────────────────────────────────────
# Coin
# ──────────────────────────────────────────────────────────────────────────────

class Coin:
    R = 11   # radius (pixels)

    def __init__(self, speed: float):
        # Position: random x anywhere inside the road; start above screen
        self.x   = random.randint(ROAD_LEFT + self.R + 2, ROAD_RIGHT - self.R - 2)
        self.y   = -self.R
        self.spd = speed

        # Randomly choose a coin type (bronze / silver / gold) using weights
        props           = pick_coin_type()
        self.name       = props["name"]
        self.body_col   = props["body"]
        self.rim_col    = props["rim"]
        self.label_col  = props["label_col"]
        self.label_text = props["label_text"]
        self.value      = props["value"]   # coin-value points awarded on pickup

    def draw(self, surface):
        """Draw the coin circle, rim, and label letter."""
        pygame.draw.circle(surface, self.body_col, (self.x, self.y), self.R)
        pygame.draw.circle(surface, self.rim_col,  (self.x, self.y), self.R, 2)
        lbl = small.render(self.label_text, True, self.label_col)
        surface.blit(lbl, (self.x - lbl.get_width() // 2,
                            self.y - lbl.get_height() // 2))

    def update(self):
        self.y += self.spd

    def off_screen(self) -> bool:
        return self.y - self.R > SCREEN_H

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.R, self.y - self.R, self.R * 2, self.R * 2)


# ──────────────────────────────────────────────────────────────────────────────
# HUD / overlay helpers
# ──────────────────────────────────────────────────────────────────────────────

def draw_hud(surface, score: int, coin_value: int, enemy_bonus: int):
    """
    Top bar: score (left), coin total value (right), and a small indicator
    showing how much the enemy speed has been boosted by coin milestones.
    """
    s = font.render(f"Score: {score}", True, WHITE)
    c = font.render(f"Coins: {coin_value}", True, YELLOW)
    surface.blit(s, (10, 8))
    surface.blit(c, (SCREEN_W - c.get_width() - 10, 8))

    # Show current enemy-speed bonus in the lower-left corner of the HUD area
    if enemy_bonus > 0:
        boost_surf = small.render(f"Enemy +{enemy_bonus} spd", True, RED)
        surface.blit(boost_surf, (10, 34))


def draw_game_over(surface, score: int, coin_value: int):
    """Semi-transparent overlay with final stats and restart hint."""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    lines = [
        (big,  "GAME OVER",                RED),
        (font, f"Score : {score}",         WHITE),
        (font, f"Coins : {coin_value} pts",YELLOW),
        (font, "R – restart   Q – quit",   WHITE),
    ]
    y = 190
    for f_, text, col in lines:
        surf = f_.render(text, True, col)
        surface.blit(surf, (SCREEN_W // 2 - surf.get_width() // 2, y))
        y += surf.get_height() + 14


# ──────────────────────────────────────────────────────────────────────────────
# Main game loop
# ──────────────────────────────────────────────────────────────────────────────

def main():
    road   = Road()
    player = PlayerCar()
    enemies: list[EnemyCar] = []
    coins:   list[Coin]     = []

    score           = 0    # increments each time an enemy passes off-screen
    coin_value      = 0    # total coin-value points collected
    base_speed      = 4    # base enemy/coin scroll speed (px/frame)
    game_over       = False

    # Tracks which coin-value milestone the enemy has been boosted to.
    # e.g. if milestone=10 and coin_value reaches 20, enemy_boost becomes 2.
    last_milestone  = 0
    enemy_boost     = 0    # total extra speed added to enemies so far

    enemy_timer     = 0
    enemy_interval  = 80
    coin_timer      = 0
    coin_interval   = random.randint(100, 180)

    while True:
        clock.tick(FPS)

        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:
                    main()
                    return
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

        # ── Game logic ─────────────────────────────────────────────────────────
        if not game_over:
            keys = pygame.key.get_pressed()
            player.move(keys)
            road.update()

            # Current scroll/enemy speed scales with score AND coin milestones
            speed       = base_speed + score // 5 + enemy_boost
            road.speed  = 5 + score // 8

            # ── Check coin-value milestone → boost enemy speed ─────────────────
            # Every COIN_MILESTONE points earned triggers one speed boost.
            current_milestone = coin_value // COIN_MILESTONE
            if current_milestone > last_milestone:
                gained        = current_milestone - last_milestone
                enemy_boost  += gained * ENEMY_SPEED_BOOST
                last_milestone = current_milestone
                # Live-update all existing enemies on screen so the change is
                # immediately felt rather than waiting for new spawns.
                for en in enemies:
                    en.spd += gained * ENEMY_SPEED_BOOST

            # ── Spawn enemies ──────────────────────────────────────────────────
            enemy_timer += 1
            if enemy_timer >= enemy_interval:
                enemies.append(EnemyCar(speed))
                enemy_timer    = 0
                enemy_interval = random.randint(55, 110)

            # ── Spawn coins ────────────────────────────────────────────────────
            coin_timer += 1
            if coin_timer >= coin_interval:
                coins.append(Coin(speed))
                coin_timer    = 0
                coin_interval = random.randint(90, 200)

            # ── Update enemies ─────────────────────────────────────────────────
            for en in enemies[:]:
                en.update()
                if en.off_screen():
                    enemies.remove(en)
                    score += 1                    # reward dodging each enemy
                elif en.rect().colliderect(player.rect()):
                    game_over = True              # collision → game over

            # ── Update coins ───────────────────────────────────────────────────
            for co in coins[:]:
                co.update()
                if co.off_screen():
                    coins.remove(co)
                elif co.rect().colliderect(player.rect()):
                    coins.remove(co)
                    coin_value += co.value        # add this coin's point value

        # ── Rendering ──────────────────────────────────────────────────────────
        road.draw(screen)

        for en in enemies: en.draw(screen)
        for co in coins:   co.draw(screen)
        player.draw(screen)

        draw_hud(screen, score, coin_value, enemy_boost)

        if game_over:
            draw_game_over(screen, score, coin_value)

        pygame.display.flip()


if __name__ == "__main__":
    main()