# -*- coding: utf-8 -*-
"""Decode NewSkillInfo.csv into data/sim/skills.json.

12-token group layout (positions 0..11), used identically by the Effect, Buff
and Dbuff columns. One skill string is one-or-more 12-token groups joined by '+'.

  [0] actionOrBuffId : in the Effect column = action type (101 ATK / 102 heal /
                       121 purify / 122 dispel); otherwise a Buff.csv buffId.
  [1] fromRound      : starting round. 0/1 = from round 1, 4 = from round 4,
                       5 = from round 5 (verified vs Des_en round phrasing).
  [2] targetCategory : 0 = inherit action's target ("the target enemy"),
                       2 = enemy troops, 4 = our troops (multi), 6 = assist/protect
                       target, 7 = own/self, 10 = enemy commander.
  [3] targetCount    : number of targets (verified == "ATK N Enemy Troops").
  [4] triggerChance  : per-group apply/hit probability (1 = guaranteed). Drives
                       "Launch X-Y ATK" ranges and "NN% Probability" states.
  [5] coefficient    : DMG / healing coefficient (== InitVal at level 0 for the
                       primary action; reduced value for ReadyRound=1 skills).
  [6] flatMagnitude  : flat stat amount when [5]==0 (e.g. "ATK Reduced 11.4").
  [7] layers/minDur  : shield layers / hit count / min duration.
  [8] maxStacks      : max stack layers (Adversity "Up To 10 Layers" -> 10).
  [9] duration       : effect duration in rounds (0 = instant / whole battle).
  [10] flagA         : 1 on direct ATK/heal actions & some buffs; rendering flag.
  [11] affectedByAttr : 1 = magnitude scales with DEF/DES attribute, 0 = not.

Verified relationships (all 416 rows):
  ImpactBy == InitVal + UpVal*10  -> max skill level is 10; ImpactBy is the
  maxed value. Value at level L (1..10) = InitVal + L*UpVal (decompiled
  GetSkillUpDes, eb46ed1b3cbb.decompiled.cs:9940-9949).
  UpType in {1,5..8,19..40,43..47} renders as percent (*100%); else flat.
  UpType==45 -> the *trigger probability* scales with level (SkillP == ImpactBy).
  MaxUse = times the skill can be learned/equipped (NOT max level); MaxUse==0 =
  relic/innate, MaxUse>0 = awakenable (decompiled:133265).
  SkillStone==1 = eligible for a skill stone (generates 5 stone-level props,
  decompiled:171136-171164).
"""
import os, csv, io, json

# this file lives at <repo>/notes/sim/_gen_skills.py
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(ROOT, "data", "csv")

SKILL_TYPE_NAME = {"1": "Strategic", "2": "Tactical", "3": "Passive", "4": "Pursuit"}

ACTION_TYPE = {
    "101": "ATK Enemy",
    "102": "Heal / Restore Life",
    "121": "Purify (cleanse own harmful effects)",
    "122": "Dispel (remove enemy beneficial effects)",
}

TARGET_CATEGORY = {
    "0": "Inherit action target (the target enemy)",
    "2": "Enemy Troops",
    "4": "Our Troops",
    "6": "Assist / Protect target",
    "7": "Own / Self",
    "10": "Enemy Commander",
}


def uptype_is_percent(ut):
    """Client renders these UpType groups as a percentage (decompiled:9938)."""
    try:
        ut = int(ut)
    except (TypeError, ValueError):
        return False
    return ut == 1 or (5 <= ut <= 8) or (19 <= ut <= 40) or (43 <= ut <= 47)


# buffIds referenced by skills but absent from Buff.csv -> special combat
# mechanics whose exact behaviour is resolved server-side. Names inferred from
# the citing skills' own Des_en text (cited per id in skills.md).
SERVER_SIDE_BUFFS = {
    "72":  "Burn Detonation (settle remaining Burn DMG)",
    "112": "Disarm variant (prepared/special)",
    "141": "Disarm + Silence (combined control)",
    "151": "Chained Pursuit (extra pursuit trigger)",
    "152": "Pursuit Empower (carried pursuits 100% trigger)",
    "153": "Multi Pursuit (additional pursuits)",
    "156": "Curse DMG over time (Eternal Flame)",
}


