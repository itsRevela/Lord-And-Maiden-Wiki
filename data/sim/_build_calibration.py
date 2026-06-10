# -*- coding: utf-8 -*-
"""Build calibration.json from the manually transcribed battle log.
Hard rules: strict UTF-8 JSON, never print CJK to console, never guess.
All numbers are copied verbatim from C:\\Users\\revela\\Downloads\\simulatorTestCase.txt
with the source line number recorded in each damage instance.
"""
import io
import json
import os

OUT = r"C:\Users\revela\Documents\Python\Lord-And-Maiden-Wiki\data\sim\calibration.json"

data = {}

# ---------------------------------------------------------------------------
# 0. Source / provenance
# ---------------------------------------------------------------------------
data["source"] = {
    "log_file": r"C:\Users\revela\Downloads\simulatorTestCase.txt",
    "description": (
        "Manually transcribed in-game practice-mode battle log for Lord and Maiden. "
        "Two consecutive battles: Battle 1 = Stalemate (fought first), "
        "Battle 2 = Victory (survivors of B1 carry over). "
        "Player team [A] = Patra / Rhea / Slider.Sp. "
        "Enemy team [E] = Rhea / Aguria.Sp / Satoru. "
        "Both teams field a unit named Rhea; side is disambiguated by [A]/[E] prefix."
    ),
    "carry_over_buff_battle2": {
        "name": "Stalemate-1, All Hero DMG Dealt Increased",
        "magnitude_pct": 33.00,
        "line": 676,
    },
    "notes": [
        "Soldier counts shown as (current / max); max drops as troops take severe wounds/deaths.",
        "DES stat is reproduced verbatim from screenshots (game's own label for a resistance-type stat).",
        "Real DMG Base 32.17+7.2 confirmed complete in later screenshots (log note 3).",
    ],
}

# ---------------------------------------------------------------------------
# 1. Formations
# ---------------------------------------------------------------------------
# Common loadout fields per unit come from the FORMATION block (lines 3-137).
# revealed_attributes captures every parenthetical (number) attributable to a
# unit+stat, tagged by battle/phase and whether buff or debuff.

formations = {
    "enemy": [
        {
            "name": "Rhea",
            "side": "E",
            "commander": True,
            "star": 5,
            "level": 80,
            "advancement": 5,
            "allocated_stat": "DEF",
            "allocated_amount": 229,
            "troop_type": "T6 Cavalry",
            "troop_count": 55000,
            "source_lines": "5-23, 167-170",
            "skills": {
                "main": "Star Shield lv10 (lv5 relic effect)",
                "modular": ["Knight Creed lv10 no awakening", "Field Therapy lv10 no awakening"],
            },
            "skill_stone": "Elf Deer lv5",
            "relic": "Rhea Relic lv5",
            "rune": "Knight Creed lv5",
            "magic_messenger": "Snow Fox (T6)",
        },
        {
            "name": "Aguria.Sp",
            "side": "E",
            "commander": False,
            "star": 5,
            "level": 80,
            "advancement": 5,
            "allocated_stat": "ATK",
            "allocated_amount": 229,
            "troop_type": "T6 Archer",
            "troop_count": 55000,
            "source_lines": "27-45, 167-170",
            "skills": {
                "main": "Swift Thrust lv10 (lv5 relic effect)",
                "modular": ["Evil Fruit lv10 no awakening", "Tactical Burst lv10 no awakening"],
            },
            "skill_stone": "Sacred Feather lv5",
            "relic": "Aguria SP Relic lv5",
            "rune": "Evil Fruit lv5",
            "magic_messenger": "Swift Fox (T6)",
        },
        {
            "name": "Satoru",
            "side": "E",
            "commander": False,
            "star": 4,
            "level": 80,
            "advancement": 5,
            "allocated_stat": "ATK SPD",
            "allocated_amount": 229,
            "troop_type": "T6 Cavalry",
            "troop_count": 55000,
            "source_lines": "49-67, 167-170",
            "skills": {
                "main": "Gray World lv10 (lv5 relic effect)",
                "modular": ["Piety lv10 no awakening", "Cocoon Silence lv10 no awakening"],
            },
            "skill_stone": "Green Tea lv5",
            "relic": "Satoru Relic lv5",
            "rune": "Cocoon Silence lv5",
            "magic_messenger": "Snow Fox (T6)",
        },
    ],
    "player": [
        {
            "name": "Patra",
            "side": "A",
            "commander": True,
            "star": 5,
            "level": 80,
            "advancement": 5,
            "allocated_stat": "ATK",
            "allocated_amount": 229,
            "troop_type": "T6 Archer",
            "troop_count": 55000,
            "source_lines": "74-92, 162-165",
            "skills": {
                "main": "Ghost Bone lv10 (lv5 relic effect)",
                "modular": ["Bone Blade lv10 max awakening", "Tactical Burst lv10 max awakening"],
            },
            "skill_stone": "Magic Spear lv5",
            "relic": "Patra SP Relic lv5",
            "rune": "Bone Blade lv5",
            "magic_messenger": "Snowvine Cat (T6)",
        },
        {
            "name": "Rhea",
            "side": "A",
            "commander": False,
            "star": 5,
            "level": 80,
            "advancement": 5,
            "allocated_stat": "DEF",
            "allocated_amount": 229,
            "troop_type": "T6 Infantry",
            "troop_count": 55000,
            "source_lines": "96-114, 162-165",
            "skills": {
                "main": "Star Shield lv10 (lv5 relic effect)",
                "modular": ["Sky Tear Arrow lv10 max awakening", "Unbounded lv10 max awakening"],
            },
            "skill_stone": "Reactive lv5",
            "relic": "Rhea Relic lv5",
            "rune": "Healing Bell lv5",
            "magic_messenger": "Ice Shark (T6)",
        },
        {
            "name": "Slider.Sp",
            "side": "A",
            "commander": False,
            "star": 5,
            "level": 80,
            "advancement": 5,
            "allocated_stat": "DES",
            "allocated_amount": 229,
            "troop_type": "T6 Siege",
            "troop_count": 55000,
            "source_lines": "118-136, 162-165",
            "skills": {
                "main": "Dark Arrive lv10 (lv5 relic effect)",
                "modular": ["Noise lv10 max awakening", "Piety lv10 max awakening"],
            },
            "skill_stone": "Field Therapy lv5",
            "relic": "Slider SP Relic lv5",
            "rune": "Healing Bell lv5",
            "magic_messenger": "Ice Shark (T6)",
        },
    ],
}
data["formations"] = formations

