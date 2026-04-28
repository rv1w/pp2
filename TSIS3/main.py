"""
main.py – TSIS3 Racer: Advanced Driving, Leaderboard & Power-Ups
Entry point that wires together ui.py, racer.py, and persistence.py.
"""

import pygame
import random
import sys

from persistence import load_settings, add_leaderboard_entry
from ui          import (main_menu, username_screen, settings_screen,
                         leaderboard_screen, game_over_screen)
from racer       import (Road, PlayerCar, EnemyCar, Coin,
                         OilSpill, Pothole, SpeedBump, NitroStrip,
                         MovingBarrier, PowerUp, draw_hud,
                         SCREEN_W, SCREEN_H, COIN_MILESTONE, ENEMY_SPEED_BOOST,
                         DIFF, PX_PER_METRE)

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Racer Extreme")
clock  = pygame.time.Clock()
FPS    = 60


# ── Safe spawn check ───────────────────────────────────────────────────────────
SAFE_ZONE_H = 200   # px below top of screen where player car cannot be

def safe_to_spawn(player) -> bool:
    """True if player is far enough up the screen that a top-spawn is safe."""
    return player.y > SAFE_ZONE_H


# ── Play session ───────────────────────────────────────────────────────────────
def play(username: str, settings: dict) -> tuple[int, int, int]:
    """
    Run one game session.
    Returns (score, distance_m, coin_value).
    """
    diff_key  = settings.get("difficulty", "normal")
    diff      = DIFF[diff_key]
    car_color = settings.get("car_color", "blue")

    road    = Road()
    player  = PlayerCar(car_color)
    enemies : list[EnemyCar]    = []
    coins   : list[Coin]        = []
    hazards : list              = []   # OilSpill | Pothole
    events  : list              = []   # SpeedBump | NitroStrip | MovingBarrier
    powerups: list[PowerUp]     = []

    score          = 0
    coin_value     = 0
    distance_px    = 0
    base_speed     = diff["base_speed"]
    game_over      = False

    last_milestone = 0
    enemy_boost    = 0.0

    enemy_timer   = 0
    enemy_int_min, enemy_int_max = diff["enemy_int"]
    enemy_interval = random.randint(enemy_int_min, enemy_int_max)

    coin_timer    = 0
    coin_interval = random.randint(100, 180)

    pu_timer      = 0
    pu_interval   = random.randint(300, 500)
    pu_active     = None   # "nitro" | "shield" | "repair" | None
    # (repair is instant so never "active", handled at collection)

    hazard_chance = diff["hazard_chance"]

    # Repair flag: counts accumulated damage from oil/potholes waiting for repair pu
    slowed_by_oil = False   # whether player is currently on oil
    oil_speed_factor = 1.0

    # ── Inner helpers ──────────────────────────────────────────────────────────

    def current_speed():
        return base_speed + score // 5 + enemy_boost

    def spawn_enemy():
        if safe_to_spawn(player):
            enemies.append(EnemyCar(current_speed()))

    def spawn_coin():
        coins.append(Coin(current_speed()))

    def spawn_powerup():
        kind = random.choice(["nitro", "shield", "repair"])
        powerups.append(PowerUp(current_speed(), kind))

    def maybe_spawn_hazard():
        r = random.random()
        if r < hazard_chance:
            cls = random.choice([OilSpill, OilSpill, Pothole])
            hazards.append(cls(current_speed()))
        if r < hazard_chance * 0.6:
            cls = random.choice([SpeedBump, NitroStrip, MovingBarrier])
            events.append(cls(current_speed()))

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r: return score, distance_px // PX_PER_METRE, coin_value
                if event.key == pygame.K_q: pygame.quit(); sys.exit()

        if not game_over:
            keys = pygame.key.get_pressed()

            # Oil slow-down multiplier is reset each frame then re-applied
            oil_speed_factor = 1.0
            slowed_by_oil    = False

            player.move(keys)
            player.tick_powerups()
            road.update()
            road.speed = 5 + score // 8

            distance_px += int(current_speed())

            # ── Coin milestone → enemy speed ──────────────────────────────────
            cur_ms = coin_value // COIN_MILESTONE
            if cur_ms > last_milestone:
                gained        = cur_ms - last_milestone
                enemy_boost  += gained * ENEMY_SPEED_BOOST
                last_milestone = cur_ms
                for en in enemies:
                    en.spd += gained * ENEMY_SPEED_BOOST

            spd = current_speed()

            # ── Spawn timers ──────────────────────────────────────────────────
            enemy_timer += 1
            if enemy_timer >= enemy_interval:
                spawn_enemy()
                enemy_timer    = 0
                # difficulty scaling: interval shrinks as score grows
                shrink = max(0, score // 10)
                enemy_interval = max(25, random.randint(
                    max(20, enemy_int_min - shrink),
                    max(30, enemy_int_max - shrink)))

            coin_timer += 1
            if coin_timer >= coin_interval:
                spawn_coin()
                coin_timer    = 0
                coin_interval = random.randint(90, 200)

            pu_timer += 1
            if pu_timer >= pu_interval:
                spawn_powerup()
                pu_timer    = 0
                pu_interval = random.randint(300, 500)

            maybe_spawn_hazard()

            # ── Update & check enemies ────────────────────────────────────────
            for en in enemies[:]:
                en.update()
                if en.off_screen():
                    enemies.remove(en)
                    score += 1
                elif en.rect().colliderect(player.rect()):
                    if player.absorb_collision():
                        game_over = True
                    else:
                        enemies.remove(en)

            # ── Update & check coins ──────────────────────────────────────────
            for co in coins[:]:
                co.update()
                if co.off_screen():
                    coins.remove(co)
                elif co.rect().colliderect(player.rect()):
                    coins.remove(co)
                    coin_value += co.value

            # ── Update & check hazards ────────────────────────────────────────
            for hz in hazards[:]:
                hz.update()
                if hz.off_screen():
                    hazards.remove(hz)
                elif hz.rect().colliderect(player.rect()):
                    if hasattr(hz, 'R'):   # Pothole
                        if player.absorb_collision():
                            game_over = True
                        hazards.remove(hz)
                    else:                  # OilSpill
                        oil_speed_factor = 0.4
                        slowed_by_oil    = True

            # Apply oil slow-down to player speed attribute temporarily
            # (We store original spd and restore it)
            if slowed_by_oil:
                player.spd = 2
            else:
                player.spd = 5 * (1.8 if player.nitro_active else 1.0)
                player.spd = 5   # base; nitro handled inside move()

            # ── Update & check road events ────────────────────────────────────
            for ev in events[:]:
                ev.update()
                if ev.off_screen():
                    events.remove(ev)
                elif ev.rect().colliderect(player.rect()):
                    if isinstance(ev, SpeedBump):
                        # SpeedBump slows the road briefly (cosmetic effect)
                        road.speed = max(2, road.speed - 1)
                    elif isinstance(ev, NitroStrip):
                        if not player.nitro_active:
                            player.nitro_active = True
                            player.nitro_timer  = 60 * 4   # 4 seconds
                            pu_active = "nitro"
                        events.remove(ev)

            # ── Update & check power-ups ──────────────────────────────────────
            for pu in powerups[:]:
                pu.update()
                if pu.off_screen():
                    powerups.remove(pu)
                elif pu.rect().colliderect(player.rect()):
                    kind = pu.kind
                    powerups.remove(pu)
                    if kind == "nitro" and not player.nitro_active:
                        player.nitro_active = True
                        player.nitro_timer  = 60 * 4
                        pu_active = "nitro"
                    elif kind == "shield" and not player.shield_active:
                        player.shield_active = True
                        pu_active = "shield"
                    elif kind == "repair":
                        # Instant: remove all oil spills from hazards
                        hazards[:] = [h for h in hazards if hasattr(h, 'R')]
                        pu_active = None   # instant, no display needed

            # Sync pu_active with actual state
            if pu_active == "nitro" and not player.nitro_active:
                pu_active = None
            if pu_active == "shield" and not player.shield_active:
                pu_active = None

        # ── Render ────────────────────────────────────────────────────────────
        road.draw(screen)

        for hz in hazards:  hz.draw(screen)
        for ev in events:   ev.draw(screen)
        for en in enemies:  en.draw(screen)
        for co in coins:    co.draw(screen)
        for pu in powerups: pu.draw(screen)
        player.draw(screen)

        draw_hud(screen, score, coin_value, enemy_boost,
                 distance_px // PX_PER_METRE, pu_active,
                 player.nitro_timer)

        if game_over:
            _draw_mini_gameover(screen)

        pygame.display.flip()

        if game_over:
            pygame.time.delay(1200)
            return score, distance_px // PX_PER_METRE, coin_value


def _draw_mini_gameover(surface):
    """Quick flash overlay shown before transitioning to game_over_screen."""
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((180, 0, 0, 100))
    surface.blit(ov, (0, 0))
    f   = pygame.font.SysFont("Arial", 54, bold=True)
    txt = f.render("CRASH!", True, (255, 255, 255))
    surface.blit(txt, (SCREEN_W//2 - txt.get_width()//2,
                        SCREEN_H//2 - txt.get_height()//2))


# ── Application entry ──────────────────────────────────────────────────────────
def run():
    settings = load_settings()
    username = None

    pygame.mixer.music.load("TSIS3/assets/music/bg.mp3")
    pygame.mixer.music.set_volume(0.5)  # от 0.0 до 1.0
    pygame.mixer.music.play(-1)

    if not settings.get("sound", True):
        pygame.mixer.music.pause()

    while True:
        action = main_menu(screen, clock)

        if action == "quit":
            pygame.quit(); sys.exit()

        elif action == "leaderboard":
            leaderboard_screen(screen, clock)

        elif action == "settings":
            settings = settings_screen(screen, clock, settings)
            
            if settings.get("sound", True):
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.pause()

        elif action == "play":
            if username is None:
                username = username_screen(screen, clock)

            while True:   # inner retry loop
                score, distance_m, coin_value = play(username, settings)

                # Save to leaderboard
                add_leaderboard_entry(username, score, distance_m)

                result = game_over_screen(screen, clock, score, distance_m, coin_value)
                if result == "retry":
                    continue     # play again immediately
                else:
                    break        # back to main menu


if __name__ == "__main__":
    run()