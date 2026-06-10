# Calibration Matchup 3 — "Pursuit & Throughput" (the attack‑volume problem)

*Scenario 3 of 3. See also: `calibration_1_baseline.md`, `calibration_2_dot.md`.*

**Purpose.** Our biggest error so far (the bout‑count gap) came from **under‑counting how many
times a unit attacks per round**. This matchup measures pursuit damage **and** multi‑hit/proc
volume directly. **SusaMaki's Flash Fire is pure pursuit with a built‑in 45% chance to fire a
*second* pursuit** — a clean read of both the pursuit‑channel coefficient and a proc rate.
**Niya** adds Assault‑style pursuit (cross‑checks the ~726 flat Real‑DMG we already have) plus a
high relic trigger (+22.8%). **Mia's Divine Punish** adds a "chance on normal attack" combo proc.
Together they generate many `Use [Skill] Probability` / `Effect Triggered Probability` lines to
tally. Enemy is the plain trio (no shield) so per‑hit damage and proc counts are easy to read.

**Calibrates:** pursuit‑channel damage, the per‑round **number** of attacks/procs (the throughput
that drives bout count), proc trigger rates (the 45% double‑pursuit is the cleanest), and a
second Assault data point.

## Setup (applies to all units)
Every hero is **Lv 80, advancement 5, 55,000 troops**, same gear set (control; mixed = no set
bonus). Names verified against the game data.

## Updated after Matchup 1 (baseline calibrated)
Matchup 1 pinned the **base damage + DEF curve**, so this run isolates the **pursuit channel +
attack/proc volume** on top of a now‑known direct‑damage baseline. Design unchanged; notes:
- **Nicole is 4★** → she auto‑fields ~**51,000** troops (not 55,000) and a **+179** allocation cap. Expected — the game sets troop count by star.
- **Thiel's modular Soul Bound / Radiant Slash carry a small −15% DMG‑Dealt‑Reduced rider** (enemy Thiel isn't perfectly inert). Minor — ignore, or swap them for a plain "ATK N enemy" modular.
- **Longer fights = more pursuit/proc data.** The enemy commander (Thiel) is +DEF, which already drags the fight out; if a run ends in **< 5 rounds**, re‑run with **all three enemies on +229 DEF** to force a near‑8‑round stalemate and maximize the number of pursuit/double‑pursuit/combo procs observed.

## What to record (priority order)
1. **Every `Use [Skill]` / `Effect Triggered Probability` / pursuit line, per round** — so I can count attacks/procs per unit per round (the throughput read).
2. All `Loss N Soldier (current/max)` damage lines, actor → target (separate normal vs pursuit vs Assault hits).
3. **In‑battle `(NNN)` attribute values** (esp. ATK and Spd of the pursuit users).
4. End‑of‑battle per‑unit troop counts + team Health/Slight/Severe/Death summary.

---
---

## ENEMY FORMATION  *(clean 4★/5★ damage dummies — no shields, varied DEF)*

Thiel (commander):
lv 80 (level 5 advancement), attributes allocated: +229 DEF
skills: (main)binding slash lv10 (lv5 relic effect), radiant slash lv10 max awakening [Tactical, max 5★], soul bound lv10 max awakening [Tactical, max 5★]
Skill stone: Holy-light Chop lv5 [Tactical, max 5★]

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
lv 80 (level 5 advancement), attributes allocated: +179 ATK   *(4★ cap is +179, not +229)*
skills: (main)fly flowers lv10 (lv5 relic effect), rose sword lv10 max awakening [Tactical, max 4★], rose blade lv10 max awakening [Tactical, max 4★]
Skill stone: Rift lv5 [Tactical, max 5★]

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
skills: (main)sky rain arrows lv10 (lv5 relic effect), arrows volley lv10 max awakening [Tactical, max 5★], chain arrows lv10 max awakening [Tactical, max 5★]
Skill stone: Purgatory Trial lv5 [Tactical, max 5★]

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

SusaMaki (commander):
lv 80 (level 5 advancement), attributes allocated: +229 ATK
skills: (main)flash fire lv10 (lv5 relic effect), white blade lv10 max awakening [Pursuit, max 5★], witcher lv10 max awakening [Passive, max 5★]
Skill stone: Holy-light Chop lv5 [Tactical, max 5★]

weapon: night's sword
clothes: day's robe
shorts: fanatical shorts
helmet: day's helmet
gloves: fanatical bracers
boots: night's boots
left accessory: light winged dagger
right accessory: aegis
relic: SusaMaki Relic lv5
Rune: White Blade lv5

magic messenger: Snow Fox (T6)

T6 archer troops (55,000x)

---

Niya:
lv 80 (level 5 advancement), attributes allocated: +229 ATK
skills: (main)slayer lv10 (lv5 relic effect), chain reaction lv10 max awakening [Pursuit, max 5★], trio lv10 max awakening [Pursuit, max 5★]
Skill stone: Rift lv5 [Tactical, max 5★]

weapon: night's sword
clothes: day's robe
shorts: fanatical shorts
helmet: day's helmet
gloves: fanatical bracers
boots: night's boots
left accessory: light winged dagger
right accessory: aegis
relic: Niya Relic lv5
Rune: Chain Reaction lv5

magic messenger: Snow Fox (T6)

T6 archer troops (55,000x)

---

Mia:
lv 80 (level 5 advancement), attributes allocated: +229 ATK
skills: (main)divine punish lv10 (lv5 relic effect), hayate blade lv10 max awakening [Passive, max 5★], force majeure lv10 max awakening [Tactical, max 5★]
Skill stone: Purgatory Trial lv5 [Tactical, max 5★]

weapon: night's sword
clothes: day's robe
shorts: fanatical shorts
helmet: day's helmet
gloves: fanatical bracers
boots: night's boots
left accessory: light winged dagger
right accessory: aegis
relic: Mia Relic lv5
Rune: Force Majeure lv5

magic messenger: Snow Fox (T6)

T6 archer troops (55,000x)

---
---

## Notes
- **SusaMaki's Flash Fire** is the key read (pure pursuit + its 45% second‑pursuit proc). Niya cross‑checks Assault; Mia adds a combo‑on‑normal proc.
- **Skill stones must be DISTINCT within a team** (no identical stone on two heroes in the same formation) — each team uses three plain‑damage stones (Holy‑light Chop / Rift / Purgatory Trial); avoid buff/heal/shield stones.
- Keep **gear + messenger identical across every unit** — control.
- Third priority of the three, but it targets the exact throughput error that caused our bout‑count miss.
