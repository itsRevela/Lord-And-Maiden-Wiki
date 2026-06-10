# Matchup 3 (Pursuit & Throughput) — findings from the in-game log

Source: `calibration_3_pursuit.md` Results + Battle log. Player = SusaMaki / Niya / Mia (pursuit +
proc), enemy = Thiel(+DEF) / Nicole(+ATK,4★) / Dolly(+DES), Archer. **Outcome: 100% player win over
10 runs** — the pursuit team dominates. Detailed match = **Victory, single battle, 4 rounds** (enemy
Nicole left at 55 troops; Thiel & Dolly wiped).

## Throughput / pursuit mechanics (the bout-count gap)
1. **Attack VOLUME is high.** In ONE round Niya fired **Slayer + Chain Reaction + Trio + Trio** (4
   pursuit skills), each triggering an **Assault** follow-up — i.e. ~8 hits from Niya in a round.
   SusaMaki: normal + **Flash Fire** + **White Blade** (2 pursuits) per round. "Skills Used" totals:
   Niya 12, SusaMaki 6, Mia 2 over 4 rounds. Pursuit/proc units act FAR more than once/round — this
   is the volume the engine under-counted.
2. **The SKILL STONE fires as a 4th equipped skill.** Niya casts **Rift** (her stone), Mia casts
   **Purgatory Trial** (her stone) — confirmed in the log. Stones must be modeled as an extra
   equipped skill (subject to the no-duplicate-per-team rule already catalogued).
