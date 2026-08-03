# -*- coding: utf-8 -*-
import os
import sys
import math
import random
import asyncio
import pygame

from map import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT,
    THEME_WAVES, MAP_THEMES,
    build_obstacles, move_with_collision,
    draw_scrolling_grid, draw_obstacle,
)
from weapon import Weapon
from player import (
    PlayerStats, ARMOR_TIERS,
    joystick_handle_down, joystick_handle_move, joystick_handle_up, joystick_vector,
)
from zombie import (
    Zombie, Boss,
    BOSS_WARNING_DURATION, BOSS_HP_MULTIPLIER, BOSS_ATTACK_MULTIPLIER,
    draw_boss_meteors,
)
from bullet import Bullet
from effects import (
    EFFECT_FLASH_DURATION,
    spawn_boss_kill_particles, spawn_explosion_particles, update_particles, draw_particles, draw_effect_flash,
)
from ui import (
    GameHUD, draw_joystick, draw_floating_bar,
    draw_pause_button, draw_pause_menu, draw_weapon_info_panel,
    TALENT_POOL, TALENT_WEIGHTS, sample_talent_options,
    draw_wrapped_text, fit_text_1line, FONT_SIZE_MD, FONT_SIZE_SM, FONT_SIZE_LG,
)
from i18n import t, instruction_lines, talent_text, next_lang


