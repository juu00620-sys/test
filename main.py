# -*- coding: utf-8 -*-
import pygame
import random
import math
import sys

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
MAP_WIDTH = 2400
MAP_HEIGHT = 1800

GRID_SIZE = 80

OBSTACLE_MARGIN = 150
PLAYER_SPAWN_CLEAR_RADIUS = 260

THEME_WAVES = 5
MAP_THEMES = [
    {"name": "青草原野", "floor": (45, 60, 40),  "grid": (55, 72, 50),   "obstacle": (150, 110, 70),  "obstacle_dark": (100, 70, 40),  "ob_size": 90, "ob_count": 18},
    {"name": "廢棄倉庫", "floor": (52, 52, 58),  "grid": (66, 66, 74),   "obstacle": (120, 120, 130), "obstacle_dark": (80, 80, 92),   "ob_size": 110, "ob_count": 14},
    {"name": "沙漠遺跡", "floor": (92, 76, 50),  "grid": (108, 90, 60),  "obstacle": (185, 150, 100), "obstacle_dark": (135, 105, 68), "ob_size": 70, "ob_count": 24},
    {"name": "冰雪凍原", "floor": (58, 68, 84),  "grid": (74, 84, 100),  "obstacle": (205, 222, 235), "obstacle_dark": (150, 172, 190),"ob_size": 100, "ob_count": 16},
]

BOSS_WARNING_DURATION = 3.0
BOSS_SIZE = 64
EFFECT_FLASH_DURATION = 0.35
BOSS_HP_MULTIPLIER = 2.0
BOSS_ATTACK_MULTIPLIER = 2.0

ZOMBIE_BASE_ATTACK = 0.3
ZOMBIE_ATTACK_GROWTH_PER_WAVE = 0.02

JOY_BASE_POS = (120, SCREEN_HEIGHT - 140)
JOY_BASE_RADIUS = 70
JOY_KNOB_RADIUS = 32
JOY_DEADZONE = 0.15

WEAPON_TYPES = {
    "rifle": {
        "name": "突擊步槍",
        "base_damage": 7.5,
        "base_fire_rate": 0.2,
        "base_shots": 1,
        "base_pierce": 1,
        "spread_angle": 5,
        "bullet_speed": 12,
        "max_range": 450,
    },
    "shotgun": {
        "name": "散彈獵槍",
        "base_damage": 5,
        "base_fire_rate": 0.6,
        "base_shots": 5,
        "base_pierce": 1,
        "spread_angle": 25,
        "bullet_speed": 10,
        "max_range": 250,
    },
    "sniper": {
        "name": "重型貫穿槍",
        "base_damage": 27.5,
        "base_fire_rate": 1.0,
        "base_shots": 1,
        "base_pierce": 4,
        "spread_angle": 0,
        "bullet_speed": 18,
        "max_range": 700,
    },
    "grenade": {
        "name": "榴彈發射器",
        "base_damage": 20,
        "base_fire_rate": 1.2,
        "base_shots": 1,
        "base_pierce": 1,
        "spread_angle": 0,
        "bullet_speed": 8,
        "max_range": 350,
    }
}

WEAPON_TIERS = {
    "精良": {"lvl": 1, "color": (50, 205, 50),   "dmg_m": 1.2, "fr_m": 0.9, "add_p": 0, "add_s": 0},
    "史詩": {"lvl": 2, "color": (147, 112, 219), "dmg_m": 1.5, "fr_m": 0.8, "add_p": 1, "add_s": 0},
    "聖級": {"lvl": 3, "color": (255, 215, 0),   "dmg_m": 2.0, "fr_m": 0.7, "add_p": 1, "add_s": 1},
    "王級": {"lvl": 4, "color": (255, 140, 0),   "dmg_m": 2.8, "fr_m": 0.6, "add_p": 2, "add_s": 2},
    "帝級": {"lvl": 5, "color": (220, 20, 60),   "dmg_m": 4.0, "fr_m": 0.5, "add_p": 3, "add_s": 3},
    "神級": {"lvl": 6, "color": (0, 255, 255),   "dmg_m": 6.5, "fr_m": 0.35, "add_p": 99, "add_s": 4}
}

ARMOR_TIERS = {
    1: {"name": "木質積木甲", "color": (220, 220, 220), "value": 30, "reduction": 0.10},
    2: {"name": "鐵合金積木甲", "color": (180, 220, 255), "value": 60, "reduction": 0.20},
    3: {"name": "黃金合金積木甲", "color": (255, 235, 150), "value": 100, "reduction": 0.35},
    4: {"name": "振金鑽石積木甲", "color": (230, 180, 255), "value": 150, "reduction": 0.50},
}

