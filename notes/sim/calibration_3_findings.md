# Matchup 3 (Pursuit & Throughput) — research notes

Source: `calibration_3_pursuit.md` (build sheets + the in-game log/results). Player =
SusaMaki / Niya / Mia (all +229 ATK, pursuit + combo), enemy = Thiel(+DEF) / Nicole(+ATK,4★) /
Dolly(+DES), Archer. **In-game outcome: 100% player win over 10 runs; the detailed match was a
single battle, ~4 rounds** (enemy Nicole left at 55 troops; Thiel & Dolly wiped).

> Status (2026-06-10): the Test-3 ENGINE changes were **reverted** — they were FACT-correct but
> could not be reconciled with the DoT calibration without fresh data (see "Why this was reverted"
> at the bottom). The engine is back at the clean three-validator state. This file is kept as a
> **research note**: the client-data facts below are real and re-usable; the open questions are what
> the next research phase should answer before we re-touch the engine.

## Client-data facts discovered (engine-independent — these are real)
These come straight from `data/sim/skills.json` (the decoded effect tokens), not from the model:

1. **Bonus pursuit hits — `actionType 151` / `153`.** A pursuit skill can list extra hits as their
   own effects with a `triggerChance`: Flash Fire = main hit + `151` @ 45% (a 2nd pursuit); Trio =
   main hit + three `153` @ 40/35/30%; Chain Reaction = main + `151` @ 40%. Coefficient + chance are
   in the data.
2. **Per-effect `triggerChance` on `at=101` is real and load-bearing.** Multi-hit skills list each
   extra hit as a separate `at=101` effect with `triggerChance < 1`. e.g. **Rift = 3 hits @ 1.0 + 4
   @ 0.30 → ~4.2 expected hits, which matches the log's observed 4** (the in-game "Use [Rift] → 4
   Loss lines"). A model that fires all 7 over-counts multi-hit / AoE damage badly.
3. **Skill LEVEL scaling.** `coef(L) = initVal + (maxedValue − initVal)·(L−1)/9` (upType additive).
   Main + modular skills are maxed (lv10 → `maxedValue`), but **skill STONES are equipped at lv5**
   (the build sheets) → a stone's per-hit coef is ~28% below its max. The data flag `skillStone`
   identifies stones.
4. **`affectedByAttr` = 0 for every direct-damage effect** (normal = tactical = pursuit) and **= 1
   only for Assault.** So pursuit DAMAGE scales with the same attribute as normal/tactical (ATK),
   NOT Speed — the "Affected By Spd" hint governs pursuit trigger/turn-order, not its damage. The
   log confirms it: the +ATK pursuit carries (SusaMaki/Niya) are the top damage dealers.
5. **Assault (`at=70`).** Slayer applies an Assault buff (Real DMG Base flat 22 + relic) that fires
   on EVERY subsequent pursuit hit (the log shows `[Slayer][Assault] Effect Activated` on Slayer,
   Chain Reaction and Trio). Second Assault data point: **Niya Real DMG Base 32.29 → hits 757 → 648
   → 468**, declining with caster troops (cf. Patra ~671-726).
6. **Combo (`at=80`)** — Divine Punish / Hayate (passive) and Force Majeure (tactical → allies) grant
   a Combo buff = a chance for one extra attack on a normal.
7. **Witcher (`at=33`)** — per-round chance to gain a Pursuit-Skill-DMG-Dealt buff (~56.29% in log).
8. **"Inherit action target (the target enemy)"** — a pursuit follows/concentrates on the unit's
   attack target (the log: Niya focus-killed Thiel, SusaMaki → Dolly, Mia → Nicole), not a spread.

## Per-hero damage (engine vs in-game) — the symptom that points at missing data
When the above were modeled, per-hero damage still came out wrong in a structured way:
- **+ATK heroes UNDER-damage ~2×** (Niya 35k vs log 65k; SusaMaki 33k vs 60k; Nicole 24k vs 59k).
- **+DEF / +DES heroes OVER-damage ~2×** (Thiel 58-110k vs log 31k; Dolly 68k vs 40k).
i.e. stat ALLOCATION barely moves damage in our model (a +DEF tank hits nearly as hard as a +ATK
carry), but in-game it clearly does (~1.5-1.9×). The offence "floor" (soldier ATK) compresses the
spread; raising allocation sensitivity instead breaks the baseline mirror. This is the core unknown.

## Why this was reverted (and what it tells us)
Applying facts #2 (triggerChance) + #3 (level scaling) improved the pursuit balance a lot
(player:enemy damage ratio 0.64 → 0.96, in-game ~1.24) **but broke the DoT validator**: cutting the
enemy's (correctly) over-counted multi-hit/AoE damage tipped the DoT-vs-sustain matchup to the
player, and NO knob re-greened it without breaking testcase/baseline. The DoT calibration had
**absorbed the over-counting bug** as load-bearing enemy pressure. That a FACT-correct fix can't be
reconciled across all four logs is strong evidence that **the model is missing real structure in how
builds/stats/effects combine** — not just mis-tuned knobs.

## Open questions for the research phase (what data we likely need)
- **Stat → damage scaling.** How exactly do ATK / DEF / DES (and the +229/+179 allocation) scale a
  hit? The "Affected by X attribute / per-200" coefficient is currently UNKNOWN_SERVER_SIDE.
- **Multi-hit / AoE accounting.** Confirm per-effect `triggerChance` + `targetCount` semantics on
  `at=101` against more logs; how AoE spreads vs concentrates.
- **DoT & sustain.** Re-run the DoT matchup in-game with corrected multi-hit handling for a fresh
  win-rate target (the old 60% is a 10-run sample with a wide CI); separate the DoT/heal/shield
  contributions from the direct channel.
- **Skill/stone level scaling** confirmation (lv5 stone vs lv10 main) against logged hit values.
- **Build interactions** the user flagged: relic / rune / awaken / soldier+race combos / affection /
  messenger — how they stack and which stat each actually feeds. Catalogue what the client exposes
  vs what is server-side, before re-touching the engine.