# ---------------------------------------------------------------------------
# 1b. Revealed in-battle attribute values (the parenthetical numbers).
# Each entry: battle, phase, side, unit, stat, kind (buff/debuff),
# stated_pct (the % string when present), resulting_value (the (number)),
# source, line.
# ---------------------------------------------------------------------------
revealed_attributes = [
    # ---- BATTLE 1, Pre War Preparation Round ----
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Aguria.Sp", "stat": "DEF",
     "kind": "buff", "effect": "DEF Attribute Increased", "stated_pct": "70.83",
     "resulting_value": 408, "source": "Field Therapy", "line": 302},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "DEF",
     "kind": "buff", "effect": "DEF Attribute Increased", "stated_pct": "70.83",
     "resulting_value": 694.4, "source": "Field Therapy", "line": 303},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "ATK",
     "kind": "buff", "effect": "ATK Attribute Increased", "stated_pct": "53.12",
     "resulting_value": 373.5, "source": "Elf Deer", "line": 305},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "DES",
     "kind": "buff", "effect": "DES Attribute Increased", "stated_pct": "53.12",
     "resulting_value": 288.1, "source": "Elf Deer", "line": 307},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "Spd",
     "kind": "buff", "effect": "Spd Attribute Increased", "stated_pct": "53.12",
     "resulting_value": 590.1, "source": "Elf Deer", "line": 308},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Aguria.Sp", "stat": "ATK",
     "kind": "buff", "effect": "ATK Attribute Increased", "stated_pct": "53.12",
     "resulting_value": 959.9, "source": "Elf Deer", "line": 309},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Aguria.Sp", "stat": "DES",
     "kind": "buff", "effect": "DES Attribute Increased", "stated_pct": "53.12",
     "resulting_value": 331.3, "source": "Elf Deer", "line": 311},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Aguria.Sp", "stat": "Spd",
     "kind": "buff", "effect": "Spd Attribute Increased", "stated_pct": "53.12",
     "resulting_value": 326.7, "source": "Elf Deer", "line": 312},
    # Dark Arrive reductions (Slider.Sp)
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "ATK",
     "kind": "debuff", "effect": "ATK Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 252.1, "source": "Dark Arrive", "line": 314},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "DEF",
     "kind": "debuff", "effect": "DEF Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 610.2, "source": "Dark Arrive", "line": 315},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "DES",
     "kind": "debuff", "effect": "DES Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 143.9, "source": "Dark Arrive", "line": 316},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "Spd",
     "kind": "debuff", "effect": "Spd Attribute Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 199.4, "source": "Dark Arrive", "line": 317},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Aguria.Sp", "stat": "ATK",
     "kind": "debuff", "effect": "ATK Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 674.1, "source": "Dark Arrive", "line": 318},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Aguria.Sp", "stat": "DEF",
     "kind": "debuff", "effect": "DEF Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 286.5, "source": "Dark Arrive", "line": 319},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Aguria.Sp", "stat": "DES",
     "kind": "debuff", "effect": "DES Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 232.6, "source": "Dark Arrive", "line": 320},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Aguria.Sp", "stat": "Spd",
     "kind": "debuff", "effect": "Spd Attribute Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 229.4, "source": "Dark Arrive", "line": 321},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "ATK",
     "kind": "debuff", "effect": "ATK Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 262.3, "source": "Dark Arrive", "line": 322},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "DEF",
     "kind": "debuff", "effect": "DEF Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 487.6, "source": "Dark Arrive", "line": 323},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "DES",
     "kind": "debuff", "effect": "DES Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 202.3, "source": "Dark Arrive", "line": 324},
    {"battle": 1, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "Spd",
     "kind": "debuff", "effect": "Spd Attribute Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 414.4, "source": "Dark Arrive", "line": 325},
    # Field Therapy (Slider.Sp) DEF buff on allies
    {"battle": 1, "phase": "prep", "side": "A", "unit": "Rhea", "stat": "DEF",
     "kind": "buff", "effect": "DEF Attribute Increased", "stated_pct": "35.05",
     "resulting_value": 798, "source": "Field Therapy (Slider.Sp)", "line": 338},
    {"battle": 1, "phase": "prep", "side": "A", "unit": "Patra", "stat": "DEF",
     "kind": "buff", "effect": "DEF Attribute Increased", "stated_pct": "35.05",
     "resulting_value": 394, "source": "Field Therapy (Slider.Sp)", "line": 339},

    # ---- BATTLE 1, Round 4 — effect-disappeared lines that reveal (values) ----
    {"battle": 1, "phase": "4", "side": "E", "unit": "Satoru", "stat": "DEF",
     "kind": "buff", "effect": "DEF Attribute Increased (Disappeared)",
     "stated_pct": None, "resulting_value": 437.9, "source": "expiry", "line": 499},
    {"battle": 1, "phase": "4", "side": "E", "unit": "Satoru", "stat": "ATK",
     "kind": "buff", "effect": "ATK Attribute Increased (Disappeared)",
     "stated_pct": None, "resulting_value": 225, "source": "expiry", "line": 500},
    {"battle": 1, "phase": "4", "side": "E", "unit": "Satoru", "stat": "DES",
     "kind": "buff", "effect": "DES Attribute Increased (Disappeared)",
     "stated_pct": None, "resulting_value": 165, "source": "expiry", "line": 501},
    {"battle": 1, "phase": "4", "side": "E", "unit": "Satoru", "stat": "Spd",
     "kind": "buff", "effect": "Spd Attribute Increased (Disappeared)",
     "stated_pct": None, "resulting_value": 377.1, "source": "expiry", "line": 502},
    {"battle": 1, "phase": "4", "side": "E", "unit": "Satoru", "stat": "ATK",
     "kind": "debuff", "effect": "ATK Reduced (Disappeared)",
     "stated_pct": None, "resulting_value": 320.4, "source": "expiry", "line": 503},
    {"battle": 1, "phase": "4", "side": "E", "unit": "Satoru", "stat": "DEF",
     "kind": "debuff", "effect": "DEF Reduced (Disappeared)",
     "stated_pct": None, "resulting_value": 623.6, "source": "expiry", "line": 504},
    {"battle": 1, "phase": "4", "side": "E", "unit": "Satoru", "stat": "DES",
     "kind": "debuff", "effect": "DES Reduced (Disappeared)",
     "stated_pct": None, "resulting_value": 235, "source": "expiry", "line": 505},
    {"battle": 1, "phase": "4", "side": "E", "unit": "Satoru", "stat": "Spd",
     "kind": "debuff", "effect": "Spd Attribute Reduced (Disappeared)",
     "stated_pct": None, "resulting_value": 537, "source": "expiry", "line": 506},
    {"battle": 1, "phase": "4", "side": "A", "unit": "Rhea", "stat": "DEF",
     "kind": "buff", "effect": "DEF Attribute Increased (Disappeared)",
     "stated_pct": None, "resulting_value": 763, "source": "expiry", "line": 515},
    {"battle": 1, "phase": "4", "side": "A", "unit": "Patra", "stat": "DEF",
     "kind": "buff", "effect": "DEF Attribute Increased (Disappeared)",
     "stated_pct": None, "resulting_value": 359, "source": "expiry", "line": 522},
    {"battle": 1, "phase": "4", "side": "E", "unit": "Rhea", "stat": "ATK",
     "kind": "debuff", "effect": "ATK Reduced (Disappeared)",
     "stated_pct": None, "resulting_value": 359, "source": "expiry", "line": 538},
    {"battle": 1, "phase": "4", "side": "E", "unit": "Rhea", "stat": "DEF",
     "kind": "debuff", "effect": "DEF Reduced (Disappeared)",
     "stated_pct": None, "resulting_value": 869, "source": "expiry", "line": 539},
    {"battle": 1, "phase": "4", "side": "E", "unit": "Rhea", "stat": "DES",
     "kind": "debuff", "effect": "DES Reduced (Disappeared)",
     "stated_pct": None, "resulting_value": 205, "source": "expiry", "line": 540},
    {"battle": 1, "phase": "4", "side": "E", "unit": "Rhea", "stat": "Spd",
     "kind": "debuff", "effect": "Spd Attribute Reduced (Disappeared)",
     "stated_pct": None, "resulting_value": 284, "source": "expiry", "line": 541},

    # ---- BATTLE 2, Pre War Preparation Round ----
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "DEF",
     "kind": "buff", "effect": "DEF Attribute Increased", "stated_pct": "70.83",
     "resulting_value": 939.8, "source": "Field Therapy", "line": 729},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "DEF",
     "kind": "buff", "effect": "DEF Attribute Increased", "stated_pct": "75.68",
     "resulting_value": 699.2, "source": "Field Therapy", "line": 730},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "ATK",
     "kind": "buff", "effect": "ATK Attribute Increased", "stated_pct": "56.76",
     "resulting_value": 415.7, "source": "Elf Deer", "line": 732},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "DES",
     "kind": "buff", "effect": "DES Attribute Increased", "stated_pct": "56.76",
     "resulting_value": 261.7, "source": "Elf Deer", "line": 734},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "Spd",
     "kind": "buff", "effect": "Spd Attribute Increased", "stated_pct": "56.76",
     "resulting_value": 340.7, "source": "Elf Deer", "line": 735},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "ATK",
     "kind": "buff", "effect": "ATK Attribute Increased", "stated_pct": "56.76",
     "resulting_value": 377.1, "source": "Elf Deer", "line": 736},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "DES",
     "kind": "buff", "effect": "DES Attribute Increased", "stated_pct": "56.76",
     "resulting_value": 291.7, "source": "Elf Deer", "line": 738},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "Spd",
     "kind": "buff", "effect": "Spd Attribute Increased", "stated_pct": "56.76",
     "resulting_value": 593.7, "source": "Elf Deer", "line": 739},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "ATK",
     "kind": "debuff", "effect": "ATK Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 291.9, "source": "Dark Arrive", "line": 741},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "DEF",
     "kind": "debuff", "effect": "DEF Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 660, "source": "Dark Arrive", "line": 742},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "DES",
     "kind": "debuff", "effect": "DES Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 183.8, "source": "Dark Arrive", "line": 743},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Rhea", "stat": "Spd",
     "kind": "debuff", "effect": "Spd Attribute Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 239.3, "source": "Dark Arrive", "line": 744},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "ATK",
     "kind": "debuff", "effect": "ATK Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 264.8, "source": "Dark Arrive", "line": 745},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "DEF",
     "kind": "debuff", "effect": "DEF Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 491.1, "source": "Dark Arrive", "line": 746},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "DES",
     "kind": "debuff", "effect": "DES Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 204.9, "source": "Dark Arrive", "line": 747},
    {"battle": 2, "phase": "prep", "side": "E", "unit": "Satoru", "stat": "Spd",
     "kind": "debuff", "effect": "Spd Attribute Reduced", "stated_pct": "22.57%+7.20%",
     "resulting_value": 416.9, "source": "Dark Arrive", "line": 748},
    {"battle": 2, "phase": "prep", "side": "A", "unit": "Rhea", "stat": "DEF",
     "kind": "buff", "effect": "DEF Attribute Increased", "stated_pct": "35.05",
     "resulting_value": 798, "source": "Field Therapy (Slider.Sp)", "line": 760},
    {"battle": 2, "phase": "prep", "side": "A", "unit": "Patra", "stat": "DEF",
     "kind": "buff", "effect": "DEF Attribute Increased", "stated_pct": "35.05",
     "resulting_value": 394, "source": "Field Therapy (Slider.Sp)", "line": 761},
]
data["revealed_attributes"] = revealed_attributes

