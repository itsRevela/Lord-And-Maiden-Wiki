# Stats, Formulas & Mechanics

How the numbers work. **All formulas here are verified from the decompiled game code**; where a calculation is server-side, that is stated explicitly.

## Stat & data conventions
- Packed lists use `id_count` (a prop id and amount), joined by `+`. Example: `Effect = 84_1000000+78_1` → *Reserve Soldiers Capacity ×1,000,000, Number Of Troops ×1*.
- `need_build = BuildingType_Level` (`0_0` = no requirement).
- The four combat stats are **Attack (ATK / AD)**, **Defense (DEF)**, **Ruin (DES / DMG)**, **Speed (SP)**.

## Hero stat growth — *client-side, exact*
A hero's effective stat at level *L*:
```
stat(L) = base + floor(growth × L)
```
Applies to Attack, Defense, Ruin and Speed independently (base + per-stat growth from the hero's data). **Hero max level = 80.** Per-hero level tables are on each hero page; bases and growth are in the [roster](../Heroes/Heroes.md).

### Hero races

| # | Race |
|---|---|
| 1 | Human |
| 2 | Orc |
| 3 | Elf |

### Hero roles (Job)

| # | Role |
|---|---|
| 1 | DPS |
| 2 | Heal |
| 3 | CC (Control) |
| 4 | Buff |
| 5 | Debuff |

### Skill types

| # | Type |
|---|---|
| 1 | Strategic |
| 2 | Tactical |
| 3 | Passive |
| 4 | Pursuit |

### RST — recommended troop & stat-point archetype
When a hero leads troops, surplus attribute points are auto-allocated by their RST (verified from code):

| RST | Soldier type | Point allocation |
|---|---|---|
| 1 | Infantry | 60% Defense, remainder Speed |
| 2 | Archer | 80% Attack, remainder Ruin |
| 3 | Cavalry | 60% Defense, remainder Attack |
| 4 | Chariot | 60% Ruin, remainder Attack |

## Troops
Soldier base stats and recruit/cure costs are fixed per tier — see [Soldiers](../Soldiers/Soldiers.md). Each of the 4 types (Infantry, Archer, Cavalry, Chariot) has tiers T1–T6. Composition bonuses: [Troop Combinations](../Military/Troop-Combinations.md).

## Build / research / craft time
Base times come straight from the data (seconds): buildings [`time`](../Buildings/Buildings.md), research [`time`](../Research/Science.md), crafting [`NeedTime`](../Crafting/Formulas.md). In-game speedups and reductions are applied on top (server-validated).

## Power
Total Power is **computed server-side** and sent to the client as a breakdown:
```
AllPower = BuildPower + SciencePower + HeroPower + SkillPower + LordPower + CodexPower
```
Each system contributes its `power` value (e.g. each building level, each tech level, each codex set lists a Power amount in its tables).

## Combat — *server-side*
Battles are resolved on the server. The client sends the chosen troops (`CSLogic_StartFight`) and receives a **Battle Report** containing the result, per-round data, kills and MVPs. The exact damage equation is therefore not present in the client. What the client (and this wiki) provides: effective hero/troop stats, skill and buff definitions, and troop-composition bonuses. See [Buffs](Buffs.md) (`+1` beneficial, `-1` detrimental).

---
*Auto-generated from game data by `tools/wikigen/build.py`. Do not edit by hand.*
