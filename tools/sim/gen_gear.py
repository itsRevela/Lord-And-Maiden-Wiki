"""Generate data/sim/gear.json — MAXED numeric values for everything a hero equips.

Source of truth: data/csv/PropInfo.csv (gear=type3, relics=type5, runes=type9),
EntryEffect.csv (gear-stat namespace), SkillAwake.csv (skill-awaken / buff namespace).
Cross-checked against the already-verified wiki pages (Equipment/Relics/Runes/
Skill-Stones/Hero-Advancement). HARD RULES from notes/sim/_AGENT_CONTEXT.md apply:
- CSV via csv.DictReader + utf-8-sig (resolver.load does this).
- never print CJK; write strict UTF-8 JSON only.
- never guess; server-side-only values get "UNKNOWN_SERVER_SIDE".

Decode evidence (decompiled eb46ed1b3cbb.cs):
- GetEquipPosDes (l.8710): slot enum 1 Weapon,2 Armor,3 Pants,4 Helmet,5 Bracers,
  6 Boots,7 Left Acc,8 Right Acc,9 Relic,10 Rune,11 Magic Messenger.
- PropDes type3 (l.8766): Effect -> GetEntryDes(ToEntryList) = EntryEffect decode;
  timeinfo "setId$3pcEffect+6pcEffect"; a piece counts toward a set if its timeinfo
  setId matches; 3/6 same-set pieces grant content/content2 (both EntryEffect lists).
- type5 (l.8792): relic levels sorted by Value; rows share PosType = the OWNING HERO id;
  gotoPanel = "ST_Num" of the Talent skill it enhances; Score = Rare*Value*1800.
- type9 (l.8802): rune bound skill = gotoPanel "ST_Num"; rows grouped by gotoPanel,
  sorted by Value (=level); Effect "45_<frac>" where here 45 = Skill Trigger Probability.
"""
import os
import sys
import csv
import json
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "wikigen"))
from resolver import Resolver, clean, fmt_num, SKILL_TYPE_NAME  # noqa: E402

R = Resolver()

GEAR_SLOT = {"1": "Weapon", "2": "Armor", "3": "Pants", "4": "Helmet",
             "5": "Bracers", "6": "Boots", "7": "Left Accessory",
             "8": "Right Accessory", "9": "Relic", "10": "Rune",
             "11": "Magic Messenger"}


def gear_rows():
    return [r for r in R.prop.values() if r.get("type") == "3"]


def decode_effect_list(s):
    """One Effect/timeinfo entry-list 'eid_val+eid_val' -> structured + display.
    Uses EntryEffect (DataType 1=flat, 2=percent val/Size*100)."""
    out = []
    s = (s or "").strip()
    if not s or s == "0":
        return out
    for tok in s.split("+"):
        tok = tok.strip()
        if "_" not in tok:
            continue
        eid, _, val = tok.partition("_")
        meta = R.entry.get(eid.strip())
        if not meta:
            out.append({"effect_id": eid, "raw_value": val, "attr": "Attr#" + eid,
                        "kind": "unknown", "value": None, "display": R.effect_value(eid, val)})
            continue
        dtype = (meta.get("DataType") or "").strip()
        attr = clean(meta.get("Name_en") or meta.get("Name"))
        if dtype == "2":
            size = float(meta.get("Size") or "1") or 1.0
            pct = float(val) / size * 100.0
            out.append({"effect_id": eid, "raw_value": val, "attr": attr,
                        "kind": "percent", "value": round(pct, 4),
                        "display": R.effect_value(eid, val)})
        else:
            try:
                fv = float(val)
                fv = int(fv) if fv == int(fv) else fv
            except ValueError:
                fv = val
            out.append({"effect_id": eid, "raw_value": val, "attr": attr,
                        "kind": "flat", "value": fv,
                        "display": R.effect_value(eid, val)})
    return out


# --- contribution tagging (which battle channel an attr feeds) ---
# Per EntryEffect.csv + _AGENT_CONTEXT verified enums.
ATK_IDS = {"6", "7", "8", "9", "10", "26", "27", "28", "29", "30", "51"}
DEF_IDS = {"11", "12", "13", "14", "15", "31", "32", "33", "34", "35", "52"}
RUIN_IDS = {"16", "17", "18", "19", "20", "36", "37", "38", "39", "40", "53"}
HP_IDS = {"1", "2", "3", "4", "5", "21", "22", "23", "24", "25"}
SPEED_IDS = {"50"}                                  # Hero ATK Spd
MARCH_IDS = {"41", "42", "43", "44", "45"}          # March speed (out-of-combat positioning)
SOLDIERS_IDS = {"54"}                               # Hero Soldiers Quantity
DMG_CHANNEL_IDS = {"46", "47", "48", "49"}          # PVE/PVP dmg dealt/taken multipliers
PROC_IDS = {"131", "132"}                           # equip skill-activation probability


