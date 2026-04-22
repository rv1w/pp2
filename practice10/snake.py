import pygame
import random
import sys

pygame.init()

CELL = 20
COLS, ROWS = 20, 20
HUD_H = 50

SCREEN_W = CELL * COLS
SCREEN_H = CELL * ROWS + HUD_H

BASE_FPS = 8
FPS_PER_LEVEL = 2
FOODS_PER_LEVEL = 3

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN_BG = (40, 170, 40)
RED = (220, 40, 40)
YELLOW = (255, 215, 0)
GRAY = (30, 30, 30)
LT_GRAY = (60, 60, 60)
GOLD = (255, 200, 0)
BLUE_HEAD = (40, 90, 220)
BLUE_BODY = (70, 130, 255)
GRID_GREEN = (30, 140, 30)

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22, bold=True)
big = pygame.font.SysFont("Arial", 44, bold=True)

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

def random_food(occupied: set) -> tuple:
    while True:
        c = random.randint(1, COLS - 2)
        r = random.randint(1, ROWS - 2)
        if (c, r) not in occupied:
            return (c, r)

class Snake:
    def __init__(self):
        cx, cy = COLS // 2, ROWS // 2
        self.body = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = RIGHT
        self._queued = RIGHT
        self._grow = False

    def queue_direction(self, new_dir: tuple):
        if new_dir != OPPOSITE.get(self.direction):
            self._queued = new_dir

    def move(self):
        self.direction = self._queued
        hx, hy = self.body[0]
        new_head = (hx + self.direction[0], hy + self.direction[1])
        self.body.insert(0, new_head)
        if self._grow:
            self._grow = False
        else:
            self.body.pop()

    def eat(self):
        self._grow = True

    def hit_wall(self) -> bool:
        hx, hy = self.body[0]
        return not (0 <= hx < COLS and 0 <= hy < ROWS)

    def hit_self(self) -> bool:
        return self.body[0] in self.body[1:]

    def draw(self, surface):
        for i, (c, r) in enumerate(self.body):
            x = c * CELL
            y = r * CELL + HUD_H
            col = BLUE_HEAD if i == 0 else BLUE_BODY
            pygame.draw.rect(surface, col, (x + 2, y + 2, CELL - 4, CELL - 4),border_radius=3)

            if i == 0:
                pygame.draw.circle(surface, WHITE, (x + 5, y + 6), 3)
                pygame.draw.circle(surface, WHITE, (x + 14, y + 6), 3)
                pygame.draw.circle(surface, BLACK, (x + 5, y + 6), 1)
                pygame.draw.circle(surface, BLACK, (x + 14, y + 6), 1)

    @property
    def cells(self) -> set:
        return set(self.body)

class Food:
    def __init__(self, occupied: set):
        self.pos = random_food(occupied)

    def draw(self, surface):
        c, r = self.pos
        cx = c * CELL + CELL // 2
        cy = r * CELL + CELL // 2 + HUD_H
        pygame.draw.circle(surface, RED, (cx, cy), CELL // 2 - 2)
        pygame.draw.circle(surface, (255, 120, 120), (cx - 3, cy - 3), 3)

def draw_hud(surface, score: int, level: int, foods_this_level: int):
    pygame.draw.rect(surface, GRAY, (0, 0, SCREEN_W, HUD_H))
    pygame.draw.line(surface, LT_GRAY, (0, HUD_H), (SCREEN_W, HUD_H), 2)

    sc = font.render(f"Score: {score}", True, WHITE)
    lv = font.render(f"Level {level}", True, GOLD)
    nxt = font.render(f"Next ↑: {FOODS_PER_LEVEL - foods_this_level % FOODS_PER_LEVEL}", True, YELLOW)

    surface.blit(sc, (12, HUD_H // 2 - sc.get_height() // 2))
    surface.blit(lv, (SCREEN_W // 2 - lv.get_width() // 2, HUD_H // 2 - lv.get_height() // 2))
    surface.blit(nxt, (SCREEN_W - nxt.get_width() - 12, HUD_H // 2 - nxt.get_height() // 2))

def draw_border(surface):
    pygame.draw.rect(surface, LT_GRAY, (0, HUD_H, SCREEN_W, CELL * ROWS), 2)

def draw_overlay(surface, title: str, sub: str = ""):
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

def main():
    snake = Snake()
    food = Food(snake.cells)

    score = 0
    level = 1
    total_foods_eaten = 0
    current_fps = BASE_FPS
    game_over = False

    while True:
        clock.tick(current_fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        main()
                        return
                    if event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
                else:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        snake.queue_direction(UP)
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        snake.queue_direction(DOWN)
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        snake.queue_direction(LEFT)
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        snake.queue_direction(RIGHT)

        if not game_over:
            snake.move()

            if snake.hit_wall():
                game_over = True
            elif snake.hit_self():
                game_over = True
            elif snake.body[0] == food.pos:
                snake.eat()
                total_foods_eaten += 1
                score += 10 * level

                new_level = total_foods_eaten // FOODS_PER_LEVEL + 1
                if new_level > level:
                    level = new_level
                    current_fps = BASE_FPS + (level - 1) * FPS_PER_LEVEL

                food = Food(snake.cells)

        screen.fill(GREEN_BG)
        draw_hud(screen, score, level, total_foods_eaten % FOODS_PER_LEVEL if total_foods_eaten else 0)

        for c in range(COLS):
            for r in range(ROWS):
                pygame.draw.rect(screen, GRID_GREEN, (c * CELL, r * CELL + HUD_H, CELL, CELL), 1)

        draw_border(screen)
        food.draw(screen)
        snake.draw(screen)

        if game_over:
            draw_overlay(screen, "GAME OVER", f"Score: {score}   Level: {level}")

        pygame.display.flip()

if __name__ == "__main__":
    main()