# Battle Mechanics

> 📘 **Community strategy.** Rebuilt from a Steam Community guide by **Lofthouse** — credit to the original author. This is player experience and screenshot-transcribed info, not data extracted from the game files, and may be out of date (originally posted 2022). Sources: [original guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2759156753) · [archive](https://github.com/itsRevela/Lord-And-Maiden-Guides).

How a battle actually plays out, how to read skill descriptions, and how a unit's fighting stats are built up. For the data-side rules (troop restraint, target %, skill order) see [Stats, Formulas & Mechanics](Stats-and-Formulas.md); for status-effect definitions see [Status Effects](Status-Effects.md).

## How a fight resolves

- A team is **1 Commander + 2 units**. You **win** when the enemy Commander loses all their troops; you **lose** when your Commander loses all theirs.
- **Pre-battle phase:** many *Strategy* (blue) skills apply here — buffs, debuffs, or effects that only switch on in later rounds.
- **8 rounds of combat.** Each round, every unit (both teams) acts in order of its **Speed**. On its turn a unit makes a **normal attack**, then rolls the chance for any **Chase / Tactical** skills to fire.
- **Targeting:** normal attacks hit **one random enemy**; skills hit random targets unless the text says otherwise. The **Commander is 25% less likely** to be targeted, which is why a DPS Commander is usually protected by its two supports.
- **Impasse:** if both Commanders still have troops after 8 rounds, the teams pause ~1 minute, then you may wait for another 8-round bout, retreat to heal, or re-engage immediately. (Exact behaviour varies by game mode.)
- Read the **battle log** for a full breakdown; once you build a **Library** you can simulate battles.

> **Key insight:** the damage an enemy deals scales largely with their **troop numbers**, so cutting the enemy's troop count is the best protection. Skills that give an early edge (strong first-3-rounds effects) let you thin the enemy while staying safe.

## Reading skill descriptions

| Phrase | What it means |
|---|---|
| "Affected by X attribute" | The effect scales with that stat — roughly **×** for every **200** points of the named stat (Attack / Speed / Defence / Destruction). |
| Damage Coefficient X | Expected damage vs. a normal attack; **1.00 = one normal attack's** worth. |
| Healing Coefficient X | Same idea, for healing. |
| Strategy skill (blue) | Fires before battle or on a stated round; **cannot** be stopped by status effects. |
| Tactical skill (purple) | Has a per-round chance to fire on the unit's turn. |
| Passive skill | Always-on self-buff; cannot be stopped by status effects. |
| Chase skill | Chance to fire **after the unit's normal attack**. |
| 1 Round Preparation | The effect applies at the **start of the unit's next turn**, not immediately. |
| Counterattack | Strikes back at any enemy that hits it with a normal attack. |
| Aid | Redirects attacks aimed at allies onto itself. |
| Combo attack | The unit makes its normal attack **twice** in a round (Chase can trigger on both). |
| Shield | Blocks the first instance of damage taken. |
| Splash | Normal attacks also deal a % of the hit to the other two enemies, **ignoring defence**. |
| "Real damage" / "strong attack" | A fixed extra hit based only on **troop count + the unit's in-battle Attack**; triggers on every hit of multi-hit skills. |
| "Burning" / "Spell damage" | Damages the enemy **before** they take their turn. |
| "Your own troops" | Affects only the skill-holder; **"2/3 of our troops"** = that many random allies. |

## What stats a unit fights with

In-battle stat = **Unit stats + Troop stats** (troop stats are boosted by armour, technology and titles **before** being added). Unit stats come from four sources:

1. **Levelling** — each stat grows by its own per-level amount (`stat(L)=base+floor(growth×L)`; see [hero pages](../Heroes/Heroes.md)).
2. **Stat points** — 1 free point per level, plus **10 per Advance** (Advances need hero dupes).
3. **Favorability** — raises **all stats by up to 30** (see [Favorability](../Progression/Favorability.md)).
4. **Race & troop bonus** — **+3%** all stats with 2 same-race units, **+5%** with 3; up to **+10%** to certain stats when all three units use the **same troop type**.

### Worked example — how in-battle Attack is built
*(Transcribed from the guide's diagram; the arithmetic and the troop value check out against our data — 90 is an actual troop Attack stat from [Soldiers](../Soldiers/Soldiers.md).)*

| Component | Value | Note |
|---|---|---|
| Unit (hero) Attack | 204 | from level + stat points + favorability |
| × team bonus (+3%) | 210.12 | 204 × 1.03 (2 same-race units) |
| Troop base Attack | 90 | the assigned troop's Attack stat |
| + armour / tech / title / etc. boosts | +81 | stacked %: +12% (10.8) +65.5% (58.95) +6.5% (5.85) +3% (2.7) +3% (2.7) |
| Troop total | 171 | 90 + 81 |
| **Calculated Attack** | **381.12** | 210.12 (unit) + 171 (troop) |

So **in-battle Attack ≈ (Unit Attack × team/race multiplier) + (Troop Attack × (1 + Σ boosts))**. The exact boost percentages depend on your armour, technology and title, so this is the *shape* of the calculation rather than fixed numbers. Defence, Destruction and Speed are built the same way. *(The in-game "actual" value can differ from the calculated one by a fraction due to rounding.)*

---
*Auto-generated from game data by `tools/wikigen/build.py`. Do not edit by hand.*
