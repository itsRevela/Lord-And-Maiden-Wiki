# Damage-formula calibration findings (from the Rosetta-Stone dataset)

Derived from `data/sim/calibration.json` (90 damage instances + 54 revealed in-battle
attribute values + per-unit buff states, both battles). These constrain the rework's
damage/heal model. The exact server equation is not in the client, but the log pins down
the *structure* and several coefficients.

## In-battle attribute values are recoverable
The `(NNN)` after a percent effect = `base × (1 + pct/100)` (for buffs) or
`base × (1 − pct/100)` (for reductions). Cross-battle consistency confirms this, e.g.:
- **Satoru** (4★, +229 ATK Spd, cavalry): from Elf Deer +53.12% → ATK 373.5 ⇒ base ≈ 244;
  Spd 590.1 ⇒ ≈ 385; DES 288.1 ⇒ ≈ 188. Battle 2 (+56.76%) reproduces ATK ≈ 240, Spd ≈ 379.
- **Aguria·Sp** (5★, +229 ATK, archer): ATK 959.9 ⇒ base ≈ 627; DES ≈ 216; Spd ≈ 213.
- **Enemy Rhea** (5★, +229 DEF, cavalry, commander): from Dark Arrive −29.77% → ATK 252.1 ⇒
  base ≈ 359; **DEF 610.2 ⇒ ≈ 869**; DES ≈ 205; Spd ≈ 284.

⇒ Hero in-battle attributes are in the **hundreds**; DEF builds reach ~870 DEF, ATK builds
~620–960 ATK. The simulator's maxed stats should land in this range (sanity target).

## Confirmed mechanics & coefficients
1. **Counterattack = 0.84 × a normal attack.** Ally Rhea (DEF build) normal vs enemy Rhea
   ≈ 482; her counters = 396 / 403 / 404 / 405 / 427 (≈ 0.82–0.84×). The passive's stated
   `DMG Coefficient 0.70+0.14 = 0.84` matches. ⇒ counter damage = normal_damage × 0.84.
2. **Mitigation is multiplicative and two-factor: DEF *and* DMG-Taken buffs.** The *same*
   Patra skill: Ghost Bone → Aguria **15,984** vs → enemy Rhea **1,917** (≈ 8.3×); Magic
   Spear → Aguria **19,116** vs Rhea **2,139** (≈ 8.9×). Aguria: DMG-Taken **+51.89%**, DEF
   reduced (~239). Rhea: DMG-Taken **−90%+30%** (Star Shield) AND DEF ~869. So the model
   needs `dmg = raw × dmg_taken_mult × def_mitigation` where dmg-taken buffs are first-class
   and can swing damage ~10×. (Star Shield's reduction is the single biggest lever in the
   fight — enemy Rhea is near-unkillable while it holds.)
3. **Damage scales with attacker ATK.** Patra (archer, +229 ATK) normal vs Satoru = 3,347 /
   3,700; ally Rhea (DEF build, low ATK) normal vs enemy Rhea ≈ 482; Slider (DES build) ≈
   500–570. Same target class, very different output ⇒ offensive stat dominates raw.
4. **Damage scales with attacker troop count.** All normal/skill outputs fall as the attacker
   loses troops over the fight; the army-size factor is real (matches our `troops_now` term).
5. **Assault Real DMG is flat & ignores DEF.** Patra's Ghost-Bone Assault pursuit = a constant
   ~**671–726** per hit regardless of target (Aguria, Rhea, Satoru all take the same), clamped
   to remaining HP on a kill (585). Stated `Real DMG Base 32.17+7.2`. It does NOT vary with the
   target's DEF or shield ⇒ true damage. (671 vs 726 tracks Patra's own state between rounds;
   model real-dmg as `RealBase × attacker_scale`, DEF-independent.)
6. **Skill > normal by a large factor.** Patra's skill column (80,543) dwarfs her normal
   column (12,352) in B1 — skills + Assault are the win condition; normals chip shielded units.
7. **Heal (Field Therapy Self-Heal) restores Slight-Wounded → Health**, blocked by Heal Ban;
   restores 0 when at full Health (L348) and up to thousands when wounded (4,962 at L459).
   Healing Coefficient shown `1.05+0.28` (ally) / `1.4` (enemy).

## Proposed transparent damage model (rework target)
For one hit of channel `ch` from attacker A on defender D:
```
raw      = coef[ch] * off(A, ch) * troop_scale(A)          # off = ATK/DES/Spd-based offence
mitig    = def_factor(D)                                    # DEF reduces; ASSUMPTION on shape
dmg      = raw * mitig * dmg_dealt_mult(A, ch) * dmg_taken_mult(D, ch) * restraint(A, D)
# real/assault/splash: mitig = 1 (DEF-independent); flat real_base * troop_scale(A)
# counter: dmg = normal_dmg * 0.84
heal     = heal_coef * heal_power(caster)   # restores Slight->Health, capped, blocked by Heal Ban
```
- `dmg_dealt_mult` includes general DMG-Dealt-Increased (5/Green-Tea 26.91%/Stalemate +33%),
  channel-specific (Tactical DMG Dealt +24.8%+9%), etc.
- `dmg_taken_mult` includes DMG-Taken-Reduced (Star Shield, Knight Creed, Reactive Block) and
  DMG-Taken-Increased (Noise +42.89%+9%). These STACK and dominate.
- Coefficients per skill come from `data/sim/skills.json` (maxedValue) + the rune/relic/awaken
  trigger & coef bonuses already wired.

## Validation targets (the simulator must roughly reproduce)
- **Battle 1 = Stalemate, Battle 2 = Victory** (survivors carry; +33% stalemate buff in B2).
- Per-unit Kills (B1): Patra ≈ 92,895, Rhea ≈ 13,370, Slider ≈ 6,032; enemy Aguria ≈ 26,031.
- Enemy Rhea (Star Shield) survives B1 with ~22k and only falls in B2 once shields lapse.
- Aguria defeated mid-B1; Satoru tanky via heals until disarmed-locked.
- Left team ends B1 with ~138,564 Health (≈ 84%); right team ~52,703 (≈ 32%).
