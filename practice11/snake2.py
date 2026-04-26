import pygame
import random
import sys
import math

pygame.init()

# ── Grid / window constants ────────────────────────────────────────────────────
CELL    = 20          # pixel size of each grid cell
COLS    = 20          # grid width  (cells)
ROWS    = 20          # grid height (cells)
HUD_H   = 50          # height of the score/level bar at the top

SCREEN_W = CELL * COLS
SCREEN_H = CELL * ROWS + HUD_H

# ── Speed constants ────────────────────────────────────────────────────────────
BASE_FPS      = 8     # starting frame-rate (moves per second)
FPS_PER_LEVEL = 2     # additional FPS gained each level
FOODS_PER_LEVEL = 3   # foods eaten to advance one level

# ── Colour palette ─────────────────────────────────────────────────────────────
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GREEN_BG   = (40,  170, 40)
GRAY       = (30,  30,  30)
LT_GRAY    = (60,  60,  60)
GOLD       = (255, 200, 0)
YELLOW     = (255, 215, 0)
BLUE_HEAD  = (40,  90,  220)
BLUE_BODY  = (70,  130, 255)
GRID_GREEN = (30,  140, 30)

# ── Food type definitions ──────────────────────────────────────────────────────
# Each entry: (display_name, body_colour, highlight_colour, score_multiplier,
#              spawn_weight, ttl_seconds)
FOOD_TYPES = [
    ("normal", (220,  40,  40), (255, 120, 120), 1, 60, 8),   # red   – common,  8 s
    ("bonus",  (255, 200,   0), (255, 240, 140), 2, 30, 6),   # gold  – uncommon, 6 s
    ("super",  ( 40, 220, 220), (160, 255, 255), 3, 10, 4),   # cyan  – rare,     4 s
]
# Separate the weights for random.choices()
FOOD_WEIGHTS = [ft[4] for ft in FOOD_TYPES]

# ── Pygame objects ─────────────────────────────────────────────────────────────
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Snake")
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("Arial", 22, bold=True)
big    = pygame.font.SysFont("Arial", 44, bold=True)

# ── Direction vectors ──────────────────────────────────────────────────────────
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def random_food(occupied: set) -> tuple:
    """Return a random (col, row) not inside *occupied* cells."""
    while True:
        c = random.randint(1, COLS - 2)
        r = random.randint(1, ROWS - 2)
        if (c, r) not in occupied:
            return (c, r)


def pick_food_type() -> dict:
    """
    Randomly select a food type using spawn weights defined in FOOD_TYPES.
    Returns a dict with all properties for that type.
    """
    chosen = random.choices(FOOD_TYPES, weights=FOOD_WEIGHTS, k=1)[0]
    name, colour, highlight, multiplier, _, ttl = chosen
    return {
        "name":        name,
        "colour":      colour,
        "highlight":   highlight,
        "multiplier":  multiplier,
        "ttl":         ttl,          # total lifetime in seconds
    }


# ──────────────────────────────────────────────────────────────────────────────
# Snake class
# ──────────────────────────────────────────────────────────────────────────────

