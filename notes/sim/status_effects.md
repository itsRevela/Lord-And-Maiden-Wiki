# Status Effects / Buffs & Debuffs - Combat-Sim Catalog

Behavior catalog of every entry in `data/csv/Buff.csv` (76 rows), for the battle simulator. Generated from `data/sim/status_effects.json` (`notes/sim/_build_status_effects.py`). Behaviors are derived from in-game text (Language_SkillDes / Language_SysTip / Language_Game), the verified wiki (`wiki/Mechanics/Status-Effects.md`, `wiki/Reference/Game-Hints.md`) and the `NewSkillInfo` Effect/Buff strings that apply each buff; each entry cites its sources.

**Key rules that govern every entry:**
- `type`: `1` positive / `-1` negative / `0` neutral (from Buff.csv `Type`).
- **Magnitudes** (damage %, heal coefficient, proc chance, duration) are NOT stored in Buff.csv; they live in the applying skill's `Effect`/`Buff` string. The final damage/heal numbers are resolved server-side - `UNKNOWN_SERVER_SIDE` (combat is server-authoritative; the client only sees inputs + the replay log).
- **Stacking** (`wiki/Reference/Game-Hints.md`): the *same* effect from the *same* skill type does not stack (only the highest applies); the same effect from *different* skill types adds together.
- **Prepared variants:** buff ids 83-86 are the telegraphed `(Prepared)` display of 114-117 (Stun / Disarm / Silence / Chaos) - they resolve to the same real CC when they fire.

## Index

| id | name | type | category | prepared |
|---:|------|:----:|----------|:--------:|
| 5 | DMG Dealt Increased | 1 | dmg_mod |  |
| 6 | DMG Dealt Reduced | -1 | dmg_mod |  |
| 7 | DMG Taken Increased | -1 | dmg_mod |  |
| 8 | DMG Taken Reduced | 1 | dmg_mod |  |
| 9 | ATK Attribute Increased | 1 | attr_mod |  |
| 10 | DEF Attribute Increased | 1 | attr_mod |  |
| 11 | DES Attribute Increased | 1 | attr_mod |  |
| 12 | Spd Attribute Increased | 1 | attr_mod |  |
| 13 | Increase All Attributes | 1 | attr_mod |  |
| 14 | ATK Reduced | -1 | attr_mod |  |
| 15 | DEF Reduced | -1 | attr_mod |  |
| 16 | DES Reduced | -1 | attr_mod |  |
| 17 | Spd Attribute Reduced | -1 | attr_mod |  |
| 18 | All Attributes Reduced | -1 | attr_mod |  |
| 19 | ATK Attribute Increased | 1 | attr_mod |  |
| 20 | DEF Attribute Increased | 1 | attr_mod |  |
| 21 | DES Attribute Increased | 1 | attr_mod |  |
| 22 | Spd Attribute Increased | 1 | attr_mod |  |
| 23 | Increase All Attributes | 1 | attr_mod |  |
| 24 | ATK Reduced | -1 | attr_mod |  |
| 25 | DEF Reduced | -1 | attr_mod |  |
| 26 | DES Reduced | -1 | attr_mod |  |
| 27 | Spd Attribute Reduced | -1 | attr_mod |  |
| 28 | All Attributes Reduced | -1 | attr_mod |  |
| 29 | Normal ATK DMG Dealt Increased | 1 | dmg_mod |  |
| 30 | Normal DMG Dealt Reduced | -1 | dmg_mod |  |
| 31 | Tactical Skill DMG Dealt Increased | 1 | dmg_mod |  |
| 32 | Tactical Skill DMG Dealt Reduced | -1 | dmg_mod |  |
| 33 | Pursuit Skill DMG Dealt Increased | 1 | dmg_mod |  |
| 34 | Pursuit Skill DMG Dealt Reduced | -1 | dmg_mod |  |
| 35 | Normal DMG Taken Increased | -1 | dmg_mod |  |
| 36 | Normal DMG Taken Reduced | 1 | dmg_mod |  |
| 37 | Tactical Skill DMG Taken Increased | -1 | dmg_mod |  |
| 38 | Reduce Tactical Skill DMG received | 1 | dmg_mod |  |
| 39 | Pursuit Skill DMG Taken Increased | -1 | dmg_mod |  |
| 40 | Pursuit Skill DMG Taken Reduced | 1 | dmg_mod |  |
| 42 | Soldier HP Increased | 1 | attr_mod |  |
| 43 | Curse DMG Taken  Reduced | 1 | dmg_mod |  |
| 44 | Burning DMG Taken Reduced | 1 | dmg_mod |  |
| 47 | Real DMG Dealt Increased | 1 | dmg_mod |  |
| 70 | Assault | 1 | proc |  |
| 73 | Shield | 1 | shield |  |
| 74 | First Aid | 1 | heal |  |
| 79 | Chance Haste | 1 | proc |  |
| 80 | Chance Combo | 1 | proc |  |
| 81 | Chance Counter | 1 | proc |  |
| 82 | Chance Splash | 1 | proc |  |
| 83 | Stun(Prepared) | -1 | control | yes |
| 84 | Disarm(Prepared) | -1 | control | yes |
| 85 | Silence(Prepared) | -1 | control | yes |
| 86 | Chaos(Prepared) | -1 | control | yes |
| 87 | Heal | 0 | heal |  |
| 88 | Instant | 1 | proc |  |
| 89 | Eternal | 0 | other |  |
| 106 | Blood Sucking | 1 | lifesteal |  |
| 107 | Self-Heal | 1 | heal |  |
| 108 | Burn | -1 | dot |  |
| 109 | Curse | -1 | dot |  |
| 111 | Chance Dodge | 1 | proc |  |
| 113 | Concentration | 1 | other |  |
| 114 | Stun | -1 | control |  |
| 115 | Disarm | -1 | control |  |
| 116 | Silence | -1 | control |  |
| 117 | Chaos | -1 | control |  |
| 118 | Taunts | -1 | taunt |  |
| 119 | Heal Ban | -1 | control |  |
| 120 | Assist | 1 | taunt |  |
| 125 | Superconducting | 1 | proc |  |
| 139 | Purification | 1 | cleanse |  |
| 140 | Sneak Attack | 1 | proc |  |
| 150 | Insight | 1 | proc |  |
| 154 | Arcane Missile | -1 | control |  |
| 155 | Precision Strike | 1 | proc |  |
| 157 | Combustion Aid | -1 | dmg_mod |  |
| 158 | Element Burs | 1 | proc |  |
| 159 | Pursuit Splash | 1 | proc |  |

