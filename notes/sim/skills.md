# Skill system — decoded reference

Source of truth: `data/csv/NewSkillInfo.csv` (416 skills). Decompiled cites refer to
`decompiled/Assembly-CSharp/eb46ed1b3cbb.decompiled.cs`. Buff ids resolve against
`data/csv/Buff.csv`. Machine-readable output: `data/sim/skills.json`.

Combat is server-authoritative: the client exposes every skill INPUT (coefficients,
trigger rates, targets, durations, buff ids) and the stated rules, but **not** the
hidden damage formula — that stays `UNKNOWN_SERVER_SIDE`.

## 1. Column reading order (verified)

The XML/CSV columns are read positionally in `ReadSkillInfoXml`
(decompiled:171076-171098) into the `SkillInfo` class (decompiled:2833-2888):

`ST, ID, Rare, MaxUse, SkillStone, Icon, Name, Des, ImpactBy, UpDes, UpType, UpVal,
InitVal, SkillP, ReadyRound, Effect, Buff, Dbuff` (+ `Name_en/Des_en/UpDes_en`).

## 2. Skill type (`ST` column)

| ST | Name | Activation | Effect lives in |
|----|------|-----------|-----------------|
| 1 | Strategic | Applied **before battle starts** (`{战斗开始前生效}`, decompiled:9908-9911). 130 skills. | `Buff` column only |
| 2 | Tactical | Active in-combat skill; trigger probability `SkillP` (decompiled:9912-9915). 206 skills. | `Effect` (action) + `Buff` (side effect) |
| 3 | Passive | Active the **whole battle** (`{整场战斗中生效}`, decompiled:9916-9918). 42 skills. | `Buff` column only |
| 4 | Pursuit | Follow-up after a normal ATK; trigger probability `SkillP` (decompiled:9920-9923). 38 skills. | `Buff` (+ a few `Effect`) |

## 3. Effect / Buff / Dbuff string format — the 12-token group

A skill string is **one or more 12-token groups joined by `+`**; each group's tokens
are joined by `_`. The **identical 12-token layout is used by the `Effect`, `Buff`
and `Dbuff` columns** (NewSkillInfo.csv). Division of labour:

- **`Effect`** = the skill's active ACTION (deal damage / heal / cleanse). Populated for
  104 Tactical + 5 Pursuit skills (Strategic/Passive have no active action -> `0`).
- **`Buff`** = the status/stat modifier the skill ALSO applies (374 skills). For
  Strategic/Passive this is the entire skill.
- **`Dbuff`** = unused in this build — **always `0`** across all 416 rows. (The class
  field exists, decompiled:2886-2887, but no skill populates it.)

### Token layout (positions 0..11)

| # | Field | Meaning | Evidence |
|---|-------|---------|----------|
| 0 | `actionType` / `buffId` | In `Effect`: action type (see §4). Elsewhere: a `Buff.csv` buffId (see §6). | `101_..` rows = "ATK", `102_..` = "Restore Life", buffId 114 = Stun, etc. |
| 1 | `fromRound` | Starting round. `0`/`1` = from round 1; `4` = from round 4; `5` = from round 5. | token[1]=1↔"In The First N Rounds"; =5↔"From The 5th Round"; =4↔"From The 4th Round" (ST=1 scan, all 130 rows) |
| 2 | `targetCategory` | Who it hits (see §5). | token[2]=2↔"Enemy Troops", =4↔"our Troops", =7↔"Own Troop", =10↔"Enemy Commander", =0↔"the target enemy" |
| 3 | `targetCount` | Number of targets. | **71/71 exact match** vs "ATK N Enemy Troop(s)" |
| 4 | `triggerChance` | Per-group apply/hit probability (`1` = guaranteed). | Drives "Launch X-Y ATK" ranges and "NN% Probability In A …State" |
| 5 | `coefficient` | DMG / healing coefficient. | == `InitVal` at level 0 for the primary action (**66/66 non-prep skills**); on `ReadyRound=1` skills it is the *reduced* in-string value (all 26 coef mismatches are prep skills) |
| 6 | `flatMagnitude` | Flat stat amount, used when `coefficient`(5)==0. | token[6]=11.4 ↔ "DEF Attribute Increased 11.4"; =8.0 ↔ "ATK Reduced 8.0" |
| 7 | `layers` / `minDur` | Shield layers / hit count / minimum duration. | token[7]=1↔"Gain 1 Layer Of Shield"; =2↔"2 Layers"; Eternal Flame =3 ↔ min of "2~3 Rounds" |
| 8 | `maxStacks` | Max stack layers. | Adversity token[8]=10 ↔ "Up To 10 Layers"; Spirit Gather =8 ↔ "Stack…8" |
| 9 | `duration` | Effect duration in rounds (`0` = instant / whole battle). | token[9]=2 ↔ "Lasting For 2 Rounds" |
| 10 | `flagA` | Rendering / mechanic flag. `1` on direct ATK & heal actions and most timed buffs; `0` on instant cleanse/dispel actions and some pre-battle stat grants. | 233/234 ATK groups have flagA=1 |
| 11 | `affectedByAttr` | `1` = magnitude scales with the caster's DEF/DES attribute; `0` = fixed. | **115/115 exact match** vs "(Affected By …Attribute)" / "(Not Affected By Attribute)" |

