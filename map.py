# -*- coding: utf-8 -*-
"""Screen/world constants, obstacle generation, collision helper, and
camera-scrolling background rendering."""
import random
import math
import sys
import pygame

pygame.init()


def _detect_screen_size():
    """Picks the game's window/canvas resolution from the device's actual
    screen shape: a portrait phone (taller than wide) gets a canvas that
    exactly matches its own reported width/height, so the game is flush
    with the screen edges instead of being squeezed into this game's
    original 1024x768 landscape design. Desktops/laptops (wider than
    tall) keep that original 1024x768. Falls back to it too if display
    info isn't available (e.g. some headless/test environments)."""
    avail_w, avail_h = 0, 0

    # In the pygbag/browser build, main.py (and this module) runs BEFORE
    # the page's own window_resize() call (see index.html's custom_site()),
    # so pygame.display.Info() can still report a stale/placeholder size
    # at this point. window.innerWidth/innerHeight reflect the browser's
    # real viewport immediately, in the same CSS pixels the rest of the
    # UI's fixed pixel sizes assume - ask the DOM directly when available.
    if sys.platform == "emscripten":
        try:
            import platform as browser
            avail_w = int(browser.window.innerWidth)
            avail_h = int(browser.window.innerHeight)
        except Exception:
            avail_w, avail_h = 0, 0

    if avail_w <= 0 or avail_h <= 0:
        try:
            info = pygame.display.Info()
            avail_w, avail_h = info.current_w, info.current_h
        except pygame.error:
            avail_w, avail_h = 0, 0

    if avail_w <= 0 or avail_h <= 0 or avail_w >= avail_h:
        return 1024, 768

    # Portrait device: use the reported width/height as-is so the canvas
    # is flush with the screen edges on every phone.
    return avail_w, avail_h


SCREEN_WIDTH, SCREEN_HEIGHT = _detect_screen_size()

# Without this, a narrow portrait screen shows far fewer world-pixels than
# the game was tuned for, which makes everything feel "zoomed in" even
# though nothing is actually being scaled - objects are simply large
# relative to the small screen. CAMERA_ZOOM < 1.0 renders the world onto a
# larger virtual viewport (WORLD_VIEW_WIDTH/HEIGHT) that then gets scaled
# down to fit the real screen, pulling the camera back on narrow screens.
# Desktop/landscape screens (width >= 850) are unaffected and stay at
# native 1:1 (zoom 1.0) - see the world_surface render step in main.py.
CAMERA_ZOOM = max(0.5, min(1.0, SCREEN_WIDTH / 850))
WORLD_VIEW_WIDTH = int(SCREEN_WIDTH / CAMERA_ZOOM)
WORLD_VIEW_HEIGHT = int(SCREEN_HEIGHT / CAMERA_ZOOM)
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
    surf_w, surf_h = screen.get_size()
    grid_color = theme["grid"]
    start_x = -(cam_x % GRID_SIZE)
    x = start_x
    while x < surf_w:
        pygame.draw.line(screen, grid_color, (x, 0), (x, surf_h), 1)
        x += GRID_SIZE

    start_y = -(cam_y % GRID_SIZE)
    y = start_y
    while y < surf_h:
        pygame.draw.line(screen, grid_color, (0, y), (surf_w, y), 1)
        y += GRID_SIZE

    map_rect = pygame.Rect(0 - cam_x, 0 - cam_y, MAP_WIDTH, MAP_HEIGHT)
    pygame.draw.rect(screen, (80, 95, 75), map_rect, width=4)


def draw_obstacle(screen, ob_rect, cam_x, cam_y, theme):
    ox, oy = ob_rect.x - cam_x, ob_rect.y - cam_y
    pygame.draw.rect(screen, (20, 18, 15), (ox + 4, oy + 8, ob_rect.width, ob_rect.height), border_radius=6)
    pygame.draw.rect(screen, theme["obstacle"], (ox, oy, ob_rect.width, ob_rect.height), border_radius=6)
    pygame.draw.rect(screen, theme["obstacle_dark"], (ox, oy, ob_rect.width, ob_rect.height), width=3, border_radius=6)