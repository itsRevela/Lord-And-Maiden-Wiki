"""Generate data/sim/troops_meta.json from the verified game CSVs.

HARD RULES obeyed:
- All CSVs parsed with csv.DictReader + encoding='utf-8-sig'.
- No CJK printed to stdout; everything is written to the UTF-8 JSON file.
- Every value is read from a CSV cell or a cited decompiled line; nothing invented.
- json.dump(..., ensure_ascii=False, indent=2).

Sources (file:row are DictReader data-row indices; file line = row+2):
  data/csv/SoldierInfo.csv      (4 types x 6 tiers)
  data/csv/TroopsEffect.csv     (type 1 = soldier combos, type 2 = race combos)
  data/csv/GoodFeel.csv         (affection lv 0..11)
  data/csv/HeroTalent.csv       (5 TalentTypes, lv 0..25)
  data/csv/Tips.csv row Id=350  (restraint triangle + -25%)
  data/csv/Language_SysTip.csv  rows 289/304 (restraint text)
  decompiled eb46ed1b3cbb: 10428,17380-17392,171702-171714 (RST=SoldierT),
    10459-10477 & 80892-80916 (RST default attr split), 85893-85910 (talent cum sum),
    85917 (max awaken points = Rare*10), 35835-35954 (GetBuffName: talent attr namespace),
    9056 (GetSoldierName), 7857 (GetHeroRaceDesTip).
"""
import os, csv, json
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(ROOT, "data", "csv")
OUT = os.path.join(ROOT, "data", "sim", "troops_meta.json")


