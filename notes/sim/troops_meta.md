# troops_meta — decode notes

Output: `data/sim/troops_meta.json`. Generator: `notes/sim/_gen_troops_meta.py`
(re-runnable; reads only `data/csv/*.csv`, writes the JSON). Cross-checked against
`wiki/Soldiers/Soldiers.md` and `wiki/Military/Troop-Combinations.md` — all values agree.

All CSV row indices below are `csv.DictReader` data-row numbers (0-based); the raw
file line = data-row + 2 (1 header + 1-based). Decompiled cites are line numbers in
`decompiled/Assembly-CSharp/eb46ed1b3cbb.decompiled.cs`.

## 1. troops — `SoldierInfo.csv`
4 types (`type`: 1 Infantry, 2 Archer, 3 Cavalry, 4 Chariot), 6 tiers each
(`level` 1-6). T6 is the max tier (flagged `is_max_tier`). Stats taken verbatim:
`attack, defense, ruin, health, movement_speed, load, power`. T6 highlights:

| Type | ATK | DEF | Ruin | HP | MoveSpd | Load | Power | src row |
|---|---|---|---|---|---|---|---|---|
| Infantry | 23 | 75 | 24 | 255 | 40 | 17 | 200 | SoldierInfo.csv:5 |
| Archer   | 130 | 57 | 18 | 60 | 45 | 15 | 200 | SoldierInfo.csv:11 |
| Cavalry  | 42 | 120 | 15 | 110 | 55 | 14 | 200 | SoldierInfo.csv:17 |
| Chariot  | 48 | 36 | 120 | 95 | 35 | 60 | 200 | SoldierInfo.csv:23 |

All 6 tiers retained per type under `tiers[]`. Type names from `GetSoldierName`
(decompiled:9056).

## 2. soldier_combinations — `TroopsEffect.csv` type 1 (rows 0-7)
Per soldier type: a **Basic** (2-of-type, `number=2`) and **Advanced**
(3-of-type, `number=3`) bonus. `condition` == `SoldierInfo.type`.

`addtion` encoding uses the **EntryEffect id space** with the soldier-% Size=10000,
so a raw `500` = 5% and `1000` = 10% (EntryEffect.csv: 25=Soldier HP, 30=Soldier ATK,
35=Soldier DEF, 40=Soldier DES, 45=Soldier March Spd, all DataType 2 / Size 10000).

| Combo | Trigger | Effect (decoded) | src row |
|---|---|---|---|
| Basic Infantry | 2 Infantry heroes | Soldier HP +5%, Soldier DEF +5% | TroopsEffect.csv:0 |
| Basic Archer | 2 Archer heroes | Soldier ATK +5%, Soldier DEF +5% | :1 |
| Basic Cavalry | 2 Cavalry heroes | Soldier March Spd +5%, Soldier DEF +5% | :2 |
| Basic Chariot | 2 Chariot heroes | Soldier DES +5%, Soldier DEF +5% | :3 |
| Advanced Infantry | 3 Infantry heroes | Soldier HP +10%, Soldier DEF +10% | :4 |
| Advanced Archer | 3 Archer heroes | Soldier ATK +10%, Soldier DEF +10% | :5 |
| Advanced Cavalry | 3 Cavalry heroes | Soldier March Spd +10%, Soldier DEF +10% | :6 |
| Advanced Chariot | 3 Chariot heroes | Soldier DES +10%, Soldier DEF +10% | :7 |

**Trigger condition:** counts how many of the 3 heroes in a team field that soldier
type. A hero's soldier type = its `HeroInfo.RST` (decompiled:10428, 17380-17392).
**Stacking:** Basic and Advanced are exclusive thresholds (keyed by `number` 2 vs 3) —
with 3 matching heroes only the +10% Advanced row applies.

## 3. race_combinations — `TroopsEffect.csv` type 2 (rows 8-13)
Per race (`condition` == `HeroInfo.Type`: 1 Human, 2 Orc, 3 Elf; `GetHeroRaceDesTip`
decompiled:7857). Basic (2-of-race) = Hero All Attributes +5; Advanced (3-of-race) =
+10. "All Attributes" decodes to the 4 hero stats `51 ATK + 52 DEF + 53 DES + 50 ATK
Spd`, each +5 or +10 (flat; EntryEffect DataType 1 / Size 1).

- Basic Human/Orc/Elf: `51_5+52_5+53_5+50_5` → all 4 hero stats +5 (rows 8/9/10).
- Advanced Human/Orc/Elf: `51_10+52_10+53_10+50_10` → all 4 hero stats +10 (rows 11/12/13).

**Stacking:** mutually exclusive thresholds keyed by `number` (2 vs 3). With 3
same-race heroes only the +10 Advanced row applies — NOT +5 and +10 together.
(Race→combo name mapping in the CSV: Human=人族, Orc=兽人, Elf=精灵; note the table in
`Troop-Combinations.md` mislabels the race rows with soldier types in its "Soldier
Type" column, but the `name_en` and race effect are correct — the JSON uses race.)

## 4. affection — `GoodFeel.csv`
`value` = Hero All Attributes bonus at that affection level. Curve lv0→lv11:
0,1,2,3,5,7,9,12,15,18,22,**30**. Max = **+30 at lv 11** (GoodFeel.csv:11). Full
curve + `upLvExp` retained in JSON.

## 5. talents — `HeroTalent.csv` (5 TalentTypes, lv 0-25)
Hero awakens talent levels; the displayed bonus is the **cumulative sum** of every
awakened level's `Effect` value (decompiled:85893-85910: sums `Effect.Split('_')[1]`
over `WakeLevelList`; Type 1 shows `+{num:N0}` flat, else `+{num*100}%`).

