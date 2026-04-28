import pygame
import sys
import math
import datetime

pygame.init()

# ── Window layout constants ────────────────────────────────────────────────────
SCREEN_W   = 900
SCREEN_H   = 700          # slightly taller to fit the expanded toolbar
TOOLBAR_H  = 110          # two rows of tools + palette
CANVAS_TOP = TOOLBAR_H
CANVAS_H   = SCREEN_H - TOOLBAR_H
CANVAS_RECT = pygame.Rect(0, CANVAS_TOP, SCREEN_W, CANVAS_H)

# ── Colour palette ─────────────────────────────────────────────────────────────
BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
LT_GRAY = (230, 230, 230)
MID_GRY = (160, 160, 160)
DK_GRAY = (80,  80,  80)

PALETTE = [
    (0,0,0),(255,255,255),(220,30,30),(30,180,30),(30,80,220),
    (255,220,0),(255,130,0),(140,0,200),(0,200,200),(255,0,180),
    (120,80,40),(100,100,100),(255,160,180),(0,100,60)
]

# ── Tool identifiers ───────────────────────────────────────────────────────────
PENCIL   = "pencil"
RECTANGLE = "rectangle"
CIRCLE   = "circle"
ERASER   = "eraser"
SQUARE   = "square"          
RT_TRI   = "right_tri"       
EQ_TRI   = "equil_tri"       
RHOMBUS  = "rhombus"        
LINE     = "line"
FILL     = "fill"
TEXT     = "text"       

# Rows of tool buttons: row 0 (original), row 1 (new shapes)
TOOLS_ROW0 = [PENCIL, LINE, RECTANGLE, CIRCLE, ERASER, FILL]
ICONS_ROW0 = ["✏ Pencil","/ Line", "▭ Rect", "◯ Circle", "⌫ Eraser", "🪣 Fill"]

TOOLS_ROW1 = [SQUARE, RT_TRI, EQ_TRI, RHOMBUS, TEXT]
ICONS_ROW1 = ["■ Square", "◺ R.Tri", "△ Eq.Tri", "◇ Rhombus","T Text"]

ALL_TOOLS = TOOLS_ROW0 + TOOLS_ROW1   # combined for easy lookup

# ── Pygame singletons ──────────────────────────────────────────────────────────
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Paint")
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("Arial", 15, bold=True)
small  = pygame.font.SysFont("Arial", 13)


# ──────────────────────────────────────────────────────────────────────────────
# Shape-geometry helpers (pure functions, no pygame state)
# ──────────────────────────────────────────────────────────────────────────────

def _square_points(p1, p2):
    """
    Return the four corners of a square whose one side is defined by p1→p2.
    The side length equals the larger of |dx| and |dy|, preserving aspect ratio.
    The square is drawn 'above' the drag direction (perpendicular to the right).
    """
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    # Use the larger dimension so the shape is always square
    side = max(abs(dx), abs(dy))
    sx = side if dx >= 0 else -side
    sy = side if dy >= 0 else -side
    # Four corners of an axis-aligned square
    return [
        (x1,      y1),
        (x1 + sx, y1),
        (x1 + sx, y1 + sy),
        (x1,      y1 + sy),
    ]


def _right_triangle_points(p1, p2):
    """
    Return the three vertices of a right-angle triangle.
    The right angle is always at p1 (top-left of the bounding box).
    The two legs run horizontally to p2.x and vertically to p2.y.

        p1 ──── (x2, y1)
        |      /
        p2 ──'
    """
    x1, y1 = p1
    x2, y2 = p2
    return [(x1, y1), (x2, y1), (x1, y2)]


