# -*- coding: utf-8 -*-
"""Particle burst and screen-flash visual effects (e.g. boss-kill celebration)."""
import random
import math
import pygame

EFFECT_FLASH_DURATION = 0.35


def spawn_boss_kill_particles(particles, x, y, count=28):
    """Append a burst of particles at (x, y) to the given particles list."""
    for _ in range(count):
        ang = random.uniform(0, 360)
        spd = random.uniform(80, 240)
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(math.radians(ang)) * spd,
            "vy": math.sin(math.radians(ang)) * spd,
            "age": 0.0, "life": random.uniform(0.4, 0.9),
            "color": random.choice([(255, 215, 0), (255, 90, 90), (255, 255, 255)])
        })


def update_particles(particles, dt):
    """Advance particle age/position in place, removing expired ones."""
    for p in particles[:]:
        p["age"] += dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        if p["age"] >= p["life"]:
            particles.remove(p)


def draw_particles(screen, particles, cam_x, cam_y):
    for p in particles:
        alpha = max(0, 255 - int(255 * (p["age"] / p["life"])))
        radius = 3 + int(6 * (p["age"] / p["life"]))
        if alpha > 0:
            particle_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (*p["color"], alpha), (radius, radius), radius)
            screen.blit(particle_surf, (p["x"] - cam_x - radius, p["y"] - cam_y - radius))


def draw_effect_flash(screen, flash_timer, screen_w, screen_h):
    if flash_timer <= 0:
        return
    flash_alpha = int(200 * (flash_timer / EFFECT_FLASH_DURATION))
    flash_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
    flash_surf.fill((255, 235, 150, flash_alpha))
    screen.blit(flash_surf, (0, 0))