Maxed (all 25 levels) cumulative totals — verified by summing the CSV column:

| Type | Name | Effect id | Maxed | total points |
|---|---|---|---|---|
| 1 | Commander | 59 | Soldiers Quantity **+3000** (flat) | 25 |
| 2 | Infantry  | 53 | Infantry HP **+30%** | 25 |
| 3 | Archer    | 19 | Archer ATK **+30%** | 25 |
| 4 | Cavalry   | 25 | Cavalry DEF **+30%** | 25 |
| 5 | Chariot   | 52 | Chariot DES **+30%** | 25 |

**Effect namespace (Task 5 deliverable):** `HeroTalent.Effect` uses a *talent-internal*
id space, **NOT** the EntryEffect catalog. Decoded:
`59` = Soldiers Quantity (flat), `53` = Infantry HP, `19` = Archer ATK, `25` = Cavalry
DEF, `52` = Chariot DES — the last four are percent and the raw value is already a
decimal fraction (e.g. `53_0.06` = +6%). Names are confirmed two ways: (a) each row's
own `Des`/`Des_en` (e.g. HeroTalent.csv:1 `Des='{带兵数量} +50'`/`Des_en='Soldiers
Quantity +50'`, `Effect='59_50'`); (b) the soldier-attribute switch in `GetBuffName`
(decompiled:35835-35954) where case 19='{弓兵}{攻击}' Archer ATK, 25='{骑兵}{防御}'
Cavalry DEF, 52='{战车}{破坏}' Chariot DES, 53='{步兵}{生命}' Infantry HP.
**Overlap trap for the simulator:** EntryEffect 53 = Hero DES, but Talent 53 =
Infantry HP — the two namespaces are NOT interchangeable.

**Awaken-point cap:** total awaken points a hero has = `Rare*10` (decompiled:85917).
Maxing all 5 talents to lv25 costs 125 points, so even a 6-star (60 pts) cannot max
every talent. The per-type maxed totals above are the cap *if that one talent is fully
taken*.

## 6. restraint — what `HeroInfo.RST` means
`RST` is the hero's **commanded soldier type**: the client assigns
`hero.SoldierT = heroInfo.RST` (decompiled:10428, 17380-17392, 171702-171714). Values
map to the same space as `SoldierInfo.type`: 1 Infantry, 2 Archer, 3 Cavalry, 4
Chariot. `RST` *also* sets the hero's default attribute-point distribution when its
`RPoint` field is empty (decompiled:10459-10477 and 80892-80916): RST1 favors
DEF+Speed, RST2 ATK+Ruin (0.8 split), RST3 DEF+ATK, RST4 Ruin+ATK — this is the
`RST_ARCHETYPE` already in resolver.py.

**Counter triangle:** `Infantry -> Archer -> Cavalry -> Infantry` (each restrains the
next; cyclic). **Chariot has NO restraint relationship.** Source: `Tips.csv` row
Id=350 (data-row 17) `des_en` = "Soldiers Of Different Types Have A Restraint Effect,
Infantry->Archer->Cavalry->Infantry, When Soldiers Are Restrained, Damage Dealt Is
Reduced By 25%." Corroborated by `Language_SysTip.csv` data-rows 289 & 304, and the UI
strings `Language_Game.csv` rows 2209/2210 ("Soldier Restraint Relationships" / "No
Restraint Relationship").

**Magnitude:** restrained soldiers deal **−25%** damage. The −25% is a stated rule;
the client does NOT apply it — battle damage arrives already resolved as
`BehaviourRet.RetVal` from the server (decompiled:19506), and no client-side
soldier-type damage multiplier (no `0.75` factor keyed to `SoldierT`) exists in combat
code. → `restraint.restrained_damage_modifier.application = "UNKNOWN_SERVER_SIDE"`.

## 7. preferred_soldier
No separate selectable "preferred soldier" bonus exists. A hero is **locked** to the
single soldier type given by its RST (`hero.SoldierT = heroInfo.RST`). The only
RST-linked client effects are (a) which soldier type the hero fields and (b) the
default RPoint attribute split (§6). The per-soldier-type talents (§5 types 2-5) are
the nearest stat boost, but they are independent of RST. No "preferred / adept /
suited soldier" bonus string or multiplier was found in the decompiled client or
`Language_SysTip`. Any matching-type bonus, if it exists, is server-side. →
`preferred_soldier.matching_bonus_magnitude = "UNKNOWN_SERVER_SIDE"`.

## UNKNOWN_SERVER_SIDE items
1. `restraint.restrained_damage_modifier.application` — the −25% restraint penalty is
   a documented rule but is applied server-side; client only receives resolved damage.
2. `preferred_soldier.matching_bonus_magnitude` — no client-side stat bonus for a hero
   using its RST-matching soldier type beyond fielding that type; any such bonus is
   server-side.
