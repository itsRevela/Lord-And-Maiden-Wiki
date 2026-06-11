# Pursuit battle — ground truth from 37 captured battles

Source: live battle logs sniffed off the wire (`SCLogic_DetailsGrand`), decoded to
`battle_*.json`. 16 `+alloc` battles (root) + 21 `base0` battles (all heroes +0, base lv80).
This is the calibration target for the pursuit matchup. **No fudging** — every number here
is measured from real server battle logs.

Matchup (fixed): Player `SusaMaki(28,cmdr) / Niya(117) / Mia(46)` vs
Enemy `Thiel(99,cmdr) / Nicole(87) / Dolly(108)`.

## 1. Win condition — TROOP depletion, not hero-HP, not 8-round bouts

Each unit has **two** pools in the wire data:
- `hpRate1` = hero **Health** (健康) — barely moves (ends ~0.58–0.93). Secondary.
- `hpRate2` = **TROOPS** (士兵) — THIS is the kill channel.

A unit is **defeated** (`已阵亡`) when its **troops (hpRate2) reach 0**. The battle ends —
and is won — when the **enemy COMMANDER's troops hit 0**. Confirmed in every log tail:
`[蒂尔]{损失}…{士兵}(0/41444)` → `[蒂尔]{已阵亡}`.

There is **no 8-round bout / stalemate-rematch** in this mode: battles run ~3–4 rounds and
end on the commander-troop-kill. (The engine's bout/stalemate machinery is harmless when a
decision happens early, but the *real* decision mechanic is troop-depletion of the enemy cmdr.)

## 2. Battle shape (measured)

| metric | +alloc (n=16) | base0 (n=21) |
|---|---|---|
| rounds | **3.69** (median 4) | **3.14** (median 3) |
| win rate (player) | **94%** | **90%** |
| enemy units dead by end | **2.75 / 3** | 2.38 / 3 |
| player units dead by end | **0.31 / 3** | 0.38 / 3 |
| player/enemy dmg ratio | **1.72×** | ~1.68× |
| final troop sum (player) | 1.25 / 3 | 1.78 / 3 |
| final troop sum (enemy) | 0.06 / 3 | 0.18 / 3 |

Max troops ≈ **54,000** per hero (SusaMaki 54352, Niya 54305, Mia 54336, Thiel 53666,
Dolly 53864). **Engine's 55,000 is correct** — troop size is NOT a calibration lever.

## 3. Kill cascade — strikers first, commander last (DEF-driven)

| unit | troops→0 in | avg round | note |
|---|---|---|---|
| Nicole (E striker) | 15/16 | **2.33** | dies first |
| Dolly (E striker) | 14/16 | **2.79** | dies second |
| Thiel (E cmdr, +DEF) | 15/16 | **3.67** | dies LAST → ends battle |
| player heroes | rarely | 3–4.5 | mostly survive |

This is a **focus cascade**: squishier strikers deplete first (less DEF → take ~full hits),
then once they're dead the survivor (the +DEF commander, who takes ~0.56×) eats ALL remaining
player damage and falls ~round 3.7. That late concentration is why the enemy commander absorbs
the largest share of player damage (~42%) — it's emergent from kill-order, not a targeting rule.

## 4. Per-hero damage targets (captured, +alloc)

| hero | dmg dealt | skill casts |
|---|---|---|
| SusaMaki | 69256 | 6.6 |
| Niya | 57650 | 8.6 |
| Mia | 31420 | 2.5 |
| Thiel | 45651 | 4.4 |
| Nicole | 24013 | 2.4 |
| Dolly | 22385 | 2.0 |

Laws (confirmed earlier from CMP_alloc_vs_base): ATK weak (~ATK^0.3), DEF strong
(+229 DEF ≈ −40% incoming), win allocation-insensitive (94% +alloc vs 90% base0).

## 5. maxUse — the real skill-firing rule (DATAMINED)

