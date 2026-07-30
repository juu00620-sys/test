# -*- coding: utf-8 -*-
import pygame
import random
import math
import sys

# ==========================================
# 1. 基礎設定與資料庫
# ==========================================
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
MAP_WIDTH = 2400
MAP_HEIGHT = 1800

GRID_SIZE = 80  # 地板格線間距，純粹用來讓玩家感覺得到鏡頭在捲動

# 障礙物設定
OBSTACLE_SIZE = 90
OBSTACLE_MARGIN = 150          # 障礙物不會生成在太靠近地圖邊界的地方
PLAYER_SPAWN_CLEAR_RADIUS = 260  # 玩家出生點附近保留淨空，避免一開局就卡住
OBSTACLE_COUNT = 18

# 4 種基礎武器種類
WEAPON_TYPES = {
    "rifle": {
        "name": "突擊步槍",
        "base_damage": 15,
        "base_fire_rate": 0.2,
        "base_shots": 1,
        "base_pierce": 1,
        "spread_angle": 5,
        "bullet_speed": 12,
    },
    "shotgun": {
        "name": "散彈獵槍",
        "base_damage": 10,
        "base_fire_rate": 0.6,
        "base_shots": 5,
        "base_pierce": 1,
        "spread_angle": 25,
        "bullet_speed": 10,
    },
    "sniper": {
        "name": "重型貫穿槍",
        "base_damage": 55,
        "base_fire_rate": 1.0,
        "base_shots": 1,
        "base_pierce": 4,
        "spread_angle": 0,
        "bullet_speed": 18,
    },
    "grenade": {
        "name": "榴彈發射器",
        "base_damage": 40,
        "base_fire_rate": 1.2,
        "base_shots": 1,
        "base_pierce": 1,
        "spread_angle": 0,
        "bullet_speed": 8,
    }
}

# 6 大武器階級 (加成與顏色)
WEAPON_TIERS = {
    "精良": {"lvl": 1, "color": (50, 205, 50),   "dmg_m": 1.2, "fr_m": 0.9, "add_p": 0, "add_s": 0},
    "史詩": {"lvl": 2, "color": (147, 112, 219), "dmg_m": 1.5, "fr_m": 0.8, "add_p": 1, "add_s": 0},
    "聖級": {"lvl": 3, "color": (255, 215, 0),   "dmg_m": 2.0, "fr_m": 0.7, "add_p": 1, "add_s": 1},
    "王級": {"lvl": 4, "color": (255, 140, 0),   "dmg_m": 2.8, "fr_m": 0.6, "add_p": 2, "add_s": 2},
    "帝級": {"lvl": 5, "color": (220, 20, 60),   "dmg_m": 4.0, "fr_m": 0.5, "add_p": 3, "add_s": 3},
    "神級": {"lvl": 6, "color": (0, 255, 255),   "dmg_m": 6.5, "fr_m": 0.35, "add_p": 99, "add_s": 4}
}

# 4 階鎧甲定義
ARMOR_TIERS = {
    1: {"name": "木質積木甲", "color": (220, 220, 220), "value": 30, "reduction": 0.10},
    2: {"name": "鐵合金積木甲", "color": (180, 220, 255), "value": 60, "reduction": 0.20},
    3: {"name": "黃金合金積木甲", "color": (255, 235, 150), "value": 100, "reduction": 0.35},
    4: {"name": "振金鑽石積木甲", "color": (230, 180, 255), "value": 150, "reduction": 0.50},
}

# 天賦選擇池
TALENT_POOL = [
    {"id": "add_armor", "name": "裝備空投鎧甲", "desc": "隨機獲得一套高階白色護甲", "max_rank": 5},
    {"id": "hp_up", "name": "體力增強", "desc": "最大生命值 +25，並回復 25 HP", "max_rank": 3},
    {"id": "speed_up", "name": "輕裝上陣", "desc": "移動速度 +12%", "max_rank": 3},
    {"id": "weapon_tier_up", "name": "武器突破", "desc": "提高當前武器一階品質！", "max_rank": 5},
    {"id": "switch_weapon", "name": "更換武器款式", "desc": "隨機更換為其他武器類型", "max_rank": 5},
]