def channel_for(eid):
    eid = str(eid).strip()
    if eid in ATK_IDS:
        return "ATK"
    if eid in DEF_IDS:
        return "DEF"
    if eid in RUIN_IDS:
        return "Ruin"
    if eid in HP_IDS:
        return "Soldier_HP"
    if eid in SPEED_IDS:
        return "Speed"
    if eid in MARCH_IDS:
        return "March_Speed"
    if eid in SOLDIERS_IDS:
        return "Soldiers"
    if eid in DMG_CHANNEL_IDS:
        return "DMG_Multiplier"
    if eid in PROC_IDS:
        return "Skill_Proc"
    return "other"


def build_equipment():
    """type3 gear in the 6 armour slots (1-6) + Magic Messenger (11). Accessories
    (7,8) are returned by build_accessories. Each gear PropInfo row is already the
    fully-built tier (no per-row leveling) so its Effect IS the maxed value."""
    by_slot = collections.OrderedDict()
    for r in gear_rows():
        slot = r.get("PosType", "?")
        if slot in ("7", "8"):           # accessories handled separately
            continue
        by_slot.setdefault(slot, []).append(r)

    result = collections.OrderedDict()
    for slot in sorted(by_slot, key=lambda x: int(x) if x.isdigit() else 99):
        items = sorted(by_slot[slot], key=lambda r: (int(r.get("rare") or 0), int(r["id"])))
        rows = []
        for r in items:
            effs = decode_effect_list(r.get("Effect"))
            ti = (r.get("timeinfo") or "0").strip()
            set_id = ti.split("$")[0] if "$" in ti else None
            rows.append({
                "id": r["id"],
                "name": clean(r.get("name_en") or r.get("name")),
                "rarity": int(r.get("rare") or 0),
                "power": int(r.get("Value") or 0),
                "set_id": set_id,
                "effects": effs,
                "channels": sorted({channel_for(e["effect_id"]) for e in effs}),
            })
        result[slot] = {"slot_id": int(slot), "slot_name": GEAR_SLOT.get(slot, "Slot " + slot),
                        "items": rows}
    return result


def set_theme_name(names):
    toks = [n.split() for n in names if n]
    if not toks:
        return "Set"
    common = []
    for i in range(min(len(t) for t in toks)):
        w = toks[0][i]
        if all(len(t) > i and t[i] == w for t in toks):
            common.append(w)
        else:
            break
    return " ".join(common) or names[0]


def build_set_bonuses():
    """timeinfo 'setId$3pc+6pc'. Group gear by setId; decode both effect lists."""
    sets = collections.OrderedDict()
    for r in gear_rows():
        ti = (r.get("timeinfo") or "0").strip()
        if ti in ("0", "") or "$" not in ti:
            continue
        sid = ti.split("$")[0]
        s = sets.setdefault(sid, {"names": [], "tiers": collections.OrderedDict()})
        s["names"].append(clean(r.get("name_en") or r.get("name")))
        if ti not in s["tiers"]:
            p3, _, p6 = ti.split("$")[1].partition("+")
            s["tiers"][ti] = {
                "rarity": int(r.get("rare") or 0),
                "three_piece": decode_effect_list(p3),
                "six_piece": decode_effect_list(p6),
                "three_piece_display": R.expand_effects(p3),
                "six_piece_display": R.expand_effects(p6),
            }
    out = []
    for sid in sorted(sets, key=lambda x: int(x) if x.isdigit() else 0):
        name = set_theme_name(sets[sid]["names"])
        for tier in sets[sid]["tiers"].values():
            out.append({"set_id": sid, "set_name": name, **tier})
    return out