## Control / Crowd-Control (CC)

### 83 - Stun(Prepared) *(Prepared variant)*

- **Type:** -1 negative
- **Behavior:** Telegraphed (Prepared) Stun -- a Stun whose application is announced one step ahead (the '(Prepared)' display of buff 114); resolves to the same Unable-to-Move state.
- **Stacking:** Becomes the real Stun (114) when it fires.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:49; Buff.csv:62 (114 Stun); Name token 眩晕(预备) = Stun(Prepared)

### 84 - Disarm(Prepared) *(Prepared variant)*

- **Type:** -1 negative
- **Behavior:** Telegraphed (Prepared) Disarm -- the '(Prepared)' display of buff 115; resolves to Disarm (cannot Normal ATK).
- **Stacking:** Becomes the real Disarm (115) when it fires.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:50; Buff.csv:63 (115 Disarm); NewSkillInfo ST1 ID1025 Dragon Serious applies 84/85/86 as '25% Probability ... Disarmed/Silenced/Chaos'

### 85 - Silence(Prepared) *(Prepared variant)*

- **Type:** -1 negative
- **Behavior:** Telegraphed (Prepared) Silence -- the '(Prepared)' display of buff 116; resolves to Silence (cannot Tactical).
- **Stacking:** Becomes the real Silence (116) when it fires.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:51; Buff.csv:64 (116 Silence); NewSkillInfo ST1 ID1025 Dragon Serious

### 86 - Chaos(Prepared) *(Prepared variant)*

- **Type:** -1 negative
- **Behavior:** Telegraphed (Prepared) Chaos -- the '(Prepared)' display of buff 117; resolves to Chaos (random-target attacks).
- **Stacking:** Becomes the real Chaos (117) when it fires.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:52; Buff.csv:65 (117 Chaos); NewSkillInfo ST1 ID1025 Dragon Serious

### 114 - Stun

- **Type:** -1 negative
- **Behavior:** Stun: the unit is Unable to Move and cannot act at all (no normal attack, tactical, or pursuit) for the duration.
- **Stacking:** Refreshes duration; cleansable by Purification.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:62; Language_SkillDes 处于眩晕状态 'In A Stunned State'; NewSkillInfo ST1 ID1009 Shocking Roar 'In A Stunned State,Unable To Move'; Status-Effects.md (Stun = cannot act)

