# Lord and Maiden — Formulas & Mechanics

Derived from the decompiled `Assembly-CSharp` (`decompiled/eb46ed1b3cbb.cs`) cross-
referenced with the extracted configs (`data/`). **Important scope note:** this
game is **server-authoritative**. The client sends requests (`CSLogic_*`
protocol messages) and the server returns results. So **battle damage and the
exact power totals are computed server-side and are NOT in the client code.**
What the client *does* compute (and what the configs give us) is documented
below — that's everything needed for a stats wiki.

---

## Data encoding conventions (used across all configs)
Many fields pack multiple values into strings:
- **`id_count`** — a property/item id and amount. e.g. `Price`, `PropList`, `Effect`, `reward`.
- **`a+b+c`** — a list. e.g. `Effect = 84_1000000+78_1+330_1` = grant prop 84 ×1,000,000, prop 78 ×1, prop 330 ×1.
- **`need_build = BT_Lv`** — requires building-type `BT` at level `Lv` (`0_0` = none).
- **`RPoint = a,b,c,d`** — comma list (e.g. recommended attribute points).
- Prop/item names resolve via `PropInfo.xml` + `Language_PropName.xml`; most `{text}` tokens resolve via `data/localization.json`.

## Hero effective stats — **client-side, exact**
A hero's in-battle stats scale linearly with level (`decompiled` lines ~10431, ~77764, ~78095):
```
Attack (AD)  = HeroInfo.attack  + floor(HeroInfo.attack_grow  × HeroLevel)
Defense(DEF) = HeroInfo.defense + floor(HeroInfo.defense_grow × HeroLevel)
Ruin   (DMG) = HeroInfo.ruin    + floor(HeroInfo.ruin_grow    × HeroLevel)
Speed  (SP)  = HeroInfo.speed   + floor(HeroInfo.speed_grow   × HeroLevel)
```
- Source data: `data/csv/HeroInfo.csv` (base + `_grow`, plus `rare`, `type`, `RST`, `skill{0,1,2}_id`).
- Battle-code aliases: `AD`=Attack, `DEF`=Defense, `DMG`=Ruin, `SP`=Speed.
- Hero level cap / EXP curve: `UpExp.xml`. Talents: `HeroTalent.xml` (+`WarlordTalent.xml` for the Lord). Skills: `NewSkillInfo.xml` → `SkillEffectInfo.xml` (+`SkillAwake.xml`), names/desc via `Language_Skill*`.

## Troops / soldiers
`SoldierInfo.xml` (`data/csv/SoldierInfo.csv`) — per-soldier:
`Attack, Defense, Ruin, Health, Speed, Load, Power` and economy:
`Recruit{Food,Wood,Stone,Iron,Time}`, `Cure{Food,Wood,Stone,Iron,Time}` (cure = healing wounded).
Troop-wide modifiers: `TroopsEffect.xml`.

## Buildings
`BuildNeed.xml` (`data/csv/BuildNeed.csv`) — one row per (building id, level):
- Cost: `food, wood, stone, iron`
- `power` granted, `time` = **build time in seconds**
- `need_build` = prerequisite (`BT_Lv`), `effect` = what the level unlocks/boosts (`id_count` list)
Static building defs (positions, max count, base price, button layout): `BuildBaseInfo.xml`.
Building unlocks by city level: `BuildUnLockInfo.xml`, `CityLvUnlock.xml`. City layout: `CityBuildLayer.txt`, `WorldSysBuildXmlInfo.xml`.

## Crafting / production queues
`Formula.xml` (`data/csv/Formula.csv`) — each recipe:
- `PropList` = inputs (`id_count`, `+`-joined), `RetPropId` = output item
- **`NeedTime`** = seconds per craft, `Max` = max queue/stack, `FType`/`TypeName` = category (e.g. "Process")
`FormulaQuickAdd.xml` = quick-add/speed-up rules (base vs box prop, multiplier).
Queue state is tracked client-side (`FormulateQueue`: `remainTime`, `makeCount`, `totalTime`) but **completion time is validated server-side**.

## Science / tech, codex, relics, VIP, store
- `ScienceInfo.xml` (tech tree, costs/effects) + `Language_Science.xml`; alliance tech `UnionScience.xml`.
- `CodexInfo.xml` (collection bonuses → contributes `CodexPower`), `PropCodex.xml`.
- `RelicInfo.xml`, `VIPData.xml`, `StoreInfo.xml`/`Pay.xml`, `LordDress.xml`/`HeroSkin.xml`.

## Power (server-computed; client displays the parts)
The client receives a breakdown over the network (`OtherPlayerInfo` / `Player.Power`):
```
AllPower = BuildPower + SciencePower + HeroPower + SkillPower + LordPower + CodexPower
```
The per-component formulas are server-side. Each config above contributes its
domain's power (buildings → BuildPower via `BuildNeed.power`, codex → CodexPower, etc.).

## Combat — **server-side**
- The client sends `CSLogic_StartFight` (user, fight type/id, selected troop ids) → `NetMgr.srvConn.Send`.
- The server returns a **`BattleReport`/`BattleDetails`**:
  `FightRet` (result), `PlayerNameA/B`, `AttackKill[]`/`DefenderKill[]` (`FightKill`),
  `InitStateList` (`FightInitState`), `RoundDataList` (`RoundData`, per round), `FightMVPs`, `Awards[]`.
- So the exact **damage equation is not in the client**. The client only computes the inputs
  (effective hero/troop stats above), shows team buffs (`TeamBuffInfo.heroEff`/`soldierEff`), and replays the report.
- Buff catalog: `Buff.xml` (`data/csv/Buff.csv`) — `Type = +1` beneficial / `-1` detrimental
  (e.g. "DMG Dealt Increased/Reduced", "DMG Taken Increased/Reduced").

## What this means for the wiki
- **Fully documentable from data:** hero/soldier base stats + growth, building costs/times/power,
  crafting recipes + queue times, science/skills/talents/codex, costs and unlock chains.
- **Server-side (treat as black box):** exact battle damage math and exact power-total formulas.
  These can only be characterized empirically (in-game observation) or from a server leak, not the client.
