"""
ui.py – All non-gameplay Pygame screens:
    • main_menu()       → "play" | "leaderboard" | "settings" | "quit"
    • username_screen() → str  (the entered name)
    • settings_screen() → updated settings dict
    • leaderboard_screen()
    • game_over_screen() → "retry" | "menu"
"""

import pygame
import sys
from persistence import load_leaderboard, save_settings

# ── Shared colours ─────────────────────────────────────────────────────────────
BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
GRAY    = (80,  80,  80)
DGRAY   = (40,  40,  40)
LGRAY   = (160, 160, 160)
YELLOW  = (255, 215,   0)
RED     = (210,  30,  30)
GREEN   = (0,   200,  70)
BLUE    = (30,   90, 210)
PURPLE  = (160,   0, 200)
TEAL    = (0,   190, 190)
ORANGE  = (230, 120,   0)
ROAD_BG = (50,   50,  50)

# ── Car colour map ─────────────────────────────────────────────────────────────
CAR_COLORS = {
    "blue":   (30,   90, 210),
    "red":    (210,  30,  30),
    "green":  (20,  180,  50),
    "purple": (160,   0, 200),
}

SCREEN_W, SCREEN_H = 400, 600


# ── Font helpers ───────────────────────────────────────────────────────────────
def _fonts():
    title  = pygame.font.SysFont("Arial", 52, bold=True)
    header = pygame.font.SysFont("Arial", 30, bold=True)
    body   = pygame.font.SysFont("Arial", 22, bold=True)
    small  = pygame.font.SysFont("Arial", 16)
    return title, header, body, small


