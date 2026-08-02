# -*- coding: utf-8 -*-
"""Zombie and Boss sprite classes plus their tuning constants."""
import math
import pygame

from map import move_with_collision

BOSS_WARNING_DURATION = 3.0
BOSS_SIZE = 64
BOSS_HP_MULTIPLIER = 2.0
BOSS_ATTACK_MULTIPLIER = 2.0

ZOMBIE_BASE_ATTACK = 0.3
ZOMBIE_ATTACK_GROWTH_PER_WAVE = 0.02


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

        move_x = dir_x + sep_x * 0.8
        move_y = dir_y + sep_y * 0.8
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
        self.image = pygame.Surface((BOSS_SIZE, BOSS_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (120, 20, 25), (0, 0, BOSS_SIZE, BOSS_SIZE), border_radius=10)
        pygame.draw.rect(self.image, (255, 215, 0), (0, 0, BOSS_SIZE, BOSS_SIZE), width=4, border_radius=10)
        pygame.draw.rect(self.image, (20, 20, 20), (16, 16, 12, 12))
        pygame.draw.rect(self.image, (20, 20, 20), (36, 16, 12, 12))
        self.rect = self.image.get_rect(center=(x, y))

        self.pos_x, self.pos_y = float(x), float(y)
        self.hp = hp
        self.max_hp = hp
        self.speed = 0.9
        self.attack = (ZOMBIE_BASE_ATTACK + (wave - 1) * ZOMBIE_ATTACK_GROWTH_PER_WAVE) * BOSS_ATTACK_MULTIPLIER

    def update(self, player_pos, obstacles, neighbors):
        dx = player_pos[0] - self.pos_x
        dy = player_pos[1] - self.pos_y
        dist = math.hypot(dx, dy)
        dir_x, dir_y = (dx / dist, dy / dist) if dist > 0 else (0.0, 0.0)
        move_x, move_y = dir_x * self.speed, dir_y * self.speed

        move_rect = pygame.Rect(0, 0, BOSS_SIZE, BOSS_SIZE)
        move_rect.center = (self.pos_x, self.pos_y)
        move_rect = move_with_collision(move_rect, move_x, move_y, obstacles)

        self.pos_x, self.pos_y = float(move_rect.centerx), float(move_rect.centery)
        self.rect.center = (int(self.pos_x), int(self.pos_y))