# ---------------------------------------------------------------------------
# 2. Damage instances — EVERY "Loss N Soldier" + Restore event.
# ---------------------------------------------------------------------------
def di(battle, rnd, line, actor, actor_side, action, target, target_side,
       loss, cur, mx, notes=""):
    return {
        "battle": battle, "round": rnd, "line": line,
        "actor": actor, "actor_side": actor_side, "action": action,
        "target": target, "target_side": target_side,
        "loss": loss, "target_current_after": cur, "target_max_after": mx,
        "notes": notes,
    }

damage_instances = [
    # ===================== BATTLE 1 =====================
    # ---- Round 1 ----
    di(1, "1", 348, "Slider.Sp", "A", "Field Therapy", "Rhea", "A", 0, 55000, 55000,
       "heal/restore (Self-Heal via Field Therapy); 0 restored"),
    di(1, "1", 354, "Rhea", "A", "normal", "Rhea", "E", 482, 54518, 54904,
       "Satoru in Aid state; A[Rhea] Normal ATK redirected to E[Rhea]"),
    di(1, "1", 355, "Slider.Sp", "A", "Field Therapy", "Patra", "A", 0, 55000, 55000,
       "heal/restore; 0 restored"),
    di(1, "1", 359, "Patra", "A", "normal", "Rhea", "E", 1459, 53059, 54613, ""),
    di(1, "1", 364, "Slider.Sp", "A", "normal", "Rhea", "E", 547, 52512, 54504,
       "Aguria.Sp in Aid state; A[Slider.Sp] Normal ATK redirected to E[Rhea]"),
    di(1, "1", 370, "Aguria.Sp", "E", "Swift Thrust", "Patra", "A", 6374, 48626, 53726, ""),
    di(1, "1", 374, "Aguria.Sp", "E", "Swift Thrust", "Patra", "A", 6245, 42381, 52477,
       "second Swift Thrust via Tactical Burst proc"),
    di(1, "1", 377, "Aguria.Sp", "E", "Evil Fruit", "Patra", "A", 6642, 35739, 51149, ""),
    di(1, "1", 381, "Aguria.Sp", "E", "Evil Fruit", "Patra", "A", 6710, 29029, 49807,
       "second Evil Fruit via Tactical Burst proc"),
    di(1, "1", 385, "Aguria.Sp", "E", "normal", "Rhea", "A", 60, 54940, 54988,
       "Patra in Aid state; E[Aguria.Sp] Normal ATK redirected to A[Rhea]"),
    di(1, "1", 387, "Rhea", "A", "counter", "Aguria.Sp", "E", 4456, 50544, 54109,
       "A[Rhea] Trigger [Counterattack] vs E[Aguria.Sp]"),
    di(1, "1", 392, "Rhea", "E", "normal", "Rhea", "A", 38, 54902, 54981,
       "Slider.Sp in Aid state; E[Rhea] Normal ATK redirected to A[Rhea]"),
    di(1, "1", 394, "Rhea", "A", "counter", "Rhea", "E", 396, 52116, 54425,
       "A[Rhea] Trigger [Counterattack] vs E[Rhea]"),

    # ---- Round 2 ----
    di(1, "2", 404, "Slider.Sp", "A", "Field Therapy", "Rhea", "A", 72, 54974, 54974,
       "heal/restore; +72 (negative loss = restore)"),
    di(1, "2", 409, "Rhea", "A", "normal", "Rhea", "E", 486, 51630, 54098,
       "Aguria.Sp in Aid state; A[Rhea] Normal ATK redirected to E[Rhea]"),
    di(1, "2", 418, "Patra", "A", "Ghost Bone", "Aguria.Sp", "E", 15984, 34560, 50557,
       "Ghost Bone main hit"),
    di(1, "2", 419, "Patra", "A", "assault_pursuit", "Aguria.Sp", "E", 671, 33889, 50423, ""),
    di(1, "2", 420, "Patra", "A", "Ghost Bone", "Rhea", "E", 1917, 49713, 53715,
       "Ghost Bone hit on second target"),
    di(1, "2", 421, "Patra", "A", "assault_pursuit", "Rhea", "E", 671, 49042, 53581, ""),
    di(1, "2", 423, "Patra", "A", "Magic Spear", "Aguria.Sp", "E", 19116, 14773, 46600, ""),
    di(1, "2", 424, "Patra", "A", "assault_pursuit", "Aguria.Sp", "E", 671, 14102, 46466, ""),
    di(1, "2", 428, "Patra", "A", "Magic Spear", "Rhea", "E", 2139, 46903, 53154,
       "second Magic Spear via Tactical Burst proc"),
    di(1, "2", 429, "Patra", "A", "assault_pursuit", "Rhea", "E", 671, 46232, 53020, ""),
    di(1, "2", 434, "Slider.Sp", "A", "normal", "Rhea", "E", 505, 45727, 52919,
       "Satoru in Aid state; A[Slider.Sp] Normal ATK redirected to E[Rhea]"),

    # ---- Round 3 ----
    di(1, "3", 451, "Slider.Sp", "A", "Field Therapy", "Rhea", "A", 0, 54974, 54974,
       "heal/restore; 0 restored"),
    di(1, "3", 455, "Rhea", "A", "normal", "Rhea", "E", 453, 45274, 52110, ""),
    di(1, "3", 459, "Slider.Sp", "A", "Field Therapy", "Patra", "A", 4962, 33991, 45860,
       "heal/restore; +4962 restored (negative loss)"),
    di(1, "3", 463, "Patra", "A", "Ghost Bone", "Satoru", "E", 6973, 48027, 53606, ""),
    di(1, "3", 464, "Patra", "A", "assault_pursuit", "Satoru", "E", 726, 47301, 53461, ""),
    di(1, "3", 465, "Patra", "A", "Ghost Bone", "Rhea", "E", 1916, 43358, 51727, ""),
    di(1, "3", 466, "Patra", "A", "assault_pursuit", "Rhea", "E", 726, 42632, 51582, ""),
    di(1, "3", 468, "Patra", "A", "Bone Blade", "Rhea", "E", 2790, 39842, 51024, ""),
    di(1, "3", 469, "Patra", "A", "assault_pursuit", "Rhea", "E", 726, 39116, 50879, ""),
    di(1, "3", 470, "Patra", "A", "Bone Blade", "Aguria.Sp", "E", 14102, 0, 40410,
       "Aguria.Sp defeated this hit (Bone Blade second target)"),
    di(1, "3", 474, "Patra", "A", "Magic Spear", "Rhea", "E", 2410, 36706, 50397, ""),
    di(1, "3", 475, "Patra", "A", "assault_pursuit", "Rhea", "E", 726, 35980, 50252, ""),
    di(1, "3", 481, "Slider.Sp", "A", "normal", "Rhea", "E", 516, 35464, 50149, ""),
    di(1, "3", 488, "Rhea", "E", "normal", "Rhea", "A", 30, 54944, 54968,
       "E[Rhea] Normal ATK on A[Rhea]"),
    di(1, "3", 490, "Rhea", "A", "counter", "Rhea", "E", 404, 35060, 50069,
       "A[Rhea] Trigger [Counterattack] vs E[Rhea]"),

    # ---- Round 4 ----
    di(1, "4", 517, "Rhea", "A", "normal", "Satoru", "E", 1438, 45863, 52558, ""),
    di(1, "4", 528, "Patra", "A", "normal", "Satoru", "E", 3347, 42516, 51889, ""),
    di(1, "4", 534, "Slider.Sp", "A", "normal", "Rhea", "E", 531, 34529, 48463, ""),
    di(1, "4", 551, "Rhea", "E", "normal", "Rhea", "A", 401, 54543, 54886,
       "E[Rhea] Normal ATK; A[Rhea] DMG Taken Reduced 59.20% (Reactive Block)"),
    di(1, "4", 553, "Rhea", "A", "counter", "Rhea", "E", 405, 34124, 48382,
       "A[Rhea] Trigger [Counterattack] vs E[Rhea]"),

    # ---- Round 5 ----
    di(1, "5", 562, "Rhea", "A", "normal", "Rhea", "E", 523, 33601, 46853,
       "A[Rhea] In Provoked State"),
    di(1, "5", 564, "Rhea", "E", "normal", "Slider.Sp", "A", 2954, 52046, 54410, ""),
    di(1, "5", 568, "Patra", "A", "normal", "Satoru", "E", 3700, 38816, 50212, ""),
    di(1, "5", 573, "Slider.Sp", "A", "normal", "Rhea", "E", 569, 33032, 46740,
       "A[Slider.Sp] In Provoked State"),

    # ---- Round 6 ----
    di(1, "6", 583, "Rhea", "A", "normal", "Rhea", "E", 498, 32534, 45271,
       "A[Rhea] In Provoked State"),
    di(1, "6", 587, "Rhea", "E", "normal", "Rhea", "A", 753, 53790, 54672, ""),
    di(1, "6", 589, "Rhea", "A", "counter", "Rhea", "E", 976, 31558, 45076,
       "A[Rhea] Trigger [Counterattack] vs E[Rhea]"),
    di(1, "6", 593, "Patra", "A", "normal", "Rhea", "E", 2633, 28925, 44550, ""),
    di(1, "6", 598, "Slider.Sp", "A", "normal", "Rhea", "E", 1236, 27689, 44303,
       "A[Slider.Sp] In Provoked State"),

    # ---- Round 7 ----
    di(1, "7", 612, "Rhea", "A", "normal", "Satoru", "E", 1508, 37308, 47747, ""),
    di(1, "7", 618, "Rhea", "E", "normal", "Rhea", "A", 911, 52879, 54402,
       "E[Rhea] Normal ATK; A[Rhea] Taunts active"),
    di(1, "7", 620, "Rhea", "A", "counter", "Rhea", "E", 403, 27286, 42562,
       "A[Rhea] Trigger [Counterattack] vs E[Rhea]"),
    di(1, "7", 625, "Patra", "A", "normal", "Rhea", "E", 1213, 26073, 42320,
       "A[Patra] In Provoked State"),
    di(1, "7", 630, "Slider.Sp", "A", "normal", "Satoru", "E", 1604, 35704, 47427, ""),

    # ---- Round 8 ----
    di(1, "8", 644, "Rhea", "A", "normal", "Rhea", "E", 515, 25558, 40593,
       "A[Rhea] In Provoked State"),
    di(1, "8", 652, "Rhea", "E", "normal", "Rhea", "A", 352, 52527, 54180,
       "E[Rhea] Normal ATK; A[Rhea] DMG Taken Reduced 59.20% (Reactive Block)"),
    di(1, "8", 654, "Rhea", "A", "counter", "Rhea", "E", 427, 25131, 40508,
       "A[Rhea] Trigger [Counterattack] vs E[Rhea]"),
    di(1, "8", 658, "Patra", "A", "Ghost Bone", "Rhea", "E", 1530, 23601, 40202, ""),
    di(1, "8", 659, "Patra", "A", "assault_pursuit", "Rhea", "E", 726, 22875, 40057, ""),
    di(1, "8", 660, "Patra", "A", "Ghost Bone", "Satoru", "E", 4626, 31078, 45330,
       "Ghost Bone second target"),
    di(1, "8", 661, "Patra", "A", "assault_pursuit", "Satoru", "E", 726, 30352, 45185, ""),
    di(1, "8", 667, "Slider.Sp", "A", "normal", "Rhea", "E", 524, 22351, 39953,
       "A[Slider.Sp] In Provoked State; final B1 enemy Rhea count 22351"),

    # ===================== BATTLE 2 =====================
    # ---- Round 1 ----
    di(2, "1", 770, "Satoru", "E", "normal", "Rhea", "A", 42, 52485, 52519,
       "E[Satoru] Normal ATK on A[Rhea]"),
    di(2, "1", 772, "Rhea", "A", "counter", "Satoru", "E", 2726, 27626, 29807,
       "A[Rhea] Trigger [Counterattack] vs E[Satoru]"),
    di(2, "1", 773, "Slider.Sp", "A", "Field Therapy", "Rhea", "A", 34, 52519, 52519,
       "heal/restore; +34 restored"),
    di(2, "1", 776, "Rhea", "A", "normal", "Rhea", "E", 556, 21795, 22240,
       "Satoru in Aid state; A[Rhea] Normal ATK redirected to E[Rhea]"),
    di(2, "1", 777, "Slider.Sp", "A", "Field Therapy", "Patra", "A", 0, 33991, 33991,
       "heal/restore; 0 restored"),
    di(2, "1", 781, "Patra", "A", "Ghost Bone", "Rhea", "E", 2599, 19196, 21721, ""),
    di(2, "1", 782, "Patra", "A", "assault_pursuit", "Rhea", "E", 726, 18470, 21576, ""),
    di(2, "1", 783, "Patra", "A", "Ghost Bone", "Satoru", "E", 15346, 12280, 26738,
       "Ghost Bone second target"),
    di(2, "1", 784, "Patra", "A", "assault_pursuit", "Satoru", "E", 726, 11554, 26593, ""),
    di(2, "1", 789, "Patra", "A", "Ghost Bone", "Rhea", "E", 2549, 15921, 21067,
       "second Ghost Bone via Tactical Burst proc"),
    di(2, "1", 790, "Patra", "A", "assault_pursuit", "Rhea", "E", 726, 15195, 20922, ""),
    di(2, "1", 791, "Patra", "A", "Ghost Bone", "Satoru", "E", 11554, 0, 24283,
       "Satoru defeated this hit (Ghost Bone second target)"),
    di(2, "1", 794, "Patra", "A", "Bone Blade", "Rhea", "E", 3257, 11938, 20271, ""),
    di(2, "1", 795, "Patra", "A", "assault_pursuit", "Rhea", "E", 726, 11212, 20126, ""),
    di(2, "1", 798, "Patra", "A", "Magic Spear", "Rhea", "E", 3049, 8163, 19517, ""),
    di(2, "1", 799, "Patra", "A", "assault_pursuit", "Rhea", "E", 726, 7437, 19372, ""),
    di(2, "1", 803, "Slider.Sp", "A", "normal", "Rhea", "E", 622, 6815, 19248, ""),

    # ---- Round 2 ----
    di(2, "2", 814, "Slider.Sp", "A", "Field Therapy", "Rhea", "A", 0, 52519, 52519,
       "heal/restore; 0 restored"),
    di(2, "2", 816, "Rhea", "A", "normal", "Rhea", "E", 579, 6236, 17890, ""),
    di(2, "2", 819, "Slider.Sp", "A", "Field Therapy", "Patra", "A", 0, 33991, 33991,
       "heal/restore; 0 restored"),
    di(2, "2", 825, "Patra", "A", "Ghost Bone", "Rhea", "E", 2351, 3885, 17420, ""),
    di(2, "2", 826, "Patra", "A", "assault_pursuit", "Rhea", "E", 726, 3159, 17275, ""),
    di(2, "2", 831, "Patra", "A", "Ghost Bone", "Rhea", "E", 2574, 585, 16761,
       "second Ghost Bone via Tactical Burst proc"),
    di(2, "2", 832, "Patra", "A", "assault_pursuit", "Rhea", "E", 585, 0, 16644,
       "Rhea defeated; assault pursuit overkill 585 (vs usual 726)"),
]
data["damage_instances"] = damage_instances