class Snake:
    def __init__(self):
        # Start in the middle of the grid, facing right, three cells long
        cx, cy = COLS // 2, ROWS // 2
        self.body      = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = RIGHT
        self._queued   = RIGHT   # buffered next direction
        self._grow     = False   # flag: eat pending → don't remove tail this frame

    def queue_direction(self, new_dir: tuple):
        """Buffer a direction change, ignoring 180-degree reversals."""
        if new_dir != OPPOSITE.get(self.direction):
            self._queued = new_dir

    def move(self):
        """Advance the snake one step in the buffered direction."""
        self.direction = self._queued
        hx, hy    = self.body[0]
        new_head  = (hx + self.direction[0], hy + self.direction[1])
        self.body.insert(0, new_head)
        if self._grow:
            self._grow = False   # keep the tail — snake is longer now
        else:
            self.body.pop()      # remove tail — snake stays same length

    def eat(self):
        """Signal that the snake should grow on the next move."""
        self._grow = True

    def hit_wall(self) -> bool:
        """True if the head is outside the grid boundaries."""
        hx, hy = self.body[0]
        return not (0 <= hx < COLS and 0 <= hy < ROWS)

    def hit_self(self) -> bool:
        """True if the head overlaps any body segment."""
        return self.body[0] in self.body[1:]

    def draw(self, surface):
        """Render each body segment; draw eyes on the head."""
        for i, (c, r) in enumerate(self.body):
            x = c * CELL
            y = r * CELL + HUD_H
            col = BLUE_HEAD if i == 0 else BLUE_BODY
            pygame.draw.rect(
                surface, col,
                (x + 2, y + 2, CELL - 4, CELL - 4),
                border_radius=3
            )
            # Eyes only on the head segment
            if i == 0:
                pygame.draw.circle(surface, WHITE,  (x + 5,  y + 6), 3)
                pygame.draw.circle(surface, WHITE,  (x + 14, y + 6), 3)
                pygame.draw.circle(surface, BLACK,  (x + 5,  y + 6), 1)
                pygame.draw.circle(surface, BLACK,  (x + 14, y + 6), 1)

    @property
    def cells(self) -> set:
        """Return the snake's occupied cells as a set for O(1) lookup."""
        return set(self.body)


# ──────────────────────────────────────────────────────────────────────────────
# Food class
# ──────────────────────────────────────────────────────────────────────────────

class Food:
    def __init__(self, occupied: set):
        self.pos       = random_food(occupied)   # grid position (col, row)
        props          = pick_food_type()        # randomly chosen type
        self.name      = props["name"]
        self.colour    = props["colour"]
        self.highlight = props["highlight"]
        self.multiplier = props["multiplier"]    # score multiplier
        self.ttl       = props["ttl"]            # total lifetime (seconds)
        self.age       = 0.0                     # seconds elapsed since spawn

    def update(self, dt: float) -> bool:
        """
        Age the food by *dt* seconds.
        Returns True if the food has expired (should be removed without scoring).
        """
        self.age += dt
        return self.age >= self.ttl

    @property
    def fraction_remaining(self) -> float:
        """0.0 = expired, 1.0 = just spawned."""
        return max(0.0, 1.0 - self.age / self.ttl)

    def draw(self, surface):
        """
        Draw the food circle plus a countdown arc that shrinks as time runs out.
        The arc colour shifts from green → yellow → red based on time remaining.
        """
        c, r   = self.pos
        cx     = c * CELL + CELL // 2
        cy     = r * CELL + CELL // 2 + HUD_H
        radius = CELL // 2 - 2

        # Main food circle
        pygame.draw.circle(surface, self.colour, (cx, cy), radius)
        # Small highlight spot
        pygame.draw.circle(surface, self.highlight, (cx - 3, cy - 3), 3)

        # ── Timer arc ─────────────────────────────────────────────────────────
        frac = self.fraction_remaining

        # Colour: green (plenty of time) → yellow → red (almost gone)
        if frac > 0.5:
            arc_col = (int(255 * (1 - frac) * 2), 220, 0)   # green → yellow
        else:
            arc_col = (220, int(220 * frac * 2), 0)           # yellow → red

        # Draw arc using a bounding rect around the food cell
        arc_rect = pygame.Rect(
            c * CELL + 1,
            r * CELL + HUD_H + 1,
            CELL - 2,
            CELL - 2,
        )
        # Arc sweeps from -90° (top) clockwise; end angle shrinks with frac
        start_angle = -math.pi / 2                        # top of circle
        end_angle   = start_angle + 2 * math.pi * frac    # shrinks over time

        if frac > 0.01:   # skip drawing if effectively expired
            pygame.draw.arc(surface, arc_col, arc_rect, start_angle, end_angle, 2)


# ──────────────────────────────────────────────────────────────────────────────
# HUD / overlay drawing helpers
# ──────────────────────────────────────────────────────────────────────────────