`maxUse` is a **per-battle cast cap** (decompiled `eb46ed1b3cbb.cs:5880-5889` shows the
in-game `UseNum / MaxUse` counter; `MaxUse==0` = unlimited). Per battle a skill fires at most
`maxUse` times; `maxUse==0` fires every round it triggers.

Relevant skills: Thiel = Binding Slash `maxUse=0` (unlimited) + Radiant Slash / Soul Bound /
Holy-light Chop `maxUse=1`. Niya = Slayer `maxUse=0` + Chain Reaction/Trio/Rift `maxUse=1`.
SusaMaki = Flash Fire `maxUse=0` + White Blade/stone `maxUse=1`.

**Confirmed**: enforcing maxUse (reset per bout, consumed on fire) makes the PLAYER skill
counts match the captures almost exactly — SusaMaki 6.7 vs 6.6, Niya 8.6 vs 8.6, Mia 2.0 vs 2.5.
The engine currently ignores maxUse and re-fires `maxUse=1` skills every round.

Implementation (implemented then reverted to keep anchors green — ~3 small edits to re-apply):
`_run_bout` resets `u.skill_uses={}`; `_avail(u,sk)`/`_mark_use(u,sk)` helpers; gate the
tactical + pursuit loops (skip if not `_avail`, `_mark_use` on fire; readyRound charge marks
on fire, not on charge; Tactical Burst recast does NOT consume a use).

## 6. The exact engine gap (committed / all-green engine vs reality)

| metric | engine | reality |
|---|---|---|
| win | 72% | **94%** |
| rounds | 5.0 | **3.7** |
| player units lost | **1.02 / 3** | **0.31 / 3** |
| enemy units lost | 2.47 / 3 | 2.75 / 3 |
| dmg ratio | 1.24× | **1.72×** |

Per-hero (committed engine): player heroes all 0.88–1.05× of captured (≈correct); enemy
strikers 0.90–1.21×; **enemy commander Thiel 1.58× (72335 vs 45651), casts 8.2 vs 4.4** —
the single dominant error. Thiel over-casts because (a) maxUse is unenforced and (b) the
battle drags to 5–7 rounds, so her unlimited Binding Slash fires every extra round.

**Root cause**: the engine doesn't reproduce the kill cascade. It spreads player damage, so
no enemy dies early, the enemy commander is never focused, the battle drags, the enemy
over-casts, the player loses ~3× too many units, ratio collapses 1.72→1.24, win 94→72.

## 7. Convergent re-fit plan (the remaining work — all grounded, no fudging)

All four anchors must stay green to their real targets: testcase 9/9, baseline 6/6,
dot 7/7, **pursuit → 94% win / 3.7 rounds / 1.72× ratio / 0.31 player-loss / per-hero shape + cascade**.

1. **Enforce maxUse** (§5) — fixes skill counts; reduces enemy over-casting at the source.
2. **Reproduce the kill cascade** (§3) — make strikers die r2–3 and the commander r3.7. Lever:
   damage concentrates on still-alive units (so killed strikers stop absorbing and the
   surviving +DEF commander eats the remainder), + correct DEF differentiation (Thiel ~0.56×).
   Calibrate to the captured death-rounds (Nicole 2.3 / Dolly 2.8 / Thiel 3.7), NOT a fudge.
3. **Re-fit global scalars** so all four anchors hit their real targets after 1–2.

This is a coupled multi-variable fit (maxUse + cascade + scalars). Each lever is justified by
ground truth above. Apply, then validate all four together and iterate on the residuals.

## 8. Re-fit EXPERIMENT (2026-06-11) — maxUse + per-hit datamine; the single-dg WALL

Datamined the per-hit damage from the captures (every `retVal`):
- **`retVal` = troops destroyed, directly** (median `retVal / Δhp2` = 54999 ≈ max troops).
- **DEF mitigation measured: the +DEF commander Thiel takes ~0.61x what strikers take** (0.59-0.64
  across SusaMaki/Niya/Mia). The engine's raw DEF curve `def_ref/(def_ref+2·DEF)` already gives
  Thiel/Nicole = 0.427/0.683 = **0.625 ≈ 0.617** — **the DEF curve is correct.**
