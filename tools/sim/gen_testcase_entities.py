"""Map every named entity in notes/sim simulatorTestCase to game-data ids.

Reads (source of truth):
  data/csv/HeroInfo.csv, NewSkillInfo.csv, PropInfo.csv, EntryEffect.csv
Reuses already-decoded sim layers:
  data/sim/heroes.json, skills.json, gear.json

Writes:
  data/sim/testcase_entities.json  (strict UTF-8, ensure_ascii=False)

Hard rules honored: CSV via csv.DictReader+utf-8-sig; never print CJK; cite
file:row; mark server-side unknowns; FLAG anything not found in the catalogue.
"""
import os
import sys
import csv
import json
import io

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "wikigen"))
from resolver import Resolver  # noqa: E402

R = Resolver()
CSV = os.path.join(ROOT, "data", "csv")


def load_csv(name):
    """Return (rows, header_row_index_by_position). Row numbers are 1-based file
    rows where row 1 = header, so a DictReader index i maps to file row i+2."""
    p = os.path.join(CSV, name + ".csv")
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


hero_rows = load_csv("HeroInfo")
skill_rows = load_csv("NewSkillInfo")
prop_rows = load_csv("PropInfo")

# index by id with file-row citation (header = row 1, first data row = row 2)
hero_by_id = {}
for i, r in enumerate(hero_rows):
    hero_by_id[r["id"]] = (r, i + 2)
skill_by_key = {}
for i, r in enumerate(skill_rows):
    skill_by_key[(r["ST"], r["ID"])] = (r, i + 2)
prop_by_id = {}
for i, r in enumerate(prop_rows):
    prop_by_id[r["id"]] = (r, i + 2)

sim_heroes = {str(h["id"]): h for h in json.load(open(os.path.join(ROOT, "data", "sim", "heroes.json"), encoding="utf-8"))["heroes"]}
sim_skills = {(str(s["st"]), str(s["id"])): s for s in json.load(open(os.path.join(ROOT, "data", "sim", "skills.json"), encoding="utf-8"))}
gear = json.load(open(os.path.join(ROOT, "data", "sim", "gear.json"), encoding="utf-8"))


def skill_block(st, sid, note_main_mod=""):
    """Resolve one skill to (skill_type, skill_id) + decoded fields, flagging miss."""
    key = (str(st), str(sid))
    rowpair = skill_by_key.get(key)
    if not rowpair:
        return {"FLAG": "NOT_FOUND", "requested": "%s_%s" % (st, sid)}
    row, fr = rowpair
    s = sim_skills.get(key, {})
    return {
        "skill_type": int(st),
        "skill_type_name": R.SKILL_TYPE_NAME[str(st)] if hasattr(R, "SKILL_TYPE_NAME") else {"1": "Strategic", "2": "Tactical", "3": "Passive", "4": "Pursuit"}[str(st)],
        "skill_id": int(sid),
        "key": "%s.%s" % (st, sid),
        "name_en": R.skill_name(st, sid),
        "des_en": (row.get("Des_en") or "").strip(),
        "skillP": row.get("SkillP"),
        "skillStone": row.get("SkillStone"),
        "maxUse": row.get("MaxUse"),
        "readyRound": row.get("ReadyRound"),
        "rare": row.get("Rare"),
        "maxedValue": s.get("maxedValue"),
        "maxedValuePercent": s.get("maxedValuePercent"),
        "triggerProbAtMax": s.get("triggerProbAtMax"),
        "buff_raw": row.get("Buff"),
        "dbuff_raw": row.get("Dbuff"),
        "effect_raw": row.get("Effect"),
        "buff_resolved": s.get("buff"),
        "dbuff_resolved": s.get("dbuff"),
        "effects_decoded": s.get("effects"),
        "_cite": "data/csv/NewSkillInfo.csv:%d" % fr,
        "_classification": note_main_mod,
    }


SKILL_TYPE_NAME = {"1": "Strategic", "2": "Tactical", "3": "Passive", "4": "Pursuit"}


