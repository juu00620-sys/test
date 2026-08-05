# -*- coding: utf-8 -*-
"""Central place for all on-screen text. Add a new language by adding a new
top-level key to STRINGS (copy the "en" block and translate the values) and
appending its code to LANG_ORDER.

IMPORTANT (web/pygbag builds especially): pygame's built-in fallback font
cannot render Chinese glyphs — you will see blank boxes instead of text.
To actually see the Chinese strings you must drop a CJK-capable .ttf file
at assets/fonts/font.ttf (e.g. Noto Sans TC / Noto Sans SC). main.py already
loads that path automatically if present.
"""

LANG_ORDER = ["en", "zh"]
LANG_LABELS = {"en": "EN", "zh": "中文"}

STRINGS = {
    "en": {
        "paused": "⏸ Paused",
        "settings": "Settings",
        "master_volume": "Master Volume: {pct}%",
        "language": "Language",
        "resume": "Resume",
        "restart": "Restart Game",
        "quit_title": "Quit to Title",
        "wave": "WAVE {n}",
        "boss_wave": "⚠️ BOSS WAVE",
        "map": "Map: {name}",
        "boss": "BOSS",
        "level_up": "🎉 Level Up! Choose a Talent",
        "more_pending": "({n} more choices pending)",
        "game_over": "💀 GAME OVER",
        "survived": "Survived to Wave {wave}",
        "char_level": "Character Level Lv.{level}",
        "restart_prompt": "[ Press ENTER / SPACE or Tap Screen to Restart ]",
        "instructions_title": "🎮 2.5D Block Man vs Zombies - Instructions",
        "instructions_lines": [
            "WASD keys / bottom-left virtual joystick:move",
            "Auto-fire: weapon automatically aims and fires at the nearest enemy when off cooldown",
            "A / D keys / on mobile tap the card directly: choose a talent upgrade",
            "Weapon tiers: Fine \u2794 Epic \u2794 Sacred \u2794 Royal \u2794 Imperial \u2794 Divine",
            "Every 5 waves the map theme changes and a BOSS appears",
        ],
        "start_prompt": "[ Press ENTER / SPACE or Tap Screen to Start ]",
        "boss_incoming": "⚠ BOSS INCOMING ⚠",
        "boss_enraged": "ENRAGED!",
        "stat_dmg": "DMG",
        "stat_shots": "Shots",
        "stat_pierce": "Pierce",
        "weapon_info_title": "Weapon & Armor Info",
        "weapon_info_weapon_section": "Weapon",
        "weapon_info_atk": "Attack Power",
        "weapon_info_atk_bonus": "Attack Bonus",
        "weapon_info_fire_rate": "Fire Interval",
        "weapon_info_range": "Range",
        "weapon_info_armor_section": "Armor",
        "weapon_info_no_armor": "No armor tier reached yet",
        "weapon_info_shield": "Shield HP",
        "weapon_info_shield_pct": "Shield Bonus",
        "weapon_info_reflect": "Damage Reflect",
        "weapon_info_lifesteal": "Lifesteal",
        "weapon_info_exp_gain": "EXP Gain",
        "weapon_info_hint": "Press C / ESC or tap X to close",
        "talents": {
            "add_armor": {"name": "Add Shield", "desc": "Roll an armor tier for a permanent HP% shield (higher tier = more shield); stacks, low rolls are ignored"},
            "armor_airdrop": {"name": "Armor Airdrop", "desc": "Roll an armor tier for a random permanent bonus - lifesteal, HP% shield, damage reflect, or exp gain"},
            "hp_up": {"name": "Vitality Boost", "desc": "Max HP +25, and restore 25 HP"},
            "speed_up": {"name": "Light Footwork", "desc": "Move speed +5%"},
            "weapon_tier_up": {"name": "Weapon Breakthrough", "desc": "Upgrade current weapon by one tier! (Boosts damage instead if already max tier)"},
            "switch_weapon": {"name": "Switch Weapon", "desc": "Randomly switch to another weapon type"},
            "atk_speed_up": {"name": "Rapid Fire", "desc": "Fire rate +1~5% (random), stacks"},
            "bullet_count_up": {"name": "Extra Round", "desc": "+1 bullet fired per shot"},
            "ricochet_up": {"name": "Ricochet", "desc": "Bullets bounce to 1 more enemy immediately after each hit"},
        },
    },
    "zh": {
        "paused": "⏸ 已暫停",
        "settings": "設定",
        "master_volume": "主音量：{pct}%",
        "language": "語言",
        "resume": "繼續遊戲",
        "restart": "重新開始",
        "quit_title": "回到主畫面",
        "wave": "第 {n} 波",
        "boss_wave": "⚠️ 首領波次",
        "map": "地圖：{name}",
        "boss": "首領",
        "level_up": "🎉 升級了！選擇一項天賦",
        "more_pending": "（還有 {n} 次選擇待處理）",
        "game_over": "💀 遊戲結束",
        "survived": "存活至第 {wave} 波",
        "char_level": "角色等級 Lv.{level}",
        "restart_prompt": "【 按下 ENTER / SPACE 或點擊畫面以重新開始 】",
        "instructions_title": "🎮 2.5D 方塊人大戰殭屍 - 遊戲說明",
        "instructions_lines": [
            "WASD 鍵／左下角虛擬搖桿移動",
            "自動開火：武器冷卻完畢後會自動瞄準並攻擊最近的敵人",
            "A／D 鍵／手機版直接點擊卡片：選擇天賦升級",
            "武器階級：精良 \u2794 史詩 \u2794 神聖 \u2794 皇家 \u2794 帝國 \u2794 神級",
            "每 5 波地圖主題會變換，並出現首領",
        ],
        "start_prompt": "【 按下 ENTER / SPACE 或點擊畫面開始遊戲 】",
        "boss_incoming": "⚠ 首領即將出現 ⚠",
        "boss_enraged": "狂暴化！",
        "stat_dmg": "傷害",
        "stat_shots": "彈數",
        "stat_pierce": "穿透",
        "weapon_info_title": "武器與護甲資訊",
        "weapon_info_weapon_section": "武器",
        "weapon_info_atk": "攻擊力",
        "weapon_info_atk_bonus": "攻擊加成",
        "weapon_info_fire_rate": "攻擊間隔",
        "weapon_info_range": "射程",
        "weapon_info_armor_section": "護甲",
        "weapon_info_no_armor": "尚未獲得護甲等級",
        "weapon_info_shield": "護盾值",
        "weapon_info_shield_pct": "護盾加成",
        "weapon_info_reflect": "反傷",
        "weapon_info_lifesteal": "吸血",
        "weapon_info_exp_gain": "經驗加成",
        "weapon_info_hint": "按 C／ESC 或點擊 X 關閉",
        "talents": {
            "add_armor": {"name": "加護盾", "desc": "隨機抽一個護甲等級，獲得生命%護盾"},
            "armor_airdrop": {"name": "護甲空投", "desc": "隨機抽一個護甲等級，獲得吸血／生命%護盾／反傷／經驗加成其中一種永久加成"},
            "hp_up": {"name": "活力強化", "desc": "最大生命值 +25，並恢復 25 點生命"},
            "speed_up": {"name": "輕盈步伐", "desc": "移動速度 +5%"},
            "weapon_tier_up": {"name": "武器突破", "desc": "將當前武器升級一階！（若已達最高階則提升傷害）"},
            "switch_weapon": {"name": "切換武器", "desc": "隨機切換為另一種武器"},
            "atk_speed_up": {"name": "急速射擊", "desc": "攻速 +1~5%（隨機），可疊加"},
            "bullet_count_up": {"name": "追加彈藥", "desc": "每次射擊 +1 發子彈"},
            "ricochet_up": {"name": "彈射", "desc": "子彈每次命中敵人後，會立即彈射攻擊 1 名額外敵人"},
        },
    },
}