def build_accessories():
    """Left (slot7, offensive) & Right (slot8, defensive) accessories. No set bonus.
    Each row is its own maxed item (Effect = the final value)."""
    out = {"left": {"slot_id": 7, "items": []}, "right": {"slot_id": 8, "items": []}}
    for r in gear_rows():
        slot = r.get("PosType")
        if slot not in ("7", "8"):
            continue
        effs = decode_effect_list(r.get("Effect"))
        rec = {
            "id": r["id"],
            "name": clean(r.get("name_en") or r.get("name")),
            "rarity": int(r.get("rare") or 0),
            "power": int(r.get("Value") or 0),
            "effects": effs,
            "channels": sorted({channel_for(e["effect_id"]) for e in effs}),
        }
        out["left" if slot == "7" else "right"]["items"].append(rec)
    for side in out.values():
        side["items"].sort(key=lambda x: (x["rarity"], int(x["id"])))
    return out


def relic_effect_text(r):
    d = clean(r.get("des_en") or r.get("des") or "")
    return d.split(":", 1)[1].strip() if ":" in d else d   # drop "Talent Skill:" prefix


def build_hero_relics():
    """type5. PosType = owning hero id; gotoPanel = ST_Num of the enhanced Talent
    skill; rows are Lv1..max (Value=level). MAX = highest Value row.
    Effect numeric code is a SKILL-BUFF code (not EntryEffect); des_en is the
    authoritative readable bonus, so we surface des_en + the raw Effect token."""
    groups = collections.OrderedDict()
    for r in R.prop.values():
        if r.get("type") == "5":
            groups.setdefault(clean(r.get("name_en") or r.get("name")), []).append(r)

    relics = []
    for name, lvls in groups.items():
        lvls = sorted(lvls, key=lambda x: int(x.get("Value") or 0))
        top = lvls[-1]
        hero_id = top.get("PosType")
        gp = top.get("gotoPanel") or ""
        st, _, sid = gp.partition("_")
        # A relic Effect is one or more 'buffId_value' tokens joined by '+'. The buff-id
        # namespace is the SKILL-BUFF one (not EntryEffect); des_en is authoritative.
        raw_eff = (top.get("Effect") or "").strip()
        eff_tokens = []
        for tok in raw_eff.split("+"):
            bid, _, bval = tok.partition("_")
            if bid:
                eff_tokens.append({"buff_id": bid, "value": bval})
        relics.append({
            "relic_id": top["id"],
            "name": name,
            "hero": name.replace(" Relic", "").strip(),
            "hero_id": hero_id,
            "rarity": int(top.get("rare") or 0),
            "max_level": int(top.get("Value") or 0),
            "enhanced_skill": {
                "skill_type_id": st, "skill_id": sid,
                "skill_type": SKILL_TYPE_NAME.get(st, "Type " + st) if st else None,
                "skill_name": R.skill_name(st, sid) if st else None,
            },
            "raw_effect_max": raw_eff,
            "effect_tokens_max": eff_tokens,
            "max_bonus": relic_effect_text(top),
            "lv1_bonus": relic_effect_text(lvls[0]),
            "score_at_max": int(top.get("rare") or 0) * int(top.get("Value") or 0) * 1800,
            "level_up_material": "UNKNOWN_SERVER_SIDE (duplicate-relic count per level not in client)",
        })
    relics.sort(key=lambda x: (-x["rarity"], x["hero"].lower()))
    return relics


def build_runes():
    """type9. gotoPanel = ST_Num of the bound Tactical/Pursuit skill; rows Lv1..max
    (Value=level). Effect '45_<frac>' where (per client des_en and the task rule) 45 =
    Skill Trigger Probability. MAX = highest Value row. Trigger chance = frac*100 (%)."""
    groups = collections.OrderedDict()
    for r in R.prop.values():
        if r.get("type") == "9":
            groups.setdefault(r.get("gotoPanel"), []).append(r)

    def chance(r):
        v = (r.get("Effect") or "").partition("_")[2]
        try:
            return round(float(v) * 100, 4)
        except ValueError:
            return None

    runes = []
    for gp, lvls in groups.items():
        st, _, sid = (gp or "").partition("_")
        lvls = sorted(lvls, key=lambda x: int(x.get("Value") or 0))
        top = lvls[-1]
        sk = R.skill_full(st, sid)
        eff_id = (top.get("Effect") or "").partition("_")[0]
        runes.append({
            "rune_id": top["id"],
            "boosted_skill": {
                "skill_type_id": st, "skill_id": sid,
                "skill_type": SKILL_TYPE_NAME.get(st, "Type " + st),
                "skill_name": R.skill_name(st, sid),
            },
            "rarity": int(top.get("rare") or 0),
            "max_level": int(top.get("Value") or 0),
            "trigger_chance_lv1_pct": chance(lvls[0]),
            "trigger_chance_max_pct": chance(top),
            "effect_id": eff_id,                # 45 = Skill Trigger Probability (rune context)
            "effect_meaning": "Skill Trigger Probability",
            "skill_effect": clean(sk.get("Des_en") or sk.get("Des")) if sk else "UNKNOWN (skill not found)",
            "upgrade_material": "Runes-Fragment (exact count per level UNKNOWN_SERVER_SIDE)",
        })
    runes.sort(key=lambda x: (-x["rarity"], x["boosted_skill"]["skill_type"],
                              x["boosted_skill"]["skill_name"].lower()))
    return runes


