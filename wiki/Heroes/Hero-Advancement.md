# Hero Advancement

A hero grows along **three separate tracks** — **Level**, **Advance**, and **Breakthrough** (skill *Awaken* is a fourth, per-skill track covered on the [Skill Catalog](Skills.md)). All are done from the hero's info panel.

```
Recruit (Lv1)  →  Level up with Hero Exp (cap Lv60)
             →  ADVANCE  (AdvLv 1..★)   +10 stat points & more troops each
             →  BREAKTHROUGH (BreakLv 1..20, 4★/5★ only)  +1 level cap & +3/+5 points each
             →  Max: Lv80, AdvLv = ★, BreakLv = 20
```

## Level
Hero EXP (Hero Exp Books / prop) levels a hero. The base level cap is **60**; raising it further requires Breakthroughs. Each level grants **+1** freely-assignable stat point.

## Advance (AdvLv)
Advancing fills a hero's stars. A hero can advance up to **its star rarity** (★3 → 3 Advances, ★4 → 4, ★5 → 5). **Each Advance grants +10 freely-assignable stat points** and raises the hero's **max soldier count**. The material is **duplicate copies of that hero** — or a **Universal Advance Card**, which substitutes for a duplicate.

**Duplicates needed per Advance:**

| Advance | Duplicates |
|---|---|
| 0 → 1 | 1 |
| 1 → 2 | 1 |
| 2 → 3 | 2 |
| 3 → 4 | 2 |
| 4 → 5 | 3 |

**Max soldier count** = `2,000 + Level×500` plus an Advance bonus:

| AdvLv | Bonus troops |
|---|---|
| 1 | +1,000 |
| 2 | +2,000 |
| 3 | +4,000 |
| 4 | +6,000 |
| 5 | +10,000 |

## Breakthrough (BreakLv)
Once a hero is **fully Advanced** (AdvLv = its rarity) **and** has reached **Lv 60**, it can **Breakthrough** — **★4 and ★5 heroes only** (★3 heroes stop at Lv 60). Each Breakthrough:
- raises the **level cap by +1** (Lv 60 → up to **Lv 80** at BreakLv 20), and
- grants **+3** (★4) / **+5** (★5) freely-assignable stat points.

The material is a **same-rarity duplicate hero** — or a **Breakthrough Card** (substitute). Max **BreakLv = 20**.

## Stat (Allocable) points
All the points above pool into one total you assign freely across **Attack / Defense / Ruin / Speed** (and can **reset**; an auto-allocate follows the hero's [RST](../Mechanics/Stats-and-Formulas.md) recommendation):

```
total points = AdvLv×10  +  (Level − 1)  +  (5 if ★5 else 3) × BreakLv
```

## The advancement cards
| Card | Use |
|---|---|
| Universal Advance Card | Substitutes for any hero duplicate when **Advancing**. |
| Breakthrough Card | Substitutes for a same-rarity duplicate when doing a **Breakthrough**. |
| Skill Exp Card | Converts into **Skill EXP** (for levelling skills). |
| Universal Codex Card | Substitutes for a hero when submitting to the **Hero Codex** (a separate system). |

*(Server-side: exact duplicate counts consumed per Breakthrough aren't in the client — the UI stages up to 10 cards at once toward the BreakLv-20 cap.)*

---
*Auto-generated from game data by `tools/wikigen/build.py`. Do not edit by hand.*