def hero_block(hid, label, expected_stat_alloc):
    rowpair = hero_by_id.get(str(hid))
    if not rowpair:
        return {"FLAG": "NOT_FOUND", "label": label}
    row, fr = rowpair
    sh = sim_heroes.get(str(hid), {})
    return {
        "label_in_testcase": label,
        "hero_id": int(hid),
        "name_en": R.hero_name(hid),
        "is_sp_variant": "Sp" in (row.get("name") or "") or "Sp" in (row.get("name_en") or ""),
        "star": int(row["rare"]),
        "race": {"id": int(row["type"]), "name_en": {"1": "Human", "2": "Orc", "3": "Elf"}.get(row["type"], "?")},
        "rst": int(row["RST"]),
        "rst_archetype": {"0": "-", "1": "Infantry (DEF+Spd)", "2": "Archer (ATK+Ruin)", "3": "Cavalry (DEF+ATK)", "4": "Chariot (Ruin+ATK)"}.get(row["RST"], "?"),
        "base_stats": {"attack": int(row["attack"]), "defense": int(row["defense"]), "ruin": int(row["ruin"]), "speed": int(row["speed"])},
        "grow": {"attack": row["attack_grow"], "defense": row["defense_grow"], "ruin": row["ruin_grow"], "speed": row["speed_grow"]},
        "maxed_lv80": sh.get("maxed_lv80"),
        "main_skill": {"st": int(row["skill0_type"]), "id": int(row["skill0_id"]), "name_en": R.skill_name(row["skill0_type"], row["skill0_id"])},
        "default_modular_skills": [
            {"slot": 1, "st": int(row["skill1_type"]), "id": int(row["skill1_id"]), "name_en": R.skill_name(row["skill1_type"], row["skill1_id"])},
            {"slot": 2, "st": int(row["skill2_type"]), "id": int(row["skill2_id"]), "name_en": R.skill_name(row["skill2_type"], row["skill2_id"])},
        ],
        "testcase_attribute_alloc": expected_stat_alloc,
        "_cite": "data/csv/HeroInfo.csv:%d" % fr,
    }


def prop_block(pid, slot_hint=""):
    rowpair = prop_by_id.get(str(pid))
    if not rowpair:
        return {"FLAG": "NOT_FOUND", "prop_id": pid}
    row, fr = rowpair
    return {
        "prop_id": int(pid),
        "name_en": R.prop_name(pid),
        "rare": row.get("rare"),
        "type": row.get("type"),
        "PosType": row.get("PosType"),
        "effect_raw": row.get("Effect"),
        "effect_decoded": R.expand_effects(row.get("Effect")),
        "value": row.get("Value"),
        "slot_hint": slot_hint,
        "_cite": "data/csv/PropInfo.csv:%d" % fr,
    }


# Build a name -> equipment item index from gear.json (with slot + set membership)
eq_idx = {}
for slot_id, info in gear["equipment"].items():
    for it in info["items"]:
        eq_idx.setdefault(it["name"].lower(), []).append((info["slot_name"], it))
for side in ("left", "right"):
    acc = gear["accessories"].get(side, {})
    for it in acc.get("items", []):
        eq_idx.setdefault(it["name"].lower(), []).append(("Accessory", it))

set_by_id = {sb["set_id"]: sb for sb in gear["set_bonuses"]}


def equip_block(name, slot_constraint=None, set_filter=None, rarity=None):
    hits = eq_idx.get(name.lower(), [])
    cand = []
    for slot, it in hits:
        if slot_constraint and slot != slot_constraint:
            continue
        if set_filter is not None and it.get("set_id") != set_filter:
            continue
        if rarity is not None and it.get("rarity") != rarity:
            continue
        cand.append((slot, it))
    if not cand:
        # fuzzy
        for nm, lst in eq_idx.items():
            if name.lower() in nm:
                for slot, it in lst:
                    if slot_constraint and slot != slot_constraint:
                        continue
                    if set_filter is not None and it.get("set_id") != set_filter:
                        continue
                    if rarity is not None and it.get("rarity") != rarity:
                        continue
                    cand.append((slot, it))
    if not cand:
        return {"FLAG": "NOT_FOUND", "requested": name}
    slot, it = cand[0]
    sid = it.get("set_id")
    out = {
        "prop_id": int(it["id"]),
        "name_en": it["name"],
        "slot": slot,
        "rarity": it.get("rarity"),
        "power": it.get("power"),
        "set_id": sid,
        "set_name": set_by_id.get(sid, {}).get("set_name") if sid else None,
        "effects": [e.get("display") for e in it.get("effects", [])],
    }
    if len(cand) > 1:
        out["_other_tiers"] = [{"prop_id": int(c[1]["id"]), "rarity": c[1].get("rarity"), "set_id": c[1].get("set_id")} for c in cand[1:]]
    return out


