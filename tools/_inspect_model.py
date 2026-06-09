"""Dump schema + sample rows of key configs to a UTF-8 file for model mapping."""
import os, csv, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "data", "csv")
OUT = os.path.join(os.path.dirname(__file__), "_model.txt")

KEY = ["PropInfo", "PropSource", "PropCodex", "BuildBaseInfo", "BuildNeed", "BuildUnLockInfo",
       "CityLvUnlock", "UpExp", "HeroInfo", "HeroTalent", "SkillAwake", "NewSkillInfo",
       "SkillEffectInfo", "SoldierInfo", "ScienceInfo", "CodexInfo", "Buff", "TroopsEffect",
       "Formula", "FormulaQuickAdd", "RelicInfo", "VIPData", "StyleLv", "HeroFile", "HeroDes",
       "HeroBgDesLine", "HeroBook", "HeroSkin", "WarlordTalent", "HeroPosInfo"]

buf = io.StringIO()
for name in KEY:
    p = os.path.join(CSV, name + ".csv")
    if not os.path.exists(p):
        buf.write("\n### %s : MISSING\n" % name); continue
    rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
    cols = list(rows[0].keys()) if rows else []
    buf.write("\n### %s  (%d rows)\ncols: %s\n" % (name, len(rows), cols))
    for r in rows[:3]:
        buf.write("  " + " | ".join("%s=%s" % (k, (r[k] or "")[:40]) for k in cols if r.get(k)) + "\n")
open(OUT, "w", encoding="utf-8").write(buf.getvalue())
print("wrote", OUT, "(", len(buf.getvalue()), "chars )")