def draw_hud(surface, score: int, level: int, foods_this_level: int):
    """Draw the top bar: score (left), level (centre), next-level counter (right)."""
    pygame.draw.rect(surface, GRAY, (0, 0, SCREEN_W, HUD_H))
    pygame.draw.line(surface, LT_GRAY, (0, HUD_H), (SCREEN_W, HUD_H), 2)

    sc  = font.render(f"Score: {score}", True, WHITE)
    lv  = font.render(f"Level {level}", True, GOLD)
    nxt = font.render(
        f"Next ↑: {FOODS_PER_LEVEL - foods_this_level % FOODS_PER_LEVEL}",
        True, YELLOW
    )

    surface.blit(sc,  (12, HUD_H // 2 - sc.get_height() // 2))
    surface.blit(lv,  (SCREEN_W // 2 - lv.get_width() // 2,
                        HUD_H // 2 - lv.get_height() // 2))
    surface.blit(nxt, (SCREEN_W - nxt.get_width() - 12,
                        HUD_H // 2 - nxt.get_height() // 2))


def draw_border(surface):
    """Draw a thin border around the play-field."""
    pygame.draw.rect(surface, LT_GRAY, (0, HUD_H, SCREEN_W, CELL * ROWS), 2)


def draw_overlay(surface, title: str, sub: str = ""):
    """
    Semi-transparent dark overlay with a big title, optional subtitle, and
    restart/quit hint.
    """
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surface.blit(overlay, (0, 0))

    t = big.render(title, True, WHITE)
    surface.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 70))

    if sub:
        s = font.render(sub, True, YELLOW)
        surface.blit(s, (SCREEN_W // 2 - s.get_width() // 2, SCREEN_H // 2))

    hint = font.render("R - restart   Q - quit", True, (180, 180, 180))
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 50))


# ──────────────────────────────────────────────────────────────────────────────
# Main game loop
# ──────────────────────────────────────────────────────────────────────────────

def main():
    snake = Snake()
    food  = Food(snake.cells)   # first food piece

    score             = 0
    level             = 1
    total_foods_eaten = 0
    current_fps       = BASE_FPS
    game_over         = False

    while True:
        # dt = elapsed time in seconds since the last frame (capped to avoid
        # huge jumps after window focus loss etc.)
        dt = min(clock.tick(current_fps) / 1000.0, 0.2)

        # ── Event handling ─────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        main()   # restart by re-entering main()
                        return
                    if event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
                else:
                    # Arrow keys and WASD both control the snake
                    if event.key in (pygame.K_UP,    pygame.K_w): snake.queue_direction(UP)
                    if event.key in (pygame.K_DOWN,  pygame.K_s): snake.queue_direction(DOWN)
                    if event.key in (pygame.K_LEFT,  pygame.K_a): snake.queue_direction(LEFT)
                    if event.key in (pygame.K_RIGHT, pygame.K_d): snake.queue_direction(RIGHT)

        # ── Game logic ─────────────────────────────────────────────────────────
        if not game_over:
            snake.move()

            # Collision checks
            if snake.hit_wall() or snake.hit_self():
                game_over = True

            elif snake.body[0] == food.pos:
                # Snake ate the food
                snake.eat()
                total_foods_eaten += 1
                score += 10 * level * food.multiplier   # bonus types score more

                # Level-up check
                new_level = total_foods_eaten // FOODS_PER_LEVEL + 1
                if new_level > level:
                    level       = new_level
                    current_fps = BASE_FPS + (level - 1) * FPS_PER_LEVEL

                food = Food(snake.cells)   # spawn a new random food

            else:
                # Age the current food; replace it silently if it has expired
                expired = food.update(dt)
                if expired:
                    food = Food(snake.cells)   # no score for expired food

        # ── Rendering ──────────────────────────────────────────────────────────
        screen.fill(GREEN_BG)

        # HUD (pass foods eaten *this* level for the "next level" counter)
        draw_hud(
            screen, score, level,
            total_foods_eaten % FOODS_PER_LEVEL if total_foods_eaten else 0
        )

        # Grid lines
        for c in range(COLS):
            for r in range(ROWS):
                pygame.draw.rect(
                    screen, GRID_GREEN,
                    (c * CELL, r * CELL + HUD_H, CELL, CELL), 1
                )

        draw_border(screen)
        food.draw(screen)    # food drawn before snake so snake appears on top
        snake.draw(screen)

        if game_over:
            draw_overlay(screen, "GAME OVER", f"Score: {score}   Level: {level}")

        pygame.display.flip()


if __name__ == "__main__":
    main()