- Exact per-hit normal targets: SusaMaki→Thiel 3472 / Nicole 5625 / Dolly 4908; Niya→Thiel 2777 /
  Nicole 4859 / Dolly 4055; Mia→Thiel 3426 / Nicole 6391 / Dolly 5692.
- Multiplier breakdown (SusaMaki→Thiel vs →Nicole): restraint 1.00, dmg-dealt 1.42, dmg-taken 0.58
  IDENTICAL for both; only DEF mitig differs (0.427 vs 0.683). So per-target differentiation is right.

**Finding: the engine UNDER-damages per-hit (~0.78x of captured) and COMPENSATES by over-firing**
(no maxUse → 5 rounds → more casts), so per-hero totals look right but kills come too slow → drag.

**Experiment: enforce maxUse + raise `damage_global` 50→65** (to match the captured per-hit table):
- WIN 62%→**78%**, rounds 7→**5**, ratio 1.08→**1.32**, player-loss 1.33→**0.82**.
- **Striker cascade now EXACT: Nicole r2.32 (cap 2.33), Dolly r2.81 (cap 2.79).** Per-hit striker
  damage matches (Nicole 1.02x, Dolly 0.97-1.21x).
- Residual: enemy cmdr **Thiel still dies ~0.85 round late (4.52 vs 3.67)** → over-casts (5.5 vs 4.4)
  → 1.58x dmg. And player casts now slightly LOW (battle shorter): SusaMaki 5.1 (cap 6.6).

**THE WALL (now precise):** dg=65 over-damages the SHIELDED testcase — Rhea (Star-Shield tank) dies
in Battle 1 (58% stalemate vs target needs her to survive B1 → fall B2), so testcase drops 9/9→7/9.
testcase wants dg≈50; pursuit/baseline want dg≈65. **A single global `damage_global` cannot fit
both** because the OFFENCE model `off = soldier_off_stat + hero_stat·hero_off_weight` under-credits
the pursuit heroes (SusaMaki/Niya/Mia) ~30% relative to the testcase heroes (Patra/Rhea): SusaMaki's
offence × 65 matches her capture, Patra's offence × 50 matches her log → SusaMaki under-credited by
~65/50. The shield cap (`max_dmg_taken_reduction`=0.75) is grounded in the testcase log (can't raise
it to compensate = that would be fudging).

**ROOT: testcase/baseline/dot are calibrated to MANUAL TRANSCRIPTIONS; pursuit to PRECISE CAPTURES.**
Resolving the offence-model weighting (so ONE set of scalars + maxUse reproduces ALL real per-hit
damage) requires the OTHER matchups' captured per-hit data. **NEXT DATAMINING: capture (sniffer
running) the baseline ATK-vs-DEF mirror, the shielded testcase (Patra/Rhea/...), and the DoT matchup**
— then re-fit the offence model + maxUse + dg to the combined captured per-hit ground truth. Engine
reverted to all-green (maxUse + dg=65 backed out; both trivially re-appliable from §5 + this section).

## 9. CONFLICT RESOLVED (2026-06-11) — shielded-grind capture proves dg=65 is universal

Captured 20 fresh battles (`notes/sim/captures/anchors/`) of the SAME pursuit matchup but with the
enemy commander Thiel made a sustain tank: modular **Skyland (Strategic)** + **Self-Healing
(Strategic)**, max DEF (attackers kept +0). +1 misclick battle with the TESTCASE heroes
Patra(60)/Rhea(40)/Slider(66) — a bonus per-hit point.

**Result: the shield reproduced the testcase dynamic** — Thiel now survives Battle 1 →
**stalemate → Battle 2/3 victory** in ~8/20 battles (was: dies ~round 3 every time). The pre-war log
is explicit:
- Thiel casts **Skyland** → its "2 of our troops" landed on **Nicole + Dolly**, each gaining
  **DMG-Taken-Reduced 19.32%+5.20% = 24.52%** (buff id 8).
