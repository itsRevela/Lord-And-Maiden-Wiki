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
skills: (main)binding slash lv10 (lv5 relic effect), radiant slash lv10 max awakening [Tactical, max 5★], soul bound lv10 max awakening [Tactical, max 5★]
Skill stone: Holy-light Chop lv5 [Tactical, max 5★]  *(plain damage stone — do NOT use a buff stone here)*

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

Thiel (commander):
lv 80 (level 5 advancement), attributes allocated: +229 ATK
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
lv 80 (level 5 advancement), attributes allocated: +229 ATK
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

## Notes
- **Why these heroes:** their main skills are pure **"Launch N ATK"** (Binding Slash 2‑3 hits / Fly Flowers 1‑3 / Sky Rain Arrows 3‑5) on 3 enemies — no debuff/buff/control riders, so every hit is a clean damage reading on all three DEF levels.
- **Skill stones are OPTIONAL and must be DISTINCT within a team.** The only rule is *no identical stone on two heroes of the same formation* (no per‑category cap). The slot can be left **empty** — for this baseline that's actually the cleanest (one fewer skill firing), so feel free to run all three with **no stone**. If you'd rather fill them, the three distinct plain‑damage stones shown (Holy‑light Chop / Rift / Purgatory Trial) are valid; just *avoid buff/heal/shield stones* (Elf Deer, Field Therapy, Reactive Block).
- **Modular skills** are the heroes' own defaults; any plain "ATK N enemy" skill is a fine substitute.
- Keep **gear + messenger identical across every unit** — it's the control (these exact pieces appeared in your first log).
- This is the highest‑value of the three: it re‑grounds the entire damage equation, currently fit only to one shielded‑tank fight.

---
---

Results:

Here's the transcription of the battle report.