# ── Generic button helper ──────────────────────────────────────────────────────
class Button:
    PAD_X, PAD_Y = 28, 10

    def __init__(self, text: str, cx: int, cy: int, font,
                 color=TEAL, text_color=BLACK, width: int = None, height: int = None):
        self.font       = font
        self.text       = text
        self.color      = color
        self.text_color = text_color
        surf            = font.render(text, True, text_color)
        w = (width  or surf.get_width()  + self.PAD_X * 2)
        h = (height or surf.get_height() + self.PAD_Y * 2)
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (cx, cy)

    def draw(self, surface, hovered=False):
        col = tuple(min(255, c + 40) for c in self.color) if hovered else self.color
        pygame.draw.rect(surface, col,   self.rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
        lbl = self.font.render(self.text, True, self.text_color)
        surface.blit(lbl, (self.rect.centerx - lbl.get_width()  // 2,
                            self.rect.centery - lbl.get_height() // 2))

    def is_hovered(self, pos) -> bool:
        return self.rect.collidepoint(pos)

    def clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and
                self.rect.collidepoint(event.pos))


# ── Background gradient ────────────────────────────────────────────────────────
def _draw_bg(surface):
    """Draw a simple dark vertical gradient as the menu background."""
    for y in range(SCREEN_H):
        t   = y / SCREEN_H
        r   = int(10  + 30  * t)
        g   = int(10  + 20  * t)
        b   = int(30  + 50  * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_W, y))


# ── Main Menu ──────────────────────────────────────────────────────────────────
def main_menu(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    Blocking call; returns one of: 'play' | 'leaderboard' | 'settings' | 'quit'.
    """
    title_f, _, body_f, _ = _fonts()
    cx = SCREEN_W // 2

    buttons = [
        Button("PLAY",        cx, 260, body_f, color=GREEN,  text_color=BLACK),
        Button("LEADERBOARD", cx, 320, body_f, color=YELLOW, text_color=BLACK),
        Button("SETTINGS",    cx, 380, body_f, color=TEAL,   text_color=BLACK),
        Button("QUIT",        cx, 440, body_f, color=RED,    text_color=WHITE),
    ]
    actions = ["play", "leaderboard", "settings", "quit"]

    while True:
        _draw_bg(screen)
        mouse = pygame.mouse.get_pos()

        # Title
        t1 = title_f.render("RACER", True, YELLOW)
        t2 = title_f.render("EXTREME", True, ORANGE)
        screen.blit(t1, (cx - t1.get_width() // 2, 100))
        screen.blit(t2, (cx - t2.get_width() // 2, 155))

        # Decorative road stripe
        pygame.draw.rect(screen, ROAD_BG, (130, 210, 140, 6))
        pygame.draw.rect(screen, WHITE,   (185, 210,  30, 6))

        for i, btn in enumerate(buttons):
            btn.draw(screen, btn.is_hovered(mouse))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            for i, btn in enumerate(buttons):
                if btn.clicked(event):
                    return actions[i]


# ── Username entry ─────────────────────────────────────────────────────────────
def username_screen(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """Returns the entered username (max 16 chars, stripped). Never empty."""
    _, header_f, body_f, small_f = _fonts()
    cx       = SCREEN_W // 2
    name     = ""
    ok_btn   = Button("START RACE", cx, 420, body_f, color=GREEN, text_color=BLACK, width=200)
    cursor_v = True
    cursor_t = 0

    while True:
        _draw_bg(screen)
        mouse = pygame.mouse.get_pos()

        hdr = header_f.render("Enter Your Name", True, WHITE)
        screen.blit(hdr, (cx - hdr.get_width() // 2, 160))

        # Input box
        box = pygame.Rect(80, 230, 240, 46)
        pygame.draw.rect(screen, DGRAY,  box, border_radius=6)
        pygame.draw.rect(screen, TEAL,   box, 2, border_radius=6)
        cursor_t += 1
        if cursor_t > 30:
            cursor_v = not cursor_v; cursor_t = 0
        display = name + ("|" if cursor_v else " ")
        txt_s = body_f.render(display, True, WHITE)
        screen.blit(txt_s, (box.x + 10, box.y + (box.height - txt_s.get_height()) // 2))

        hint = small_f.render("Up to 16 characters", True, LGRAY)
        screen.blit(hint, (cx - hint.get_width() // 2, 285))

        ok_btn.draw(screen, ok_btn.is_hovered(mouse))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip():
                    return name.strip()
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 16 and event.unicode.isprintable():
                    name += event.unicode
            if ok_btn.clicked(event) and name.strip():
                return name.strip()


# ── Settings Screen ────────────────────────────────────────────────────────────
def settings_screen(screen: pygame.Surface, clock: pygame.time.Clock,
                    settings: dict) -> dict:
    """Mutates and returns the settings dict; saves to disk on Back."""
    _, header_f, body_f, small_f = _fonts()
    cx      = SCREEN_W // 2
    s       = dict(settings)   # work on a copy

    back_btn = Button("BACK", cx, 540, body_f, color=GRAY, text_color=WHITE, width=160)

    # Toggle / cycle helpers
    def toggle_row(label, key, values, labels, y):
        """Draw a row with left/right arrows to cycle through values."""
        lbl_s = body_f.render(label, True, LGRAY)
        screen.blit(lbl_s, (60, y))
        idx     = values.index(s[key]) if s[key] in values else 0
        val_lbl = body_f.render(labels[idx], True, YELLOW)
        screen.blit(val_lbl, (270, y))
        # arrows
        left  = pygame.Rect(245,  y, 20, 28)
        right = pygame.Rect(350,  y, 20, 28)
        pygame.draw.polygon(screen, WHITE, [(left.right,  left.top),
                                             (left.left,   left.centery),
                                             (left.right,  left.bottom)])
        pygame.draw.polygon(screen, WHITE, [(right.left,  right.top),
                                             (right.right, right.centery),
                                             (right.left,  right.bottom)])
        return left, right, values, idx

    while True:
        _draw_bg(screen)
        mouse = pygame.mouse.get_pos()

        hdr = header_f.render("SETTINGS", True, WHITE)
        screen.blit(hdr, (cx - hdr.get_width() // 2, 60))
        pygame.draw.line(screen, TEAL, (60, 104), (340, 104), 2)

        rows = {}  # name → (left_rect, right_rect, values, cur_idx)

        # Sound
        rows["sound"] = toggle_row(
            "Sound",  "sound",
            [True, False], ["ON", "OFF"], 150)

        # Car colour
        rows["car_color"] = toggle_row(
            "Car Colour", "car_color",
            ["blue", "red", "green", "purple"],
            ["Blue", "Red", "Green", "Purple"], 220)

        # Preview car colour swatch
        pygame.draw.rect(screen, CAR_COLORS[s["car_color"]], (310, 218, 28, 28), border_radius=4)
        pygame.draw.rect(screen, WHITE, (310, 218, 28, 28), 1, border_radius=4)

        # Difficulty
        rows["difficulty"] = toggle_row(
            "Difficulty", "difficulty",
            ["easy", "normal", "hard"],
            ["Easy", "Normal", "Hard"], 290)

        back_btn.draw(screen, back_btn.is_hovered(mouse))
        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, (left_r, right_r, values, idx) in rows.items():
                    if left_r.collidepoint(event.pos):
                        s[key] = values[(idx - 1) % len(values)]
                    elif right_r.collidepoint(event.pos):
                        s[key] = values[(idx + 1) % len(values)]
                if back_btn.clicked(event):
                    save_settings(s)
                    return s


# ── Leaderboard Screen ─────────────────────────────────────────────────────────
def leaderboard_screen(screen: pygame.Surface, clock: pygame.time.Clock) -> None:
    """Display the top-10 saved scores."""
    _, header_f, body_f, small_f = _fonts()
    cx       = SCREEN_W // 2
    entries  = load_leaderboard()
    back_btn = Button("BACK", cx, 555, body_f, color=GRAY, text_color=WHITE, width=160)

    while True:
        _draw_bg(screen)
        mouse = pygame.mouse.get_pos()

        hdr = header_f.render("LEADERBOARD", True, YELLOW)
        screen.blit(hdr, (cx - hdr.get_width() // 2, 28))
        pygame.draw.line(screen, YELLOW, (40, 72), (360, 72), 2)

        # Column headers
        col_labels = [("RANK", 38), ("NAME", 90), ("SCORE", 255), ("DIST", 345)]
        for lbl, x in col_labels:
            s = small_f.render(lbl, True, LGRAY)
            screen.blit(s, (x, 82))
        pygame.draw.line(screen, GRAY, (30, 100), (370, 100), 1)

        if not entries:
            msg = body_f.render("No scores yet!", True, LGRAY)
            screen.blit(msg, (cx - msg.get_width() // 2, 260))
        else:
            for i, e in enumerate(entries[:10]):
                y      = 108 + i * 36
                rank_c = YELLOW if i == 0 else (LGRAY if i == 1 else (ORANGE if i == 2 else WHITE))
                rank_s = body_f.render(f"#{i+1}", True, rank_c)
                name_s = body_f.render(str(e.get("name","?"))[:12], True, WHITE)
                scr_s  = body_f.render(str(e.get("score", 0)), True, GREEN)
                dst_s  = small_f.render(f'{e.get("distance", 0)} m', True, TEAL)
                screen.blit(rank_s, (38,  y))
                screen.blit(name_s, (90,  y))
                screen.blit(scr_s,  (255, y))
                screen.blit(dst_s,  (345, y + 4))
                if i % 2 == 1:
                    bar = pygame.Surface((340, 34), pygame.SRCALPHA)
                    bar.fill((255, 255, 255, 10))
                    screen.blit(bar, (30, y - 2))

        back_btn.draw(screen, back_btn.is_hovered(mouse))
        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if back_btn.clicked(event):
                return


# ── Game Over Screen ───────────────────────────────────────────────────────────
def game_over_screen(screen: pygame.Surface, clock: pygame.time.Clock,
                     score: int, distance: int, coin_value: int) -> str:
    """Returns 'retry' or 'menu'."""
    title_f, header_f, body_f, small_f = _fonts()
    cx = SCREEN_W // 2

    retry_btn = Button("RETRY",    cx, 400, body_f, color=GREEN,  text_color=BLACK, width=200)
    menu_btn  = Button("MAIN MENU", cx, 460, body_f, color=TEAL,   text_color=BLACK, width=200)

    while True:
        _draw_bg(screen)
        mouse = pygame.mouse.get_pos()

        # Overlay
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 100))
        screen.blit(ov, (0, 0))

        go = title_f.render("GAME OVER", True, RED)
        screen.blit(go, (cx - go.get_width() // 2, 120))

        stats = [
            (f"Score     {score}",     WHITE),
            (f"Distance  {distance} m", TEAL),
            (f"Coins     {coin_value} pts", YELLOW),
        ]
        for i, (txt, col) in enumerate(stats):
            s = body_f.render(txt, True, col)
            screen.blit(s, (cx - s.get_width() // 2, 230 + i * 44))

        retry_btn.draw(screen, retry_btn.is_hovered(mouse))
        menu_btn.draw(screen,  menu_btn.is_hovered(mouse))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if retry_btn.clicked(event): return "retry"
            if menu_btn.clicked(event):  return "menu"