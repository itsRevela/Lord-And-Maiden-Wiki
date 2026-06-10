# The Rosetta-Stone test case — how Lord & Maiden battles *actually* work

Source: `simulatorTestCase.txt` — a complete, manually transcribed in-game battle log
(practice mode), two battles between **Player [A]** = Patra / Rhea / Slider·Sp and
**Enemy [E]** = Rhea / Aguria·Sp / Satoru. Battle 1 = **Stalemate**, Battle 2 =
**Victory** (rematch, survivors carried over). This is the ground truth the simulator is
calibrated against. Line numbers below refer to the test-case file.

> **Status vs our engine:** our v1 used `Passive→Strategic→Tactical→Normal→Pursuit` inside
> 8 rounds with a scale-free exchange damage model. The log shows the real system is
> structurally different (a dedicated **Pre-War Preparation** phase, a **wound/casualty**
> model, prepared-CC re-rolls, Assault/Counter/Reactive/Assist/Taunt, and a stalemate
> escalation buff). This document is the rework spec.

---

## 1. Match / battle / phase structure

- A **Match** is a sequence of **Battles** (bouts). Undecided after 8 rounds → **Stalemate**,
  then an immediate rematch **Battle 2** with troop counts carried over. Repeats until a
  commander is wiped. (Confirms the earlier user note.) Lines 143–146, 184–189, 225.
- Each Battle runs three phase groups, in order:
  1. **Passive Exertion Round** (L265–272) — passives register/announce with
     `Effective Probability: 100%`. Counterattack shows its coefficient here
     (`DMG Coefficient 0.70+0.14`, L269/700).
  2. **Pre War Preparation Round** (L274–340) — **Strategic skills fire here, before round 1**,
     in a fixed order; this is where shields, team buffs, attribute buffs/debuffs, prepared
     CC, heal-over-time and dmg-amp are all set up.
  3. **Round 1 … Round 8** (L342+) — the actual exchanges.

### Stalemate escalation buff
Battle 2 opens with: **"Stalemate-1, All Hero DMG Dealt Increased 33.00%"** (L676). After a
stalemate the next bout grants **+33% All-Hero DMG Dealt** (the `-1` = stalemate count;
presumably stacks/escalates to force a decision). NEW mechanic — model it.

---

## 2. Casualty / HP model (troops = HP, but with wound tiers)

Every unit has **55,000** troops (165,000 team). Casualties are tracked in four buckets
(team summaries L150–160, 191–201):
- **Health** — live, fighting troops. This is the effective HP.
- **Slight Wound** — temporarily downed, *recoverable by healing*.
- **Severe Wound** + **Death** — permanent losses; they reduce the unit's **max**.

Soldier counts print as **`(current / max)`** (L354 etc.). `current` = Health; `max` =
Health + Slight Wound (i.e. everything still potentially recoverable). Each round-start note
"*soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death*"
(L398) ⇒ **between rounds a fraction of Slight Wounds convert to Severe/Death**, lowering
`max`. Healing (Self-Heal / Field Therapy) restores Slight-Wounded back to Health (L459:
`Restore 4962 Soldier (33991/45860)`).

**Win/lose:** a unit is **Defeated** at `current = 0` (L471, 792, 833). A side loses when its
**Commander** is defeated; if neither commander falls in 8 rounds → Stalemate.

**Carry-over:** Battle 2 starts each unit at its Battle-1-end **Health** (Patra 33,991 /
Rhea 52,527 / Slider 52,046; sum 138,564 = B1 left "Health"). L191, 203–206, 225.

> Implementation: track per unit `health`, `slight`, `severe+death`, `max`. Damage removes
> Health → Slight (and a portion straight to Severe/Death). Between rounds, worsen a share of
> Slight → Severe/Death. Healing moves Slight → Health. The "Kills" stat = total Health
> removed from enemies; "Slight/Severe/Death" columns = casualties *inflicted*.

---

## 3. Value notation `base% + flat%` (and `(NNN)` resulting stat)

Effects print as **`X% + Y%`** or **`X (Y)`**:
- `X%` = the **stat-derived / skill-level base**; `Y%` = a **flat add-on** from skill-stone /
  awakening / relic / rune. Use the **sum**. Examples: `DMG Taken Reduced 82.22%+30.00%`
  (Star Shield + lv5 relic, L285); `Tactical Skill DMG Dealt Increased 24.80%+9.00%` (L289);
  `Silence(Prepared) … 40.00%+12.00%` (L356); `ATK Reduced 22.57%+7.20% (252.1)` (L314).
