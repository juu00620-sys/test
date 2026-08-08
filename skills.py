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
]

SKILL_DATA = {
    # Thrown at the nearest zombie in range; explodes on impact for splash
    # damage plus a burn-over-time debuff, reusing the same explosive
    # Bullet mechanics as the Grenade Launcher weapon (main.py's existing
    # trigger_explosion()/burn-tick logic handles it with no extra code).
    "grenade_skill": {
        "range": 150,
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
        "range": 100,
        "damage": 7,
        "attack_interval": 0.5,
    },
    # Locks onto the nearest zombie in range and channels for `duration`
    # seconds, dealing `damage` every `tick_interval` seconds. If the
    # locked target dies before the channel ends, it immediately retargets
    # the next-nearest zombie in range and keeps ticking until the full
    # duration has elapsed either way. Goes on `cooldown` only after the
    # channel actually ends (by running out of duration or targets).
    "laser_skill": {
        "range": 300,
        "damage": 7,
        "tick_interval": 0.5,
        "duration": 8.0,
        "cooldown": 1.2,
    },
}