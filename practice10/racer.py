import pygame
import random
import sys

pygame.init()

SCREEN_W, SCREEN_H = 400, 600
FPS = 60

ROAD_LEFT = 60
ROAD_RIGHT = 340
LANE_W = (ROAD_RIGHT - ROAD_LEFT) // 3

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 90, 90)
DKGRAY = (50, 50, 50)
YELLOW = (255, 215, 0)
GOLD = (200, 160, 0)
RED = (210, 30, 30)
BLUE = (30, 90, 210)
LT_BLU = (160, 210, 255)
GRASS = (45, 120, 45)
GREEN = (0, 180, 0)

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Racer")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22, bold=True)
big = pygame.font.SysFont("Arial", 48, bold=True)
small = pygame.font.SysFont("Arial", 14, bold=True)

def random_lane_x(obj_width):
    lane = random.randint(0, 2)
    return ROAD_LEFT + lane * LANE_W + (LANE_W - obj_width) // 2

class Road:
    LINE_H = 55
    LINE_GAP = 35
    SEGMENT = LINE_H + LINE_GAP

    def __init__(self):
        self.offset = 0
        self.speed = 5

    def update(self):
        self.offset = (self.offset + self.speed) % self.SEGMENT

    def draw(self, surface):
        surface.fill(GRASS)
        pygame.draw.rect(surface, GRAY, (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_H))
        pygame.draw.rect(surface, WHITE, (ROAD_LEFT - 4, 0, 4, SCREEN_H))
        pygame.draw.rect(surface, WHITE, (ROAD_RIGHT, 0, 4, SCREEN_H))
        for lane in range(1, 3):
            x = ROAD_LEFT + LANE_W * lane - 2
            y = self.offset - self.SEGMENT
            while y < SCREEN_H:
                pygame.draw.rect(surface, WHITE, (x, y, 4, self.LINE_H))
                y += self.SEGMENT

class PlayerCar:
    W, H = 38, 68

    def __init__(self):
        self.x = SCREEN_W // 2 - self.W // 2
        self.y = SCREEN_H - 110
        self.spd = 5

    def draw(self, surface):
        x, y, w, h = self.x, self.y, self.W, self.H
        pygame.draw.rect(surface, BLUE, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, LT_BLU, (x + 5, y + 8, w - 10, 18))
        pygame.draw.rect(surface, LT_BLU, (x + 5, y + h - 22, w - 10, 12))
        for wx, wy in [(x-6, y+6), (x+w-2, y+6), (x-6, y+h-22), (x+w-2, y+h-22)]:
            pygame.draw.rect(surface, BLACK, (wx, wy, 8, 14), border_radius=2)

    def move(self, keys):
        if keys[pygame.K_a] and self.x > ROAD_LEFT:
            self.x -= self.spd
        if keys[pygame.K_d] and self.x + self.W < ROAD_RIGHT:
            self.x += self.spd
        if keys[pygame.K_w] and self.y > 0:
            self.y -= self.spd
        if keys[pygame.K_s] and self.y + self.H < SCREEN_H:
            self.y += self.spd

    def rect(self):
        return pygame.Rect(self.x + 4, self.y + 4, self.W - 8, self.H - 8)

class EnemyCar:
    W, H = 38, 68

    def __init__(self, speed):
        self.x = random_lane_x(self.W)
        self.y = -self.H - random.randint(0, 60)
        self.spd = speed
        self.col = random.choice([(200, 40, 40), (180, 90, 0), (140, 0, 140)])

    def draw(self, surface):
        x, y, w, h = self.x, self.y, self.W, self.H
        pygame.draw.rect(surface, self.col, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, LT_BLU, (x+5, y+h-22, w-10, 12))
        for wx, wy in [(x-6, y+6), (x+w-2, y+6), (x-6, y+h-22), (x+w-2, y+h-22)]:
            pygame.draw.rect(surface, BLACK, (wx, wy, 8, 14), border_radius=2)

    def update(self):
        self.y += self.spd

    def off_screen(self):
        return self.y > SCREEN_H

    def rect(self):
        return pygame.Rect(self.x + 4, self.y + 4, self.W - 8, self.H - 8)

class Coin:
    R = 11

    def __init__(self, speed):
        self.x = random.randint(ROAD_LEFT + self.R + 2, ROAD_RIGHT - self.R - 2)
        self.y = -self.R
        self.spd = speed

    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (self.x, self.y), self.R)
        pygame.draw.circle(surface, GOLD, (self.x, self.y), self.R, 2)
        lbl = small.render("$", True, GOLD)
        surface.blit(lbl, (self.x - lbl.get_width()//2, self.y - lbl.get_height()//2))

    def update(self):
        self.y += self.spd

    def off_screen(self):
        return self.y - self.R > SCREEN_H

    def rect(self):
        return pygame.Rect(self.x - self.R, self.y - self.R, self.R*2, self.R*2)

def draw_hud(surface, score, coins):
    s = font.render(f"Score: {score}", True, WHITE)
    c = font.render(f"Coins: {coins}", True, YELLOW)
    surface.blit(s, (10, 8))
    surface.blit(c, (SCREEN_W - c.get_width() - 10, 8))

def draw_game_over(surface, score, coins):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    lines = [
        (big, "GAME OVER", RED),
        (font, f"Score : {score}", WHITE),
        (font, f"Coins : {coins}", YELLOW),
        (font, "R – restart   Q – quit", WHITE),
    ]

    y = 190
    for f_, text, col in lines:
        surf = f_.render(text, True, col)
        surface.blit(surf, (SCREEN_W//2 - surf.get_width()//2, y))
        y += surf.get_height() + 14

def main():
    road = Road()
    player = PlayerCar()
    enemies = []
    coins = []
    score = 0
    coin_count = 0
    base_speed = 4
    game_over = False

    enemy_timer = 0
    enemy_interval = 80
    coin_timer = 0
    coin_interval = random.randint(100, 180)

    while True:
        clock.tick(FPS)

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

        if not game_over:
            keys = pygame.key.get_pressed()
            player.move(keys)
            road.update()

            speed = base_speed + score // 5
            road.speed = 5 + score // 8

            enemy_timer += 1
            if enemy_timer >= enemy_interval:
                enemies.append(EnemyCar(speed))
                enemy_timer = 0
                enemy_interval = random.randint(55, 110)

            coin_timer += 1
            if coin_timer >= coin_interval:
                coins.append(Coin(speed))
                coin_timer = 0
                coin_interval = random.randint(90, 200)

            for en in enemies[:]:
                en.update()
                if en.off_screen():
                    enemies.remove(en)
                    score += 1
                elif en.rect().colliderect(player.rect()):
                    game_over = True

            for co in coins[:]:
                co.update()
                if co.off_screen():
                    coins.remove(co)
                elif co.rect().colliderect(player.rect()):
                    coins.remove(co)
                    coin_count += 1

        road.draw(screen)

        for en in enemies:
            en.draw(screen)
        for co in coins:
            co.draw(screen)
        player.draw(screen)

        draw_hud(screen, score, coin_count)

        if game_over:
            draw_game_over(screen, score, coin_count)

        pygame.display.flip()

if __name__ == "__main__":
    main()