# ------------------------------------------------------------------ HEROES
heroes = {
    "Patra": hero_block(60, "Patra", "+229 ATK"),
    "Rhea": hero_block(40, "Rhea", "+229 DEF"),
    "Aguria_Sp": hero_block(98, "Aguria · Sp", "+229 ATK"),
    "Satoru": hero_block(97, "Satoru", "+229 ATK SPD"),
    "Slider_Sp": hero_block(66, "Slider · Sp", "+229 DES"),
}
# base counterparts of SP variants (for reference)
heroes["_base_counterparts"] = {
    "Aguria_base": hero_block(95, "Aguria (base, NOT in testcase)", "-"),
    "Slider_base": hero_block(16, "Slider (base, NOT in testcase)", "-"),
}
heroes["_sp_variant_note"] = (
    "SP variants are SEPARATE HeroInfo ids from the base hero: "
    "Aguria=95 vs Aguria·Sp=98; Slider=16 vs Slider·Sp=66. "
    "They have different stars/RST/skill kits. (HeroInfo.csv)"
)

# ------------------------------------------------------------------ SKILLS
# name -> (st,id, classification). Classification per where it sits in the build.
skill_map = [
    ("Ghost Bone", "2", "81", "main (Patra)"),
    ("Bone Blade", "2", "144", "modular (Patra) + rune"),
    ("Star Shield", "1", "26", "main (Rhea)"),
    ("Sky Tear Arrow", "1", "76", "modular (Rhea)"),
    ("Unbounded", "1", "49", "modular (Rhea); also Satoru default modular slot1"),
    ("Knight Creed", "2", "110", "modular (enemy Rhea) + rune"),
    ("Field Therapy", "1", "46", "skill-stone (Slider·Sp & enemy Rhea); also modular"),
    ("Swift Thrust", "2", "111", "main (Aguria·Sp)"),
    ("Evil Fruit", "2", "101", "modular (Aguria·Sp) + rune"),
    ("Tactical Burst", "3", "26", "passive modular (Patra & Aguria·Sp)"),
    ("Sacred Feather", "3", "28", "passive skill-stone (Aguria·Sp)"),
    ("Gray World", "1", "52", "main (Satoru)"),
    ("Piety", "1", "56", "ALIAS->'Devout'; skill-stone purify (Satoru & Slider·Sp)"),
    ("Cocoon Silence", "2", "99", "modular (Satoru) + rune"),
    ("Green Tea", "2", "59", "skill-stone (Satoru)"),
    ("Dark Arrive", "1", "42", "main (Slider·Sp)"),
    ("Noise", "1", "32", "modular (Slider·Sp)"),
    ("Counterattack", "1", "9", "passive component of Reactive Block trigger"),
    ("Reactive Block", "3", "16", "passive skill-stone (Rhea); 'Reactive' is the short name"),
    ("Magic Spear", "2", "125", "skill-stone (Patra)"),
    ("Healing Bell", "2", "58", "rune (Rhea & Slider·Sp)"),
    ("Reactive", "3", "16", "ALIAS of 'Reactive Block' (skill-stone, Rhea)"),
    ("Elf Deer", "1", "58", "skill-stone (enemy Rhea)"),
]
skills = {}
for name, st, sid, cls in skill_map:
    b = skill_block(st, sid, cls)
    b["testcase_name"] = name
    skills[name] = b
skills["Piety"]["FLAG_ALIAS"] = (
    "No skill named 'Piety' exists in NewSkillInfo. Behaviour in log "
    "(purify 2 troops, first 3 rounds) matches 'Devout' 1_56 exactly. "
    "Treated as a display alias. VERIFY in-game."
)
skills["Reactive"]["FLAG_ALIAS"] = "Same skill as 'Reactive Block' 3_16 (short form)."