The client does NOT switch on these tokens to compute damage (server-side); it uses
them only to render tooltips and play VFX. The authoritative cross-check for token
meaning is therefore the per-skill `Des_en` string, correlated above.

### Multi-group examples

- `Sword Break` (Tactical 12) `Effect = 101_0_2_2_1_0.50_0_0_0_0_1_0` → ATK 2 enemy troops, coef 0.50.
- `Rift` (Tactical 100) — "Launch 3-7 ATK on 1 enemy" = 7 groups of `101`; first 3 have
  `triggerChance=1` (guaranteed), last 4 have `triggerChance=0.3` → 3 guaranteed + up to 4 = 3-7 hits.
- `Divine Light` (Tactical 49) `102_..` + `121_0_0_2_0.50_..` → heal, then 50% chance to purify.
- `Biting` (Tactical 17) `Effect=101_0_2_1_..` + `Buff=14_0_0_1_1_0_8.0_0_0_2_0_1` → ATK,
  then apply buffId 14 (ATK Reduced) flatMagnitude 8.0 for 2 rounds on the same target (targetCategory 0).

## 4. `actionType` enum (token[0] in the `Effect` column)

Only four action types exist; everything else is a buff id.

| actionType | Meaning |
|-----------|---------|
| 101 | ATK enemy (deal damage) |
| 102 | Heal / Restore Life |
| 121 | Purify — cleanse **own** harmful effects (from Tactical/Pursuit skills) |
| 122 | Dispel — remove **enemy** beneficial effects (from Tactical/Pursuit skills) |

(101 also appears inside `Buff` strings for counterattack/pursuit-ATK references,
e.g. buffId 81 Counter, Pursuit skills.)

## 5. `targetCategory` enum (token[2])

| value | Meaning |
|-------|---------|
| 0 | Inherit the action's target ("the target enemy") — used by side-effect buffs attached to an attack |
| 2 | Enemy Troops |
| 4 | Our Troops (multi-select) |
| 6 | Assist / Protect target (e.g. Star Shield, Block — protect our troops / Assist buff 120) |
| 7 | Own / Self |
| 10 | Enemy Commander (single, back-line leader) |

## 6. Buff / state ids (token[0] outside the `Effect` column)

Resolved against `data/csv/Buff.csv` (76 rows; `Type` 1=positive, -1=negative, 0=neutral).
Key states referenced by skills:

- **Stat mods:** 5/6 DMG Dealt ±, 7/8 DMG Taken ±, 9-12 ATK/DEF/DES/Spd up, 13 All up,
  14-17 ATK/DEF/DES?/Spd down, 18 All down, 29-40 Normal/Tactical/Pursuit DMG dealt/taken ±,
  42 Soldier HP up, 43/44 Curse/Burn DMG taken down, 47 Real DMG up.
- **Control / states:** 70 Assault, 73 Shield, 74 First Aid, 83-86 Stun/Disarm/Silence/Chaos
  (Prepared variants), 87 Heal, 88 Instant, 89 Eternal, 106 Blood Sucking, 107 Self-Heal,
  108 Burn, 109 Curse, 113 Concentration, 114 Stun, 115 Disarm, 116 Silence, 117 Chaos,
  118 Taunts, 119 Heal Ban, 120 Assist, 125 Superconducting, 139 Purification, 140 Sneak
  Attack, 150 Insight, 154 Arcane Missile, 155 Precision Strike, 157 Combustion Aid,
  158 Element Burst, 159 Pursuit Splash.
- **Chance procs (Buff.csv ships these untranslated):** 79 Chance Haste, 80 Chance Combo,
  81 Chance Counter, 82 Chance Splash, 111 Chance Dodge.

### buffIds referenced by skills but ABSENT from Buff.csv → `UNKNOWN_SERVER_SIDE`

Names below are inferred from the citing skill's own `Des_en`; exact mechanics are
resolved server-side and absent from the client. In `skills.json` these render with a
`(UNKNOWN_SERVER_SIDE)` suffix where not mapped.

| buffId | Cited by | Inferred meaning |
|--------|----------|------------------|
| 72  | Exploding Flame (S2.73), Dragon Breath (T2.1019) | Burn detonation — settle remaining Burn DMG |
| 112 | Heart Net (S1.44) | Disarm variant (round-1 control) |
| 141 | Jungle Chase (P4.26) | Combined Disarm + Silence control |
| 151 | Flash Fire (P4.14) | Chained / extra pursuit trigger |
| 152 | Polaris (P4.37) | Pursuit empower — carried pursuits 100% trigger |
| 153 | Heart Chain (P4.28) | Multi pursuit — additional pursuits |
| 156 | Eternal Flame (T2.151) | Curse DMG-over-time |