TALENT_POOL = [
    {"id": "add_armor", "name": "裝備空投鎧甲", "desc": "隨機獲得一套高階白色護甲", "max_rank": 5},
    {"id": "hp_up", "name": "體力增強", "desc": "最大生命值 +25，並回復 25 HP", "max_rank": 3},
    {"id": "speed_up", "name": "輕裝上陣", "desc": "移動速度 +12%", "max_rank": 3},
    {"id": "weapon_tier_up", "name": "武器突破", "desc": "提高當前武器一階品質！", "max_rank": 5},
    {"id": "switch_weapon", "name": "更換武器款式", "desc": "隨機更換為其他武器類型", "max_rank": 5},
]

TALENT_WEIGHTS = {
    "add_armor": 1.0,
    "hp_up": 1.0,
    "speed_up": 1.0,
    "weapon_tier_up": 0.35,
    "switch_weapon": 1.0,
}

def weighted_sample_without_replacement(population, weights, k):
    pool = list(population)
    w = list(weights)
    result = []
    for _ in range(min(k, len(pool))):
        total = sum(w)
        r = random.uniform(0, total)
        upto = 0.0
        for i, wt in enumerate(w):
            upto += wt
            if upto >= r:
                result.append(pool.pop(i))
                w.pop(i)
                break
        else:
            result.append(pool.pop())
            w.pop()
    return result

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

def joystick_handle_down(pos, joy_state):
    cx, cy = JOY_BASE_POS
    dist = math.hypot(pos[0] - cx, pos[1] - cy)
    if dist <= JOY_BASE_RADIUS * 1.6:
        joy_state["active"] = True
        joy_state["offset"] = [0.0, 0.0]

def joystick_handle_move(pos, joy_state):
    if not joy_state["active"]:
        return
    cx, cy = JOY_BASE_POS
    ox, oy = pos[0] - cx, pos[1] - cy
    dist = math.hypot(ox, oy)
    if dist > JOY_BASE_RADIUS:
        ox = ox / dist * JOY_BASE_RADIUS
        oy = oy / dist * JOY_BASE_RADIUS
    joy_state["offset"] = [ox, oy]

def joystick_handle_up(joy_state):
    joy_state["active"] = False
    joy_state["offset"] = [0.0, 0.0]

def joystick_vector(joy_state):
    if not joy_state["active"]:
        return 0.0, 0.0, 0.0
    ox, oy = joy_state["offset"]
    dist = math.hypot(ox, oy)
    if dist < 1e-6:
        return 0.0, 0.0, 0.0
    return ox / dist, oy / dist, min(1.0, dist / JOY_BASE_RADIUS)

def draw_joystick(screen, joy_state):
    base_surf = pygame.Surface((JOY_BASE_RADIUS * 2, JOY_BASE_RADIUS * 2), pygame.SRCALPHA)
    pygame.draw.circle(base_surf, (255, 255, 255, 60), (JOY_BASE_RADIUS, JOY_BASE_RADIUS), JOY_BASE_RADIUS)
    pygame.draw.circle(base_surf, (255, 255, 255, 120), (JOY_BASE_RADIUS, JOY_BASE_RADIUS), JOY_BASE_RADIUS, width=3)
    screen.blit(base_surf, (JOY_BASE_POS[0] - JOY_BASE_RADIUS, JOY_BASE_POS[1] - JOY_BASE_RADIUS))

    ox, oy = joy_state["offset"] if joy_state["active"] else (0.0, 0.0)
    knob_surf = pygame.Surface((JOY_KNOB_RADIUS * 2, JOY_KNOB_RADIUS * 2), pygame.SRCALPHA)
    pygame.draw.circle(knob_surf, (255, 255, 255, 170), (JOY_KNOB_RADIUS, JOY_KNOB_RADIUS), JOY_KNOB_RADIUS)
    knob_x = JOY_BASE_POS[0] + ox - JOY_KNOB_RADIUS
    knob_y = JOY_BASE_POS[1] + oy - JOY_KNOB_RADIUS
    screen.blit(knob_surf, (knob_x, knob_y))

