import math
import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame

WIDTH, HEIGHT = 960, 640
FPS = 60
TRACK_MARGIN = 80
TRACK_WIDTH = 160

COLORS = {
    "background": (18, 18, 30),
    "track": (70, 70, 90),
    "grass": (30, 120, 50),
    "white": (240, 240, 240),
    "yellow": (255, 210, 0),
    "boost": (120, 200, 255),
    "slow": (220, 40, 40),
}

@dataclass
class Character:
    name: str
    color: Tuple[int, int, int]

@dataclass
class PowerUp:
    rect: pygame.Rect
    effect: str
    active: bool = True

class Kart:
    def __init__(self, character: Character, x: float, y: float, rotation: float) -> None:
        self.character = character
        self.x = x
        self.y = y
        self.rotation = rotation
        self.speed = 0.0
        self.boost_timer = 0.0
        self.slow_timer = 0.0
        self.lap = 0
        self.progress = 0.0

    def update(self, dt: float, turning: float, throttle: float) -> None:
        max_speed = 260
        acceleration = 200
        drag = 90
        turn_speed = 160

        if self.boost_timer > 0:
            self.boost_timer = max(0.0, self.boost_timer - dt)
            max_speed *= 1.7
            acceleration *= 1.5
        if self.slow_timer > 0:
            self.slow_timer = max(0.0, self.slow_timer - dt)
            max_speed *= 0.4
            acceleration *= 0.4

        self.speed += throttle * acceleration * dt
        if throttle == 0:
            self.speed -= min(abs(self.speed), drag * dt) * math.copysign(1, self.speed) if self.speed else 0
        self.speed = max(-80, min(self.speed, max_speed))

        if self.speed != 0:
            self.rotation += turning * turn_speed * dt * (self.speed / max_speed)

        dx = math.cos(math.radians(self.rotation)) * self.speed * dt
        dy = math.sin(math.radians(self.rotation)) * self.speed * dt
        self.x += dx
        self.y += dy

    def apply_power_up(self, effect: str) -> None:
        if effect == "boost":
            self.boost_timer = 2.2
        elif effect == "slow":
            self.slow_timer = 2.0

    @property
    def pos(self) -> Tuple[float, float]:
        return self.x, self.y


def build_track_path() -> List[Tuple[float, float]]:
    points: List[Tuple[float, float]] = []
    rect = pygame.Rect(TRACK_MARGIN, TRACK_MARGIN, WIDTH - TRACK_MARGIN * 2, HEIGHT - TRACK_MARGIN * 2)
    segments = 40
    for i in range(segments):
        angle = (i / segments) * 2 * math.pi
        r_x = rect.width / 2
        r_y = rect.height / 2
        x = WIDTH / 2 + math.cos(angle) * r_x
        y = HEIGHT / 2 + math.sin(angle) * r_y
        points.append((x, y))
    return points

TRACK_PATH = build_track_path()


def point_progress(x: float, y: float) -> float:
    closest = 0
    min_dist = float("inf")
    for i, (px, py) in enumerate(TRACK_PATH):
        dist = (px - x) ** 2 + (py - y) ** 2
        if dist < min_dist:
            min_dist = dist
            closest = i
    return closest / len(TRACK_PATH)


def draw_track(surface: pygame.Surface) -> None:
    surface.fill(COLORS["grass"])
    outer_rect = pygame.Rect(TRACK_MARGIN, TRACK_MARGIN, WIDTH - TRACK_MARGIN * 2, HEIGHT - TRACK_MARGIN * 2)
    pygame.draw.ellipse(surface, COLORS["track"], outer_rect)
    inner_rect = outer_rect.inflate(-TRACK_WIDTH, -TRACK_WIDTH)
    pygame.draw.ellipse(surface, COLORS["grass"], inner_rect)
    for i in range(16):
        t = i / 16
        angle = t * 2 * math.pi
        x = WIDTH / 2 + math.cos(angle) * outer_rect.width / 2
        y = HEIGHT / 2 + math.sin(angle) * outer_rect.height / 2
        w = 20
        h = 10
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (x, y)
        color = COLORS["white"] if i % 2 == 0 else COLORS["yellow"]
        pygame.draw.rect(surface, color, rect)