def build_skill_awake():
    """SkillAwake.csv keyed by (skill_type, skill_id). 'Effecs' is CUMULATIVE per Lv
    (Lv4 = full Lv4 total, NOT an increment), in the SKILL-BUFF id namespace (NOT
    EntryEffect). MAX = highest Lv row. des_en is the authoritative readable.
    SkillAwake = the per-skill *Awaken* leveling track (shared by a hero's innate
    skills AND a skill-stone's granted skill); it is NOT the skill-stone item."""
    out = []
    for (st, sid), rows in R.awaken.items():
        rows = sorted(rows, key=lambda x: int(x["Lv"]))
        top = rows[-1]
        eff_id, _, eff_val = (top.get("Effecs") or "").partition("_")
        out.append({
            "skill_type_id": st,
            "skill_id": sid,
            "skill_type": SKILL_TYPE_NAME.get(st, "Type " + st),
            "skill_name": R.skill_name(st, sid),
            "max_level": int(top["Lv"]),
            "max_effecs_raw": top.get("Effecs"),
            "max_buff_id": eff_id or None,
            "max_buff_value": eff_val or None,
            "max_bonus": clean(top.get("des_en") or top.get("des")),
            "lv1_bonus": clean(rows[0].get("des_en") or rows[0].get("des")),
        })
    out.sort(key=lambda x: (int(x["skill_type_id"]), int(x["skill_id"])))
    return out


def main():
    data = collections.OrderedDict()
    data["_meta"] = {
        "source": "data/csv/PropInfo.csv, EntryEffect.csv, SkillAwake.csv",
        "generated_by": "tools/sim/gen_gear.py",
        "decode_evidence": "decompiled/eb46ed1b3cbb.cs GetEquipPosDes l.8710, GetPropDes l.8766-8818",
        "slot_enum": {str(k): v for k, v in sorted(GEAR_SLOT.items(), key=lambda x: int(x[0]))},
        "slots_per_hero": {GEAR_SLOT[k]: 1 for k in GEAR_SLOT},
        "notes": [
            "Each gear PropInfo row (type3) is a fully-built tier; its Effect string IS the maxed value for that tier.",
            "EntryEffect DataType 1=flat (+val), 2=percent (val/Size*100); Size=10000 for percent attrs.",
            "EffectType 45 = 'Soldier March Spd' in the gear/EntryEffect namespace, but for RUNES the client renders 45 as 'Skill Trigger Probability' (honored here).",
            "Relic/SkillAwake numeric codes are a SKILL-BUFF namespace (NOT EntryEffect); des_en is authoritative.",
            "Combat damage formula is server-authoritative (UNKNOWN_SERVER_SIDE); only inputs/rules are in the client.",
        ],
    }
    data["equipment"] = build_equipment()
    data["set_bonuses"] = build_set_bonuses()
    data["accessories"] = build_accessories()
    data["hero_relics"] = build_hero_relics()
    data["runes"] = build_runes()
    data["skill_awake"] = build_skill_awake()

    outdir = os.path.join(ROOT, "data", "sim")
    os.makedirs(outdir, exist_ok=True)
    outp = os.path.join(outdir, "gear.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # ASCII-only summary to stdout (no CJK).
    counts = {
        "equipment_slots": len(data["equipment"]),
        "equipment_items": sum(len(s["items"]) for s in data["equipment"].values()),
        "set_bonus_rows": len(data["set_bonuses"]),
        "left_acc": len(data["accessories"]["left"]["items"]),
        "right_acc": len(data["accessories"]["right"]["items"]),
        "hero_relics": len(data["hero_relics"]),
        "runes": len(data["runes"]),
        "skill_awake": len(data["skill_awake"]),
    }
    print("wrote", outp)
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