**Result: FAIL** (revela's loss)

**Header**

| | Left | Right |
|---|---|---|
| Player | revela — Glorius | Customize-Enemy — Nothing |
| Level | Lv.48 | Lv.48 |
| Health bar | 11,370 / 161,000 | 20,120 / 161,000 |

**Team Totals**

| | revela (Left) | Nothing (Right) |
|---|---|---|
| Total Number Of Troops | 161,000 | 161,000 |
| Health | 11,370 | 20,120 |
| Slight Wound | 135,674 | 127,495 |
| Severe Wound | 10,078 | 9,650 |
| Death | 3,878 | 3,735 |

**Units** — both sides field the same trio (all Lv.80): Thiel ★★★★★ (55,000), Nicole ★★★★ (51,000), Dolly ★★★★★ (55,000).

**Per-Unit Stats — revela (Left)**

| Stat | Thiel | Nicole | Dolly |
|---|---|---|---|
| Kills | 27,710 | 28,501 | 84,669 |
| Heal | 0 | 0 | 0 |
| Slight Wound | 48,245 | 44,668 | 42,761 |
| Severe Wound | 4,864 | 4,562 | 652 |
| Death | 1,891 | 1,770 | 217 |

**Per-Unit Stats — Nothing (Right)**

| Stat | Thiel | Nicole | Dolly |
|---|---|---|---|
| Kills | 67,876 | 17,062 | 64,692 |
| Heal | 0 | 0 | 0 |
| Slight Wound | 34,267 | 44,799 | 48,429 |
| Severe Wound | 460 | 4,464 | 4,726 |
| Death | 153 | 1,737 | 1,845 |

Every figure cross-checks: each side's per-unit Slight/Severe/Death and Health sums to its team totals (161,000 troops each), and each team's total Kills equals the opponent's total casualties (revela 140,880; Nothing 149,630). 

---
---

Battle log:

# Match Log — Transcription (Fail Match)

**Match:** revela (Glorius) vs. Customize-Enemy (Nothing) — both Lv.48
**Result:** FAIL (revela's loss) — single battle, 4 rounds.

**Legend**
- `[A]` = Ally team (revela / green ▲): **Thiel**, **Nicole**, **Dolly**
- `[E]` = Enemy team (Nothing / red ▲): **Thiel**, **Nicole**, **Dolly**
- Both teams field the *same three units* (Thiel / Nicole / Dolly), so every line is tagged `[A]` or `[E]` to mark the acting side. The game distinguished them only by green/red colour.
- Soldier counts are `(current / max)`; max declines as troops take severe wounds/deaths.
- Every `Loss` line below was cross-checked against running soldier counts to confirm its side.

---

## Damage Statistics

**Ally (revela)**

| Unit | Normal ATK | Skill | Skills Used |
|---|---|---|---|
| Thiel | 9,291 | 18,419 | 3 |
| Nicole | 7,355 | 21,146 | 4 |
| Dolly | 16,443 | 68,226 | 5 |

**Enemy (Nothing)**

| Unit | Normal ATK | Skill | Skills Used |
|---|---|---|---|
| Thiel | 11,762 | 56,114 | 6 |
| Nicole | 4,935 | 12,127 | 3 |
| Dolly | 11,759 | 52,933 | 3 |

## Passive Exertion Round
*(header only — no events logged)*

## Pre War Preparation Round
*(header only — no events logged)*

## Round 1
```
[E] [Dolly][Sky Rain Arrows] Ready Probability: 50.00%
[E] [Dolly] Use [Chain Arrows] Probability: 35.00%+7.00%
[A] [Nicole] Loss 6767 Soldier (44233/49647)
[A] [Thiel] Loss 6619 Soldier (48381/53677)
[E] [Dolly] Normal ATK
[A] [Dolly] Loss 4516 Soldier (50484/54097)
[A] [Dolly][Sky Rain Arrows] Ready Probability: 50.00%
[A] [Dolly][Purgatory Trial] Ready Probability: 45.00%+9.00%
[A] [Dolly] Normal ATK
[E] [Dolly] Loss 5641 Soldier (49359/53872)
[E] [Thiel][Soul Bound] Ready Probability: 45.00%+9.00%
[E] [Thiel] Use [Holy-light Chop] Probability: 35.00%+7.00%
[A] [Thiel] Loss 3974 Soldier (44407/52883)
[A] [Nicole] Loss 3945 Soldier (40288/48858)
[A] [Dolly] Loss 3700 Soldier (46784/53357)
[E] [Thiel] Normal ATK
[A] [Thiel] Loss 4771 Soldier (39636/51929)
[A] [Thiel] Normal ATK
[E] [Nicole] Loss 5149 Soldier (45851/49971)
[A] [Nicole] Use [Rose Blade] Probability: 35.00%+5.60%
[E] [Nicole] Loss 5419 Soldier (40432/48888)
[E] [Dolly] Loss 4828 Soldier (44531/52907)
[A] [Nicole] Use [Rift] Probability: 30.00%+6.00%
[E] [Nicole] Loss 1903 Soldier (38529/48508)
[E] [Nicole] Loss 1772 Soldier (36757/48154)
[E] [Nicole] Loss 1959 Soldier (34798/47763)
[E] [Nicole] Loss 1959 Soldier (32839/47372)
[A] [Nicole] Normal ATK
[E] [Nicole] Loss 4927 Soldier (27912/46387)
[E] [Nicole] Use [Rift] Probability: 30.00%+6.00%
[A] [Nicole] Loss 1476 Soldier (38812/48563)
[A] [Nicole] Loss 1522 Soldier (37290/48259)
[A] [Nicole] Loss 1616 Soldier (35674/47936)
[E] [Nicole] Normal ATK
[A] [Dolly] Loss 3958 Soldier (42826/52566)
```

## Round 2
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[E] [Dolly] Use [Sky Rain Arrows] Probability: 50.00%
[A] [Thiel] Loss 1932 Soldier (37704/50314)
[A] [Nicole] Loss 2101 Soldier (33573/46290)
[A] [Dolly] Loss 2029 Soldier (40797/51187)
[A] [Thiel] Loss 1932 Soldier (35772/49928)
[A] [Nicole] Loss 2123 Soldier (31450/45866)
[A] [Dolly] Loss 1930 Soldier (38867/50801)
[A] [Thiel] Loss 1993 Soldier (33779/49530)
[A] [Nicole] Loss 2275 Soldier (29175/45411)
[A] [Dolly] Loss 1871 Soldier (36996/50427)
[A] [Thiel] Loss 2054 Soldier (31725/49120)
[A] [Nicole] Loss 2101 Soldier (27074/44991)
[A] [Dolly] Loss 1989 Soldier (35007/50030)
[E] [Dolly][Arrows Volley] Ready Probability: 45.00%+9.00%
[E] [Dolly] Normal ATK
[A] [Nicole] Loss 4695 Soldier (22379/44052)
[A] [Dolly] Use [Sky Rain Arrows] Probability: 50.00%
[E] [Thiel] Loss 1556 Soldier (53444/54689)
[E] [Nicole] Loss 2432 Soldier (25480/44054)
[E] [Dolly] Loss 2102 Soldier (42429/51650)
[E] [Thiel] Loss 1637 Soldier (51807/54362)
[E] [Nicole] Loss 2383 Soldier (23097/43578)
[E] [Dolly] Loss 2255 Soldier (40174/51199)
[E] [Thiel] Loss 1556 Soldier (50251/54051)
[E] [Nicole] Loss 2432 Soldier (20665/43092)
[E] [Dolly] Loss 2080 Soldier (38094/50783)
[A] [Dolly][Arrows Volley] Ready Probability: 45.00%+9.00%
[A] [Dolly] Use [Chain Arrows] Probability: 35.00%+7.00%
[E] [Thiel] Loss 4842 Soldier (45409/53083)
[E] [Dolly] Loss 6802 Soldier (31292/49423)
[A] [Dolly] Use [Purgatory Trial] Probability: 45.00%+9.00%
[E] [Dolly] Loss 9702 Soldier (21590/47483)
[E] [Nicole] Loss 10057 Soldier (10608/41081)
[A] [Dolly] Normal ATK
[E] [Nicole] Loss 4966 Soldier (5642/40088)
[E] [Thiel] Use [Soul Bound] Probability: 45.00%+9.00%
[A] [Thiel] Loss 10079 Soldier (21646/47105)
[A] [Nicole] Loss 10635 Soldier (11744/41925)
[A] [Thiel][DMG Dealt Reduced] 15.08%
[A] [Nicole][DMG Dealt Reduced] 15.08%
[E] [Thiel] Normal ATK
[A] [Dolly] Loss 4242 Soldier (30765/49182)
[A] [Thiel][Soul Bound] Ready Probability: 45.00%+9.00%
[A] [Thiel] Use [Holy-light Chop] Probability: 35.00%+7.00%
[E] [Thiel] Loss 1924 Soldier (43485/52699)
[E] [Nicole] Loss 2640 Soldier (3002/39560)
[E] [Dolly] Loss 2475 Soldier (19115/46988)
[A] [Thiel] Normal ATK
[E] [Thiel] Loss 2288 Soldier (41197/52242)
[A] [Nicole] Use [Rose Sword] Probability: 30.00%+4.80%
[E] [Thiel] Loss 702 Soldier (40495/52102)
[E] [Nicole] Loss 1141 Soldier (1861/39332)
[E] [Dolly] Loss 1007 Soldier (18108/46787)
[A] [Nicole] Normal ATK
[E] [Dolly] Loss 1997 Soldier (16111/46388)
[E] [Nicole] Use [Fly Flowers] Probability: 35.00%
[A] [Thiel] Loss 483 Soldier (21163/47009)
[A] [Nicole] Loss 547 Soldier (11197/41816)
[A] [Dolly] Loss 497 Soldier (30268/49083)
[A] [Thiel] Loss 517 Soldier (20646/46906)
[A] [Nicole] Loss 515 Soldier (10682/41713)
[A] [Dolly] Loss 501 Soldier (29767/48983)
[E] [Nicole] Use [Rose Sword] Probability: 30.00%+4.80%
[A] [Thiel] Loss 507 Soldier (20139/46805)
[A] [Nicole] Loss 504 Soldier (10178/41613)
[A] [Dolly] Loss 463 Soldier (29304/48891)
[A] [Thiel] Loss 473 Soldier (19666/46711)
[A] [Nicole] Loss 510 Soldier (9668/41511)
[A] [Dolly] Loss 487 Soldier (28817/48794)
[A] [Thiel] Loss 497 Soldier (19169/46612)
[A] [Nicole] Loss 515 Soldier (9153/41408)
[A] [Dolly] Loss 497 Soldier (28320/48695)
[E] [Nicole] Normal ATK
[A] [Dolly] Loss 977 Soldier (27343/48500)
```

## Round 3
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[E] [Dolly] Use [Arrows Volley] Probability: 45.00%+9.00%
[A] [Thiel] Loss 1752 Soldier (17417/43518)
[A] [Nicole] Loss 1723 Soldier (7430/37839)
[A] [Dolly] Loss 1599 Soldier (25744/46066)
[A] [Thiel] Loss 1634 Soldier (15783/43192)
[A] [Nicole] Loss 1866 Soldier (5564/37466)
[A] [Dolly] Loss 1599 Soldier (24145/45747)
[A] [Thiel] Loss 1617 Soldier (14166/42869)
[A] [Nicole] Loss 1812 Soldier (3752/37104)
[A] [Dolly] Loss 1615 Soldier (22530/45424)
[E] [Dolly][Purgatory Trial] Ready Probability: 45.00%+9.00%
[E] [Dolly] Normal ATK
[A] [Dolly] Loss 2548 Soldier (19982/44915)
[A] [Dolly][Sky Rain Arrows] Ready Probability: 50.00%
[A] [Dolly] Use [Arrows Volley] Probability: 45.00%+9.00%
[E] [Thiel] Loss 1719 Soldier (38776/50599)
[E] [Nicole] Loss 1861 Soldier (0/35213)
[E] [Nicole] Defeated
[E] [Dolly] Loss 2390 Soldier (13721/42883)
[E] [Thiel] Loss 1618 Soldier (37158/50276)
[E] [Dolly] Loss 2163 Soldier (11558/42451)
[E] [Thiel] Loss 1752 Soldier (35406/49926)
[E] [Dolly] Loss 2368 Soldier (9190/41978)
[A] [Dolly] Normal ATK
[E] [Dolly] Loss 3381 Soldier (5809/41302)
[A] [Thiel] Use [Binding Slash] Probability: 45.00%
[E] [Thiel] Loss 854 Soldier (34552/49756)
[E] [Dolly] Loss 1189 Soldier (4620/41065)
[E] [Thiel] Loss 819 Soldier (33733/49593)
[E] [Dolly] Loss 1142 Soldier (3478/40837)
[A] [Thiel] Use [Soul Bound] Probability: 45.00%+9.00%
[E] [Thiel] Loss 3898 Soldier (29835/48814)
[E] [Dolly] Loss 3478 Soldier (0/40142)
[E] [Dolly] Defeated
[A] [Thiel][DMG Dealt Reduced] 15.08%
[E] [Thiel][DMG Dealt Reduced] 15.08%
[A] [Thiel] Normal ATK
[E] [Thiel] Loss 1854 Soldier (27981/48444)
[E] [Thiel] Use [Binding Slash] Probability: 45.00%
[A] [Thiel] Loss 1427 Soldier (12739/42584)
[A] [Nicole] Loss 1463 Soldier (2289/36812)
[A] [Dolly] Loss 1277 Soldier (18705/44660)
[A] [Thiel] Loss 1427 Soldier (11312/42299)
[A] [Nicole] Loss 1492 Soldier (797/36514)
[A] [Dolly] Loss 1303 Soldier (17402/44400)
[E] [Thiel][Soul Bound] Ready Probability: 45.00%+9.00%
[E] [Thiel] Normal ATK
[A] [Thiel] Loss 2749 Soldier (8563/41750)
[A] [Nicole] Use [Rose Blade] Probability: 35.00%+5.60%
[E] [Thiel] Loss 456 Soldier (27525/48353)
[A] [Nicole] Normal ATK
[E] [Thiel] Loss 431 Soldier (27094/48267)
```

## Round 4
*On the battlefield, soldiers' injuries gradually worsen, changing from Slight Wound to Severe Wound or Death.*
```
[A] [Dolly] Use [Sky Rain Arrows] Probability: 50.00%
[E] [Thiel] Loss 1076 Soldier (26018/45935)
[E] [Thiel] Loss 1099 Soldier (24919/45716)
[E] [Thiel] Loss 1189 Soldier (23730/45479)
[E] [Thiel] Loss 1155 Soldier (22575/45248)
[A] [Dolly][Arrows Volley] Ready Probability: 45.00%+9.00%
[A] [Dolly][Purgatory Trial] Ready Probability: 45.00%+9.00%
[A] [Dolly] Normal ATK
[E] [Thiel] Loss 2455 Soldier (20120/44757)
[E] [Thiel] Use [Binding Slash] Probability: 45.00%
[A] [Thiel] Loss 1119 Soldier (7444/38209)
[A] [Nicole] Loss 797 Soldier (0/32784)
[A] [Nicole] Defeated
[A] [Dolly] Loss 1162 Soldier (16240/41469)
[A] [Thiel] Loss 1165 Soldier (6279/37976)
[A] [Dolly] Loss 1062 Soldier (15178/41257)
[A] [Thiel] Loss 1177 Soldier (5102/37741)
[A] [Dolly] Loss 1095 Soldier (14083/41038)
[E] [Thiel] Use [Radiant Slash] Probability: 35.00%+7.00%
[A] [Thiel] Loss 2741 Soldier (2361/37193)
[A] [Dolly] Loss 2713 Soldier (11370/40496)
[A] [Thiel][DMG Dealt Reduced] Effect Updated
[A] [Dolly][DMG Dealt Reduced] 9.56%
[E] [Thiel] Use [Soul Bound] Probability: 45.00%+9.00%
[A] [Thiel] Loss 2361 Soldier (0/36721)
[A] [Thiel] Defeated
```

**>>> RESULT: FAIL (revela loss).**
Final standing — Ally: Thiel defeated, Nicole defeated, **Dolly surviving at 11,370**. Enemy: Nicole defeated, Dolly defeated, **Thiel surviving at 20,120**. The log ends in Round 4 with ally Thiel's defeat; revela's last unit (Dolly, 11,370) had fewer surviving troops than the enemy's last unit (Thiel, 20,120), hence the loss.

---

## Transcription notes
1. **Three shared unit names.** Both teams run Thiel / Nicole / Dolly, so every line carries an `[A]` (ally) or `[E]` (enemy) tag. The original log distinguished sides only by green/red colour.
2. **Side tags are count-verified.** Every `Loss (current/max)` value was reconciled against the running per-unit totals, so the side attribution on casualty lines is confirmed by arithmetic, not just colour. (Example check: ally Dolly 14,083 − 2,713 = 11,370, the final surviving total.)
3. **One colour I double-checked:** in Round 1, the second `[Thiel] Normal ATK` is **ally** (green) — it produces an enemy-Nicole loss and opens revela's offensive phase. The first `[Thiel] Normal ATK` just above it is enemy (red). They look similar at small size but are opposite sides.
4. **"Soul Bound" / "Radiant Slash" apply `[DMG Dealt Reduced]` to the units they hit**, so that debuff is tagged to the victim's side (e.g., in Round 3 ally Thiel's Soul Bound debuffs enemy Thiel → `[E] [Thiel][DMG Dealt Reduced]`).
5. **Round-start flavour text** ("On the battlefield, soldiers' injuries gradually worsen…") appears on Rounds 2–4, matching the game.
6. **Passive Exertion Round** and **Pre War Preparation Round** were shown as headers with no events beneath them before Round 1; reproduced as such.