def load(name):
    with open(os.path.join(CSV, name + ".csv"), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


SOLDIER_TYPE = {1: "Infantry", 2: "Archer", 3: "Cavalry", 4: "Chariot"}
RACE = {1: "Human", 2: "Orc", 3: "Elf"}

# --- 1. troops ----------------------------------------------------------------
def build_troops():
    rows = load("SoldierInfo")
    by_type = defaultdict(list)
    stat_keys = ["attack", "defense", "ruin", "health",
                 "movement_speed", "load", "power"]
    for r in rows:
        by_type[int(r["type"])].append(r)
    troops = {}
    for t in (1, 2, 3, 4):
        tiers_rows = sorted(by_type[t], key=lambda r: int(r["level"]))
        max_tier = max(int(r["level"]) for r in tiers_rows)
        tiers = []
        for r in tiers_rows:
            lv = int(r["level"])
            tiers.append({
                "tier": lv,
                "label": "T%d" % lv,
                "is_max_tier": lv == max_tier,
                "attack": int(r["attack"]),
                "defense": int(r["defense"]),
                "ruin": int(r["ruin"]),
                "health": int(r["health"]),
                "movement_speed": int(r["movement_speed"]),
                "load": int(r["load"]),
                "power": int(r["power"]),
            })
        t6 = [x for x in tiers if x["is_max_tier"]][0]
        troops[str(t)] = {
            "type_id": t,
            "type_name_en": SOLDIER_TYPE[t],
            "max_tier": max_tier,
            "max_tier_label": "T%d" % max_tier,
            "max_tier_stats": {k: t6[k] for k in stat_keys},
            "tiers": tiers,
        }
    return troops


# --- 2 & 3. combinations ------------------------------------------------------
def decode_addtion(addtion):
    """TroopsEffect addtion: id_value pairs joined by '+'. ids are the
    EntryEffect namespace; soldier % (25/30/35/40/45) use Size=10000 so a raw
    value of 500 = 5%, 1000 = 10%. Hero stats (50/51/52/53) are flat (Size=1).
    Returns a list of {effect_id, raw_value, ...} read straight from the cell."""
    SOLDIER_PCT = {25: "Soldier HP", 30: "Soldier ATK", 35: "Soldier DEF",
                   40: "Soldier DES", 45: "Soldier March Spd"}
    HERO_FLAT = {50: "Hero ATK Spd", 51: "Hero ATK", 52: "Hero DEF",
                 53: "Hero DES", 54: "Hero Soldiers Quantity"}
    out = []
    for tok in addtion.split("+"):
        eid_s, _, val_s = tok.partition("_")
        eid = int(eid_s)
        raw = int(val_s)
        if eid in SOLDIER_PCT:
            out.append({"effect_id": eid, "attr_en": SOLDIER_PCT[eid],
                        "kind": "soldier_percent", "raw_value": raw,
                        "percent": raw / 10000.0 * 100.0})
        elif eid in HERO_FLAT:
            out.append({"effect_id": eid, "attr_en": HERO_FLAT[eid],
                        "kind": "hero_flat", "raw_value": raw, "flat": raw})
        else:
            out.append({"effect_id": eid, "attr_en": "Attr#%d" % eid,
                        "kind": "unknown", "raw_value": raw})
    return out


def build_combinations():
    rows = load("TroopsEffect")
    soldier = {}   # per soldier type -> {basic, advanced}
    race = {}      # per race -> {basic, advanced}
    for r in rows:
        ttype = int(r["type"])
        cond = int(r["condition"])
        number = int(r["number"])
        entry = {
            "name_en": r["name_en"],
            "trigger_count": number,            # heroes of that type/race in the 3-hero team
            "tier": "Basic" if number == 2 else "Advanced",
            "addtion_raw": r["addtion"],
            "addtion_des_en": r["addtion_des_en"],
            "effects": decode_addtion(r["addtion"]),
        }
        if ttype == 1:                          # soldier-type combination
            key = str(cond)                     # condition == SoldierInfo.type
            soldier.setdefault(key, {"soldier_type_id": cond,
                                     "soldier_type_en": SOLDIER_TYPE[cond]})
            soldier[key]["basic" if number == 2 else "advanced"] = entry
        elif ttype == 2:                        # race combination
            key = str(cond)                     # condition == HeroInfo.Type (race)
            race.setdefault(key, {"race_id": cond, "race_en": RACE[cond]})
            race[key]["basic" if number == 2 else "advanced"] = entry
    return soldier, race


# --- 4. affection -------------------------------------------------------------
def build_affection():
    rows = load("GoodFeel")
    curve = []
    for r in rows:
        curve.append({
            "level": int(r["lv"]),
            "all_attributes_bonus": int(r["value"]),
            "des_en": r["des_en"],
            "up_lv_exp": int(r["upLvExp"]),
        })
    mx = max(curve, key=lambda c: c["level"])
    return {
        "stat_affected": "Hero All Attributes (ATK + DEF + DES/Ruin + ATK Spd)",
        "max_level": mx["level"],
        "max_bonus": mx["all_attributes_bonus"],
        "curve": curve,
    }


# --- 5. talents ---------------------------------------------------------------
# Talent Effect namespace (NOT EntryEffect). Verified vs each row's Des/Des_en and
# the soldier-attr name switch in GetBuffName (decompiled:35835-35954):
#   59 = Soldiers Quantity (flat)   [Des '{带兵数量}', Des_en 'Soldiers Quantity']
#   53 = Infantry HP    (GetBuffName case 53 '{步兵} {生命}')   percent (raw is decimal)
#   19 = Archer ATK     (GetBuffName case 19 '{弓兵} {攻击}')   percent
#   25 = Cavalry DEF    (GetBuffName case 25 '{骑兵} {防御}')   percent
#   52 = Chariot DES    (GetBuffName case 52 '{战车} {破坏}')   percent
TALENT_EFFECT_NS = {
    59: {"attr_en": "Soldiers Quantity", "kind": "flat"},
    53: {"attr_en": "Infantry HP", "kind": "percent"},
    19: {"attr_en": "Archer ATK", "kind": "percent"},
    25: {"attr_en": "Cavalry DEF", "kind": "percent"},
    52: {"attr_en": "Chariot DES", "kind": "percent"},
}


def build_talents():
    rows = load("HeroTalent")
    g = defaultdict(list)
    for r in rows:
        g[int(r["TalentType"])].append(r)
    talents = {}
    for tt in sorted(g):
        rs = sorted(g[tt], key=lambda r: int(r["TalentLv"]))
        max_lv = max(int(r["TalentLv"]) for r in rs)
        # cumulative sum of Effect value across all levels 1..max (lv0 is '0')
        eids = set()
        total = 0.0
        per_level = []
        for r in rs:
            lv = int(r["TalentLv"])
            eff = r["Effect"]
            if eff and eff != "0" and "_" in eff:
                eid_s, _, val_s = eff.partition("_")
                eid = int(eid_s)
                val = float(val_s)
                eids.add(eid)
            else:
                eid, val = None, 0.0
            total += val
            per_level.append({
                "level": lv, "effect_id": eid, "effect_value": val,
                "need_point": int(r["NeedPoint"]), "des_en": r["Des_en"],
            })
        assert len(eids) <= 1, "talent type %d mixes effect ids %s" % (tt, eids)
        eid = next(iter(eids))
        ns = TALENT_EFFECT_NS[eid]
        if ns["kind"] == "flat":
            maxed = {"flat": round(total)}
            maxed_display = "%s +%d" % (ns["attr_en"], round(total))
        else:
            maxed = {"percent": round(total * 100.0, 2)}
            maxed_display = "%s +%g%%" % (ns["attr_en"], round(total * 100.0, 6))
        talents[str(tt)] = {
            "talent_type": tt,
            "name_en": rs[0]["Name_en"],
            "max_level": max_lv,
            "effect_id": eid,
            "effect_namespace_attr_en": ns["attr_en"],
            "effect_kind": ns["kind"],
            "maxed_cumulative": maxed,
            "maxed_display_en": maxed_display,
            "total_points_to_max": sum(int(r["NeedPoint"]) for r in rs),
            "per_level": per_level,
        }
    return talents


def build():
    troops = build_troops()
    soldier_combos, race_combos = build_combinations()
    affection = build_affection()
    talents = build_talents()

    meta = {
        "_about": "Troops, team-composition bonuses, affection, talents, and the "
                  "soldier restraint triangle for the Lord & Maiden battle simulator. "
                  "All numbers read from data/csv/*.csv; mechanics cited to the "
                  "decompiled client. Combat damage itself is server-authoritative.",
        "enums": {
            "soldier_type": {str(k): v for k, v in SOLDIER_TYPE.items()},
            "race": {str(k): v for k, v in RACE.items()},
            "_source": "GetSoldierName decompiled:9056; GetHeroRaceDesTip decompiled:7857",
        },
        "troops": troops,
        "soldier_combinations": {
            "_about": "TroopsEffect type 1. Trigger = how many heroes in the 3-hero "
                      "team field this soldier type. 2 = Basic, 3 = Advanced. A hero's "
                      "soldier type = its HeroInfo.RST (decompiled:10428,17380).",
            "_stacking": "Basic (2-of-type) and Advanced (3-of-type) are mutually "
                         "exclusive thresholds keyed by TroopsEffect.number (2 vs 3); "
                         "at 3 matching heroes only the Advanced row applies.",
            "by_soldier_type": soldier_combos,
            "_source": "data/csv/TroopsEffect.csv rows 0-7 (type=1)",
        },
        "race_combinations": {
            "_about": "TroopsEffect type 2. Trigger = how many heroes in the 3-hero "
                      "team are of this race (HeroInfo.Type). 'All Attributes' = the 4 "
                      "hero stats ATK(51)+DEF(52)+DES(53)+ATK-Spd(50), each +5 (Basic) "
                      "or +10 (Advanced).",
            "_stacking": "Basic (2-of-race, +5) and Advanced (3-of-race, +10) are "
                         "mutually exclusive thresholds keyed by number (2 vs 3); with "
                         "3 same-race heroes only the +10 Advanced row applies, NOT "
                         "+5 and +10 together.",
            "by_race": race_combos,
            "_source": "data/csv/TroopsEffect.csv rows 8-13 (type=2)",
        },
        "affection": affection,
        "talents": {
            "_about": "HeroTalent awakening. Each TalentType levels 1..25; the hero's "
                      "displayed bonus is the cumulative sum of every awakened level's "
                      "Effect value (decompiled:85893-85910). Type 1 (Commander) is a "
                      "flat Soldiers-Quantity bonus; types 2-5 are percent soldier-stat "
                      "bonuses for that soldier type.",
            "_namespace": "HeroTalent.Effect uses a talent-internal id space, NOT the "
                          "EntryEffect catalog. 59=Soldiers Quantity (flat); 53=Infantry "
                          "HP, 19=Archer ATK, 25=Cavalry DEF, 52=Chariot DES (percent, "
                          "raw value is already a decimal fraction e.g. 0.06=6%). Names "
                          "verified per-row via Des/Des_en and the soldier-attr switch "
                          "GetBuffName decompiled:35835-35954 (case 19/25/52/53). NOTE "
                          "the overlap trap: EntryEffect 53=Hero DES but Talent 53="
                          "Infantry HP.",
            "_max_awaken_points": "A hero's total awaken points = Rare*10 "
                                  "(decompiled:85917). Maxing ALL 5 talents to lv25 needs "
                                  "125 points, so even a 6-star (60 pts) cannot max every "
                                  "talent; the per-type maxed_cumulative below is the cap "
                                  "if that single talent is taken to lv25.",
            "by_type": talents,
            "_source": "data/csv/HeroTalent.csv (130 rows)",
        },
        "restraint": {
            "_about": "RST (HeroInfo.RST) is the hero's commanded soldier type: the "
                      "client sets hero.SoldierT = heroInfo.RST (decompiled:10428, "
                      "17380-17392, 171702-171714). Values map 1=Infantry, 2=Archer, "
                      "3=Cavalry, 4=Chariot (same space as SoldierInfo.type). RST also "
                      "drives the hero's default attribute-point split when RPoint is "
                      "empty (decompiled:10459-10477, 80892-80916): RST1 favors "
                      "DEF+Speed, RST2 ATK+Ruin, RST3 DEF+ATK, RST4 Ruin+ATK.",
            "triangle": {
                "order": ["Infantry", "Archer", "Cavalry"],
                "restrains": {"Infantry": "Archer", "Archer": "Cavalry",
                              "Cavalry": "Infantry"},
                "note": "Cyclic: Infantry->Archer->Cavalry->Infantry. The restrainer's "
                        "soldiers are at advantage; the restrained side's soldiers deal "
                        "reduced damage. Chariot (type 4) has NO restraint relationship.",
                "no_relationship_types": ["Chariot"],
            },
            "restrained_damage_modifier": {
                "value_percent": -25,
                "applies_to": "outgoing damage of the restrained (disadvantaged) "
                              "soldiers",
                "text_en": "When Soldiers Are Restrained, Damage Dealt Is Reduced By "
                           "25%.",
                "source": "data/csv/Tips.csv row Id=350 (data-row 17); "
                          "data/csv/Language_SysTip.csv data-rows 289 & 304",
                "application": "UNKNOWN_SERVER_SIDE",
                "application_note": "The -25% is a stated rule; the client never "
                                    "computes it. Battle damage arrives pre-resolved as "
                                    "BehaviourRet.RetVal from the server "
                                    "(decompiled:19506). No client-side soldier-type "
                                    "damage multiplier exists (no 0.75 factor tied to "
                                    "SoldierT in combat code).",
            },
        },
        "preferred_soldier": {
            "_about": "There is no separate selectable 'preferred soldier' bonus. A "
                      "hero is locked to the single soldier type given by its RST "
                      "(hero.SoldierT = heroInfo.RST). The only RST-linked effects found "
                      "client-side are: (a) it sets which soldier type the hero fields, "
                      "and (b) it sets the default attribute-point distribution when "
                      "RPoint is empty (see restraint._about). The per-soldier-type "
                      "talents (talents.by_type 2-5) are the closest thing to a "
                      "'preferred soldier' stat boost, but they are independent of RST "
                      "and apply to whichever soldier type the talent names.",
            "matching_bonus_magnitude": "UNKNOWN_SERVER_SIDE",
            "matching_bonus_note": "No client-side stat bonus is granted simply for a "
                                   "hero using its RST-matching soldier type beyond "
                                   "fielding that type. Searched decompiled + "
                                   "Language_SysTip; no 'preferred/adept/suited soldier' "
                                   "bonus string or multiplier exists. If any such bonus "
                                   "is applied, it is resolved server-side.",
        },
    }
    return meta


def main():
    meta = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    # ASCII-only confirmation to stdout
    print("wrote", OUT)
    print("troops:", len(meta["troops"]),
          "soldier_combos:", len(meta["soldier_combinations"]["by_soldier_type"]),
          "race_combos:", len(meta["race_combinations"]["by_race"]),
          "talents:", len(meta["talents"]["by_type"]),
          "affection_levels:", len(meta["affection"]["curve"]))
    t = meta["talents"]["by_type"]
    for k in sorted(t, key=int):
        print("  talent", k, t[k]["name_en"], "->", t[k]["maxed_display_en"])


if __name__ == "__main__":
    main()
