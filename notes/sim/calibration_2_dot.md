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

## Updated after Matchup 1 (baseline calibrated)
Matchup 1 pinned the **base damage + DEF curve**, so this run isolates the **DoT channel** on top
of a now‑known direct‑damage baseline. Design unchanged; notes:
- **Nicole is 4★** → she auto‑fields ~**51,000** troops (not 55,000) and a **+179** allocation cap. Expected — nothing to set; the game decides troop count by star.
- **Thiel's modular Soul Bound / Radiant Slash carry a small −15% DMG‑Dealt‑Reduced rider** (so the enemy Thiel isn't perfectly inert). Minor — ignore, or swap them for a plain "ATK N enemy" modular if you prefer.
- **Longer fights = more DoT‑tick data.** The enemy commander (Thiel) is +DEF, which already drags the fight out; if a run ends in **< 5 rounds**, re‑run with **all three enemies on +229 DEF** to force a near‑8‑round stalemate and maximize the number of Burn/Curse ticks observed.

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

Cthugha·Sp (commander):
lv 80 (level 5 advancement), attributes allocated: +229 DES
skills: (main)exploding flame lv10 (lv5 relic effect), sin judgment lv10 max awakening [Tactical, max 5★], fire emblem lv10 max awakening [Passive, max 5★]
Skill stone: Holy-light Chop lv5 [Tactical, max 5★]

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
skills: (main)blazing sword lv10 (lv5 relic effect), erythema imprint lv10 max awakening [Tactical, max 5★], flame bash lv10 max awakening [Tactical, max 5★]
Skill stone: Rift lv5 [Tactical, max 5★]

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
skills: (main)soul drain lv10 (lv5 relic effect), lunar guardian lv10 max awakening [Tactical, max 5★], wail lv10 max awakening [Passive, max 5★]
Skill stone: Purgatory Trial lv5 [Tactical, max 5★]

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
- **Skill stones must be DISTINCT within a team** (no identical stone on two heroes in the same formation) — each team uses three plain‑damage stones (Holy‑light Chop / Rift / Purgatory Trial); *avoid* buff/heal/resist stones so they don't alter the DoT.
- Keep **gear + messenger identical across every unit** — control.
- Second‑most‑valuable of the three (a channel we have zero data on).

---
---

Battle reports (match 1):

Here are both battle reports transcribed, in order (Stalemate first, then Victory).

## Battle 1 — STALEMATE

**Header**

| | Left | Right |
|---|---|---|
| Player | revela — Glorius | Customize-Enemy — Nothing |
| Level | Lv.48 | Lv.48 |
| Health bar | 4,660 / 165,000 | 2,385 / 161,000 |

**Team Totals**

| | revela (Left) | Nothing (Right) |
|---|---|---|
| Total Number Of Troops | 165,000 | 161,000 |
| Health | 4,660 | 2,385 |
| Slight Wound | 150,318 | 144,493 |
| Severe Wound | 7,315 | 10,202 |
| Death | 2,707 | 3,920 |

**Units** (all Lv.80) — Left: Cthugha·Sp ★★★★★ (55,000), Cthugha ★★★★★ (55,000), Nyx ★★★★★ (55,000). Right: Thiel ★★★★★ (55,000), Nicole ★★★★ (51,000), Dolly ★★★★★ (55,000).

**Per-Unit Stats — revela (Left)**

| Stat | Cthugha·Sp | Cthugha | Nyx |
|---|---|---|---|
| Kills | 78,872 | 24,195 | 55,548 |
| Heal | 4,691 | 3,939 | 890 |
| Slight Wound | 50,093 | 48,211 | 52,014 |
| Severe Wound | 1,168 | 4,890 | 1,257 |
| Death | 389 | 1,899 | 419 |

**Per-Unit Stats — Nothing (Right)**

| Stat | Thiel | Nicole | Dolly |
|---|---|---|---|
| Kills | 150,262 | 7,440 | 12,158 |
| Heal | 0 | 0 | 0 |
| Slight Wound | 51,351 | 44,904 | 48,238 |
| Severe Wound | 948 | 4,384 | 4,870 |
| Death | 316 | 1,712 | 1,892 |

## Battle 2 — VICTORY (胜利)

**Header**

| | Left | Right |
|---|---|---|
| Player | revela — Glorius | Customize-Enemy — Nothing |
| Level | Lv.48 | Lv.48 |
| Health bar | 4,660 / 165,000 | 0 / 161,000 |

**Team Totals**

