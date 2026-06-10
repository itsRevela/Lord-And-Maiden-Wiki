# Calibration Matchup 1 — "Vanilla Baseline" (the damage formula itself)

*Scenario 1 of 3. See also: `calibration_2_dot.md`, `calibration_3_pursuit.md`.*
*(All heroes are 4★/5★ — practice mode only allows 4★/5★ selection.)*

**Purpose.** Pin the raw damage equation with **zero shields / heals / control / attribute
buffs**. The trio use **pure "Launch N ATK" damage skills with no riders** (Binding Slash,
Fly Flowers, Sky Rain Arrows), so almost the only things happening are normal attacks + clean
multi‑hit damage. The enemy trio each allocate a **different** stat (DEF / ATK / Ruin) → three
effective DEF values → we trace the **DEF‑mitigation curve in one log**. Both sides field
**Archer** troops so **restraint is neutral** (no ×0.75 muddying the read). Because every main
hits 3 enemies, each cast gives a damage reading on all three DEF levels at once.

**Calibrates:** `damage_global`, `def_ref` (mitigation curve), how ATK→damage, how troop count
scales damage, and (bonus) the 20/40/40 targeting split — watch which enemy the normals hit.

> **Restraint add‑on (high value, optional):** re‑run this exact matchup with the **player team
> on Cavalry** (enemy stays Archer). Archer restrains Cavalry, so the player becomes the
> *restrained* side — comparing the player's output to this Archer baseline (I'll account for
> the known Cavalry‑vs‑Archer soldier stats) isolates the **−25% restraint multiplier**. A third
> run of **player Infantry vs enemy Archer** (player *favored*) confirms the favored side gets no
> bonus. Restraint drives every troop‑type recommendation the optimizer makes.

## Setup (applies to all units)
Every hero is **Lv 80, advancement 5, 55,000 troops**, same gear set (a *control* — mixed pieces
= no set bonus, intentional). All names verified against the game data. These heroes have no
disruptive effects, so their relics (which only raise the damage skill's trigger) are harmless;
keep them, or leave relic/rune **empty** for an even barer baseline — your call.

## What to record (priority order)
1. **Per‑round damage lines** — every `Loss N Soldier (current/max)`, tagged actor → target.
2. **In‑battle `(NNN)` attribute values** — the parenthetical numbers after attribute lines.
3. **End‑of‑battle per‑unit troop counts** + the team Health/Slight/Severe/Death summary.
4. The full round log (Passive Exertion + Pre‑War Prep + each round) if feasible.

If short on time, the most valuable subset is **end‑of‑Battle‑1 per‑unit troop counts + any `(NNN)` stats**.

---
---

## ENEMY FORMATION

Thiel (commander):
lv 80 (level 5 advancement), attributes allocated: +229 DEF
skills: (main)binding slash lv10 (lv5 relic effect), radiant slash lv10 max awakening, soul bound lv10 max awakening
Skill stone: Magic Spear lv5  *(plain damage stone — do NOT use a buff stone here)*

weapon: night's sword
clothes: day's robe
shorts: fanatical shorts
helmet: day's helmet
gloves: fanatical bracers
boots: night's boots
left accessory: light winged dagger
right accessory: aegis
relic: Thiel Relic lv5  *(optional — only boosts the damage skill's trigger)*
Rune: none

magic messenger: Snow Fox (T6)

T6 archer troops (55,000x)

---

Nicole:
lv 80 (level 5 advancement), attributes allocated: +179 ATK   *(4★ cap is +179, not +229)*
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

Thiel (commander):
lv 80 (level 5 advancement), attributes allocated: +229 ATK
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
lv 80 (level 5 advancement), attributes allocated: +179 ATK   *(4★ cap is +179, not +229)*
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
lv 80 (level 5 advancement), attributes allocated: +229 ATK
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

## Notes
- **Why these heroes:** their main skills are pure **"Launch N ATK"** (Binding Slash 2‑3 hits / Fly Flowers 1‑3 / Sky Rain Arrows 3‑5) on 3 enemies — no debuff/buff/control riders, so every hit is a clean damage reading on all three DEF levels.
- **Skill stone** is secondary. Magic Spear is a plain damage stone; if 3× the same stone is blocked by team stone‑rules, swap any **plain damage** stone and tell me which — *avoid buff/heal/shield stones* (Elf Deer, Field Therapy, Reactive Block).
- **Modular skills** are the heroes' own defaults; any plain "ATK N enemy" skill is a fine substitute.
- Keep **gear + messenger identical across every unit** — it's the control (these exact pieces appeared in your first log).
- This is the highest‑value of the three: it re‑grounds the entire damage equation, currently fit only to one shielded‑tank fight.