# ---------------------------------------------------------------------------
# 3. Buff states — per battle, per unit, active modifiers + magnitudes.
# ---------------------------------------------------------------------------
buff_states = {
    "battle_1": {
        "A": {
            "Patra": [
                {"effect": "Tactical Burst", "magnitude": "Effective Probability 100.00%", "kind": "passive", "line": 267},
                {"effect": "Silence(Prepared)", "magnitude": "trigger 40.00%+12.00%", "kind": "debuff_on_self", "line": 279},
                {"effect": "Assist", "magnitude": "applied", "kind": "buff", "line": 286},
                {"effect": "Tactical Skill DMG Dealt Increased", "magnitude": "24.80%+9.00%", "kind": "buff", "source": "Sky Tear Arrow", "line": 289},
                {"effect": "Purification", "magnitude": "applied", "kind": "buff", "line": 334},
                {"effect": "Self-Heal", "magnitude": "Healing Coefficient 1.05+0.28", "kind": "buff", "source": "Field Therapy", "line": 337},
                {"effect": "DEF Attribute Increased", "magnitude": "35.05 (394)", "kind": "buff", "source": "Field Therapy", "line": 339},
                {"effect": "Heal Ban", "magnitude": "applied (from Aguria.Sp Swift Thrust)", "kind": "debuff", "line": 371},
                {"effect": "Stun", "magnitude": "applied (from Evil Fruit)", "kind": "debuff", "line": 378},
            ],
            "Rhea": [
                {"effect": "Reactive Block", "magnitude": "Effective Probability 100.00%; on trigger DMG Taken Reduced 59.20%", "kind": "passive", "line": 268},
                {"effect": "Counterattack", "magnitude": "DMG Coefficient 0.70+0.14", "kind": "passive", "line": 269},
                {"effect": "Silence(Prepared)", "magnitude": "trigger 40.00%+12.00%", "kind": "debuff_on_self", "line": 279},
                {"effect": "DMG Taken Reduced", "magnitude": "82.22%+30.00%", "kind": "buff", "source": "Star Shield", "line": 285},
                {"effect": "Purification", "magnitude": "applied", "kind": "buff", "line": 333},
                {"effect": "Self-Heal", "magnitude": "Healing Coefficient 1.05+0.28", "kind": "buff", "source": "Field Therapy", "line": 336},
                {"effect": "DEF Attribute Increased", "magnitude": "35.05 (798)", "kind": "buff", "source": "Field Therapy", "line": 338},
                {"effect": "Taunts", "magnitude": "applied (provoked, from enemy Knight Creed)", "kind": "debuff", "line": 546},
            ],
            "Slider.Sp": [
                {"effect": "Silence(Prepared)", "magnitude": "trigger 40.00%+12.00%", "kind": "debuff_on_self", "line": 280},
                {"effect": "Assist", "magnitude": "applied", "kind": "buff", "line": 287},
                {"effect": "Tactical Skill DMG Dealt Increased", "magnitude": "24.80%+9.00%", "kind": "buff", "source": "Sky Tear Arrow", "line": 290},
                {"effect": "Taunts", "magnitude": "applied (provoked, from enemy Knight Creed)", "kind": "debuff", "line": 547},
            ],
        },
        "E": {
            "Rhea": [
                {"effect": "DMG Taken Reduced", "magnitude": "90.17%+30.00%", "kind": "buff", "source": "Star Shield", "line": 296},
                {"effect": "Silence(Prepared)", "magnitude": "trigger 60.00%+12.00%", "kind": "debuff_on_self", "line": 292},
                {"effect": "ATK Reduced", "magnitude": "22.57%+7.20% (252.1)", "kind": "debuff", "source": "Dark Arrive", "line": 314},
                {"effect": "DEF Reduced", "magnitude": "22.57%+7.20% (610.2)", "kind": "debuff", "source": "Dark Arrive", "line": 315},
                {"effect": "DES Reduced", "magnitude": "22.57%+7.20% (143.9)", "kind": "debuff", "source": "Dark Arrive", "line": 316},
                {"effect": "Spd Attribute Reduced", "magnitude": "22.57%+7.20% (199.4)", "kind": "debuff", "source": "Dark Arrive", "line": 317},
                {"effect": "Heal Ban", "magnitude": "applied", "kind": "debuff", "source": "Dark Arrive", "line": 326},
                {"effect": "DMG Taken Increased", "magnitude": "42.89%+9.00%", "kind": "debuff", "source": "Noise", "line": 330},
                {"effect": "DMG Dealt Increased", "magnitude": "26.91%", "kind": "buff", "source": "Green Tea (Satoru)", "line": 509},
                {"effect": "DMG Taken Reduced", "magnitude": "54.82%", "kind": "buff", "source": "Knight Creed", "line": 545},
            ],
            "Aguria.Sp": [
                {"effect": "Tactical Burst", "magnitude": "Effective Probability 100.00%", "kind": "passive", "line": 270},
                {"effect": "Sacred Feather", "magnitude": "Effective Probability 100.00%; trigger 41.50%", "kind": "passive", "line": 271},
                {"effect": "Silence(Prepared)", "magnitude": "trigger 60.00%+12.00%", "kind": "debuff_on_self", "line": 293},
                {"effect": "Assist", "magnitude": "applied", "kind": "buff", "line": 297},
                {"effect": "Self-Heal", "magnitude": "Healing Coefficient 1.4", "kind": "buff", "source": "Field Therapy", "line": 300},
                {"effect": "DEF Attribute Increased", "magnitude": "70.83 (408)", "kind": "buff", "source": "Field Therapy", "line": 302},
                {"effect": "ATK Attribute Increased", "magnitude": "53.12 (959.9)", "kind": "buff", "source": "Elf Deer", "line": 309},
                {"effect": "DES Attribute Increased", "magnitude": "53.12 (331.3)", "kind": "buff", "source": "Elf Deer", "line": 311},
                {"effect": "Spd Attribute Increased", "magnitude": "53.12 (326.7)", "kind": "buff", "source": "Elf Deer", "line": 312},
                {"effect": "ATK Reduced", "magnitude": "22.57%+7.20% (674.1)", "kind": "debuff", "source": "Dark Arrive", "line": 318},
                {"effect": "DEF Reduced", "magnitude": "22.57%+7.20% (286.5)", "kind": "debuff", "source": "Dark Arrive", "line": 319},
                {"effect": "DES Reduced", "magnitude": "22.57%+7.20% (232.6)", "kind": "debuff", "source": "Dark Arrive", "line": 320},
                {"effect": "Spd Attribute Reduced", "magnitude": "22.57%+7.20% (229.4)", "kind": "debuff", "source": "Dark Arrive", "line": 321},
                {"effect": "Heal Ban", "magnitude": "applied", "kind": "debuff", "source": "Dark Arrive", "line": 327},
                {"effect": "DMG Taken Increased", "magnitude": "42.89%+9.00%", "kind": "debuff", "source": "Noise", "line": 331},
            ],
            "Satoru": [
                {"effect": "Disarm", "magnitude": "applied (self, from Gray World)", "kind": "self_effect", "line": "276 (cast)"},
                {"effect": "Silence(Prepared)", "magnitude": "trigger 60.00%+12.00%", "kind": "debuff_on_self", "line": 294},
                {"effect": "Assist", "magnitude": "applied", "kind": "buff", "line": 298},
                {"effect": "Self-Heal", "magnitude": "Healing Coefficient 1.4", "kind": "buff", "source": "Field Therapy", "line": 301},
                {"effect": "DEF Attribute Increased", "magnitude": "70.83 (694.4)", "kind": "buff", "source": "Field Therapy", "line": 303},
                {"effect": "ATK Attribute Increased", "magnitude": "53.12 (373.5)", "kind": "buff", "source": "Elf Deer", "line": 305},
                {"effect": "DES Attribute Increased", "magnitude": "53.12 (288.1)", "kind": "buff", "source": "Elf Deer", "line": 307},
                {"effect": "Spd Attribute Increased", "magnitude": "53.12 (590.1)", "kind": "buff", "source": "Elf Deer", "line": 308},
                {"effect": "ATK Reduced", "magnitude": "22.57%+7.20% (262.3)", "kind": "debuff", "source": "Dark Arrive", "line": 322},
                {"effect": "DEF Reduced", "magnitude": "22.57%+7.20% (487.6)", "kind": "debuff", "source": "Dark Arrive", "line": 323},
                {"effect": "DES Reduced", "magnitude": "22.57%+7.20% (202.3)", "kind": "debuff", "source": "Dark Arrive", "line": 324},
                {"effect": "Spd Attribute Reduced", "magnitude": "22.57%+7.20% (414.4)", "kind": "debuff", "source": "Dark Arrive", "line": 325},
                {"effect": "Heal Ban", "magnitude": "applied", "kind": "debuff", "source": "Dark Arrive", "line": 328},
                {"effect": "DMG Dealt Increased", "magnitude": "26.91%", "kind": "buff", "source": "Green Tea", "line": 510},
            ],
        },
    },
    "battle_2": {
        "carry_over": {"effect": "All Hero DMG Dealt Increased", "magnitude": "33.00%", "source": "Stalemate-1", "line": 676},
        "A": {
            "Patra": [
                {"effect": "Tactical Burst", "magnitude": "Effective Probability 100.00%", "kind": "passive", "line": 698},
                {"effect": "Silence(Prepared)", "magnitude": "applied", "kind": "debuff_on_self", "line": 707},
                {"effect": "Assist", "magnitude": "applied", "kind": "buff", "line": 715},
                {"effect": "Tactical Skill DMG Dealt Increased", "magnitude": "24.80%+9.00%", "kind": "buff", "source": "Sky Tear Arrow", "line": 719},
                {"effect": "Purification", "magnitude": "applied", "kind": "buff", "line": 755},
                {"effect": "Self-Heal", "magnitude": "Healing Coefficient 1.05+0.28", "kind": "buff", "source": "Field Therapy", "line": 759},
                {"effect": "DEF Attribute Increased", "magnitude": "35.05 (394)", "kind": "buff", "source": "Field Therapy", "line": 761},
            ],
            "Rhea": [
                {"effect": "Reactive Block", "magnitude": "Effective Probability 100.00%", "kind": "passive", "line": 699},
                {"effect": "Counterattack", "magnitude": "DMG Coefficient 0.70+0.14", "kind": "passive", "line": 700},
                {"effect": "DMG Taken Reduced", "magnitude": "82.22%+30.00%", "kind": "buff", "source": "Star Shield", "line": 714},
                {"effect": "Silence(Prepared)", "magnitude": "applied", "kind": "debuff_on_self", "line": 708},
                {"effect": "Purification", "magnitude": "applied", "kind": "buff", "line": 756},
                {"effect": "Self-Heal", "magnitude": "Healing Coefficient 1.05+0.28", "kind": "buff", "source": "Field Therapy", "line": 758},
                {"effect": "DEF Attribute Increased", "magnitude": "35.05 (798)", "kind": "buff", "source": "Field Therapy", "line": 760},
            ],
            "Slider.Sp": [
                {"effect": "Silence(Prepared)", "magnitude": "applied", "kind": "debuff_on_self", "line": 709},
                {"effect": "Assist", "magnitude": "applied", "kind": "buff", "line": 716},
                {"effect": "Tactical Skill DMG Dealt Increased", "magnitude": "24.80%+9.00%", "kind": "buff", "source": "Sky Tear Arrow", "line": 718},
            ],
        },
        "E": {
            "Rhea": [
                {"effect": "DMG Taken Reduced", "magnitude": "90.17%+30.00%", "kind": "buff", "source": "Star Shield", "line": 724},
                {"effect": "Self-Heal", "magnitude": "Healing Coefficient 1.4", "kind": "buff", "source": "Field Therapy", "line": 727},
                {"effect": "DEF Attribute Increased", "magnitude": "70.83 (939.8)", "kind": "buff", "source": "Field Therapy", "line": 729},
                {"effect": "ATK Attribute Increased", "magnitude": "56.76 (415.7)", "kind": "buff", "source": "Elf Deer", "line": 732},
                {"effect": "DES Attribute Increased", "magnitude": "56.76 (261.7)", "kind": "buff", "source": "Elf Deer", "line": 734},
                {"effect": "Spd Attribute Increased", "magnitude": "56.76 (340.7)", "kind": "buff", "source": "Elf Deer", "line": 735},
                {"effect": "ATK Reduced", "magnitude": "22.57%+7.20% (291.9)", "kind": "debuff", "source": "Dark Arrive", "line": 741},
                {"effect": "DEF Reduced", "magnitude": "22.57%+7.20% (660)", "kind": "debuff", "source": "Dark Arrive", "line": 742},
                {"effect": "DES Reduced", "magnitude": "22.57%+7.20% (183.8)", "kind": "debuff", "source": "Dark Arrive", "line": 743},
                {"effect": "Spd Attribute Reduced", "magnitude": "22.57%+7.20% (239.3)", "kind": "debuff", "source": "Dark Arrive", "line": 744},
                {"effect": "Heal Ban", "magnitude": "applied", "kind": "debuff", "source": "Dark Arrive", "line": 749},
                {"effect": "DMG Taken Increased", "magnitude": "42.89%+9.00%", "kind": "debuff", "source": "Noise", "line": 752},
            ],
            "Aguria.Sp": [
                {"effect": "DEFEATED_ENTERING_BATTLE_2", "magnitude": "0 troops; contributes nothing", "kind": "status", "line": 225},
            ],
            "Satoru": [
                {"effect": "Disarm", "magnitude": "applied (self, from Gray World); purified Round 1", "kind": "self_effect", "line": 706},
                {"effect": "Silence(Prepared)", "magnitude": "applied", "kind": "debuff_on_self", "line": 722},
                {"effect": "Assist", "magnitude": "applied", "kind": "buff", "line": 725},
                {"effect": "Self-Heal", "magnitude": "Healing Coefficient 1.4", "kind": "buff", "source": "Field Therapy", "line": 728},
                {"effect": "DEF Attribute Increased", "magnitude": "75.68 (699.2)", "kind": "buff", "source": "Field Therapy", "line": 730},
                {"effect": "ATK Attribute Increased", "magnitude": "56.76 (377.1)", "kind": "buff", "source": "Elf Deer", "line": 736},
                {"effect": "DES Attribute Increased", "magnitude": "56.76 (291.7)", "kind": "buff", "source": "Elf Deer", "line": 738},
                {"effect": "Spd Attribute Increased", "magnitude": "56.76 (593.7)", "kind": "buff", "source": "Elf Deer", "line": 739},
                {"effect": "ATK Reduced", "magnitude": "22.57%+7.20% (264.8)", "kind": "debuff", "source": "Dark Arrive", "line": 745},
                {"effect": "DEF Reduced", "magnitude": "22.57%+7.20% (491.1)", "kind": "debuff", "source": "Dark Arrive", "line": 746},
                {"effect": "DES Reduced", "magnitude": "22.57%+7.20% (204.9)", "kind": "debuff", "source": "Dark Arrive", "line": 747},
                {"effect": "Spd Attribute Reduced", "magnitude": "22.57%+7.20% (416.9)", "kind": "debuff", "source": "Dark Arrive", "line": 748},
                {"effect": "Heal Ban", "magnitude": "applied", "kind": "debuff", "source": "Dark Arrive", "line": 750},
                {"effect": "DMG Taken Increased", "magnitude": "42.89%+9.00%", "kind": "debuff", "source": "Noise", "line": 753},
            ],
        },
    },
}
data["buff_states"] = buff_states

