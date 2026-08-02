# -*- coding: utf-8 -*-
"""Bullet sprite class."""
import math
import pygame

from map import MAP_WIDTH, MAP_HEIGHT


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle_deg, damage, speed, pierce, color, tier_lvl, max_range):
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
        self.hit_enemies = set()
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
