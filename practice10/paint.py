import pygame
import sys
import math

pygame.init()

SCREEN_W = 900
SCREEN_H = 650
TOOLBAR_H = 70
CANVAS_TOP = TOOLBAR_H
CANVAS_H = SCREEN_H - TOOLBAR_H
CANVAS_RECT = pygame.Rect(0, CANVAS_TOP, SCREEN_W, CANVAS_H)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LT_GRAY = (230, 230, 230)
MID_GRY = (160, 160, 160)
DK_GRAY = (80, 80, 80)

PALETTE = [
    (0,0,0),(255,255,255),(220,30,30),(30,180,30),(30,80,220),
    (255,220,0),(255,130,0),(140,0,200),(0,200,200),(255,0,180),
    (120,80,40),(100,100,100),(255,160,180),(0,100,60)
]

PENCIL = "pencil"
RECTANGLE = "rectangle"
CIRCLE = "circle"
ERASER = "eraser"
TOOLS = [PENCIL, RECTANGLE, CIRCLE, ERASER]
ICONS = ["✏ Pencil", "▭ Rect", "◯ Circle", "⌫ Eraser"]

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Paint")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 15, bold=True)
small = pygame.font.SysFont("Arial", 13)

class PaintApp:
    def __init__(self):
        self.canvas = pygame.Surface((SCREEN_W, CANVAS_H))
        self.canvas.fill(WHITE)

        self.color = BLACK
        self.tool = PENCIL
        self.brush_size = 5
        self.eraser_size = 20

        self.drawing = False
        self.start_pos = None
        self.prev_pos = None
        self._snapshot = None

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._on_press(event.pos)
        elif event.type == pygame.MOUSEMOTION and self.drawing:
            self._on_drag(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._on_release(event.pos)

    def _on_press(self, pos):
        mx, my = pos
        if my < TOOLBAR_H:
            self._toolbar_click(mx, my)
            return

        cp = (mx, my - CANVAS_TOP)
        self.drawing = True
        self.start_pos = cp
        self.prev_pos = cp

        if self.tool == PENCIL:
            pygame.draw.circle(self.canvas, self.color, cp, self.brush_size)
        elif self.tool == ERASER:
            pygame.draw.circle(self.canvas, WHITE, cp, self.eraser_size)
        elif self.tool in (RECTANGLE, CIRCLE):
            self._snapshot = self.canvas.copy()

    def _on_drag(self, pos):
        mx, my = pos
        cx = max(0, min(SCREEN_W - 1, mx))
        cy = max(CANVAS_TOP, min(SCREEN_H - 1, my))
        cp = (cx, cy - CANVAS_TOP)

        if self.tool == PENCIL:
            pygame.draw.line(self.canvas, self.color, self.prev_pos, cp, self.brush_size * 2)
            pygame.draw.circle(self.canvas, self.color, cp, self.brush_size)
            self.prev_pos = cp

        elif self.tool == ERASER:
            pygame.draw.circle(self.canvas, WHITE, cp, self.eraser_size)
            self.prev_pos = cp

        elif self.tool in (RECTANGLE, CIRCLE):
            self.canvas.blit(self._snapshot, (0, 0))
            self._draw_shape(self.start_pos, cp, self.canvas)

    def _on_release(self, pos):
        if not self.drawing:
            return

        mx, my = pos
        cx = max(0, min(SCREEN_W - 1, mx))
        cy = max(CANVAS_TOP, min(SCREEN_H - 1, my))
        cp = (cx, cy - CANVAS_TOP)

        if self.tool in (RECTANGLE, CIRCLE):
            self.canvas.blit(self._snapshot, (0, 0))
            self._draw_shape(self.start_pos, cp, self.canvas)

        self.drawing = False
        self.start_pos = None
        self.prev_pos = None
        self._snapshot = None

    def _draw_shape(self, p1, p2, surface):
        x1, y1 = p1
        x2, y2 = p2

        if self.tool == RECTANGLE:
            rect = pygame.Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            pygame.draw.rect(surface, self.color, rect, 2)

        elif self.tool == CIRCLE:
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            radius = int(math.hypot(x2 - x1, y2 - y1) / 2)
            if radius > 0:
                pygame.draw.circle(surface, self.color, (cx, cy), radius, 2)

    def _toolbar_click(self, mx, my):
        for i, col in enumerate(PALETTE):
            sx = 10 + i * 38
            if sx <= mx <= sx + 32 and 6 <= my <= 34:
                self.color = col
                return

        for i, tool in enumerate(TOOLS):
            tx = 10 + i * 100
            if tx <= mx <= tx + 92 and 38 <= my <= 62:
                self.tool = tool
                return

        if 628 <= mx <= 650 and 6 <= my <= 28:
            self.brush_size = max(1, self.brush_size - 1)
        elif 654 <= mx <= 676 and 6 <= my <= 28:
            self.brush_size = min(40, self.brush_size + 1)

        if 628 <= mx <= 650 and 36 <= my <= 58:
            self.eraser_size = max(5, self.eraser_size - 2)
        elif 654 <= mx <= 676 and 36 <= my <= 58:
            self.eraser_size = min(60, self.eraser_size + 2)

        if SCREEN_W - 80 <= mx <= SCREEN_W - 10 and 20 <= my <= 50:
            self.canvas.fill(WHITE)

    def draw(self, surface):
        surface.blit(self.canvas, (0, CANVAS_TOP))

        mx, my = pygame.mouse.get_pos()

        if self.tool == ERASER:
            pygame.draw.circle(surface, MID_GRY, (mx, my), self.eraser_size, 2)

        pygame.draw.rect(surface, LT_GRAY, (0, 0, SCREEN_W, TOOLBAR_H))
        pygame.draw.line(surface, MID_GRY, (0, TOOLBAR_H), (SCREEN_W, TOOLBAR_H), 2)

        for i, col in enumerate(PALETTE):
            sx = 10 + i * 38
            pygame.draw.rect(surface, col, (sx, 6, 32, 28))
            border = BLACK if col == self.color else DK_GRAY
            thick = 3 if col == self.color else 1
            pygame.draw.rect(surface, border, (sx, 6, 32, 28), thick)

        for i, (tool, icon) in enumerate(zip(TOOLS, ICONS)):
            tx = 10 + i * 100
            btn_col = (180,180,180) if tool != self.tool else (120,120,120)
            pygame.draw.rect(surface, btn_col, (tx, 38, 92, 26))
            lbl = font.render(icon, True, BLACK)
            surface.blit(lbl, (tx + 46 - lbl.get_width()//2, 44))

        self._draw_size_control(surface, 550, 6, "Brush", self.brush_size)
        self._draw_size_control(surface, 550, 36, "Ersr", self.eraser_size)

        pygame.draw.rect(surface, self.color, (SCREEN_W - 180, 10, 40, 40))
        pygame.draw.rect(surface, BLACK, (SCREEN_W - 180, 10, 40, 40), 2)

        pygame.draw.rect(surface, (200,50,50), (SCREEN_W - 80, 20, 70, 28))
        ct = font.render("Clear", True, WHITE)
        surface.blit(ct, (SCREEN_W - 80 + 35 - ct.get_width()//2, 25))

    def _draw_size_control(self, surface, x, y, label, value):
        lbl = small.render(f"{label}: {value}", True, DK_GRAY)
        surface.blit(lbl, (x, y + 2))
        pygame.draw.rect(surface, MID_GRY, (x + 78, y, 22, 22))
        surface.blit(font.render("-", True, BLACK), (x + 84, y + 2))
        pygame.draw.rect(surface, MID_GRY, (x + 104, y, 22, 22))
        surface.blit(font.render("+", True, BLACK), (x + 108, y + 2))

def main():
    app = PaintApp()

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            app.handle(event)

        screen.fill(WHITE)
        app.draw(screen)
        pygame.display.flip()

if __name__ == "__main__":
    main()