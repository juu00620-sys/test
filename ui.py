# -*- coding: utf-8 -*-
"""HUD rendering, virtual joystick rendering, floating health bars,
and the talent-upgrade pool used on level-up."""
import math
import random
import pygame

from player import ARMOR_TIERS, JOY_BASE_POS, JOY_BASE_RADIUS, JOY_KNOB_RADIUS
from i18n import t, talent_text, LANG_LABELS, map_theme_name, weapon_display_name, armor_tier_name

# Must match the point sizes main.py uses when creating font_sm/font_md/font_lg/font_xl,
# so text-fitting helpers here start from the same size before shrinking to fit.
FONT_SIZE_SM = 13
FONT_SIZE_MD = 18
FONT_SIZE_LG = 26
FONT_SIZE_XL = 40

# Display names/descriptions now live in i18n.py (see talent_text()) so they
# can be translated. This pool only carries the stable, language-independent
# data used by game logic.
TALENT_POOL = [
    {"id": "add_armor", "max_rank": 5},
    {"id": "armor_airdrop", "max_rank": 5},
    {"id": "hp_up", "max_rank": 3},
    {"id": "speed_up", "max_rank": 3},
    {"id": "weapon_tier_up", "max_rank": 5},
    {"id": "switch_weapon", "max_rank": 5},
    {"id": "atk_speed_up", "max_rank": 5},
    {"id": "bullet_count_up", "max_rank": 4},
    {"id": "ricochet_up", "max_rank": 5, "requires_weapon": "rifle"},
]

TALENT_WEIGHTS = {
    "add_armor": 1.0,
    "armor_airdrop": 1.0,
    "hp_up": 1.0,
    "speed_up": 1.0,
    "weapon_tier_up": 0.35,
    "switch_weapon": 1.0,
    "atk_speed_up": 1.0,
    "bullet_count_up": 0.4,
    "ricochet_up": 0.5,
}

# Talent ids inside the same set are never offered together in one 3-choice
# talent-select screen. add_armor ("加護盾") and armor_airdrop ("護甲空投")
# both revolve around armor rolls, so they're kept mutually exclusive.
EXCLUSIVE_TALENT_GROUPS = [
    {"add_armor", "armor_airdrop"},
]


def _violates_exclusive_groups(chosen_ids):
    for group in EXCLUSIVE_TALENT_GROUPS:
        if len(group.intersection(chosen_ids)) > 1:
            return True
    return False


def sample_talent_options(population, weights, k, max_attempts=20):
    """Like weighted_sample_without_replacement, but re-rolls (up to
    max_attempts times) if the draw would put two ids from the same
    EXCLUSIVE_TALENT_GROUPS set in the same result."""
    picks = weighted_sample_without_replacement(population, weights, k)
    attempts = 1
    while _violates_exclusive_groups([p["id"] for p in picks]) and attempts < max_attempts:
        picks = weighted_sample_without_replacement(population, weights, k)
        attempts += 1
    return picks


_FONT_CACHE = {}


def _cached_font(font_path, size):
    key = (font_path, size)
    f = _FONT_CACHE.get(key)
    if f is None:
        f = pygame.font.Font(font_path, size)
        _FONT_CACHE[key] = f
    return f


def wrap_text(font, text, max_width):
    """Wraps text to fit max_width using the given font. Breaks on the last
    space when one is available (works for space-delimited languages);
    otherwise breaks per character (needed for CJK text, which has no
    spaces between words)."""
    if not text:
        return [""]
    if font.size(text)[0] <= max_width:
        return [text]
    lines = []
    current = ""
    for ch in text:
        trial = current + ch
        if font.size(trial)[0] <= max_width or not current:
            current = trial
        else:
            if " " in current:
                cut = current.rfind(" ")
                lines.append(current[:cut])
                current = current[cut + 1:].lstrip() + ch
            else:
                lines.append(current)
                current = ch
    if current:
        lines.append(current)
    return lines


