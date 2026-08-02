# -*- coding: utf-8 -*-
"""Weapon type/tier data tables and the Weapon class."""
import random

WEAPON_TYPES = {
    "rifle": {
        "name": "Assault Rifle",
        "base_damage": 7.5,
        "base_fire_rate": 0.2,
        "base_shots": 1,
        "base_pierce": 1,
        "spread_angle": 5,
        "bullet_speed": 12,
        "max_range": 450,
    },
    "shotgun": {
        "name": "Shotgun",
        "base_damage": 5,
        "base_fire_rate": 0.6,
        "base_shots": 5,
        "base_pierce": 1,
        "spread_angle": 25,
        "bullet_speed": 10,
        "max_range": 250,
    },
    "sniper": {
        "name": "Heavy Sniper",
        "base_damage": 27.5,
        "base_fire_rate": 1.0,
        "base_shots": 1,
        "base_pierce": 4,
        "spread_angle": 0,
        "bullet_speed": 18,
        "max_range": 700,
    },
    "grenade": {
        "name": "Grenade Launcher",
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
    "Fine": {"lvl": 1, "color": (50, 205, 50),   "dmg_m": 1.2, "fr_m": 0.9, "add_p": 0, "add_s": 0},
    "Epic": {"lvl": 2, "color": (147, 112, 219), "dmg_m": 1.5, "fr_m": 0.8, "add_p": 1, "add_s": 0},
    "Sacred": {"lvl": 3, "color": (255, 215, 0),   "dmg_m": 2.0, "fr_m": 0.7, "add_p": 1, "add_s": 1},
    "Royal": {"lvl": 4, "color": (255, 140, 0),   "dmg_m": 2.8, "fr_m": 0.6, "add_p": 2, "add_s": 2},
    "Imperial": {"lvl": 5, "color": (220, 20, 60),   "dmg_m": 4.0, "fr_m": 0.5, "add_p": 3, "add_s": 3},
    "Divine": {"lvl": 6, "color": (0, 255, 255),   "dmg_m": 6.5, "fr_m": 0.35, "add_p": 99, "add_s": 4}
}


class Weapon:
    def __init__(self, type_id="rifle", tier_name="Fine"):
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