def draw_kart(surface: pygame.Surface, kart: Kart) -> None:
    body = pygame.Surface((48, 28), pygame.SRCALPHA)
    pygame.draw.rect(body, kart.character.color, (0, 0, 48, 28), border_radius=10)
    pygame.draw.rect(body, (0, 0, 0), (6, 4, 12, 20), border_radius=4)
    pygame.draw.rect(body, (0, 0, 0), (30, 4, 12, 20), border_radius=4)
    rotated = pygame.transform.rotate(body, -kart.rotation)
    rect = rotated.get_rect(center=(kart.x, kart.y))
    surface.blit(rotated, rect)


def draw_powerup(surface: pygame.Surface, powerup: PowerUp) -> None:
    color = COLORS["boost"] if powerup.effect == "boost" else COLORS["slow"]
    pygame.draw.rect(surface, color, powerup.rect, border_radius=6)


def spawn_powerups() -> List[PowerUp]:
    powerups: List[PowerUp] = []
    angles = [random.uniform(0, 2 * math.pi) for _ in range(5)]
    outer_rect = pygame.Rect(TRACK_MARGIN + 40, TRACK_MARGIN + 40, WIDTH - (TRACK_MARGIN + 40) * 2, HEIGHT - (TRACK_MARGIN + 40) * 2)
    for angle in angles:
        x = WIDTH / 2 + math.cos(angle) * outer_rect.width / 2
        y = HEIGHT / 2 + math.sin(angle) * outer_rect.height / 2
        rect = pygame.Rect(0, 0, 26, 26)
        rect.center = (x, y)
        effect = random.choice(["boost", "slow"])
        powerups.append(PowerUp(rect=rect, effect=effect))
    return powerups


def control_player() -> Tuple[float, float]:
    keys = pygame.key.get_pressed()
    throttle = 0
    turning = 0
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        throttle += 1
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        throttle -= 1
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        turning -= 1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        turning += 1
    return turning, throttle


def ai_control(kart: Kart) -> Tuple[float, float]:
    target_index = int((kart.progress + 0.03) * len(TRACK_PATH)) % len(TRACK_PATH)
    target = TRACK_PATH[target_index]
    dx = target[0] - kart.x
    dy = target[1] - kart.y
    desired_angle = math.degrees(math.atan2(dy, dx))
    angle_diff = (desired_angle - kart.rotation + 180) % 360 - 180
    turning = max(-1, min(1, angle_diff / 45))
    throttle = 1.0 if abs(angle_diff) < 90 else 0.5
    return turning, throttle


def update_progress(kart: Kart) -> None:
    prev = kart.progress
    kart.progress = point_progress(kart.x, kart.y)
    if prev > 0.8 and kart.progress < 0.2:
        kart.lap += 1


def apply_collision_bounds(kart: Kart) -> None:
    outer_rect = pygame.Rect(TRACK_MARGIN, TRACK_MARGIN, WIDTH - TRACK_MARGIN * 2, HEIGHT - TRACK_MARGIN * 2)
    inner_rect = outer_rect.inflate(-TRACK_WIDTH, -TRACK_WIDTH)
    center = pygame.Vector2(WIDTH / 2, HEIGHT / 2)
    pos = pygame.Vector2(kart.x, kart.y)
    offset = pos - center
    if offset.length_squared() > 0:
        distance = offset.length()
        outer_limit = outer_rect.width / 2
        inner_limit = inner_rect.width / 2
        if distance > outer_limit:
            offset.scale_to_length(outer_limit)
            new_pos = center + offset
            kart.x, kart.y = new_pos
            kart.speed *= 0.4
        if distance < inner_limit:
            offset.scale_to_length(inner_limit)
            new_pos = center + offset
            kart.x, kart.y = new_pos
            kart.speed *= 0.5


def handle_powerups(karts: List[Kart], powerups: List[PowerUp]) -> None:
    for powerup in powerups:
        if not powerup.active:
            continue
        for kart in karts:
            kart_rect = pygame.Rect(0, 0, 36, 36)
            kart_rect.center = (kart.x, kart.y)
            if kart_rect.colliderect(powerup.rect):
                powerup.active = False
                kart.apply_power_up(powerup.effect)
                other = [k for k in karts if k is not kart]
                if powerup.effect == "slow" and other:
                    other[0].apply_power_up("slow")
                break


