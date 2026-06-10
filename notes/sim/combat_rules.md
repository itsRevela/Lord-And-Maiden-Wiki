# Combat Rules — authoritative model for the battle simulator

Source of truth for STATED rules: `wiki/Mechanics/Battle-Mechanics.md`, `wiki/Reference/Game-Hints.md`,
`wiki/Mechanics/Status-Effects.md`, `data/csv/Tips.csv`, `data/csv/Language_SysTip.csv`,
`data/csv/Language_Game.csv`, `data/csv/EntryEffect.csv`, and the decompiled client
`decompiled/Assembly-CSharp/eb46ed1b3cbb.decompiled.cs`. Machine-readable constants:
`data/sim/combat_rules.json`. Companion docs: `notes/sim/skills.md`, `notes/sim/status_effects.md`,
`notes/sim/troops_meta.md`, `notes/sim/gear.md`.

> **Combat is server-authoritative.** The client receives a fully-resolved replay log and only
> *renders* it; it never computes order, targets, or damage. The parser
> (`ParseBattleDetails`, decompiled:19490-19533) reads `RoundData{Round, BList[FightBehaviour]}`,
> where each `FightBehaviour{FightPos, BeforeAction[BehaviourRet], BehaviourList[BehaviourAction]}`
> and each `BehaviourRet{TargetPos, RetType, RetVal, HPRate1, HPRate2}` (classes at
> decompiled:38706-38739, 20063-20078). Every number the simulator must produce — damage,
> heals, hit/miss, order — arrives pre-computed as `RetVal`/`HPRate`. The simulator therefore has
> to **reimplement** the hidden math; the formula itself is `UNKNOWN_SERVER_SIDE`.

---

## A. EXTRACTED FACTS (stated in the client / data files)

### A1. Team & win condition
- A team is **1 Commander + 2 Strikers** (3 fighting positions per side).
  - `FightPos` 1 = a side's Commander (kill-stat lookups Find `FightPos == 1` as the commander
    row, decompiled:124036-124037). Positions are 1-3 for one team and 4-6 for the other; the
    replay renderer treats `FightPos <= 3` vs `>= 4` as the two opposing sides
    (decompiled:37708-37716, 37762).
- **Win/lose:** "The Commander Is The Core Of The Team; When The Commander Dies, The Battle Is
  Lost." (`Tips.csv` Id=10 / row0; `Language_SysTip.csv` row285). Each team must have a Commander
  with Strength > 0 (`Tips.csv` Id=30 / row1).
- **Leaving a battle counts as a loss** (`Game-Hints.md` Combat; `wiki/Mechanics/Battle-Mechanics.md`).

### A2. Round structure — 8 rounds
- Battles run **8 rounds**. The replay renderer hard-codes the round counter as `roundData.Round
  + "/8"` (decompiled:37449). Community guide concurs: "8 rounds of combat"
  (`Battle-Mechanics.md`).