class Weapon:
    def __init__(self, type_id="rifle", tier_name="精良"):
        self.type_id = type_id
        self.type_data = WEAPON_TYPES[type_id]
        self.tier_name = tier_name
        self.tier_data = WEAPON_TIERS[tier_name]

    @property
    def display_name(self):
        return f"【{self.tier_name}】{self.type_data['name']}"

    @property
    def damage(self):
        return self.type_data["base_damage"] * self.tier_data["dmg_m"]

    @property
    def fire_rate(self):
        return self.type_data["base_fire_rate"] * self.tier_data["fr_m"]

    @property
    def shot_count(self):
        return self.type_data["base_shots"] + self.tier_data["add_s"]

    @property
    def pierce(self):
        return self.type_data["base_pierce"] + self.tier_data["add_p"]

    @property
    def max_range(self):
        return self.type_data["max_range"]

    @property
    def color(self):
        return self.tier_data["color"]

    def upgrade_tier(self):
        tiers = list(WEAPON_TIERS.keys())
        idx = tiers.index(self.tier_name)
        if idx < len(tiers) - 1:
            self.tier_name = tiers[idx + 1]
            self.tier_data = WEAPON_TIERS[self.tier_name]

    def change_type_randomly(self):
        other_types = [t for t in WEAPON_TYPES.keys() if t != self.type_id]
        self.type_id = random.choice(other_types)
        self.type_data = WEAPON_TYPES[self.type_id]

class PlayerStats:
    def __init__(self):
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 100

        self.max_hp = 100
        self.hp = 100
        self.move_speed = 5.0

        self.armor_tier = 0
        self.armor_hp = 0
        self.max_armor_hp = 0
        self.damage_reduction = 0.0

        self.weapon = Weapon("rifle", "精良")

    def equip_armor(self, tier):
        tier_info = ARMOR_TIERS[tier]
        self.armor_tier = tier
        self.max_armor_hp = tier_info["value"]
        self.armor_hp = self.max_armor_hp
        self.damage_reduction = tier_info["reduction"]

    def take_damage(self, raw_damage):
        damage = raw_damage * (1.0 - self.damage_reduction)
        if self.armor_hp > 0:
            if self.armor_hp >= damage:
                self.armor_hp -= damage
                damage = 0
            else:
                damage -= self.armor_hp
                self.armor_hp = 0
                self.armor_tier = 0
                self.damage_reduction = 0.0

        if damage > 0:
            self.hp -= damage
            if self.hp < 0:
                self.hp = 0

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

