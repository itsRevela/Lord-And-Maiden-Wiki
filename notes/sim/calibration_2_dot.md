# Calibration Matchup 2 — "DoT Lab" (Burn & Curse channels)

*Scenario 2 of 3. See also: `calibration_1_baseline.md`, `calibration_3_pursuit.md`.*

**Purpose.** Burn/Curse damage‑over‑time is in **none** of our data — the simulator's per‑round
DoT is currently a placeholder. These three heroes carry DoT with **known coefficients printed
in the skill text**: Cthugha·Sp's Exploding Flame is **Burn coef 1.0**, Cthugha's Blazing Sword
is **Burn** at a different coef (lets us confirm DoT scales linearly with the coefficient), and
Nyx's Soul Drain is **Curse coef 0.50**. They're allocated **+229 DES (Ruin)** because DoT is
hinted to scale with DES — maxing it gives the strongest signal.

The enemy is a plain trio with **no healer and no DoT‑resist**, so the before‑round
`Burning DMG Taken` / `Curse DMG Taken` ticks are *clean*. The enemy's varied allocation
(DEF/ATK/Ruin) also tells us whether DoT **ignores DEF** (identical tick on the high‑ and
low‑DEF targets → true‑damage‑like).

**Calibrates:** the DoT per‑round formula (coefficient → soldiers lost), whether it scales with
caster DES or target HP, Burn‑vs‑Curse difference, and DEF‑independence.
**Key reads:** the per‑round `… Before Each Round … DMG Taken` tick lines on each enemy.

## Setup (applies to all units)
Every hero is **Lv 80, advancement 5, 55,000 troops**, same gear set (control; mixed = no set
bonus). Names verified against the game data.

## What to record (priority order)
1. **The per‑round DoT tick lines** (`Burning/Curse DMG Taken`, the `Loss N` it produces) on each enemy — this is the core data here.
2. All other per‑round damage lines (`Loss N (current/max)`), actor → target.
3. **In‑battle `(NNN)` attribute values** (esp. each DoT caster's DES).
4. End‑of‑battle per‑unit troop counts + team Health/Slight/Severe/Death summary.

---
---

## ENEMY FORMATION  *(clean 4★/5★ damage dummies — no heals/shields/resist, varied DEF)*

Thiel (commander):
lv 80 (level 5 advancement), attributes allocated: +229 DEF
skills: (main)binding slash lv10 (lv5 relic effect), radiant slash lv10 max awakening, soul bound lv10 max awakening
Skill stone: Magic Spear lv5

weapon: night's sword
clothes: day's robe
shorts: fanatical shorts
helmet: day's helmet
gloves: fanatical bracers
boots: night's boots
left accessory: light winged dagger
right accessory: aegis
relic: Thiel Relic lv5  *(optional)*
Rune: none

magic messenger: Snow Fox (T6)

T6 archer troops (55,000x)

---

Nicole:
lv 80 (level 5 advancement), attributes allocated: +229 ATK
skills: (main)fly flowers lv10 (lv5 relic effect), rose sword lv10 max awakening, rose blade lv10 max awakening
Skill stone: Magic Spear lv5

weapon: night's sword
clothes: day's robe
shorts: fanatical shorts
helmet: day's helmet
gloves: fanatical bracers
boots: night's boots
left accessory: light winged dagger
right accessory: aegis
relic: Nicole Relic lv5  *(optional)*
Rune: none

magic messenger: Snow Fox (T6)

T6 archer troops (55,000x)

---

Dolly:
lv 80 (level 5 advancement), attributes allocated: +229 DES
skills: (main)sky rain arrows lv10 (lv5 relic effect), arrows volley lv10 max awakening, chain arrows lv10 max awakening
Skill stone: Magic Spear lv5

weapon: night's sword
clothes: day's robe
shorts: fanatical shorts
helmet: day's helmet
gloves: fanatical bracers
boots: night's boots
left accessory: light winged dagger
right accessory: aegis
relic: Dolly Relic lv5  *(optional)*
Rune: none

magic messenger: Snow Fox (T6)

T6 archer troops (55,000x)

---
---

## PLAYER FORMATION

Cthugha·Sp (commander):
lv 80 (level 5 advancement), attributes allocated: +229 DES
skills: (main)exploding flame lv10 (lv5 relic effect), sin judgment lv10 max awakening, fire emblem lv10 max awakening
Skill stone: Magic Spear lv5

weapon: night's sword
clothes: day's robe
shorts: fanatical shorts
helmet: day's helmet
gloves: fanatical bracers
boots: night's boots
left accessory: light winged dagger
right accessory: aegis
relic: Cthugha·Sp Relic lv5
Rune: Sin Judgment lv5

magic messenger: Snow Fox (T6)

T6 archer troops (55,000x)

---

Cthugha:
lv 80 (level 5 advancement), attributes allocated: +229 DES
skills: (main)blazing sword lv10 (lv5 relic effect), erythema imprint lv10 max awakening, flame bash lv10 max awakening
Skill stone: Magic Spear lv5

weapon: night's sword
clothes: day's robe
shorts: fanatical shorts
helmet: day's helmet
gloves: fanatical bracers
boots: night's boots
left accessory: light winged dagger
right accessory: aegis
relic: Cthugha Relic lv5
Rune: Flame Bash lv5

magic messenger: Snow Fox (T6)

T6 archer troops (55,000x)

---

Nyx:
lv 80 (level 5 advancement), attributes allocated: +229 DES
skills: (main)soul drain lv10 (lv5 relic effect), lunar guardian lv10 max awakening, wail lv10 max awakening
Skill stone: Magic Spear lv5

weapon: night's sword
clothes: day's robe
shorts: fanatical shorts
helmet: day's helmet
gloves: fanatical bracers
boots: night's boots
left accessory: light winged dagger
right accessory: aegis
relic: Nyx Relic lv5
Rune: Lunar Guardian lv5

magic messenger: Snow Fox (T6)

T6 archer troops (55,000x)   *(Nyx is Infantry by default — field her on Archer here so direct‑skill restraint stays neutral; her DoT is unaffected)*

---
---

## Notes
- The three DoT mains (Exploding Flame = Burn 1.0, Blazing Sword = Burn at a different coef, Soul Drain = Curse 0.5) are the whole point — their coefficients are printed in‑game, so the ticks become directly solvable.
- **Skill stone**: plain damage (Magic Spear) is fine; *avoid* buff/heal/resist stones so they don't alter the DoT.
- Keep **gear + messenger identical across every unit** — control.
- Second‑most‑valuable of the three (a channel we have zero data on).
