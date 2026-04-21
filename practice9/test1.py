import pygame

pygame.init()
screen = pygame.display.set_mode((600, 400))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((50, 50, 50))
    pygame.display.update()

pygame.quit()

tracks = [
    "music/popolam.mp3",
    "music/ivl.mp3"
    "music/L.mp3",
    "music/prostuda.mp3",
    "music/Ya hochu s toboy.mp3",
]