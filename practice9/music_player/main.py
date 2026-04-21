import pygame
import sys
from player import MusicPlayer


def format_time(seconds):
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02}"

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 700, 450
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Music Player UI")

font = pygame.font.SysFont("Centurygothic", 28)
small_font = pygame.font.SysFont("Centurygothic", 20)

tracks = [
    "music/MACAN & SCIRENA - IVL.mp3",
    "music/MACAN & BRANYA - Пополам.mp3",
    "music/MACAN - L.mp3",
    "music/MACAN & Xcho - Простуда.mp3",
    "music/MACAN & SCIRENA - Я хочу с тобой.mp3",
]

player = MusicPlayer(tracks)

clock = pygame.time.Clock()

def draw_progress_bar(x, y, w, h, progress):
    pygame.draw.rect(screen, (255, 255, 255), (x, y, w, h),border_radius=20)
    pygame.draw.rect(screen, (0, 150, 255), (x, y, int(w * progress), h),border_radius=20)

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

    screen.fill((10, 10, 12))

    track_name = player.get_current_track().split("/")[-1]
    text = font.render(f"{track_name}", True, (255, 255, 255))
    screen.blit(text, (50, 100))

    pos = pygame.mixer.music.get_pos() // 1000
    time_text = font.render(format_time(pos), True, (200, 200, 200))
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