"""Shared data loader + cross-reference resolver for the wiki generator.

Everything is read from data/csv (extracted from the game). IDs are resolved to
English names so generated pages never contain a bare numeric id without a name.
"""
import os
import csv
import re
import json
import math

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_DIR = os.path.join(ROOT, "data", "csv")

# verified from decompiled GetSkillTypeName / GetHeroJobDes (tokens resolved via localization)
SKILL_TYPE_NAME = {"1": "Strategic", "2": "Tactical", "3": "Passive", "4": "Pursuit"}
HERO_ROLE = {"1": "DPS", "2": "Heal", "3": "CC (Control)", "4": "Buff", "5": "Debuff"}
RACE_NAME = {"1": "Human", "2": "Orc", "3": "Elf"}   # GetHeroRaceDesTip
NPC_JOB = {"1": "Peasant Woman", "2": "Craftsman", "3": "Researcher", "4": "Angler"}  # GetJobDes
HERO_MAX_LEVEL = 80   # verified: code level brackets reach 80; UpExp type 2 = 1..80


def load(name):
    p = os.path.join(CSV_DIR, name + ".csv")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def has(name):
    return os.path.exists(os.path.join(CSV_DIR, name + ".csv"))


def fmt_num(s):
    """1000000 -> 1,000,000 ; keep decimals/text as-is."""
    s = (s or "").strip()
    try:
        if re.fullmatch(r"-?\d+", s):
            return format(int(s), ",")
        f = float(s)
        return ("%g" % f)
    except ValueError:
        return s


def clean(text):
    """Strip leftover { } localization braces and tidy separators for display."""
    if text is None:
        return ""
    return text.replace("{", "").replace("}", "").replace("\n", " ").strip()


# Soldier type + RST archetype names (verified from decompiled code)
SOLDIER_TYPE = {"1": "Infantry", "2": "Archer", "3": "Cavalry", "4": "Chariot"}
RST_ARCHETYPE = {
    "0": "—",
    "1": "Infantry (DEF + Speed)",
    "2": "Archer (ATK + Ruin)",
    "3": "Cavalry (DEF + ATK)",
    "4": "Chariot (Ruin + ATK)",
}