class GameHUD:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h

    def _draw_panel(self, surface, rect, bg_color, border_color=(15, 15, 20), depth=3):
        x, y, w, h = rect
        pygame.draw.rect(surface, border_color, (x, y + depth, w, h), border_radius=6)
        pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, border_color, (x, y, w, h), width=2, border_radius=6)

    def draw(self, screen, stats, current_wave, wave_timer_ratio, theme_name, boss, font_sm, font_md, font_lg):
        panel_x, panel_y = 20, 20
        panel_w, panel_h = 290, 90
        self._draw_panel(screen, (panel_x, panel_y, panel_w, panel_h), (35, 38, 50))

        self._draw_panel(screen, (panel_x + 10, panel_y + 10, 45, 45), (255, 200, 0))
        lvl_surf = font_lg.render(str(stats.level), True, (20, 20, 20))
        screen.blit(lvl_surf, (panel_x + 32 - lvl_surf.get_width()//2, panel_y + 32 - lvl_surf.get_height()//2))

        bar_x, bar_w = panel_x + 65, 210
        self._draw_panel(screen, (bar_x, panel_y + 15, bar_w, 20), (50, 20, 25))

        tot_cap = max(stats.max_hp, stats.hp + stats.armor_hp)
        inner_w = bar_w - 4

        hp_w = int(inner_w * (stats.hp / tot_cap)) if tot_cap > 0 else 0
        if hp_w > 0:
            pygame.draw.rect(screen, (230, 50, 60), (bar_x + 2, panel_y + 17, hp_w, 16), border_radius=3)

        if stats.armor_hp > 0:
            arm_color = ARMOR_TIERS[stats.armor_tier]["color"] if stats.armor_tier in ARMOR_TIERS else (255, 255, 255)
            arm_w = int(inner_w * (stats.armor_hp / tot_cap))
            arm_x = bar_x + 2 + hp_w
            if arm_x + arm_w > bar_x + 2 + inner_w:
                arm_w = (bar_x + 2 + inner_w) - arm_x
            if arm_w > 0:
                pygame.draw.rect(screen, arm_color, (arm_x, panel_y + 17, arm_w, 16), border_radius=3)

        text_str = f"{int(stats.hp)} + {int(stats.armor_hp)} ARM" if stats.armor_hp > 0 else f"{int(stats.hp)}/{int(stats.max_hp)}"
        screen.blit(font_sm.render(text_str, True, (255, 255, 255)), (bar_x + 40, panel_y + 16))

        self._draw_panel(screen, (bar_x, panel_y + 45, bar_w, 14), (10, 50, 70))
        exp_w = int(inner_w * (stats.exp / stats.exp_to_next_level)) if stats.exp_to_next_level > 0 else 0
        if exp_w > 0:
            pygame.draw.rect(screen, (0, 210, 255), (bar_x + 2, panel_y + 47, exp_w, 10), border_radius=3)

        wave_w = 220
        wave_x = (self.screen_w - wave_w) // 2
        self._draw_panel(screen, (wave_x, 15, wave_w, 50), (30, 30, 40))
        wave_str = "⚠️ BOSS WAVE" if current_wave % 5 == 0 else f"WAVE {current_wave}"
        w_surf = font_md.render(wave_str, True, (255, 50, 50) if current_wave % 5 == 0 else (255, 200, 0))
        screen.blit(w_surf, (wave_x + (wave_w - w_surf.get_width()) // 2, 18))

        theme_surf = font_sm.render(f"地圖：{theme_name}", True, (200, 210, 200))
        screen.blit(theme_surf, (wave_x + (wave_w - theme_surf.get_width()) // 2, 42))

        timer_w = int((wave_w - 20) * wave_timer_ratio)
        if timer_w > 0:
            pygame.draw.rect(screen, (255, 100, 0), (wave_x + 10, 58, timer_w, 4), border_radius=2)

        if boss is not None:
            boss_w = 320
            boss_x = (self.screen_w - boss_w) // 2
            self._draw_panel(screen, (boss_x, 70, boss_w, 26), (40, 15, 15))
            ratio = max(0.0, boss.hp / boss.max_hp)
            fill_w = int((boss_w - 8) * ratio)
            if fill_w > 0:
                pygame.draw.rect(screen, (220, 20, 40), (boss_x + 4, 74, fill_w, 18), border_radius=3)
            label = font_sm.render("BOSS", True, (255, 255, 255))
            screen.blit(label, (boss_x + boss_w // 2 - label.get_width() // 2, 76))

        card_w, card_h = 240, 70
        wx, wy = self.screen_w - card_w - 20, self.screen_h - card_h - 20
        self._draw_panel(screen, (wx, wy, card_w, card_h), (30, 32, 45))
        pygame.draw.rect(screen, stats.weapon.color, (wx, wy, card_w, card_h), width=2, border_radius=6)

        screen.blit(font_md.render(stats.weapon.display_name, True, stats.weapon.color), (wx + 10, wy + 8))
        d_text = f"傷害:{int(stats.weapon.damage)} | 彈數:{stats.weapon.shot_count} | 貫穿:{stats.weapon.pierce}"
        screen.blit(font_sm.render(d_text, True, (200, 200, 200)), (wx + 10, wy + 38))

class GameSession:
    def __init__(self):
        self.stats = PlayerStats()
        self.bullets = pygame.sprite.Group()
        self.zombies = pygame.sprite.Group()

        self.theme_index = 0
        self.obstacles = build_obstacles(self.theme_index)

        self.player_pos = [MAP_WIDTH // 2, MAP_HEIGHT // 2]
        self.player_angle = 0.0
        self.shoot_cooldown = 0.0

        self.current_wave = 1
        self.wave_timer = 30.0
        self.zombie_spawn_timer = 0.0

        self.pending_talent_choices = 0

        self.boss_wave_active = False
        self.boss_spawned = False
        self.boss_warning_timer = 0.0

        self.effect_flash_timer = 0.0
        self.particles = []

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

def draw_floating_bar(screen, cx, cy_top, width, height, ratio, fg_color, bg_color=(40, 15, 20)):
    x = cx - width // 2
    pygame.draw.rect(screen, bg_color, (x, cy_top, width, height), border_radius=3)
    fill_w = int((width - 2) * max(0.0, min(1.0, ratio)))
    if fill_w > 0:
        pygame.draw.rect(screen, fg_color, (x + 1, cy_top + 1, fill_w, height - 2), border_radius=2)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2.5D 積木人大戰殭屍")
    clock = pygame.time.Clock()

    FONT_NAME = "microsoftjhenghei"
    font_path = pygame.font.match_font(FONT_NAME)
    if font_path:
        font_sm = pygame.font.Font(font_path, 13)
        font_md = pygame.font.Font(font_path, 18)
        font_lg = pygame.font.Font(font_path, 26)
        font_xl = pygame.font.Font(font_path, 40)
    else:
        font_sm = pygame.font.SysFont(FONT_NAME, 13, bold=True)
        font_md = pygame.font.SysFont(FONT_NAME, 18, bold=True)
        font_lg = pygame.font.SysFont(FONT_NAME, 26, bold=True)
        font_xl = pygame.font.SysFont(FONT_NAME, 40, bold=True)

    hud = GameHUD(SCREEN_WIDTH, SCREEN_HEIGHT)

    session = GameSession()

    game_state = "INSTRUCTION"
    selected_talent_idx = 0
    talent_options = []

    joy_state = {"active": False, "offset": [0.0, 0.0]}

    final_stats_snapshot = {"wave": 1, "level": 1}

    def start_new_talent_choice():
        nonlocal talent_options, selected_talent_idx, game_state
        weights = [TALENT_WEIGHTS[t["id"]] for t in TALENT_POOL]
        talent_options = weighted_sample_without_replacement(TALENT_POOL, weights, 3)
        selected_talent_idx = 0
        game_state = "TALENT_SELECT"

    def confirm_talent(idx):
        nonlocal game_state
        chosen = talent_options[idx]
        stats = session.stats
        if chosen["id"] == "add_armor":
            stats.equip_armor(random.randint(1, 4))
        elif chosen["id"] == "hp_up":
            stats.max_hp += 25
            stats.hp = min(stats.hp + 25, stats.max_hp)
        elif chosen["id"] == "speed_up":
            stats.move_speed *= 1.12
        elif chosen["id"] == "weapon_tier_up":
            stats.weapon.upgrade_tier()
        elif chosen["id"] == "switch_weapon":
            stats.weapon.change_type_randomly()

        session.pending_talent_choices = max(0, session.pending_talent_choices - 1)
        if session.pending_talent_choices > 0:
            start_new_talent_choice()
        else:
            game_state = "PLAYING"

    def handle_pointer_down(pos):
        nonlocal game_state, session
        if game_state == "INSTRUCTION":
            game_state = "PLAYING"
        elif game_state == "GAME_OVER":
            session = GameSession()
            game_state = "INSTRUCTION"
        elif game_state == "TALENT_SELECT":
            for idx in range(len(talent_options)):
                bx = 180 + idx * 230
                by = 280
                if pygame.Rect(bx, by, 200, 240).collidepoint(pos):
                    confirm_talent(idx)
                    break
        elif game_state == "PLAYING":
            joystick_handle_down(pos, joy_state)

    def handle_pointer_move(pos):
        if game_state == "PLAYING":
            joystick_handle_move(pos, joy_state)

    def handle_pointer_up():
        if game_state == "PLAYING":
            joystick_handle_up(joy_state)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if game_state == "INSTRUCTION":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        game_state = "PLAYING"

                elif game_state == "TALENT_SELECT":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        selected_talent_idx = (selected_talent_idx - 1) % len(talent_options)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        selected_talent_idx = (selected_talent_idx + 1) % len(talent_options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        confirm_talent(selected_talent_idx)

                elif game_state == "GAME_OVER":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        session = GameSession()
                        game_state = "INSTRUCTION"

            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_pointer_down(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                handle_pointer_move(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                handle_pointer_up()
            elif event.type == pygame.FINGERDOWN:
                handle_pointer_down((event.x * SCREEN_WIDTH, event.y * SCREEN_HEIGHT))
            elif event.type == pygame.FINGERMOTION:
                handle_pointer_move((event.x * SCREEN_WIDTH, event.y * SCREEN_HEIGHT))
            elif event.type == pygame.FINGERUP:
                handle_pointer_up()

        if game_state == "PLAYING":
            stats = session.stats
            bullets = session.bullets
            zombies = session.zombies
            obstacles = session.obstacles
            player_pos = session.player_pos

            keys = pygame.key.get_pressed()

            kb_dx, kb_dy = 0, 0
            if keys[pygame.K_a]: kb_dx -= 1
            if keys[pygame.K_d]: kb_dx += 1
            if keys[pygame.K_w]: kb_dy -= 1
            if keys[pygame.K_s]: kb_dy += 1

            joy_dx, joy_dy, joy_mag = joystick_vector(joy_state)

            move_dir_x = move_dir_y = None
            speed_scale = 1.0
            if joy_mag > JOY_DEADZONE:
                move_dir_x, move_dir_y = joy_dx, joy_dy
                speed_scale = joy_mag
            elif kb_dx != 0 or kb_dy != 0:
                length = math.hypot(kb_dx, kb_dy)
                move_dir_x, move_dir_y = kb_dx / length, kb_dy / length

            if move_dir_x is not None:
                session.player_angle = math.degrees(math.atan2(move_dir_y, move_dir_x)) % 360
                move_x = move_dir_x * stats.move_speed * speed_scale
                move_y = move_dir_y * stats.move_speed * speed_scale

                player_rect = pygame.Rect(0, 0, 32, 32)
                player_rect.center = (player_pos[0], player_pos[1])
                player_rect = move_with_collision(player_rect, move_x, move_y, obstacles)

                player_pos[0] = max(0, min(MAP_WIDTH, player_rect.centerx))
                player_pos[1] = max(0, min(MAP_HEIGHT, player_rect.centery))

            if session.shoot_cooldown > 0:
                session.shoot_cooldown -= dt

            if session.shoot_cooldown <= 0:
                nearest = None
                nearest_dist = None
                for z in zombies:
                    d = math.hypot(z.rect.centerx - player_pos[0], z.rect.centery - player_pos[1])
                    if nearest_dist is None or d < nearest_dist:
                        nearest_dist = d
                        nearest = z

                if nearest is not None:
                    aim_angle = math.degrees(math.atan2(
                        nearest.rect.centery - player_pos[1],
                        nearest.rect.centerx - player_pos[0]
                    )) % 360
                else:
                    aim_angle = session.player_angle

                w = stats.weapon
                count = w.shot_count
                spread = w.type_data["spread_angle"]

                if count == 1:
                    angles = [aim_angle]
                else:
                    start_a = aim_angle - (spread * (count - 1) / 2)
                    angles = [start_a + i * spread for i in range(count)]

                for ang in angles:
                    b = Bullet(
                        player_pos[0], player_pos[1], ang,
                        w.damage, w.type_data["bullet_speed"],
                        w.pierce, w.color, w.tier_data["lvl"],
                        w.max_range
                    )
                    bullets.add(b)
                session.shoot_cooldown = w.fire_rate

            session.wave_timer -= dt
            if session.wave_timer <= 0:
                session.current_wave += 1
                session.wave_timer = 30.0

                new_theme = ((session.current_wave - 1) // THEME_WAVES) % len(MAP_THEMES)
                if new_theme != session.theme_index:
                    session.theme_index = new_theme
                    session.obstacles = build_obstacles(new_theme)
                    obstacles = session.obstacles

                if session.current_wave % 5 == 0:
                    session.boss_wave_active = True
                    session.boss_spawned = False
                    session.boss_warning_timer = BOSS_WARNING_DURATION

            if session.boss_warning_timer > 0:
                session.boss_warning_timer = max(0.0, session.boss_warning_timer - dt)

            boss_in_play = next((z for z in zombies if getattr(z, "is_boss", False)), None)

            if session.boss_wave_active and not session.boss_spawned and session.boss_warning_timer <= 0:
                bx = player_pos[0] + random.choice([-600, 600])
                by = player_pos[1] + random.choice([-450, 450])
                bx = max(0, min(MAP_WIDTH, bx))
                by = max(0, min(MAP_HEIGHT, by))
                boss_hp = (400 + session.current_wave * 80) * BOSS_HP_MULTIPLIER
                zombies.add(Boss(bx, by, hp=boss_hp, wave=session.current_wave))
                session.boss_spawned = True
                boss_in_play = next((z for z in zombies if getattr(z, "is_boss", False)), None)

            if session.boss_wave_active and session.boss_spawned and boss_in_play is None:
                session.boss_wave_active = False

            if not session.boss_wave_active or (session.boss_spawned and boss_in_play is None):
                session.zombie_spawn_timer -= dt
                if session.zombie_spawn_timer <= 0:
                    session.zombie_spawn_timer = max(0.4, 2.0 - (session.current_wave * 0.1))
                    zx = player_pos[0] + random.choice([-500, 500])
                    zy = player_pos[1] + random.choice([-400, 400])
                    zx = max(0, min(MAP_WIDTH, zx))
                    zy = max(0, min(MAP_HEIGHT, zy))
                    spawn_rect = pygame.Rect(0, 0, 32, 32)
                    spawn_rect.center = (zx, zy)
                    if not any(spawn_rect.colliderect(ob) for ob in obstacles):
                        zombies.add(Zombie(zx, zy, hp=20 + session.current_wave * 10, wave=session.current_wave))

            bullets.update(dt)
            for z in zombies:
                z.update(player_pos, obstacles, zombies)

            for p in session.particles[:]:
                p["age"] += dt
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                if p["age"] >= p["life"]:
                    session.particles.remove(p)
            if session.effect_flash_timer > 0:
                session.effect_flash_timer = max(0.0, session.effect_flash_timer - dt)

            for b in bullets:
                hits = pygame.sprite.spritecollide(b, zombies, False)
                for z in hits:
                    if z not in b.hit_enemies:
                        b.hit_enemies.add(z)
                        z.hp -= b.damage
                        b.pierce -= 1
                        if z.hp <= 0:
                            is_boss_kill = getattr(z, "is_boss", False)
                            death_x, death_y = z.rect.centerx, z.rect.centery
                            z.kill()

                            if is_boss_kill:
                                stats.exp += 150
                                stats.weapon.upgrade_tier()
                                stats.weapon.upgrade_tier()
                                session.effect_flash_timer = EFFECT_FLASH_DURATION
                                for _ in range(28):
                                    ang = random.uniform(0, 360)
                                    spd = random.uniform(80, 240)
                                    session.particles.append({
                                        "x": death_x, "y": death_y,
                                        "vx": math.cos(math.radians(ang)) * spd,
                                        "vy": math.sin(math.radians(ang)) * spd,
                                        "age": 0.0, "life": random.uniform(0.4, 0.9),
                                        "color": random.choice([(255, 215, 0), (255, 90, 90), (255, 255, 255)])
                                    })
                            else:
                                stats.exp += 12.5

                            while stats.exp >= stats.exp_to_next_level:
                                stats.level += 1
                                stats.exp -= stats.exp_to_next_level
                                stats.exp_to_next_level = int(stats.exp_to_next_level * 1.2)
                                session.pending_talent_choices += 1
                        if b.pierce <= 0:
                            b.kill()
                            break

            player_rect = pygame.Rect(player_pos[0] - 16, player_pos[1] - 16, 32, 32)
            for z in zombies:
                if player_rect.colliderect(z.rect):
                    stats.take_damage(z.attack)

            if session.pending_talent_choices > 0:
                start_new_talent_choice()

            if stats.hp <= 0:
                final_stats_snapshot["wave"] = session.current_wave
                final_stats_snapshot["level"] = stats.level
                game_state = "GAME_OVER"

        theme = MAP_THEMES[session.theme_index]
        screen.fill(theme["floor"])

        stats = session.stats
        bullets = session.bullets
        zombies = session.zombies
        obstacles = session.obstacles
        player_pos = session.player_pos

        cam_x = player_pos[0] - SCREEN_WIDTH // 2
        cam_y = player_pos[1] - SCREEN_HEIGHT // 2

        if game_state in ("PLAYING", "TALENT_SELECT", "GAME_OVER"):
            draw_scrolling_grid(screen, cam_x, cam_y, theme)

            render_objects = []
            render_objects.append((player_pos[1], "player", player_pos))
            for z in zombies:
                render_objects.append((z.rect.centery, "zombie", z))
            for ob in obstacles:
                render_objects.append((ob.centery, "obstacle", ob))

            render_objects.sort(key=lambda item: item[0])

            for b in bullets:
                screen.blit(b.image, (b.rect.x - cam_x, b.rect.y - cam_y))

            for obj in render_objects:
                if obj[1] == "player":
                    px, py = obj[2][0] - cam_x, obj[2][1] - cam_y
                    pygame.draw.ellipse(screen, (20, 30, 20), (px - 16, py + 8, 32, 12))
                    pygame.draw.rect(screen, (30, 100, 220), (px - 16, py - 16, 32, 32), border_radius=4)
                    hp_ratio = stats.hp / stats.max_hp if stats.max_hp > 0 else 0
                    draw_floating_bar(screen, px, py - 30, 40, 6, hp_ratio, (230, 50, 60))
                    if stats.armor_hp > 0:
                        arm_ratio = stats.armor_hp / stats.max_armor_hp if stats.max_armor_hp > 0 else 0
                        arm_color = ARMOR_TIERS[stats.armor_tier]["color"] if stats.armor_tier in ARMOR_TIERS else (255, 255, 255)
                        draw_floating_bar(screen, px, py - 22, 40, 4, arm_ratio, arm_color)
                elif obj[1] == "zombie":
                    z = obj[2]
                    zx, zy = z.rect.x - cam_x, z.rect.y - cam_y
                    shadow_w = z.rect.width
                    pygame.draw.ellipse(screen, (20, 30, 20), (zx, zy + z.rect.height - 8, shadow_w, 10))
                    screen.blit(z.image, (zx, zy))
                    z_hp_ratio = z.hp / z.max_hp if z.max_hp > 0 else 0
                    bar_w = 46 if getattr(z, "is_boss", False) else 28
                    draw_floating_bar(screen, z.rect.centerx - cam_x, zy - 10, bar_w, 5, z_hp_ratio, (220, 40, 40))
                elif obj[1] == "obstacle":
                    draw_obstacle(screen, obj[2], cam_x, cam_y, theme)

            for p in session.particles:
                alpha = max(0, 255 - int(255 * (p["age"] / p["life"])))
                radius = 3 + int(6 * (p["age"] / p["life"]))
                if alpha > 0:
                    particle_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(particle_surf, (*p["color"], alpha), (radius, radius), radius)
                    screen.blit(particle_surf, (p["x"] - cam_x - radius, p["y"] - cam_y - radius))

            boss_for_hud = next((z for z in zombies if getattr(z, "is_boss", False)), None)
            hud.draw(screen, stats, session.current_wave, session.wave_timer / 30.0,
                     theme["name"], boss_for_hud, font_sm, font_md, font_lg)

            if session.boss_warning_timer > 0:
                blink = math.sin(pygame.time.get_ticks() * 0.02) > 0
                if blink:
                    warn_surf = font_xl.render("⚠ BOSS 來襲 ⚠", True, (255, 50, 50))
                    screen.blit(warn_surf, ((SCREEN_WIDTH - warn_surf.get_width()) // 2, 220))

            if session.effect_flash_timer > 0:
                flash_alpha = int(200 * (session.effect_flash_timer / EFFECT_FLASH_DURATION))
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                flash_surf.fill((255, 235, 150, flash_alpha))
                screen.blit(flash_surf, (0, 0))

            if game_state == "PLAYING":
                draw_joystick(screen, joy_state)

        if game_state == "TALENT_SELECT":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            title = font_lg.render("🎉 經驗值滿額！請選擇升級天賦", True, (255, 215, 0))
            screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 150))

            if session.pending_talent_choices > 1:
                queue_txt = font_sm.render(f"（本次還有 {session.pending_talent_choices - 1} 次選擇等待中）", True, (255, 255, 255))
                screen.blit(queue_txt, ((SCREEN_WIDTH - queue_txt.get_width()) // 2, 195))

            for idx, opt in enumerate(talent_options):
                is_sel = (idx == selected_talent_idx)
                bx = 180 + idx * 230
                by = 280
                pygame.draw.rect(screen, (60, 65, 85) if is_sel else (35, 38, 50), (bx, by, 200, 240), border_radius=10)
                pygame.draw.rect(screen, (255, 215, 0) if is_sel else (80, 80, 80), (bx, by, 200, 240), width=3 if is_sel else 1, border_radius=10)

                screen.blit(font_md.render(opt["name"], True, (255, 255, 255)), (bx + 15, by + 20))
                desc_surf = font_sm.render(opt["desc"], True, (200, 200, 200))
                screen.blit(desc_surf, (bx + 15, by + 70))

        if game_state == "GAME_OVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 0, 0, 210))
            screen.blit(overlay, (0, 0))

            title = font_lg.render("💀 GAME OVER", True, (255, 60, 60))
            screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 260))

            stat_line1 = font_md.render(f"存活至第 {final_stats_snapshot['wave']} 波", True, (255, 255, 255))
            screen.blit(stat_line1, ((SCREEN_WIDTH - stat_line1.get_width()) // 2, 330))

            stat_line2 = font_md.render(f"角色等級 Lv.{final_stats_snapshot['level']}", True, (255, 255, 255))
            screen.blit(stat_line2, ((SCREEN_WIDTH - stat_line2.get_width()) // 2, 365))

            restart_txt = font_md.render("【 按 ENTER / SPACE 或點擊畫面 重新開始 】", True, (0, 255, 200))
            screen.blit(restart_txt, ((SCREEN_WIDTH - restart_txt.get_width()) // 2, 430))

        if game_state == "INSTRUCTION":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((15, 15, 25, 230))
            screen.blit(overlay, (0, 0))

            pygame.draw.rect(screen, (35, 40, 55), (212, 184, 600, 400), border_radius=12)
            pygame.draw.rect(screen, (255, 215, 0), (212, 184, 600, 400), width=3, border_radius=12)

            screen.blit(font_lg.render("🎮 2.5D 積木人大戰殭屍 - 操作說明", True, (255, 215, 0)), (260, 215))

            lines = [
                "WASD 鍵 / 左下角虛擬搖桿 : 控制移動與角色面向",
                "自動射擊 : 武器冷卻好會自動瞄準最近的敵人開火",
                "A / D 鍵 / 手機請直接點擊卡片 : 選擇升級天賦",
                "武器階級 : 精良 ➔ 史詩 ➔ 聖級 ➔ 王級 ➔ 帝級 ➔ 神級",
                "每 5 波會切換地圖主題，並有一隻 BOSS 來襲"
            ]
            for i, line in enumerate(lines):
                screen.blit(font_md.render(f"• {line}", True, (220, 220, 220)), (250, 280 + i * 38))

            start_txt = font_md.render("【 按 ENTER / SPACE 或點擊畫面 開始遊戲 】", True, (0, 255, 200))
            screen.blit(start_txt, ((SCREEN_WIDTH - start_txt.get_width()) // 2, 520))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()