def _equilateral_triangle_points(p1, p2):
    """
    Return the three vertices of an equilateral triangle.
    p1 is the top-left corner of the bounding box; p2 is the bottom-right.
    Base = |x2-x1|; the apex is centred above (or below) the base.

    The height of an equilateral triangle with base b is  h = (√3/2) · b.
    """
    x1, y1 = p1
    x2, y2 = p2
    base   = abs(x2 - x1)
    height = int(base * math.sqrt(3) / 2)

    # Direction: apex goes in the same vertical direction as the drag
    sign   = 1 if y2 >= y1 else -1

    # Base vertices at y1, apex above (or below) them
    left_x  = min(x1, x2)
    right_x = max(x1, x2)
    apex_x  = (left_x + right_x) // 2
    return [
        (left_x,  y1),
        (right_x, y1),
        (apex_x,  y1 + sign * height),
    ]


def _rhombus_points(p1, p2):
    """
    Return the four vertices of a rhombus (diamond) inscribed in the
    bounding box defined by p1 (drag start) and p2 (current drag position).

    The four mid-points of the bounding-box edges form the rhombus:
        top-centre, right-centre, bottom-centre, left-centre.
    """
    x1, y1 = p1
    x2, y2 = p2
    mx = (x1 + x2) // 2   # horizontal midpoint
    my = (y1 + y2) // 2   # vertical   midpoint
    return [
        (mx, y1),   # top
        (x2, my),   # right
        (mx, y2),   # bottom
        (x1, my),   # left
    ]

def flood_fill(self, x, y, new_color):
    target_color = self.canvas.get_at((x, y))
    if target_color == new_color:
        return

    stack = [(x, y)]

    while stack:
        px, py = stack.pop()

        if px < 0 or px >= SCREEN_W or py < 0 or py >= CANVAS_H:
            continue

        if self.canvas.get_at((px, py)) != target_color:
            continue

        self.canvas.set_at((px, py), new_color)

        stack.append((px+1, py))
        stack.append((px-1, py))
        stack.append((px, py+1))
        stack.append((px, py-1))

# ──────────────────────────────────────────────────────────────────────────────
# Main application class
# ──────────────────────────────────────────────────────────────────────────────

