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

---
---

battle report:

Here's the transcription.

**Result: 胜利 (Victory)**

**Header**

| | Left | Right |
|---|---|---|
| Player | revela — Glorius | Customize-Enemy — Nothing |
| Level | Lv.48 | Lv.48 |
| Health bar | 34,741 / 165,000 | 55 / 161,000 |

**Team Totals**

| | revela (Left) | Nothing (Right) |
|---|---|---|
| Total Number Of Troops | 165,000 | 161,000 |
| Health | 34,741 | 55 |
| Slight Wound | 121,887 | 146,664 |
| Severe Wound | 6,077 | 10,308 |
| Death | 2,295 | 3,973 |

**Units** (all Lv.80, ★★★★★) — Left: SusaMaki (55,000), Niya (55,000), Mia (55,000). Right: Thiel (55,000), Nicole ★★★★ (51,000), Dolly (55,000).

**Per-Unit Stats — revela (Left)**

| Stat | SusaMaki | Niya | Mia |
|---|---|---|---|
| Kills | 60,241 | 65,355 | 35,349 |
| Heal | 0 | 0 | 0 |
| Slight Wound | 33,261 | 40,320 | 48,306 |
| Severe Wound | 587 | 672 | 4,818 |
| Death | 195 | 224 | 1,876 |

**Per-Unit Stats — Nothing (Right)**

| Stat | Thiel | Nicole | Dolly |
|---|---|---|---|
| Kills | 30,845 | 59,382 | 40,032 |
| Heal | 0 | 0 | 0 |
| Slight Wound | 48,132 | 50,063 | 48,469 |
| Severe Wound | 4,950 | 662 | 4,696 |
| Death | 1,918 | 220 | 1,835 |

Notes:

- **New ally roster** — SusaMaki, Niya, Mia (enemy still Thiel / Nicole / Dolly). No shared names across sides.
- All figures reconcile: each side's Slight + Severe + Death + Health equals its troop total, and each team's total Kills equals the opponent's non-health losses (revela 160,945; Nothing 130,259), consistent with 0 healing on both sides.
- It was a narrow win — the enemy finished with just 55 troops left (Nicole's survivors; Thiel and Dolly both fully wiped). On revela's side, SusaMaki ended at 20,957 and Niya at 13,784, with Mia wiped out.

---
---

battle log:

# Match Log — Transcription (Victory)

**Match:** revela (Glorius) vs. Customize-Enemy (Nothing) — both Lv.48
**Result:** VICTORY (revela win) — single battle, 4 rounds.

**Legend**
- `[A]` = Ally team (revela / green ▲): **SusaMaki**, **Niya**, **Mia**
- `[E]` = Enemy team (Nothing / red ▲): **Thiel**, **Nicole**, **Dolly**
- No shared unit names this match, so `[A]`/`[E]` marks side for readability only (no name collision to resolve). Kept for consistency with the other transcriptions.
- Soldier counts are `(current / max)`; max declines as troops take severe wounds/deaths.
- On combined skill/follow-up lines, the inline `E[…]` marks the damaged unit's side. Every `Loss` line was cross-checked against running soldier counts.

---

## Damage Statistics

**Ally (revela)**

| Unit | Normal ATK | Skill | Skills Used |
|---|---|---|---|
| SusaMaki | 17,746 | 42,495 | 6 |
| Niya | 12,218 | 53,137 | 12 |
| Mia | 22,362 | 12,987 | 2 |

**Enemy (Nothing)**

| Unit | Normal ATK | Skill | Skills Used |
|---|---|---|---|
| Thiel | 5,627 | 25,218 | 4 |
| Nicole | 11,840 | 47,542 | 5 |
| Dolly | 7,345 | 32,687 | 3 |

## Passive Exertion Round
```
[A] [SusaMaki][Witcher] Effective Probability: 100.00%
[A] [Mia][Divine Punish] Effective Probability: 100.00%
[A] [Mia][ATK Attribute Increased] 49.79 (989.1)
[A] [Mia][Hayate Blade] Effective Probability: 100.00%
[A] [Mia][Combo] Effect Cannot Be Replaced
```

## Pre War Preparation Round
*(header only — no events logged)*

## Round 1
```
[A] [SusaMaki] Normal ATK
[E] [Dolly] Loss 5441 Soldier (49559/53912)
[A] [Niya] Use [Rift] Probability: 30.00%+6.00%
[E] [Thiel] Loss 1541 Soldier (53459/54692)
[E] [Thiel] Loss 1604 Soldier (51855/54372)
[E] [Thiel] Loss 1604 Soldier (50251/54052)
[E] [Thiel] Loss 1557 Soldier (48694/53741)
[A] [Niya] Normal ATK
[E] [Thiel] Loss 4404 Soldier (44290/52861)
[A] [Niya] Use [Slayer] Probability: 76.00%+22.80%
[A] [Niya][Assault] Effect Applied Real DMG Base 32.29
[E] [Thiel] Loss 4782 Soldier (39508/51905)
[A] [Niya][Slayer][Assault] Effect Activated, E[Thiel] Loss 757 Soldier (38751/51754)
[A] [Niya] Use [Chain Reaction] Probability: 40.00%+16.00%
[E] [Thiel] Loss 5180 Soldier (33571/50718)
[A] [Niya][Slayer][Assault] Effect Activated, E[Thiel] Loss 757 Soldier (32814/50567)
[A] [Mia][Purgatory Trial] Ready Probability: 45.00%+9.00%
[A] [Mia] Normal ATK
[E] [Nicole] Loss 6457 Soldier (44543/49709)
[A] [Mia][Divine Punish] Effect Triggered Probability: 76.00%+22.80%
[A] [Mia] Trigger [Combo]
[E] [Nicole] Loss 6259 Soldier (38284/48458)
[E] [Dolly] Use [Chain Arrows] Probability: 35.00%+7.00%
[A] [Mia] Loss 6328 Soldier (48672/53735)
[A] [Niya] Loss 6579 Soldier (48421/53685)
[E] [Dolly][Purgatory Trial] Ready Probability: 45.00%+9.00%
[E] [Dolly] Normal ATK
[A] [Niya] Loss 4588 Soldier (43833/52768)
[E] [Thiel] Use [Binding Slash] Probability: 45.00%
[A] [SusaMaki] Loss 1802 Soldier (53198/54640)
[A] [Niya] Loss 1815 Soldier (42018/52405)
[A] [Mia] Loss 1645 Soldier (47027/53406)
[A] [SusaMaki] Loss 1663 Soldier (51535/54308)
[A] [Niya] Loss 1780 Soldier (40238/52049)
[A] [Mia] Loss 1645 Soldier (45382/53077)
[E] [Thiel] Use [Radiant Slash] Probability: 35.00%+7.00%
[A] [Mia] Loss 4365 Soldier (41017/52204)
[A] [SusaMaki] Loss 4506 Soldier (47029/53407)
[A] [Mia][DMG Dealt Reduced] 9.56%
[A] [SusaMaki][DMG Dealt Reduced] 9.56%
[E] [Thiel] Normal ATK
[A] [Mia] Loss 3638 Soldier (37379/51477)
[E] [Nicole] Use [Rose Blade] Probability: 35.00%+5.60%
[A] [SusaMaki] Loss 5103 Soldier (41926/52387)
[A] [Mia] Loss 4993 Soldier (32386/50479)
[E] [Nicole] Use [Rift] Probability: 30.00%+6.00%
[A] [Mia] Loss 1669 Soldier (30717/50146)
[A] [Mia] Loss 1603 Soldier (29114/49826)
[A] [Mia] Loss 1702 Soldier (27412/49486)
[A] [Mia] Loss 1603 Soldier (25809/49166)
[E] [Nicole] Normal ATK
[A] [SusaMaki] Loss 4594 Soldier (37332/51469)
```

## Round 2
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[A] [SusaMaki] Normal ATK
[E] [Dolly] Loss 4056 Soldier (45503/52666)
[A] [SusaMaki] Use [Flash Fire] Probability: 45.00%+13.50%
[E] [Dolly] Loss 6238 Soldier (39265/51419)
[A] [SusaMaki] Use [White Blade] Probability: 40.00%+16.00%
[E] [Dolly] Loss 7063 Soldier (32202/50007)
[A] [Niya][Assault] Effect Disappeared
[A] [Niya] Normal ATK
[E] [Thiel] Loss 3732 Soldier (29082/48046)
[A] [Niya] Use [Slayer] Probability: 76.00%+22.80%
[A] [Niya][Assault] Effect Applied Real DMG Base 32.29
[E] [Thiel] Loss 4349 Soldier (24733/47177)
[A] [Niya][Slayer][Assault] Effect Activated, E[Thiel] Loss 648 Soldier (24085/47048)
[A] [Niya] Use [Chain Reaction] Probability: 40.00%+16.00%
[E] [Thiel] Loss 4478 Soldier (19607/46153)
[A] [Niya][Slayer][Assault] Effect Activated, E[Thiel] Loss 648 Soldier (18959/46024)
[A] [Niya] Use [Trio] Probability: 40.00%+8.00%
[E] [Thiel] Loss 3481 Soldier (15478/45328)
[A] [Niya][Slayer][Assault] Effect Activated, E[Thiel] Loss 648 Soldier (14830/45199)
[A] [Niya] Use [Trio] Probability: 35.00%
[E] [Thiel] Loss 1566 Soldier (13264/44886)
[A] [Niya][Slayer][Assault] Effect Activated, E[Thiel] Loss 648 Soldier (12616/44757)
[A] [Mia] Use [Purgatory Trial] Probability: 45.00%+9.00%
[E] [Dolly] Loss 7749 Soldier (24453/48458)
[E] [Thiel] Loss 5238 Soldier (7378/43710)
[A] [Mia] Normal ATK
[E] [Dolly] Loss 3567 Soldier (20886/47745)
[A] [Mia][Divine Punish] Effect Triggered Probability: 76.00%+22.80%
[A] [Mia] Trigger [Combo]
[E] [Thiel] Loss 2695 Soldier (4683/43171)
[E] [Dolly][Arrows Volley] Ready Probability: 45.00%+9.00%
[E] [Dolly] Use [Chain Arrows] Probability: 35.00%+7.00%
[A] [Niya] Loss 4236 Soldier (36002/50021)
[A] [Mia] Loss 3874 Soldier (21935/46057)
[E] [Dolly] Use [Purgatory Trial] Probability: 45.00%+9.00%
[A] [Mia] Loss 5866 Soldier (16069/44884)
[A] [Niya] Loss 5804 Soldier (30198/48861)
[E] [Dolly] Normal ATK
[A] [SusaMaki] Loss 2757 Soldier (34575/49505)
[E] [Thiel] Use [Holy-light Chop] Probability: 35.00%+7.00%
[A] [SusaMaki] Loss 1169 Soldier (33406/49272)
[A] [Niya] Loss 1109 Soldier (29089/48640)
[A] [Mia] Loss 1122 Soldier (14947/44660)
[E] [Thiel] Normal ATK
[A] [Niya] Loss 1428 Soldier (27661/48355)
[E] [Nicole] Use [Fly Flowers] Probability: 35.00%
[A] [SusaMaki] Loss 2139 Soldier (31267/48845)
[A] [Niya] Loss 2222 Soldier (25439/47911)
[A] [Mia] Loss 2009 Soldier (12938/44259)
[A] [SusaMaki] Loss 2117 Soldier (29150/48422)
[A] [Niya] Loss 2222 Soldier (23217/47467)
[A] [Mia] Loss 2199 Soldier (10739/43820)
[A] [SusaMaki] Loss 2248 Soldier (26902/47973)
[A] [Niya] Loss 2288 Soldier (20929/47010)
[A] [Mia] Loss 2030 Soldier (8709/43414)
[E] [Nicole] Use [Rift] Probability: 30.00%+6.00%
[A] [SusaMaki] Loss 1619 Soldier (25283/47650)
[A] [SusaMaki] Loss 1670 Soldier (23613/47316)
[A] [SusaMaki] Loss 1773 Soldier (21840/46962)
[E] [Nicole] Normal ATK
[A] [Mia] Loss 4319 Soldier (4390/42551)
```

## Round 3
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[A] [SusaMaki][Witcher] Effect Triggered Probability: 40.00%
[A] [SusaMaki][Pursuit Skill DMG Dealt Increased] 56.29%+20.00%
[A] [SusaMaki] Normal ATK
[E] [Dolly] Loss 3363 Soldier (17523/44388)
[A] [SusaMaki] Use [Flash Fire] Probability: 45.00%+13.50%
[E] [Dolly] Loss 7689 Soldier (9834/42851)
[A] [SusaMaki] Use [White Blade] Probability: 40.00%+16.00%
[E] [Dolly] Loss 9731 Soldier (103/40905)
[A] [Niya][Assault] Effect Disappeared
[A] [Niya] Use [Rift] Probability: 30.00%+6.00%
[E] [Thiel] Loss 980 Soldier (3703/39127)
[E] [Thiel] Loss 941 Soldier (2762/38939)
[E] [Thiel] Loss 980 Soldier (1782/38743)
[E] [Thiel] Loss 941 Soldier (841/38555)
[A] [Niya] Normal ATK
[E] [Nicole] Loss 4082 Soldier (34202/45710)
[A] [Niya] Use [Slayer] Probability: 76.00%+22.80%
[A] [Niya][Assault] Effect Applied Real DMG Base 32.29
[E] [Nicole] Loss 4525 Soldier (29677/44805)
[A] [Niya][Slayer][Assault] Effect Activated, E[Nicole] Loss 468 Soldier (29209/44712)
[A] [Niya] Use [Chain Reaction] Probability: 40.00%+16.00%
[E] [Nicole] Loss 5205 Soldier (24004/43671)
[A] [Niya][Slayer][Assault] Effect Activated, E[Nicole] Loss 468 Soldier (23536/43578)
[A] [Niya] Use [Chain Reaction] Probability: 40.00%
[E] [Dolly] Loss 103 Soldier (0/40885)
[E] [Dolly] Defeated
[A] [Niya] Use [Trio] Probability: 40.00%+8.00%
[E] [Nicole] Loss 3810 Soldier (19726/42816)
[A] [Niya][Slayer][Assault] Effect Activated, E[Nicole] Loss 468 Soldier (19258/42723)
[A] [Mia] Use [Force Majeure] Probability: 35.00%+14.00%
[A] [Niya][Combo] Effect Applied
[A] [SusaMaki][Combo] Effect Applied
[A] [Mia][Purgatory Trial] Ready Probability: 45.00%+9.00%
[A] [Mia] Normal ATK
[E] [Nicole] Loss 1718 Soldier (17540/42380)
[A] [Mia][Divine Punish] Effect Triggered Probability: 76.00%+22.80%
[A] [Mia] Trigger [Combo]
[E] [Nicole] Loss 1666 Soldier (15874/42047)
[E] [Thiel] Use [Binding Slash] Probability: 45.00%
[A] [SusaMaki] Loss 297 Soldier (21543/44391)
[A] [Niya] Loss 286 Soldier (20643/44345)
[A] [Mia] Loss 280 Soldier (4110/38679)
[A] [SusaMaki] Loss 297 Soldier (21246/44332)
[A] [Niya] Loss 280 Soldier (20363/44289)
[A] [Mia] Loss 274 Soldier (3836/38625)
[A] [SusaMaki] Loss 289 Soldier (20957/44275)
[A] [Niya] Loss 303 Soldier (20060/44229)
[A] [Mia] Loss 291 Soldier (3545/38567)
[E] [Thiel][Soul Bound] Ready Probability: 45.00%+9.00%
[E] [Thiel] Normal ATK
[A] [Mia] Loss 561 Soldier (2984/38455)
[E] [Nicole] Use [Rose Blade] Probability: 35.00%+5.60%
[A] [Mia] Loss 2984 Soldier (0/37859)
[A] [Mia] Defeated
[A] [Niya] Loss 3349 Soldier (16711/43560)
[E] [Nicole] Normal ATK
[A] [Niya] Loss 2927 Soldier (13784/42975)
```

## Round 4
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[A] [SusaMaki][DMG Dealt Reduced] Effect Disappeared
[A] [SusaMaki] Normal ATK
[E] [Nicole] Loss 4045 Soldier (11829/38621)
[A] [SusaMaki] Use [Flash Fire] Probability: 45.00%+13.50%
[E] [Nicole] Loss 5197 Soldier (6632/37582)
[A] [SusaMaki] Use [White Blade] Probability: 40.00%+16.00%
[E] [Nicole] Loss 6577 Soldier (55/36267)
[A] [SusaMaki][Combo] Effect Triggered Probability: 60.00%
[A] [SusaMaki] Trigger [Combo]
[E] [Thiel] Loss 841 Soldier (0/34616)
[E] [Thiel] Defeated
```

**>>> RESULT: VICTORY (revela win).**
Final standing — Ally: SusaMaki 20,957, Niya 13,784, Mia 0 (defeated). Enemy: Thiel 0 (defeated), Nicole 55 (surviving), Dolly 0 (defeated). The log ends with Thiel's defeat in Round 4; the enemy's last unit (Nicole) was left at just 55 troops.

---

## Transcription notes
1. **No shared unit names** (ally SusaMaki / Niya / Mia vs. enemy Thiel / Nicole / Dolly), so `[A]`/`[E]` tags mark side for readability only — no ambiguity to resolve.
2. **All side tags are count-verified.** Every `Loss (current/max)` reconciles against the running per-unit totals; the final values fall straight out of the arithmetic and match the report exactly (ally SusaMaki 20,957 / Niya 13,784, enemy Nicole 55).
3. **Niya's `[Slayer][Assault]` follow-ups and Mia's `[Divine Punish]`→`[Combo]`** chains are logged as separate "Effect Activated/Triggered" hits; targets are tagged inline (always the enemy here).
4. **Round-start flavour text** ("On the battlefield, soldiers' injuries gradually worsen…") appears on Rounds 2–4, matching the game.
5. **Passive Exertion Round** had entries (SusaMaki/Mia passives) while **Pre War Preparation Round** was an empty header; both reproduced as shown.
6. **Battle end:** the screenshots end at Thiel's defeat in Round 4. Per the report this is a Victory for revela even though enemy Nicole survived at 55 troops (Thiel and Dolly were both wiped); no further ally losses occurred, consistent with the final report figures.


---
---

all matches (matches 1 through 10):
match 1: victory
match 2: victory
match 3: victory
match 4: victory
match 5: victory
match 6: victory
match 7: victory
match 8: victory
match 9: victory
match 10: victory

100% win rate (keep in mind that this is a small sample)