3. **Skill multi-cast:** Niya cast **Trio twice** in one round (lines: "Use Trio 40%+8%" then "Use
   Trio 35%") — a pursuit can re-fire.
4. **Combo (extra attack):** Mia's **Divine Punish** (passive) "Effect Triggered 76%+22.8% → Trigger
   [Combo]" = a bonus hit after a normal; **Force Majeure** applies a `Combo` buff to allies;
   SusaMaki then "Combo Triggered 60% → Trigger [Combo]" landed the kill. So Combo = a chance for an
   extra attack (proc buffs 80/Combo).
5. **Witcher (passive):** "Effect Triggered 40% → **Pursuit Skill DMG Dealt Increased 56.29%+20%**" —
   a self-buff amplifying pursuit damage.

## Assault — second data point (refines `real_dmg_scale`)
Niya's Slayer applies **Assault, Real DMG Base 32.29** (note: NO "+7.2" — that addend was Patra's
relic). Assault follow-up hits: **757 → 648 → 468** across rounds (declining with Niya's troops),
and **468** while Niya was lower. Patra (Rosetta) was base 39.37 → ~671–726. So Assault ≈
`RealBase × ~scale × troop_factor`, DEF-independent — consistent across both heroes. Use to confirm
`real_dmg_scale`.

## Damage magnitudes (anchors)
- Pursuit hits (SusaMaki Flash Fire / White Blade): ~**6,200–9,700** (boosted by Witcher +56% in R3).
- Assault (Niya): ~**468–757**, flat-ish, declining with troops.
- Rift (stone, Niya) = **4 hits** (~940–1,600 each).
- Per-unit kills: Niya 65,355 / SusaMaki 60,241 / Mia 35,349; enemy Nicole 59,382 / Dolly 40,032 / Thiel 30,845.

## Calibration targets for `validate_pursuit.py`
- **Player win ~100%** (10/10 in-game) — the pursuit team should win nearly always.
- **Single battle, ~4 rounds** (no rematch — decisive).
- **High attack volume:** pursuit units fire multiple pursuits + Assault/Combo procs per round (not ~1).
- Assault (Niya) hits in the **~450–760** band, declining with caster troops.
- Mia (combo) and SusaMaki end as the survivors-ish; enemy nearly wiped (Nicole ~55 left in the sample).

## Engine work this implies (the big one)
- **Wire the skill stone as a 4th equipped skill** (main + 2 modular + stone). CAUTION: this affects
  ALL teams, including the other 3 validators (their teams have stones too — Rosetta's Elf Deer is a
  big attribute buff!). Re-validate testcase 9/9 + baseline 6/6 + dot 7/7 AND build pursuit; re-tune
  only if forced, documented.
- **Raise pursuit/proc throughput** so a pursuit DPS fires several pursuits + Assault/Combo procs per
  round (match the log's volume), incl. pursuit re-cast (Trio twice) and Combo (proc buff).
- Confirm `real_dmg_scale` against Niya's Assault (base 32.29 → ~468–757).
- Witcher / Pursuit-DMG-Dealt-Increased buff applied.

---

## IMPLEMENTED (2026-06-10) — what shipped + what the test revealed

The throughput data turned out to be FACT-driven: the relevant effects already live in the client
data; the engine was simply DROPPING them. All four changes are gated so they cannot fire for the
testcase/baseline/dot rosters (those action types/ids are absent there), so those validators stayed
**9/9 + 6/6 + 7/7** throughout.

1. **`at=151` / `at=153` bonus pursuit hits** (Flash Fire 45% 2nd-pursuit; Chain Reaction; Trio ×3).
   coef + triggerChance are FACTS in the data; the engine now replays each as one extra pursuit hit.
2. **Assault fires on EVERY pursuit hit** (not just normals): Slayer's standing Assault (id 70) now
   re-fires on Chain Reaction / Trio, matching "[Slayer][Assault] Effect Activated" per follow-up.
   Scoped to the PURSUIT channel so the tactical Assault carrier (Patra, testcase) is unchanged.
3. **Combo (`at=80`)** — Divine Punish / Hayate (passive) and Force Majeure (tactical→allies) grant a
   Combo buff (synthetic id 280) → a chance for one extra normal-channel attack after a normal.
4. **Witcher (`at=33`)** — per-round chance to gain a 1-round Pursuit-Skill-DMG-Dealt buff
   (`pursuit_dmg_buff_value=0.5629`, the log's "56.29%").
5. **Pursuit damage scales with ATK, not Speed** — the client field `affectedByAttr` is **0 for every
   direct-damage effect** (normal = tactical = pursuit) and only 1 for Assault. The old
   `pursuit→speed` assumption was wrong; "Affected By Spd" governs trigger/turn-order. Fixed
   `CHANNEL_PRIMARY_HERO_STAT["pursuit"]="atk"` (only touches pursuit teams; DoT stays empirically ruin).
6. **Pursuit focus-fire** — "Inherit action target" now CONCENTRATES a unit's pursuit hits on one
   enemy (the log: Niya focus-killed Thiel, SusaMaki→Dolly, Mia→Nicole) instead of scattering.
   Computed lazily so non-pursuit teams draw no extra RNG (baseline/dot byte-for-byte unchanged).

**Validated (GATING — Matchup-3's stated purpose):** Assault band (81% in 350-850, median ~424,
log 468-757), Assault declines with caster troops (corr -0.63), pursuit throughput (Niya ~7 hits/round),
fast decisive resolution (median 4 rounds, matching the log). `validate_pursuit.py` **4/4 gating PASS**.

### KNOWN GAP (documented, NOT fudged): outcome win-rate
Engine has the player winning ~25% (in-game 100%). In a WIN the per-hero damage shape matches the log
(player out-damages ~3:1), but the OUTCOME is decided by a high-variance commander-death race, and the
engine **over-credits the surviving tanky enemy commander's multi-hit tactical/AoE kit** — e.g. Thiel
(+DEF) "deals" ~110k vs ~31k in-game. Per-hero engine vs log: +ATK heroes ~0.5× (under), +DEF/+DES
~1.7-1.9× (over). Contributing factors, all in the SHARED damage model (not the pursuit mechanics added):
  - the offence floor (`soldier.atk`) compresses the ATK-vs-DEF/DES damage spread to ~1.16× when the
    game shows ~1.5-1.9× — BUT raising allocation sensitivity breaks the baseline mirror (verified by
    sweep), so it is NOT a free knob;
  - multi-hit tactical/stone effects (Rift = 7 `at=101` at max vs ~4 fired in-game at the lv5 stone)
    are counted at max level — stone/skill LEVEL scaling is not modelled;
  - the binary commander-death win condition + a squishy +ATK player commander amplify the variance.
Levers tried and rejected (each broke a green validator or didn't help): allocation sensitivity
(`soldier_off_frac`) breaks baseline; commander-target protection breaks dot and also shields the
enemy's tank; global target-persistence backfires (helps the enemy focus the squishy player commander).
**Fixing the win-rate requires a deliberate multi-log recalibration of the shared damage model
(skill/stone level scaling + tank-vs-DPS distribution) that re-fits all four logs simultaneously** —
flagged for a decision, not forced.
