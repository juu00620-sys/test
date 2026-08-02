# -*- coding: utf-8 -*-
"""HUD rendering, virtual joystick rendering, floating health bars,
and the talent-upgrade pool used on level-up."""
import random
import pygame

from player import ARMOR_TIERS, JOY_BASE_POS, JOY_BASE_RADIUS, JOY_KNOB_RADIUS

TALENT_POOL = [
    {"id": "add_armor", "name": "Armor Airdrop", "desc": "Randomly gain a high-tier armor set", "max_rank": 5},
    {"id": "hp_up", "name": "Vitality Boost", "desc": "Max HP +25, and restore 25 HP", "max_rank": 3},
    {"id": "speed_up", "name": "Light Footwork", "desc": "Move speed +12%", "max_rank": 3},
    {"id": "weapon_tier_up", "name": "Weapon Breakthrough", "desc": "Upgrade current weapon by one tier!", "max_rank": 5},
    {"id": "switch_weapon", "name": "Switch Weapon", "desc": "Randomly switch to another weapon type", "max_rank": 5},
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


def draw_floating_bar(screen, cx, cy_top, width, height, ratio, fg_color, bg_color=(40, 15, 20)):
    x = cx - width // 2
    pygame.draw.rect(screen, bg_color, (x, cy_top, width, height), border_radius=3)
    fill_w = int((width - 2) * max(0.0, min(1.0, ratio)))
    if fill_w > 0:
        pygame.draw.rect(screen, fg_color, (x + 1, cy_top + 1, fill_w, height - 2), border_radius=2)


def draw_pause_button(screen, screen_w, margin=16, size=44):
    """Small tappable pause icon top-right, for touch devices with no ESC key."""
    rect = pygame.Rect(screen_w - size - margin, margin, size, size)
    pygame.draw.rect(screen, (35, 38, 50), rect, border_radius=8)
    pygame.draw.rect(screen, (255, 215, 0), rect, width=2, border_radius=8)
    bar_w, bar_h = 5, 18
    cx, cy = rect.center
    pygame.draw.rect(screen, (255, 255, 255), (cx - 9, cy - bar_h // 2, bar_w, bar_h), border_radius=1)
    pygame.draw.rect(screen, (255, 255, 255), (cx + 4, cy - bar_h // 2, bar_w, bar_h), border_radius=1)
    return rect


def draw_pause_menu(screen, screen_w, screen_h, font_lg, font_md, font_sm, settings):
    """Draws the paused/settings overlay. Returns (button_rects, slider_rect)
    so the caller can hit-test clicks/taps against them."""
    overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    title = font_lg.render("⏸ Paused", True, (255, 215, 0))
    screen.blit(title, ((screen_w - title.get_width()) // 2, 130))

    panel_w, panel_h = 360, 380
    px = (screen_w - panel_w) // 2
    py = 200
    pygame.draw.rect(screen, (35, 38, 50), (px, py, panel_w, panel_h), border_radius=12)
    pygame.draw.rect(screen, (255, 215, 0), (px, py, panel_w, panel_h), width=3, border_radius=12)

    label = font_md.render("Settings", True, (255, 255, 255))
    screen.blit(label, (px + 20, py + 18))

    vol_label = font_sm.render(f"Master Volume: {int(settings['master_volume'] * 100)}%", True, (200, 200, 200))
    screen.blit(vol_label, (px + 20, py + 55))

    slider_x, slider_y, slider_w, slider_h = px + 20, py + 82, panel_w - 40, 10
    pygame.draw.rect(screen, (20, 20, 25), (slider_x, slider_y, slider_w, slider_h), border_radius=5)
    fill_w = int(slider_w * max(0.0, min(1.0, settings["master_volume"])))
    if fill_w > 0:
        pygame.draw.rect(screen, (0, 210, 255), (slider_x, slider_y, fill_w, slider_h), border_radius=5)
    knob_x = slider_x + fill_w
    pygame.draw.circle(screen, (255, 255, 255), (knob_x, slider_y + slider_h // 2), 8)

    button_labels = ["Resume", "Restart Game", "Quit to Title"]
    btn_w, btn_h = panel_w - 40, 50
    start_y = py + 125
    button_rects = []
    for i, text in enumerate(button_labels):
        bx, by = px + 20, start_y + i * (btn_h + 15)
        pygame.draw.rect(screen, (55, 60, 80), (bx, by, btn_w, btn_h), border_radius=8)
        pygame.draw.rect(screen, (255, 215, 0), (bx, by, btn_w, btn_h), width=2, border_radius=8)
        txt_surf = font_md.render(text, True, (255, 255, 255))
        screen.blit(txt_surf, (bx + (btn_w - txt_surf.get_width()) // 2, by + (btn_h - txt_surf.get_height()) // 2))
        button_rects.append(pygame.Rect(bx, by, btn_w, btn_h))

    slider_rect = pygame.Rect(slider_x, slider_y - 10, slider_w, slider_h + 20)
    return button_rects, slider_rect


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

        theme_surf = font_sm.render(f"Map: {theme_name}", True, (200, 210, 200))
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
        d_text = f"DMG:{int(stats.weapon.damage)} | Shots:{stats.weapon.shot_count} | Pierce:{stats.weapon.pierce}"
        screen.blit(font_sm.render(d_text, True, (200, 200, 200)), (wx + 10, wy + 38))