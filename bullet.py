# -*- coding: utf-8 -*-
"""Bullet sprite class."""
import math
import pygame

from map import MAP_WIDTH, MAP_HEIGHT


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle_deg, damage, speed, pierce, color, tier_lvl, max_range,
                 explosive=False, explosion_radius=0, explosion_damage=0.0,
                 burn_dps=0.0, burn_duration=0.0, bounces=0):
        super().__init__()
        radius = 4 + tier_lvl
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        pygame.draw.circle(self.image, (255, 255, 255), (radius, radius), max(2, radius - 3))
        self.rect = self.image.get_rect(center=(x, y))

        rad = math.radians(angle_deg)
        self.vx = math.cos(rad) * speed
        self.vy = math.sin(rad) * speed
        self.damage = damage
        self.pierce = pierce
        # "Ricochet" talent charges: immediately after any hit, a bullet
        # with bounces left retargets the nearest un-hit zombie instead of
        # continuing straight (see the collision loop in main.py).
        # Decremented per bounce.
        self.bounces = bounces
        self.hit_enemies = set()
        self.pos_x, self.pos_y = float(x), float(y)

        self.start_x, self.start_y = float(x), float(y)
        self.max_range = max_range

        # Optional splash-damage-on-impact + burn-over-time, used by
        # explosive weapons (e.g. the Grenade Launcher). Inert by default.
        self.explosive = explosive
        self.explosion_radius = explosion_radius
        self.explosion_damage = explosion_damage
        self.burn_dps = burn_dps
        self.burn_duration = burn_duration

    def update(self, dt):
        self.pos_x += self.vx
        self.pos_y += self.vy
        self.rect.x, self.rect.y = int(self.pos_x), int(self.pos_y)

        traveled = math.hypot(self.pos_x - self.start_x, self.pos_y - self.start_y)
        if traveled >= self.max_range:
            self.kill()
            return

        if not (0 <= self.pos_x <= MAP_WIDTH and 0 <= self.pos_y <= MAP_HEIGHT):
            self.kill()


class ZombieBullet(pygame.sprite.Sprite):
    """Projectile fired by a RangedZombie (zombie.py) at the player. Kept
    deliberately simpler than the player's Bullet (no pierce/explosive/
    ricochet - it only ever needs to hit the one player), but shares the
    same straight-line travel + max_range/map-bounds despawn behavior.
    Uses a color distinct from every weapon-tier color the player's own
    bullets can have, and a spiky silhouette instead of a plain circle,
    so it always reads as an enemy projectile at a glance."""

    COLOR = (225, 25, 140)  # hot magenta - not used by any WEAPON_TIERS color

    def __init__(self, x, y, angle_deg, damage, speed=7, max_range=520):
        super().__init__()
        radius = 6
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        # Dark core with a bright jagged outline, distinct from the
        # player bullets' plain filled-circle-with-white-glint look.
        pts = []
        for i in range(8):
            a = math.radians(i * 45)
            r = radius if i % 2 == 0 else radius * 0.55
            pts.append((radius + math.cos(a) * r, radius + math.sin(a) * r))
        pygame.draw.polygon(self.image, self.COLOR, pts)
        pygame.draw.circle(self.image, (40, 0, 25), (radius, radius), max(2, radius - 4))
        self.rect = self.image.get_rect(center=(x, y))

        rad = math.radians(angle_deg)
        self.vx = math.cos(rad) * speed
        self.vy = math.sin(rad) * speed
        self.damage = damage
        self.pos_x, self.pos_y = float(x), float(y)

        self.start_x, self.start_y = float(x), float(y)
        self.max_range = max_range

    def update(self, dt):
        self.pos_x += self.vx
        self.pos_y += self.vy
        self.rect.x, self.rect.y = int(self.pos_x), int(self.pos_y)

        traveled = math.hypot(self.pos_x - self.start_x, self.pos_y - self.start_y)
        if traveled >= self.max_range:
            self.kill()
            return

        if not (0 <= self.pos_x <= MAP_WIDTH and 0 <= self.pos_y <= MAP_HEIGHT):
            self.kill()