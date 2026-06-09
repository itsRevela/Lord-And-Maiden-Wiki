"""Shared data loader + cross-reference resolver for the wiki generator.

Everything is read from data/csv (extracted from the game). IDs are resolved to
English names so generated pages never contain a bare numeric id without a name.
"""
import os
import csv
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_DIR = os.path.join(ROOT, "data", "csv")


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
        return clean(r.get("name_en") or r.get("name")) if r else ("Skill#%s.%s" % (st, sid))

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
