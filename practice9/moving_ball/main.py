import pygame
import sys
from ball import Ball

pygame.init()

WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Moving Ball")

clock = pygame.time.Clock()

ball = Ball(WIDTH // 2, HEIGHT // 2)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                ball.move(0, -20, WIDTH, HEIGHT)
            elif event.key == pygame.K_DOWN:
                ball.move(0, 20, WIDTH, HEIGHT)
            elif event.key == pygame.K_LEFT:
                ball.move(-20, 0, WIDTH, HEIGHT)
            elif event.key == pygame.K_RIGHT:
                ball.move(20, 0, WIDTH, HEIGHT)

    screen.fill((34, 139, 34)) 

    pygame.draw.line(screen, (255, 255, 255), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 3)

    pygame.draw.circle(screen, (255, 255, 255), (WIDTH//2, HEIGHT//2), 60, 3)
    ball.draw(screen)

    pygame.display.flip()
    clock.tick(60)