### 115 - Disarm

- **Type:** -1 negative
- **Behavior:** Disarm: the unit cannot launch Normal ATK (tactical/pursuit skills still usable).
- **Stacking:** Refreshes duration; usually cleansable, but some self-applied Disarm is flagged 'Cannot Be purified'.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:63; NewSkillInfo ST2 ID1027 Destroy Domain 'In A Disarmed State,Cannot Launch Normal ATK'; Status-Effects.md (Disarm = no normal attack)

### 116 - Silence

- **Type:** -1 negative
- **Behavior:** Silence: the unit cannot launch Tactical skills (normal attack and pursuit still usable).
- **Stacking:** Refreshes duration; cleansable by Purification.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:64; NewSkillInfo ST2 ID1024 Cold Attack 'In A Silenced State,Cannot Launch Tactical Skills'; Status-Effects.md (Silence = no tactical skills)

### 117 - Chaos

- **Type:** -1 negative
- **Behavior:** Chaos: the unit carries out Undifferentiated ATK -- normal attacks and damage-dealing Tactical skills (and pursuits they trigger) hit completely random targets, friend or foe. Overrides Taunt.
- **Stacking:** Refreshes duration; cleansable by Purification.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:65; Language_SysTip 混乱 'Chaos effect only applies to normal attacks and damage-dealing Tactical Skills. Subsequent Pursuit ... is also affected'; NewSkillInfo ST4 ID17 Chaos 'Carry Out Undifferentiated ATK'; Status-Effects.md

### 119 - Heal Ban

- **Type:** -1 negative
- **Behavior:** Heal Ban (Forbidden Treatment): the unit cannot be healed by any source for the duration.
- **Stacking:** Refreshes duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:67; Language_SkillDes 无法受到治疗效果 'Cannot Be Healed'; NewSkillInfo ST2 ID76 Taboo Seal 'Forbidden Treatment State,Cannot Be Healed'; Status-Effects.md

### 154 - Arcane Missile

- **Type:** -1 negative
- **Behavior:** Arcane Missile: a recurring random-CC effect -- before each round, a chance to inflict one of Disarm / Silence / Chaos / Stun on the target.
- **Stacking:** Re-rolls each round while active.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:73; NewSkillInfo ST1 ID86 Arcane Missile 'Before Each Round,A Chance to In A Disarmed/Silenced/Chaos/Stunned State'

## Taunt / Forced-Targeting & Cover

### 118 - Taunts

- **Type:** -1 negative
- **Behavior:** Taunt (Provoke): forces enemies to direct their Normal ATK at the taunter, overriding normal target selection. Ignored if the taunted unit is also under Chaos.
- **Stacking:** Refreshes duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:66; NewSkillInfo ST2 ID110 Knight Creed 'In A Provoked State'; Status-Effects.md (Taunt forces normal-attack on taunter; ignored under Chaos)

### 120 - Assist

- **Type:** +1 positive
- **Behavior:** Assist (Protect): the bearer guards allied troops from Normal ATK -- 'Protect Our Troops From Normal ATK', intercepting normal attacks aimed at protected allies (an ally-side cover/redirect).
- **Stacking:** Refreshes duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:68; NewSkillInfo ST1 ID26 Star Shield 'Protect Our Troops From Normal ATK' (Buff=120_...); ST2 ID21 Block (120)

## Damage over Time (DoT)

### 108 - Burn

- **Type:** -1 negative
- **Behavior:** Burn: a damage-over-time -- 'Before Each Round, Burning DMG Taken' at a skill-supplied DMG coefficient (~0.5-1.69). Mitigated by buff 44; amplified by 157; can be detonated by 158 / Exploding-Flame skills.
- **Stacking:** Per-skill coefficient and duration; reapplying refreshes/can enable detonation skills.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:58; NewSkillInfo ST2 ID19 Hopeless; ST1 ID1009 Shocking Roar (coef 1.69); ST2 ID73 Exploding Flame (detonate 1.6 if Burning)

### 109 - Curse

