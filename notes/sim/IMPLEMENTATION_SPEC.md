# LAM simulator — research-confirmed implementation spec

Synthesized from the 6-facet research + adversarial validation (workflow wf_def5d531-46c, 12 agents).
Only items the VALIDATORS independently confirmed against the decompiled client / `data/sim/*.json` /
the in-game logs are listed as "implement". Server-side unknowns are listed separately and must be
modeled as **labeled `ASSUMPTION` knobs fit to MEASURED magnitudes — never tuned to hit a win-rate.**
Full detail: `notes/sim/_research_digest.md`.

## GUARD RAILS (no fudging)
- **Calibrate scalars to MEASURED per-hit/tick magnitudes** (clean baseline normals ~4,000-5,600;
  pursuit hits ~6,000-9,700; Burn ticks ~700-4,000), **NOT** to a target win-rate or pass-count.
- **Never widen/weaken a validator target.** Fix the model. If a target genuinely can't be met without
  a fresh in-game log, say so and stop — do not adjust knobs to fake it.
- Every constant traces to a `data/sim/*` field, a decompiled line, or a logged measurement; otherwise
  it's an explicit `ASSUMPTION` knob, labeled as such.

## WHAT'S ALREADY CORRECT — do not "fix"
- **Per-instance ATK scaling is essentially right.** The clean isolated allocation effect is **~1.25x**
  (baseline Dolly +ATK 5,641 vs +DES 4,516; calibration_1_findings:29-30); the engine's
  `offence = soldier.atk + hero_stat*0.20` gives ~1.16x — a ~7% gap, NOT 2x. The "+ATK out-damages 2x"
  in the pursuit log is a THROUGHPUT + in-battle-buff confound, not per-hit scaling. **Do NOT crank
  `hero_off_weight` to chase 2x — it breaks the baseline mirror.** (If anything, a tiny lift toward
  ~1.25x clean, re-checking baseline stays ~50%.)
- DEF mitigation `600/(600+2*DEF)` matches the one clean DEF read (-0.46 exponent, DEF192->403 ratio
  0.712). Do NOT flatten it (would break baseline).
- Counter 0.84, Reactive Block 0.30 proc / 0.592 reduction, DMG-Taken cap ~0.75, 20/40/40 normal
  targeting, stalemate +33%/stack, server-authoritative replay model — all confirmed; keep.
- Star troop/points for 5★ (55,000/+229) and 4★ (51,000/+179) are EXACT (decompiled maxed-preview
  cs:77749-77767). Only 3★ is wrong (see below).

## CONFIRMED FIXES (client-grounded, validator-approved)

