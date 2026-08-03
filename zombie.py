# -*- coding: utf-8 -*-
"""Zombie and Boss sprite classes plus their tuning constants."""
import math
import random
import pygame

from map import move_with_collision

BOSS_WARNING_DURATION = 3.0
BOSS_SIZE = 64
BOSS_HP_MULTIPLIER = 2.0
BOSS_ATTACK_MULTIPLIER = 2.0

ZOMBIE_BASE_ATTACK = 0.3
ZOMBIE_ATTACK_GROWTH_PER_WAVE = 0.02

# map.py's move_with_collision() already resolves X and Y separately, so it
# already lets movers slide along a wall's face. The actual reason zombies
# stall near obstacles is that they have no steering logic at all - if the
# player is directly on the far side of an obstacle, the desired direction
# is aimed straight into it with no sideways component to slide on, so the
# zombie just pushes into the wall every frame. This probes a short distance
# ahead and, if that's blocked, adds a sideways steering force tangent to
# the obstacle so the zombie curves around it instead of stalling.
OBSTACLE_AVOID_LOOKAHEAD = 40
OBSTACLE_AVOID_WEIGHT = 1.3

# The boss is twice the size of a normal zombie (64px vs 32px), so a probe
# that only looks 40px ahead barely gives it any warning before it's already
# touching a wall - by the time it reacts there's almost no room left to
# curve around, which is what made it look "stuck". Give the boss a longer
# probe and a stronger steering weight so it starts curving earlier/harder.
BOSS_OBSTACLE_AVOID_LOOKAHEAD = 70
BOSS_OBSTACLE_AVOID_WEIGHT = 2.0

# Extra safety net: if the boss still ends up barely moving for a frame
# despite trying to (e.g. wedged into a corner formed by two obstacles),
# kick in a short burst of much stronger sideways steering so it visibly
# breaks free instead of appearing frozen.
STUCK_DISTANCE_THRESHOLD = 0.15
STUCK_ESCAPE_FRAMES = 18
STUCK_ESCAPE_WEIGHT = 3.2


def _obstacle_avoid_vector(pos_x, pos_y, dir_x, dir_y, obstacles, size, lookahead=OBSTACLE_AVOID_LOOKAHEAD):
    if dir_x == 0 and dir_y == 0:
        return 0.0, 0.0
    probe_x = pos_x + dir_x * lookahead
    probe_y = pos_y + dir_y * lookahead
    half = size / 2
    probe_rect = pygame.Rect(probe_x - half, probe_y - half, size, size)

    avoid_x, avoid_y = 0.0, 0.0
    for ob in obstacles:
        if probe_rect.colliderect(ob):
            ocx, ocy = ob.center
            away_x, away_y = pos_x - ocx, pos_y - ocy
            # tangent direction perpendicular to where we're heading, picking
            # whichever of the two perpendicular sides already leans toward
            # where we are relative to the obstacle (so it curves the short way)
            perp_x, perp_y = -dir_y, dir_x
            if perp_x * away_x + perp_y * away_y < 0:
                perp_x, perp_y = -perp_x, -perp_y
            avoid_x += perp_x
            avoid_y += perp_y
    return avoid_x, avoid_y

# --- Boss enrage mode ---
ENRAGE_HP_RATIO = 0.30          # enrage triggers at <=30% HP...
ENRAGE_TIME_THRESHOLD = 60.0    # ...or after 60s in the fight, whichever comes first
ENRAGE_SPEED_MULTIPLIER = 1.6
ENRAGE_ATTACK_MULTIPLIER = 1.5

# --- Boss meteor strike ---
METEOR_WARNING_TIME = 1.1       # telegraph duration before impact (dodgeable)
METEOR_IMPACT_TIME = 0.3        # impact flash duration
METEOR_RADIUS = 65
METEOR_COOLDOWN_NORMAL = 5.0
METEOR_COOLDOWN_ENRAGED = 2.6
METEOR_DAMAGE_MULTIPLIER = 3.0  # relative to boss.attack
METEOR_TARGET_SPREAD = 90       # random offset around the player so it's not a guaranteed hit


