# -*- coding: utf-8 -*-
"""Weapon type/tier data tables and the Weapon class."""
import random

WEAPON_TYPES = {
    "rifle": {
        "name": "Assault Rifle",
        "base_damage": 5.5,
        "base_fire_rate": 0.5,
        "base_shots": 1,
        "base_pierce": 1,
        "spread_angle": 5,
        "bullet_speed": 12,
        "max_range": 450,
        "explosive": False,
    },
    "shotgun": {
        "name": "Shotgun",
        "base_damage": 10,
        "base_fire_rate": 0.8,
        "base_shots": 5,
        "base_pierce": 2,
        "spread_angle": 5,
        "bullet_speed": 10,
        "max_range": 250,
        "explosive": False,
        # Intrinsic lifesteal, unrelated to the "Armor Airdrop" talent's
        # lifesteal_percent player stat - baseline 2%, +1% per tier level
        # above Fine (see Weapon.lifesteal_percent below).
        "base_lifesteal": 0.02,
    },
    "sniper": {
        "name": "Heavy Sniper",
        "base_damage": 22.5,
        "base_fire_rate": 1.0,
        "base_shots": 1,
        "base_pierce": 4,
        "spread_angle": 0,
        "bullet_speed": 18,
        "max_range": 600,
        "explosive": False,
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
        # On impact this deals splash damage to nearby zombies (in addition
        # to the direct hit) and sets everything caught in the blast on
        # fire for a few seconds.
        "explosive": True,
        "explosion_radius": 90,           # blast radius in pixels ("small area")
        "explosion_damage_ratio": 0.7,    # splash damage, relative to the shot's own damage
        "burn_dps_ratio": 0.18,           # burn damage/sec, relative to the shot's own damage
        "burn_duration": 3.0,             # seconds the burn lasts
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
        # Extra multiplier stacked on top of the tier's dmg_m once the
        # weapon can no longer be tier-upgraded (already at max tier).
        self.bonus_damage_mult = 1.0

    @property
    def display_name(self):
        return f"【{self.tier_name}】{self.type_data['name']}"

    @property
    def damage(self):
        return self.type_data["base_damage"] * self.tier_data["dmg_m"] * self.bonus_damage_mult

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

    @property
    def lifesteal_percent(self):
        """Weapon-intrinsic lifesteal (currently only the Shotgun has any,
        via its "base_lifesteal" entry in WEAPON_TYPES) - a flat % of each
        hit's damage healed back, +1% per tier level above Fine. This is
        separate from PlayerStats.lifesteal_percent (the "Armor Airdrop"
        talent's stat); main.py adds the two together when a shot lands."""
        base = self.type_data.get("base_lifesteal", 0.0)
        if base <= 0:
            return 0.0
        return base + (self.tier_data["lvl"] - 1) * 0.01

    def is_max_tier(self):
        tiers = list(WEAPON_TIERS.keys())
        return self.tier_name == tiers[-1]

    def upgrade_tier(self):
        """Upgrade to the next tier. Returns True if it upgraded, False if
        already at max tier (nothing changes)."""
        tiers = list(WEAPON_TIERS.keys())
        idx = tiers.index(self.tier_name)
        if idx < len(tiers) - 1:
            self.tier_name = tiers[idx + 1]
            self.tier_data = WEAPON_TIERS[self.tier_name]
            return True
        return False

    def upgrade_tier_or_boost_damage(self, boost_ratio=0.15):
        """Used by the "Weapon Breakthrough" talent: upgrade to the next
        tier as usual. If the weapon is already at max tier (so there is
        no higher tier to grant), instead permanently boost its damage by
        boost_ratio (default +15%) so the talent still has an effect.
        Returns "tier" or "damage" depending on which happened."""
        if self.upgrade_tier():
            return "tier"
        self.bonus_damage_mult *= (1 + boost_ratio)
        return "damage"

    def change_type_randomly(self):
        other_types = [t for t in WEAPON_TYPES.keys() if t != self.type_id]
        self.type_id = random.choice(other_types)
        self.type_data = WEAPON_TYPES[self.type_id]