### A. combat.py `_fire_skill` — model skills as WAVES (the big one)
A skill's hits = the list of its `at=101` effect groups. For each group, in order:
1. **Roll the per-effect `triggerChance`** (token[4]); skip the wave if it fails. (Rift = 3@1.0 +
   4@0.30 → E[4.2] hits, matching the log's 4. Currently ALL groups fire unconditionally → over-count.)
2. **Use the per-effect `coefficient` (token[5]) × level scaling**, NOT the skill's `maxedValue`.
   (maxedValue ≈ sum of group coefs; firing N groups at maxedValue double-counts. ReadyRound=1 prep
   skills' token coef genuinely differs from initVal — read the token, don't derive it.)
3. **Targeting / CONCENTRATION**: `targetCategory==2` "Enemy Troops" = the OPENER → pick targetCount
   distinct enemies (use the 20/40/40 weighting for the first pick — see unknowns); `targetCategory==0`
   "Inherit action target" = re-hit the SAME target(s) the opener chose (focus memory), NOT a fresh
   uniform re-sample. Multi-hit skills CONCENTRATE. Replace the current squishiness-spread in
   `_pick_attack_targets`.
4. **151/153 bonus pursuits**: model as SEQUENTIAL re-triggers (the log renders each as its own
   "Use [Skill]" line + one hit) — after a pursuit hit lands, roll each follow-up group's chance in
   order; on a proc fire one more pursuit hit carrying its OWN token coef, and re-apply the Assault
   rider. Currently dropped entirely (isAction=False → skipped). 151 has tcat=2 (may spread), 153
   tcat=0 (focus).
5. **Assault (at=70) rider** fires once per attack event (normal + each pursuit hit), flat real-DMG
   base from token[6] + relic, DEF/shield-ignoring. Extend to the new 151/153 events.

### B. model.py — level scaling, pursuit channel, in-battle buffs
- **Level law**: `coef(L) = initVal + L*upVal`, L∈1..10, `maxedValue == coef(10)` (decompiled
  GetSkillUpDes cs:9940-9949; verified across all 416 skills). NOT `(L-1)/9`. Main/modular = lv10 (=
  maxedValue, unchanged). **Skill STONES = lv5** → `coef(5) = initVal + 5*upVal`; use the exact ratio
  `(initVal+5*upVal)/(initVal+10*upVal)` (≈75%, varies 74.5-76% per skill — not a flat constant).
  For `upType==45` skills the TRIGGER prob also scales by the same law.
- **Skill stone as a 4th equipped skill** (the `skillStone` flag marks stones), lv5; constraints:
  optional, no per-category cap, no two identical stones per team, no two identical skills (innate+
  stone) per team (user-confirmed/server-enforced — label as such).
- **Pursuit damage scales with ATK, not Speed**: `CHANNEL_PRIMARY_HERO_STAT["pursuit"]="atk"`
  (`affectedByAttr==0` on every direct at=101 effect incl. pursuit; Speed governs trigger/turn-order).
- **In-battle self-buffs folded into effective offence DURING battle** — the static build undercounts
  in-battle ATK ~1.9x (calibration.json reveals: Satoru 129→~244; Mia Divine Punish 521→989, log L278).
  Apply at=9 (ATK Attribute Increased), at=5 (DMG Dealt Increased), at=33 (Pursuit-DMG) as live
  effective-stat / dmg-dealt buffs (magnitude = the per-200 ASSUMPTION knob, fit to the log's +49.79%).
- **troop_scale for DIRECT channels is over-steep** (linear; log implies ~sqrt for the attacker's own
  attrition). Consider a gentler attacker-troop factor for direct hits (the real/Assault channel
  already uses 0.5+0.5*ts; DoT already floors at 0.15). ASSUMPTION exponent — fit, document.

### C. data.py — build aggregation (pure correctness, client buff_ids)
- **Awaken**: route Skill/Effect-Trigger-Probability awakens (buff_id 45/1) into `skill_trigger_bonus`
  (135/187 currently dropped). Match 'trigger probability' BEFORE the stat fallback.
- **Healing-Coefficient (buff_id 3) mis-routed as damage coef** — separate it from 'coefficient'
  (require buff_id 2 / 'dmg coefficient' for kind='coef').
- **"All Attributes Reduced" (buff_id 18) sign bug** — apply as negative.
- **Relics**: route by buff_id, not keyword (21/98 currently return None): 5/6→dmg_dealt±, 7/8→
  dmg_taken±, 31/33→tactical/pursuit dmg-dealt, 41→real_dmg_bonus, 4→blood-sucking. Wire into the
  existing gear_dmg_dealt/real_dmg_bonus channels.
- **3★ values**: troop count 49,000 (not 47,000), free points 169 (not 129). (GetMaxSoldierCount(80,3,
  full)=49000; num4=40+79+3*20=169.)
- **PVE/PVP dmg-dealt/taken double-count** — split at decode; apply only PVE in PvE battles.
- soldier-type-specific gear keys (Archer/Cavalry/... ATK) missing in data.py `_SOLDIER_ATTR` (latent).

### D. DoT / Detonate / sustain (combat.py / model.py)
- **Remove the DoT DEF-mitigation curve** (no DEF term in the server spec; no DEF trend in the log).
- **Detonate (at=72) is DETERMINISTIC** on re-cast onto a Burning target (drop the 0.4 chance gate)
  and **does NOT consume the Burn** (log: R3 detonate Dolly → R4 Dolly still takes a Burn tick).
- **Heal shape**: scale off the HEALER's troops/Soldiers-HP (with a floor, sublinear decline), NOT
  `coef*heal_scale*target.slight`.
- **Shield = absorb the FIRST incoming instance** (one layer, can't stack); do NOT special-case "largest".
- DoT scales with the CASTER (already correct — keep). Snapshot-vs-live-recompute timing is NOT cleanly
  resolved (needs a fresh log) — keep caster-scaled but note the open question.

### E. Re-fit rule (do this in the SAME change as A-D)
Using per-effect coef ≈ halves raw skill damage and gating triggerChance cuts multi-hit volume, so the
global scalars MUST be re-derived together, fit to the **measured** magnitudes:
- `damage_global` / `normal_attack_coef`: fit so clean baseline normals land ~4,000-5,600 and pursuit
  hits ~6,000-9,700. (Log-implied normal coef is ~1.05-1.10, not 0.9 — re-derive jointly.)
- `dot_global`: re-fit so Burn ticks stay in ~700-4,000 (the over-count it had absorbed is now gone).
- Treat the DoT win-rate carefully: the in-game 60% was a 10-run anecdote fit against the buggy enemy.
  Match the dot SHAPE (B1 stalemate→B2 victory, Burn band + decline, Curse≈0.5×Burn, detonate band,
  Thiel-last) and report the resulting win-rate honestly — do NOT tune knobs to force 60%.

## SERVER-SIDE UNKNOWNS — model as labeled ASSUMPTION knobs, never fudge; flag if a target needs them
- The core stat→damage equation & the "Affected by X / per-200" coefficient (the exact ATK/DEF/troop
  powers). Only the SHAPE is known. Keep the global scalar an `ASSUMPTION`.
- Whether 20/40/40 governs SKILL first-pick or only normals (the squishy-commander crux). Use 20/40/40
  for the opener as the best estimate; label it.
- DoT snapshot-vs-live, DoT/Detonate amplification by tactical buffs, exact detonate magnitude.
- The TRUE DoT-matchup win-rate after the over-count fix (needs a fresh in-game DoT run).
- Real-DMG/Assault base→Loss scaling with troops/ATK; level-suppression curve; restraint application
  point (zero log coverage — all logs Archer-vs-Archer); within-bucket target selection; speed tie-break.

## VALIDATION (all must hold; pursuit is the goal)
- testcase 9/9, baseline 6/6, dot: shape + bands green (win-rate reported honestly).
- pursuit: in-game **100% player win in ~4 rounds**, per-hero shape (Niya/SusaMaki top; +ATK > +DEF/DES),
  Assault band ~350-850 declining, throughput (Niya ~7 hits/round).
