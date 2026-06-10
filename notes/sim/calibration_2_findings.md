# Matchup 2 (DoT Lab) — findings from the in-game log

Source: `calibration_2_dot.md` Results + Battle log. Player = Cthugha·Sp / Cthugha / Nyx (DoT +
sustain), enemy = Thiel(+DEF) / Nicole(+ATK,4★) / Dolly(+DES), Archer. **Match outcome: 60% player
win over 10 runs** (1 stalemate→victory, then 5 wins / 4 losses; small sample → ~50–60%). Detailed
match 1 = **Battle 1 STALEMATE (8 rounds) → Battle 2 VICTORY**.

## DoT mechanics (NEW — this was a pure placeholder before)
1. **DoT ticks at the BEFORE-ACTION phase** as `[<skill>][<Burn|Curse>] Effect Activated, E[X] Loss N`.
   Applied to N targets (Exploding Flame → 2; Soul Drain → 3) for a few rounds; re-cast = "Effect
   Updated" (refresh), expires = "Effect Disappeared".
2. **~Linear in the stated coefficient.** Burn (Exploding Flame, coef **1.0**) ≈ **2×** Curse (Soul
   Drain, coef **0.5**): same target Thiel, R6 → Burn **1,577** vs Curse **708** (2.23×).
3. **Scales with the CASTER (army size / DES), NOT the target's HP.** Burn ticks fall as Cthugha·Sp
   loses troops over the fight: R2 **3,982** → R3 **3,660** → R5/R6 **1,577** → R8 **674** (caster
   ~45k → ~3k troops). So DoT damage ∝ caster troops (× coef × DES), like other channels.
4. **DEF effect on DoT: present but secondary** — the high-DEF Thiel takes less than low-DEF
   Nicole, but most of that gap is the caster-troop decline above; treat DoT as DEF-mitigated only
   mildly (fit the residual). (Open: exact DEF dependence — the agent should fit it.)
5. **DETONATE (Element-Burst style).** `[Cthugha·Sp][Detonate] Effective → E[X] Loss N` bursts the
   DoT for a big hit: Dolly **6,716**, Nicole **5,542**, Thiel **3,129 / 5,311**. So Burn/Curse can
   be consumed for burst damage (a mechanic to add or approximate).
6. **Shield = absorb one instance** (confirmed): `[Shield] Resisted This DMG … Effect Disappeared`
   — Lunar Guardian / Fire Emblem grant shields; matches the engine's shield model.
7. **Lunar Guardian = shield + heal-over-time** (`Restore ~1,100–1,600/round` to 2 allies). This
   sustain is what produced the 8-round stalemate; the engine must apply it or the player dies early.

## Tick data (calibration anchors)
**Burn — Exploding Flame, coef 1.0, caster Cthugha·Sp (+229 DES):** R2 Nicole 3,982 · R3 Dolly 3,660
· R4 Dolly 1,442(kill-clamped) · R5 Thiel 1,577 · R6 Thiel 1,577 · R8 Thiel 674 · B2R1 Thiel 227(clamp).
**Curse — Soul Drain, coef 0.5, caster Nyx (+229 DES):** R3 Dolly 1,164 · R3 Thiel 898 · R4 Thiel 898
· R6 Thiel 708 · R7 Thiel 708 · B2R1 Thiel 344.
**Detonate bursts:** ~3,100–6,700.

## Calibration targets for `validate_dot.py`
- **Player win ~50–60%** over many seeds (target ~60%, small in-game sample).
- **Match 1 shape:** Battle 1 reaches an **8-round stalemate** (player sustain holds), Battle 2 = victory.
- **Burn tick** in the **~700–4,000** band, **declining with caster troops**; **Curse ≈ 0.5× Burn** for the same caster/target.
- Enemy commander Thiel (+DEF) is the last to fall; the +ATK / +DES strikers die first (Nicole, Dolly defeated mid-B1).
- Detonate produces ~3k–6.7k bursts when it fires.

## Per-unit (Battle 1) for cross-check
Ally kills: Cthugha·Sp 78,872 / Cthugha 24,195 / Nyx 55,548. Enemy kills: Thiel 150,262 (tanky
commander did most ally damage) / Nicole 7,440 / Dolly 12,158. Heals: Cthugha·Sp 4,691, Cthugha
3,939, Nyx 890.

## Engine work this implies
- Replace the placeholder DoT with: `tick ≈ coef × off(caster, DES) × troop_scale(caster) × (mild DEF mitigation)`, ticking at before-action for the stated duration; Curse and Burn share the formula (coef differs).
- Ensure Lunar Guardian (shield + HoT) and Fire Emblem are applied (sustain → stalemate).
- Add/approximate **Detonate** (consume DoT for a burst).
- Build `validate_dot.py`; keep `validate_testcase.py` 9/9 and `validate_baseline.py` 6/6.