- The trailing **`(NNN)`** = the **resulting absolute attribute value** after the modifier
  (e.g. enemy Rhea ATK becomes 252.1 after Dark Arrive). These give us **real in-battle stat
  magnitudes** (hundreds range) — gold for calibration. `DEF Attribute Increased 70.83 (408)`
  (L302) = +70.83 → DEF 408.
- Probabilities also use `base%+flat%`: a **prepared** Silence re-rolls each round at
  `40%+12%` (on allies) / `60%+12%` (on enemies) (L345/356) — note enemy units re-trigger CC
  at a higher base (60 vs 40).

---

## 4. Targeting, aid, taunt

- **Normal-attack targeting**: weighted toward strikers (our 20/40/40 rule stands), but
  modified by Aid/Taunt below.
- **Assist / Aid** (from Star Shield, L286): protected allies gain `Assist`; the assister is
  "**In An Aid State**" and intercepts. Lines like `[E][Satoru] In An Aid State, A[Rhea]
  Normal ATK E[Rhea]` (L353) show the aid unit announced when an attack resolves on the team.
  (Exact redirect rule still fuzzy — appears to let the aider soak hits aimed at strikers;
  refine during rework.)
- **Taunt → Provoked**: Knight Creed (enemy Rhea) applies `Taunts` to ally Rhea + Slider
  (L546–547); those units become "**In A Provoked State**" (L560, 571) and are forced to
  normal-attack the taunter. Taunt lasts ~ a couple rounds then "Effect Disappeared" (L608).

---

## 5. Status effects observed (behaviours to implement)

| Effect | Source(s) in log | Behaviour |
|---|---|---|
| **Silence(Prepared)** | Gray World, Unbounded (L278–280, 292) | Applied in prep; **re-rolls each round** (`Triggered Probability 40/60%+12%`); on trigger → "In A Silenced State, Cannot Launch Tactical Skills" that round. Purifiable. |
| **Silence** (non-prepared) | Cocoon Silence (L636) | Direct silence. |
| **Disarm** | Gray World, Ghost Bone (L417) | "Cannot Launch Normal ATK". Ghost Bone disarms its target each cast. |
| **Stun** | Evil Fruit (L378) | "Cannot act". Purifiable (L414). |
| **Heal Ban** (Forbidden Treatment) | Dark Arrive (L326) | "Cannot Be Healed" while active. |
| **DMG Taken Reduced** | Star Shield (~82–90%+30%), Knight Creed (54.82%), Reactive Block (59.20%) | Multiplicative incoming-damage reduction; **stacks** (commander Rhea ≈ near-immune). |
| **DMG Taken Increased** | Noise (42.89%+9%) | Incoming-damage amplification. |
| **DMG Dealt Increased** | Green Tea (26.91%), Stalemate buff (33%) | Outgoing amplification. |
| **Tactical Skill DMG Dealt Increased** | Sky Tear Arrow (24.8%+9%) | Channel-specific dmg-dealt buff. |
| **Attribute Increased/Reduced** (ATK/DEF/DES/Spd) | Elf Deer (+~53%), Field Therapy (DEF), Dark Arrive (−22.57%+7.2%) | Flat/percent stat mods; show resulting `(NNN)`. "Effect Cannot Be Replaced" when a stronger same-type is present (L306). |
| **Self-Heal** (HoT) | Field Therapy (`Healing Coefficient 1.05+0.28` ally / `1.4` enemy) | Heals at round start: `[Field Therapy][Self-Heal] Effect Activated, [X] Restore N Soldier`. Blocked by Heal Ban. |
| **Purification** | Piety, Star Shield's relic? (L333) | Re-rolls each round (`40%+8%`) to **cleanse one debuff** (Silence/Stun/Disarm). |
| **Assault** | Ghost Bone (`Real DMG Base 32.17+7.2`, L416) | Buff on caster: **every one of its attacks triggers an extra Assault pursuit dealing flat Real DMG** (`Loss 671/726`, ignores DEF). |
| **Counterattack** | passive (Rhea, coef `0.70+0.14`=0.84) | When normal-attacked, deals a counter hit (`Trigger [Counterattack]` → `Loss N`, L386/393). |
| **Reactive Block** | passive (Rhea), `Triggered Probability 30%` | Chance on being hit to apply `DMG Taken Reduced 59.20%` for that hit (L549–550). |
| **Tactical Burst** | passive (Patra/Aguria) | Chance after a tactical skill to **re-cast it** (`Triggered 40%+8%` → `Use [Magic Spear]` again, L426–427). |
| **Sacred Feather** | passive (Aguria), `Triggered 41.5%` | Procs to purify own prepared-silence then cast (L367–368). |