def talent_card_rects(count):
    """Lays out `count` talent-select cards. On screens wide enough it's
    the original single horizontal row, centered; on screens too narrow
    for that (portrait phones), the cards stack vertically instead so
    each one stays full-width and fully on-screen rather than overflowing
    the sides."""
    gap = 20
    default_w, default_h = 200, 240
    row_w = count * default_w + (count - 1) * gap

    if SCREEN_WIDTH >= row_w + 40:
        start_x = (SCREEN_WIDTH - row_w) // 2
        by = min(280, max(20, SCREEN_HEIGHT - default_h - 40))
        return [pygame.Rect(start_x + i * (default_w + gap), by, default_w, default_h) for i in range(count)]

    card_w = min(default_w, SCREEN_WIDTH - 40)
    card_h = min(default_h, max(140, (SCREEN_HEIGHT - 60 - (count - 1) * gap) // count))
    bx = (SCREEN_WIDTH - card_w) // 2
    total_h = count * card_h + (count - 1) * gap
    start_y = max(20, (SCREEN_HEIGHT - total_h) // 2)
    return [pygame.Rect(bx, start_y + i * (card_h + gap), card_w, card_h) for i in range(count)]


class GameSession:
    """Bundles all the mutable state for one playthrough so it can be
    rebuilt wholesale after death / restart."""
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


async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2.5D Block Man vs Zombies")
    clock = pygame.time.Clock()

    # Optional custom font: drop a .ttf into assets/fonts/font.ttf and it
    # will be picked up automatically; otherwise falls back to the safe
    # built-in pygame default font (works reliably in the browser/WASM build).
    FONT_PATH = os.path.join("assets", "fonts", "font.ttf")
    if not os.path.isfile(FONT_PATH):
        FONT_PATH = None

    font_sm = pygame.font.Font(FONT_PATH, 13)
    font_md = pygame.font.Font(FONT_PATH, 18)
    font_lg = pygame.font.Font(FONT_PATH, 26)
    font_xl = pygame.font.Font(FONT_PATH, 40)

    hud = GameHUD(SCREEN_WIDTH, SCREEN_HEIGHT, FONT_PATH)

    session = GameSession()

    game_state = "INSTRUCTION"
    selected_talent_idx = 0
    talent_options = []

    joy_state = {"active": False, "offset": [0.0, 0.0]}

    settings = {"master_volume": 0.7, "lang": "en"}
    pause_buttons = []
    pause_slider_rect = None
    pause_lang_button_rect = None
    pause_button_rect = None
    weapon_card_rect = None
    weapon_info_close_rect = None
    weapon_info_scroll = 0.0
    weapon_info_max_scroll = 0.0
    dragging_volume = False
    dragging_weapon_info = False
    weapon_info_drag_last_y = 0

    final_stats_snapshot = {"wave": 1, "level": 1}

    def start_new_talent_choice():
        nonlocal talent_options, selected_talent_idx, game_state
        weights = [TALENT_WEIGHTS[t["id"]] for t in TALENT_POOL]
        talent_options = sample_talent_options(TALENT_POOL, weights, 3)
        selected_talent_idx = 0
        game_state = "TALENT_SELECT"

    def confirm_talent(idx):
        nonlocal game_state
        chosen = talent_options[idx]
        stats = session.stats
        if chosen["id"] == "add_armor":
            stats.try_add_shield_tier(random.randint(1, 4))
        elif chosen["id"] == "armor_airdrop":
            stats.apply_airdrop(random.randint(1, 4))
        elif chosen["id"] == "hp_up":
            stats.add_max_hp(25)
        elif chosen["id"] == "speed_up":
            stats.move_speed *= 1.05
        elif chosen["id"] == "weapon_tier_up":
            stats.weapon.upgrade_tier_or_boost_damage()
        elif chosen["id"] == "switch_weapon":
            stats.weapon.change_type_randomly()

        session.pending_talent_choices = max(0, session.pending_talent_choices - 1)
        if session.pending_talent_choices > 0:
            start_new_talent_choice()
        else:
            game_state = "PLAYING"

    def award_zombie_kill(z):
        """Kills z and grants its rewards (exp / boss loot / talent
        choices). Shared by direct bullet hits, explosion splash damage,
        and burn ticks so the reward logic only lives in one place."""
        stats = session.stats
        is_boss_kill = getattr(z, "is_boss", False)
        death_x, death_y = z.rect.centerx, z.rect.centery
        z.kill()

        if is_boss_kill:
            stats.exp += 150 * (1.0 + stats.exp_gain_mult)
            session.pending_talent_choices += 1
            session.effect_flash_timer = EFFECT_FLASH_DURATION
            spawn_boss_kill_particles(session.particles, death_x, death_y)
        else:
            stats.exp += 12.5 * (1.0 + stats.exp_gain_mult)

        while stats.exp >= stats.exp_to_next_level:
            stats.level += 1
            stats.exp -= stats.exp_to_next_level
            stats.exp_to_next_level = int(stats.exp_to_next_level * 1.2)
            session.pending_talent_choices += 1

    def trigger_explosion(b, origin_zombie):
        """Grenade Launcher impact: splash damage to nearby zombies plus a
        burn-over-time debuff on everything caught in the blast."""
        ex, ey = origin_zombie.rect.centerx, origin_zombie.rect.centery
        spawn_explosion_particles(session.particles, ex, ey)

        for other in list(session.zombies):
            if other is origin_zombie:
                continue
            d = math.hypot(other.rect.centerx - ex, other.rect.centery - ey)
            if d <= b.explosion_radius:
                other.hp -= b.explosion_damage
                if session.stats.lifesteal_percent > 0:
                    stats = session.stats
                    stats.hp = min(stats.max_hp, stats.hp + b.explosion_damage * stats.lifesteal_percent)
                if other.hp <= 0:
                    award_zombie_kill(other)
                elif hasattr(other, "apply_burn"):
                    other.apply_burn(b.burn_dps, b.burn_duration)

        if origin_zombie.hp > 0 and hasattr(origin_zombie, "apply_burn"):
            origin_zombie.apply_burn(b.burn_dps, b.burn_duration)

    def handle_pointer_down(pos):
        nonlocal game_state, session, dragging_volume, dragging_weapon_info, weapon_info_drag_last_y, weapon_info_scroll
        if game_state == "INSTRUCTION":
            game_state = "PLAYING"
        elif game_state == "GAME_OVER":
            session = GameSession()
            game_state = "INSTRUCTION"
        elif game_state == "TALENT_SELECT":
            for idx, rect in enumerate(talent_card_rects(len(talent_options))):
                if rect.collidepoint(pos):
                    confirm_talent(idx)
                    break
        elif game_state == "PAUSED":
            for idx, rect in enumerate(pause_buttons):
                if rect.collidepoint(pos):
                    if idx == 0:
                        game_state = "PLAYING"
                    elif idx == 1:
                        session = GameSession()
                        game_state = "PLAYING"
                    elif idx == 2:
                        session = GameSession()
                        game_state = "INSTRUCTION"
                    return
            if pause_lang_button_rect and pause_lang_button_rect.collidepoint(pos):
                settings["lang"] = next_lang(settings["lang"])
                return
            if pause_slider_rect and pause_slider_rect.collidepoint(pos):
                dragging_volume = True
                ratio = (pos[0] - pause_slider_rect.x) / pause_slider_rect.width
                settings["master_volume"] = max(0.0, min(1.0, ratio))
        elif game_state == "WEAPON_INFO":
            if weapon_info_close_rect and weapon_info_close_rect.collidepoint(pos):
                game_state = "PLAYING"
            else:
                dragging_weapon_info = True
                weapon_info_drag_last_y = pos[1]
        elif game_state == "PLAYING":
            if pause_button_rect and pause_button_rect.collidepoint(pos):
                game_state = "PAUSED"
            elif weapon_card_rect and weapon_card_rect.collidepoint(pos):
                game_state = "WEAPON_INFO"
                weapon_info_scroll = 0.0
            else:
                joystick_handle_down(pos, joy_state)

    def handle_pointer_move(pos):
        nonlocal weapon_info_scroll, weapon_info_drag_last_y
        if game_state == "PLAYING":
            joystick_handle_move(pos, joy_state)
        elif game_state == "PAUSED" and dragging_volume and pause_slider_rect:
            ratio = (pos[0] - pause_slider_rect.x) / pause_slider_rect.width
            settings["master_volume"] = max(0.0, min(1.0, ratio))
        elif game_state == "WEAPON_INFO" and dragging_weapon_info:
            dy = pos[1] - weapon_info_drag_last_y
            weapon_info_scroll = max(0.0, min(weapon_info_max_scroll, weapon_info_scroll - dy))
            weapon_info_drag_last_y = pos[1]

    def handle_pointer_up():
        nonlocal dragging_volume, dragging_weapon_info
        if game_state == "PLAYING":
            joystick_handle_up(joy_state)
        dragging_volume = False
        dragging_weapon_info = False

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and game_state in ("PLAYING", "PAUSED"):
                    game_state = "PAUSED" if game_state == "PLAYING" else "PLAYING"
                elif event.key == pygame.K_ESCAPE and game_state == "WEAPON_INFO":
                    game_state = "PLAYING"
                elif event.key == pygame.K_c and game_state == "PLAYING":
                    game_state = "WEAPON_INFO"
                    weapon_info_scroll = 0.0
                elif event.key == pygame.K_c and game_state == "WEAPON_INFO":
                    game_state = "PLAYING"

                elif game_state == "INSTRUCTION":
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
            elif event.type == pygame.MOUSEWHEEL:
                if game_state == "WEAPON_INFO":
                    weapon_info_scroll = max(0.0, min(weapon_info_max_scroll, weapon_info_scroll - event.y * 40))

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
            if joy_mag > 0.15:
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

                is_explosive = w.type_data.get("explosive", False)
                if is_explosive:
                    explosion_radius = w.type_data.get("explosion_radius", 0)
                    explosion_damage = w.damage * w.type_data.get("explosion_damage_ratio", 1.0)
                    burn_dps = w.damage * w.type_data.get("burn_dps_ratio", 0.0)
                    burn_duration = w.type_data.get("burn_duration", 0.0)
                else:
                    explosion_radius, explosion_damage, burn_dps, burn_duration = 0, 0.0, 0.0, 0.0

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
                        w.max_range,
                        explosive=is_explosive, explosion_radius=explosion_radius,
                        explosion_damage=explosion_damage,
                        burn_dps=burn_dps, burn_duration=burn_duration,
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
            for z in list(zombies):
                if getattr(z, "is_boss", False):
                    z.update(player_pos, obstacles, zombies, dt,
                             on_player_hit=lambda dmg, boss=z: stats.take_damage(dmg, attacker=boss))
                    if z.hp <= 0:
                        award_zombie_kill(z)
                else:
                    z.update(player_pos, obstacles, zombies)

            for z in list(zombies):
                if getattr(z, "burn_timer", 0.0) > 0:
                    z.hp -= z.burn_dps * dt
                    z.burn_timer = max(0.0, z.burn_timer - dt)
                    if z.hp <= 0:
                        award_zombie_kill(z)

            update_particles(session.particles, dt)
            if session.effect_flash_timer > 0:
                session.effect_flash_timer = max(0.0, session.effect_flash_timer - dt)

            for b in bullets:
                hits = pygame.sprite.spritecollide(b, zombies, False)
                for z in hits:
                    if z not in b.hit_enemies:
                        b.hit_enemies.add(z)
                        z.hp -= b.damage
                        b.pierce -= 1
                        if stats.lifesteal_percent > 0:
                            stats.hp = min(stats.max_hp, stats.hp + b.damage * stats.lifesteal_percent)

                        if getattr(b, "explosive", False):
                            trigger_explosion(b, z)
                            b.pierce = 0  # grenades explode on first impact, they don't pierce onward

                        if z.hp <= 0:
                            award_zombie_kill(z)
                    if b.pierce <= 0:
                        b.kill()
                        break

            player_rect = pygame.Rect(player_pos[0] - 16, player_pos[1] - 16, 32, 32)
            for z in list(zombies):
                if player_rect.colliderect(z.rect):
                    stats.take_damage(z.attack, attacker=z)
                    if z.hp <= 0:
                        award_zombie_kill(z)

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

        if game_state in ("PLAYING", "TALENT_SELECT", "GAME_OVER", "PAUSED", "WEAPON_INFO"):
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
                    if getattr(z, "burn_timer", 0.0) > 0:
                        glow_r = 34 if getattr(z, "is_boss", False) else 20
                        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (255, 120, 0, 90), (glow_r, glow_r), glow_r)
                        screen.blit(glow_surf, (z.rect.centerx - cam_x - glow_r, z.rect.centery - cam_y - glow_r))
                    screen.blit(z.image, (zx, zy))
                    z_hp_ratio = z.hp / z.max_hp if z.max_hp > 0 else 0
                    bar_w = 46 if getattr(z, "is_boss", False) else 28
                    draw_floating_bar(screen, z.rect.centerx - cam_x, zy - 10, bar_w, 5, z_hp_ratio, (220, 40, 40))
                    if getattr(z, "enraged", False):
                        enrage_surf = font_sm.render(t(settings["lang"], "boss_enraged"), True, (255, 90, 0))
                        screen.blit(enrage_surf, (z.rect.centerx - cam_x - enrage_surf.get_width() // 2, zy - 26))
                elif obj[1] == "obstacle":
                    draw_obstacle(screen, obj[2], cam_x, cam_y, theme)

            boss_for_hud = next((z for z in zombies if getattr(z, "is_boss", False)), None)
            draw_boss_meteors(screen, boss_for_hud, cam_x, cam_y)

            draw_particles(screen, session.particles, cam_x, cam_y)

            weapon_card_rect = hud.draw(screen, stats, session.current_wave, session.wave_timer / 30.0,
                     theme["name"], boss_for_hud, font_sm, font_md, font_lg, settings["lang"])

            if session.boss_warning_timer > 0:
                blink = math.sin(pygame.time.get_ticks() * 0.02) > 0
                if blink:
                    warn_surf = font_xl.render(t(settings["lang"], "boss_incoming"), True, (255, 50, 50))
                    screen.blit(warn_surf, ((SCREEN_WIDTH - warn_surf.get_width()) // 2, 220))

            draw_effect_flash(screen, session.effect_flash_timer, SCREEN_WIDTH, SCREEN_HEIGHT)

            if game_state == "PLAYING":
                draw_joystick(screen, joy_state)
                pause_button_rect = draw_pause_button(screen, SCREEN_WIDTH)

        if game_state == "PAUSED":
            pause_buttons, pause_slider_rect, pause_lang_button_rect = draw_pause_menu(
                screen, SCREEN_WIDTH, SCREEN_HEIGHT, font_lg, font_md, font_sm, settings, FONT_PATH
            )

        if game_state == "WEAPON_INFO":
            weapon_info_close_rect, weapon_info_max_scroll = draw_weapon_info_panel(
                screen, SCREEN_WIDTH, SCREEN_HEIGHT, font_lg, font_md, font_sm, stats, settings["lang"], FONT_PATH,
                scroll_offset=weapon_info_scroll,
            )
            weapon_info_scroll = max(0.0, min(weapon_info_scroll, weapon_info_max_scroll))

        if game_state == "TALENT_SELECT":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            title = font_lg.render(t(settings["lang"], "level_up"), True, (255, 215, 0))
            screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 150))

            if session.pending_talent_choices > 1:
                queue_txt = font_sm.render(
                    t(settings["lang"], "more_pending", n=session.pending_talent_choices - 1),
                    True, (255, 255, 255)
                )
                screen.blit(queue_txt, ((SCREEN_WIDTH - queue_txt.get_width()) // 2, 195))

            card_rects = talent_card_rects(len(talent_options))
            for idx, opt in enumerate(talent_options):
                is_sel = (idx == selected_talent_idx)
                bx, by, card_w, card_h = card_rects[idx]
                pygame.draw.rect(screen, (60, 65, 85) if is_sel else (35, 38, 50), (bx, by, card_w, card_h), border_radius=10)
                pygame.draw.rect(screen, (255, 215, 0) if is_sel else (80, 80, 80), (bx, by, card_w, card_h), width=3 if is_sel else 1, border_radius=10)

                inner_w = card_w - 30  # 15px padding on each side

                opt_name = talent_text(settings["lang"], opt["id"], "name")
                name_font, name_text = fit_text_1line(FONT_PATH, opt_name, inner_w, FONT_SIZE_MD)
                screen.blit(name_font.render(name_text, True, (255, 255, 255)), (bx + 15, by + 20))

                opt_desc = talent_text(settings["lang"], opt["id"], "desc")
                desc_area_h = card_h - 70 - 15  # from the desc's top down to the card's bottom padding
                max_desc_lines = max(1, desc_area_h // (font_sm.get_height() + 4))
                draw_wrapped_text(screen, font_sm, opt_desc, (200, 200, 200), bx + 15, by + 70, inner_w,
                                   line_gap=4, max_lines=max_desc_lines)

        if game_state == "GAME_OVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 0, 0, 210))
            screen.blit(overlay, (0, 0))

            title = font_lg.render(t(settings["lang"], "game_over"), True, (255, 60, 60))
            screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 260))

            stat_line1 = font_md.render(t(settings["lang"], "survived", wave=final_stats_snapshot['wave']), True, (255, 255, 255))
            screen.blit(stat_line1, ((SCREEN_WIDTH - stat_line1.get_width()) // 2, 330))

            stat_line2 = font_md.render(t(settings["lang"], "char_level", level=final_stats_snapshot['level']), True, (255, 255, 255))
            screen.blit(stat_line2, ((SCREEN_WIDTH - stat_line2.get_width()) // 2, 365))

            restart_txt = font_md.render(t(settings["lang"], "restart_prompt"), True, (0, 255, 200))
            screen.blit(restart_txt, ((SCREEN_WIDTH - restart_txt.get_width()) // 2, 430))

        if game_state == "INSTRUCTION":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((15, 15, 25, 230))
            screen.blit(overlay, (0, 0))

            panel_w = min(600, SCREEN_WIDTH - 40)
            panel_h = min(400, SCREEN_HEIGHT - 40)
            panel_x = (SCREEN_WIDTH - panel_w) // 2
            panel_y = (SCREEN_HEIGHT - panel_h) // 2
            pygame.draw.rect(screen, (35, 40, 55), (panel_x, panel_y, panel_w, panel_h), border_radius=12)
            pygame.draw.rect(screen, (255, 215, 0), (panel_x, panel_y, panel_w, panel_h), width=3, border_radius=12)

            title_font, title_text = fit_text_1line(FONT_PATH, t(settings["lang"], "instructions_title"), panel_w - 96, FONT_SIZE_LG)
            screen.blit(title_font.render(title_text, True, (255, 215, 0)), (panel_x + 48, panel_y + 31))

            lines = instruction_lines(settings["lang"])
            text_x = panel_x + 38
            avail_w = panel_x + panel_w - text_x - 20  # panel's right edge minus the text's x minus right padding
            cursor_y = panel_y + 96
            for line in lines:
                used_h = draw_wrapped_text(screen, font_md, f"• {line}", (220, 220, 220), text_x, cursor_y, avail_w,
                                            line_gap=4, max_lines=2)
                cursor_y += used_h + 8

            # Drawn below the panel instead of over the last instruction
            # line (they used to overlap), enlarged, and blinking so it
            # reads clearly as the "press to continue" cue. It's part of
            # the same INSTRUCTION-state block, so it disappears together
            # with the panel the moment the game starts.
            start_font, start_text = fit_text_1line(FONT_PATH, t(settings["lang"], "start_prompt"), SCREEN_WIDTH - 40, FONT_SIZE_LG)
            start_surf = start_font.render(start_text, True, (0, 255, 200))
            blink_alpha = int(160 + 95 * math.sin(pygame.time.get_ticks() / 220))
            start_surf.set_alpha(max(60, blink_alpha))
            start_y = min(panel_y + panel_h + 26, SCREEN_HEIGHT - start_surf.get_height() - 16)
            screen.blit(start_surf, ((SCREEN_WIDTH - start_surf.get_width()) // 2, start_y))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())