- Thiel casts **Self-Healing** → Thiel heal coef **1.4+0.28 = 1.68** + **DEF → 658.6** (from ~403).

**This resolves the dg=50-vs-65 conflict in favour of dg=65, universally.** Measured: the
UNSHIELDED strikers take **~0.74-0.755× of base0** even at round 1 (full troops). That is exactly
`base0(dg=65) × (1 − 0.2452 Skyland reduction) = 0.755`. So the underlying per-hit scale is STILL
**dg=65** — the drop is a *modeled* DMG-Taken-Reduced buff, NOT a lower damage scalar. The testcase
tank (Rhea) survives via **DMG-Taken-Reduced + heal + DEF**, not via dg=50; the old testcase fit used
dg=50 to FAKE that survival. So: **set dg=65 everywhere + model the shield/heal at the captured
magnitudes** (Skyland 24.52% DTR per cast capping at the ~74% stack cap; Self-Healing 1.68 heal +
DEF buff) → the tank survives for the right reason and all four anchors share one scale.

**RE-FIT (now fully grounded, no fudging):** dg=65 (universal, confirmed across base0 + alloc +
shielded) + enforce maxUse (§5) + ensure DMG-Taken-Reduced (buff 8) + heal + DEF buffs model at the
captured magnitudes so the testcase tank survives at dg=65. Then validate all four. The earlier
"testcase dies at dg=65" failure was the engine's shield/heal being too weak at the higher scale —
calibrate it to these captured numbers. Per-hit normal targets + DEF curve (0.61) already confirmed.

## 10. DERIVED from game files + captures (2026-06-11)