# ------------------------------------------------------------------ SKILL STONES
# Skill stones simply equip a NewSkillInfo skill whose SkillStone flag == 1.
stone_names = {
    "Elf Deer": ("1", "58"),
    "Sacred Feather": ("3", "28"),
    "Green Tea": ("2", "59"),
    "Magic Spear": ("2", "125"),
    "Reactive": ("3", "16"),
    "Field Therapy": ("1", "46"),
}
skill_stones = {}
for name, (st, sid) in stone_names.items():
    row = skill_by_key.get((st, sid))
    blk = skill_block(st, sid, "skill-stone")
    blk["testcase_name"] = name
    blk["is_skill_stone_eligible"] = (row[0].get("SkillStone") == "1") if row else None
    skill_stones[name] = blk

# ------------------------------------------------------------------ RELICS
relic_by_name = {hr["name"]: hr for hr in gear["hero_relics"]}
relic_requests = {
    "Rhea Relic": "Rhea Relic",
    "Aguria SP Relic": "Aguria·Sp Relic",
    "Satoru Relic": "Satoru Relic",
    "Patra SP Relic": "Patra Relic",        # testcase says 'Patra SP' but Patra has no SP variant
    "Slider SP Relic": "Slider·Sp Relic",
}
relics = {}
for req, catalog_name in relic_requests.items():
    hr = relic_by_name.get(catalog_name)
    if not hr:
        relics[req] = {"FLAG": "NOT_FOUND", "looked_for": catalog_name}
    else:
        entry = dict(hr)
        entry["testcase_name"] = req
        if req == "Patra SP Relic":
            entry["FLAG_DISCREPANCY"] = (
                "Testcase says 'Patra SP Relic' but no Patra SP hero exists; "
                "only Patra (id 60) with relic 20075 'Patra Relic'. Resolved to that."
            )
        relics[req] = entry

# ------------------------------------------------------------------ RUNES
rune_by_skill = {}
for ru in gear["runes"]:
    rune_by_skill[ru["boosted_skill"]["skill_name"]] = ru
rune_names = ["Knight Creed", "Evil Fruit", "Cocoon Silence", "Bone Blade", "Healing Bell"]
runes = {}
for nm in rune_names:
    ru = rune_by_skill.get(nm)
    runes[nm] = ({"FLAG": "NOT_FOUND", "looked_for": nm} if not ru else dict(ru, testcase_name=nm))

# ------------------------------------------------------------------ MAGIC MESSENGERS
mm_ids = {"Snow Fox": "3628", "Swift Fox": "3624", "Snowvine Cat": "3604", "Ice Shark": "3636"}
magic_messengers = {}
for nm, pid in mm_ids.items():
    blk = prop_block(pid, "Magic Messenger (slot 11)")
    blk["testcase_name"] = nm + " (T6)"
    magic_messengers[nm] = blk
magic_messengers["_system_note"] = (
    "Magic Messengers = PropInfo PosType 11, type 3 (49 rows total, IDs 3601-3649, "
    "tiers T3-T6). Each occupies the 11th hero gear slot (gen_gear slot_enum). "
    "Effect string uses the EntryEffect namespace (NOT skill-buff): all grant flat "
    "Hero ATK/DEF/DES + Hero ATK Spd, plus one conditional combat modifier at T4+: "
    "code 46=PVE DMG Dealt +%, 48=PVE DMG Taken Reduced %, 131=Equip Tactical Skill "
    "Activation Prob %, 132=Equip Pursuit Skill Activation Prob %. T6 grants +25 ATK-stat "
    "+60 ATK Spd + an 8%/4% conditional. NOT modeled in gear.json -> NEW SYSTEM to add. "
    "(PropInfo.csv PosType==11; EntryEffect.csv codes verified.)"
)

