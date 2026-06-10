# -*- coding: utf-8 -*-
"""Build data/sim/status_effects.json from Buff.csv + verified evidence.

Behaviors are hand-curated from EVIDENCE gathered by the companion scan scripts
(_buff_evidence_scan, _buff_skilldes_scan, _buff_extra_scan, _buff_bycol_scan),
the existing wiki (Status-Effects.md, Game-Hints.md), and Language_SkillDes/
Language_Game/Language_SysTip rows. Each entry carries an `evidence` list citing
file:row or skill ids. Magnitudes that vary per-skill (the buff registry stores no
fixed value) are noted as carried by the applying skill; the server resolves the
final damage formula (UNKNOWN_SERVER_SIDE).

HARD RULES obeyed: CSV via DictReader utf-8-sig; all CJK written to UTF-8 file only;
no guessed numbers; strict JSON (ensure_ascii=False, indent=2).
"""
import csv
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(ROOT, "data", "csv")
OUT_JSON = os.path.join(ROOT, "data", "sim", "status_effects.json")


def load(name):
    with io.open(os.path.join(CSV, name + ".csv"), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


buff_rows = {r["buffId"]: r for r in load("Buff")}
loc = json.load(io.open(os.path.join(ROOT, "data", "localization.json"), encoding="utf-8"))


def loc_en(token):
    return (loc.get(token.strip("{}"), {}) or {}).get("English_Text")


# Verified supplemental CN->EN for the 'Chance' buffs the game ships with a blank
# Name_en and that are absent from localization.json (taken verbatim from
# tools/wikigen/resolver.py _CJK_FIX, which the wiki already uses).
_CJK_FIX = {
    "概率极速": "Chance Haste",
    "概率连击": "Chance Combo",
    "概率反击": "Chance Counter",
    "概率溅射": "Chance Splash",
    "概率闪避": "Chance Dodge",
}


# Per-buff curated mechanics. Keys are buffId (str).
# fields: category, behavior, prepared_variant, stacking, evidence (list of citations)
C = {
    # ---- DMG modifiers (dmg_mod) ----
    "5": ("dmg_mod", "Multiplies the bearer's outgoing damage upward by a skill-supplied percentage; pure damage-dealt buff with no other effect. Magnitude is carried by the applying skill, not fixed in Buff.csv.",
          "Same effect from the same skill type does not stack (highest applies); different skill types add together.",
          ["Buff.csv:2", "Language_SkillDes.csv 'DMG Dealt Increased'", "Game-Hints.md (same-type effects don't stack)"]),
    "6": ("dmg_mod", "Reduces the target's outgoing damage by a skill-supplied percentage (e.g. Bless Immortals -35%). Magnitude carried by the applying skill.",
          "Same-type does not stack (highest); cross-type adds.",
          ["Buff.csv:3", "NewSkillInfo ST1 ID1027 Bless Immortals (DMG Dealt Reduced 35%)"]),
    "7": ("dmg_mod", "Increases damage the target takes by a skill-supplied percentage (Affected By DES); amplifies all incoming hits while active.",
          "Same-type does not stack (highest); cross-type adds.",
          ["Buff.csv:4", "NewSkillInfo ST1 ID1042 Cold Secret 'DMG Taken Increased 15.2%'"]),
    "8": ("dmg_mod", "Reduces damage the bearer takes by a skill-supplied percentage (Affected By DEF); common defensive buff.",
          "Same-type does not stack (highest); cross-type adds.",
          ["Buff.csv:5", "NewSkillInfo ST1 ID1005 Devil Fruit 'DMG Taken Reduced'"]),
    "9": ("attr_mod", "Raises the bearer's ATK attribute by a skill-supplied amount (flat point value or %, Affected By DEF).",
          "Same-type does not stack (highest); cross-type adds.",
          ["Buff.csv:6", "NewSkillInfo ST1 ID65 Boost Morale 'ATK Attribute Increased 11.4'"]),
    "10": ("attr_mod", "Raises the bearer's DEF attribute by a skill-supplied amount.", "Same-type highest; cross-type adds.",
           ["Buff.csv:7", "NewSkillInfo ST1 ID27 Self-Healing 'DEF Attribute Increased 15.2'"]),
    "11": ("attr_mod", "Raises the bearer's DES (Ruin) attribute by a skill-supplied amount.", "Same-type highest; cross-type adds.",
           ["Buff.csv:8", "localization 破坏属性提高"]),
    "12": ("attr_mod", "Raises the bearer's Speed attribute by a skill-supplied amount.", "Same-type highest; cross-type adds.",
           ["Buff.csv:9", "NewSkillInfo ST1 ID15 Feather Fall 'Spd Attribute Increased 11.4'"]),
    "13": ("attr_mod", "Raises all four of the bearer's attributes (ATK/DEF/DES/Spd) by a skill-supplied amount.", "Same-type highest; cross-type adds.",
           ["Buff.csv:10", "NewSkillInfo ST2 ID88 Elk Armor 'Increase All Attributes 7.4'"]),
    "14": ("attr_mod", "Lowers the target's ATK attribute by a skill-supplied amount.", "Same-type highest; cross-type adds.",
           ["Buff.csv:11", "localization 攻击属性降低"]),
    "15": ("attr_mod", "Lowers the target's DEF attribute by a skill-supplied amount.", "Same-type highest; cross-type adds.",
           ["Buff.csv:12", "localization 防御属性降低"]),
    "16": ("attr_mod", "Lowers the target's DES (Ruin) attribute by a skill-supplied amount.", "Same-type highest; cross-type adds.",
           ["Buff.csv:13", "localization 破坏属性降低"]),
    "17": ("attr_mod", "Lowers the target's Speed attribute by a skill-supplied amount.", "Same-type highest; cross-type adds.",
           ["Buff.csv:14", "localization 速度属性降低"]),
    "18": ("attr_mod", "Lowers all four of the target's attributes by a skill-supplied amount (Affected By DES).", "Same-type highest; cross-type adds.",
           ["Buff.csv:15", "NewSkillInfo ST1 ID1004 Rock Fire 'All Attributes Reduced'"]),
    # 19-28 are a second copy of the attribute up/down family (same names/Types as 9-18);
    # the registry duplicates them as a distinct effect-instance id space.
    "19": ("attr_mod", "Raises the bearer's ATK attribute (duplicate registry entry of 9; used by some skills, e.g. Blazing Slash).", "Same-type highest; cross-type adds.",
           ["Buff.csv:16", "NewSkillInfo ST1 ID1040 Blazing Slash uses buff 19"]),
    "20": ("attr_mod", "Raises the bearer's DEF attribute (duplicate registry entry of 10).", "Same-type highest; cross-type adds.",
           ["Buff.csv:17", "localization 防御属性提高"]),
    "21": ("attr_mod", "Raises the bearer's DES attribute (duplicate registry entry of 11).", "Same-type highest; cross-type adds.",
           ["Buff.csv:18", "localization 破坏属性提高"]),
    "22": ("attr_mod", "Raises the bearer's Speed attribute (duplicate registry entry of 12).", "Same-type highest; cross-type adds.",
           ["Buff.csv:19", "localization 速度属性提高"]),
    "23": ("attr_mod", "Raises all of the bearer's attributes (duplicate registry entry of 13).", "Same-type highest; cross-type adds.",
           ["Buff.csv:20", "localization 所有属性提高"]),
    "24": ("attr_mod", "Lowers the target's ATK attribute (duplicate registry entry of 14).", "Same-type highest; cross-type adds.",
           ["Buff.csv:21", "localization 攻击属性降低"]),
    "25": ("attr_mod", "Lowers the target's DEF attribute (duplicate registry entry of 15).", "Same-type highest; cross-type adds.",
           ["Buff.csv:22", "localization 防御属性降低"]),
    "26": ("attr_mod", "Lowers the target's DES attribute (duplicate registry entry of 16).", "Same-type highest; cross-type adds.",
           ["Buff.csv:23", "localization 破坏属性降低"]),
    "27": ("attr_mod", "Lowers the target's Speed attribute (duplicate registry entry of 17).", "Same-type highest; cross-type adds.",
           ["Buff.csv:24", "localization 速度属性降低"]),
    "28": ("attr_mod", "Lowers all of the target's attributes (duplicate registry entry of 18).", "Same-type highest; cross-type adds.",
           ["Buff.csv:25", "localization 所有属性降低"]),
    # ---- per-source damage-channel modifiers (dmg_mod) ----
    "29": ("dmg_mod", "Increases the bearer's Normal-ATK damage by a skill-supplied percentage.", "Same-type highest; cross-type adds.",
           ["Buff.csv:26", "localization 普通攻击伤害提高"]),
    "30": ("dmg_mod", "Decreases the target's Normal-ATK damage by a skill-supplied percentage.", "Same-type highest; cross-type adds.",
           ["Buff.csv:27", "localization 普通攻击伤害降低"]),
    "31": ("dmg_mod", "Increases the bearer's Tactical-skill damage by a skill-supplied percentage (Affected By Spd).", "Same-type highest; cross-type adds.",
           ["Buff.csv:28", "NewSkillInfo ST2 ID1044 Melting Soul 'Tactical Skill DMG Dealt Increased 15.2%'"]),
    "32": ("dmg_mod", "Decreases the target's Tactical-skill damage by a skill-supplied percentage.", "Same-type highest; cross-type adds.",
           ["Buff.csv:29", "localization 战术技能伤害降低"]),
    "33": ("dmg_mod", "Increases the bearer's Pursuit-skill damage by a skill-supplied percentage (Affected By Spd).", "Same-type highest; cross-type adds.",
           ["Buff.csv:30", "NewSkillInfo ST1 ID1037 Glowing Leaf 'Pursuit Skill DMG Dealt Increased'"]),
    "34": ("dmg_mod", "Decreases the target's Pursuit-skill damage by a skill-supplied percentage.", "Same-type highest; cross-type adds.",
           ["Buff.csv:31", "localization 追击技能伤害降低"]),
    "35": ("dmg_mod", "Increases Normal-ATK damage the target takes by a skill-supplied percentage.", "Same-type highest; cross-type adds.",
           ["Buff.csv:32", "localization 受到普通攻击伤害提高"]),
    "36": ("dmg_mod", "Decreases Normal-ATK damage the bearer takes by a skill-supplied percentage.", "Same-type highest; cross-type adds.",
           ["Buff.csv:33", "localization 受到普通攻击伤害降低"]),
    "37": ("dmg_mod", "Increases Tactical-skill damage the target takes by a skill-supplied percentage.", "Same-type highest; cross-type adds.",
           ["Buff.csv:34", "localization 受到战术技能伤害提高"]),
    "38": ("dmg_mod", "Decreases Tactical-skill damage the bearer takes by a skill-supplied percentage.", "Same-type highest; cross-type adds.",
           ["Buff.csv:35", "localization 受到战术技能伤害降低"]),
    "39": ("dmg_mod", "Increases Pursuit-skill damage the target takes by a skill-supplied percentage (Affected By DES); e.g. Demon Rock Slash +15.4%.", "Same-type highest; cross-type adds.",
           ["Buff.csv:36", "NewSkillInfo ST4 ID1002 Demon Rock Slash 'takes increased Pursuit damage 15.4%'"]),
    "40": ("dmg_mod", "Decreases Pursuit-skill damage the bearer takes by a skill-supplied percentage.", "Same-type highest; cross-type adds.",
           ["Buff.csv:37", "localization 受到追击技能伤害降低"]),
    "42": ("attr_mod", "Raises the bearer's Soldier HP attribute by a skill-supplied amount (boosts both effective HP and healing, which scales off HP).", "Same-type highest; cross-type adds.",
           ["Buff.csv:38", "localization 士兵生命属性提高", "Game-Hints.md (healing scales off Soldiers' HP)"]),
    "43": ("dmg_mod", "Reduces Curse (DoT) damage the bearer takes by a skill-supplied percentage (Affected By DEF); resistance buff vs the Curse channel.", "Same-type highest; cross-type adds.",
           ["Buff.csv:39", "NewSkillInfo ST3 ID14 Magic Cloak 'Curse DMG Taken Reduced'"]),
    "44": ("dmg_mod", "Reduces Burn (DoT) damage the bearer takes by a skill-supplied percentage; resistance buff vs the Burn channel.", "Same-type highest; cross-type adds.",
           ["Buff.csv:40", "Language_SkillDes 受到燃烧伤害降低 'Burning DMG Taken Reduced'"]),
    "47": ("dmg_mod", "Increases the True/Real damage the bearer deals by a skill-supplied percentage (True damage ignores DEF mitigation).", "Same-type highest; cross-type adds.",
           ["Buff.csv:41", "localization 造成真实伤害提高"]),
    # ---- proc / state buffs ----
    "70": ("proc", "Assault state: the bearer's Normal ATK gains added True/Real damage (Affected By ATK; per-skill Real DMG Base 12.5-50). An offensive empowerment, not a heal or DoT.",
            False, "Carried per-skill; refreshes/overwrites with the higher value (attr-style).",
            ["Buff.csv:42", "NewSkillInfo ST1 ID65 Boost Morale; ST2 ID67 Epee Storm 'Real DMG Base 30'", "Game 强袭 'Enhances Assault effects'"]),
    "73": ("shield", "Shield: grants N layers; each layer fully blocks one incoming damage instance (not a damage amount). Pierced by attacks flagged 'Ignores Dodge and Shield'.",
            "Stacks as layers (skills grant 1-2). Each blocked hit consumes one layer.",
            ["Buff.csv:43", "Language_SkillDes 'Gain N Layers Of Shield, Which Can Block N DMG'", "NewSkillInfo ST2 ID1008 Wing Shield (2 layers)", "Status-Effects.md (Shield absorbs first instance)"]),
    "74": ("heal", "First Aid: a reactive heal -- when the bearer takes a Normal ATK, a chance to Restore Life (skill-supplied healing coefficient, e.g. 0.55-0.76; scales off Soldiers' HP).",
            "Per-skill coefficient and trigger chance.",
            ["Buff.csv:44", "NewSkillInfo ST1 ID37 Past Memory (74, coef 0.55); ST1 ID1005 Devil Fruit (74, coef 0.76)"]),
    "79": ("proc", "Chance Haste: a percentage chance to gain an extra/faster action (Haste proc). Trigger chance is skill-supplied.",
            "Per-skill proc chance.",
            ["Buff.csv:45", "resolver._CJK_FIX 概率极速 'Chance Haste'"]),
    "80": ("proc", "Chance Combo: on a Normal ATK, a chance to immediately strike again (combo follow-up). Trigger chance is skill-supplied (e.g. Glowing Leaf 75%).",
            "Per-skill proc chance.",
            ["Buff.csv:46", "NewSkillInfo ST1 ID55 Clap Thunder 'A Chance to Combo'; ST1 ID1037 '75% Probability Combo'"]),
    "81": ("proc", "Chance Counter: when the bearer receives a Normal ATK, a chance to counterattack (skill-supplied DMG coefficient, e.g. 0.7-1.69). Once applied it cannot be prevented.",
            "Per-skill chance + coefficient.",
            ["Buff.csv:47", "NewSkillInfo ST1 ID9 Counterattack (coef 0.95); ST1 ID82 '100% Counterattack'", "Status-Effects.md (Counterattack cannot be prevented)"]),
    "82": ("proc", "Chance Splash: on a Normal ATK (or Pursuit), a chance to splash damage to other enemies (skill-supplied DMG coefficient, e.g. 0.5-1.5).",
            "Per-skill chance + coefficient.",
            ["Buff.csv:48", "NewSkillInfo ST1 ID10 Red Blade 'Splash On Other Enemies (coef 0.50)'"]),
    # ---- control (CC) ----
    "114": ("control", "Stun: the unit is Unable to Move and cannot act at all (no normal attack, tactical, or pursuit) for the duration.",
             False, "Refreshes duration; cleansable by Purification.",
             ["Buff.csv:62", "Language_SkillDes 处于眩晕状态 'In A Stunned State'", "NewSkillInfo ST1 ID1009 Shocking Roar 'In A Stunned State,Unable To Move'", "Status-Effects.md (Stun = cannot act)"]),
    "115": ("control", "Disarm: the unit cannot launch Normal ATK (tactical/pursuit skills still usable).",
             False, "Refreshes duration; usually cleansable, but some self-applied Disarm is flagged 'Cannot Be purified'.",
             ["Buff.csv:63", "NewSkillInfo ST2 ID1027 Destroy Domain 'In A Disarmed State,Cannot Launch Normal ATK'", "Status-Effects.md (Disarm = no normal attack)"]),
    "116": ("control", "Silence: the unit cannot launch Tactical skills (normal attack and pursuit still usable).",
             False, "Refreshes duration; cleansable by Purification.",
             ["Buff.csv:64", "NewSkillInfo ST2 ID1024 Cold Attack 'In A Silenced State,Cannot Launch Tactical Skills'", "Status-Effects.md (Silence = no tactical skills)"]),
    "117": ("control", "Chaos: the unit carries out Undifferentiated ATK -- normal attacks and damage-dealing Tactical skills (and pursuits they trigger) hit completely random targets, friend or foe. Overrides Taunt.",
             False, "Refreshes duration; cleansable by Purification.",
             ["Buff.csv:65", "Language_SysTip 混乱 'Chaos effect only applies to normal attacks and damage-dealing Tactical Skills. Subsequent Pursuit ... is also affected'", "NewSkillInfo ST4 ID17 Chaos 'Carry Out Undifferentiated ATK'", "Status-Effects.md"]),
    # prepared variants 83-86 telegraph 114-117
    "83": ("control", "Telegraphed (Prepared) Stun -- a Stun whose application is announced one step ahead (the '(Prepared)' display of buff 114); resolves to the same Unable-to-Move state.",
            True, "Becomes the real Stun (114) when it fires.",
            ["Buff.csv:49", "Buff.csv:62 (114 Stun)", "Name token 眩晕(预备) = Stun(Prepared)"]),
    "84": ("control", "Telegraphed (Prepared) Disarm -- the '(Prepared)' display of buff 115; resolves to Disarm (cannot Normal ATK).",
            True, "Becomes the real Disarm (115) when it fires.",
            ["Buff.csv:50", "Buff.csv:63 (115 Disarm)", "NewSkillInfo ST1 ID1025 Dragon Serious applies 84/85/86 as '25% Probability ... Disarmed/Silenced/Chaos'"]),
    "85": ("control", "Telegraphed (Prepared) Silence -- the '(Prepared)' display of buff 116; resolves to Silence (cannot Tactical).",
            True, "Becomes the real Silence (116) when it fires.",
            ["Buff.csv:51", "Buff.csv:64 (116 Silence)", "NewSkillInfo ST1 ID1025 Dragon Serious"]),
    "86": ("control", "Telegraphed (Prepared) Chaos -- the '(Prepared)' display of buff 117; resolves to Chaos (random-target attacks).",
            True, "Becomes the real Chaos (117) when it fires.",
            ["Buff.csv:52", "Buff.csv:65 (117 Chaos)", "NewSkillInfo ST1 ID1025 Dragon Serious"]),
    "118": ("taunt", "Taunt (Provoke): forces enemies to direct their Normal ATK at the taunter, overriding normal target selection. Ignored if the taunted unit is also under Chaos.",
             False, "Refreshes duration.",
             ["Buff.csv:66", "NewSkillInfo ST2 ID110 Knight Creed 'In A Provoked State'", "Status-Effects.md (Taunt forces normal-attack on taunter; ignored under Chaos)"]),
    "119": ("control", "Heal Ban (Forbidden Treatment): the unit cannot be healed by any source for the duration.",
             False, "Refreshes duration.",
             ["Buff.csv:67", "Language_SkillDes 无法受到治疗效果 'Cannot Be Healed'", "NewSkillInfo ST2 ID76 Taboo Seal 'Forbidden Treatment State,Cannot Be Healed'", "Status-Effects.md"]),
    "154": ("control", "Arcane Missile: a recurring random-CC effect -- before each round, a chance to inflict one of Disarm / Silence / Chaos / Stun on the target.",
             False, "Re-rolls each round while active.",
             ["Buff.csv:73", "NewSkillInfo ST1 ID86 Arcane Missile 'Before Each Round,A Chance to In A Disarmed/Silenced/Chaos/Stunned State'"]),
    # ---- DoT ----
    "108": ("dot", "Burn: a damage-over-time -- 'Before Each Round, Burning DMG Taken' at a skill-supplied DMG coefficient (~0.5-1.69). Mitigated by buff 44; amplified by 157; can be detonated by 158 / Exploding-Flame skills.",
             False, "Per-skill coefficient and duration; reapplying refreshes/can enable detonation skills.",
             ["Buff.csv:58", "NewSkillInfo ST2 ID19 Hopeless; ST1 ID1009 Shocking Roar (coef 1.69)", "ST2 ID73 Exploding Flame (detonate 1.6 if Burning)"]),
    "109": ("dot", "Curse: a damage-over-time -- 'Before Each Round, Curse DMG Taken' at a skill-supplied DMG coefficient (~0.5-1.69). Mitigated by buff 43; amplified by 157; detonated by 158.",
             False, "Per-skill coefficient and duration.",
             ["Buff.csv:59", "NewSkillInfo ST1 ID1002 Frighten (coef 1.33); ST1 ID1007 Black Bog (coef 1.52)"]),
    "157": ("dmg_mod", "Combustion Aid: a debuff that amplifies DoT taken -- when the target takes Curse or Burning damage, a chance to multiply that DoT instance by 1.5x.",
             False, "Per-skill trigger chance; multiplier 1.5x is in the effect string.",
             ["Buff.csv:75", "NewSkillInfo ST1 ID92 Combustion Aid 'Make Curse or Burning DMG Taken*1.5' (Buff=157_..._1.5_...)"]),
    "158": ("proc", "Element Burst: a proc -- when the bearer attacks an enemy that has Tactical Burning or Curse, a chance to immediately settle all remaining Burn+Curse DoT at 1.3x and then remove those effects (detonation; multi-stage attacks trigger only on the first hit).",
             False, "Per-skill trigger chance; multiplier 1.3x in effect string.",
             ["Buff.csv:76", "NewSkillInfo ST3 ID40 Element Burs 'settle all remaining Burning and Curse DMG at 1.3x, ... effects are removed' (Buff=158_..._1.3_...)"]),
    # ---- lifesteal ----
    "106": ("lifesteal", "Blood Sucking: the bearer recruits/restores some enemy soldiers when it deals damage, by a skill-supplied Blood Sucking Coefficient (0.4-1.5). A lifesteal multiplier on damage dealt.",
             False, "Per-skill coefficient and duration.",
             ["Buff.csv:56", "NewSkillInfo ST2 ID84 Night Elf 'Blood Sucking Coefficien 0.6'; ST4 ID1005 (1.50)", "Language_SkillDes 离间系数 'Blood Sucking Coefficient'"]),
    "107": ("heal", "Self-Heal / regen: 'Before Each Round, Restore Life' at a skill-supplied Healing Coefficient (0.32-1.52; scales off Soldiers' HP). The core periodic-heal buff used by most healers.",
             False, "Per-skill coefficient and duration; cross-type heals add.",
             ["Buff.csv:57", "NewSkillInfo ST1 ID1 Healing Light (107, coef 0.45); ST3 ID7 Holy Water (107, coef 0.57)", "Game-Hints.md (healing scales off HP)"]),
    "87": ("heal", "Heal: an instant restore-life effect (heal value scales off the Soldiers' HP attribute). The generic active-heal status shown as 'Healing'.",
            False, "Per-skill coefficient.",
            ["Buff.csv:53", "Language_SysTip 治疗效果受士兵生命属性影响 'Healing Effect Is Affected By Soldiers HP'", "Language_SkillDes 治疗系数 'Healing Coefficient'"]),
    # ---- other / utility positive states ----
    "88": ("proc", "Instant / Swiftcast: while active, when the bearer activates a Tactical skill that needs preparation, a chance to reduce its preparation time by 1 round.",
            False, "Per-skill trigger chance and duration.",
            ["Buff.csv:54", "NewSkillInfo ST2 ID75 Sheep Game 'Swiftcast State, ... Reduce Preparation Time By 1 Round'"]),
    "89": ("other", "Eternal: 'Attribute Will Not Be Changed' -- the bearer's attributes are locked so they cannot be raised or lowered (immune to attribute buffs/debuffs) for the duration. Does not block CC or DoT.",
            False, "Refreshes duration.",
            ["Buff.csv:55", "NewSkillInfo ST1 ID77 Angel Blesse 'In An Eternal State,Attribute Will Not Be Changed'"]),
    "111": ("proc", "Chance Dodge: when receiving a Normal ATK, a chance to dodge it entirely (skill-supplied chance, e.g. 30%). Bypassed by attacks flagged 'Ignores Dodge and Shield'.",
             False, "Per-skill proc chance.",
             ["Buff.csv:60", "NewSkillInfo ST2 ID68 Idol Voice '30% Probability Dodge'", "resolver._CJK_FIX 概率闪避 'Chance Dodge'"]),
    "113": ("other", "Concentration (Focus): the bearer is Immune to Disarm/Silence/Stun/Chaos/Taunt during its turn -- it ignores those control effects while acting, but does not remove or block them from being applied.",
             False, "Refreshes duration.",
             ["Buff.csv:61", "NewSkillInfo ST1 ID14 Field 'In A Focused State,Immune: Disarm, Silence, Stun, Chaos, Taunts'", "Status-Effects.md (Immune/Concentration)"]),
    "120": ("taunt", "Assist (Protect): the bearer guards allied troops from Normal ATK -- 'Protect Our Troops From Normal ATK', intercepting normal attacks aimed at protected allies (an ally-side cover/redirect).",
             False, "Refreshes duration.",
             ["Buff.csv:68", "NewSkillInfo ST1 ID26 Star Shield 'Protect Our Troops From Normal ATK' (Buff=120_...)", "ST2 ID21 Block (120)"]),
    "125": ("proc", "Superconducting: while active, when the bearer uses a Tactical skill that does NOT require preparation, a chance to immediately cast that Tactical skill 1 additional time.",
             False, "Per-skill trigger chance and duration.",
             ["Buff.csv:69", "NewSkillInfo ST1 ID63 Mana Storage 'Superconducting ... Activate The Tactical Skill 1 Additional Time'"]),
    "139": ("cleanse", "Purification: removes harmful effects produced by Tactical and Pursuit skills from an ally (cleanse). Often applied 'before each round, a chance to Purify: Disarm/Silence/Stun/Chaos/Taunt'. Some debuffs are flagged 'Cannot Be purified'.",
             False, "Per-skill chance; one cleanse per trigger.",
             ["Buff.csv:70", "Language_SkillDes 净化 'Purify The Harmful Effect Produced By Tactical And Pursuit Skill'", "NewSkillInfo ST1 ID53 Time Story", "Status-Effects.md (Purify)"]),
    "140": ("proc", "Sneak Attack: the bearer's attacks Will Not Be Affected by the Counter ATK Effect (it cannot be counterattacked). A defensive proc-immunity, typically paired with a DMG-dealt buff.",
             False, "Boolean state; refreshes duration.",
             ["Buff.csv:71", "NewSkillInfo ST3 ID17 Sneak Attack 'Will Not Be Affected by the Counter ATK Effect' (Buff=140_...)"]),
    "150": ("proc", "Insight: raises the activation probability of ALL the bearer's Pursuit skills by a skill-supplied amount ('All Pursuit Skill Probabilities Increased').",
             False, "Per-skill magnitude and duration.",
             ["Buff.csv:72", "NewSkillInfo ST1 ID84 Broken Star 'In An Insight State,All Pursuit Skill Probabilities Increased' (Buff=150_...)"]),
    "155": ("proc", "Precision Strike: when the bearer launches an attack, a chance to Ignore Dodge and Shield AND ignore Soldier-Restraint penalties (the attack cannot be dodged/blocked and loses the -25% restraint reduction).",
             False, "Per-skill trigger chance and duration.",
             ["Buff.csv:74", "NewSkillInfo ST1 ID91 Time's Flow / ST1 ID94 Night Dance Allure / ST3 ID42 ATK-DEF Shift all carry Buff=155_... 'Ignores Dodge and Shield, Ignores Soldier Restraint effects'"]),
    "159": ("proc", "Pursuit Splash: when the bearer launches a Pursuit skill, a chance to splash that pursuit damage onto other enemies (skill-supplied DMG coefficient ~0.6). A pursuit-channel version of Splash.",
             False, "Per-skill trigger chance and coefficient.",
             ["Buff.csv:77", "NewSkillInfo ST1 ID93 Arcane Buff / ST3 ID41 Weakness Break 'When Launching Pursuit Skills, A Chance to Splash On Other Enemies (coef 0.60)'", "Name token 追击+溅射"]),
}

out = {}
missing = []
for bid, row in buff_rows.items():
    cn_token = row.get("Name", "")
    name_en = (row.get("Name_en") or "").strip()
    if not name_en:
        # fill blank English from localization via the {Name} token, then from the
        # verified supplemental CJK map for terms the game ships untranslated
        stripped = cn_token.strip("{}")
        name_en = loc_en(cn_token) or _CJK_FIX.get(stripped, "")
    if bid not in C:
        missing.append(bid)
        continue
    spec = C[bid]
    if len(spec) == 4:
        # (category, behavior, stacking, evidence) -> prepared_variant defaults False
        cat, behavior, stacking, evidence = spec
        prepared = False
    else:
        cat, behavior, prepared, stacking, evidence = spec
    out[bid] = {
        "id": int(bid),
        "name_en": name_en,
        "name_cn_token": cn_token,
        "type": int(row.get("Type", "0")),
        "category": cat,
        "behavior": behavior,
        "prepared_variant": prepared,
        "stacking": stacking,
        "magnitude": "Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).",
        "evidence": evidence,
    }

# order numerically
out = {k: out[k] for k in sorted(out, key=lambda x: int(x))}

os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
with io.open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# Report (no CJK) to stdout
print("wrote", OUT_JSON)
print("entries:", len(out), "of", len(buff_rows), "buff rows")
print("missing (not catalogued):", missing)