# ==========================================
# 2. 障礙物與碰撞輔助函式
# ==========================================
def build_obstacles():
    """產生固定配置的積木障礙物（用固定亂數種子，方便每次測試地圖配置一致）。"""
    rng = random.Random(20260730)
    obstacles = []
    spawn_x, spawn_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
    attempts = 0
    while len(obstacles) < OBSTACLE_COUNT and attempts < 1000:
        attempts += 1
        x = rng.randint(OBSTACLE_MARGIN, MAP_WIDTH - OBSTACLE_MARGIN - OBSTACLE_SIZE)
        y = rng.randint(OBSTACLE_MARGIN, MAP_HEIGHT - OBSTACLE_MARGIN - OBSTACLE_SIZE)
        rect = pygame.Rect(x, y, OBSTACLE_SIZE, OBSTACLE_SIZE)
        cx, cy = rect.center
        if math.hypot(cx - spawn_x, cy - spawn_y) < PLAYER_SPAWN_CLEAR_RADIUS:
            continue
        if any(rect.colliderect(o.inflate(40, 40)) for o in obstacles):
            continue
        obstacles.append(rect)
    return obstacles

def move_with_collision(rect, dx, dy, obstacles):
    """
    X、Y 軸分開位移與檢查碰撞，讓角色/殭屍可以貼著障礙物邊緣滑動，
    而不是一撞到就整個卡死不能動。回傳位移後的 rect（原地修改並回傳）。
    """
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

# ==========================================
# 3. 玩家與武器類別
# ==========================================
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

        # 鎧甲屬性
        self.armor_tier = 0
        self.armor_hp = 0
        self.max_armor_hp = 0
        self.damage_reduction = 0.0

        # 當前武器
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

# ==========================================
# 4. 遊戲物件 (子彈/殭屍)
# ==========================================
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle_deg, damage, speed, pierce, color, tier_lvl):
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

    def update(self, dt):
        self.pos_x += self.vx
        self.pos_y += self.vy
        self.rect.x, self.rect.y = int(self.pos_x), int(self.pos_y)
        if not (0 <= self.pos_x <= MAP_WIDTH and 0 <= self.pos_y <= MAP_HEIGHT):
            self.kill()

class Zombie(pygame.sprite.Sprite):
    def __init__(self, x, y, hp=30):
        super().__init__()
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        # 積木殭屍造型
        pygame.draw.rect(self.image, (40, 160, 60), (0, 0, 32, 32), border_radius=4)
        pygame.draw.rect(self.image, (20, 20, 20), (6, 6, 6, 6))
        pygame.draw.rect(self.image, (20, 20, 20), (20, 6, 6, 6))
        self.rect = self.image.get_rect(center=(x, y))

        self.pos_x, self.pos_y = float(x), float(y)
        self.hp = hp
        self.speed = 2.0

    def update(self, player_pos, obstacles, neighbors):
        dx = player_pos[0] - self.pos_x
        dy = player_pos[1] - self.pos_y
        dist = math.hypot(dx, dy)
        dir_x, dir_y = (dx / dist, dy / dist) if dist > 0 else (0.0, 0.0)

        # 分離力：跟附近其他殭屍互相推開，避免大家疊在同一個點上
        # 變成一坨閃爍的色塊（這就是「破圖」感的來源）。
        sep_x, sep_y = 0.0, 0.0
        for other in neighbors:
            if other is self:
                continue
            ox = self.pos_x - other.pos_x
            oy = self.pos_y - other.pos_y
            d = math.hypot(ox, oy)
            if 0 < d < 34:  # 殭屍圖示是 32x32，小於這個距離視為疊在一起
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

