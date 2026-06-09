"""Generate the wiki (markdown) from extracted data. Every number comes from
data/csv; every id is resolved to a name. Re-run after data changes.

Usage: python tools/wikigen/build.py
"""
import os
import re
import collections

from resolver import (Resolver, load, has, fmt_num, clean, secs,
                      SOLDIER_TYPE, RST_ARCHETYPE, SKILL_TYPE_NAME, HERO_ROLE,
                      RACE_NAME, NPC_JOB, HERO_MAX_LEVEL, ROOT)

WIKI = os.path.join(ROOT, "wiki")
R = Resolver()
PAGES = []   # (section, title, relpath)


def write(relpath, title, section, lines):
    path = os.path.join(WIKI, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = "# %s\n\n" % title + "\n".join(lines) + "\n\n---\n*Auto-generated from game data by `tools/wikigen/build.py`. Do not edit by hand.*\n"
    open(path, "w", encoding="utf-8").write(body)
    PAGES.append((section, title, relpath))


def tbl(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return out


# --------------------------------------------------------------------------- #
def gen_buildings():
    rows = load("BuildNeed")
    by_b = collections.OrderedDict()
    for r in rows:
        by_b.setdefault(r["id"], []).append(r)
    lines = ["Per-level costs, build time, power and effects for every building. "
             "Resource costs are per upgrade; **time** is base build time (before speedups).", ""]
    # in-page TOC
    lines.append("## Buildings")
    for bid in by_b:
        nm = R.build_name(bid)
        lines.append("- [%s](#%s)" % (nm, nm.lower().replace(" ", "-").replace("'", "")))
    lines.append("")
    for bid, lvls in by_b.items():
        base = R.build_base.get(bid, {})
        nm = R.build_name(bid)
        maxc = base.get("MaxCount", "?")
        lines.append("## %s" % nm)
        meta = []
        if maxc and maxc != "0":
            meta.append("Max count: **%s**" % maxc)
        meta.append("Max level: **%d**" % max(int(l["lv"]) for l in lvls))
        lines.append(" · ".join(meta))
        lines.append("")
        body = []
        for l in sorted(lvls, key=lambda x: int(x["lv"])):
            eff = R.desc(l.get("des_en")) or R.expand_props(l.get("effect"))
            body.append([l["lv"], fmt_num(l["food"]), fmt_num(l["wood"]), fmt_num(l["stone"]),
                         fmt_num(l["iron"]), secs(l["time"]), fmt_num(l["power"]),
                         R.need_build(l["need_build"]), eff])
        lines += tbl(["Lv", "Food", "Wood", "Stone", "Iron", "Time", "Power", "Requires", "Effect"], body)
        lines.append("")
    write("Buildings/Buildings.md", "Buildings", "City & Economy", lines)


def gen_soldiers():
    rows = load("SoldierInfo")
    by_t = collections.OrderedDict()
    for r in rows:
        by_t.setdefault(r["type"], []).append(r)
    lines = ["All troop types and tiers with combat and economy stats. "
             "Recruit/Cure costs are **per soldier**; times are per soldier (seconds).", ""]
    for t, sl in by_t.items():
        lines.append("## %s" % SOLDIER_TYPE.get(t, "Type " + t))
        body = []
        for s in sorted(sl, key=lambda x: int(x["level"])):
            body.append(["T%s" % s["level"], s["attack"], s["defense"], s["ruin"], s["health"],
                         s["movement_speed"], s["load"], fmt_num(s["power"]),
                         "%s/%s/%s/%s" % (s["recruit_food"], s["recruit_wood"], s["recruit_stone"], s["recruit_iron"]),
                         secs(s["recruit_time"]),
                         "%s/%s/%s/%s" % (s["cure_food"], s["cure_wood"], s["cure_stone"], s["cure_iron"]),
                         secs(s["cure_time"])])
        lines += tbl(["Tier", "ATK", "DEF", "Ruin", "HP", "Move Spd", "Load", "Power",
                      "Recruit F/W/S/I", "Recruit Time", "Cure F/W/S/I", "Cure Time"], body)
        lines.append("")
    write("Soldiers/Soldiers.md", "Soldiers (Troops)", "Military", lines)


def gen_science():
    rows = load("ScienceInfo")
    by_id = collections.OrderedDict()
    for r in rows:
        by_id.setdefault(r["id"], []).append(r)
    lines = ["Research / technology tree. Each tech has multiple levels with rising cost and effect.", ""]
    for sid, lvls in by_id.items():
        nm = clean(lvls[0].get("name_en") or lvls[0].get("name"))
        lines.append("### %s" % nm)
        body = []
        for l in sorted(lvls, key=lambda x: int(x["lv"])):
            body.append([l["lv"], fmt_num(l["power"]), fmt_num(l["food"]), fmt_num(l["wood"]),
                         fmt_num(l["stone"]), fmt_num(l["iron"]), secs(l["time"]),
                         R.need_build(l["need_build"]) if l.get("need_build", "0") not in ("0", "") else "—",
                         R.desc(l.get("des_en"))])
        lines += tbl(["Lv", "Power", "Food", "Wood", "Stone", "Iron", "Time", "Req. Building", "Effect"], body)
        lines.append("")
    write("Research/Science.md", "Research / Technology", "City & Economy", lines)


def gen_formulas():
    rows = load("Formula")
    by_type = collections.OrderedDict()
    for r in rows:
        by_type.setdefault(clean(r.get("TypeName_en") or r.get("TypeName")), []).append(r)
    lines = ["Crafting / production recipes. **Time** is per craft (seconds). "
             "**Max** is the max stack/queue size.", ""]
    for tn, fl in by_type.items():
        lines.append("## %s" % (tn or "Misc"))
        body = []
        for r in fl:
            body.append([r["FId"], R.prop_name(r["RetPropId"]), R.expand_props(r["PropList"]),
                         secs(r["NeedTime"]), r["Max"]])
        lines += tbl(["Recipe ID", "Output", "Inputs", "Time", "Max"], body)
        lines.append("")
    qa = load("FormulaQuickAdd")
    if qa:
        lines.append("## Quick-Add Yields")
        lines.append("The crafting UI's \"quick add\" shortcut: how much of a base material converts into "
                     "a target output. `Multiplier` is the raw conversion factor from the game data.")
        lines.append("")
        body = [[r["ID"], R.prop_name(r.get("basePropId")), R.prop_name(r.get("boxPropId")),
                 fmt_num(r.get("propMutil"))] for r in qa]
        lines += tbl(["ID", "Base Material", "Target Output", "Multiplier"], body)
        lines.append("")
    write("Crafting/Formulas.md", "Crafting & Production", "City & Economy", lines)


def gen_talents(config, title, relpath, has_props):
    rows = load(config)
    by_t = collections.OrderedDict()
    for r in rows:
        by_t.setdefault(clean(r.get("Name_en") or r.get("Name")), []).append(r)
    lines = ["Talent trees: each talent gains effects per level (costs talent points / items).", ""]
    for nm, tl in by_t.items():
        lines.append("### %s" % nm)
        body = []
        for r in sorted(tl, key=lambda x: int(x["TalentLv"])):
            row = [r["TalentLv"], r.get("NeedPoint", "")]
            if has_props:
                row.append(R.expand_props(r.get("NeedProps")))
            row.append(R.desc(r.get("Des_en") or r.get("Des")))
            body.append(row)
        head = ["Lv", "Points"] + (["Items"] if has_props else []) + ["Effect"]
        lines += tbl(head, body)
        lines.append("")
    write(relpath, title, "Heroes & Lord", lines)


def gen_vip():
    rows = load("VIPData")
    lines = ["VIP levels, EXP required, cumulative buffs and daily bonuses.", ""]
    body = []
    for r in rows:
        body.append([r["vip_lv"], fmt_num(r["upExp"]), R.desc(r.get("buff_text_en") or r.get("buff_text")),
                     R.expand_props(r.get("daily_bonus"))])
    lines += tbl(["VIP", "EXP Req.", "Buffs (cumulative)", "Daily Bonus"], body)
    write("Progression/VIP.md", "VIP Levels", "Progression", lines)


def gen_style():
    rows = load("StyleLv")
    lines = ["Style / charm level progression and its city bonuses.", ""]
    body = []
    for r in rows:
        body.append([r["StyleLv"], fmt_num(r["NeedVal"]), fmt_num(r["Power"]), R.desc(r.get("Des_en") or r.get("Des"))])
    lines += tbl(["Style Lv", "Req. Value", "Power", "Effect"], body)
    write("Progression/Style.md", "Style Level", "Progression", lines)


def gen_buffs():
    rows = load("Buff")
    lines = ["Combat/effect buff catalog. **Type +1** = beneficial, **-1** = detrimental.", ""]
    body = [[r["buffId"], clean(r.get("Name_en") or r.get("Name")),
             "good (+1)" if r["Type"] == "1" else ("bad (-1)" if r["Type"] == "-1" else r["Type"])]
            for r in rows]
    lines += tbl(["Buff ID", "Name", "Type"], body)
    write("Mechanics/Buffs.md", "Buffs & Debuffs", "Mechanics", lines)


def gen_troop_combos():
    rows = load("TroopsEffect")
    lines = ["Troop composition bonuses — fielding certain soldier types together grants effects.", ""]
    body = []
    for r in rows:
        body.append([clean(r.get("name_en") or r.get("name")),
                     SOLDIER_TYPE.get(r.get("condition"), r.get("condition")),
                     r.get("number"), clean(r.get("addtion_des_en") or r.get("addtion_des"))])
    lines += tbl(["Combination", "Soldier Type", "Count", "Bonus"], body)
    write("Military/Troop-Combinations.md", "Troop Combinations", "Military", lines)


def gen_codex():
    rows = load("CodexInfo")
    lines = ["Hero codex sets — collecting the listed heroes grants the set bonus and Power.", "",
             "*`Effect Type`/`Effect Val` are the raw set-bonus parameters from the data.*", ""]
    body = []
    for r in rows:
        heroes = " / ".join(R.hero_name(h) for h in r["NeedHeroList"].split("_") if h)
        body.append([r["CodexId"], r["Rare"], r.get("AdLv", ""), heroes, r["EffectType"], r["EffectVal"]])
    lines += tbl(["Codex ID", "Rare", "Adv Lv", "Heroes Required", "Effect Type", "Effect Val"], body)
    write("Codex/Codex.md", "Hero Codex (Collections)", "Codex & Collections", lines)


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "x"


def _hero_skills(h):
    out = []
    for i in (0, 1, 2):
        st, sid = h["skill%d_type" % i], h["skill%d_id" % i]
        if st == "0" and sid == "0":
            continue
        sk = R.skill_full(st, sid)
        nm = clean(sk.get("Name_en") or sk.get("Name")) if sk else "Skill#%s.%s" % (st, sid)
        out.append((st, sid, nm, sk))
    return out


def gen_heroes():
    heroes = [h for h in load("HeroInfo") if R.is_named_hero(h["id"])]
    heroes.sort(key=lambda h: (-int(h["rare"]), int(h["id"])))
    lines = ["The playable hero roster (%d heroes). Stats shown are **base** (level 0 reference) "
             "with per-level **growth**; effective stat at level *L* = `base + floor(growth × L)`. "
             "Hero max level is **%d**. Click a hero for full per-level tables, skills, and lore." % (len(heroes), HERO_MAX_LEVEL),
             "",
             "- **Rarity**: 2–5 (higher = rarer). **Race**: hero faction (1–3). "
             "**Role**: DPS / Heal / CC / Buff / Debuff. **RST**: recommended troop & stat-point archetype.",
             "- Skills are linked to the [Skill catalog](Skills.md).", ""]
    body = []
    for h in heroes:
        skills = " · ".join("%s (%s)" % (nm, SKILL_TYPE_NAME.get(st, st)) for st, sid, nm, sk in _hero_skills(h))
        page = "roster/%s-%s.md" % (h["id"], _slug(R.hero_name(h["id"])))
        body.append([
            h["id"],
            "[%s](%s)" % (R.hero_name(h["id"]), page),
            "★" + h["rare"],
            RACE_NAME.get(h["type"], h["type"]),
            R.hero_role(h["id"]),
            RST_ARCHETYPE.get(h["RST"], h["RST"]).split(" (")[0],
            "%s/%s/%s/%s" % (h["attack"], h["defense"], h["ruin"], h["speed"]),
            "%s/%s/%s/%s" % (h["attack_grow"], h["defense_grow"], h["ruin_grow"], h["speed_grow"]),
            skills or "—",
        ])
    lines += tbl(["ID", "Hero", "Rarity", "Race", "Role", "Archetype",
                  "Base A/D/R/S", "Growth A/D/R/S", "Skills"], body)
    write("Heroes/Heroes.md", "Heroes (Roster)", "Heroes & Lord", lines)
    gen_hero_pages(heroes)


def gen_hero_pages(heroes):
    for h in heroes:
        hid = h["id"]
        nm = R.hero_name(hid)
        L = ["[← Back to roster](../Heroes.md)", ""]
        # identity
        role = R.hero_role(hid)
        L.append("**Rarity:** ★%s  ·  **Race:** %s  ·  **Role:** %s  ·  **Archetype (RST):** %s"
                 % (h["rare"], RACE_NAME.get(h["type"], h["type"]), role, RST_ARCHETYPE.get(h["RST"], h["RST"])))
        L.append("")
        # bio
        hf = R.herofile.get(hid)
        if hf:
            bio = []
            if hf.get("Heighi", "0") not in ("0", ""): bio.append("Height %scm" % hf["Heighi"])
            if hf.get("Age", "0") not in ("0", ""): bio.append("Age %s" % hf["Age"])
            if hf.get("Birthday", "0") not in ("0", ""): bio.append("Birthday %s" % hf["Birthday"])
            if clean(hf.get("Character_en")): bio.append("Character: %s" % clean(hf["Character_en"]))
            if clean(hf.get("Interest_en")): bio.append("Interest: %s" % clean(hf["Interest_en"]))
            if bio:
                L.append("## Profile")
                L.append(" · ".join(bio)); L.append("")
        # background story
        bg = R.herobg.get(hid)
        if bg:
            paras = [clean(bg.get("Bg_Line%d_en" % i)) for i in range(1, 13)]
            paras = [p for p in paras if p and p != "0"]
            if paras:
                L.append("## Background")
                for p in paras:
                    L.append(p + "\n")
        # voice lines
        hd = R.herodes.get(hid)
        if hd:
            vl = []
            for label, key in [("Summon", "summon_line_en"), ("Tap 1", "click_line1_en"),
                               ("Tap 2", "click_line2_en"), ("Tap 3", "click_line3_en")]:
                v = clean(hd.get(key))
                if v and v != "0":
                    vl.append((label, v))
            if vl:
                L.append("## Voice Lines")
                L += tbl(["Line", "Text"], vl); L.append("")
        # base stats + growth
        L.append("## Base Stats & Growth")
        L += tbl(["Stat", "Base", "Growth / Level"],
                 [["Attack", h["attack"], h["attack_grow"]],
                  ["Defense", h["defense"], h["defense_grow"]],
                  ["Ruin", h["ruin"], h["ruin_grow"]],
                  ["Speed", h["speed"], h["speed_grow"]]])
        L.append("")
        # full level progression
        L.append("## Stat Progression (Lv 1–%d)" % HERO_MAX_LEVEL)
        L.append("`stat(L) = base + floor(growth × L)`")
        prog = []
        for lv in range(1, HERO_MAX_LEVEL + 1):
            prog.append([lv,
                         R.hero_stat_at(h["attack"], h["attack_grow"], lv),
                         R.hero_stat_at(h["defense"], h["defense_grow"], lv),
                         R.hero_stat_at(h["ruin"], h["ruin_grow"], lv),
                         R.hero_stat_at(h["speed"], h["speed_grow"], lv)])
        L += tbl(["Lv", "Attack", "Defense", "Ruin", "Speed"], prog)
        L.append("")
        # skills
        L.append("## Skills")
        for st, sid, snm, sk in _hero_skills(h):
            L.append("### %s — *%s*" % (snm, SKILL_TYPE_NAME.get(st, "Type " + st)))
            if sk:
                if clean(sk.get("Des_en")):
                    L.append(clean(sk["Des_en"]))
                meta = []
                if sk.get("Rare"): meta.append("Rarity ★%s" % sk["Rare"])
                if sk.get("MaxUse", "0") not in ("0", ""): meta.append("Max uses/battle: %s" % sk["MaxUse"])
                if sk.get("ReadyRound", "0") not in ("0", ""): meta.append("Ready on round %s" % sk["ReadyRound"])
                if meta:
                    L.append("*" + " · ".join(meta) + "*")
                aw = R.awaken.get((st, sid))
                if aw:
                    L.append("")
                    L += tbl(["Skill Lv", "Effect"],
                             [[a["Lv"], clean(a.get("des_en") or a.get("des"))] for a in aw])
            L.append("")
        L.append("---")
        L.append("**Related:** [Hero Roster](../Heroes.md) · [Hero Talents](../Hero-Talents.md) · "
                 "[Hero Skins](../Hero-Skins.md) · [Skill Catalog](../Skills.md)")
        write("Heroes/roster/%s-%s.md" % (hid, _slug(nm)), nm, "_hidden", L)


def gen_skills():
    rows = load("NewSkillInfo")
    by_t = collections.OrderedDict()
    for r in rows:
        by_t.setdefault(r["ST"], []).append(r)
    # reverse index: which named heroes innately carry each (ST, ID) skill
    users = {}
    for h in load("HeroInfo"):
        if not R.is_named_hero(h["id"]):
            continue
        nm = R.hero_name(h["id"])
        page = "roster/%s-%s.md" % (h["id"], _slug(nm))
        for i in (0, 1, 2):
            key = (h["skill%d_type" % i], h["skill%d_id" % i])
            if key == ("0", "0"):
                continue
            users.setdefault(key, []).append("[%s](%s)" % (nm, page))
    lines = ["Full skill catalog. **Type**: Strategic / Tactical / Passive / Pursuit. "
             "Skills level up (\"awaken\") — see per-level effects on each hero's page. "
             "`Impact` is the skill's base power coefficient; `Init`/`+Lv` show base value and per-level gain. "
             "`Used by` lists heroes that carry the skill innately.", ""]
    for st in sorted(by_t, key=lambda x: int(x)):
        lines.append("## %s Skills" % SKILL_TYPE_NAME.get(st, "Type " + st))
        body = []
        for r in sorted(by_t[st], key=lambda x: int(x["ID"])):
            body.append([r["ID"], clean(r.get("Name_en") or r.get("Name")), "★" + r["Rare"],
                         r.get("MaxUse", "0"), r.get("ReadyRound", "0"),
                         r.get("ImpactBy", ""), r.get("InitVal", ""), r.get("UpVal", ""),
                         clean(r.get("Des_en") or r.get("Des")),
                         ", ".join(users.get((st, r["ID"]), [])) or "—"])
        lines += tbl(["ID", "Name", "Rarity", "Max Use", "Ready Rd", "Impact", "Init", "+/Lv", "Description", "Used by"], body)
        lines.append("")
    write("Heroes/Skills.md", "Skill Catalog", "Heroes & Lord", lines)


def gen_ai_heroes():
    heroes = [h for h in load("HeroInfo") if not R.is_named_hero(h["id"])]
    heroes.sort(key=lambda h: int(h["id"]))
    lines = ["Non-roster heroes used by AI / enemies / events (%d). Same stat model as "
             "[playable heroes](Heroes.md): `stat(L) = base + floor(growth × L)`." % len(heroes), ""]
    body = []
    for h in heroes:
        body.append([h["id"], R.hero_name(h["id"]), "★" + h["rare"], RACE_NAME.get(h["type"], h["type"]),
                     "%s/%s/%s/%s" % (h["attack"], h["defense"], h["ruin"], h["speed"]),
                     "%s/%s/%s/%s" % (h["attack_grow"], h["defense_grow"], h["ruin_grow"], h["speed_grow"])])
    lines += tbl(["ID", "Name", "Rarity", "Race", "Base A/D/R/S", "Growth A/D/R/S"], body)
    write("Heroes/AI-Heroes.md", "AI / Enemy Heroes", "Heroes & Lord", lines)


def gen_npcs():
    rows = load("NPCData")
    lines = ["Assignable workers (\"Maidens\") placed in production buildings. "
             "Higher rarity / weight = stronger work output.", ""]
    body = []
    for r in rows:
        body.append([r.get("XmlNum", ""), clean(r.get("Name_en") or r.get("Name")),
                     NPC_JOB.get(r.get("JobType"), r.get("JobType")), "★" + r.get("Rare", ""),
                     r.get("Weight", ""), R.expand_props(r.get("WorkEffects")),
                     R.expand_props(r.get("WorkCosts"))])
    lines += tbl(["ID", "Name", "Job", "Rarity", "Weight", "Work Effect", "Work Cost"], body)
    write("Characters/Maidens.md", "Maidens (Workers / NPCs)", "Characters & Lore", lines)


def gen_props():
    rows = load("PropInfo")
    by_t = collections.OrderedDict()
    for r in rows:
        by_t.setdefault(r["type"], []).append(r)
    lines = ["Master catalog of every item / resource / material (\"prop\") in the game, "
             "grouped by internal type. Prop IDs are referenced throughout the wiki "
             "(costs, rewards, effects).", "",
             "| Type | Count |", "|---|---|"]
    for t in sorted(by_t, key=lambda x: int(x) if x.isdigit() else 0):
        lines.append("| Type %s | %d |" % (t, len(by_t[t])))
    lines.append("")
    for t in sorted(by_t, key=lambda x: int(x) if x.isdigit() else 0):
        lines.append("## Type %s (%d)" % (t, len(by_t[t])))
        body = []
        for r in sorted(by_t[t], key=lambda x: int(x["id"]) if x["id"].isdigit() else 0):
            body.append([r["id"], clean(r.get("name_en") or r.get("name")),
                         "★" + r.get("rare", "0"), clean(r.get("des_en"))[:90]])
        lines += tbl(["ID", "Name", "Rarity", "Description"], body)
        lines.append("")
    write("Items/Items.md", "Items & Resources (Props)", "Items", lines)


def gen_mechanics():
    L = [
        "How the numbers work. **All formulas here are verified from the decompiled game "
        "code**; where a calculation is server-side, that is stated explicitly.", "",
        "## Stat & data conventions",
        "- Packed lists use `id_count` (a prop id and amount), joined by `+`. "
        "Example: `Effect = 84_1000000+78_1` → *Reserve Soldiers Capacity ×1,000,000, Number Of Troops ×1*.",
        "- `need_build = BuildingType_Level` (`0_0` = no requirement).",
        "- The four combat stats are **Attack (ATK / AD)**, **Defense (DEF)**, "
        "**Ruin (DES / DMG)**, **Speed (SP)**.", "",
        "## Hero stat growth — *client-side, exact*",
        "A hero's effective stat at level *L*:",
        "```",
        "stat(L) = base + floor(growth × L)",
        "```",
        "Applies to Attack, Defense, Ruin and Speed independently (base + per-stat growth "
        "from the hero's data). **Hero max level = %d.** Per-hero level tables are on each "
        "hero page; bases and growth are in the [roster](../Heroes/Heroes.md)." % HERO_MAX_LEVEL, "",
        "### Hero races", "",
        "| # | Race |", "|---|---|"] + ["| %s | %s |" % (k, v) for k, v in RACE_NAME.items()] + [
        "", "### Hero roles (Job)", "",
        "| # | Role |", "|---|---|"] + ["| %s | %s |" % (k, v) for k, v in HERO_ROLE.items()] + [
        "", "### Skill types", "",
        "| # | Type |", "|---|---|"] + ["| %s | %s |" % (k, v) for k, v in SKILL_TYPE_NAME.items()] + [
        "", "### RST — recommended troop & stat-point archetype",
        "When a hero leads troops, surplus attribute points are auto-allocated by their RST "
        "(verified from code):", "",
        "| RST | Soldier type | Point allocation |", "|---|---|---|",
        "| 1 | Infantry | 60% Defense, remainder Speed |",
        "| 2 | Archer | 80% Attack, remainder Ruin |",
        "| 3 | Cavalry | 60% Defense, remainder Attack |",
        "| 4 | Chariot | 60% Ruin, remainder Attack |", "",
        "## Troops",
        "Soldier base stats and recruit/cure costs are fixed per tier — see [Soldiers](../Soldiers/Soldiers.md). "
        "Each of the 4 types (Infantry, Archer, Cavalry, Chariot) has tiers T1–T6. "
        "Composition bonuses: [Troop Combinations](../Military/Troop-Combinations.md).", "",
        "## Build / research / craft time",
        "Base times come straight from the data (seconds): buildings [`time`](../Buildings/Buildings.md), "
        "research [`time`](../Research/Science.md), crafting [`NeedTime`](../Crafting/Formulas.md). "
        "In-game speedups and reductions are applied on top (server-validated).", "",
        "## Power",
        "Total Power is **computed server-side** and sent to the client as a breakdown:",
        "```",
        "AllPower = BuildPower + SciencePower + HeroPower + SkillPower + LordPower + CodexPower",
        "```",
        "Each system contributes its `power` value (e.g. each building level, each tech level, "
        "each codex set lists a Power amount in its tables).", "",
        "## Combat — *server-side*",
        "Battles are resolved on the server. The client sends the chosen troops "
        "(`CSLogic_StartFight`) and receives a **Battle Report** containing the result, "
        "per-round data, kills and MVPs. The exact damage equation is therefore not present "
        "in the client. What the client (and this wiki) provides: effective hero/troop stats, "
        "skill and buff definitions, and troop-composition bonuses. "
        "See [Buffs](Buffs.md) (`+1` beneficial, `-1` detrimental).",
    ]
    write("Mechanics/Stats-and-Formulas.md", "Stats, Formulas & Mechanics", "Mechanics", L)


def gen_recommend():
    rows = load("Recommend")
    lines = ["Developer-recommended hero teams and skill loadouts (great starting builds). "
             "Each team is 3 heroes; skills are listed per hero.", ""]
    body = []
    for r in rows:
        cells = [r["RecId"], R.desc(r.get("Des_en") or r.get("Des"))]
        for i in (1, 2, 3):
            h = r.get("HeroNum%d" % i, "0")
            sk = R.skill_list(r.get("SkillNum%d" % i, ""))
            cells.append("**%s**<br/>%s" % (R.hero_name(h), sk) if h != "0" else "—")
        body.append(cells)
    lines += tbl(["ID", "Category", "Hero 1", "Hero 2", "Hero 3"], body)
    write("Teams/Recommended-Teams.md", "Recommended Teams & Builds", "Teams & Builds", lines)


def gen_favorability():
    rows = load("GoodFeel")
    lines = ["Hero favorability (\"GoodFeel\") levels — raise affinity for a global all-hero stat bonus.", ""]
    body = [[r["lv"], fmt_num(r["upLvExp"]), R.expand_props(r.get("costProp")), R.desc(r.get("des_en") or r.get("des"))]
            for r in rows]
    lines += tbl(["Lv", "EXP", "Cost / Level", "Effect"], body)
    write("Progression/Favorability.md", "Favorability (GoodFeel)", "Progression", lines)


def gen_ship():
    rows = load("ShipData")
    lines = ["Transport/Naval ship levels.", ""]
    body = [[r["ShipLv"], r["MoveSpeed"], r["LoadCount"], R.expand_props(r.get("UpNeeds"))] for r in rows]
    lines += tbl(["Ship Lv", "Move Speed", "Load Count", "Upgrade Cost"], body)
    write("Progression/Ship.md", "Ship Levels", "Progression", lines)


def gen_lord_dress():
    rows = load("LordDress")
    lines = ["Lord cosmetic outfits (suits). Pieces are item ids.", ""]
    body = []
    for r in rows:
        pieces = ", ".join(R.prop_name(r[k]) for k in ("Pos1_PropId", "Pos2_PropId", "Pos3_PropId")
                           if r.get(k, "0") not in ("0", ""))
        body.append([r["SuitID"], clean(r.get("SuitName_en") or r.get("SuitName")), "★" + r.get("Rare", ""), pieces or "—"])
    lines += tbl(["Suit ID", "Name", "Rarity", "Pieces"], body)
    write("Progression/Lord-Outfits.md", "Lord Outfits", "Progression", lines)


def gen_union_science():
    rows = load("UnionScience")
    by_id = collections.OrderedDict()
    for r in rows:
        by_id.setdefault(r["id"], []).append(r)
    lines = ["Alliance (Union) research. Uses alliance resources (Ci/Si/Fe/Ue/Gold).", ""]
    for sid, lvls in by_id.items():
        lines.append("### %s" % clean(lvls[0].get("name_en") or lvls[0].get("name")))
        body = []
        for l in sorted(lvls, key=lambda x: int(x["lv"])):
            body.append([l["lv"], fmt_num(l["power"]),
                         "%s/%s/%s/%s/%s" % (l["union_Ci"], l["union_Si"], l["union_Fe"], l["union_Ue"], l["union_Gold"]),
                         secs(l["time"]), R.desc(l.get("des_en"))])
        lines += tbl(["Lv", "Power", "Cost Ci/Si/Fe/Ue/Gold", "Time", "Effect"], body)
        lines.append("")
    write("Alliance/Union-Research.md", "Alliance Research", "Alliance", lines)


def gen_bosses():
    lines = ["World and alliance bosses with their enemy formations and rewards.", ""]
    for cfg, title in [("WolrdBoss", "World Bosses"), ("UnionBoss", "Alliance Bosses")]:
        rows = load(cfg)
        if not rows:
            continue
        lines.append("## %s" % title)
        body = [[r["BossId"], clean(r.get("Name_en") or r.get("Name")), R.expand_ai(r.get("AiInfo"))] for r in rows]
        lines += tbl(["ID", "Boss", "Enemy Formation"], body)
        lines.append("")
    ncw = load("NewCityWar")
    if ncw:
        lines.append("## City War Bosses")
        body = [[r["CityLv"], clean(r.get("Name_en") or r.get("Name")), clean(r.get("Con_en") or r.get("Con")),
                 secs(r.get("FightTime")), R.expand_ai(r.get("AiInfo"))] for r in ncw]
        lines += tbl(["Lv", "Boss", "Condition", "Fight Time", "Enemy Formation"], body)
    write("World/Bosses.md", "Bosses", "PvE & World", lines)


def gen_campaign():
    rows = load("MainGate")
    lines = ["Main campaign stages (\"gates\"). Beat the enemy formation to clear; each grants a "
             "first-clear reward and passive idle Income.", "",
             "*%d stages total.*" % len(rows), ""]
    body = []
    for r in rows:
        body.append([r["gateNum"], r.get("NeedLv", ""), R.expand_ai(r.get("AiInfo")),
                     R.expand_props(r.get("FirstAward"))])
    lines += tbl(["Stage", "Lord Lv", "Enemy Formation", "First-Clear Reward"], body)
    write("World/Campaign.md", "Campaign (Main Gates)", "PvE & World", lines)


def gen_trials():
    rows = load("Assess")
    lines = ["Assessment trial gates — sequential fights with a troop cap.", ""]
    body = [[r["GateNum"], r.get("GroupId", ""), r.get("MaxTroop", ""), R.expand_ai(r.get("AiInfo")),
             R.expand_props(r.get("FirstAward"))] for r in rows]
    lines += tbl(["Gate", "Group", "Max Troops", "Enemy Formation", "First Reward"], body)
    write("World/Trials.md", "Trials (Assessment)", "PvE & World", lines)


def gen_worldmap():
    rows = load("WorldMapInfo")
    lines = ["World-map objects you can attack/occupy for rewards.", ""]
    body = [[clean(r.get("Name_en") or r.get("Name")), r.get("Lv", ""), R.expand_ai(r.get("AiInfo")),
             R.expand_props(r.get("PassAward"))] for r in rows]
    lines += tbl(["Object", "Lv", "Enemy Formation", "Reward"], body)
    write("World/World-Map.md", "World Map Objects", "PvE & World", lines)


def gen_quests():
    lines = ["All quest, mission and event systems.", ""]
    defs = [
        ("MainQuests", "Main Quests", ["Chapter", "name_en", "des_en", "reward"], ["Chapter", "Name", "Objective", "Reward"]),
        ("DailyQuests", "Daily Quests", ["name_en", "des_en", "activity", "reward"], ["Category", "Objective", "Activity", "Reward"]),
        ("WeekQuests", "Weekly Quests", ["name_en", "des_en", "activity", "reward"], ["Category", "Objective", "Activity", "Reward"]),
        ("AnnalsQuests", "Annals (Achievements)", ["Title_en", "des_en", "star", "reward"], ["Category", "Objective", "Stars", "Reward"]),
        ("LifeTask", "Life Tasks", ["TaskDes_en", "Awards"], ["Objective", "Reward"]),
        ("HeroBook", "Hero Handbook", ["Title_en", "Des_en", "Awards"], ["Category", "Objective", "Reward"]),
        ("HandBook", "Newcomer Handbook", ["Des_en", "Reward"], ["Objective", "Reward"]),
        ("WeekEvent", "Weekly Events", ["EventName_en", "des_en", "reward"], ["Event", "Objective", "Reward"]),
        ("MonthEvent", "Monthly Events", ["Des_en", "Reward"], ["Objective", "Reward"]),
    ]
    for cfg, title, cols, head in defs:
        rows = load(cfg)
        if not rows:
            continue
        lines.append("## %s" % title)
        body = []
        for r in rows:
            row = []
            for c in cols:
                v = r.get(c, "")
                if c in ("reward", "Reward", "Awards"):
                    v = R.expand_props(v)
                else:
                    v = clean(v)
                row.append(v)
            body.append(row)
        lines += tbl(head, body)
        lines.append("")
    sq = load("SideQuests")
    if sq:
        cats = collections.Counter(clean(r.get("name_en") or r.get("name")) for r in sq)
        lines.append("## Side Quests")
        lines.append("%d side-quest steps (repetitive per-building/per-level objectives). Breakdown by category:" % len(sq))
        lines.append("")
        lines += tbl(["Category", "Steps"], sorted(cats.items(), key=lambda x: -x[1]))
    write("Quests/Quests-and-Events.md", "Quests & Events", "Quests & Events", lines)


def gen_story():
    sl = load("StoryLine")
    lines = ["The game's narrative. Spoilers ahead.", "", "## Prologue / Story Lines", ""]
    for r in sl:
        t = clean(r.get("line_en"))
        if t and t != "0":
            lines.append("> " + t + "\n")
    mp = load("MainPlot")
    by_ch = collections.OrderedDict()
    for r in mp:
        by_ch.setdefault(r["chapter"], []).append(r)
    lines.append("## Main Story")
    for ch, plot in by_ch.items():
        lines.append("\n### Chapter %s\n" % ch)
        for r in plot:
            txt = clean(r.get("content_en"))
            if not txt or txt == "0":
                continue
            sp = r.get("speaker", "0")
            if sp not in ("0", "") and sp in R.hero:
                lines.append("**%s:** %s" % (R.hero_name(sp), txt))
            else:
                lines.append("> " + txt)
        lines.append("")
    write("Lore/Story.md", "Story & Plot", "Characters & Lore", lines)


def gen_tips():
    rows = load("Tips")
    by_t = collections.OrderedDict()
    for r in rows:
        by_t.setdefault(clean(r.get("TypeName_en") or r.get("TypeName")), []).append(r)
    lines = ["In-game loading tips and mechanics hints, grouped by topic.", ""]
    for tn, tl in by_t.items():
        tips = [d for d in (clean(r.get("des_en") or r.get("des")) for r in tl) if d and d != "0"]
        if not tips:
            continue
        lines.append("### %s" % (tn or "General"))
        lines += ["- " + d for d in tips]
        lines.append("")
    write("Reference/Tips.md", "Game Tips", "Reference", lines)


def gen_entry_effects():
    rows = load("EntryEffect")
    lines = ["Catalog of attribute/effect entries used by gear, buffs and bonuses.", ""]
    body = [[r["EffectType"], clean(r.get("Name_en") or r.get("Name"))] for r in rows]
    lines += tbl(["Effect ID", "Attribute"], body)
    write("Reference/Attributes.md", "Attribute / Effect Catalog", "Reference", lines)


def gen_collections():
    rows = load("PropCodex")
    by_t = collections.OrderedDict()
    for r in rows:
        by_t.setdefault(clean(r.get("TypeName_en") or r.get("TypeName")), []).append(r)
    lines = ["Item-collection sets (\"PropCodex\") — gather the listed items to unlock a permanent bonus + Power.", ""]
    for tn, cl in by_t.items():
        lines.append("## %s" % (tn or "Misc"))
        body = [[r["Id"], R.expand_props(r.get("NeedProps")), R.expand_effects(r.get("Effects")), fmt_num(r.get("Power"))]
                for r in cl]
        lines += tbl(["Set ID", "Required Items", "Bonus", "Power"], body)
        lines.append("")
    write("Codex/Item-Collections.md", "Item Collections", "Codex & Collections", lines)


def gen_home():
    secs_order = ["Overview", "Mechanics", "Heroes & Lord", "Teams & Builds", "Military",
                  "City & Economy", "PvE & World", "Alliance", "Progression", "Quests & Events",
                  "Codex & Collections", "Characters & Lore", "Items", "Reference"]
    by_sec = collections.defaultdict(list)
    for sec, title, rel in PAGES:
        by_sec[sec].append((title, rel))
    lines = ["**Lord and Maiden** — a complete, data-mined reference for stats, formulas, "
             "and progression. All numbers are extracted directly from the game files.", "",
             "> Generated from game data. See `notes/` for methodology and `tools/` for the generators.", "",
             "## Table of Contents", ""]
    for sec in secs_order + [s for s in by_sec if s not in secs_order]:
        if sec not in by_sec or sec == "_hidden":
            continue
        lines.append("### %s" % sec)
        for title, rel in sorted(by_sec[sec]):
            lines.append("- [%s](%s)" % (title, rel.replace(" ", "%20")))
        lines.append("")
    open(os.path.join(WIKI, "README.md"), "w", encoding="utf-8").write(
        "# Lord and Maiden — Wiki\n\n" + "\n".join(lines) + "\n")


def main():
    os.makedirs(WIKI, exist_ok=True)
    gen_mechanics()
    gen_heroes()
    gen_ai_heroes()
    gen_skills()
    gen_npcs()
    gen_props()
    gen_buildings()
    gen_soldiers()
    gen_science()
    gen_formulas()
    gen_talents("HeroTalent", "Hero Talents", "Heroes/Hero-Talents.md", has_props=True)
    gen_talents("WarlordTalent", "Lord Talents", "Heroes/Lord-Talents.md", has_props=False)
    gen_vip()
    gen_style()
    gen_favorability()
    gen_ship()
    gen_lord_dress()
    gen_buffs()
    gen_troop_combos()
    gen_codex()
    gen_collections()
    gen_recommend()
    gen_union_science()
    gen_bosses()
    gen_campaign()
    gen_trials()
    gen_worldmap()
    gen_quests()
    gen_story()
    gen_tips()
    gen_entry_effects()
    import build_extra
    build_extra.register(write, tbl, R)
    gen_home()
    print("generated %d pages in %s" % (len(PAGES), WIKI))
    for sec, title, rel in PAGES:
        print("  [%s] %s -> %s" % (sec, title, rel))


if __name__ == "__main__":
    main()