class Resolver:
    def __init__(self):
        self.prop = {r["id"]: r for r in load("PropInfo")}
        self.hero = {r["id"]: r for r in load("HeroInfo")}
        self.build_base = {r["id"]: r for r in load("BuildBaseInfo")}
        self.buff = {r["buffId"]: r for r in load("Buff")}
        self.skill = {(r["ST"], r["ID"]): r for r in load("NewSkillInfo")}
        self.science = load("ScienceInfo")
        self.science_by_id = {}
        for r in self.science:
            self.science_by_id.setdefault(r["id"], r)
        # hero lore/role links (keyed by character id)
        self.herodes = {r["id"]: r for r in load("HeroDes")}
        self.herofile = {r["HeroNum"]: r for r in load("HeroFile")}
        self.herobg = {r["Hero_id"]: r for r in load("HeroBgDesLine")}
        # skill awaken per-level table keyed by (skill_type, skill_id)
        self.awaken = {}
        for r in load("SkillAwake"):
            self.awaken.setdefault((r["skill_type"], r["skill_id"]), []).append(r)
        for k in self.awaken:
            self.awaken[k].sort(key=lambda x: int(x["Lv"]))
        # AI formation units + attribute/effect catalog (separate id spaces)
        self.ai = {r["AiNum"]: r for r in load("AiInfo")}
        self.entry = {r["EffectType"]: r for r in load("EntryEffect")}
        # localization
        locp = os.path.join(ROOT, "data", "localization.json")
        self.loc = json.load(open(locp, encoding="utf-8")) if os.path.exists(locp) else {}

    def effect_name(self, eid):
        r = self.entry.get(str(eid).strip())
        return clean(r.get("Name_en") or r.get("Name")) if r else ("Attr#" + str(eid))

    def expand_effects(self, s, sep="+"):
        """'111_200+115_50' -> 'Infantry HP ×200, ...' using the EntryEffect catalog."""
        s = (s or "").strip()
        if not s or s == "0":
            return "—"
        out = []
        for tok in s.split(sep):
            if "_" in tok:
                eid, _, val = tok.partition("_")
                out.append("%s ×%s" % (self.effect_name(eid), fmt_num(val)))
            elif tok:
                out.append(self.effect_name(tok))
        return ", ".join(out)

    def loc_en(self, token):
        return (self.loc.get(token.strip("{}"), {}) or {}).get("English_Text", token)

    def resolve_tokens(self, text):
        if not text or "{" not in text:
            return clean(text)
        return clean(re.sub(r"\{([^{}]*)\}", lambda m: self.loc_en(m.group(1)) or m.group(0), text))

    def is_named_hero(self, hid):
        return str(hid) in self.herodes

    def hero_role(self, hid):
        r = self.herodes.get(str(hid))
        return HERO_ROLE.get(r["HeroJob"], "—") if r else "—"

    def skill_full(self, st, sid):
        return self.skill.get((str(st), str(sid)))

    def hero_stat_at(self, base, grow, level):
        return int(base) + math.floor(float(grow) * level)

    def skill_list(self, s, sep="+"):
        """'2_81+2_100+3_26' -> 'Taboo Seal, ...' (each token is skilltype_id)."""
        s = (s or "").strip()
        if not s or s == "0":
            return "—"
        out = []
        for tok in s.split(sep):
            if "_" in tok:
                st, _, sid = tok.partition("_")
                out.append(self.skill_name(st, sid))
            elif tok:
                out.append(tok)
        return ", ".join(out)

    def expand_ai(self, s):
        """AI formation 'aiNum,aiNum,..._lv_x_y'. Each aiNum is an AiInfo unit whose
        HeroNum1..3 are HeroInfo ids -> resolve to the enemy hero team."""
        s = (s or "").strip()
        if not s or s == "0":
            return "—"
        ids, _, params = s.partition("_")
        units = []
        for aid in ids.split(","):
            aid = aid.strip()
            if not aid:
                continue
            row = self.ai.get(aid)
            if row:
                hs = [self.hero_name(row["HeroNum%d" % i]) for i in (1, 2, 3)
                      if row.get("HeroNum%d" % i, "0") not in ("0", "")]
                units.append(" / ".join(hs) if hs else ("AI#" + aid))
            elif aid in self.hero:
                units.append(self.hero_name(aid))
            else:
                units.append("AI#" + aid)
        # dedupe consecutive duplicates (formations often repeat the same unit)
        out = []
        for u in units:
            if not out or out[-1] != u:
                out.append(u)
        txt = "; ".join(out)
        if params:
            txt += "  *(Lv/params: %s)*" % params
        return txt

    # ---- name lookups ----
    def prop_name(self, pid):
        pid = str(pid).strip()
        r = self.prop.get(pid)
        if r:
            return clean(r.get("name_en") or r.get("name")) or ("Prop#" + pid)
        return "Prop#" + pid

    def hero_name(self, hid):
        r = self.hero.get(str(hid).strip())
        return clean(r.get("name_en") or r.get("name")) if r else ("Hero#" + str(hid))

    def build_name(self, bid):
        r = self.build_base.get(str(bid).strip())
        return clean(r.get("name_en") or r.get("name")) if r else ("Build#" + str(bid))

    def buff_name(self, bid):
        r = self.buff.get(str(bid).strip())
        return clean(r.get("name_en") or r.get("name")) if r else ("Buff#" + str(bid))

    def skill_name(self, st, sid):
        r = self.skill.get((str(st), str(sid)))
        if not r:
            return "Skill#%s.%s" % (st, sid)
        return clean(r.get("Name_en") or r.get("name_en") or r.get("Name") or r.get("name")) or ("Skill#%s.%s" % (st, sid))

    def science_name(self, sid):
        r = self.science_by_id.get(str(sid).strip())
        return clean(r.get("name_en") or r.get("name")) if r else ("Tech#" + str(sid))

    # ---- packed-list expanders ----
    def expand_props(self, s, sep="+"):
        """'84_1000000+78_1' -> 'Reserve Soldiers Capacity ×1,000,000, Numbers ×1'."""
        s = (s or "").strip()
        if not s or s in ("0", "0_0"):
            return "—"
        out = []
        for tok in s.split(sep):
            tok = tok.strip()
            if "_" in tok:
                pid, _, cnt = tok.partition("_")
                out.append("%s ×%s" % (self.prop_name(pid), fmt_num(cnt)))
            elif tok:
                out.append(self.prop_name(tok))
        return ", ".join(out)

    def need_build(self, s):
        """'10_2' -> 'Sawmill Lv 2' ; '0_0' -> '—'."""
        s = (s or "").strip()
        if not s or s == "0_0":
            return "—"
        bid, _, lv = s.partition("_")
        return "%s Lv %s" % (self.build_name(bid), lv)


def secs(s):
    """Seconds -> human duration (e.g. 9000 -> 2h 30m)."""
    try:
        n = int(float(s))
    except (ValueError, TypeError):
        return s
    if n <= 0:
        return "0s"
    d, n = divmod(n, 86400)
    h, n = divmod(n, 3600)
    m, s2 = divmod(n, 60)
    parts = []
    if d: parts.append("%dd" % d)
    if h: parts.append("%dh" % h)
    if m: parts.append("%dm" % m)
    if s2 and not d: parts.append("%ds" % s2)
    return " ".join(parts) or "0s"