def draw_wrapped_text(screen, font, text, color, x, y, max_width, line_gap=4, max_lines=None, dry_run=False):
    """Draws text wrapped to stay within max_width, starting at (x, y). If
    max_lines is given and there would be more lines than that, the extra
    is cut and the last visible line gets a trailing ellipsis so nothing
    overflows past that many lines. Returns the total pixel height used.
    With dry_run=True, computes/returns that height without drawing
    anything (screen may be None) - lets a caller measure how tall a block
    of text will be first, to size a container to fit it."""
    lines = wrap_text(font, text, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and font.size(last + "…")[0] > max_width:
            last = last[:-1]
        lines[-1] = (last + "…") if last else "…"
    line_h = font.get_height() + line_gap
    if not dry_run:
        for i, line in enumerate(lines):
            screen.blit(font.render(line, True, color), (x, y + i * line_h))
    return len(lines) * line_h


def fit_text_1line(font_path, text, max_width, base_size, min_size=10):
    """Shrinks font size (down to min_size) until text fits max_width on a
    single line; if it still doesn't fit at min_size, truncates with an
    ellipsis. Returns (font, text_to_render) — the font may differ from
    what base_size would normally give, and the text may be shortened."""
    size = base_size
    font = _cached_font(font_path, size)
    while font.size(text)[0] > max_width and size > min_size:
        size -= 1
        font = _cached_font(font_path, size)
    if font.size(text)[0] > max_width:
        fitted = text
        while len(fitted) > 1 and font.size(fitted + "…")[0] > max_width:
            fitted = fitted[:-1]
        text = (fitted + "…") if fitted else "…"
    return font, text


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


def draw_gear_icon(screen, center, radius, color, teeth=8, inner_ratio=0.62, hole_ratio=0.34):
    """Draws a simple gear/cog shape: a star-like polygon (alternating outer
    tooth points and inner root points) with a circular hole punched in the
    middle, in the given color."""
    cx, cy = center
    inner_r = radius * inner_ratio
    points = []
    step = math.pi / teeth
    for i in range(teeth * 2):
        angle = i * step - math.pi / 2
        r = radius if i % 2 == 0 else inner_r
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(screen, color, points)
    pygame.draw.circle(screen, color, (cx, cy), inner_r * 0.72)


def draw_pause_button(screen, screen_w, margin=16, size=44):
    """Small tappable gear (settings/pause) icon top-right, for touch
    devices with no ESC key."""
    rect = pygame.Rect(screen_w - size - margin, margin, size, size)
    pygame.draw.rect(screen, (35, 38, 50), rect, border_radius=8)
    pygame.draw.rect(screen, (255, 215, 0), rect, width=2, border_radius=8)
    draw_gear_icon(screen, rect.center, size * 0.30, (255, 255, 255), teeth=8)
    # Punch the hole in the gear using the button's own background color.
    pygame.draw.circle(screen, (35, 38, 50), rect.center, size * 0.30 * 0.62 * 0.72)
    return rect


def draw_pause_menu(screen, screen_w, screen_h, font_lg, font_md, font_sm, settings, font_path=None):
    """Draws the paused/settings overlay. Returns (button_rects, slider_rect,
    lang_button_rect) so the caller can hit-test clicks/taps against them."""
    lang = settings.get("lang", "en")

    overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    title_font, title_text = fit_text_1line(font_path, t(lang, "paused"), screen_w - 40, FONT_SIZE_LG)
    title = title_font.render(title_text, True, (255, 215, 0))
    screen.blit(title, ((screen_w - title.get_width()) // 2, 130))

    panel_w, panel_h = min(360, screen_w - 40), min(450, screen_h - 240)
    px = (screen_w - panel_w) // 2
    py = 200
    pygame.draw.rect(screen, (35, 38, 50), (px, py, panel_w, panel_h), border_radius=12)
    pygame.draw.rect(screen, (255, 215, 0), (px, py, panel_w, panel_h), width=3, border_radius=12)

    inner_w = panel_w - 40
    label_font, label_text = fit_text_1line(font_path, t(lang, "settings"), inner_w, FONT_SIZE_MD)
    label = label_font.render(label_text, True, (255, 255, 255))
    screen.blit(label, (px + 20, py + 18))

    vol_font, vol_text = fit_text_1line(
        font_path, t(lang, "master_volume", pct=int(settings["master_volume"] * 100)), inner_w, FONT_SIZE_SM
    )
    vol_label = vol_font.render(vol_text, True, (200, 200, 200))
    screen.blit(vol_label, (px + 20, py + 55))

    slider_x, slider_y, slider_w, slider_h = px + 20, py + 82, panel_w - 40, 10
    pygame.draw.rect(screen, (20, 20, 25), (slider_x, slider_y, slider_w, slider_h), border_radius=5)
    fill_w = int(slider_w * max(0.0, min(1.0, settings["master_volume"])))
    if fill_w > 0:
        pygame.draw.rect(screen, (0, 210, 255), (slider_x, slider_y, fill_w, slider_h), border_radius=5)
    knob_x = slider_x + fill_w
    pygame.draw.circle(screen, (255, 255, 255), (knob_x, slider_y + slider_h // 2), 8)

    # --- Language toggle row ---
    lang_row_y = slider_y + 34
    lang_btn_w, lang_btn_h = 90, 34
    lang_label_max_w = panel_w - 40 - lang_btn_w - 10
    lang_label_font, lang_label_text = fit_text_1line(font_path, t(lang, "language"), lang_label_max_w, FONT_SIZE_SM)
    lang_label = lang_label_font.render(lang_label_text, True, (200, 200, 200))
    screen.blit(lang_label, (px + 20, lang_row_y + 10))

    lang_btn_x = px + panel_w - 20 - lang_btn_w
    lang_button_rect = pygame.Rect(lang_btn_x, lang_row_y, lang_btn_w, lang_btn_h)
    pygame.draw.rect(screen, (55, 60, 80), lang_button_rect, border_radius=8)
    pygame.draw.rect(screen, (0, 210, 255), lang_button_rect, width=2, border_radius=8)
    lang_btn_font, lang_btn_text = fit_text_1line(font_path, LANG_LABELS.get(lang, lang.upper()), lang_btn_w - 12, FONT_SIZE_SM)
    lang_txt = lang_btn_font.render(lang_btn_text, True, (255, 255, 255))
    screen.blit(lang_txt, (lang_button_rect.centerx - lang_txt.get_width() // 2,
                            lang_button_rect.centery - lang_txt.get_height() // 2))

    button_labels = [t(lang, "resume"), t(lang, "restart"), t(lang, "quit_title")]
    btn_w, btn_h = panel_w - 40, 50
    start_y = lang_row_y + lang_btn_h + 20
    button_rects = []
    for i, text in enumerate(button_labels):
        bx, by = px + 20, start_y + i * (btn_h + 15)
        pygame.draw.rect(screen, (55, 60, 80), (bx, by, btn_w, btn_h), border_radius=8)
        pygame.draw.rect(screen, (255, 215, 0), (bx, by, btn_w, btn_h), width=2, border_radius=8)
        btn_font, btn_text = fit_text_1line(font_path, text, btn_w - 20, FONT_SIZE_MD)
        txt_surf = btn_font.render(btn_text, True, (255, 255, 255))
        screen.blit(txt_surf, (bx + (btn_w - txt_surf.get_width()) // 2, by + (btn_h - txt_surf.get_height()) // 2))
        button_rects.append(pygame.Rect(bx, by, btn_w, btn_h))

    slider_rect = pygame.Rect(slider_x, slider_y - 10, slider_w, slider_h + 20)
    return button_rects, slider_rect, lang_button_rect


# Content is rendered onto an off-screen surface this tall, then only a
# scrollable window of it is blitted onto the panel. Comfortably above the
# ~450px the current weapon+armor stat rows actually need, so scrolling
# math never has to deal with the content overflowing this scratch buffer.
_WEAPON_INFO_CONTENT_SURF_H = 700


def draw_weapon_info_panel(screen, screen_w, screen_h, font_lg, font_md, font_sm, stats, lang, font_path=None, scroll_offset=0):
    """Draws the weapon/armor detail overlay (opened via the C key or by
    tapping the weapon card). The stat list is rendered onto an off-screen
    surface and only a scroll_offset-shifted window of it is shown, so the
    caller can let it be scrolled (mouse wheel / touch-drag) instead of the
    content overflowing the panel. Returns (close_button_rect, max_scroll)
    so the caller can hit-test the "X" button and clamp its scroll state."""
    overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    panel_w, panel_h = min(420, screen_w - 40), min(480, screen_h - 40)
    px = (screen_w - panel_w) // 2
    py = (screen_h - panel_h) // 2
    pygame.draw.rect(screen, (35, 38, 50), (px, py, panel_w, panel_h), border_radius=12)
    pygame.draw.rect(screen, (255, 215, 0), (px, py, panel_w, panel_h), width=3, border_radius=12)

    inner_w = panel_w - 40

    title_font, title_text = fit_text_1line(font_path, t(lang, "weapon_info_title"), inner_w - 40, FONT_SIZE_LG)
    screen.blit(title_font.render(title_text, True, (255, 215, 0)), (px + 20, py + 18))

    # --- Close ("X") button, top-right of the panel ---
    close_size = 32
    close_rect = pygame.Rect(px + panel_w - 20 - close_size, py + 16, close_size, close_size)
    pygame.draw.rect(screen, (60, 30, 30), close_rect, border_radius=8)
    pygame.draw.rect(screen, (255, 90, 90), close_rect, width=2, border_radius=8)
    x_font = _cached_font(font_path, FONT_SIZE_MD)
    x_surf = x_font.render("X", True, (255, 255, 255))
    screen.blit(x_surf, (close_rect.centerx - x_surf.get_width() // 2, close_rect.centery - x_surf.get_height() // 2))

    weapon = stats.weapon

    # --- Scrollable content area, between the title and the hint line ---
    content_top = py + 65
    content_bottom = py + panel_h - 40
    content_h = content_bottom - content_top

    content_surf = pygame.Surface((panel_w, _WEAPON_INFO_CONTENT_SURF_H), pygame.SRCALPHA)
    cursor_y = 0

    def section_label(text_key):
        nonlocal cursor_y
        s_font, s_text = fit_text_1line(font_path, t(lang, text_key), inner_w, FONT_SIZE_MD)
        content_surf.blit(s_font.render(s_text, True, (255, 215, 0)), (20, cursor_y))
        cursor_y += s_font.get_height() + 8
        pygame.draw.line(content_surf, (70, 74, 90), (20, cursor_y), (panel_w - 20, cursor_y), 1)
        cursor_y += 8

    def stat_row(label_key, value_str, value_color=(255, 255, 255)):
        nonlocal cursor_y
        l_font, l_text = fit_text_1line(font_path, t(lang, label_key), inner_w * 0.55, FONT_SIZE_SM)
        content_surf.blit(l_font.render(l_text, True, (190, 190, 200)), (20, cursor_y))
        v_font, v_text = fit_text_1line(font_path, value_str, inner_w * 0.42, FONT_SIZE_SM)
        v_surf = v_font.render(v_text, True, value_color)
        content_surf.blit(v_surf, (panel_w - 20 - v_surf.get_width(), cursor_y))
        cursor_y += max(l_font.get_height(), v_font.get_height()) + 12

    # --- Weapon section ---
    section_label("weapon_info_weapon_section")

    name_font, name_text = fit_text_1line(font_path, weapon_display_name(lang, weapon.type_id, weapon.tier_name), inner_w, FONT_SIZE_MD)
    content_surf.blit(name_font.render(name_text, True, weapon.color), (20, cursor_y))
    cursor_y += name_font.get_height() + 14

    tier_mult = weapon.tier_data["dmg_m"]
    bonus_str = f"x{tier_mult:.2f}"
    if weapon.bonus_damage_mult > 1.0:
        bonus_str += f" (+{(weapon.bonus_damage_mult - 1) * 100:.0f}%)"

    stat_row("weapon_info_atk", f"{weapon.damage:.1f}")
    stat_row("weapon_info_atk_bonus", bonus_str)
    stat_row("weapon_info_fire_rate", f"{weapon.fire_rate:.2f}s")
    stat_row("stat_shots", str(weapon.shot_count))
    stat_row("stat_pierce", str(weapon.pierce))
    stat_row("weapon_info_range", str(weapon.max_range))

    cursor_y += 6

    # --- Armor section ---
    section_label("weapon_info_armor_section")

    if stats.armor_tier in ARMOR_TIERS:
        tier_info = ARMOR_TIERS[stats.armor_tier]
        tier_name = armor_tier_name(lang, stats.armor_tier, fallback=tier_info["name"])
        tier_font, tier_text = fit_text_1line(font_path, tier_name, inner_w, FONT_SIZE_MD)
        content_surf.blit(tier_font.render(tier_text, True, tier_info["color"]), (20, cursor_y))
        cursor_y += tier_font.get_height() + 14
    else:
        none_font, none_text = fit_text_1line(font_path, t(lang, "weapon_info_no_armor"), inner_w, FONT_SIZE_MD)
        content_surf.blit(none_font.render(none_text, True, (150, 150, 150)), (20, cursor_y))
        cursor_y += none_font.get_height() + 14

    stat_row("weapon_info_shield", f"{int(stats.armor_hp)} / {int(stats.max_armor_hp)}")
    stat_row("weapon_info_shield_pct", f"+{stats.shield_percent * 100:.0f}%")
    stat_row("weapon_info_reflect", f"+{stats.reflect_percent * 100:.0f}%")
    stat_row("weapon_info_lifesteal", f"+{(stats.lifesteal_percent + weapon.lifesteal_percent) * 100:.0f}%")
    stat_row("weapon_info_exp_gain", f"+{stats.exp_gain_mult * 100:.0f}%")

    total_content_h = cursor_y
    max_scroll = max(0, total_content_h - content_h)
    scroll_offset = max(0, min(int(scroll_offset), max_scroll))

    visible_rect = pygame.Rect(0, scroll_offset, panel_w, min(content_h, _WEAPON_INFO_CONTENT_SURF_H - scroll_offset))
    screen.blit(content_surf.subsurface(visible_rect), (px, content_top))

    # --- Scrollbar thumb, only shown once content actually overflows ---
    if max_scroll > 0:
        track_x = px + panel_w - 10
        pygame.draw.rect(screen, (60, 64, 80), (track_x, content_top, 4, content_h), border_radius=2)
        thumb_h = max(24, int(content_h * content_h / total_content_h))
        thumb_y = content_top + int((content_h - thumb_h) * (scroll_offset / max_scroll))
        pygame.draw.rect(screen, (0, 210, 255), (track_x, thumb_y, 4, thumb_h), border_radius=2)

    hint_font, hint_text = fit_text_1line(font_path, t(lang, "weapon_info_hint"), inner_w, FONT_SIZE_SM)
    hint_surf = hint_font.render(hint_text, True, (150, 150, 160))
    screen.blit(hint_surf, (px + (panel_w - hint_surf.get_width()) // 2, py + panel_h - 30))

    return close_rect, max_scroll


class GameHUD:
    def __init__(self, screen_w, screen_h, font_path=None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.font_path = font_path

    def _draw_panel(self, surface, rect, bg_color, border_color=(15, 15, 20), depth=3):
        x, y, w, h = rect
        pygame.draw.rect(surface, border_color, (x, y + depth, w, h), border_radius=6)
        pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, border_color, (x, y, w, h), width=2, border_radius=6)

    def draw(self, screen, stats, current_wave, wave_timer_ratio, theme_name, boss, font_sm, font_md, font_lg, lang="en"):
        # On a narrow (portrait phone) screen the wave banner used to be
        # centered at a fixed y=15, which overlaps the top-left level/HP
        # panel once the screen is too narrow to fit both side by side.
        # Below that width, stack the wave banner underneath the panel
        # instead; wide/landscape screens keep the original side-by-side
        # layout untouched.
        narrow = self.screen_w < 700
        margin = 12 if narrow else 20

        # Level / HP / EXP panel: kept anchored to the top-left corner,
        # just drawn at half its original size.
        panel_scale = 0.5
        panel_x, panel_y = margin, margin
        panel_w = min(int(290 * panel_scale), self.screen_w - 2 * margin)
        panel_h = int(90 * panel_scale)
        self._draw_panel(screen, (panel_x, panel_y, panel_w, panel_h), (35, 38, 50))

        badge = int(45 * panel_scale)
        badge_pad = int(10 * panel_scale)
        self._draw_panel(screen, (panel_x + badge_pad, panel_y + badge_pad, badge, badge), (255, 200, 0))
        lvl_surf = font_sm.render(str(stats.level), True, (20, 20, 20))
        badge_cx, badge_cy = panel_x + badge_pad + badge // 2, panel_y + badge_pad + badge // 2
        screen.blit(lvl_surf, (badge_cx - lvl_surf.get_width() // 2, badge_cy - lvl_surf.get_height() // 2))

        bar_x = panel_x + int(65 * panel_scale)
        bar_w = panel_w - (bar_x - panel_x) - badge_pad
        bar1_y, bar1_h = panel_y + int(15 * panel_scale), int(20 * panel_scale)
        self._draw_panel(screen, (bar_x, bar1_y, bar_w, bar1_h), (50, 20, 25))

        tot_cap = max(stats.max_hp, stats.hp + stats.armor_hp)
        inner_w = bar_w - 4
        fill_y, fill_h = bar1_y + 2, bar1_h - 4

        hp_w = int(inner_w * (stats.hp / tot_cap)) if tot_cap > 0 else 0
        if hp_w > 0:
            pygame.draw.rect(screen, (230, 50, 60), (bar_x + 2, fill_y, hp_w, fill_h), border_radius=3)

        if stats.armor_hp > 0:
            arm_color = ARMOR_TIERS[stats.armor_tier]["color"] if stats.armor_tier in ARMOR_TIERS else (255, 255, 255)
            arm_w = int(inner_w * (stats.armor_hp / tot_cap))
            arm_x = bar_x + 2 + hp_w
            if arm_x + arm_w > bar_x + 2 + inner_w:
                arm_w = (bar_x + 2 + inner_w) - arm_x
            if arm_w > 0:
                pygame.draw.rect(screen, arm_color, (arm_x, fill_y, arm_w, fill_h), border_radius=3)

        text_str = f"{int(stats.hp)} + {int(stats.armor_hp)} ARM" if stats.armor_hp > 0 else f"{int(stats.hp)}/{int(stats.max_hp)}"
        hp_text_font, hp_text_text = fit_text_1line(self.font_path, text_str, max(20, bar_w - 20), FONT_SIZE_SM)
        screen.blit(hp_text_font.render(hp_text_text, True, (255, 255, 255)), (bar_x + int(40 * panel_scale), bar1_y - 1))

        bar2_y, bar2_h = panel_y + int(45 * panel_scale), int(14 * panel_scale)
        self._draw_panel(screen, (bar_x, bar2_y, bar_w, bar2_h), (10, 50, 70))
        exp_w = int(inner_w * (stats.exp / stats.exp_to_next_level)) if stats.exp_to_next_level > 0 else 0
        if exp_w > 0:
            pygame.draw.rect(screen, (0, 210, 255), (bar_x + 2, bar2_y + 2, exp_w, bar2_h - 4), border_radius=3)

        wave_w = min(220, self.screen_w - 2 * margin)
        wave_x = (self.screen_w - wave_w) // 2
        wave_y = (panel_y + panel_h + 10) if narrow else 15
        self._draw_panel(screen, (wave_x, wave_y, wave_w, 50), (30, 30, 40))
        wave_str = t(lang, "boss_wave") if current_wave % 5 == 0 else t(lang, "wave", n=current_wave)
        w_font, w_text = fit_text_1line(self.font_path, wave_str, wave_w - 16, FONT_SIZE_MD)
        w_surf = w_font.render(w_text, True, (255, 50, 50) if current_wave % 5 == 0 else (255, 200, 0))
        screen.blit(w_surf, (wave_x + (wave_w - w_surf.get_width()) // 2, wave_y + 3))

        map_str = t(lang, "map", name=map_theme_name(lang, theme_name))
        theme_font, theme_text = fit_text_1line(self.font_path, map_str, wave_w - 16, FONT_SIZE_SM)
        theme_surf = theme_font.render(theme_text, True, (200, 210, 200))
        screen.blit(theme_surf, (wave_x + (wave_w - theme_surf.get_width()) // 2, wave_y + 27))

        timer_w = int((wave_w - 20) * wave_timer_ratio)
        if timer_w > 0:
            pygame.draw.rect(screen, (255, 100, 0), (wave_x + 10, wave_y + 43, timer_w, 4), border_radius=2)

        if boss is not None:
            boss_w = min(320, self.screen_w - 2 * margin)
            boss_x = (self.screen_w - boss_w) // 2
            boss_y = wave_y + 55
            self._draw_panel(screen, (boss_x, boss_y, boss_w, 26), (40, 15, 15))
            ratio = max(0.0, boss.hp / boss.max_hp)
            fill_w = int((boss_w - 8) * ratio)
            if fill_w > 0:
                pygame.draw.rect(screen, (220, 20, 40), (boss_x + 4, boss_y + 4, fill_w, 18), border_radius=3)
            boss_font, boss_text = fit_text_1line(self.font_path, t(lang, "boss"), boss_w - 16, FONT_SIZE_SM)
            label = boss_font.render(boss_text, True, (255, 255, 255))
            screen.blit(label, (boss_x + boss_w // 2 - label.get_width() // 2, boss_y + 6))

        # Weapon card: shrunk on narrow screens so it clears the (also
        # smaller, see player.py) joystick in the opposite bottom corner.
        card_scale = 0.8 if narrow else 1.0
        card_w, card_h = int(240 * card_scale), int(70 * card_scale)
        wx, wy = self.screen_w - card_w - margin, self.screen_h - card_h - margin
        self._draw_panel(screen, (wx, wy, card_w, card_h), (30, 32, 45))
        pygame.draw.rect(screen, stats.weapon.color, (wx, wy, card_w, card_h), width=2, border_radius=6)

        weapon_name = weapon_display_name(lang, stats.weapon.type_id, stats.weapon.tier_name)
        name_font, name_text = fit_text_1line(self.font_path, weapon_name, card_w - 20, FONT_SIZE_MD)
        screen.blit(name_font.render(name_text, True, stats.weapon.color), (wx + 10, wy + 8))
        d_text = (
            f"{t(lang, 'stat_dmg')}:{int(stats.weapon.damage)} | "
            f"{t(lang, 'stat_shots')}:{stats.weapon.shot_count} | "
            f"{t(lang, 'stat_pierce')}:{stats.weapon.pierce}"
        )
        stat_font, stat_text = fit_text_1line(self.font_path, d_text, card_w - 20, FONT_SIZE_SM)
        screen.blit(stat_font.render(stat_text, True, (200, 200, 200)), (wx + 10, wy + 38))

        return pygame.Rect(wx, wy, card_w, card_h)