class PaintApp:
    def __init__(self):
        # The canvas is a separate Surface so we can blit snapshots for
        # rubber-band previewing without permanently marking pixels.
        self.canvas = pygame.Surface((SCREEN_W, CANVAS_H))
        self.canvas.fill(WHITE)

        self.color       = BLACK
        self.tool        = PENCIL
        self.brush_size  = 5
        self.eraser_size = 20

        self.drawing    = False
        self.start_pos  = None   # canvas-space drag start
        self.prev_pos   = None   # last canvas-space position (for pencil lines)
        self._snapshot  = None   # canvas copy taken at drag start (for previews)

        self.text_mode = False
        self.text_input = ""
        self.text_pos = (0, 0)

    # ── Event dispatch ─────────────────────────────────────────────────────────

    def handle(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._on_press(event.pos)

        elif event.type == pygame.MOUSEMOTION and self.drawing:
            self._on_drag(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._on_release(event.pos)

        elif event.type == pygame.KEYDOWN:

            #  brush size
            if event.key == pygame.K_1:
                self.brush_size = 2
            elif event.key == pygame.K_2:
                self.brush_size = 5
            elif event.key == pygame.K_3:
                self.brush_size = 10

            #  save
            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                filename = f"paint_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                pygame.image.save(self.canvas, filename)
                print("Saved:", filename)

            #  TEXT TOOL
            elif self.text_mode:
                if event.key == pygame.K_RETURN:
                    txt = font.render(self.text_input, True, self.color)
                    self.canvas.blit(txt, self.text_pos)
                    self.text_mode = False

                elif event.key == pygame.K_ESCAPE:
                    self.text_mode = False

                elif event.key == pygame.K_BACKSPACE:
                    self.text_input = self.text_input[:-1]

                else:
                    self.text_input += event.unicode

    # ── Mouse-press ────────────────────────────────────────────────────────────

    def _on_press(self, pos):
        mx, my = pos

        # Click inside the toolbar → route to toolbar handler, not canvas
        if my < TOOLBAR_H:
            self._toolbar_click(mx, my)
            return

        # Convert screen coordinates to canvas-local coordinates
        cp = (mx, my - CANVAS_TOP)
        self.drawing   = True
        self.start_pos = cp
        self.prev_pos  = cp

        if self.tool == PENCIL:
            # Dot on press so clicks without drag still register
            pygame.draw.circle(self.canvas, self.color, cp, self.brush_size)
        elif self.tool == ERASER:
            pygame.draw.circle(self.canvas, WHITE, cp, self.eraser_size)
        elif self.tool in (RECTANGLE, CIRCLE, SQUARE, RT_TRI, EQ_TRI, RHOMBUS, LINE):
            # Save a snapshot so we can restore the canvas each drag frame
            # (prevents ghost trails while rubber-banding shapes)
            self._snapshot = self.canvas.copy()
        elif self.tool == FILL:
            self.flood_fill(cp[0], cp[1], self.color)
            self.drawing = False

        elif self.tool == TEXT:
            self.text_mode = True
            self.text_input = ""
            self.text_pos = cp

    # ── Mouse-drag ─────────────────────────────────────────────────────────────

    def _on_drag(self, pos):
        mx, my = pos
        # Clamp to canvas bounds
        cx = max(0, min(SCREEN_W - 1, mx))
        cy = max(CANVAS_TOP, min(SCREEN_H - 1, my))
        cp = (cx, cy - CANVAS_TOP)

        if self.tool == PENCIL:
            # Draw a thick line segment from last position to current,
            # then cap with a circle to avoid gaps on sharp turns
            pygame.draw.line(self.canvas, self.color,
                             self.prev_pos, cp, self.brush_size * 2)
            pygame.draw.circle(self.canvas, self.color, cp, self.brush_size)
            self.prev_pos = cp

        elif self.tool == LINE:
            self.canvas.blit(self._snapshot, (0, 0))
            pygame.draw.line(self.canvas, self.color, self.start_pos, cp, self.brush_size)

        elif self.tool == ERASER:
            pygame.draw.circle(self.canvas, WHITE, cp, self.eraser_size)
            self.prev_pos = cp

        elif self.tool in (RECTANGLE, CIRCLE, SQUARE, RT_TRI, EQ_TRI, RHOMBUS, LINE):
            # Restore the snapshot so previous preview frame is erased
            self.canvas.blit(self._snapshot, (0, 0))
            self._draw_shape(self.start_pos, cp, self.canvas)

    # ── Mouse-release ──────────────────────────────────────────────────────────

    def _on_release(self, pos):
        if not self.drawing:
            return

        mx, my = pos
        cx = max(0, min(SCREEN_W - 1, mx))
        cy = max(CANVAS_TOP, min(SCREEN_H - 1, my))
        cp = (cx, cy - CANVAS_TOP)

        # Commit the final shape to the canvas
        if self.tool in (RECTANGLE, CIRCLE, SQUARE, RT_TRI, EQ_TRI, RHOMBUS):
            self.canvas.blit(self._snapshot, (0, 0))
            self._draw_shape(self.start_pos, cp, self.canvas)

        self.drawing    = False
        self.start_pos  = None
        self.prev_pos   = None
        self._snapshot  = None

    # ── Shape dispatcher ───────────────────────────────────────────────────────

    def _draw_shape(self, p1, p2, surface):
        """
        Dispatch to the correct drawing routine for the active tool.
        All shape-tool renderers receive canvas-space p1 / p2.
        """
        col = self.color

        if self.tool == RECTANGLE:
            rect = pygame.Rect(min(p1[0], p2[0]), min(p1[1], p2[1]),
                               abs(p2[0]-p1[0]), abs(p2[1]-p1[1]))
            pygame.draw.rect(surface, col, rect, self.brush_size)

        elif self.tool == CIRCLE:
            cx     = (p1[0] + p2[0]) // 2
            cy     = (p1[1] + p2[1]) // 2
            radius = int(math.hypot(p2[0]-p1[0], p2[1]-p1[1]) / 2)
            if radius > 0:
                pygame.draw.circle(surface, col, (cx, cy), radius, self.brush_size)

        elif self.tool == SQUARE:
            # Use helper to get axis-aligned square vertices then draw polygon
            pts = _square_points(p1, p2)
            if len(pts) >= 3:
                pygame.draw.polygon(surface, col, pts, self.brush_size)

        elif self.tool == RT_TRI:
            # Right-angle at p1; legs are horizontal and vertical
            pts = _right_triangle_points(p1, p2)
            pygame.draw.polygon(surface, col, pts, self.brush_size)

        elif self.tool == EQ_TRI:
            # Equilateral triangle inscribed in the horizontal span of the drag
            pts = _equilateral_triangle_points(p1, p2)
            pygame.draw.polygon(surface, col, pts, self.brush_size)

        elif self.tool == RHOMBUS:
            # Diamond whose tips touch the four edge midpoints of the bounding box
            pts = _rhombus_points(p1, p2)
            pygame.draw.polygon(surface, col, pts, self.brush_size)

        elif self.tool == LINE:
            pygame.draw.line(surface, col, p1, p2, self.brush_size)

    def flood_fill(self, x, y, new_color):
        target_color = self.canvas.get_at((x, y))

        if target_color == new_color:
            return

        stack = [(x, y)]

        while stack:
            px, py = stack.pop()

            # borders
            if px < 0 or px >= SCREEN_W or py < 0 or py >= CANVAS_H:
                continue

            if self.canvas.get_at((px, py)) != target_color:
                continue

            # fill
            self.canvas.set_at((px, py), new_color)

            # neighbours
            stack.append((px + 1, py))
            stack.append((px - 1, py))
            stack.append((px, py + 1))
            stack.append((px, py - 1))

    # ── Toolbar click handler ──────────────────────────────────────────────────

    def _toolbar_click(self, mx, my):
        """
        Handle clicks in the toolbar area.
        Layout (y ranges):
          Row 0 (y  6-34):  colour palette swatches
          Row 1 (y 38-62):  original tools (pencil / rect / circle / eraser)
          Row 2 (y 70-94):  new shape tools (square / right-tri / eq-tri / rhombus)
          Right zone:        brush / eraser size controls + preview swatch + Clear
        """
        # ── Colour palette (row 0) ─────────────────────────────────────────────
        for i, col in enumerate(PALETTE):
            sx = 10 + i * 38
            if sx <= mx <= sx + 32 and 6 <= my <= 34:
                self.color = col
                return

        # ── Original tool buttons (row 1) ─────────────────────────────────────
        for i, tool in enumerate(TOOLS_ROW0):
            tx = 10 + i * 105
            if tx <= mx <= tx + 97 and 38 <= my <= 62:
                self.tool = tool
                return

        # ── New shape buttons (row 2) ──────────────────────────────────────────
        for i, tool in enumerate(TOOLS_ROW1):
            tx = 10 + i * 105
            if tx <= mx <= tx + 97 and 70 <= my <= 94:
                self.tool = tool
                return

        # ── Brush size −/+ (right zone, row 0) ────────────────────────────────
        if 555 <= mx <= 577 and 6 <= my <= 28:
            self.brush_size = max(1, self.brush_size - 1)
        elif 581 <= mx <= 603 and 6 <= my <= 28:
            self.brush_size = min(40, self.brush_size + 1)

        # ── Eraser size −/+ (right zone, row 1) ───────────────────────────────
        if 555 <= mx <= 577 and 36 <= my <= 58:
            self.eraser_size = max(5, self.eraser_size - 2)
        elif 581 <= mx <= 603 and 36 <= my <= 58:
            self.eraser_size = min(60, self.eraser_size + 2)

        # ── Clear button ───────────────────────────────────────────────────────
        if SCREEN_W - 80 <= mx <= SCREEN_W - 10 and 38 <= my <= 68:
            self.canvas.fill(WHITE)

    # ── Render ─────────────────────────────────────────────────────────────────

    def draw(self, surface):
        """Blit the canvas then draw all toolbar UI on top."""
        # Canvas first (sits below toolbar visually)
        surface.blit(self.canvas, (0, CANVAS_TOP))

        # Eraser preview cursor
        if self.tool == ERASER:
            mx, my = pygame.mouse.get_pos()
            pygame.draw.circle(surface, MID_GRY, (mx, my), self.eraser_size, self.brush_size)

        # ── Toolbar background ─────────────────────────────────────────────────
        pygame.draw.rect(surface, LT_GRAY, (0, 0, SCREEN_W, TOOLBAR_H))
        pygame.draw.line(surface, MID_GRY, (0, TOOLBAR_H), (SCREEN_W, TOOLBAR_H), self.brush_size)

        # ── Colour palette swatches ────────────────────────────────────────────
        for i, col in enumerate(PALETTE):
            sx = 10 + i * 38
            pygame.draw.rect(surface, col, (sx, 6, 32, 28))
            border = BLACK if col == self.color else DK_GRAY
            thick  = 3 if col == self.color else 1
            pygame.draw.rect(surface, border, (sx, 6, 32, 28), thick)

        # ── Row 1 tool buttons ─────────────────────────────────────────────────
        for i, (tool, icon) in enumerate(zip(TOOLS_ROW0, ICONS_ROW0)):
            tx      = 10 + i * 105
            btn_col = (120, 120, 120) if tool == self.tool else (180, 180, 180)
            pygame.draw.rect(surface, btn_col, (tx, 38, 97, 26))
            lbl = font.render(icon, True, BLACK)
            surface.blit(lbl, (tx + 48 - lbl.get_width() // 2, 44))

        # ── Row 2 new shape buttons ────────────────────────────────────────────
        for i, (tool, icon) in enumerate(zip(TOOLS_ROW1, ICONS_ROW1)):
            tx      = 10 + i * 105
            btn_col = (120, 120, 120) if tool == self.tool else (180, 180, 180)
            pygame.draw.rect(surface, btn_col, (tx, 70, 97, 26))
            lbl = font.render(icon, True, BLACK)
            surface.blit(lbl, (tx + 48 - lbl.get_width() // 2, 76))

        # ── Size controls (brush + eraser) ─────────────────────────────────────
        self._draw_size_control(surface, 548,  6, "Brush", self.brush_size)
        self._draw_size_control(surface, 548, 36, "Ersr",  self.eraser_size)

        # ── Active-colour preview swatch ───────────────────────────────────────
        pygame.draw.rect(surface, self.color, (SCREEN_W - 130, 10, 40, 40))
        pygame.draw.rect(surface, BLACK,      (SCREEN_W - 130, 10, 40, 40), self.brush_size)

        # ── Clear button ───────────────────────────────────────────────────────
        pygame.draw.rect(surface, (200, 50, 50), (SCREEN_W - 80, 38, 70, 30))
        ct = font.render("Clear", True, WHITE)
        surface.blit(ct, (SCREEN_W - 80 + 35 - ct.get_width() // 2, 44))

        # ── TEXT TOOL ──────────────────────────────────────────────────────────
        if self.text_mode:
            txt = font.render(self.text_input, True, self.color)
            surface.blit(txt, (self.text_pos[0], self.text_pos[1] + CANVAS_TOP))

    def _draw_size_control(self, surface, x, y, label, value):
        """Render a labelled −/+ size control at position (x, y) in the toolbar."""
        lbl = small.render(f"{label}: {value}", True, DK_GRAY)
        surface.blit(lbl, (x, y + 2))
        # Minus button
        pygame.draw.rect(surface, MID_GRY, (x + 78, y, 22, 22))
        surface.blit(font.render("-", True, BLACK), (x + 84, y + 2))
        # Plus button
        pygame.draw.rect(surface, MID_GRY, (x + 104, y, 22, 22))
        surface.blit(font.render("+", True, BLACK), (x + 108, y + 2))


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

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