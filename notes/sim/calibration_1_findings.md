# Matchup 1 (Vanilla Baseline) — findings from the in-game log

Source: `calibration_1_baseline.md` Results section. Near‑mirror (both teams Thiel/Nicole/Dolly,
same gear/stones, Archer troops) differing ONLY in stat allocation. **Player LOST** — single
battle, decided **Round 4** when the player's commander (Thiel, +229 ATK) was wiped; the enemy's
commander (Thiel, **+229 DEF**) survived (20,120) vs the player's last unit Dolly (11,370).

## Confirmed mechanics (new)
1. **Troop count by hero star** (Lv80, advancement 5): **5★ = 55,000, 4★ = 51,000** (Nicole);
   −4,000/star ⇒ 3★ ≈ 47,000. **No commander troop bonus** (commander Thiel 5★ = 55,000 = a
   non‑commander 5★). → Engine `build_team` fixed to star‑based counts; the old +commander_talent
   (+3,000) and flat‑55k were wrong.
2. **A battle can end before round 8 by commander death** — no stalemate/rematch needed when one
   side is clearly stronger. (Stalemate→rematch only if neither commander falls in 8 rounds.)
3. **DEF allocation dominates survivability** — the *only* difference between the mirror teams was
   allocation, and **+229 DEF flipped the mirror**: the +DEF Thiel outlived the +ATK Thiel and won
   as commander. ⇒ the DEF‑mitigation term must be strong (a +229 DEF swing is decisive).
4. **"Pure damage" modular skills carry a rider:** **Soul Bound** and **Radiant Slash** apply
   **DMG Dealt Reduced 15.08%** to the unit they hit (a debuff on the victim). So the baseline
   isn't perfectly clean — but the −15% dmg‑dealt is small and identifiable.
5. **Skill structure:** each skill rolls a **"Ready Probability"** (preparation) then a **"Use
   Probability"** (`base%+flat`, flat from relic/rune/awaken). Multi‑hit skills emit N consecutive
   Loss lines: **Rift** = 4 hits (`Launch 3‑7`), **Sky Rain Arrows** = 4 hits on *each* of 3 targets
   (`Launch 3‑5`), Chain Arrows / Arrows Volley multi‑target.

## Damage magnitudes (calibration anchors, no attribute buffs in play)
Effective stats (engine build, post troop‑fix): +ATK builds ATK ≈ 436–521, +DEF Thiel DEF ≈ 403,
+DES Dolly Ruin ≈ 407; soldier (T6 Archer) atk 236 / def 95 / hp 108.
- **Normal attacks ≈ 3,950–5,640/hit.** Ally Dolly(+ATK)→enemy Dolly(+DES) = **5,641**; enemy
  Dolly(+DES)→ally Dolly(+ATK) = 4,516; enemy Thiel(+DEF)→ally Thiel = 4,771; ally Thiel(+ATK)→
  enemy Nicole = 5,149; ally Nicole(+ATK)→enemy Nicole = 4,927.
- **Skill hits:** Chain Arrows → 4,842 & 6,802; **Purgatory Trial** → **9,702 & 10,057**; Rift
  per‑hit ≈ 1,900–2,000 (×4); Sky Rain Arrows per‑hit ≈ 1,500–2,100.
- Attacker **ATK** raises damage (ally Dolly+ATK 5,641 > enemy Dolly+DES 4,516, same base hero);
  defender **DEF** lowers it (and made the +DEF commander win).

## Calibration targets for a `validate_baseline.py`
- **Outcome = a TRUE COIN‑FLIP. Authoritative target: player win rate ≈ 50% (10 in‑game runs = 5
  wins / 5 losses).** The matchup is balanced and variance‑driven (decided by RNG: skill/prep
  procs, multi‑hit ranges, targeting). This is a tight calibration constraint: **a +229 ATK
  allocation edge and a +229 DEF allocation edge must come out EQUAL** (neither dominates). Aim
  the model at ~50% ± a few %; the +DEF commander is marginally tankier but the +ATK side hits
  marginally harder, and they cancel.
- **Single battle, decided ~round 4** (no rematch — one commander falls before round 8 in this
  close fight, but ~4 rounds, not a full 8‑round stalemate).
- Both teams **nearly wiped** at the end (run 1: left ≈ 11,370 / right ≈ 20,120 Health) — a tight
  finish either way.
- Top dealers (run 1): enemy Thiel ≈ 67,876 kills, ally Dolly ≈ 84,669; team kills ≈ 140,880
  (player) / 149,630 (enemy). (Per‑run kills vary with the RNG; use as ballpark, not exact.)
- Normal hits land in the **~4,000–5,600** band at these stats.

## Open model gaps this exposes
- **Damage magnitude** vs the engine's current `damage_global`/`def_mitigation` needs refitting so
  both this baseline AND the original Rosetta Stone reproduce (the Rosetta fit was anchored to one
  shielded‑tank fight; this clean fight should tighten `def_ref`/ATK scaling).
- **Skill stones not modelled** (4th skill) — still pending; not in this baseline's player builds if
  run with empty stones, but present if filled.
- Skill riders (Soul Bound/Radiant Slash −15% dmg‑dealt) — model or note.