# ------------------------------------------------------------------ EQUIPMENT
equipment_requests = [
    ("Night's Sword", "Weapon", None, None),
    ("Day's Robe", "Armor", None, None),
    ("Fanatical Shorts", "Pants", None, None),
    ("Day's Helmet", "Helmet", None, None),
    ("Fanatical Bracers", "Bracers", None, None),
    ("Night's Boots", "Boots", None, None),
    ("Light Winged Dagger", "Accessory", None, None),
    ("Aegis", "Accessory", None, None),
    ("Light Sword", "Weapon", None, None),
    ("Abyss Armor", "Armor", None, None),
    ("Abyss Pants", "Pants", None, None),
    ("Streamer Helmet", "Helmet", None, None),
    ("Cool Bracers", "Bracers", None, None),
    ("Cool Boots", "Boots", None, None),
    ("Fate (axe)", "Weapon", "28", None),
    ("Fate (armor)", "Armor", "28", None),
    ("Fate (shorts)", "Pants", "28", None),
    ("Fate (helmet)", "Helmet", "28", None),
    ("Fate (bracers)", "Bracers", "28", None),
    ("Fate (boots)", "Boots", "28", None),
    ("Witch's Contract", "Accessory", None, None),
]
equipment = {}
for label, slot, setf, rar in equipment_requests:
    lookup = label.split(" (")[0]  # 'Fate'
    blk = equip_block(lookup, slot_constraint=slot, set_filter=setf, rarity=rar)
    blk["testcase_label"] = label
    equipment[label] = blk
equipment["_fate_set_bonus"] = {
    "set_id": "28",
    "set_name": "Fate",
    "three_piece": set_by_id.get("28", {}).get("three_piece_display"),
    "six_piece": set_by_id.get("28", {}).get("six_piece_display"),
    "note": "Slider·Sp wears full 6pc Fate (Chariot set) -> gets both 3pc + 6pc bonus. RST 4 = Chariot/Siege.",
}
equipment["_set_note"] = (
    "Night's/Day's/Fanatical pieces are PvE-oriented (DMG codes 46/48); "
    "Light/Abyss/Streamer/Cool are PvP-oriented (codes 47/49). None of these "
    "carry a set_id (set_id=null) so they grant no set bonus; only Fate (set 28) does."
)

# ------------------------------------------------------------------ OUTPUT
doc = {
    "_about": "Resolution of every named entity in notes/sim simulatorTestCase to game-data ids + decoded effects.",
    "_sources": [
        "input: simulatorTestCase battle log (player-supplied)",
        "data/csv/HeroInfo.csv, NewSkillInfo.csv, PropInfo.csv, EntryEffect.csv",
        "data/sim/heroes.json, skills.json, gear.json (already-decoded layers)",
    ],
    "_hard_rules": "CSV read utf-8-sig DictReader; ensure_ascii=False; file:row cites; UNKNOWN_SERVER_SIDE for hidden formula.",
    "_flags_summary": [
        "Magic Messengers: NEW SYSTEM, not in gear.json (PropInfo PosType 11).",
        "'Piety' is not a skill name -> alias of 'Devout' 1_56 (behavior match).",
        "'Patra SP Relic': no Patra SP hero/relic exists -> resolved to 'Patra Relic' (20075).",
        "Satoru shown as 4-star in battle report but HeroInfo id 97 is 5-star.",
        "SP variants (Aguria·Sp 98, Slider·Sp 66) are distinct hero ids from base (95, 16).",
        "Combat damage formula = UNKNOWN_SERVER_SIDE.",
    ],
    "heroes": heroes,
    "skills": skills,
    "skill_stones": skill_stones,
    "relics": relics,
    "runes": runes,
    "magic_messengers": magic_messengers,
    "equipment": equipment,
}

outp = os.path.join(ROOT, "data", "sim", "testcase_entities.json")
with io.open(outp, "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, indent=2)

# concise stdout (ASCII only) ----------------------------------------------
def count_flags(o, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            if k.startswith("FLAG"):
                acc.append(v if isinstance(v, str) else str(v))
            count_flags(v, acc)
    elif isinstance(o, list):
        for v in o:
            count_flags(v, acc)
flags = []
count_flags(doc, flags)
print("WROTE", outp)
print("heroes:", len([k for k in heroes if not k.startswith("_")]))
print("skills:", len(skills), "skill_stones:", len(skill_stones))
print("relics:", len(relics), "runes:", len(runes))
print("magic_messengers:", len([k for k in magic_messengers if not k.startswith("_")]))
print("equipment:", len([k for k in equipment if not k.startswith("_")]))
print("inline FLAG markers:", len(flags))