class Zombie(pygame.sprite.Sprite):
    is_boss = False

    def __init__(self, x, y, hp=30, wave=1):
        super().__init__()
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (40, 160, 60), (0, 0, 32, 32), border_radius=4)
        pygame.draw.rect(self.image, (20, 20, 20), (6, 6, 6, 6))
        pygame.draw.rect(self.image, (20, 20, 20), (20, 6, 6, 6))
        self.rect = self.image.get_rect(center=(x, y))

        self.pos_x, self.pos_y = float(x), float(y)
        self.hp = hp
        self.max_hp = hp
        self.speed = 1.3
        self.attack = ZOMBIE_BASE_ATTACK + (wave - 1) * ZOMBIE_ATTACK_GROWTH_PER_WAVE

        # Burn-over-time status (set by explosive weapons); 0 means not burning.
        self.burn_timer = 0.0
        self.burn_dps = 0.0

    def apply_burn(self, dps, duration):
        """Sets/refreshes the burning status. Takes the stronger of the
        current and incoming dps, and the longer of the two durations,
        so re-igniting an already-burning target doesn't weaken it."""
        if dps <= 0 or duration <= 0:
            return
        self.burn_dps = max(self.burn_dps, dps)
        self.burn_timer = max(self.burn_timer, duration)

    def update(self, player_pos, obstacles, neighbors):
        dx = player_pos[0] - self.pos_x
        dy = player_pos[1] - self.pos_y
        dist = math.hypot(dx, dy)
        dir_x, dir_y = (dx / dist, dy / dist) if dist > 0 else (0.0, 0.0)

        sep_x, sep_y = 0.0, 0.0
        for other in neighbors:
            if other is self:
                continue
            ox = self.pos_x - other.pos_x
            oy = self.pos_y - other.pos_y
            d = math.hypot(ox, oy)
            if 0 < d < 34:
                sep_x += ox / d
                sep_y += oy / d

        avoid_x, avoid_y = _obstacle_avoid_vector(self.pos_x, self.pos_y, dir_x, dir_y, obstacles, size=32)

        move_x = dir_x + sep_x * 0.5 + avoid_x * OBSTACLE_AVOID_WEIGHT
        move_y = dir_y + sep_y * 0.5 + avoid_y * OBSTACLE_AVOID_WEIGHT
        m = math.hypot(move_x, move_y)
        if m > 0:
            move_x = move_x / m * self.speed
            move_y = move_y / m * self.speed

        move_rect = pygame.Rect(0, 0, 32, 32)
        move_rect.center = (self.pos_x, self.pos_y)
        move_rect = move_with_collision(move_rect, move_x, move_y, obstacles)

        self.pos_x, self.pos_y = float(move_rect.centerx), float(move_rect.centery)
        self.rect.center = (int(self.pos_x), int(self.pos_y))


