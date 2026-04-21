import pygame
import sys
from player import MusicPlayer

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 700, 450
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Music Player UI")

font = pygame.font.SysFont("Arial", 28)
small_font = pygame.font.SysFont("Arial", 20)

tracks = [
    "music/popolam.mp3",
    "music/ivl.mp3",
    "music/L.mp3",
    "music/prostuda.mp3",
    "music/Ya hochu s toboy.mp3",
]

player = MusicPlayer(tracks)

clock = pygame.time.Clock()

def draw_progress_bar(x, y, w, h, progress):
    pygame.draw.rect(screen, (70, 70, 70), (x, y, w, h))
    pygame.draw.rect(screen, (0, 200, 100), (x, y, int(w * progress), h))

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

    screen.fill((25, 25, 30))

    track_name = player.get_current_track().split("/")[-1]
    text = font.render(f"Now Playing: {track_name}", True, (255, 255, 255))
    screen.blit(text, (50, 100))

    pos = pygame.mixer.music.get_pos() // 1000
    time_text = font.render(f"{pos}s", True, (200, 200, 200))
    screen.blit(time_text, (50, 150))

    progress = (pos % 100) / 100
    draw_progress_bar(50, 200, 600, 20, progress)

    controls = [
        "P - Play",
        "S - Stop",
        "N - Next",
        "B - Back",
        "Q - Quit"
    ]

    for i, ctrl in enumerate(controls):
        ctrl_text = small_font.render(ctrl, True, (150, 150, 150))
        screen.blit(ctrl_text, (50, 300 + i * 25))

    pygame.display.flip()
    clock.tick(60)