"""Emit data/sim/combat_rules.json — machine-readable combat constants.

All values are STATED facts cited in notes/sim/combat_rules.md (Tips.csv,
Language_SysTip.csv, EntryEffect.csv, and the decompiled client). Anything the
client does not contain is the literal string "UNKNOWN_SERVER_SIDE".

Re-runnable: writes only data/sim/combat_rules.json. Strict JSON
(ensure_ascii=False, indent=2) per the project HARD RULES.
"""
import os
import io
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "sim", "combat_rules.json")

UNK = "UNKNOWN_SERVER_SIDE"

DATA = {
    "_meta": {
        "doc": "notes/sim/combat_rules.md",
        "authority": "Combat is server-authoritative; the client renders a resolved replay "
                     "(RoundData/FightBehaviour/BehaviourRet). The damage formula is "
                     "UNKNOWN_SERVER_SIDE. Constants below are STATED rules + inputs only.",
        "sources": [
            "data/csv/Tips.csv",
            "data/csv/Language_SysTip.csv",
            "data/csv/Language_Game.csv",
            "data/csv/EntryEffect.csv",
            "decompiled/Assembly-CSharp/eb46ed1b3cbb.decompiled.cs",
            "wiki/Mechanics/Battle-Mechanics.md",
            "wiki/Reference/Game-Hints.md",
            "wiki/Mechanics/Status-Effects.md",
        ],
    },

    "team": {
        "size": 3,
        "composition": "1 Commander + 2 Strikers",
        "commander_fight_pos": 1,
        "positions_per_side": [1, 2, 3],
        "side_split": {"sideA": [1, 2, 3], "sideB": [4, 5, 6]},
        "win_condition": "A side loses when its Commander loses all troops.",
        "leaving_battle": "counts as a loss",
        "source": "Tips.csv Id=10/Id=30; Language_SysTip row285; decompiled:124036-124037 "
                  "(FightPos==1 = Commander); decompiled:37708-37762 (FightPos<=3 vs >=4)",
    },

    "round_count": 8,
    "round_count_source": "decompiled:37449 (roundData.Round + \"/8\"); Battle-Mechanics.md",

    "round_phase_order": [
        {"phase": "before_action",
         "what": "per-unit BeforeAction[BehaviourRet]: DoT (Burn108/Curse109), periodic "
                 "Self-Heal(107), pre-round CC rolls (Arcane Missile 154)",
         "source": "decompiled:37453-37464; status_effects.md"},
        {"phase": "action",
         "what": "per-unit BehaviourList[BehaviourAction]: normal attack + skills fired",
         "source": "decompiled:37465-37472"},
    ],
    "round_phase_order_note": "Units are iterated in the server-given RoundData.BList order "
                              "(decompiled:19493-19531, 37450); client never sorts.",

    "skill_activation_order": ["Passive", "Strategic", "Tactical", "Normal ATK", "Pursuit"],
    "skill_activation_order_source": "Tips.csv Id=130/row6; Language_SysTip row294; Game-Hints.md",
    "skill_activation_order_note": "Within-unit resolution order (NOT cross-unit turn order). "
                                   "Pursuit fires after the unit's Normal ATK.",

    "turn_order": {
        "key": "hero_atk_spd",
        "entry_effect_id": 50,
        "entry_effect_name": "Hero ATK Spd",
        "direction": "higher Speed acts earlier",
        "tie_break": UNK,
        "source": "Battle-Mechanics.md ('in order of its Speed'); EntryEffect.csv 50=Hero ATK Spd; "
                  "no client-side sort (server supplies RoundData.BList order)",
    },

    "restraint": {
        "triangle": {"Infantry": "Archer", "Archer": "Cavalry", "Cavalry": "Infantry"},
        "neutral_types": ["Chariot"],
        "soldier_type_enum": {"1": "Infantry", "2": "Archer", "3": "Cavalry", "4": "Chariot"},
        "hero_soldier_type_field": "HeroInfo.RST (hero.SoldierT = heroInfo.RST)",
        "restrained_side_modifier": 0.75,
        "modifies": "damage DEALT by the restrained (countered) side is reduced 25% (x0.75)",
        "bypass": "Precision Strike (buff 155) ignores Soldier Restraint",
        "application": UNK,
        "source": "Tips.csv Id=350/row17; Language_SysTip rows 289,304; Language_Game 2209/2210; "
                  "decompiled:10428,17380-17392 (RST->SoldierT); no client-side 0.75 factor",
    },

    "level_suppression": {
        "rule": "higher-tier soldiers deal more damage to lower-tier soldiers",
        "separate_from_restraint": True,
        "tier_field": "SoldierInfo.level (1-6)",
        "magnitude": UNK,
        "source": "Tips.csv Id=330/row16; Language_SysTip row288; Game-Hints.md",
    },

    "targeting": {
        "normal_attack_weights_no_taunt": {"commander": 0.20, "striker1": 0.40, "striker2": 0.40},
        "skills": "random target(s) within the skill's targetCategory/targetCount unless text says otherwise",
        "target_category_enum": {
            "0": "inherit attack target", "2": "Enemy Troops", "4": "Our Troops",
            "6": "Assist/Protect target", "7": "Own/Self", "10": "Enemy Commander",
        },
        "overrides": {
            "taunt_118": "forces enemy Normal ATK onto the taunter",
            "assist_120": "redirects Normal ATK aimed at protected allies onto the bearer",
            "chaos_117": "Normal ATK + damage Tactical (and triggered Pursuit) hit random friend/foe; overrides Taunt",
        },
        "within_bucket_selection": UNK,
        "source": "Tips.csv Id=90/row4; Game-Hints.md; Tips.csv Id=310 (Chaos); skills.md/status_effects.md",
    },

    "skill_activation": {
        "skill_type_enum": {"1": "Strategic", "2": "Tactical", "3": "Passive", "4": "Pursuit"},
        "Strategic": {"when": "before battle (or round-gated via Effect token[1] fromRound)",
                      "stoppable_by_cc": False,
                      "source": "decompiled:9908-9911; skills.md"},
        "Passive": {"when": "whole battle, always on",
                    "stoppable_by_cc": False,
                    "source": "decompiled:9916-9918; skills.md"},
        "Tactical": {"when": "on the unit's turn, probability = SkillP",
                     "may_need_preparation": True,
                     "source": "decompiled:9912-9915; skills.md"},
        "Pursuit": {"when": "after the unit's Normal ATK, probability = SkillP",
                    "source": "decompiled:9920-9923; Battle-Mechanics.md"},
        "trigger_prob_field": "NewSkillInfo.SkillP (UpType==45 -> probability scales with level)",
        "trigger_prob_gear": {
            "131": {"name": "Equip Tactical Skill Activation Probability", "datatype": 2, "size": 10000},
            "132": {"name": "Equip Pursuit Skill Activation Probability", "datatype": 2, "size": 10000},
            "note": "percent gear effects that ADD to the skill's SkillP",
        },
        "insight_buff_150": "raises activation probability of ALL the bearer's Pursuit skills",
        "preparation_modifiers": {
            "instant_88": "chance to cut a Tactical's preparation by 1 round",
            "superconducting_125": "chance to re-cast a no-prep Tactical 1 additional time",
        },
        "source": "EntryEffect.csv 131/132; skills.md; status_effects.md 150/88/125",
    },

    "damage_categories": [
        {"channel": "normal", "dealt_buffs": [29], "taken_buffs": [35, 36],
         "general_dealt": [5, 6], "general_taken": [7, 8],
         "mitigation": "DMG Taken Reduced (8, Affected By DEF), Normal DMG Taken Reduced (36), Dodge(111), Shield(73)"},
        {"channel": "tactical", "dealt_buffs": [31], "taken_buffs": [37, 38],
         "mitigation": "Tactical DMG Taken Reduced (38), general (8)"},
        {"channel": "pursuit", "dealt_buffs": [33], "taken_buffs": [39, 40],
         "mitigation": "Pursuit DMG Taken Reduced (40), general (8)"},
        {"channel": "real_dmg", "dealt_buffs": [47],
         "mitigation": "ignores DEF (true damage)", "magnitude": UNK},
        {"channel": "burn_dot", "buff_id": 108, "phase": "before_action",
         "coef_range": [0.5, 1.69], "resist_buff": 44, "amp_buff": 157, "detonate_buff": 158,
         "magnitude": UNK},
        {"channel": "curse_dot", "buff_id": 109, "phase": "before_action",
         "coef_range": [0.5, 1.69], "resist_buff": 43, "amp_buff": 157, "detonate_buff": 158,
         "magnitude": UNK},
        {"channel": "blood_sucking", "buff_id": 106, "coef_range": [0.4, 1.5],
         "what": "lifesteal: restore soldiers on damage dealt", "magnitude": UNK},
        {"channel": "splash", "buff_ids": [82, 159], "coef_range": [0.5, 1.5],
         "mitigation": "ignores defence (Battle-Mechanics.md)"},
    ],
    "ret_type_enum": {
        "1-3": "damage instance taken (shows -RetVal)",
        "4": "heal (shows +RetVal)",
        "5": "no-number result (block/dodge/shield)",
        "6": "positive buff applied",
        "7": "negative buff/debuff applied",
        "source": "decompiled:37489-37520",
    },

    "attribute_scaling": {
        "rule": "'Affected by X' always refers to the caster; effect scales ~x per 200 points of the named stat",
        "coefficient_per_200": UNK,
        "examples": {"dmg_dealt_up_5": "Affected By DES", "dmg_taken_down_8": "Affected By DEF",
                     "tactical_dealt_31": "Affected By Spd", "pursuit_dealt_33": "Affected By Spd",
                     "healing": "Affected By Soldiers' HP"},
        "source": "Battle-Mechanics.md; Game-Hints.md; Tips.csv Id=250/Id=270 (community magnitude)",
    },

    "in_battle_stat": {
        "formula_shape": "in_battle_stat ~= (hero_stat * team_race_multiplier) + (troop_stat * (1 + sum gear/tech/title%))",
        "hero_stat_at_level": "base + floor(growth * level)",
        "hp_pool": "Hero Soldiers Quantity (EntryEffect 54); max = 2000 + Level*500 + Advance bonus",
        "damage_scales_with": "troop numbers",
        "exact_constants": UNK,
        "source": "Battle-Mechanics.md worked example; Game-Hints.md; gear.md; resolver.hero_stat_at",
    },

    "commander_role": {
        "win_anchor": True,
        "target_weight": 0.20,
        "on_death": "generates a large number of severely-wounded soldiers (Tips.csv Id=430)",
        "siege_chariot_bombard": "team can bombard buildings only if the Commander fields Chariot soldiers (Tips.csv Id=770)",
        "extra_combat_aura": UNK,
        "source": "Tips.csv Id=10/90/430/770; Language_SysTip 285/293/399",
    },

    "stacking": {
        "same_effect_different_type": "adds together",
        "same_effect_same_type": "does not stack (highest applies)",
        "unique_states": ["Dodge", "Assault", "Instant", "Superconducting", "Eternal",
                          "Concentration", "Taunts", "Assist"],
        "prepared_cc_resolves_to": {"83": 114, "84": 115, "85": 116, "86": 117},
        "source": "Tips.csv Id=150/170/190; Language_SysTip 295/296; Game-Hints.md; status_effects.md",
    },

    "impasse": {
        "after_rounds": 8,
        "behaviour": "pause (~1 min); may repeat / retreat / re-engage; varies by mode",
        "resolution": UNK,
        "source": "Battle-Mechanics.md",
    },

    "modeling_assumptions_server_side": [
        "core_damage_equation",
        "restraint_application_point (apply x0.75 to restrained attacker's outgoing damage)",
        "level_suppression_curve",
        "speed_tie_break (deterministic by FightPos / side)",
        "within_bucket_target_selection (uniform random + Taunt/Assist/Chaos overrides)",
        "affected_by_attribute_coefficient (~+1 unit per 200 points)",
        "real_dmg_and_splash_base_magnitude (true damage, bypasses DEF)",
        "dot_base_damage (coef * power * (1-resist) * (1+amp), before_action phase)",
        "blood_sucking_and_heal_magnitude (scales off Soldiers' HP)",
        "proc_resolution_order_and_rng (resolve in activation order, single seeded RNG)",
        "commander_combat_aura (assume none)",
        "impasse_multibout_continuation",
    ],

    "unknown_server_side": [
        "Core damage equation (RetVal mapping from stats/coefficients).",
        "Restraint -25% application (rule stated; no client-side 0.75 factor).",
        "Level-suppression magnitude/curve (direction only).",
        "Speed tie-break / sub-ordering within equal Speed.",
        "Within-bucket target selection beyond 20/40/40 normal-attack weights.",
        "'Affected by X attribute' coefficient (the /200-points rule is community-stated).",
        "Real DMG / Splash base magnitude (only 'ignores DEF' stated).",
        "Burn/Curse DoT resolved per-round damage.",
        "Blood Sucking / heal resolved magnitude.",
        "Proc resolution order & RNG (Counter/Combo/Dodge/Splash/First-Aid).",
        "Commander hidden combat aura (none stated; assumed none).",
        "Impasse / multi-bout continuation behaviour (mode-specific).",
    ],
}


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(DATA, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