class Boss(Zombie):
    is_boss = True

    def __init__(self, x, y, hp, wave=1):
        pygame.sprite.Sprite.__init__(self)
        self.image_normal = pygame.Surface((BOSS_SIZE, BOSS_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(self.image_normal, (120, 20, 25), (0, 0, BOSS_SIZE, BOSS_SIZE), border_radius=10)
        pygame.draw.rect(self.image_normal, (255, 215, 0), (0, 0, BOSS_SIZE, BOSS_SIZE), width=4, border_radius=10)
        pygame.draw.rect(self.image_normal, (20, 20, 20), (16, 16, 12, 12))
        pygame.draw.rect(self.image_normal, (20, 20, 20), (36, 16, 12, 12))

        self.image_enraged = pygame.Surface((BOSS_SIZE, BOSS_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(self.image_enraged, (185, 30, 20), (0, 0, BOSS_SIZE, BOSS_SIZE), border_radius=10)
        pygame.draw.rect(self.image_enraged, (255, 110, 0), (0, 0, BOSS_SIZE, BOSS_SIZE), width=4, border_radius=10)
        pygame.draw.rect(self.image_enraged, (255, 240, 0), (16, 16, 12, 12))
        pygame.draw.rect(self.image_enraged, (255, 240, 0), (36, 16, 12, 12))

        self.image = self.image_normal
        self.rect = self.image.get_rect(center=(x, y))

        self.pos_x, self.pos_y = float(x), float(y)
        self.hp = hp
        self.max_hp = hp
        self.speed = 1.15
        self.attack = (ZOMBIE_BASE_ATTACK + (wave - 1) * ZOMBIE_ATTACK_GROWTH_PER_WAVE) * BOSS_ATTACK_MULTIPLIER

        self.base_speed = self.speed
        self.base_attack = self.attack
        self.age = 0.0
        self.enraged = False
        self.stuck_timer = 0

        self.meteor_cd = METEOR_COOLDOWN_NORMAL * 0.6  # first meteor arrives a bit sooner
        self.meteors = []  # each: {"x", "y", "timer", "state": "warning"/"impact"}

        # Burn-over-time status (set by explosive weapons); 0 means not burning.
        self.burn_timer = 0.0
        self.burn_dps = 0.0

    def _try_enrage(self):
        if self.enraged:
            return
        if self.hp <= self.max_hp * ENRAGE_HP_RATIO or self.age >= ENRAGE_TIME_THRESHOLD:
            self.enraged = True
            self.speed = self.base_speed * ENRAGE_SPEED_MULTIPLIER
            self.attack = self.base_attack * ENRAGE_ATTACK_MULTIPLIER
            self.image = self.image_enraged

    def _update_meteors(self, dt, player_pos, on_player_hit):
        self.meteor_cd -= dt
        if self.meteor_cd <= 0:
            cooldown = METEOR_COOLDOWN_ENRAGED if self.enraged else METEOR_COOLDOWN_NORMAL
            self.meteor_cd = cooldown
            volley = 2 if self.enraged else 1
            for _ in range(volley):
                tx = player_pos[0] + random.uniform(-METEOR_TARGET_SPREAD, METEOR_TARGET_SPREAD)
                ty = player_pos[1] + random.uniform(-METEOR_TARGET_SPREAD, METEOR_TARGET_SPREAD)
                self.meteors.append({"x": tx, "y": ty, "timer": METEOR_WARNING_TIME, "state": "warning"})

        for m in self.meteors[:]:
            m["timer"] -= dt
            if m["state"] == "warning" and m["timer"] <= 0:
                m["state"] = "impact"
                m["timer"] = METEOR_IMPACT_TIME
                dist = math.hypot(player_pos[0] - m["x"], player_pos[1] - m["y"])
                if dist <= METEOR_RADIUS and on_player_hit:
                    on_player_hit(self.attack * METEOR_DAMAGE_MULTIPLIER)
            elif m["state"] == "impact" and m["timer"] <= 0:
                self.meteors.remove(m)

    def _move(self, player_pos, obstacles):
        dx = player_pos[0] - self.pos_x
        dy = player_pos[1] - self.pos_y
        dist = math.hypot(dx, dy)
        dir_x, dir_y = (dx / dist, dy / dist) if dist > 0 else (0.0, 0.0)

        avoid_x, avoid_y = _obstacle_avoid_vector(
            self.pos_x, self.pos_y, dir_x, dir_y, obstacles,
            size=BOSS_SIZE, lookahead=BOSS_OBSTACLE_AVOID_LOOKAHEAD,
        )

        weight = BOSS_OBSTACLE_AVOID_WEIGHT
        if self.stuck_timer > 0:
            weight = STUCK_ESCAPE_WEIGHT
            self.stuck_timer -= 1

        move_x = dir_x + avoid_x * weight
        move_y = dir_y + avoid_y * weight
        m = math.hypot(move_x, move_y)
        if m > 0:
            move_x = move_x / m * self.speed
            move_y = move_y / m * self.speed

        move_rect = pygame.Rect(0, 0, BOSS_SIZE, BOSS_SIZE)
        move_rect.center = (self.pos_x, self.pos_y)
        move_rect = move_with_collision(move_rect, move_x, move_y, obstacles)

        new_x, new_y = float(move_rect.centerx), float(move_rect.centery)
        actual_moved = math.hypot(new_x - self.pos_x, new_y - self.pos_y)

        # We intended to move (move_x/move_y non-trivial) but barely got
        # anywhere - almost certainly wedged against a wall/corner. Kick
        # off a short burst of much stronger sideways steering so it
        # visibly breaks free next frame instead of sitting there.
        if actual_moved < STUCK_DISTANCE_THRESHOLD and (abs(move_x) + abs(move_y)) > 0.01:
            self.stuck_timer = STUCK_ESCAPE_FRAMES

        self.pos_x, self.pos_y = new_x, new_y
        self.rect.center = (int(self.pos_x), int(self.pos_y))

    def update(self, player_pos, obstacles, neighbors, dt=0.0, on_player_hit=None):
        self.age += dt
        self._try_enrage()
        self._move(player_pos, obstacles)
        self._update_meteors(dt, player_pos, on_player_hit)


def draw_boss_meteors(screen, boss, cam_x, cam_y):
    """Draws warning rings for incoming meteors and a flash for impacts.
    Call this once per frame while a boss is alive, in world/camera space."""
    if boss is None or not getattr(boss, "is_boss", False):
        return
    for m in boss.meteors:
        sx, sy = m["x"] - cam_x, m["y"] - cam_y
        if m["state"] == "warning":
            progress = 1.0 - max(0.0, m["timer"]) / METEOR_WARNING_TIME  # 0 -> 1 as impact nears
            outer_radius = METEOR_RADIUS
            fill_radius = max(1, int(outer_radius * progress))

            ring_surf = pygame.Surface((outer_radius * 2, outer_radius * 2), pygame.SRCALPHA)

            # Outline shows the full danger zone right away so it can be dodged.
            outline_alpha = int(150 + 90 * progress)
            pygame.draw.circle(ring_surf, (255, 160, 0, outline_alpha), (outer_radius, outer_radius), outer_radius, width=3)

            # Semi-transparent red glow expands from the center outward,
            # filling the circle in sync with the warning countdown.
            fill_alpha = int(70 + 110 * progress)
            pygame.draw.circle(ring_surf, (255, 50, 0, fill_alpha), (outer_radius, outer_radius), fill_radius)

            screen.blit(ring_surf, (sx - outer_radius, sy - outer_radius))
        else:
            progress = max(0.0, m["timer"]) / METEOR_IMPACT_TIME
            radius = max(1, int(METEOR_RADIUS * (0.6 + 0.6 * (1 - progress))))
            alpha = int(255 * progress)
            flash_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 220, 120, alpha), (radius, radius), radius)
            screen.blit(flash_surf, (sx - radius, sy - radius))