def load(name):
    with open(os.path.join(CSV, name + ".csv"), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def clean(t):
    if t is None:
        return ""
    return t.replace("{", "").replace("}", "").replace("\n", " ").strip()


def main():
    skills = load("NewSkillInfo")
    buffrows = {r["buffId"]: r for r in load("Buff")}

    # Authoritative skill-name translation: the game's own Language_SkillName.csv,
    # keyed by the Simplified token (== NewSkillInfo.Name stripped of { }).  The
    # NewSkillInfo.Name_en column (and the merged localization.json) have DRIFTED for a
    # few skills -- e.g. 虔诚 is officially "Piety" but Name_en says "Devout", 谨慎
    # "Cautious" not "Prudent", 恐吓 "Intimidation" not "Skull", 守护之盾 "Guard Shield",
    # 狩猎 "Hunting".  Prefer the localization file so names match the in-game UI.
    _langname = {}
    for r in load("Language_SkillName"):
        simp = (r.get("Simplified_Text") or "").strip()
        en = (r.get("English_Text") or "").strip()
        if simp and en:
            _langname[simp] = en

    def official_name(r):
        tok = clean(r.get("Name"))                # braces stripped -> Simplified token
        return _langname.get(tok) or clean(r.get("Name_en")) or tok

    def buff_name(bid):
        r = buffrows.get(str(bid))
        if r:
            nm = clean(r.get("Name_en") or r.get("Name"))
            return nm or ("Buff#" + str(bid))
        return SERVER_SIDE_BUFFS.get(str(bid), "Buff#" + str(bid) + " (UNKNOWN_SERVER_SIDE)")

    def parse_groups(s):
        s = (s or "").strip()
        if s in ("0", ""):
            return []
        return [grp.split("_") for grp in s.split("+") if len(grp.split("_")) == 12]

    def num(x):
        try:
            f = float(x)
            return int(f) if f == int(f) else f
        except (TypeError, ValueError):
            return x

    def parse_effects(raw):
        """Render each 12-token group into a structured effect record."""
        recs = []
        for t in parse_groups(raw):
            aid = t[0]
            # 101/102/121/122 are actions wherever they appear (the Effect column
            # holds the primary action; the Buff column can also reference an ATK,
            # e.g. counterattack/pursuit). Everything else is a Buff.csv state id.
            if aid in ACTION_TYPE:
                name = ACTION_TYPE[aid]
                is_action = True
            else:
                name = buff_name(aid)
                is_action = False
            recs.append({
                "actionType": int(aid),
                "actionName": name,
                "isAction": is_action,
                "fromRound": num(t[1]),
                "targetCategory": int(t[2]),
                "targetCategoryName": TARGET_CATEGORY.get(t[2], "UNKNOWN(%s)" % t[2]),
                "targetCount": num(t[3]),
                "triggerChance": num(t[4]),
                "coefficient": num(t[5]),
                "flatMagnitude": num(t[6]),
                "layersOrMinDur": num(t[7]),
                "maxStacks": num(t[8]),
                "duration": num(t[9]),
                "flagA": num(t[10]),
                "affectedByAttr": num(t[11]),
                "rawTokens": t,
            })
        return recs

    out = []
    for r in skills:
        st = r["ST"]
        sid = r["ID"]
        init_v = float(r["InitVal"])
        up_v = float(r["UpVal"])
        impact = float(r["ImpactBy"])
        # value at max level (10). ImpactBy already equals InitVal + 10*UpVal,
        # but compute it from the formula to be explicit/auditable.
        maxed = round(init_v + 10 * up_v, 6)
        pct = uptype_is_percent(r["UpType"])
        up_type = int(r["UpType"]) if r["UpType"].strip() else 0

        # effects: actions from the Effect column + side effects from Buff/Dbuff.
        effects = parse_effects(r["Effect"]) + parse_effects(r["Buff"]) + parse_effects(r["Dbuff"])

        buff_first = parse_groups(r["Buff"])
        dbuff_first = parse_groups(r["Dbuff"])
        buff_obj = None
        if buff_first:
            bid = buff_first[0][0]
            buff_obj = {"id": int(bid), "name": buff_name(bid)}
        dbuff_obj = None
        if dbuff_first:
            bid = dbuff_first[0][0]
            dbuff_obj = {"id": int(bid), "name": buff_name(bid)}

        # trigger probability at max level. For UpType==45 the probability is the
        # scaled value (SkillP == ImpactBy at level 10); else SkillP is fixed.
        skillp = float(r["SkillP"])
        trigger_max = round(init_v + 10 * up_v, 6) if up_type == 45 else skillp

        out.append({
            "key": "%s_%s" % (st, sid),
            "st": int(st),
            "st_name": SKILL_TYPE_NAME.get(st, "Unknown"),
            "id": int(sid),
            "name_en": official_name(r),
            "des_en": clean(r["Des_en"]),
            "rare": int(r["Rare"]) if r["Rare"].strip() else 0,
            "skillStone": r["SkillStone"].strip() == "1",
            "maxUse": int(r["MaxUse"]) if r["MaxUse"].strip() else 0,
            "readyRound": int(r["ReadyRound"]) if r["ReadyRound"].strip() else 0,
            "skillP": skillp,
            "triggerProbAtMax": trigger_max,
            "impactBy": impact,
            "upType": up_type,
            "upTypeIsPercent": pct,
            "upVal": up_v,
            "initVal": init_v,
            "maxedValue": maxed,
            "maxedValuePercent": round(maxed * 100, 4) if pct else None,
            "buff": buff_obj,
            "dbuff": dbuff_obj,
            "effect_raw": r["Effect"],
            "buff_raw": r["Buff"],
            "dbuff_raw": r["Dbuff"],
            "effects": effects,
        })

    out.sort(key=lambda x: (x["st"], x["id"]))

    dst_dir = os.path.join(ROOT, "data", "sim")
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, "skills.json")
    with io.open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # console-safe summary (ASCII only)
    from collections import Counter
    print("wrote %d skills to %s" % (len(out), dst))
    print("by ST:", dict(Counter(s["st_name"] for s in out)))
    print("skillStone eligible:", sum(1 for s in out if s["skillStone"]))


if __name__ == "__main__":
    main()