def show_character_select(screen: pygame.Surface, clock: pygame.time.Clock, characters: List[Character]) -> Character:
    font = pygame.font.Font(None, 48)
    small = pygame.font.Font(None, 32)
    index = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    index = (index + 1) % len(characters)
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    index = (index - 1) % len(characters)
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return characters[index]

        screen.fill(COLORS["background"])
        title = font.render("Select your racer", True, COLORS["white"])
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 120)))

        for i, character in enumerate(characters):
            color = character.color
            rect = pygame.Rect(0, 0, 120, 120)
            rect.center = (WIDTH // 2 + (i - index) * 180, HEIGHT // 2)
            pygame.draw.rect(screen, color, rect, border_radius=20)
            label = small.render(character.name, True, COLORS["white"])
            label_rect = label.get_rect(center=(rect.centerx, rect.bottom + 30))
            screen.blit(label, label_rect)

        prompt = small.render("Press Enter to race", True, COLORS["white"])
        screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT - 80)))

        pygame.display.flip()
        clock.tick(FPS)


def draw_hud(screen: pygame.Surface, player: Kart, opponent: Kart, total_laps: int) -> None:
    font = pygame.font.Font(None, 28)
    hud = font.render(
        f"Lap {player.lap + 1}/{total_laps}  |  Speed: {int(player.speed):3d}  |  Rival Lap: {opponent.lap + 1}/{total_laps}",
        True,
        COLORS["white"],
    )
    screen.blit(hud, (20, 20))
    if player.boost_timer > 0:
        boost = font.render(f"Boost: {player.boost_timer:0.1f}s", True, COLORS["boost"])
        screen.blit(boost, (20, 50))
    if player.slow_timer > 0:
        slow = font.render(f"Slowed: {player.slow_timer:0.1f}s", True, COLORS["slow"])
        screen.blit(slow, (20, 80))


def show_results(screen: pygame.Surface, clock: pygame.time.Clock, winner: str) -> None:
    font = pygame.font.Font(None, 64)
    small = pygame.font.Font(None, 32)
    timer = 0
    while timer < 6:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                return
        screen.fill(COLORS["background"])
        message = font.render(f"{winner} wins!", True, COLORS["white"])
        screen.blit(message, message.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
        prompt = small.render("Press Enter to play again or Esc to quit", True, COLORS["white"])
        screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))
        pygame.display.flip()
        clock.tick(FPS)
        timer += 1 / FPS


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Arcade Racer")
    clock = pygame.time.Clock()

    characters = [
        Character("Nova", (235, 75, 75)),
        Character("Bolt", (80, 200, 120)),
        Character("Violet", (120, 90, 220)),
        Character("Blaze", (230, 150, 40)),
    ]

    total_laps = 3

    while True:
        player_choice = show_character_select(screen, clock, characters)
        opponent_choice = random.choice([c for c in characters if c is not player_choice])

        start_angle = -90
        player = Kart(player_choice, WIDTH / 2 + math.cos(math.radians(start_angle)) * (TRACK_MARGIN + TRACK_WIDTH / 2), HEIGHT / 2 + math.sin(math.radians(start_angle)) * (TRACK_MARGIN + TRACK_WIDTH / 2), start_angle)
        opponent = Kart(opponent_choice, WIDTH / 2 + math.cos(math.radians(start_angle + 5)) * (TRACK_MARGIN + TRACK_WIDTH / 2), HEIGHT / 2 + math.sin(math.radians(start_angle + 5)) * (TRACK_MARGIN + TRACK_WIDTH / 2), start_angle)

        powerups = spawn_powerups()

        running = True
        while running:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

            turning, throttle = control_player()
            player.update(dt, turning, throttle)

            ai_turn, ai_throttle = ai_control(opponent)
            opponent.update(dt, ai_turn, ai_throttle)

            update_progress(player)
            update_progress(opponent)

            apply_collision_bounds(player)
            apply_collision_bounds(opponent)

            handle_powerups([player, opponent], powerups)

            if player.lap >= total_laps:
                show_results(screen, clock, player.character.name)
                running = False
            if opponent.lap >= total_laps:
                show_results(screen, clock, opponent.character.name)
                running = False

            draw_track(screen)
            for powerup in powerups:
                if powerup.active:
                    draw_powerup(screen, powerup)
            draw_kart(screen, opponent)
            draw_kart(screen, player)
            draw_hud(screen, player, opponent, total_laps)

            pygame.display.flip()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
    finally:
        pygame.quit()
