# -*- coding: utf-8 -*-
"""Player stats, armor data, and virtual-joystick input handling."""
import math

from map import SCREEN_WIDTH, SCREEN_HEIGHT
from weapon import Weapon

ARMOR_TIERS = {
    1: {"name": "Wooden Block Armor", "color": (220, 220, 220)},
    2: {"name": "Iron Alloy Block Armor", "color": (180, 220, 255)},
    3: {"name": "Gold Alloy Block Armor", "color": (255, 235, 150)},
    4: {"name": "Vibranium Diamond Block Armor", "color": (230, 180, 255)},
}

# "Add Shield" talent (id "add_armor" in the talent pool): each pick rolls a
# tier 1-4. The pick only takes effect if the rolled tier >= the highest
# tier already reached (a roll below that is ignored so a lucky early pick
# can never be "downgraded" later, but the choice is still spent). Effect
# stacks: each successful pick adds this tier's % of max HP as bonus shield
# capacity on top of whatever shield capacity already exists.
SHIELD_TIER_PERCENT = {1: 0.01, 2: 0.03, 3: 0.05, 4: 0.07}

# "Armor Airdrop" talent (id "armor_airdrop"): each pick rolls a tier 1-4
# independently (no gating against the current tier - it always applies).
# The tier determines which stat gets a permanent bonus, and the bonus
# amount is simply the tier number as a percent (1%/2%/3%/4%), stacking
# each time that tier comes up again. Mutually exclusive with "add_armor"
# in the same talent-select screen (see EXCLUSIVE_GROUPS in ui.py).
AIRDROP_TYPE_BY_TIER = {
    1: "lifesteal",  # Wooden -> lifesteal
    2: "shield",      # Iron Alloy -> HP% shield (shares the same shield pool as add_armor)
    3: "reflect",     # Gold Alloy -> damage reflect
    4: "exp",         # Vibranium Diamond -> exp gain
}

# Virtual joystick (bottom-left, mouse/touch both work). Scaled down on
# narrow (portrait phone) screens - at the original fixed size it would
# eat a big chunk of a phone-width screen and crowd the weapon info card
# in the opposite corner.
_JOY_SCALE = max(0.6, min(1.0, SCREEN_WIDTH / 700))
JOY_BASE_RADIUS = int(70 * _JOY_SCALE)
JOY_KNOB_RADIUS = int(32 * _JOY_SCALE)
JOY_MARGIN_LEFT = 40
JOY_MARGIN_BOTTOM = 60
JOY_BASE_POS = (JOY_MARGIN_LEFT + JOY_BASE_RADIUS, SCREEN_HEIGHT - JOY_MARGIN_BOTTOM - JOY_BASE_RADIUS)
JOY_DEADZONE = 0.15


class PlayerStats:
    def __init__(self):
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 100

        self.max_hp = 100
        self.hp = 100
        self.move_speed = 5.0

        # Highest armor tier reached so far (drives ARMOR_TIERS color for the
        # HUD bar; also used to gate new "add_armor" picks - see
        # try_add_shield_tier).
        self.armor_tier = 0
        self.armor_hp = 0.0
        self.max_armor_hp = 0.0
        # Total % of max_hp currently converted into shield capacity, summed
        # across every successful add_armor / armor_airdrop("shield") pick.
        self.shield_percent = 0.0
        # Reserved for future flat damage-reduction effects; no talent sets
        # this anymore now that armor works purely as an HP% shield.
        self.damage_reduction = 0.0

        # Armor Airdrop bonus stats (stack additively across picks).
        self.reflect_percent = 0.0     # % of an incoming hit reflected back at the attacker
        self.lifesteal_percent = 0.0   # % of damage dealt to zombies healed back to the player
        self.exp_gain_mult = 0.0       # extra exp gained, e.g. 0.02 = +2% exp

        # "+% Attack Speed" talent (id "atk_speed_up"): each pick rolls a
        # random 1-5% and adds it here permanently (stacks additively).
        # Applied by dividing the weapon's fire_rate (cooldown seconds) by
        # (1 + attack_speed_percent) at the point the shot is fired.
        self.attack_speed_percent = 0.0
        # "Bullet Count +1" talent (id "bullet_count_up"): each pick adds a
        # permanent +1 bullet fired per shot, on top of weapon.shot_count.
        self.bonus_shot_count = 0
        # "Ricochet +1" talent (id "ricochet_up"): each pick grants every
        # fired bullet +1 permanent bounce charge - immediately after any
        # hit (regardless of remaining pierce), the bullet retargets the
        # nearest un-hit zombie instead of continuing straight, consuming
        # one charge per bounce.
        self.ricochet_count = 0

        self.weapon = Weapon("rifle", "Fine")

        # Boss-kill reward skills (see skills.py / SKILL_SELECT in
        # main.py) - a set of skill ids the player has unlocked. Each one
        # then fires automatically, independent of and in addition to the
        # main weapon above.
        self.skills = set()

    def _recompute_shield(self):
        """Recomputes max_armor_hp from shield_percent and tops up the
        current shield buffer by however much new capacity was just added,
        without discarding shield HP the player already had banked."""
        new_max = self.max_hp * self.shield_percent
        gained = max(0.0, new_max - self.max_armor_hp)
        self.max_armor_hp = new_max
        self.armor_hp = min(self.max_armor_hp, self.armor_hp + gained)

    def add_max_hp(self, amount):
        """Raises max_hp (e.g. from the hp_up talent) and heals by the same
        amount, then re-syncs shield capacity since it's a % of max_hp."""
        self.max_hp += amount
        self.hp = min(self.hp + amount, self.max_hp)
        if self.shield_percent > 0:
            self._recompute_shield()

    def try_add_shield_tier(self, tier):
        """"Add Shield" talent pick. Only applies if tier >= the highest
        tier already reached; a lower roll is silently ignored (the choice
        is still spent, but nothing changes) so the player is never
        downgraded. Returns True if it applied, False if ignored."""
        if tier < self.armor_tier:
            return False
        self.armor_tier = tier
        self.shield_percent += SHIELD_TIER_PERCENT.get(tier, 0.0)
        self._recompute_shield()
        return True

    def apply_airdrop(self, tier):
        """"Armor Airdrop" talent pick. Always applies regardless of the
        current tier: stacks tier% into whichever stat that tier maps to.
        armor_tier (used only for the HUD color) is bumped up-only and
        never lowered by a weak roll. Returns the (effect_name, value)
        that was applied."""
        effect = AIRDROP_TYPE_BY_TIER.get(tier, "shield")
        value = tier * 0.01
        if effect == "lifesteal":
            self.lifesteal_percent += value
        elif effect == "shield":
            self.shield_percent += value
            self._recompute_shield()
            self.armor_tier = max(self.armor_tier, tier)
        elif effect == "reflect":
            self.reflect_percent += value
        elif effect == "exp":
            self.exp_gain_mult += value
        return effect, value

    def take_damage(self, raw_damage, attacker=None):
        if attacker is not None and self.reflect_percent > 0:
            attacker.hp -= raw_damage * self.reflect_percent

        damage = raw_damage * (1.0 - self.damage_reduction)
        if self.armor_hp > 0:
            if self.armor_hp >= damage:
                self.armor_hp -= damage
                damage = 0
            else:
                damage -= self.armor_hp
                self.armor_hp = 0
                # Note: armor_tier / shield_percent are NOT reset here.
                # The shield is a permanent talent bonus (max_armor_hp), not
                # breakable equipment - only its current buffer drains to 0,
                # and it can be topped back up by a later add_armor /
                # armor_airdrop("shield") pick via _recompute_shield().

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