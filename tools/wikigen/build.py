"""Generate the wiki (markdown) from extracted data. Every number comes from
data/csv; every id is resolved to a name. Re-run after data changes.

Usage: python tools/wikigen/build.py
"""
import os
import re
import collections

from resolver import (Resolver, load, has, fmt_num, clean, secs,
                      SOLDIER_TYPE, RST_ARCHETYPE, SKILL_TYPE_NAME, HERO_ROLE,
                      HERO_MAX_LEVEL, ROOT)

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
            eff = clean(l.get("des_en")) or R.expand_props(l.get("effect"))
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
                         clean(l.get("des_en"))])
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
            row.append(clean(r.get("Des_en") or r.get("Des")))
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
        body.append([r["vip_lv"], fmt_num(r["upExp"]), clean(r.get("buff_text_en") or r.get("buff_text")),
                     R.expand_props(r.get("daily_bonus"))])
    lines += tbl(["VIP", "EXP Req.", "Buffs (cumulative)", "Daily Bonus"], body)
    write("Progression/VIP.md", "VIP Levels", "Progression", lines)


def gen_style():
    rows = load("StyleLv")
    lines = ["Style / charm level progression and its city bonuses.", ""]
    body = []
    for r in rows:
        body.append([r["StyleLv"], fmt_num(r["NeedVal"]), fmt_num(r["Power"]), clean(r.get("Des_en") or r.get("Des"))])
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
            h["type"],
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
                 % (h["rare"], h["type"], role, RST_ARCHETYPE.get(h["RST"], h["RST"])))
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
        write("Heroes/roster/%s-%s.md" % (hid, _slug(nm)), nm, "_hidden", L)


def gen_skills():
    rows = load("NewSkillInfo")
    by_t = collections.OrderedDict()
    for r in rows:
        by_t.setdefault(r["ST"], []).append(r)
    lines = ["Full skill catalog. **Type**: Strategic / Tactical / Passive / Pursuit. "
             "Skills level up (\"awaken\") — see per-level effects on each hero's page. "
             "`Impact` is the skill's base power coefficient; `Init`/`+Lv` show base value and per-level gain.", ""]
    for st in sorted(by_t, key=lambda x: int(x)):
        lines.append("## %s Skills" % SKILL_TYPE_NAME.get(st, "Type " + st))
        body = []
        for r in sorted(by_t[st], key=lambda x: int(x["ID"])):
            body.append([r["ID"], clean(r.get("Name_en") or r.get("Name")), "★" + r["Rare"],
                         r.get("MaxUse", "0"), r.get("ReadyRound", "0"),
                         r.get("ImpactBy", ""), r.get("InitVal", ""), r.get("UpVal", ""),
                         clean(r.get("Des_en") or r.get("Des"))])
        lines += tbl(["ID", "Name", "Rarity", "Max Use", "Ready Rd", "Impact", "Init", "+/Lv", "Description"], body)
        lines.append("")
    write("Heroes/Skills.md", "Skill Catalog", "Heroes & Lord", lines)


def gen_home():
    secs_order = ["Overview", "Mechanics", "Heroes & Lord", "Military", "City & Economy",
                  "Progression", "Codex & Collections", "Items", "Lore"]
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
    gen_heroes()
    gen_skills()
    gen_buildings()
    gen_soldiers()
    gen_science()
    gen_formulas()
    gen_talents("HeroTalent", "Hero Talents", "Heroes/Hero-Talents.md", has_props=True)
    gen_talents("WarlordTalent", "Lord Talents", "Heroes/Lord-Talents.md", has_props=False)
    gen_vip()
    gen_style()
    gen_buffs()
    gen_troop_combos()
    gen_codex()
    gen_home()
    print("generated %d pages in %s" % (len(PAGES), WIKI))
    for sec, title, rel in PAGES:
        print("  [%s] %s -> %s" % (sec, title, rel))


if __name__ == "__main__":
    main()
