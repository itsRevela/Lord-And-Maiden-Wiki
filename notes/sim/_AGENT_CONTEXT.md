# Shared context for battle-simulator decode agents

We are decoding the Unity game **Lord and Maiden** to build a battle simulator.
Repo root: `C:\Users\revela\Documents\Python\Lord-And-Maiden-Wiki`

## Sources
- `data/csv/*.csv` — game configs (the source of truth).
- `data/localization.json` — `{token: {"English_Text": ...}}` for `{...}` tokens.
- `decompiled/Assembly-CSharp/eb46ed1b3cbb.decompiled.cs` — main game C# (172k lines).
- Other DLLs: `decompiled/*.cs`.
- Existing wiki (already verified): `wiki/**` — reuse, don't contradict.
- Reuse `tools/wikigen/resolver.py` helpers: `clean()`, `effect_name()`, `effect_value()`,
  `expand_effects()`, `skill_name()`, `buff_name()`, `hero_stat_at()`, `is_named_hero()`,
  `hero_role()`. **Read resolver.py first.**

## HARD RULES (violating these corrupts the data)
1. Parse CSV with `csv.DictReader` + `encoding="utf-8-sig"`. Fields contain quoted commas —
   `awk`/`grep`/`split(",")` give WRONG columns. Never split CSV on commas.
2. The Windows console is **cp1252 and cannot print CJK**. Write ALL output to UTF-8 files
   (`io.open(path,"w",encoding="utf-8")`). Never print Chinese to stdout.
3. **NEVER GUESS.** Cite the exact `file:row` or `decompiled:line` for every claim. If a
   value or behavior is resolved server-side and absent from the client, write the literal
   string `"UNKNOWN_SERVER_SIDE"` with a short note. Do not invent numbers.
4. Output JSON must be strict (`json.dump(..., ensure_ascii=False, indent=2)`).

## Verified enums (use these; confirm/extend, don't re-derive)
- **Skill type (`ST` column; also HeroInfo skillN_type):** 1=Strategic, 2=Tactical, 3=Passive, 4=Pursuit.
- **EntryEffect** (`EntryEffect.csv`): `DataType` 1=flat (`+val`), 2=percent (`pct = val/Size*100`).
  Hero stats: **50=ATK Spd (Speed), 51=ATK, 52=DEF, 53=DES/Ruin, 54=Soldiers Quantity**.
  Soldier flat 5/10/15/20=HP/ATK/DEF/DES; soldier % 25/30/35/40/45=HP/ATK/DEF/DES/MarchSpd.
- **Buff.csv** = status-effect / stat-mod registry. `Type` 1=positive, -1=negative, 0=neutral.
- **Skill `Effect` string** (`NewSkillInfo.Effect`): one or more 12-token groups joined by `+`.
  Layout (correlate with `Des_en` to confirm every position):
  `actionType _ fromRound _ targetCategory _ targetCount _ ? _ coefficient _ ? _ ? _ ? _ ? _ ? _ ?`
  Known actionType: 101=ATK enemy, 102=heal/restore, 121=purify/cleanse.
  Known targetCategory: 2=enemy, 4=our troops (multi), 7=own/self. `fromRound` 0 = from round 1.
- **HeroInfo.csv:** id,name,type(race 1/2/3),rare(star),RST,RPoint,attack,defense,ruin,speed,
  *_grow, skill0_type/id (MAIN skill), skill1_type/id + skill2_type/id (modular slots), icon, name_en.
- **Race:** 1=Human, 2=Orc, 3=Elf (from TroopsEffect type 2). **Soldier type:** 1=Infantry, 2=Archer,
  3=Cavalry, 4=Chariot (SoldierInfo.type).
- **HERO_CARDS = {81,82,83,102}** are NOT heroes (filler cards) — exclude from hero lists.

## Combat reality (established)
Combat is **server-authoritative**: the exact damage equation is NOT in the client. The client
receives a replay log (`FightBehaviour`/`BehaviourRet`: TargetPos, RetType, RetVal, HPRate). So the
client exposes every INPUT (stats, skill coefficients, trigger rates, durations, targets, combo
effects, status effects) and the stated RULES, but not the hidden damage formula. Catalogue inputs
and rules faithfully; mark the formula itself `UNKNOWN_SERVER_SIDE`.

## What to return to the orchestrator
Only: (a) a ≤200-word summary, (b) the output file paths you wrote, (c) a bullet list of every
`UNKNOWN_SERVER_SIDE` item you hit. Keep your reply short — the JSON/notes files are the deliverable.