# map.py's MAP_THEMES entries keep their original English "name" as a
# stable key (so other modules that may compare/store that string keep
# working); this table translates that key for display purposes only.
MAP_THEME_NAMES = {
    "en": {
        "Grassy Plains": "Grassy Plains",
        "Abandoned Warehouse": "Abandoned Warehouse",
        "Desert Ruins": "Desert Ruins",
        "Frozen Tundra": "Frozen Tundra",
    },
    "zh": {
        "Grassy Plains": "青翠平原",
        "Abandoned Warehouse": "廢棄倉庫",
        "Desert Ruins": "沙漠遺跡",
        "Frozen Tundra": "冰凍凍原",
    },
}

# weapon.py's WEAPON_TYPES dict keys (e.g. "rifle") are stable ids.
WEAPON_TYPE_NAMES = {
    "en": {
        "rifle": "Assault Rifle",
        "shotgun": "Shotgun",
        "sniper": "Heavy Sniper",
        "grenade": "Grenade Launcher",
    },
    "zh": {
        "rifle": "突擊步槍",
        "shotgun": "散彈槍",
        "sniper": "重型狙擊槍",
        "grenade": "榴彈發射器",
    },
}

# weapon.py's WEAPON_TIERS dict keys (e.g. "Fine") are used as stable ids
# throughout the game logic (upgrade_tier(), etc.), so they stay in English
# in weapon.py — this table only translates them for display.
WEAPON_TIER_NAMES = {
    "en": {
        "Fine": "Fine",
        "Epic": "Epic",
        "Sacred": "Sacred",
        "Royal": "Royal",
        "Imperial": "Imperial",
        "Divine": "Divine",
    },
    "zh": {
        "Fine": "精良",
        "Epic": "史詩",
        "Sacred": "神聖",
        "Royal": "皇家",
        "Imperial": "帝國",
        "Divine": "神級",
    },
}