- **Per-round phase order** (verbatim from the replay renderer `RoundAniIE`,
  decompiled:37446-37484, iterating each acting unit's `FightBehaviour` in the server-given
  `BList` order):
  1. **Per-unit "before action" phase** — `FightBehaviour.BeforeAction` (a list of
     `BehaviourRet`) is played first (decompiled:37453-37464). This is where the
     **before-the-turn** effects land: DoT (Burn 108 / Curse 109 are "Before Each Round, …DMG
     Taken", see `status_effects.md`), periodic Self-Heal (107, "Before Each Round, Restore
     Life"), and pre-round CC rolls (Arcane Missile 154 "Before Each Round, a chance to …").
  2. **Action phase** — `FightBehaviour.BehaviourList` (`BehaviourAction`s) is played
     (decompiled:37465-37472): the unit's normal attack plus any skills it fires.
- **Impasse:** if both Commanders still hold troops after 8 rounds, the bout pauses (~1 min) and
  may repeat / retreat / re-engage; exact behaviour varies by mode (`Battle-Mechanics.md`).
  Treated as a draw/continue boundary by the simulator.

### A3. Skill *activation* (within-unit) order — the authoritative ordering rule
- **Skill Activation Order: Passive Skill → Strategic Skill → Tactical Skill → Normal ATK →
  Pursuit Skill** (`Tips.csv` Id=130 / row6, `TypeName_en` = "Skill"; `Language_SysTip.csv`
  row294; mirrored in `Game-Hints.md`).
  - This is the order in which a unit's *own* effects resolve, NOT the cross-unit turn order
    (that is A4). It tells the simulator: Passives are already on; Strategics that are gated to
    this round switch on; then the unit may fire a Tactical; then it makes its Normal ATK; then it
    rolls Pursuit (Pursuit fires *after* the normal attack — `Battle-Mechanics.md` "Chase skill =
    chance to fire after the unit's normal attack").
- The community guide gives the same flow informally: "On its turn a unit makes a normal attack,
  then rolls the chance for any Chase/Tactical skills to fire" (`Battle-Mechanics.md`).

### A4. Turn / action order between units — by Speed (ATK Spd, stat 50)
- "Each round, every unit (both teams) acts **in order of its Speed**" (`Battle-Mechanics.md`).
  "Speed" here is the hero **ATK Spd** attribute = `EntryEffect` **50 = Hero ATK Spd**
  (`EntryEffect.csv`; gear note "Hero ATK Spd = how often the hero acts in combat",
  `notes/sim/gear.md`). Higher Speed acts earlier.
- In the client the final order is simply the server-supplied sequence of `FightBehaviour` in
  `RoundData.BList` (decompiled:19493-19531, 37450); the client does not sort.
- **Speed-tie resolution is `UNKNOWN_SERVER_SIDE`** (no client tie-break code; see B).

### A5. Restraint triangle (soldier-type counter)
- **Infantry → Archer → Cavalry → Infantry** (cyclic; each restrains the next). **Chariot has NO
  restraint relationship.** Magnitude: a restrained soldier's **Damage Dealt is reduced by 25%**.
  - Source: `Tips.csv` Id=350 / row17 (`TypeName_en` = "Soldier"): "Soldiers Of Different Types
    Have A Restraint Effect, Infantry->Archer->Cavalry->Infantry, When Soldiers Are Restrained,
    Damage Dealt Is Reduced By 25%." Corroborated `Language_SysTip.csv` rows 289 + 304;
    `Game-Hints.md` Combat; UI labels `Language_Game.csv` 2209/2210 ("Soldier Restraint
    Relationships" / "No Restraint Relationship").
- **What it modifies:** **damage DEALT by the restrained (losing) side is ×0.75** (it is a
  penalty on the attacker who is countered, not a bonus to the defender). The text is unambiguous:
  "When Soldiers Are Restrained, Damage Dealt Is Reduced by 25%."
- A hero's soldier type = its `HeroInfo.RST` (`hero.SoldierT = heroInfo.RST`,
  decompiled:10428,17380-17392; see `notes/sim/troops_meta.md` §6).
- **Bypass:** Precision Strike (buff 155) "Ignores Soldier Restraint effects" — an attack flagged
  with it does not suffer the −25% (`status_effects.md` 155).

### A6. Level suppression (soldier-tier difference)
- "Soldiers Of Different Levels Have A Suppression Effect, And High-Level Soldiers Deal More
  Damage To Low-Level Soldiers" — **separate from restraint** (`Tips.csv` Id=330 / row16;
  `Language_SysTip.csv` row288; `Game-Hints.md` "Level suppression … separate from restraint").
- **Magnitude / curve is `UNKNOWN_SERVER_SIDE`** — the text states the direction only, not the
  per-level multiplier (see B). "Level" here is the soldier **tier** (`SoldierInfo.level` 1-6, see
  `troops_meta.md` §1).

### A7. Targeting (when no Taunt)
- **Normal-attack target is chosen randomly by weight: Commander 20%, Striker 1 = 40%, Striker 2 =
  40%** (`Tips.csv` Id=90 / row4: "Target Selection (without Taunt): Chance that Commander will be
  chosen … 20%; Striker 1 … 40%; Striker 2 … 40%"; `Game-Hints.md` "Commander 20%, each Striker
  40%"). (The 2022 community guide phrases this loosely as "Commander 25% less likely"; the data
  file value 20/40/40 is authoritative.)
- **Skills** hit random target(s) within their `targetCategory`/`targetCount` unless the skill text
  says otherwise (`Battle-Mechanics.md`; `skills.md` §5 `targetCategory` enum: 2 Enemy Troops,
  4 Our Troops, 7 Self, 10 Enemy Commander, 0 inherit-attack-target, 6 assist target).
- **Targeting overrides:**
  - **Taunt (118)** forces enemy Normal ATK onto the taunter (`status_effects.md` 118).
  - **Assist (120)** redirects Normal ATK aimed at protected allies onto the bearer
    (`status_effects.md` 120).
  - **Chaos (117)** makes Normal ATK and damage-dealing Tactical skills (and the Pursuits they
    trigger) hit **completely random** targets, friend or foe; overrides Taunt (`Tips.csv` Id=310;
    `Language_SysTip.csv` row428; `status_effects.md` 117).
  - The exact within-bucket target selection (front-to-back? lowest-HP?) beyond the stated random
    weights is `UNKNOWN_SERVER_SIDE` (B).

### A8. Skill activation / triggering
- **Strategic (ST=1)** — applied **before battle starts** (`{战斗开始前生效}`, decompiled:9908-9911),
  or gated to a stated round via the skill's `Effect`/`Buff` token[1] `fromRound` (e.g. "From The
  5th Round"; `skills.md` §3 token[1], §2). Always active (cannot be stopped by CC),
  `Battle-Mechanics.md`. Effectively one-time / round-gated application.
- **Passive (ST=3)** — active the **whole battle** (`{整场战斗中生效}`, decompiled:9916-9918); always-on
  self-buff, cannot be stopped by CC.
- **Tactical (ST=2)** — active in-combat skill; fires on the unit's turn with a **per-round trigger
  probability `SkillP`** (decompiled:9912-9915; `skills.md` §8, e.g. 0.35 = 35%). May need
  preparation rounds (`ReadyRound`).
- **Pursuit (ST=4)** — follow-up rolled **after the unit's Normal ATK**, with trigger probability
  `SkillP` (decompiled:9920-9923; `Battle-Mechanics.md` "Chase skill").
- **Trigger-chance scaling with level:** when a skill's `UpType == 45` the probability itself
  scales with skill level (`SkillP == ImpactBy`; `skills.md` §8). `skills.json` exposes
  `skillP` and `triggerProbAtMax`.
- **Gear that raises trigger chance:**
  - `EntryEffect` **131 = Equip Tactical Skill Activation Probability**, **132 = Equip Pursuit
    Skill Activation Probability** (both percent, Size 10000; `EntryEffect.csv`). Carried by Magic
    Messenger / accessories (`gear.md`). They **add to** the skill's `SkillP`.
  - A **Rune** raises the trigger chance of one specific Tactical/Pursuit skill (`Effect = 45_frac`
    in rune context; `gear.md` Runes).
  - **Insight (buff 150)** raises the activation probability of **all** the bearer's Pursuit skills
    by a skill-supplied amount (`status_effects.md` 150).
- **Preparation modifiers:** Instant/Swiftcast (88) can cut a Tactical's preparation by 1 round;
  Superconducting (125) can re-cast a no-prep Tactical once more (`status_effects.md` 88, 125).
- **CC gating of activation** (which skill types each control blocks):
  - Stun (114) — cannot act at all. Disarm (115) — no Normal ATK. Silence (116) — no Tactical.
    Chaos (117) — random targets. Heal Ban (119) — cannot be healed. Concentration (113) — immune
    to CC during its turn. (`status_effects.md`; `Status-Effects.md`.)

### A9. Damage categories & their mitigation (as stated by the client)
The replay tags each result with a `RetType` (decompiled:37489-37520):
`RetType <= 3` = a damage instance taken (shows `−RetVal`, plays a hit); `== 4` = heal (`+RetVal`);
`== 5` = a no-number result (block/dodge/shield/“−1”); `== 6` = positive buff applied;
`== 7` = negative buff applied. (Magnitudes inside `RetVal` are server-resolved.)

| Channel | What it is | ± DMG buff family (Buff.csv) | Stated mitigation / defence stat |
|---|---|---|---|
| **Normal ATK** | auto-attack each turn | dealt 29 / taken 35,36 | general DMG Taken Reduced (8, "Affected By DEF"); Normal DMG Taken Reduced (36); Dodge (111); Shield (73) blocks one instance |
| **Tactical** | ST=2 active skill (`Effect` action 101) | dealt 31 / taken 37,38 | Tactical DMG Taken Reduced (38); general DMG Taken Reduced (8) |
| **Pursuit** | ST=4 follow-up after Normal ATK | dealt 33 / taken 39,40 | Pursuit DMG Taken Reduced (40); general (8) |
| **Real DMG** | true/extra hit; "fixed extra hit based on troop count + in-battle Attack" (`Battle-Mechanics.md`) | dealt 47 (Real DMG Dealt Increased) | **Ignores DEF mitigation** — true damage (`status_effects.md` 47). Mitigation channel = `UNKNOWN_SERVER_SIDE` beyond "ignores DEF". |
| **Burn (DoT)** | 108, "Before Each Round, Burning DMG Taken" (coef ~0.5-1.69) | taken-down: Burning DMG Taken Reduced (44); amplified by Combustion Aid (157) ×1.5; detonated by Element Burst (158)/Exploding-Flame | Burning DMG Taken Reduced (44); detonation/amp via 157/158 |
| **Curse (DoT)** | 109, "Before Each Round, Curse DMG Taken" (coef ~0.5-1.69) | taken-down: Curse DMG Taken Reduced (43); amp 157; detonate 158 | Curse DMG Taken Reduced (43) |
| **Blood Sucking (lifesteal)** | 106; bearer restores soldiers when it deals damage, by a Blood Sucking Coefficient 0.4-1.5 | n/a (heal-on-hit) | scales off damage dealt; heal value formula `UNKNOWN_SERVER_SIDE` |
| **Splash** | normal/pursuit splash to other enemies (82 / 159), coef ~0.5-1.5 | rides the source channel | "ignoring defence" per `Battle-Mechanics.md` (Splash ignores DEF) |

- **General "Affected By X" attribute scaling** (`Battle-Mechanics.md`, `Game-Hints.md`,
  `Tips.csv` Id=250): "Affected by X attribute" always refers to the **caster**; effect scales
  "roughly × for every 200 points of the named stat". DMG Dealt-up (5) commonly Affected By DES;
  DMG Taken-down (8) Affected By DEF; Tactical/Pursuit dealt (31/33) Affected By Spd; healing
  Affected By Soldiers' HP (`Tips.csv` Id=270). The exact 200-point coefficient is community-stated
  (B).
- **Shield (73)** blocks the **first instance** of damage (per layer), not an amount; pierced by
  "Ignores Dodge and Shield" attacks (155) (`status_effects.md` 73, 155;
  `Status-Effects.md`).

### A10. In-battle stat construction (inputs the formula consumes)
- **In-battle stat = Hero stat + Troop stat**, where the troop stat is pre-boosted by armour /
  technology / titles, and the hero stat is multiplied by the race/team bonus
  (`Battle-Mechanics.md` worked example; `Game-Hints.md` Stats). Shape:
  `in_battle_stat ≈ (hero_stat × team_race_multiplier) + (troop_stat × (1 + Σ gear/tech/title%))`.
  - Hero stat sources: levelling `stat(L)=base+floor(growth×L)` (resolver `hero_stat_at`), +1
    free point/level + 10/Advance, Favorability up to +30 all stats, race/troop combos
    (`troops_meta.md`).
- **Damage scales largely with troop NUMBERS** ("the damage an enemy deals scales largely with
  their troop numbers", `Battle-Mechanics.md`). HP pool = soldiers (`Hero Soldiers Quantity` /
  `EntryEffect 54`; max soldiers = `2000 + Level*500 + Advance bonus`, `gear.md`).

### A11. Commander role
- The Commander is the **win/lose anchor** (its death = loss; A1) and is **targeted less** (20% vs
  40% per striker; A7). When the Commander dies, "A Large Number Of Severely Wounded Soldiers Will
  Be Generated" (`Tips.csv` Id=430; `Language_SysTip.csv` row293).
- **Chariot bombard:** only when the **team Commander fields Chariot-type soldiers** can the team
  bombard buildings in Siege (`Tips.csv` Id=770; `Language_SysTip.csv` row399).
- **No separate stat/aura bonus** for the Commander slot vs the two strikers is stated in the
  client (the three heroes use identical stat construction). Any combat aura tied to the Commander
  slot is `UNKNOWN_SERVER_SIDE` (B).

### A12. Stacking rules (govern buff aggregation each round)
- **Same effect from DIFFERENT skill types → adds together; same effect from the SAME type → does
  not stack (only the highest applies)** (`Tips.csv` Id=150/Id=170; `Language_SysTip.csv`
  rows295/296; `Game-Hints.md`). Applies to every dmg_mod / attr_mod buff (`status_effects.md`).
- **Unique states (cannot co-exist as duplicates):** Dodge, Assault, Instant, Superconducting,
  Eternal, Concentration, Taunts, Assist (`Tips.csv` Id=190 / row9).
- **Prepared CC (83-86)** are the telegraphed display of real CC (114-117); they resolve to the
  same effect when they fire (`status_effects.md`).

---

## B. MODELING ASSUMPTIONS (server-side — simulator must choose, and label as assumed)

The exact battle math lives on the server (decompiled:19490-19533 — the client only parses a
resolved `RetVal` log). The simulator must adopt explicit, transparent stand-ins. Each below is an
ASSUMPTION, not an extracted value.

1. **Core damage equation** — `UNKNOWN_SERVER_SIDE`. No `RetVal = f(ATK, DEF, …)` exists in the
   client. *Assumption:* see the recommended transparent model in §C.
2. **Restraint application point** — the −25% is a *stated* rule (A5) but applied server-side; the
   client receives already-resolved damage and has **no** `0.75` factor keyed to `SoldierT`
   (decompiled:19506; `troops_meta.md` UNKNOWN list). *Assumption:* apply ×0.75 to the restrained
   attacker's outgoing damage (per the text "Damage Dealt … Reduced by 25%").
3. **Level-suppression curve** — direction stated (A6), magnitude/per-tier multiplier
   `UNKNOWN_SERVER_SIDE`. *Assumption:* a small per-tier-difference multiplier (e.g. neutral 1.0,
   +x% per tier the attacker is higher); flag as tunable, default conservative.
4. **Speed tie-break** — order is by Speed (A4) but ties / sub-ordering within equal Speed is
   `UNKNOWN_SERVER_SIDE` (no client sort). *Assumption:* stable deterministic tie-break (e.g. by
   FightPos, attacker side first); expose as a config seed.
5. **Within-bucket target pick** — only the 20/40/40 normal-attack weights and "random within
   category" are stated (A7); whether skills prefer front/back/lowest-HP is
   `UNKNOWN_SERVER_SIDE`. *Assumption:* uniform random within the legal target set, respecting
   Taunt/Assist/Chaos overrides, seeded RNG.
6. **"Affected by X" coefficient** — the "× per 200 points" rule is community-stated, not in data
   (A9). *Assumption:* use ~+1 multiplier-unit per 200 points of the named stat as a starting
   coefficient; tunable.
7. **Real DMG / Splash mitigation** — stated to ignore DEF (A9) but the base formula
   (troop count + in-battle ATK) magnitude is `UNKNOWN_SERVER_SIDE`. *Assumption:* model as a
   true-damage add that bypasses DEF and Shield-amount but is still gated by Shield-instance/Dodge
   only where the text says it is not bypassed.
8. **DoT base damage** — Burn/Curse use a skill-supplied coefficient (~0.5-1.69) but the resolved
   per-round number is `UNKNOWN_SERVER_SIDE`. *Assumption:* `coef × attacker_effective_power`,
   then ×(1−resist 43/44)×(1+amp 157), resolved in the BeforeAction phase (A2).
9. **Blood Sucking / heal magnitude** — coefficient known, resolved value
   `UNKNOWN_SERVER_SIDE`; heals scale off Soldiers' HP (stated). *Assumption:*
   `heal = coef × soldiers_HP_based_power`.
10. **Proc resolution order & RNG** (Counter/Combo/Dodge/Splash/First-Aid interplay within a turn)
    — sequencing is `UNKNOWN_SERVER_SIDE`. *Assumption:* resolve in the A3 activation order, roll
    each proc independently with a single seeded RNG stream.
11. **Commander combat aura** — none stated beyond targeting/win-condition (A11); any hidden aura
    is `UNKNOWN_SERVER_SIDE`. *Assumption:* none (Commander = strikers statistically, only
    targeting weight + win anchor differ).
12. **Impasse / multi-bout continuation** mode-specific behaviour `UNKNOWN_SERVER_SIDE`.
    *Assumption:* treat post-round-8 as a draw unless a mode rule says otherwise.

---

## C. Recommended transparent damage model (every factor labelled)

Make the simulator *explicit and auditable*: compute each labelled factor, then multiply. This
mirrors the buff families the data exposes, so it stays faithful to the catalogued inputs while
isolating the one unknown (the base coefficient mapping).

```
per_hit_damage =
      effective_power(attacker, channel)        # EXTRACTED inputs (stats A10), MAPPING assumed (B6)
    × channel_coefficient                        # EXTRACTED: skill coef / 1.0 for normal (skills.md token[5]/InitVal)
    × restraint_factor                           # EXTRACTED rule 0.75 if restrained else 1.0 (A5); bypass if Precision-Strike(155)
    × level_suppression_factor                   # ASSUMED curve (B3); direction EXTRACTED (A6)
    × (1 + Σ dmg_dealt_mods)                      # EXTRACTED buffs 5/29/31/33 (+) , 6/30/32/34 (−); stacking per A12
    × (1 + Σ dmg_taken_mods_on_target)           # EXTRACTED buffs 7/35/37/39 (+), 8/36/38/40 (−); DEF-affected (A9)
    × crit/proc_multipliers                      # EXTRACTED proc set (Splash 82/159, Combo 80, Counter 81…); rolls ASSUMED (B10)
    + real_damage_add                            # EXTRACTED channel 47; bypasses DEF (A9); magnitude ASSUMED (B7)
then:
    apply Dodge(111) / Shield(73) instance gates # EXTRACTED gating rules (A9)
    subtract from target soldier-HP pool         # HP pool EXTRACTED (A10); soldiers = damage scalar
```

- **`effective_power`**: built from in-battle ATK (normal), or Spd-affected power (Tactical 31 /
  Pursuit 33), or DES-affected (DMG-dealt-up 5), per A9/A10. The ATK→damage *mapping constant* is
  the single ASSUMED scalar (B1/B6); everything multiplying it is EXTRACTED.
- **`channel_coefficient`**: 1.00 for a normal attack ("1.00 = one normal attack's worth",
  `Game-Hints.md`); for skills it is the skill's `coefficient` (`skills.md` token[5], scaling to
  `maxedValue`).