## 7. Attack-type taxonomy

Damage is dealt by three channels, each with its own ± DMG buff family (see §6):

- **Normal ATK** — the auto-attack each round. Buffs 29/30 (dealt ±), 35/36 (taken ±).
  Pursuit skills (ST=4) and counter/combo/splash procs key off "When ATK Normally".
- **Tactical Skill** — ST=2 active skills (the `Effect` action). Buffs 31/32 (dealt ±),
  37/38 (taken ±).
- **Pursuit Skill** — ST=4 follow-up after a normal ATK. Buffs 33/34 (dealt ±),
  39/40 (taken ±).

Special damage flavours referenced by skills: **Burn** (108, DoT, "Burning DMG Taken"),
**Curse** (109, DoT, "Curse DMG Taken"), and **Real DMG** (47, "造成真实伤害提高").
Skill-stone equipping rule (Language_Game): Strategic = one stone per team; Tactical /
Passive / Pursuit may equip +1 additional stone.

## 8. Max-level value computation (verified on all 416 rows)

```
value(level L) = InitVal + L * UpVal       # L = 1..10  (decompiled:9940-9949)
maxedValue     = InitVal + 10 * UpVal       # level 10 = cap
```

`ImpactBy == InitVal + UpVal*10` holds for **all 416 skills** → `ImpactBy` is exactly the
maxed value, and **max skill level is 10**. By construction `UpVal == InitVal/10` and
`InitVal == ImpactBy/2`, so the level-1 value is `InitVal` and level-10 doubles it.

Rendering (decompiled:9938): `UpType ∈ {1, 5-8, 19-40, 43-47}` → shown as **percent**
(`value*100%`); all other `UpType` → **flat number**. `UpType` otherwise names the scaled
quantity (e.g. 2 = DMG coefficient, 3 = healing coefficient, 9 = ATK up, 45 = trigger
probability). `UpDes_en` is the human label ("DMG Coefficient", "Healing Coefficient",
"Effect Trigger Probability", …).

### Other fields

- **`SkillP`** — base trigger probability for ST=2/4 (Tactical/Pursuit), e.g. 0.35 = 35%.
  ST=1/3 ignore it (always active). When `UpType == 45` the **probability itself** scales
  with level: `SkillP == ImpactBy` and `triggerProbAtMax = InitVal + 10*UpVal == SkillP`
  (decompiled:9914, 9922). `skills.json` exposes `triggerProbAtMax`.
- **`ReadyRound`** — preparation rounds before the skill fires ("N Round Preparation Time").
  Almost always 0 or 1. On `ReadyRound=1` skills the coefficient embedded in the `Effect`
  string (token[5]) is the *post-preparation* value, lower than the headline `InitVal`
  (e.g. Sharp Claw InitVal 1.26 vs in-string 1.20). `maxedValue` is computed from
  `InitVal/UpVal` (the headline scaling), not the reduced token.
- **`MaxUse`** — `{可学习次数}` = how many times the skill can be **learned/equipped**, NOT a
  level cap. `MaxUse == 0` → relic/innate skill (`{圣物}`); `MaxUse > 0` → awakenable
  (`{觉醒}`) (decompiled:5880-5889, 88538, 133265). It does NOT participate in value scaling.
- **`SkillStone`** — `1` = skill is eligible for a skill stone; the loader auto-generates
  5 stone-level prop items per such skill (decompiled:171136-171164). 207 of 416 are
  eligible. `ImpactBy` ("受X影响") is the column header the stone's per-level value uses.
- **`Rare`** — star rarity (3/4/5). Higher rarity skills carry larger coefficients.

## 9. Output: `data/sim/skills.json`

Array of 416 objects, sorted by `(st, id)`. Per skill: `key` ("ST_ID"), `st`, `st_name`,
`id`, `name_en`, `des_en`, `rare`, `skillStone` (bool), `maxUse`, `readyRound`, `skillP`,
`triggerProbAtMax`, `impactBy`, `upType`, `upTypeIsPercent`, `upVal`, `initVal`,
`maxedValue`, `maxedValuePercent`, `buff` (id+name | null), `dbuff` (null — column unused),
`effect_raw`, `buff_raw`, `dbuff_raw`, and `effects[]`. Each `effects[]` entry:
`actionType`, `actionName`, `isAction`, `fromRound`, `targetCategory`,
`targetCategoryName`, `targetCount`, `triggerChance`, `coefficient`, `flatMagnitude`,
`layersOrMinDur`, `maxStacks`, `duration`, `flagA`, `affectedByAttr`, `rawTokens[]`.

Generator: `notes/sim/_gen_skills.py`.