def map_theme_name(lang, english_name):
    table = MAP_THEME_NAMES.get(lang, MAP_THEME_NAMES["en"])
    return table.get(english_name, english_name)


def weapon_type_name(lang, type_id):
    table = WEAPON_TYPE_NAMES.get(lang, WEAPON_TYPE_NAMES["en"])
    return table.get(type_id, type_id)


# player.py's ARMOR_TIERS dict keys (1-4, int) are stable ids used by game
# logic (try_add_shield_tier(), etc.), so ARMOR_TIERS itself keeps its
# "name" in English — this table only translates it for display.
ARMOR_TIER_NAMES = {
    "en": {
        1: "Wooden Block Armor",
        2: "Iron Alloy Block Armor",
        3: "Gold Alloy Block Armor",
        4: "Vibranium Diamond Block Armor",
    },
    "zh": {
        1: "木塊護甲",
        2: "鐵合金塊護甲",
        3: "金合金塊護甲",
        4: "振金鑽石塊護甲",
    },
}


def armor_tier_name(lang, tier, fallback=""):
    table = ARMOR_TIER_NAMES.get(lang, ARMOR_TIER_NAMES["en"])
    return table.get(tier, ARMOR_TIER_NAMES["en"].get(tier, fallback))


def weapon_tier_name(lang, tier_name):
    table = WEAPON_TIER_NAMES.get(lang, WEAPON_TIER_NAMES["en"])
    return table.get(tier_name, tier_name)


def weapon_display_name(lang, type_id, tier_name):
    return f"【{weapon_tier_name(lang, tier_name)}】{weapon_type_name(lang, type_id)}"


def t(lang, key, **kwargs):
    """Look up a translated string and .format() it with kwargs.
    Falls back to English, then to the raw key, if missing."""
    table = STRINGS.get(lang, STRINGS["en"])
    s = table.get(key, STRINGS["en"].get(key, key))
    return s.format(**kwargs) if kwargs else s


def instruction_lines(lang):
    table = STRINGS.get(lang, STRINGS["en"])
    return table.get("instructions_lines", STRINGS["en"]["instructions_lines"])


def talent_text(lang, talent_id, field):
    table = STRINGS.get(lang, STRINGS["en"])["talents"]
    entry = table.get(talent_id, STRINGS["en"]["talents"].get(talent_id, {}))
    return entry.get(field, "")


def next_lang(lang):
    idx = LANG_ORDER.index(lang) if lang in LANG_ORDER else 0
    return LANG_ORDER[(idx + 1) % len(LANG_ORDER)]