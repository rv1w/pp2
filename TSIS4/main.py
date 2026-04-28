# main.py — Snake TSIS 4: all screens + main game loop

import sys
import json
import random
import math
import os
import pygame

import db
from config import (
    CELL, COLS, ROWS, HUD_H, SCREEN_W, SCREEN_H,
    BLACK, WHITE, GRAY, MID_GRAY, LT_GRAY, GOLD, YELLOW,
    BLUE_HEAD, BLUE_BODY, GREEN_BG,
    UI_BG, UI_PANEL, UI_BORDER, UI_ACCENT, UI_ACCENT2,
    UI_TEXT, UI_MUTED, UI_DANGER, UI_BTN, UI_BTN_HOV, UI_BTN_ACT,
    UP, DOWN, LEFT, RIGHT, OPPOSITE,
    BASE_FPS, FPS_PER_LEVEL, FOODS_PER_LEVEL,
    OBSTACLES_PER_LEVEL, MAX_OBSTACLES,
    SPEED_BOOST_EXTRA, SPEED_SLOW_REDUCE,
)
from game import (
    Snake, Food, PowerUp,
    generate_obstacles, draw_obstacles,
    draw_hud, draw_grid, draw_border,
)

# ──────────────────────────────────────────────────────────────────────────────
# Settings helpers
# ──────────────────────────────────────────────────────────────────────────────

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS = {
    "snake_color":      [60, 120, 255],
    "snake_head_color": [30, 80, 210],
    "grid_overlay":     True,
    "sound":            False,
}

def load_settings() -> dict:
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        # fill any missing keys with defaults
        for k, v in DEFAULT_SETTINGS.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return dict(DEFAULT_SETTINGS)