- **Type:** -1 negative
- **Behavior:** Curse: a damage-over-time -- 'Before Each Round, Curse DMG Taken' at a skill-supplied DMG coefficient (~0.5-1.69). Mitigated by buff 43; amplified by 157; detonated by 158.
- **Stacking:** Per-skill coefficient and duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:59; NewSkillInfo ST1 ID1002 Frighten (coef 1.33); ST1 ID1007 Black Bog (coef 1.52)

## Shields

### 73 - Shield

- **Type:** +1 positive
- **Behavior:** Shield: grants N layers; each layer fully blocks one incoming damage instance (not a damage amount). Pierced by attacks flagged 'Ignores Dodge and Shield'.
- **Stacking:** Stacks as layers (skills grant 1-2). Each blocked hit consumes one layer.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:43; Language_SkillDes 'Gain N Layers Of Shield, Which Can Block N DMG'; NewSkillInfo ST2 ID1008 Wing Shield (2 layers); Status-Effects.md (Shield absorbs first instance)

## Lifesteal

### 106 - Blood Sucking

- **Type:** +1 positive
- **Behavior:** Blood Sucking: the bearer recruits/restores some enemy soldiers when it deals damage, by a skill-supplied Blood Sucking Coefficient (0.4-1.5). A lifesteal multiplier on damage dealt.
- **Stacking:** Per-skill coefficient and duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:56; NewSkillInfo ST2 ID84 Night Elf 'Blood Sucking Coefficien 0.6'; ST4 ID1005 (1.50); Language_SkillDes 离间系数 'Blood Sucking Coefficient'

## Healing

### 74 - First Aid