# ---------------------------------------------------------------------------
# 4. Unit summaries — per-unit stat tables + team summaries, BOTH battles.
# ---------------------------------------------------------------------------
unit_summaries = {
    "battle_1": {
        "result": "Stalemate",
        "source_lines": "143-180, 247-263",
        "damage_statistics": {
            "A": {
                "Patra": {"normal_atk": 12352, "skill": 80543, "skills_used": 7},
                "Rhea": {"normal_atk": 13370, "skill": 0, "skills_used": 0},
                "Slider.Sp": {"normal_atk": 6032, "skill": 0, "skills_used": 0},
            },
            "E": {
                "Rhea": {"normal_atk": 5439, "skill": 0, "skills_used": 3},
                "Aguria.Sp": {"normal_atk": 60, "skill": 25971, "skills_used": 4},
                "Satoru": {"normal_atk": 0, "skill": 0, "skills_used": 3},
            },
        },
        "per_unit_stats": {
            "A": {
                "Patra": {"kills": 92895, "heal": 4962, "slight_wound": 20171, "severe_wound": 629, "death": 209},
                "Rhea": {"kills": 13370, "heal": 72, "slight_wound": 2425, "severe_wound": 36, "death": 12},
                "Slider.Sp": {"kills": 6032, "heal": 0, "slight_wound": 2881, "severe_wound": 55, "death": 18},
            },
            "E": {
                "Rhea": {"kills": 5439, "heal": 0, "slight_wound": 31747, "severe_wound": 677, "death": 225},
                "Aguria.Sp": {"kills": 26031, "heal": 0, "slight_wound": 48444, "severe_wound": 4715, "death": 1841},
                "Satoru": {"kills": 0, "heal": 0, "slight_wound": 24060, "severe_wound": 441, "death": 147},
            },
        },
        "team_summary": {
            "left_revela": {"total_troops": 165000, "health": 138564, "slight_wound": 25477, "severe_wound": 720, "death": 239,
                            "header": "revela / Glorius / Lv.48 — 138,564 / 165,000"},
            "right_rhea": {"total_troops": 165000, "health": 52703, "slight_wound": 104251, "severe_wound": 5833, "death": 2213,
                           "header": "Rhea / Nothing — 52,703 / 165,000"},
        },
        "survivors_entering_battle_2": {"E_Rhea": 22351, "E_Satoru": 30352, "E_Aguria.Sp": 0, "line": 670},
    },
    "battle_2": {
        "result": "Victory",
        "source_lines": "184-221, 678-694",
        "damage_statistics": {
            "A": {
                "Patra": {"normal_atk": 0, "skill": 48220, "skills_used": 6},
                "Rhea": {"normal_atk": 3861, "skill": 0, "skills_used": 0},
                "Slider.Sp": {"normal_atk": 622, "skill": 0, "skills_used": 0},
            },
            "E": {
                "Rhea": {"normal_atk": 0, "skill": 0, "skills_used": 0},
                "Aguria.Sp": {"normal_atk": 0, "skill": 0, "skills_used": 0},
                "Satoru": {"normal_atk": 42, "skill": 0, "skills_used": 0},
            },
        },
        "per_unit_stats": {
            "A": {
                "Patra": {"kills": 48220, "heal": 0, "slight_wound": 0, "severe_wound": 0, "death": 0},
                "Rhea": {"kills": 3861, "heal": 34, "slight_wound": 8, "severe_wound": 0, "death": 0},
                "Slider.Sp": {"kills": 622, "heal": 0, "slight_wound": 0, "severe_wound": 0, "death": 0},
            },
            "E": {
                "Rhea": {"kills": 0, "heal": 0, "slight_wound": 19700, "severe_wound": 4287, "death": 1697},
                "Aguria.Sp": {"kills": 0, "heal": 0, "slight_wound": 0, "severe_wound": 0, "death": 0},
                "Satoru": {"kills": 42, "heal": 0, "slight_wound": 26840, "severe_wound": 4326, "death": 1712},
            },
        },
        "team_summary": {
            "left_revela": {"total_troops": 138564, "health": 138556, "slight_wound": 8, "severe_wound": 0, "death": 0,
                            "header": "revela / Glorius / Lv.48 — 138,556 / 165,000",
                            "note": "Total Number Of Troops 138,564 carries over from Battle 1 surviving health (line 191/225)"},
            "right_rhea": {"total_troops": 52703, "health": 0, "slight_wound": 46540, "severe_wound": 8613, "death": 3409,
                           "header": "Rhea / Nothing — 0 / 165,000"},
        },
        "starting_troops": {
            "A": {"Patra": 33991, "Rhea": 52527, "Slider.Sp": 52046},
            "E": {"Rhea": 22351, "Aguria.Sp": 0, "Satoru": 30352},
            "source_lines": "203-211",
        },
    },
}
data["unit_summaries"] = unit_summaries

# ---------------------------------------------------------------------------
# Write strict UTF-8 JSON.
# ---------------------------------------------------------------------------
with io.open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Console summary (ASCII only — never print CJK).
print("WROTE", OUT)
print("damage_instances:", len(data["damage_instances"]))
print("revealed_attributes:", len(data["revealed_attributes"]))
