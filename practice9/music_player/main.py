import pygame
import sys
from player import MusicPlayer

pygame.init()

screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Music Player")

font = pygame.font.SysFont(None, 36)

tracks = [
    "music/popolam.mp3",
    "music/ivl.mp3",
    "music/L.mp3",
    "music/prostuda.mp3",
    "music/Ya hochu s toboy.mp3",
]

player = MusicPlayer(tracks)

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                player.play()
            elif event.key == pygame.K_s:
                player.stop()
            elif event.key == pygame.K_n:
                player.next()
            elif event.key == pygame.K_b:
                player.prev()
            elif event.key == pygame.K_q:
                pygame.quit()
                sys.exit()

    screen.fill((20, 20, 20))

    text = font.render(f"Now playing: {player.get_current_track()}", True, (255, 255, 255))
    screen.blit(text, (50, 150))

    pygame.display.flip()
    clock.tick(60)