- **DoT** (Burn/Curse) and **periodic heals/Self-Heal** resolve in the **BeforeAction** phase
  (A2), each as `coef × power × (1 − resist) × (1 + amp)` (B8/B9).
- **Stacking** of all the `Σ` terms follows A12 (cross-type adds, same-type takes max) before the
  multiply.

Expose every ASSUMED factor (B1, B3, B6, B7, B10) as a tunable config so the model stays
transparent and can be calibrated against observed replay `RetVal`s later.

---

## UNKNOWN_SERVER_SIDE list
- Core damage equation (`RetVal` mapping from stats/coefficients) — not in client.
- Restraint −25% **application** (rule stated; no client-side 0.75 factor).
- Level-suppression **magnitude/curve** (direction stated only).
- Speed **tie-break / sub-ordering** within equal Speed.
- **Within-bucket target selection** beyond the 20/40/40 normal-attack weights (front/back/low-HP?).
- "Affected by X attribute" **coefficient** (the ×/200-points rule is community-stated).
- **Real DMG / Splash** base magnitude (only "ignores DEF" is stated).
- **Burn/Curse DoT** resolved per-round damage.
- **Blood Sucking / heal** resolved magnitude.
- **Proc resolution order & RNG** (Counter/Combo/Dodge/Splash/First-Aid interplay).
- **Commander** hidden combat aura (none stated; assumed none).
- **Impasse / multi-bout** continuation behaviour (mode-specific).
