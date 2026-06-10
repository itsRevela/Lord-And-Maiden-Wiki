# -*- coding: utf-8 -*-
"""Render notes/sim/status_effects.md from data/sim/status_effects.json.
Grouped by category, readable for the combat-sim work. UTF-8 file output only."""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "data", "sim", "status_effects.json")
OUT = os.path.join(ROOT, "notes", "sim", "status_effects.md")

d = json.load(io.open(SRC, encoding="utf-8"))

CAT_ORDER = [
    ("control", "Control / Crowd-Control (CC)"),
    ("taunt", "Taunt / Forced-Targeting & Cover"),
    ("dot", "Damage over Time (DoT)"),
    ("shield", "Shields"),
    ("lifesteal", "Lifesteal"),
    ("heal", "Healing"),
    ("cleanse", "Cleanse"),
    ("proc", "Procs / Conditional Triggers"),
    ("dmg_mod", "Damage Modifiers"),
    ("attr_mod", "Attribute Modifiers"),
    ("other", "Other / Special States"),
]
TYPE_LABEL = {1: "+1 positive", -1: "-1 negative", 0: "0 neutral"}

lines = []
lines.append("# Status Effects / Buffs & Debuffs - Combat-Sim Catalog")
lines.append("")
lines.append("Behavior catalog of every entry in `data/csv/Buff.csv` (76 rows), for the battle "
             "simulator. Generated from `data/sim/status_effects.json` "
             "(`notes/sim/_build_status_effects.py`). Behaviors are derived from in-game text "
             "(Language_SkillDes / Language_SysTip / Language_Game), the verified wiki "
             "(`wiki/Mechanics/Status-Effects.md`, `wiki/Reference/Game-Hints.md`) and the "
             "`NewSkillInfo` Effect/Buff strings that apply each buff; each entry cites its sources.")
lines.append("")
lines.append("**Key rules that govern every entry:**")
lines.append("- `type`: `1` positive / `-1` negative / `0` neutral (from Buff.csv `Type`).")
lines.append("- **Magnitudes** (damage %, heal coefficient, proc chance, duration) are NOT stored "
             "in Buff.csv; they live in the applying skill's `Effect`/`Buff` string. The final "
             "damage/heal numbers are resolved server-side - `UNKNOWN_SERVER_SIDE` (combat is "
             "server-authoritative; the client only sees inputs + the replay log).")
lines.append("- **Stacking** (`wiki/Reference/Game-Hints.md`): the *same* effect from the *same* "
             "skill type does not stack (only the highest applies); the same effect from "
             "*different* skill types adds together.")
lines.append("- **Prepared variants:** buff ids 83-86 are the telegraphed `(Prepared)` display of "
             "114-117 (Stun / Disarm / Silence / Chaos) - they resolve to the same real CC when they fire.")
lines.append("")

# index table
lines.append("## Index")
lines.append("")
lines.append("| id | name | type | category | prepared |")
lines.append("|---:|------|:----:|----------|:--------:|")
for k in sorted(d, key=lambda x: int(x)):
    v = d[k]
    lines.append("| %d | %s | %d | %s | %s |" % (
        v["id"], v["name_en"] or "(blank)", v["type"], v["category"],
        "yes" if v["prepared_variant"] else ""))
lines.append("")

for cat, title in CAT_ORDER:
    members = [d[k] for k in sorted(d, key=lambda x: int(x)) if d[k]["category"] == cat]
    if not members:
        continue
    lines.append("## %s" % title)
    lines.append("")
    for v in members:
        head = "### %d - %s" % (v["id"], v["name_en"] or "(blank)")
        if v["prepared_variant"]:
            head += " *(Prepared variant)*"
        lines.append(head)
        lines.append("")
        lines.append("- **Type:** %s" % TYPE_LABEL.get(v["type"], str(v["type"])))
        lines.append("- **Behavior:** %s" % v["behavior"])
        lines.append("- **Stacking:** %s" % v["stacking"])
        lines.append("- **Magnitude:** %s" % v["magnitude"])
        lines.append("- **Evidence:** %s" % "; ".join(v["evidence"]))
        lines.append("")

lines.append("---")
lines.append("*Catalog of inputs/rules only. The damage and healing formulas themselves are "
             "`UNKNOWN_SERVER_SIDE`. Regenerate with `python notes/sim/_build_status_effects.py` "
             "then `python notes/sim/_build_status_effects_md.py`.*")

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("wrote", OUT, "(%d lines)" % len(lines))