| | revela (Left) | Nothing (Right) |
|---|---|---|
| Total Number Of Troops | 4,660 | 2,385 |
| Health | 4,660 | 0 |
| Slight Wound | 0 | 2,111 |
| Severe Wound | 0 | 4,049 |
| Death | 0 | 1,618 |

**Units** — entering troop counts (Battle-1 survivors): Cthugha·Sp 3,350, Cthugha 0 (defeated), Nyx 1,310; Thiel 2,385, Nicole 0 (defeated), Dolly 0 (defeated).

**Per-Unit Stats — revela (Left)**

| Stat | Cthugha·Sp | Cthugha | Nyx |
|---|---|---|---|
| Kills | 1,373 | 0 | 1,012 |
| Heal | 0 | 0 | 0 |
| Slight Wound | 0 | 0 | 0 |
| Severe Wound | 0 | 0 | 0 |
| Death | 0 | 0 | 0 |

**Per-Unit Stats — Nothing (Right)**

| Stat | Thiel | Nicole | Dolly |
|---|---|---|---|
| Kills | 0 | 0 | 0 |
| Heal | 0 | 0 | 0 |
| Slight Wound | 2,111 | 0 | 0 |
| Severe Wound | 4,049 | 0 | 0 |
| Death | 1,618 | 0 | 0 |

A few notes:

- **New ally roster this match** — Cthugha·Sp, Cthugha, Nyx (the enemy is still Thiel / Nicole / Dolly). No shared names across the two sides this time, so disambiguation tags won't be needed when you send the battle log.
- **Battle order confirmed.** Battle 2's entering troop counts are exactly Battle 1's survivors: ally Cthugha·Sp 3,350 / Cthugha 0 / Nyx 1,310 (= 4,660 health from the Stalemate) and enemy Thiel 2,385 / Nicole 0 / Dolly 0 (= 2,385). So only Cthugha·Sp + Nyx vs. Thiel actually fight in Battle 2, and Battle-2 kills (1,373 + 1,012 = 2,385) equal Thiel's entire entering force.
- **Stalemate figures reconcile** (each side's Slight + Severe + Death + Health = its troop total). The Right team's Battle-1 Kills (169,860) exceed the Left's non-health losses by exactly 9,520 — which equals the Left team's total Heal, i.e. troops that were healed and then killed again got counted twice.
- **One quirk in the Victory report:** the enemy's casualty breakdown (Slight 2,111 + Severe 4,049 + Death 1,618 = 7,778) is larger than Thiel's 2,385 entering troops. That's the wound-state escalation counting — as the round banner warns, slight wounds convert to severe then death, and each stage is tallied — so the categories overlap rather than partition. Transcribed as shown.

---
---

Battle log (match 1):

# Match Log — Transcription (Stalemate → Victory)

**Match:** revela (Glorius) vs. Customize-Enemy (Nothing) — both Lv.48
**Order of events:** Battle 1 = **Stalemate** (8 rounds), then Battle 2 = **Victory** (1 round).

**Legend**
- `[A]` = Ally team (revela / green ▲): **Cthugha·Sp**, **Cthugha**, **Nyx**
- `[E]` = Enemy team (Nothing / red ▲): **Thiel**, **Nicole**, **Dolly**
- The two rosters share no unit names this match, so `[A]`/`[E]` is for side-clarity only (no name collision to resolve). Tags are kept for consistency with the other transcriptions.
- Soldier counts are `(current / max)`; max declines as troops take severe wounds/deaths.
- On combined aid/skill lines, the inline `E[…]` marks the damaged unit's side. Every `Loss` line was cross-checked against running soldier counts.

---

# BATTLE 1 — STALEMATE

## Damage Statistics

**Ally (revela)**

| Unit | Normal ATK | Skill | Skills Used |
|---|---|---|---|
| Cthugha·Sp | 18,648 | 60,224 | 14 |
| Cthugha | 12,700 | 11,495 | 3 |
| Nyx | 18,037 | 37,511 | 11 |

**Enemy (Nothing)**

| Unit | Normal ATK | Skill | Skills Used |
|---|---|---|---|
| Thiel | 20,151 | 130,111 | 15 |
| Nicole | 7,440 | 0 | 0 |
| Dolly | 3,509 | 8,649 | 1 |

## Passive Exertion Round
```
[A] [Cthugha·Sp][Fire Emblem] Effective Probability: 100.00%
[A] [Nyx][Wail] Effective Probability: 100.00%
[A] [Nyx][Tactical Skill DMG Dealt Increased] 46.88%+16.00%
```

## Pre War Preparation Round
*(header only — no events logged)*

## Round 1
```
[A] [Nyx] Use [Lunar Guardian] Probability: 36.00%+14.40%
[A] [Cthugha][Shield] Effect Applied
[A] [Cthugha·Sp][Shield] Effect Applied
[A] [Cthugha] Restore 0 Soldier (55000/55000)
[A] [Cthugha·Sp] Restore 0 Soldier (55000/55000)
[A] [Nyx][Purgatory Trial] Ready Probability: 45.00%+9.00%
[A] [Nyx] Normal ATK
[E] [Dolly] Loss 4430 Soldier (50570/54114)
[A] [Cthugha][Erythema Imprint] Ready Probability: 45.00%+9.00%
[A] [Cthugha] Normal ATK
[E] [Dolly] Loss 4748 Soldier (45822/53165)
[E] [Dolly][Arrows Volley] Ready Probability: 45.00%+9.00%
[E] [Dolly] Normal ATK
[A] [Cthugha·Sp][Shield] Resisted This DMG Probability: 100.00%
[A] [Cthugha·Sp][Shield] Effect Disappeared
[A] [Cthugha·Sp] Use [Sin Judgment] Probability: 35.00%+14.00%
[E] [Nicole][Tactical Skill DMG Taken Increased] 29.06%
[E] [Dolly][Tactical Skill DMG Taken Increased] 29.06%
[A] [Cthugha·Sp] Use [Holy-light Chop] Probability: 35.00%+7.00%
[E] [Thiel] Loss 2900 Soldier (52100/54420)
[E] [Nicole] Loss 5615 Soldier (45385/49877)
[E] [Dolly] Loss 4766 Soldier (41056/52212)
[A] [Cthugha·Sp] Normal ATK
[E] [Nicole] Loss 5174 Soldier (40211/48843)
[E] [Thiel] Use [Binding Slash] Probability: 45.00%
[A] [Cthugha·Sp] Loss 2187 Soldier (52813/54563)
[A] [Cthugha][Shield] Resisted This DMG Probability: 100.00%
[A] [Cthugha][Shield] Effect Disappeared
[A] [Nyx] Loss 2211 Soldier (52789/54558)
[A] [Cthugha·Sp] Loss 2208 Soldier (50605/54122)
[A] [Cthugha] Loss 2128 Soldier (52872/54575)
[A] [Nyx] Loss 2061 Soldier (50728/54146)
[E] [Thiel] Use [Radiant Slash] Probability: 35.00%+7.00%
[A] [Cthugha] Loss 5708 Soldier (47164/53434)
[A] [Cthugha·Sp] Loss 5151 Soldier (45454/53092)
[A] [Cthugha][DMG Dealt Reduced] 9.56%
[A] [Cthugha·Sp][DMG Dealt Reduced] 9.56%
[E] [Thiel][Soul Bound] Ready Probability: 45.00%+9.00%
[E] [Thiel] Normal ATK
[A] [Cthugha] Loss 4480 Soldier (42684/52538)
[E] [Nicole] Normal ATK
[A] [Nyx] Loss 4676 Soldier (46052/53211)
```

## Round 2
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[A] [Nyx] Use [Lunar Guardian] Probability: 36.00%+14.40%
[A] [Cthugha][Shield] Effect Applied
[A] [Cthugha·Sp][Shield] Effect Applied
[A] [Cthugha] Restore 1602 Soldier (44286/51553)
[A] [Cthugha·Sp] Restore 1634 Soldier (47088/52329)
[A] [Nyx] Use [Purgatory Trial] Probability: 45.00%+9.00%
[E] [Dolly] Loss 10165 Soldier (30891/49064)
[E] [Nicole] Loss 12355 Soldier (27856/45509)
[A] [Nyx] Normal ATK
[E] [Dolly] Loss 4013 Soldier (26878/48262)
[A] [Cthugha] Use [Erythema Imprint] Probability: 45.00%+9.00%
[E] [Thiel][Tactical Skill DMG Taken Increased] 34.24%
[E] [Nicole][Tactical Skill DMG Taken Increased] Effect Updated
[E] [Dolly][Tactical Skill DMG Taken Increased] Effect Updated
[A] [Cthugha][Flame Bash] Ready Probability: 45.00%+18.00%
[A] [Cthugha] Normal ATK
[E] [Nicole] Loss 4076 Soldier (23780/44694)
[E] [Dolly] Use [Arrows Volley] Probability: 45.00%+9.00%
[A] [Cthugha·Sp][Shield] Resisted This DMG Probability: 100.00%
[A] [Cthugha·Sp][Shield] Effect Disappeared
[A] [Cthugha][Shield] Resisted This DMG Probability: 100.00%
[A] [Cthugha][Shield] Effect Disappeared
[A] [Nyx] Loss 2242 Soldier (43810/52048)
[A] [Cthugha·Sp] Loss 2176 Soldier (44912/51894)
[A] [Cthugha] Loss 2138 Soldier (42148/51126)
[A] [Nyx] Loss 2093 Soldier (41717/51630)
[E] [Dolly] Normal ATK
[A] [Cthugha] Loss 3509 Soldier (38639/50425)
[A] [Cthugha·Sp] Use [Exploding Flame] Probability: 40.00%+12.00%
[E] [Nicole][Burn] Effect Applied DMG Coefficient 1.00
[E] [Dolly][Burn] Effect Applied DMG Coefficient 1.00
[A] [Cthugha·Sp] Use [Sin Judgment] Probability: 35.00%+14.00%
[E] [Nicole][Tactical Skill DMG Taken Increased] Effect Cannot Be Replaced
[E] [Thiel][Tactical Skill DMG Taken Increased] Effect Cannot Be Replaced
[A] [Cthugha·Sp] Use [Holy-light Chop] Probability: 35.00%+7.00%
[E] [Thiel] Loss 2998 Soldier (49102/53589)
[E] [Nicole] Loss 4637 Soldier (19143/43767)
[E] [Dolly] Loss 4052 Soldier (22826/47452)
[A] [Cthugha·Sp] Normal ATK
[E] [Dolly] Loss 3585 Soldier (19241/46735)
[E] [Thiel] Use [Binding Slash] Probability: 45.00%
[A] [Cthugha·Sp] Loss 1979 Soldier (42933/51499)
[A] [Cthugha] Loss 2065 Soldier (36574/50012)
[A] [Nyx] Loss 2042 Soldier (39675/51222)
[A] [Cthugha·Sp] Loss 2123 Soldier (40810/51075)
[A] [Cthugha] Loss 2238 Soldier (34336/49565)
[A] [Nyx] Loss 1979 Soldier (37696/50827)
[A] [Cthugha·Sp] Loss 2000 Soldier (38810/50675)
[A] [Cthugha] Loss 2173 Soldier (32163/49131)
[A] [Nyx] Loss 2063 Soldier (35633/50415)
[E] [Thiel] Use [Soul Bound] Probability: 45.00%+9.00%
[A] [Cthugha] Loss 10120 Soldier (22043/47107)
[A] [Nyx] Loss 9505 Soldier (26128/48514)
[A] [Cthugha][DMG Dealt Reduced] Effect Updated
[A] [Nyx][DMG Dealt Reduced] 15.08%
[E] [Thiel] Use [Holy-light Chop] Probability: 35.00%+7.00%
[A] [Cthugha·Sp] Loss 3722 Soldier (35088/49931)
[A] [Cthugha] Loss 3662 Soldier (18381/46375)
[A] [Nyx] Loss 3725 Soldier (22403/47769)
[E] [Thiel] Normal ATK
[A] [Cthugha] Loss 4528 Soldier (13853/45470)
[A] [Cthugha·Sp][Exploding Flame][Burn] Effect Activated, E[Nicole] Loss 3982 Soldier (15161/42971)
[E] [Nicole] Normal ATK
[A] [Cthugha·Sp] Loss 2764 Soldier (32324/49379)
```

## Round 3
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[A] [Nyx] Use [Soul Drain] Probability: 40.00%+12.00%
[E] [Thiel][Curse] Effect Applied DMG Coefficient 0.50
[E] [Nicole][Curse] Effect Applied DMG Coefficient 0.50
[E] [Dolly][Curse] Effect Applied DMG Coefficient 0.50
[A] [Cthugha·Sp][Shield] Effect Applied
[A] [Cthugha][Shield] Effect Applied
[A] [Nyx][Shield] Effect Applied
[A] [Nyx] Use [Lunar Guardian] Probability: 36.00%+14.40%
[A] [Cthugha][Shield] Effect Cannot Be Replaced
[A] [Cthugha·Sp][Shield] Effect Cannot Be Replaced
[A] [Cthugha] Restore 1213 Soldier (15066/42309)
[A] [Cthugha·Sp] Restore 1109 Soldier (33433/47674)
[A] [Nyx] Normal ATK
[E] [Nicole] Loss 2775 Soldier (12386/39635)
[A] [Cthugha][Erythema Imprint] Ready Probability: 45.00%+9.00%
[A] [Cthugha] Use [Flame Bash] Probability: 45.00%+18.00%
[E] [Nicole] Loss 6844 Soldier (5542/38267)
[E] [Thiel] Loss 4651 Soldier (44451/52211)
[E] [Nicole][ATK Reduced] 63.08 (786.1)
[E] [Thiel][ATK Reduced] 63.08 (636.3)
[A] [Cthugha] Normal ATK
[E] [Dolly] Loss 1953 Soldier (17288/43596)
[A] [Cthugha·Sp][Exploding Flame][Burn] Effect Activated, E[Dolly] Loss 3660 Soldier (13628/42864)
[A] [Nyx][Soul Drain][Curse] Effect Activated, E[Dolly] Loss 1164 Soldier (12464/42632)
[E] [Dolly][Sky Rain Arrows] Ready Probability: 50.00%
[E] [Dolly][Arrows Volley] Ready Probability: 45.00%+9.00%
[E] [Dolly] Normal ATK
[A] [Cthugha·Sp][Shield] Resisted This DMG Probability: 100.00%
[A] [Cthugha·Sp][Shield] Effect Disappeared
[A] [Cthugha·Sp] Use [Exploding Flame] Probability: 40.00%+12.00%
[A] [Cthugha·Sp][Detonate] Effective
[E] [Dolly] Loss 6716 Soldier (5748/41289)
[A] [Cthugha·Sp][Detonate] Effective
[E] [Nicole] Loss 5542 Soldier (0/37159)
[E] [Nicole] Defeated
[A] [Cthugha·Sp] Use [Sin Judgment] Probability: 35.00%+14.00%
[E] [Thiel][Tactical Skill DMG Taken Increased] Effect Updated
[E] [Dolly][Tactical Skill DMG Taken Increased] Effect Updated
[A] [Cthugha·Sp] Normal ATK
[E] [Thiel] Loss 2314 Soldier (42137/51749)
[A] [Nyx][Soul Drain][Curse] Effect Activated, E[Thiel] Loss 898 Soldier (41239/51570)
[E] [Thiel] Use [Radiant Slash] Probability: 35.00%+7.00%
[A] [Cthugha][Shield] Resisted This DMG Probability: 100.00%
[A] [Cthugha][Shield] Effect Disappeared
[A] [Nyx][Shield] Resisted This DMG Probability: 100.00%
[A] [Nyx][Shield] Effect Disappeared
[A] [Cthugha][DMG Dealt Reduced] Effect Updated
[A] [Nyx][DMG Dealt Reduced] Effect Updated
[E] [Thiel][Soul Bound] Ready Probability: 45.00%+9.00%
[E] [Thiel] Use [Holy-light Chop] Probability: 35.00%+7.00%
[A] [Cthugha·Sp] Loss 2900 Soldier (30533/47094)
[A] [Cthugha] Loss 3058 Soldier (12008/41698)
[A] [Nyx] Loss 2991 Soldier (19412/44635)
[E] [Thiel] Normal ATK
[A] [Cthugha·Sp] Loss 3553 Soldier (26980/46384)
```

## Round 4
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[A] [Nyx] Use [Lunar Guardian] Probability: 36.00%+14.40%
[A] [Cthugha][Shield] Effect Applied
[A] [Cthugha·Sp][Shield] Effect Applied
[A] [Cthugha] Restore 1124 Soldier (13132/38729)
[A] [Cthugha·Sp] Restore 1135 Soldier (28115/44444)
[A] [Nyx][Purgatory Trial] Ready Probability: 45.00%+9.00%
[A] [Nyx] Normal ATK
[E] [Dolly] Loss 2383 Soldier (3365/37259)
[A] [Cthugha] Use [Erythema Imprint] Probability: 45.00%+9.00%
[E] [Thiel][Tactical Skill DMG Taken Increased] Effect Updated
[E] [Dolly][Tactical Skill DMG Taken Increased] Effect Updated
[A] [Cthugha] Normal ATK
[E] [Dolly] Loss 1923 Soldier (1442/36875)
[A] [Cthugha·Sp][Exploding Flame][Burn] Effect Activated, E[Dolly] Loss 1442 Soldier (0/36587)
[E] [Dolly] Defeated
[A] [Cthugha·Sp][DMG Dealt Reduced] Effect Disappeared
[A] [Cthugha·Sp] Normal ATK
[E] [Thiel] Loss 2324 Soldier (38915/50073)
[A] [Nyx][Soul Drain][Curse] Effect Activated, E[Thiel] Loss 898 Soldier (38017/49894)
[E] [Thiel] Use [Binding Slash] Probability: 45.00%
[A] [Cthugha·Sp][Shield] Resisted This DMG Probability: 100.00%
[A] [Cthugha·Sp][Shield] Effect Disappeared
[A] [Cthugha][Shield] Resisted This DMG Probability: 100.00%
[A] [Cthugha][Shield] Effect Disappeared
[A] [Nyx] Loss 1636 Soldier (17776/41786)
[A] [Cthugha·Sp] Loss 1654 Soldier (26461/44114)
[A] [Cthugha] Loss 1725 Soldier (11407/38384)
[A] [Nyx] Loss 1756 Soldier (16020/41435)
[E] [Thiel] Use [Soul Bound] Probability: 45.00%+9.00%
[A] [Cthugha] Loss 8283 Soldier (3124/36728)
[A] [Cthugha·Sp] Loss 7857 Soldier (18604/42543)
[A] [Cthugha][DMG Dealt Reduced] Effect Updated
[A] [Cthugha·Sp][DMG Dealt Reduced] 15.08%
[E] [Thiel] Use [Holy-light Chop] Probability: 35.00%+7.00%
[A] [Cthugha·Sp] Loss 2871 Soldier (15733/41969)
[A] [Cthugha] Loss 3124 Soldier (0/36104)
[A] [Cthugha] Defeated
[A] [Nyx] Loss 2814 Soldier (13206/40873)
[E] [Thiel] Normal ATK
[A] [Nyx] Loss 3696 Soldier (9510/40134)
```

## Round 5
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[A] [Nyx] Use [Lunar Guardian] Probability: 36.00%+14.40%
[A] [Cthugha·Sp][Shield] Effect Applied
[A] [Nyx][Shield] Effect Applied
[A] [Cthugha·Sp] Restore 813 Soldier (16546/39346)
[A] [Nyx] Restore 890 Soldier (10400/37072)
[A] [Nyx] Use [Purgatory Trial] Probability: 45.00%+9.00%
[E] [Thiel] Loss 5497 Soldier (32520/47608)
[A] [Nyx] Normal ATK
[E] [Thiel] Loss 1345 Soldier (31175/47339)
[A] [Cthugha·Sp] Use [Exploding Flame] Probability: 40.00%+12.00%
[E] [Thiel][Burn] Effect Applied DMG Coefficient 1.00
[A] [Cthugha·Sp] Use [Sin Judgment] Probability: 35.00%+14.00%
[E] [Thiel][Tactical Skill DMG Taken Increased] Effect Updated
[A] [Cthugha·Sp] Normal ATK
[E] [Thiel] Loss 1515 Soldier (29660/47036)
[E] [Thiel][Curse] Effect Disappeared
[E] [Thiel][ATK Reduced] Effect Disappeared (699.4)
[A] [Cthugha·Sp][Exploding Flame][Burn] Effect Activated, E[Thiel] Loss 1577 Soldier (28083/46721)
[E] [Thiel] Normal ATK
[A] [Cthugha·Sp][Shield] Resisted This DMG Probability: 100.00%
[A] [Cthugha·Sp][Shield] Effect Disappeared
```

## Round 6
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[A] [Nyx][DMG Dealt Reduced] Effect Disappeared
[A] [Nyx] Use [Soul Drain] Probability: 40.00%+12.00%
[E] [Thiel][Curse] Effect Applied DMG Coefficient 0.50
[A] [Cthugha·Sp][Shield] Effect Applied
[A] [Nyx][Shield] Effect Updated
[A] [Nyx][Purgatory Trial] Ready Probability: 45.00%+9.00%
[A] [Nyx] Normal ATK
[E] [Thiel] Loss 1502 Soldier (26581/44558)
[A] [Cthugha·Sp] Use [Exploding Flame] Probability: 40.00%+12.00%
[A] [Cthugha·Sp][Detonate] Effective
[E] [Thiel] Loss 3129 Soldier (23452/43933)
[A] [Cthugha·Sp] Use [Holy-light Chop] Probability: 35.00%+7.00%
[E] [Thiel] Loss 1646 Soldier (21806/43604)
[A] [Cthugha·Sp] Normal ATK
[E] [Thiel] Loss 1530 Soldier (20276/43298)
[A] [Cthugha·Sp][Exploding Flame][Burn] Effect Activated, E[Thiel] Loss 1577 Soldier (18699/42983)
[A] [Nyx][Soul Drain][Curse] Effect Activated, E[Thiel] Loss 708 Soldier (17991/42842)
[E] [Thiel] Use [Binding Slash] Probability: 45.00%
[A] [Cthugha·Sp][Shield] Resisted This DMG Probability: 100.00%
[A] [Cthugha·Sp][Shield] Effect Disappeared
[A] [Nyx][Shield] Resisted This DMG Probability: 100.00%
[A] [Nyx][Shield] Effect Disappeared
[A] [Cthugha·Sp] Loss 1225 Soldier (15321/36821)
[A] [Nyx] Loss 1212 Soldier (9188/34163)
[E] [Thiel][Soul Bound] Ready Probability: 45.00%+9.00%
[E] [Thiel] Use [Holy-light Chop] Probability: 35.00%+7.00%
[A] [Cthugha·Sp] Loss 2256 Soldier (13065/36370)
[A] [Nyx] Loss 2193 Soldier (6995/33725)
[E] [Thiel] Normal ATK
[A] [Cthugha·Sp] Loss 2579 Soldier (10486/35855)
```

## Round 7
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[A] [Nyx] Use [Purgatory Trial] Probability: 45.00%+9.00%
[E] [Thiel] Loss 4903 Soldier (13088/39377)
[A] [Nyx] Normal ATK
[E] [Thiel] Loss 1128 Soldier (11960/39152)
[A] [Cthugha·Sp][DMG Dealt Reduced] Effect Disappeared
[A] [Cthugha·Sp][Fire Emblem] Effect Triggered Probability: 40.00%
[A] [Cthugha·Sp][Tactical Skill DMG Dealt Increased] 50.28%+20.00%
[A] [Cthugha·Sp] Use [Exploding Flame] Probability: 40.00%+12.00%
[A] [Cthugha·Sp][Detonate] Effective
[E] [Thiel] Loss 5311 Soldier (6649/38090)
[A] [Cthugha·Sp] Use [Sin Judgment] Probability: 35.00%+14.00%
[E] [Thiel][Tactical Skill DMG Taken Increased] Effect Updated
[A] [Cthugha·Sp] Normal ATK
[E] [Thiel] Loss 1525 Soldier (5124/37785)
[E] [Thiel][Burn] Effect Disappeared
[A] [Nyx][Soul Drain][Curse] Effect Activated, E[Thiel] Loss 708 Soldier (4416/37644)
[E] [Thiel] Use [Binding Slash] Probability: 45.00%
[A] [Cthugha·Sp] Loss 592 Soldier (9894/33201)
[A] [Nyx] Loss 599 Soldier (6396/30933)
[A] [Cthugha·Sp] Loss 655 Soldier (9239/33070)
[A] [Nyx] Loss 599 Soldier (5797/30814)
[E] [Thiel] Use [Radiant Slash] Probability: 35.00%+7.00%
[A] [Cthugha·Sp] Loss 1577 Soldier (7662/32755)
[A] [Nyx] Loss 1609 Soldier (4188/30493)
[A] [Cthugha·Sp][DMG Dealt Reduced] 9.56%
[A] [Nyx][DMG Dealt Reduced] 9.56%
[E] [Thiel] Use [Soul Bound] Probability: 45.00%+9.00%
[A] [Cthugha·Sp] Loss 2997 Soldier (4665/32156)
[A] [Nyx] Loss 2878 Soldier (1310/29918)
[A] [Cthugha·Sp][DMG Dealt Reduced] Effect Updated
[A] [Nyx][DMG Dealt Reduced] Effect Updated
[E] [Thiel] Normal ATK
[A] [Cthugha·Sp] Loss 1315 Soldier (3350/31893)
```

## Round 8
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[A] [Nyx] Use [Soul Drain] Probability: 40.00%+12.00%
[E] [Thiel][Curse] Effect Updated
[A] [Cthugha·Sp][Shield] Effect Applied
[A] [Nyx][Shield] Effect Applied
[A] [Nyx] Normal ATK
[E] [Thiel] Loss 461 Soldier (3955/34230)
[A] [Cthugha·Sp] Use [Exploding Flame] Probability: 40.00%+12.00%
[E] [Thiel][Burn] Effect Applied DMG Coefficient 1.00
[A] [Cthugha·Sp] Normal ATK
[E] [Thiel] Loss 681 Soldier (3274/34094)
[A] [Nyx][Soul Drain][Curse] Effect Activated, E[Thiel] Loss 215 Soldier (3059/34051)
[A] [Cthugha·Sp][Exploding Flame][Burn] Effect Activated, E[Thiel] Loss 674 Soldier (2385/33917)
[E] [Thiel][Soul Bound] Ready Probability: 45.00%+9.00%
[E] [Thiel] Normal ATK
[A] [Cthugha·Sp][Shield] Resisted This DMG Probability: 100.00%
[A] [Cthugha·Sp][Shield] Effect Disappeared
```
*(The screenshots end mid–Round 8 here; Round 8 was the final round and the battle concluded as a Stalemate when the round limit was reached.)*

**>>> BATTLE 1 RESULT: STALEMATE.** Survivors entering Battle 2 — Ally: Cthugha·Sp 3,350, Cthugha 0 (defeated), Nyx 1,310. Enemy: Thiel 2,385, Nicole 0 (defeated), Dolly 0 (defeated).

---

# BATTLE 2 — VICTORY

> Carry-over buff: **Stalemate-1, All Hero DMG Dealt Increased 33.00%**

## Damage Statistics

**Ally (revela)**

| Unit | Normal ATK | Skill | Skills Used |
|---|---|---|---|
| Cthugha·Sp | 1,146 | 227 | 2 |
| Cthugha | 0 | 0 | 0 |
| Nyx | 668 | 344 | 1 |

**Enemy (Nothing)**

| Unit | Normal ATK | Skill | Skills Used |
|---|---|---|---|
| Thiel | 0 | 0 | 0 |
| Nicole | 0 | 0 | 0 |
| Dolly | 0 | 0 | 0 |

## Passive Exertion Round
```
[A] [Cthugha·Sp][Fire Emblem] Effective Probability: 100.00%
[A] [Nyx][Wail] Effective Probability: 100.00%
[A] [Nyx][Tactical Skill DMG Dealt Increased] 46.88%+16.00%
```

## Pre War Preparation Round
*(header only — no events logged)*

## Round 1
```
[A] [Nyx] Use [Soul Drain] Probability: 40.00%+12.00%
[E] [Thiel][Curse] Effect Applied DMG Coefficient 0.50
[A] [Cthugha·Sp][Shield] Effect Applied
[A] [Nyx][Shield] Effect Applied
[A] [Nyx][Purgatory Trial] Ready Probability: 45.00%+9.00%
[A] [Nyx] Normal ATK
[E] [Thiel] Loss 668 Soldier (1717/2252)
[A] [Cthugha·Sp] Use [Exploding Flame] Probability: 40.00%+12.00%
[E] [Thiel][Burn] Effect Applied DMG Coefficient 1.00
[A] [Cthugha·Sp] Use [Sin Judgment] Probability: 35.00%+14.00%
[E] [Thiel][Tactical Skill DMG Taken Increased] 29.06%
[A] [Cthugha·Sp] Normal ATK
[E] [Thiel] Loss 1146 Soldier (571/2023)
[A] [Nyx][Soul Drain][Curse] Effect Activated, E[Thiel] Loss 344 Soldier (227/1955)
[A] [Cthugha·Sp][Exploding Flame][Burn] Effect Activated, E[Thiel] Loss 227 Soldier (0/1910)
[E] [Thiel] Defeated
```

**>>> BATTLE 2 RESULT: VICTORY.** All enemy units defeated (Thiel's 2,385 entering troops wiped; Cthugha·Sp + Nyx took no losses).

---

## Transcription notes
1. **No shared unit names** this match (ally Cthugha·Sp / Cthugha / Nyx vs. enemy Thiel / Nicole / Dolly), so `[A]`/`[E]` tags mark side for readability only — there is no Rhea-style ambiguity to resolve.
2. **All side tags are count-verified.** Every `Loss (current/max)` reconciles against the running per-unit totals (e.g., ally Cthugha·Sp's final stalemate value 3,350 and enemy Thiel's 2,385 both fall out of the arithmetic and match the Battle-2 entering counts and the report screenshots).
3. **Battle order confirmed.** Battle 2 opens with the **Stalemate-1** buff and its entering troops equal Battle 1's survivors; Battle-2 kills (Cthugha·Sp 1,373 + Nyx 1,012 = 2,385) equal Thiel's entire entering force.
4. **`[Burn]` / `[Soul Drain][Curse]` / `[Detonate]` follow-up hits** are logged as "Effect Activated, [target] Loss …" lines; the target's side is tagged inline (always the enemy in this match).
5. **Round-start flavour text** ("On the battlefield, soldiers' injuries gradually worsen…") appears on Rounds 2–8 of Battle 1, matching the game.
6. **Passive Exertion Round** and **Pre War Preparation Round** were shown as headers with no events beneath them (in both battles); reproduced as such.
7. **Battle 1's screenshots end mid–Round 8**, right after an enemy Thiel attack was fully resisted by ally shields (no further troop changes). Round 8 was the final round; the match resolved as a Stalemate at the round limit, with the survivor counts noted above.


---
---

all matches (matches 1 through 10):
match 1: stalemate, victory
match 2: victory
match 3: victory
match 4: victory
match 5: loss
match 6: loss
match 7: victory
match 8: loss
match 9: loss
match 10: victory

60% win rate (keep in mind that this is a small sample)