- **Type:** +1 positive
- **Behavior:** First Aid: a reactive heal -- when the bearer takes a Normal ATK, a chance to Restore Life (skill-supplied healing coefficient, e.g. 0.55-0.76; scales off Soldiers' HP).
- **Stacking:** Per-skill coefficient and trigger chance.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:44; NewSkillInfo ST1 ID37 Past Memory (74, coef 0.55); ST1 ID1005 Devil Fruit (74, coef 0.76)

### 87 - Heal

- **Type:** 0 neutral
- **Behavior:** Heal: an instant restore-life effect (heal value scales off the Soldiers' HP attribute). The generic active-heal status shown as 'Healing'.
- **Stacking:** Per-skill coefficient.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:53; Language_SysTip 治疗效果受士兵生命属性影响 'Healing Effect Is Affected By Soldiers HP'; Language_SkillDes 治疗系数 'Healing Coefficient'

### 107 - Self-Heal

- **Type:** +1 positive
- **Behavior:** Self-Heal / regen: 'Before Each Round, Restore Life' at a skill-supplied Healing Coefficient (0.32-1.52; scales off Soldiers' HP). The core periodic-heal buff used by most healers.
- **Stacking:** Per-skill coefficient and duration; cross-type heals add.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:57; NewSkillInfo ST1 ID1 Healing Light (107, coef 0.45); ST3 ID7 Holy Water (107, coef 0.57); Game-Hints.md (healing scales off HP)

## Cleanse

### 139 - Purification

- **Type:** +1 positive
- **Behavior:** Purification: removes harmful effects produced by Tactical and Pursuit skills from an ally (cleanse). Often applied 'before each round, a chance to Purify: Disarm/Silence/Stun/Chaos/Taunt'. Some debuffs are flagged 'Cannot Be purified'.
- **Stacking:** Per-skill chance; one cleanse per trigger.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:70; Language_SkillDes 净化 'Purify The Harmful Effect Produced By Tactical And Pursuit Skill'; NewSkillInfo ST1 ID53 Time Story; Status-Effects.md (Purify)

## Procs / Conditional Triggers

### 70 - Assault

- **Type:** +1 positive
- **Behavior:** Assault state: the bearer's Normal ATK gains added True/Real damage (Affected By ATK; per-skill Real DMG Base 12.5-50). An offensive empowerment, not a heal or DoT.
- **Stacking:** Carried per-skill; refreshes/overwrites with the higher value (attr-style).
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:42; NewSkillInfo ST1 ID65 Boost Morale; ST2 ID67 Epee Storm 'Real DMG Base 30'; Game 强袭 'Enhances Assault effects'

### 79 - Chance Haste

- **Type:** +1 positive
- **Behavior:** Chance Haste: a percentage chance to gain an extra/faster action (Haste proc). Trigger chance is skill-supplied.
- **Stacking:** Per-skill proc chance.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:45; resolver._CJK_FIX 概率极速 'Chance Haste'

### 80 - Chance Combo

- **Type:** +1 positive
- **Behavior:** Chance Combo: on a Normal ATK, a chance to immediately strike again (combo follow-up). Trigger chance is skill-supplied (e.g. Glowing Leaf 75%).
- **Stacking:** Per-skill proc chance.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:46; NewSkillInfo ST1 ID55 Clap Thunder 'A Chance to Combo'; ST1 ID1037 '75% Probability Combo'

### 81 - Chance Counter

- **Type:** +1 positive
- **Behavior:** Chance Counter: when the bearer receives a Normal ATK, a chance to counterattack (skill-supplied DMG coefficient, e.g. 0.7-1.69). Once applied it cannot be prevented.
- **Stacking:** Per-skill chance + coefficient.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:47; NewSkillInfo ST1 ID9 Counterattack (coef 0.95); ST1 ID82 '100% Counterattack'; Status-Effects.md (Counterattack cannot be prevented)

### 82 - Chance Splash

- **Type:** +1 positive
- **Behavior:** Chance Splash: on a Normal ATK (or Pursuit), a chance to splash damage to other enemies (skill-supplied DMG coefficient, e.g. 0.5-1.5).
- **Stacking:** Per-skill chance + coefficient.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:48; NewSkillInfo ST1 ID10 Red Blade 'Splash On Other Enemies (coef 0.50)'

### 88 - Instant

- **Type:** +1 positive
- **Behavior:** Instant / Swiftcast: while active, when the bearer activates a Tactical skill that needs preparation, a chance to reduce its preparation time by 1 round.
- **Stacking:** Per-skill trigger chance and duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:54; NewSkillInfo ST2 ID75 Sheep Game 'Swiftcast State, ... Reduce Preparation Time By 1 Round'

### 111 - Chance Dodge

- **Type:** +1 positive
- **Behavior:** Chance Dodge: when receiving a Normal ATK, a chance to dodge it entirely (skill-supplied chance, e.g. 30%). Bypassed by attacks flagged 'Ignores Dodge and Shield'.
- **Stacking:** Per-skill proc chance.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:60; NewSkillInfo ST2 ID68 Idol Voice '30% Probability Dodge'; resolver._CJK_FIX 概率闪避 'Chance Dodge'

### 125 - Superconducting

- **Type:** +1 positive
- **Behavior:** Superconducting: while active, when the bearer uses a Tactical skill that does NOT require preparation, a chance to immediately cast that Tactical skill 1 additional time.
- **Stacking:** Per-skill trigger chance and duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:69; NewSkillInfo ST1 ID63 Mana Storage 'Superconducting ... Activate The Tactical Skill 1 Additional Time'

### 140 - Sneak Attack

- **Type:** +1 positive
- **Behavior:** Sneak Attack: the bearer's attacks Will Not Be Affected by the Counter ATK Effect (it cannot be counterattacked). A defensive proc-immunity, typically paired with a DMG-dealt buff.
- **Stacking:** Boolean state; refreshes duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:71; NewSkillInfo ST3 ID17 Sneak Attack 'Will Not Be Affected by the Counter ATK Effect' (Buff=140_...)

### 150 - Insight

- **Type:** +1 positive
- **Behavior:** Insight: raises the activation probability of ALL the bearer's Pursuit skills by a skill-supplied amount ('All Pursuit Skill Probabilities Increased').
- **Stacking:** Per-skill magnitude and duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:72; NewSkillInfo ST1 ID84 Broken Star 'In An Insight State,All Pursuit Skill Probabilities Increased' (Buff=150_...)

### 155 - Precision Strike

- **Type:** +1 positive
- **Behavior:** Precision Strike: when the bearer launches an attack, a chance to Ignore Dodge and Shield AND ignore Soldier-Restraint penalties (the attack cannot be dodged/blocked and loses the -25% restraint reduction).
- **Stacking:** Per-skill trigger chance and duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:74; NewSkillInfo ST1 ID91 Time's Flow / ST1 ID94 Night Dance Allure / ST3 ID42 ATK-DEF Shift all carry Buff=155_... 'Ignores Dodge and Shield, Ignores Soldier Restraint effects'

### 158 - Element Burs

- **Type:** +1 positive
- **Behavior:** Element Burst: a proc -- when the bearer attacks an enemy that has Tactical Burning or Curse, a chance to immediately settle all remaining Burn+Curse DoT at 1.3x and then remove those effects (detonation; multi-stage attacks trigger only on the first hit).
- **Stacking:** Per-skill trigger chance; multiplier 1.3x in effect string.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:76; NewSkillInfo ST3 ID40 Element Burs 'settle all remaining Burning and Curse DMG at 1.3x, ... effects are removed' (Buff=158_..._1.3_...)

### 159 - Pursuit Splash

- **Type:** +1 positive
- **Behavior:** Pursuit Splash: when the bearer launches a Pursuit skill, a chance to splash that pursuit damage onto other enemies (skill-supplied DMG coefficient ~0.6). A pursuit-channel version of Splash.
- **Stacking:** Per-skill trigger chance and coefficient.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:77; NewSkillInfo ST1 ID93 Arcane Buff / ST3 ID41 Weakness Break 'When Launching Pursuit Skills, A Chance to Splash On Other Enemies (coef 0.60)'; Name token 追击+溅射

## Damage Modifiers

### 5 - DMG Dealt Increased

- **Type:** +1 positive
- **Behavior:** Multiplies the bearer's outgoing damage upward by a skill-supplied percentage; pure damage-dealt buff with no other effect. Magnitude is carried by the applying skill, not fixed in Buff.csv.
- **Stacking:** Same effect from the same skill type does not stack (highest applies); different skill types add together.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:2; Language_SkillDes.csv 'DMG Dealt Increased'; Game-Hints.md (same-type effects don't stack)

### 6 - DMG Dealt Reduced

- **Type:** -1 negative
- **Behavior:** Reduces the target's outgoing damage by a skill-supplied percentage (e.g. Bless Immortals -35%). Magnitude carried by the applying skill.
- **Stacking:** Same-type does not stack (highest); cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:3; NewSkillInfo ST1 ID1027 Bless Immortals (DMG Dealt Reduced 35%)

### 7 - DMG Taken Increased

- **Type:** -1 negative
- **Behavior:** Increases damage the target takes by a skill-supplied percentage (Affected By DES); amplifies all incoming hits while active.
- **Stacking:** Same-type does not stack (highest); cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:4; NewSkillInfo ST1 ID1042 Cold Secret 'DMG Taken Increased 15.2%'

### 8 - DMG Taken Reduced

- **Type:** +1 positive
- **Behavior:** Reduces damage the bearer takes by a skill-supplied percentage (Affected By DEF); common defensive buff.
- **Stacking:** Same-type does not stack (highest); cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:5; NewSkillInfo ST1 ID1005 Devil Fruit 'DMG Taken Reduced'

### 29 - Normal ATK DMG Dealt Increased

- **Type:** +1 positive
- **Behavior:** Increases the bearer's Normal-ATK damage by a skill-supplied percentage.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:26; localization 普通攻击伤害提高

### 30 - Normal DMG Dealt Reduced

- **Type:** -1 negative
- **Behavior:** Decreases the target's Normal-ATK damage by a skill-supplied percentage.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:27; localization 普通攻击伤害降低

### 31 - Tactical Skill DMG Dealt Increased

- **Type:** +1 positive
- **Behavior:** Increases the bearer's Tactical-skill damage by a skill-supplied percentage (Affected By Spd).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:28; NewSkillInfo ST2 ID1044 Melting Soul 'Tactical Skill DMG Dealt Increased 15.2%'

### 32 - Tactical Skill DMG Dealt Reduced

- **Type:** -1 negative
- **Behavior:** Decreases the target's Tactical-skill damage by a skill-supplied percentage.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:29; localization 战术技能伤害降低

### 33 - Pursuit Skill DMG Dealt Increased

- **Type:** +1 positive
- **Behavior:** Increases the bearer's Pursuit-skill damage by a skill-supplied percentage (Affected By Spd).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:30; NewSkillInfo ST1 ID1037 Glowing Leaf 'Pursuit Skill DMG Dealt Increased'

### 34 - Pursuit Skill DMG Dealt Reduced

- **Type:** -1 negative
- **Behavior:** Decreases the target's Pursuit-skill damage by a skill-supplied percentage.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:31; localization 追击技能伤害降低

### 35 - Normal DMG Taken Increased

- **Type:** -1 negative
- **Behavior:** Increases Normal-ATK damage the target takes by a skill-supplied percentage.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:32; localization 受到普通攻击伤害提高

### 36 - Normal DMG Taken Reduced

- **Type:** +1 positive
- **Behavior:** Decreases Normal-ATK damage the bearer takes by a skill-supplied percentage.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:33; localization 受到普通攻击伤害降低

### 37 - Tactical Skill DMG Taken Increased

- **Type:** -1 negative
- **Behavior:** Increases Tactical-skill damage the target takes by a skill-supplied percentage.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:34; localization 受到战术技能伤害提高

### 38 - Reduce Tactical Skill DMG received

- **Type:** +1 positive
- **Behavior:** Decreases Tactical-skill damage the bearer takes by a skill-supplied percentage.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:35; localization 受到战术技能伤害降低

### 39 - Pursuit Skill DMG Taken Increased

- **Type:** -1 negative
- **Behavior:** Increases Pursuit-skill damage the target takes by a skill-supplied percentage (Affected By DES); e.g. Demon Rock Slash +15.4%.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:36; NewSkillInfo ST4 ID1002 Demon Rock Slash 'takes increased Pursuit damage 15.4%'

### 40 - Pursuit Skill DMG Taken Reduced

- **Type:** +1 positive
- **Behavior:** Decreases Pursuit-skill damage the bearer takes by a skill-supplied percentage.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:37; localization 受到追击技能伤害降低

### 43 - Curse DMG Taken  Reduced

- **Type:** +1 positive
- **Behavior:** Reduces Curse (DoT) damage the bearer takes by a skill-supplied percentage (Affected By DEF); resistance buff vs the Curse channel.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:39; NewSkillInfo ST3 ID14 Magic Cloak 'Curse DMG Taken Reduced'

### 44 - Burning DMG Taken Reduced

- **Type:** +1 positive
- **Behavior:** Reduces Burn (DoT) damage the bearer takes by a skill-supplied percentage; resistance buff vs the Burn channel.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:40; Language_SkillDes 受到燃烧伤害降低 'Burning DMG Taken Reduced'

### 47 - Real DMG Dealt Increased

- **Type:** +1 positive
- **Behavior:** Increases the True/Real damage the bearer deals by a skill-supplied percentage (True damage ignores DEF mitigation).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:41; localization 造成真实伤害提高

### 157 - Combustion Aid

- **Type:** -1 negative
- **Behavior:** Combustion Aid: a debuff that amplifies DoT taken -- when the target takes Curse or Burning damage, a chance to multiply that DoT instance by 1.5x.
- **Stacking:** Per-skill trigger chance; multiplier 1.5x is in the effect string.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:75; NewSkillInfo ST1 ID92 Combustion Aid 'Make Curse or Burning DMG Taken*1.5' (Buff=157_..._1.5_...)

## Attribute Modifiers

### 9 - ATK Attribute Increased

- **Type:** +1 positive
- **Behavior:** Raises the bearer's ATK attribute by a skill-supplied amount (flat point value or %, Affected By DEF).
- **Stacking:** Same-type does not stack (highest); cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:6; NewSkillInfo ST1 ID65 Boost Morale 'ATK Attribute Increased 11.4'

### 10 - DEF Attribute Increased

- **Type:** +1 positive
- **Behavior:** Raises the bearer's DEF attribute by a skill-supplied amount.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:7; NewSkillInfo ST1 ID27 Self-Healing 'DEF Attribute Increased 15.2'

### 11 - DES Attribute Increased

- **Type:** +1 positive
- **Behavior:** Raises the bearer's DES (Ruin) attribute by a skill-supplied amount.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:8; localization 破坏属性提高

### 12 - Spd Attribute Increased

- **Type:** +1 positive
- **Behavior:** Raises the bearer's Speed attribute by a skill-supplied amount.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:9; NewSkillInfo ST1 ID15 Feather Fall 'Spd Attribute Increased 11.4'

### 13 - Increase All Attributes

- **Type:** +1 positive
- **Behavior:** Raises all four of the bearer's attributes (ATK/DEF/DES/Spd) by a skill-supplied amount.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:10; NewSkillInfo ST2 ID88 Elk Armor 'Increase All Attributes 7.4'

### 14 - ATK Reduced

- **Type:** -1 negative
- **Behavior:** Lowers the target's ATK attribute by a skill-supplied amount.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:11; localization 攻击属性降低

### 15 - DEF Reduced

- **Type:** -1 negative
- **Behavior:** Lowers the target's DEF attribute by a skill-supplied amount.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:12; localization 防御属性降低

### 16 - DES Reduced

- **Type:** -1 negative
- **Behavior:** Lowers the target's DES (Ruin) attribute by a skill-supplied amount.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:13; localization 破坏属性降低

### 17 - Spd Attribute Reduced

- **Type:** -1 negative
- **Behavior:** Lowers the target's Speed attribute by a skill-supplied amount.
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:14; localization 速度属性降低

### 18 - All Attributes Reduced

- **Type:** -1 negative
- **Behavior:** Lowers all four of the target's attributes by a skill-supplied amount (Affected By DES).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:15; NewSkillInfo ST1 ID1004 Rock Fire 'All Attributes Reduced'

### 19 - ATK Attribute Increased

- **Type:** +1 positive
- **Behavior:** Raises the bearer's ATK attribute (duplicate registry entry of 9; used by some skills, e.g. Blazing Slash).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:16; NewSkillInfo ST1 ID1040 Blazing Slash uses buff 19

### 20 - DEF Attribute Increased

- **Type:** +1 positive
- **Behavior:** Raises the bearer's DEF attribute (duplicate registry entry of 10).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:17; localization 防御属性提高

### 21 - DES Attribute Increased

- **Type:** +1 positive
- **Behavior:** Raises the bearer's DES attribute (duplicate registry entry of 11).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:18; localization 破坏属性提高

### 22 - Spd Attribute Increased

- **Type:** +1 positive
- **Behavior:** Raises the bearer's Speed attribute (duplicate registry entry of 12).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:19; localization 速度属性提高

### 23 - Increase All Attributes

- **Type:** +1 positive
- **Behavior:** Raises all of the bearer's attributes (duplicate registry entry of 13).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:20; localization 所有属性提高

### 24 - ATK Reduced

- **Type:** -1 negative
- **Behavior:** Lowers the target's ATK attribute (duplicate registry entry of 14).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:21; localization 攻击属性降低

### 25 - DEF Reduced

- **Type:** -1 negative
- **Behavior:** Lowers the target's DEF attribute (duplicate registry entry of 15).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:22; localization 防御属性降低

### 26 - DES Reduced

- **Type:** -1 negative
- **Behavior:** Lowers the target's DES attribute (duplicate registry entry of 16).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:23; localization 破坏属性降低

### 27 - Spd Attribute Reduced

- **Type:** -1 negative
- **Behavior:** Lowers the target's Speed attribute (duplicate registry entry of 17).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:24; localization 速度属性降低

### 28 - All Attributes Reduced

- **Type:** -1 negative
- **Behavior:** Lowers all of the target's attributes (duplicate registry entry of 18).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:25; localization 所有属性降低

### 42 - Soldier HP Increased

- **Type:** +1 positive
- **Behavior:** Raises the bearer's Soldier HP attribute by a skill-supplied amount (boosts both effective HP and healing, which scales off HP).
- **Stacking:** Same-type highest; cross-type adds.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:38; localization 士兵生命属性提高; Game-Hints.md (healing scales off Soldiers' HP)

## Other / Special States

### 89 - Eternal

- **Type:** 0 neutral
- **Behavior:** Eternal: 'Attribute Will Not Be Changed' -- the bearer's attributes are locked so they cannot be raised or lowered (immune to attribute buffs/debuffs) for the duration. Does not block CC or DoT.
- **Stacking:** Refreshes duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:55; NewSkillInfo ST1 ID77 Angel Blesse 'In An Eternal State,Attribute Will Not Be Changed'

### 113 - Concentration

- **Type:** +1 positive
- **Behavior:** Concentration (Focus): the bearer is Immune to Disarm/Silence/Stun/Chaos/Taunt during its turn -- it ignores those control effects while acting, but does not remove or block them from being applied.
- **Stacking:** Refreshes duration.
- **Magnitude:** Carried by the applying skill's Effect/Buff string; final damage/heal formula is UNKNOWN_SERVER_SIDE (combat is server-authoritative).
- **Evidence:** Buff.csv:61; NewSkillInfo ST1 ID14 Field 'In A Focused State,Immune: Disarm, Silence, Stun, Chaos, Taunts'; Status-Effects.md (Immune/Concentration)

---
*Catalog of inputs/rules only. The damage and healing formulas themselves are `UNKNOWN_SERVER_SIDE`. Regenerate with `python notes/sim/_build_status_effects.py` then `python notes/sim/_build_status_effects_md.py`.*