**Heal (Self-Healing, buff 107):** game files give coef (0.7->1.4 maxed, NewSkillInfo.csv) but NOT
the multiplier (server-side; decompiled client only has ShowSoldierCount display). Captures give it:
**heal = coef x 0.063 x MAX_troops, capped by the recoverable (Slight) pool, scales with MAX troops
(constant 5856 as Thiel's current fell 49k->23k), NOT current.** Engine `heal_scale` set 0.05->0.063.

**DMG-Taken-Reduced DEF-scaling (buff 8), DERIVED, replaces a x6.0 fudge:** affectedByAttr=1 => scales
with the CASTER's DEF. Two captured Skyland points (coef 0.08): Thiel DEF 589.6 -> 19.32%, and (misclick
battle, Slider debuffed Thiel's DEF to 438.4) -> 16.41%. Both solve to **DTR = coef x (1 + DEF/417)**
(+ flat relic bonus). Cross-check: captured Rhea Star Shield 65.05%+30% = coef 0.25 x (1+DEF/417) at her
DEF + 30% relic. Engine `_affected_pct` had `coef x (1+(DEF+Ruin)/400) x 6.0` -> 144% (pinned to cap);
replaced for buff 8 with `coef x (1 + casterDEF/dtr_def_ref)`, dtr_def_ref=417. The misclick battle
(Patra/Rhea/Slider) was a goldmine: Rhea Star Shield 65.05%+30%, Slider DEF-debuff 18.45%, DMG-taken-
increased 35.06%, Self-Healing DEF-buff +35 (heal coef 1.05+0.28 for the testcase heroes).

## 11. THE TRANSCRIPTION WALL (2026-06-11) — why testcase won't go green at dg=65

State after the grounded re-fit (dg=65 + maxUse + heal 0.063 + derived DTR): **pursuit win 72->79%,
ratio 1.24->1.35, striker cascade EXACT; but testcase 7/9, baseline 5/6, dot 5/7.** Testcase fails ONLY
the two "Rhea survives Battle 1" targets: she's cap-protected (74%) yet dies ~46% at dg=65. Root: dg=65
is +30% vs the dg=50 the TRANSCRIPTION was fit to, and **the transcription is imprecise** — it recorded
Rhea's Star Shield as 90.17%, but the capture proves 65.05%. So testcase/baseline/dot targets are built
on hand-transcribed numbers that disagree with the precise captures (which confirm dg=65). **Cannot
honestly tune the engine to pass transcription targets that the captured ground truth contradicts.**
RESOLUTION OPTIONS: (a) capture the ACTUAL testcase + baseline + dot matchups (the misclick proved the
user CAN field Patra/Rhea/Slider) -> re-derive those validators from captures -> all four on ground
truth; or (b) treat the transcription validators as approximate and optimise for captured accuracy.
Pursuit residual (79% vs 94%, 5 vs 3.7 rounds) is the remaining captured-data gap.

## 12. Testcase RE-GROUNDED as a capture-based shield validator (2026-06-11)

Per user, instead of fielding the original Rosetta enemy (Rhea/Aguria/Satoru), the testcase is
re-derived from the 20 shielded-Thiel captures (kept enemy heroes; ONLY Thiel adjusted into a
sustain tank: Skyland+Self-Healing+max DEF). `simulator/validate_shield.py` formalizes it.
**Captured targets (n=20):** player win 65% (13W/6L/1D), rounds mean 4.70 / median 4, Thiel
(enemy cmd) survives 35%, enemy dead 2.50/3, player dead 0.80/3, dmg ratio P/E 1.50.
fightRet enum confirmed: 1=enemy-cmd-dead (player win), 2=player-cmd-dead (loss), 3=draw.

**Engine vs these targets: 0/6** — win 47% (65), rounds 6 (4.7), Thiel-survive 53% (35),
dmg ratio 1.05 (1.50). Per-hero: SusaMaki 0.76, Mia 0.85 (UNDER); Thiel 1.40, Dolly 1.18 (OVER);
Niya 1.04, Nicole 0.98 (OK). **This is the SAME signature as pursuit** -> a systematic
THROUGHPUT/BALANCE gap (player carries under-credited, enemy commander over-credited), NOT a
magnitude error (dg/DTR/heal/maxUse are all derived-correct now). Confirmed across THREE
capture-grounded matchups. The enemy commander out-lasting drags every fight ~1-1.5 rounds and
flips ~20% of outcomes. NEXT: close the carry-vs-enemy-cmd balance (why SusaMaki/player commander
under-fires ~0.76 while striker Niya is 1.04; why enemy cmd Thiel over-credits ~1.4) -- likely the
offence/throughput model or commander-targeting/protection, the last un-grounded piece.

## 13. WITCHER BUG FIXED (2026-06-11) — the balance lever, grounded

Root cause of the carry-vs-cmd gap: `_self_buff_pct` did `(coefficient/100) * (ATK/per200)`. The
`/100` is correct for whole-number `flatMagnitude` tokens (Divine Punish at=9 = 15.2) but WRONG for
Witcher (at=33), whose token is a FRACTIONAL `coefficient` (0.13, maxedValue 0.25). So SusaMaki's
Witcher pursuit-dmg buff applied at **0.003 instead of the captured ~0.563** -> her pursuits got
~zero amplification -> the entire player-carry under-credit. Fix (combat.py at=33 handler): use the
skill's maxed coefficient * ATK/per200 = 0.25 * (ATK ~432/200) = **0.540** (captured ~0.563). One fix
lifted BOTH grounded matchups: **pursuit 79->88% win, ratio 1.35->1.62, rounds 5->4, player-loss
0.82->0.47; shield validator 0/6 -> 3/6 (win 47->64% PASS, Thiel-survive 53->36% PASS).** Residual
(small): pursuit 88 vs 94%, ratio 1.62 vs 1.72; shield rounds 6 vs 4-5 + ratio 1.23 vs 1.30; SusaMaki
0.87, Mia 0.85 still slightly under (possible similar buff/throughput residual on Mia). The
transcription anchors (testcase 7/9, baseline 5/6, dot 5/7) remain superseded by the capture-grounded
pursuit + shield validators at dg=65.