---

## 6. Skill role map (from this fight)

- **Strategic / prep (fire in Pre-War):** Gray World (self-disarm + AoE prepared Silence on
  enemies), Star Shield (commander big DMG-Taken-Reduced + Assist to allies), Sky Tear Arrow
  (ally tactical-dmg buff), Unbounded (AoE prepared Silence on enemies), Field Therapy (ally
  Self-Heal HoT + DEF buff), Elf Deer (skill-stone: ally all-attribute buff), Dark Arrive
  (AoE enemy all-attribute reduction + Heal Ban), Noise (enemy DMG-Taken-Increased), Piety
  (ally Purification).
- **Active damage (in rounds):** Ghost Bone (Patra main: Assault + Disarm target, the engine
  of her damage), Bone Blade, Magic Spear (skill-stone), Swift Thrust, Evil Fruit
  (Aguria, + Stun).
- **Passives:** Tactical Burst, Counterattack, Reactive Block, Sacred Feather.
- **Round-gated:** Green Tea (Satoru, from R4/R7), Knight Creed (enemy Rhea, from R4),
  Cocoon Silence (Satoru, R8).

---

## 7. Damage calibration anchors (for the formula)

In-battle hero attributes are **hundreds** (e.g. enemy Rhea ATK 252–292, DEF 610–660; Aguria
ATK ~960; Satoru Spd ~590). Troops 55k. Clean(ish) instances:
- Patra (ATK build, archer, ~55k) **Ghost Bone** vs Aguria (DMG-Taken+42.89%, DEF-reduced) =
  **15,984** (L418); **Magic Spear** vs Aguria = **19,116** (L423).
- Same skills vs enemy Rhea (Star Shield −90%+30%) = only **1,917 / 2,139** (L420/428) — the
  ~10× gap is the DMG-Taken-Reduced stack ⇒ mitigation buffs dominate.
- Normal ATKs vs shielded Rhea: ally Rhea (DEF build) 482; Patra (ATK) 1,459; Slider (DES)
  547 (L354/359/364).
- **Assault Real DMG** (flat, ignores DEF): 671 then 726 then 585(partial). `Real DMG Base
  32.17+7.2 = 39.37`. (Scaling factor ~18× to be solved with the dataset.)

> The full damage-instance dataset (every Loss, with target buff-state) is being extracted to
> `data/sim/calibration.json`. The formula must reproduce: huge target-dependent variance via
> DMG-Taken mods, flat Real-DMG pursuits, and the per-unit Kills totals
> (Patra 92,895 / Rhea 13,370 / Slider 6,032 in B1).

---

## 8. Rework checklist (engine)

1. **Phases:** add Passive-Exertion + Pre-War-Preparation; fire Strategic skills + apply
   prepared/HoT/shield/attribute effects in prep, before round 1.
2. **Casualty model:** health/slight/severe/death with inter-round worsening; carry **Health**
   between bouts; Defeated at health 0; commander-death = loss; 8-round draw = Stalemate.
3. **Stalemate escalation:** +33% All-Hero DMG Dealt per prior stalemate (carry-over buff).
4. **Buff engine:** `base%+flat%` summed; DMG-taken/dealt (general + per-channel) multipliers;
   attribute add/mult with "cannot be replaced"; durations + "Effect Disappeared".
5. **Prepared CC:** per-round re-roll (40/60%+flat); Silence→no tactical, Disarm→no normal,
   Stun→no act, Heal Ban→no heal.
6. **Procs/reactions:** Assault (flat real-dmg pursuit on each attack), Counterattack (on being
   normal-attacked), Reactive Block (chance dmg-taken-reduced), Tactical Burst (chance re-cast),
   Sacred Feather, Purification (re-roll cleanse).
7. **Aid/Taunt:** Assist soaks hits for strikers; Taunt→Provoked forces target = taunter.
8. **Tracking:** per-unit Kills / Heal / SlightWound / SevereWound / Death to compare to the
   log's stat tables.
9. **Calibrate** the damage/heal formula to the dataset (Section 7) and **validate** both
   battles end Stalemate→Victory with matching casualty magnitudes.