# ==========================================
# 5. 2.5D HUD & UI 系統 (完整渲染邏輯)
# ==========================================
class GameHUD:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h

    def _draw_panel(self, surface, rect, bg_color, border_color=(15, 15, 20), depth=3):
        x, y, w, h = rect
        pygame.draw.rect(surface, border_color, (x, y + depth, w, h), border_radius=6)
        pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, border_color, (x, y, w, h), width=2, border_radius=6)

    def draw(self, screen, stats, current_wave, wave_timer_ratio, font_sm, font_md, font_lg):
        # 1. 左上角複合血條 (紅血 + 白鎧甲)
        panel_x, panel_y = 20, 20
        panel_w, panel_h = 290, 90
        self._draw_panel(screen, (panel_x, panel_y, panel_w, panel_h), (35, 38, 50))

        # LV 徽章
        self._draw_panel(screen, (panel_x + 10, panel_y + 10, 45, 45), (255, 200, 0))
        lvl_surf = font_lg.render(str(stats.level), True, (20, 20, 20))
        screen.blit(lvl_surf, (panel_x + 32 - lvl_surf.get_width()//2, panel_y + 32 - lvl_surf.get_height()//2))

        # 同血條雙色繪製
        bar_x, bar_w = panel_x + 65, 210
        self._draw_panel(screen, (bar_x, panel_y + 15, bar_w, 20), (50, 20, 25))

        tot_cap = max(stats.max_hp, stats.hp + stats.armor_hp)
        inner_w = bar_w - 4

        # 紅色 HP
        hp_w = int(inner_w * (stats.hp / tot_cap)) if tot_cap > 0 else 0
        if hp_w > 0:
            pygame.draw.rect(screen, (230, 50, 60), (bar_x + 2, panel_y + 17, hp_w, 16), border_radius=3)

        # 白色/階級 Armor (接在紅血後方)
        if stats.armor_hp > 0:
            arm_color = ARMOR_TIERS[stats.armor_tier]["color"] if stats.armor_tier in ARMOR_TIERS else (255, 255, 255)
            arm_w = int(inner_w * (stats.armor_hp / tot_cap))
            arm_x = bar_x + 2 + hp_w
            if arm_x + arm_w > bar_x + 2 + inner_w:
                arm_w = (bar_x + 2 + inner_w) - arm_x
            if arm_w > 0:
                pygame.draw.rect(screen, arm_color, (arm_x, panel_y + 17, arm_w, 16), border_radius=3)

        # 血條數字標籤
        text_str = f"{int(stats.hp)} + {int(stats.armor_hp)} ARM" if stats.armor_hp > 0 else f"{int(stats.hp)}/{int(stats.max_hp)}"
        screen.blit(font_sm.render(text_str, True, (255, 255, 255)), (bar_x + 40, panel_y + 16))

        # 經驗值條
        self._draw_panel(screen, (bar_x, panel_y + 45, bar_w, 14), (10, 50, 70))
        exp_w = int(inner_w * (stats.exp / stats.exp_to_next_level)) if stats.exp_to_next_level > 0 else 0
        if exp_w > 0:
            pygame.draw.rect(screen, (0, 210, 255), (bar_x + 2, panel_y + 47, exp_w, 10), border_radius=3)

        # 2. 正上方 Wave 波次與倒數條
        wave_w = 200
        wave_x = (self.screen_w - wave_w) // 2
        self._draw_panel(screen, (wave_x, 15, wave_w, 50), (30, 30, 40))
        wave_str = "BOSS WAVE" if current_wave % 5 == 0 else f"WAVE {current_wave}"
        w_surf = font_md.render(wave_str, True, (255, 50, 50) if current_wave % 5 == 0 else (255, 200, 0))
        screen.blit(w_surf, (wave_x + (wave_w - w_surf.get_width()) // 2, 20))

        # 波次倒數條
        timer_w = int((wave_w - 20) * wave_timer_ratio)
        if timer_w > 0:
            pygame.draw.rect(screen, (255, 100, 0), (wave_x + 10, 52, timer_w, 4), border_radius=2)

        # 3. 右下角武器面板
        card_w, card_h = 240, 70
        wx, wy = self.screen_w - card_w - 20, self.screen_h - card_h - 20
        self._draw_panel(screen, (wx, wy, card_w, card_h), (30, 32, 45))
        pygame.draw.rect(screen, stats.weapon.color, (wx, wy, card_w, card_h), width=2, border_radius=6)

        screen.blit(font_md.render(stats.weapon.display_name, True, stats.weapon.color), (wx + 10, wy + 8))
        d_text = f"傷害:{int(stats.weapon.damage)} | 彈數:{stats.weapon.shot_count} | 貫穿:{stats.weapon.pierce}"
        screen.blit(font_sm.render(d_text, True, (200, 200, 200)), (wx + 10, wy + 38))

# ==========================================
# 6. 遊戲狀態容器 (供重開機使用)
# ==========================================
class GameSession:
    """把一局遊戲會用到的所有可變狀態包在一起，方便死亡後整包重建。"""
    def __init__(self):
        self.stats = PlayerStats()
        self.bullets = pygame.sprite.Group()
        self.zombies = pygame.sprite.Group()
        self.obstacles = build_obstacles()

        self.player_pos = [MAP_WIDTH // 2, MAP_HEIGHT // 2]
        self.player_angle = 0.0
        self.shoot_cooldown = 0.0

        self.current_wave = 1
        self.wave_timer = 30.0
        self.zombie_spawn_timer = 0.0

        # 升級佇列：一幀內可能同時觸發多次升級，
        # 用計數器排隊，逐一顯示天賦選擇畫面，不會被後面的擊殺覆蓋掉。
        self.pending_talent_choices = 0

# ==========================================
# 7. 場景繪製輔助
# ==========================================
def draw_scrolling_grid(screen, cam_x, cam_y):
    """
    畫出會隨鏡頭捲動的地板格線，讓玩家能夠實際「看到」自己在地圖上移動，
    而不是像純色背景那樣完全沒有參照物、看起來像卡住不能動。
    """
    grid_color = (38, 44, 38)
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

    # 地圖邊界線：畫出整張地圖的外框，讓玩家清楚知道世界的邊界在哪
    map_rect = pygame.Rect(0 - cam_x, 0 - cam_y, MAP_WIDTH, MAP_HEIGHT)
    pygame.draw.rect(screen, (80, 95, 75), map_rect, width=4)

def draw_obstacle(screen, ob_rect, cam_x, cam_y):
    ox, oy = ob_rect.x - cam_x, ob_rect.y - cam_y
    pygame.draw.rect(screen, (25, 20, 15), (ox + 4, oy + 8, ob_rect.width, ob_rect.height), border_radius=6)
    pygame.draw.rect(screen, (150, 110, 70), (ox, oy, ob_rect.width, ob_rect.height), border_radius=6)
    pygame.draw.rect(screen, (100, 70, 40), (ox, oy, ob_rect.width, ob_rect.height), width=3, border_radius=6)

# ==========================================
# 8. 主程式與完整遊戲迴圈
# ==========================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2.5D 積木人大戰殭屍")
    clock = pygame.time.Clock()

    # 字型初始化：統一使用微軟正黑體，若系統找不到該字型則自動退回預設字型
    FONT_NAME = "microsoftjhenghei"  # 微軟正黑體 (pygame.font.SysFont 會自動忽略空白/大小寫)
    font_path = pygame.font.match_font(FONT_NAME)
    if font_path:
        font_sm = pygame.font.Font(font_path, 13)
        font_md = pygame.font.Font(font_path, 18)
        font_lg = pygame.font.Font(font_path, 26)
    else:
        font_sm = pygame.font.SysFont(FONT_NAME, 13, bold=True)
        font_md = pygame.font.SysFont(FONT_NAME, 18, bold=True)
        font_lg = pygame.font.SysFont(FONT_NAME, 26, bold=True)

    hud = GameHUD(SCREEN_WIDTH, SCREEN_HEIGHT)

    session = GameSession()

    game_state = "INSTRUCTION"  # INSTRUCTION, PLAYING, TALENT_SELECT, GAME_OVER
    selected_talent_idx = 0
    talent_options = []

    # 死亡當下記錄下來的最終戰績，畫面上要一直顯示到重開為止
    final_stats_snapshot = {"wave": 1, "level": 1}

    def start_new_talent_choice():
        """從佇列中取出一次升級，產生新的天賦選項。呼叫前請確保 pending_talent_choices > 0。"""
        nonlocal talent_options, selected_talent_idx, game_state
        talent_options = random.sample(TALENT_POOL, 3)
        selected_talent_idx = 0
        game_state = "TALENT_SELECT"

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # 控制 60 FPS 並取得每幀秒數

        # --- 事件處理 ---
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
                        chosen = talent_options[selected_talent_idx]
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

                        # 這次選擇消耗掉一次排隊的升級機會。
                        # 如果同一幀還累積了其他升級，馬上接著顯示下一輪選項，
                        # 不會直接跳回 PLAYING 而把它們跳過。
                        session.pending_talent_choices = max(0, session.pending_talent_choices - 1)
                        if session.pending_talent_choices > 0:
                            start_new_talent_choice()
                        else:
                            game_state = "PLAYING"

                elif game_state == "GAME_OVER":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        # 整包重建遊戲狀態，回到說明畫面重新開始一局
                        session = GameSession()
                        game_state = "INSTRUCTION"

        # --- 戰鬥邏輯更新 ---
        if game_state == "PLAYING":
            stats = session.stats
            bullets = session.bullets
            zombies = session.zombies
            obstacles = session.obstacles
            player_pos = session.player_pos

            keys = pygame.key.get_pressed()

            # 1. WASD 移動邏輯 (加入障礙物碰撞，並將方向向量正規化避免斜走過快)
            dx, dy = 0, 0
            if keys[pygame.K_a]: dx -= 1
            if keys[pygame.K_d]: dx += 1
            if keys[pygame.K_w]: dy -= 1
            if keys[pygame.K_s]: dy += 1

            if dx != 0 or dy != 0:
                session.player_angle = math.degrees(math.atan2(dy, dx)) % 360
                length = math.hypot(dx, dy)
                move_x = dx / length * stats.move_speed
                move_y = dy / length * stats.move_speed

                player_rect = pygame.Rect(0, 0, 32, 32)
                player_rect.center = (player_pos[0], player_pos[1])
                player_rect = move_with_collision(player_rect, move_x, move_y, obstacles)

                player_pos[0] = max(0, min(MAP_WIDTH, player_rect.centerx))
                player_pos[1] = max(0, min(MAP_HEIGHT, player_rect.centery))

            # 2. ENTER 鍵連續射擊邏輯
            if session.shoot_cooldown > 0:
                session.shoot_cooldown -= dt

            if keys[pygame.K_RETURN] and session.shoot_cooldown <= 0:
                w = stats.weapon
                count = w.shot_count
                spread = w.type_data["spread_angle"]

                if count == 1:
                    angles = [session.player_angle]
                else:
                    start_a = session.player_angle - (spread * (count - 1) / 2)
                    angles = [start_a + i * spread for i in range(count)]

                for ang in angles:
                    b = Bullet(
                        player_pos[0], player_pos[1], ang,
                        w.damage, w.type_data["bullet_speed"],
                        w.pierce, w.color, w.tier_data["lvl"]
                    )
                    bullets.add(b)
                session.shoot_cooldown = w.fire_rate

            # 3. 波次與生怪計時器
            session.wave_timer -= dt
            if session.wave_timer <= 0:
                session.current_wave += 1
                session.wave_timer = 30.0

            session.zombie_spawn_timer -= dt
            if session.zombie_spawn_timer <= 0:
                session.zombie_spawn_timer = max(0.4, 2.0 - (session.current_wave * 0.1))
                zx = player_pos[0] + random.choice([-500, 500])
                zy = player_pos[1] + random.choice([-400, 400])
                zx = max(0, min(MAP_WIDTH, zx))
                zy = max(0, min(MAP_HEIGHT, zy))
                spawn_rect = pygame.Rect(0, 0, 32, 32)
                spawn_rect.center = (zx, zy)
                # 避免生成點剛好卡在障礙物裡；卡到就跳過這次生成，下個計時週期再試
                if not any(spawn_rect.colliderect(ob) for ob in obstacles):
                    zombies.add(Zombie(zx, zy, hp=20 + session.current_wave * 10))

            # 4. 物件更新與碰撞處理
            bullets.update(dt)
            for z in zombies:
                z.update(player_pos, obstacles, zombies)

            # 子彈與殭屍碰撞
            for b in bullets:
                hits = pygame.sprite.spritecollide(b, zombies, False)
                for z in hits:
                    if z not in b.hit_enemies:
                        b.hit_enemies.add(z)
                        z.hp -= b.damage
                        b.pierce -= 1
                        if z.hp <= 0:
                            z.kill()
                            stats.exp += 25
                            # 升級觸發：用 while 處理一次擊殺內連續升多級的情況，
                            # 每升一級就把選擇機會排進佇列，而不是直接覆蓋。
                            while stats.exp >= stats.exp_to_next_level:
                                stats.level += 1
                                stats.exp -= stats.exp_to_next_level
                                stats.exp_to_next_level = int(stats.exp_to_next_level * 1.2)
                                session.pending_talent_choices += 1
                        if b.pierce <= 0:
                            b.kill()
                            break

            # 玩家與殭屍碰撞
            player_rect = pygame.Rect(player_pos[0] - 16, player_pos[1] - 16, 32, 32)
            for z in zombies:
                if player_rect.colliderect(z.rect):
                    stats.take_damage(0.3)

            # 這一幀如果有排隊的升級選擇，且尚未死亡，就進入天賦選擇畫面
            if session.pending_talent_choices > 0:
                start_new_talent_choice()

            # 5. 死亡判定：血量歸零就結束這一局，顯示 GAME OVER 畫面
            if stats.hp <= 0:
                final_stats_snapshot["wave"] = session.current_wave
                final_stats_snapshot["level"] = stats.level
                game_state = "GAME_OVER"

        # --- 畫面繪製與 2.5D Camera ---
        screen.fill((45, 50, 45))  # 地圖底色

        stats = session.stats
        bullets = session.bullets
        zombies = session.zombies
        obstacles = session.obstacles
        player_pos = session.player_pos

        cam_x = player_pos[0] - SCREEN_WIDTH // 2
        cam_y = player_pos[1] - SCREEN_HEIGHT // 2

        if game_state in ("PLAYING", "TALENT_SELECT", "GAME_OVER"):
            # 先畫捲動格線 + 地圖邊界，讓移動看得出來
            draw_scrolling_grid(screen, cam_x, cam_y)

            # Y-sorting 深度排序繪製 (加入障礙物一起排序)
            render_objects = []
            render_objects.append((player_pos[1], "player", player_pos))
            for z in zombies:
                render_objects.append((z.rect.centery, "zombie", z))
            for ob in obstacles:
                render_objects.append((ob.centery, "obstacle", ob))

            render_objects.sort(key=lambda item: item[0])

            # 繪製子彈
            for b in bullets:
                screen.blit(b.image, (b.rect.x - cam_x, b.rect.y - cam_y))

            # 繪製積木角色、殭屍、障礙物與陰影 (依 Y 座標排序，確保前後遮蔽正確)
            for obj in render_objects:
                if obj[1] == "player":
                    px, py = obj[2][0] - cam_x, obj[2][1] - cam_y
                    pygame.draw.ellipse(screen, (20, 30, 20), (px - 16, py + 8, 32, 12))
                    pygame.draw.rect(screen, (30, 100, 220), (px - 16, py - 16, 32, 32), border_radius=4)
                elif obj[1] == "zombie":
                    z = obj[2]
                    zx, zy = z.rect.x - cam_x, z.rect.y - cam_y
                    pygame.draw.ellipse(screen, (20, 30, 20), (zx, zy + 24, 32, 10))
                    screen.blit(z.image, (zx, zy))
                elif obj[1] == "obstacle":
                    draw_obstacle(screen, obj[2], cam_x, cam_y)

            # 繪製頂層 HUD
            hud.draw(screen, stats, session.current_wave, session.wave_timer / 30.0, font_sm, font_md, font_lg)

        # --- 升級 UI Overlay ---
        if game_state == "TALENT_SELECT":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            title = font_lg.render("經驗值滿額！請選擇升級天賦", True, (255, 215, 0))
            screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 150))

            # 如果佇列裡還有排隊的升級，提示玩家還有幾次可以選
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

        # --- 死亡結算畫面 ---
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

            restart_txt = font_md.render("【 按 ENTER 或 SPACE 鍵 重新開始 】", True, (0, 255, 200))
            screen.blit(restart_txt, ((SCREEN_WIDTH - restart_txt.get_width()) // 2, 430))

        # --- 遊戲開始操作說明 ---
        if game_state == "INSTRUCTION":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((15, 15, 25, 230))
            screen.blit(overlay, (0, 0))

            pygame.draw.rect(screen, (35, 40, 55), (212, 184, 600, 400), border_radius=12)
            pygame.draw.rect(screen, (255, 215, 0), (212, 184, 600, 400), width=3, border_radius=12)

            screen.blit(font_lg.render("🎮 2.5D 積木人大戰殭屍 - 操作說明", True, (255, 215, 0)), (260, 215))

            lines = [
                "WASD 鍵 : 控制移動與角色面向",
                "長按 ENTER : 發射當前武器彈幕",
                "A / D 鍵 : 天賦選單左右切換選項",
                "武器階級 : 精良 ➔ 史詩 ➔ 聖級 ➔ 王級 ➔ 帝級 ➔ 神級",
                "複合血條 : 紅色為基礎 HP，白色為護甲鎧甲 (先扣護甲)"
            ]
            for i, line in enumerate(lines):
                screen.blit(font_md.render(f"• {line}", True, (220, 220, 220)), (250, 280 + i * 38))

            start_txt = font_md.render("【 按 ENTER 或 SPACE 鍵 開始遊戲 】", True, (0, 255, 200))
            screen.blit(start_txt, ((SCREEN_WIDTH - start_txt.get_width()) // 2, 520))

        # 更新畫面
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()