def save_settings(s: dict):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(s, f, indent=4)
    except Exception as e:
        print(f"[Settings] save failed: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Pygame init
# ──────────────────────────────────────────────────────────────────────────────

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Snake — TSIS 4")
clock  = pygame.time.Clock()


# Fonts
F_TITLE  = pygame.font.SysFont("Courier New", 52, bold=True)
F_BIG    = pygame.font.SysFont("Courier New", 36, bold=True)
F_MED    = pygame.font.SysFont("Arial", 22, bold=True)
F_BODY   = pygame.font.SysFont("Arial", 18, bold=True)
F_SMALL  = pygame.font.SysFont("Arial", 14, bold=True)
F_MONO   = pygame.font.SysFont("Courier New", 16)

# ──────────────────────────────────────────────────────────────────────────────
# UI helpers
# ──────────────────────────────────────────────────────────────────────────────

def draw_background(surf):
    """Animated dark starfield background for menu screens."""
    surf.fill(UI_BG)
    t = pygame.time.get_ticks() / 1000.0
    for i in range(40):
        random.seed(i * 7919)
        x = random.randint(0, SCREEN_W)
        y = random.randint(0, SCREEN_H)
        blink = abs(math.sin(t * 0.8 + i * 0.4))
        r = int(80 + 120 * blink)
        pygame.draw.circle(surf, (r, r, r), (x, y), 1)


class Button:
    def __init__(self, rect, label, color=None, hover_color=None, text_color=WHITE,
                 font=None, border_radius=8):
        self.rect         = pygame.Rect(rect)
        self.label        = label
        self.color        = color or UI_BTN
        self.hover_color  = hover_color or UI_BTN_HOV
        self.text_color   = text_color
        self.font         = font or F_BODY
        self.border_radius = border_radius
        self._pressed     = False

    def draw(self, surf):
        mx, my = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mx, my)
        col     = self.hover_color if hovered else self.color
        pygame.draw.rect(surf, col, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surf, UI_BORDER, self.rect, 1, border_radius=self.border_radius)
        ts = self.font.render(self.label, True, self.text_color)
        surf.blit(ts, (self.rect.centerx - ts.get_width() // 2,
                       self.rect.centery - ts.get_height() // 2))

    def is_clicked(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


def draw_panel(surf, rect, alpha=220):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    s.fill((*UI_PANEL, alpha))
    pygame.draw.rect(s, (*UI_BORDER, 255),
                     (0, 0, rect[2], rect[3]), 1, border_radius=10)
    surf.blit(s, (rect[0], rect[1]))


def draw_title_snake(surf):
    """Decorative snake logo on the main menu."""
    base_x, base_y = SCREEN_W // 2 - 120, 80
    segments = [(base_x + i * 22, base_y + int(math.sin(i * 0.7 +
                  pygame.time.get_ticks() / 400.0) * 8)) for i in range(11)]
    for i, (x, y) in enumerate(segments):
        col = (30, 80, 210) if i == 0 else (60, 120, 255)
        pygame.draw.circle(surf, col, (x, y), 9 if i == 0 else 8)
        if i == 0:
            pygame.draw.circle(surf, WHITE, (x - 3, y - 2), 2)
            pygame.draw.circle(surf, WHITE, (x + 3, y - 2), 2)
            pygame.draw.circle(surf, BLACK, (x - 3, y - 2), 1)
            pygame.draw.circle(surf, BLACK, (x + 3, y - 2), 1)


# ──────────────────────────────────────────────────────────────────────────────
# Text input widget
# ──────────────────────────────────────────────────────────────────────────────

class TextInput:
    def __init__(self, rect, placeholder="", max_len=20):
        self.rect        = pygame.Rect(rect)
        self.placeholder = placeholder
        self.max_len     = max_len
        self.text        = ""
        self.active      = True
        self._blink_t    = 0

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return True   # "confirm"
            elif len(self.text) < self.max_len and event.unicode.isprintable():
                self.text += event.unicode
        return False

    def draw(self, surf):
        self._blink_t += 1
        cursor_vis = (self._blink_t // 30) % 2 == 0

        pygame.draw.rect(surf, (25, 30, 50), self.rect, border_radius=6)
        pygame.draw.rect(surf, UI_ACCENT, self.rect, 2, border_radius=6)

        display = self.text if self.text else self.placeholder
        col     = UI_TEXT if self.text else UI_MUTED
        ts      = F_BODY.render(display, True, col)
        surf.blit(ts, (self.rect.x + 10,
                       self.rect.centery - ts.get_height() // 2))

        if cursor_vis and self.active:
            cx = self.rect.x + 10 + ts.get_width() + 2
            cy = self.rect.centery - ts.get_height() // 2
            pygame.draw.line(surf, UI_ACCENT, (cx, cy), (cx, cy + ts.get_height()), 2)


# ──────────────────────────────────────────────────────────────────────────────
# Screen: Main Menu
# ──────────────────────────────────────────────────────────────────────────────

def screen_main_menu(db_ok: bool) -> tuple[str, str]:
    """
    Returns (action, username).
    action is one of: "play", "leaderboard", "settings", "quit"
    """
    BW, BH = 220, 46
    bx = SCREEN_W // 2 - BW // 2

    btn_play   = Button((bx, 220, BW, BH), "Play",
                        color=(30, 90, 50), hover_color=(45, 120, 70),
                        text_color=WHITE, font=F_MED)
    btn_lb     = Button((bx, 278, BW, BH), "Leaderboard", font=F_BODY)
    btn_sett   = Button((bx, 336, BW, BH), "Settings", font=F_BODY)
    btn_quit   = Button((bx, 394, BW, BH), "Quit",
                        color=(60, 20, 20), hover_color=(90, 30, 30), font=F_BODY)

    username_input = TextInput((SCREEN_W // 2 - 130, 160, 260, 40),
                               placeholder="Enter username…")

    db_warning = not db_ok

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                pygame.quit(); sys.exit()

            if username_input.handle(event):
                if username_input.text.strip():
                    return "play", username_input.text.strip()

            if btn_play.is_clicked(event):
                uname = username_input.text.strip() or "Player"
                return "play", uname
            if btn_lb.is_clicked(event):
                uname = username_input.text.strip() or "Player"
                return "leaderboard", uname
            if btn_sett.is_clicked(event):
                return "settings", username_input.text.strip() or "Player"
            if btn_quit.is_clicked(event):
                pygame.quit(); sys.exit()

        draw_background(screen)
        draw_panel(screen, (SCREEN_W // 2 - 160, 60, 320, 400))

        # Title
        t1 = F_TITLE.render("SNAKE", True, UI_ACCENT)
        screen.blit(t1, (SCREEN_W // 2 - t1.get_width() // 2, 70))
        draw_title_snake(screen)

        # Username label
        lbl = F_SMALL.render("Username:", True, UI_MUTED)
        screen.blit(lbl, (SCREEN_W // 2 - 130, 146))
        username_input.draw(screen)

        btn_play.draw(screen)
        btn_lb.draw(screen)
        btn_sett.draw(screen)
        btn_quit.draw(screen)

        if db_warning:
            warn = F_SMALL.render("DB unavailable — scores won't be saved", True, (220, 160, 0))
            screen.blit(warn, (SCREEN_W // 2 - warn.get_width() // 2, SCREEN_H - 28))

        pygame.display.flip()
        clock.tick(60)


# ──────────────────────────────────────────────────────────────────────────────
# Screen: Leaderboard
# ──────────────────────────────────────────────────────────────────────────────

def screen_leaderboard():
    rows    = db.get_leaderboard(10)
    btn_bk  = Button((SCREEN_W // 2 - 80, SCREEN_H - 60, 160, 38), "← Back", font=F_BODY)

    COL_X = [30, 70, 230, 330, 420]   # rank | username | score | level | date

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                return
            if btn_bk.is_clicked(event):
                return

        draw_background(screen)
        draw_panel(screen, (20, 40, SCREEN_W - 40, SCREEN_H - 80))

        title = F_BIG.render("LEADERBOARD", True, GOLD)
        screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 55))

        # Header row
        headers = ["#", "Username", "Score", "Level", "Date"]
        for i, h in enumerate(headers):
            hs = F_SMALL.render(h, True, UI_MUTED)
            screen.blit(hs, (COL_X[i] + 20, 110))
        pygame.draw.line(screen, UI_BORDER, (30, 128), (SCREEN_W - 30, 128), 1)

        if not rows:
            ns = F_BODY.render("No records yet — play to set a score!", True, UI_MUTED)
            screen.blit(ns, (SCREEN_W // 2 - ns.get_width() // 2, 200))
        else:
            for idx, r in enumerate(rows):
                y   = 138 + idx * 34
                # Alternate row shading
                if idx % 2 == 0:
                    pygame.draw.rect(screen, (30, 35, 58),
                                     (22, y - 4, SCREEN_W - 44, 30), border_radius=4)
                rank_col = GOLD if idx == 0 else (200, 200, 200) if idx == 1 else (180, 120, 60) if idx == 2 else UI_TEXT
                values   = [
                    str(r["rank"]),
                    str(r["username"])[:18],
                    str(r["score"]),
                    str(r["level_reached"]),
                    str(r["played_at"])[:10],
                ]
                for i, v in enumerate(values):
                    col = rank_col if i == 0 else (UI_ACCENT2 if i == 2 else UI_TEXT)
                    vs  = F_BODY.render(v, True, col)
                    screen.blit(vs, (COL_X[i] + 20, y))

        btn_bk.draw(screen)
        pygame.display.flip()
        clock.tick(60)


# ──────────────────────────────────────────────────────────────────────────────
# Screen: Settings
# ──────────────────────────────────────────────────────────────────────────────

COLOR_PRESETS = [
    ("Blue",   [60, 120, 255], [30, 80, 210]),
    ("Green",  [50, 200, 80],  [20, 140, 50]),
    ("Red",    [220, 60, 60],  [160, 30, 30]),
    ("Purple", [160, 60, 220], [100, 30, 160]),
    ("Orange", [240, 130, 30], [180, 80, 20]),
    ("Teal",   [40, 200, 180], [20, 140, 120]),
]


def screen_settings(settings: dict) -> dict:
    s = dict(settings)

    btn_save = Button((SCREEN_W // 2 - 100, SCREEN_H - 70, 200, 42),
                      "Save & Back",
                      color=(30, 90, 50), hover_color=(45, 120, 70), font=F_MED)

    color_buttons = []
    for i, (name, body, head) in enumerate(COLOR_PRESETS):
        bx = 60 + i * 72
        color_buttons.append({
            "rect":  pygame.Rect(bx, 220, 60, 60),
            "name":  name,
            "body":  body,
            "head":  head,
        })

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return s
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # Color buttons
                for cb in color_buttons:
                    if cb["rect"].collidepoint(mx, my):
                        s["snake_color"]      = cb["body"]
                        s["snake_head_color"] = cb["head"]
                # Grid toggle
                if pygame.Rect(SCREEN_W // 2 - 30, 320, 60, 30).collidepoint(mx, my):
                    s["grid_overlay"] = not s["grid_overlay"]
                # Sound toggle
                if pygame.Rect(SCREEN_W // 2 - 30, 380, 60, 30).collidepoint(mx, my):
                    s["sound"] = not s["sound"]

                    if s["sound"]:
                        pygame.mixer.music.unpause()
                    else:
                        pygame.mixer.music.pause()
            if btn_save.is_clicked(event):
                save_settings(s)
                return s

        draw_background(screen)
        draw_panel(screen, (20, 40, SCREEN_W - 40, SCREEN_H - 80))

        title = F_BIG.render("SETTINGS", True, UI_TEXT)
        screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 55))

        # Snake colour label
        cl = F_BODY.render("Snake Colour:", True, UI_MUTED)
        screen.blit(cl, (40, 190))

        # Colour preset buttons
        for cb in color_buttons:
            selected = s["snake_color"] == cb["body"]
            pygame.draw.rect(screen, cb["body"], cb["rect"], border_radius=8)
            border_c = WHITE if selected else UI_BORDER
            border_w = 3    if selected else 1
            pygame.draw.rect(screen, border_c, cb["rect"], border_w, border_radius=8)
            nl = F_SMALL.render(cb["name"], True, WHITE)
            screen.blit(nl, (cb["rect"].centerx - nl.get_width() // 2,
                             cb["rect"].bottom + 4))

        # Preview snake
        prev_x = SCREEN_W // 2 - 55
        for i in range(6):
            col = tuple(s["snake_head_color"]) if i == 0 else tuple(s["snake_color"])
            pygame.draw.rect(screen, col, (prev_x + i * 20, 300, 16, 16), border_radius=3)

        # Grid toggle
        pygame.draw.line(screen, UI_BORDER, (30, 316), (SCREEN_W - 30, 316), 1)
        gl = F_BODY.render("Grid Overlay:", True, UI_MUTED)
        screen.blit(gl, (40, 325))
        tog_r = pygame.Rect(SCREEN_W // 2 + 30, 320, 60, 30)
        tog_c = UI_ACCENT if s["grid_overlay"] else MID_GRAY
        pygame.draw.rect(screen, tog_c, tog_r, border_radius=15)
        knob_x = tog_r.x + (40 if s["grid_overlay"] else 4)
        pygame.draw.circle(screen, WHITE, (knob_x, tog_r.centery), 12)
        tv = F_SMALL.render("" if s["grid_overlay"] else "", True, WHITE)
        screen.blit(tv, (tog_r.x + (10 if not s["grid_overlay"] else 28), tog_r.centery - tv.get_height() // 2))

        # Sound toggle
        sl = F_BODY.render("Sound:", True, UI_MUTED)
        screen.blit(sl, (40, 385))
        stog_r = pygame.Rect(SCREEN_W // 2 + 30, 380, 60, 30)
        stog_c = UI_ACCENT if s["sound"] else MID_GRAY
        pygame.draw.rect(screen, stog_c, stog_r, border_radius=15)
        sknob_x = stog_r.x + (40 if s["sound"] else 4)
        pygame.draw.circle(screen, WHITE, (sknob_x, stog_r.centery), 12)
        sv = F_SMALL.render("" if s["sound"] else "", True, WHITE)
        screen.blit(sv, (stog_r.x + (10 if not s["sound"] else 28), stog_r.centery - sv.get_height() // 2))

        pygame.draw.line(screen, UI_BORDER, (30, 416), (SCREEN_W - 30, 416), 1)

        btn_save.draw(screen)
        pygame.display.flip()
        clock.tick(60)


# ──────────────────────────────────────────────────────────────────────────────
# Screen: Game Over
# ──────────────────────────────────────────────────────────────────────────────

def screen_game_over(score: int, level: int, personal_best: int) -> str:
    """Returns 'retry' or 'menu'."""
    BW, BH = 180, 46
    btn_retry = Button((SCREEN_W // 2 - BW - 10, SCREEN_H // 2 + 80, BW, BH),
                       "Retry",
                       color=(30, 90, 50), hover_color=(45, 120, 70), font=F_MED)
    btn_menu  = Button((SCREEN_W // 2 + 10, SCREEN_H // 2 + 80, BW, BH),
                       "Main Menu", font=F_MED)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "retry"
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    return "menu"
            if btn_retry.is_clicked(event):
                return "retry"
            if btn_menu.is_clicked(event):
                return "menu"

        draw_background(screen)
        draw_panel(screen, (SCREEN_W // 2 - 200, SCREEN_H // 2 - 140, 400, 260))

        go  = F_TITLE.render("GAME OVER", True, UI_DANGER)
        screen.blit(go, (SCREEN_W // 2 - go.get_width() // 2, SCREEN_H // 2 - 130))

        sc_txt  = F_MED.render(f"Score:  {score}", True, GOLD)
        lv_txt  = F_MED.render(f"Level:  {level}", True, UI_TEXT)
        pb_new  = score > personal_best and personal_best > 0
        pb_col  = UI_ACCENT if pb_new else UI_MUTED
        pb_txt  = F_MED.render(f"Best:   {max(score, personal_best)}" + (" 🏆 NEW!" if pb_new else ""), True, pb_col)

        screen.blit(sc_txt, (SCREEN_W // 2 - sc_txt.get_width() // 2, SCREEN_H // 2 - 50))
        screen.blit(lv_txt, (SCREEN_W // 2 - lv_txt.get_width() // 2, SCREEN_H // 2 - 10))
        screen.blit(pb_txt, (SCREEN_W // 2 - pb_txt.get_width() // 2, SCREEN_H // 2 + 30))

        btn_retry.draw(screen)
        btn_menu.draw(screen)

        hint = F_SMALL.render("R - retry   ESC - menu", True, UI_MUTED)
        screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 142))

        pygame.display.flip()
        clock.tick(60)


# ──────────────────────────────────────────────────────────────────────────────
# Core game session
# ──────────────────────────────────────────────────────────────────────────────

def run_game(settings: dict, player_id: int | None, personal_best: int) -> tuple[int, int]:
    """
    Run one game session and return (score, level_reached).
    """
    body_c = tuple(settings["snake_color"])
    head_c = tuple(settings["snake_head_color"])
    grid_on = settings["grid_overlay"]

    pygame.mixer.music.load("TSIS4/assets/music/bg.mp3")
    pygame.mixer.music.set_volume(0.5)  # от 0.0 до 1.0
    pygame.mixer.music.play(-1)

    if not settings["sound"]:
        pygame.mixer.music.pause()

    snake     = Snake(body_color=body_c, head_color=head_c)
    obstacles : set = set()

    def blocked_cells():
        return snake.cells | {f.pos for f in foods} | {pu.pos for pu in [powerup] if powerup} | obstacles

    # Foods list (normal + possibly poison)
    foods : list[Food]  = [Food(snake.cells)]
    powerup : PowerUp | None = None

    score             = 0
    level             = 1
    total_foods_eaten = 0
    current_fps       = BASE_FPS
    game_over         = False

    # Power-up state
    active_pu         : str | None = None   # name of active effect
    active_pu_end     : int        = 0      # pygame.time.get_ticks() expiry
    shield_active     : bool       = False
    # Spawn control
    pu_spawn_timer    : int        = pygame.time.get_ticks() + 8000  # next PU spawn attempt
    poison_spawn_timer: int        = pygame.time.get_ticks() + 5000

    def effective_fps():
        fps = BASE_FPS + (level - 1) * FPS_PER_LEVEL
        if active_pu == "speed":
            fps = min(fps + SPEED_BOOST_EXTRA, 30)
        elif active_pu == "slow":
            fps = max(fps - SPEED_SLOW_REDUCE, 2)
        return fps

    def check_powerup_expiry():
        nonlocal active_pu, shield_active
        if active_pu and active_pu != "shield":
            if pygame.time.get_ticks() >= active_pu_end:
                active_pu = None

    def foods_this_level():
        return total_foods_eaten % FOODS_PER_LEVEL

    def pu_fraction():
        if not active_pu or active_pu == "shield":
            return 0.0
        total_ms = {"speed": 5000, "slow": 5000}.get(active_pu, 5000)
        left_ms  = active_pu_end - pygame.time.get_ticks()
        return max(0.0, left_ms / total_ms)

    while True:
        dt  = min(clock.tick(effective_fps()) / 1000.0, 0.2)
        now = pygame.time.get_ticks()

        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if game_over:
                    # Any key exits back to caller after showing game-over overlay
                    return score, level
                else:
                    if event.key in (pygame.K_UP,    pygame.K_w): snake.queue_direction(UP)
                    if event.key in (pygame.K_DOWN,  pygame.K_s): snake.queue_direction(DOWN)
                    if event.key in (pygame.K_LEFT,  pygame.K_a): snake.queue_direction(LEFT)
                    if event.key in (pygame.K_RIGHT, pygame.K_d): snake.queue_direction(RIGHT)
                    if event.key == pygame.K_ESCAPE:
                        return score, level

        # ── Logic ─────────────────────────────────────────────────────────────
        if not game_over:
            check_powerup_expiry()
            snake.move()

            head = snake.body[0]

            # --- Collision ---
            wall_hit = snake.hit_wall()
            self_hit = snake.hit_self()
            obs_hit  = snake.hit_obstacle(obstacles)

            if wall_hit or self_hit or obs_hit:
                if shield_active:
                    # Shield absorbs ONE collision → respawn head safely
                    shield_active = False
                    active_pu     = None
                    # Undo the move by reverting head to second segment
                    snake.body[0] = snake.body[1]
                else:
                    game_over = True

            # --- Eat normal/bonus/super food ---
            for f in list(foods):
                if head == f.pos:
                    if f.is_poison:
                        snake.eat_poison()
                        if snake.dead_from_poison():
                            game_over = True
                    else:
                        snake.eat()
                        total_foods_eaten += 1
                        score += 10 * level * f.multiplier
                        # Level-up
                        new_level = total_foods_eaten // FOODS_PER_LEVEL + 1
                        if new_level > level:
                            level = new_level
                            # Add obstacles from level 3 onwards
                            if level >= 3:
                                n_obs = min(
                                    len(obstacles) + OBSTACLES_PER_LEVEL,
                                    MAX_OBSTACLES
                                )
                                extra = n_obs - len(obstacles)
                                if extra > 0:
                                    new_obs = generate_obstacles(
                                        snake.cells,
                                        {ff.pos for ff in foods},
                                        extra
                                    )
                                    obstacles |= new_obs
                    foods.remove(f)
                    # Spawn replacement food
                    foods.append(Food(blocked_cells()))
                    break

            # --- Eat power-up ---
            if powerup and head == powerup.pos:
                collected_pu_name = powerup.name
                collected_pu_dur  = powerup.effect_dur
                powerup           = None
                active_pu         = collected_pu_name
                if collected_pu_name == "shield":
                    shield_active = True
                else:
                    active_pu_end = now + collected_pu_dur * 1000
                score += 5 * level

            # --- Age foods ---
            for f in list(foods):
                if f.update(dt):
                    foods.remove(f)
                    foods.append(Food(blocked_cells()))

            # --- Age / spawn power-up ---
            if powerup:
                if powerup.update(dt):
                    powerup = None
            elif not powerup and now >= pu_spawn_timer:
                powerup = PowerUp(blocked_cells())
                pu_spawn_timer = now + random.randint(10000, 18000)

            # --- Poison spawn ---
            has_poison = any(f.is_poison for f in foods)
            if not has_poison and now >= poison_spawn_timer:
                foods.append(Food.poison(blocked_cells()))
                poison_spawn_timer = now + random.randint(8000, 15000)

        # ── Render ────────────────────────────────────────────────────────────
        screen.fill((28, 120, 28))

        if grid_on:
            draw_grid(screen)

        draw_border(screen)
        draw_obstacles(screen, obstacles)

        for f in foods:
            f.draw(screen)
        if powerup:
            powerup.draw(screen)

        snake.draw(screen, shield_active=shield_active)

        draw_hud(
            screen, score, level,
            foods_this_level(),
            personal_best,
            active_pu if active_pu != "shield" else None,
            pu_fraction(),
            shield_active,
        )

        if game_over:
            # Semi-transparent overlay
            ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 140))
            screen.blit(ov, (0, 0))
            go_t = F_TITLE.render("GAME OVER", True, UI_DANGER)
            screen.blit(go_t, (SCREEN_W // 2 - go_t.get_width() // 2,
                                SCREEN_H // 2 - 40))
            hint = F_BODY.render("R - retry   Q - menu", True, (180, 180, 180))
            screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2,
                                SCREEN_H // 2 + 20))

        pygame.display.flip()




# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    settings = load_settings()
    db_ok    = db.ensure_schema()

    while True:
        action, username = screen_main_menu(db_ok)

        if action == "leaderboard":
            screen_leaderboard()
            continue

        if action == "settings":
            settings = screen_settings(settings)
            continue

        # action == "play"
        player_id    = db.get_or_create_player(username) if db_ok else None
        personal_best = db.get_personal_best(player_id) if player_id else 0

        while True:
            score, level = run_game(settings, player_id, personal_best)

            # Save to DB
            if player_id:
                db.save_session(player_id, score, level)
                personal_best = max(personal_best, score)

            result = screen_game_over(score, level, personal_best)
            if result == "retry":
                continue      # play again with same username
            else:
                break         # back to main menu


if __name__ == "__main__":
    main()