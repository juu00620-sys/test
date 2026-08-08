# -*- coding: utf-8 -*-
"""Player skill data. Unlike the level-up TALENT_POOL (ui.py), these are
awarded exclusively for defeating a boss (see the boss-kill branch of
award_zombie_kill() and the SKILL_SELECT game state in main.py). Each
skill, once acquired, fires automatically every frame on its own cooldown
- independent of and in addition to the player's main weapon - auto-
targeting the nearest zombie within its own range.

SKILL_POOL carries the stable, language-independent identity (an "id" and
a placeholder "max_rank" for future leveling); display name/description
live in i18n.py (see skill_text()) so they can be translated. SKILL_DATA
carries the actual gameplay numbers, read directly by main.py's skill-fire
logic - keeping them here (not duplicated into i18n strings) means the
selection-card stat line and the firing logic can never drift apart.
"""

SKILL_POOL = [
    {"id": "grenade_skill", "max_rank": 1},
    {"id": "dagger_skill", "max_rank": 1},
    {"id": "laser_skill", "max_rank": 1},
    {"id": "tornado_skill", "max_rank": 1},
]

SKILL_DATA = {
    # Thrown at the nearest zombie in range; explodes on impact for splash
    # damage plus a burn-over-time debuff, reusing the same explosive
    # Bullet mechanics as the Grenade Launcher weapon (main.py's existing
    # trigger_explosion()/burn-tick logic handles it with no extra code).
    "grenade_skill": {
        "range": 250,
        "damage": 5,
        "attack_interval": 1.2,
        "bullet_speed": 8,
        "explosion_radius": 70,
        "explosion_damage_ratio": 0.7,
        "burn_dps_ratio": 0.18,
        "burn_duration": 3.0,
    },
    # Fast, short-range instant stab - no projectile, just direct damage
    # to the nearest zombie in range the moment the cooldown is up.
    "dagger_skill": {
        "range": 200,
        "damage": 7,
        "attack_interval": 0.3,
    },
    # Locks onto the nearest zombie in range and channels for `duration`
    # seconds, dealing `damage` every `tick_interval` seconds. If the
    # locked target dies before the channel ends, it immediately retargets
    # the next-nearest zombie in range and keeps ticking until the full
    # duration has elapsed either way. Goes on `cooldown` only after the
    # channel actually ends (by running out of duration or targets).
    "laser_skill": {
        "range": 500,
        "damage": 7,
        "tick_interval": 0.5,
        "duration": 8.0,
        "cooldown": 1.2,
    },
    # Summons a tornado near the player every `cooldown` seconds (replacing
    # any tornado already out). It has no fixed lifetime of its own - it
    # persists until the next resummon - and each frame it:
    #   1. seeks the nearest zombie within `range` and drifts toward it at
    #      `move_speed` (slow, so it reads as "drifting" not chasing),
    #   2. pulls every zombie within `pull_radius` toward its own center,
    #   3. deals damage to every zombie inside `pull_radius` once per
    #      `tick_interval` seconds.
    # The actual per-tick damage is rolled fresh from [damage_min,
    # damage_max] on each resummon (`damage` mirrors that as "min~max" for
    # the stat-card display only - use damage_min/damage_max in the firing
    # logic, not this one), then permanently grows by
    # `damage_growth_per_kill` and the tornado's on-screen/pull size
    # multiplies by `size_growth_per_kill` for every zombie it kills - so a
    # long-lived tornado snowballs into a much bigger, harder-hitting one
    # before the next resummon resets it.
    "tornado_skill": {
        "range": 500,
        "damage": "6~20",
        "cooldown": 10.0,
        "damage_min": 6,
        "damage_max": 20,
        "tick_interval": 0.8,
        "pull_radius": 130,
        "move_speed": 1,
        "damage_growth_per_kill": 1,
        "size_growth_per_kill": 2.0,
    },
}