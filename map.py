# -*- coding: utf-8 -*-
"""Screen/world constants, obstacle generation, collision helper, and
camera-scrolling background rendering."""
import random
import math
import pygame

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
MAP_WIDTH = 2400
MAP_HEIGHT = 1800

GRID_SIZE = 80

OBSTACLE_MARGIN = 150
PLAYER_SPAWN_CLEAR_RADIUS = 260

THEME_WAVES = 5
MAP_THEMES = [
    {"name": "Grassy Plains", "floor": (45, 60, 40),  "grid": (55, 72, 50),   "obstacle": (150, 110, 70),  "obstacle_dark": (100, 70, 40),  "ob_size": 90, "ob_count": 18},
    {"name": "Abandoned Warehouse", "floor": (52, 52, 58),  "grid": (66, 66, 74),   "obstacle": (120, 120, 130), "obstacle_dark": (80, 80, 92),   "ob_size": 110, "ob_count": 14},
    {"name": "Desert Ruins", "floor": (92, 76, 50),  "grid": (108, 90, 60),  "obstacle": (185, 150, 100), "obstacle_dark": (135, 105, 68), "ob_size": 70, "ob_count": 24},
    {"name": "Frozen Tundra", "floor": (58, 68, 84),  "grid": (74, 84, 100),  "obstacle": (205, 222, 235), "obstacle_dark": (150, 172, 190),"ob_size": 100, "ob_count": 16},
]


def build_obstacles(theme_index):
    theme = MAP_THEMES[theme_index]
    ob_size = theme["ob_size"]
    ob_count = theme["ob_count"]

    rng = random.Random(20260730 + theme_index * 97)
    obstacles = []
    spawn_x, spawn_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
    attempts = 0
    while len(obstacles) < ob_count and attempts < 1500:
        attempts += 1
        x = rng.randint(OBSTACLE_MARGIN, MAP_WIDTH - OBSTACLE_MARGIN - ob_size)
        y = rng.randint(OBSTACLE_MARGIN, MAP_HEIGHT - OBSTACLE_MARGIN - ob_size)
        rect = pygame.Rect(x, y, ob_size, ob_size)
        cx, cy = rect.center
        if math.hypot(cx - spawn_x, cy - spawn_y) < PLAYER_SPAWN_CLEAR_RADIUS:
            continue
        if any(rect.colliderect(o.inflate(40, 40)) for o in obstacles):
            continue
        obstacles.append(rect)
    return obstacles


def move_with_collision(rect, dx, dy, obstacles):
    rect.x += dx
    for ob in obstacles:
        if rect.colliderect(ob):
            if dx > 0:
                rect.right = ob.left
            elif dx < 0:
                rect.left = ob.right

    rect.y += dy
    for ob in obstacles:
        if rect.colliderect(ob):
            if dy > 0:
                rect.bottom = ob.top
            elif dy < 0:
                rect.top = ob.bottom

    return rect


def draw_scrolling_grid(screen, cam_x, cam_y, theme):
    grid_color = theme["grid"]
    start_x = -(cam_x % GRID_SIZE)
    x = start_x
    while x < SCREEN_WIDTH:
        pygame.draw.line(screen, grid_color, (x, 0), (x, SCREEN_HEIGHT), 1)
        x += GRID_SIZE

    start_y = -(cam_y % GRID_SIZE)
    y = start_y
    while y < SCREEN_HEIGHT:
        pygame.draw.line(screen, grid_color, (0, y), (SCREEN_WIDTH, y), 1)
        y += GRID_SIZE

    map_rect = pygame.Rect(0 - cam_x, 0 - cam_y, MAP_WIDTH, MAP_HEIGHT)
    pygame.draw.rect(screen, (80, 95, 75), map_rect, width=4)


def draw_obstacle(screen, ob_rect, cam_x, cam_y, theme):
    ox, oy = ob_rect.x - cam_x, ob_rect.y - cam_y
    pygame.draw.rect(screen, (20, 18, 15), (ox + 4, oy + 8, ob_rect.width, ob_rect.height), border_radius=6)
    pygame.draw.rect(screen, theme["obstacle"], (ox, oy, ob_rect.width, ob_rect.height), border_radius=6)
    pygame.draw.rect(screen, theme["obstacle_dark"], (ox, oy, ob_rect.width, ob_rect.height), width=3, border_radius=6)
