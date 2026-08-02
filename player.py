# -*- coding: utf-8 -*-
"""Player stats, armor data, and virtual-joystick input handling."""
import math

from map import SCREEN_HEIGHT
from weapon import Weapon

ARMOR_TIERS = {
    1: {"name": "Wooden Block Armor", "color": (220, 220, 220), "value": 30, "reduction": 0.10},
    2: {"name": "Iron Alloy Block Armor", "color": (180, 220, 255), "value": 60, "reduction": 0.20},
    3: {"name": "Gold Alloy Block Armor", "color": (255, 235, 150), "value": 100, "reduction": 0.35},
    4: {"name": "Vibranium Diamond Block Armor", "color": (230, 180, 255), "value": 150, "reduction": 0.50},
}

# Virtual joystick (bottom-left, mouse/touch both work)
JOY_BASE_POS = (120, SCREEN_HEIGHT - 140)
JOY_BASE_RADIUS = 70
JOY_KNOB_RADIUS = 32
JOY_DEADZONE = 0.15


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

        self.weapon = Weapon("rifle", "Fine")

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
