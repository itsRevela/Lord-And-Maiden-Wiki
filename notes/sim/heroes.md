# heroes — decode notes

Outputs: `data/sim/heroes.json`, `data/sim/portraits.json`.
Generator: `notes/sim/_gen_heroes.py` (re-runnable; reads only `data/csv/*.csv` +
`tools/wikigen/resolver.py`, writes the two JSON files).
Cross-checked against `wiki/Heroes/Hero-Leaderboards.md`, `wiki/Heroes/Heroes.md`,
and the already-decoded `data/sim/troops_meta.json` (RST / restraint / preferred-soldier).

All `file:row` are `csv.DictReader` data-row indices (raw line = row + 2).
Decompiled cites are line numbers in
`decompiled/Assembly-CSharp/eb46ed1b3cbb.decompiled.cs`.

## 1. Source schema — `HeroInfo.csv`
250 rows. Fields (verified vs the `HeroInfo` POCO `[XMLExtension]` map, decompiled:2701-2760):
`id, name, type(race), rare(star), RST, RPoint, attack, defense, ruin, speed,
attack_grow, defense_grow, ruin_grow, speed_grow, skill0_type/id (MAIN),
skill1_type/id + skill2_type/id (modular slots), icon, name_en`.

Enums (all from resolver.py / verified): race `type` 1 Human / 2 Orc / 3 Elf
(`GetHeroRaceDesTip` decompiled:7857) — **confirmed**. RST 1 Infantry / 2 Archer /
3 Cavalry / 4 Chariot (same space as `SoldierInfo.type`). Skill type 1 Strategic /
2 Tactical / 3 Passive / 4 Pursuit. Role (HeroJob) 1 DPS / 2 Heal / 3 CC / 4 Buff /
5 Debuff.

## 2. Roster taxonomy — every row tagged
| category | count | is_named_hero | playable | what it is |
|---|---|---|---|---|
| `named_hero` | 113 | true | true | real recruitable heroes (in HeroDes) |
| `filler` | 5 | true | **false** | ids 41-45 "Unknown Brave/Mage/Shooter/Pikeman/Swordsman" — in HeroDes but uniform 28/28/28/28 base, 0.7 grow tutorial shells |
| `card` | 4 | false | false | ids {81,82,83,102} — Universal Advanced / Codex / Skill Exp / Breakthrough cards (HeroDes placeholders, not heroes) |
| `ai_unit` | 128 | false | false | id ≥ 1000 — AI/enemy formation units (decompiled:9794 `AIIsBoss`) |
| **total** | **250** | | | |

- **Named heroes = 118** (113 playable + 5 Unknown filler). This matches the wiki's
  "118 heroes" — `wiki/Heroes/Heroes.md` and the leaderboard include the 5 Unknown
  rows. The simulator-selectable roster is **113** (Unknown excluded per task).
- `is_named_hero` follows `resolver.is_named_hero` (present in HeroDes, not a card).
- AI units (id ≥ 1000) break down as: 1001-1009 named beasts/bosses; 1010-1099 generic
  tiered enemy waves (Barbarian / Elf / Goblin / Skeleton / Frost / Shark / Sky, each
  3★/4★/5★ + a Leader); 2000-2029 named story/boss characters; 3001-3020 elite
  world-boss monsters. These are enemy/AI rosters, not summonable heroes.

## 3. Stats — base, grow, and Lv80 (level argument CONFIRMED)
`stat(L) = base + floor(grow × L)` (resolver.hero_stat_at). **Max level = 80**
(`HERO_MAX_LEVEL`; UpExp type 2 spans 1..80).

**Lv80 uses level = 80, NOT 79.** Verified against `wiki/Heroes/Hero-Leaderboards.md`,
which is generated with `R.hero_stat_at(base, grow, HERO_MAX_LEVEL)`
(`tools/wikigen/build_extra.py:948-951`). The published numbers reproduce with
**level=80** exactly:
- Saintess Shin (id 2): ATK 44 + floor(1.1×80)=132, DEF 64+floor(1.6×80)=192,
  Ruin 80+floor(2×80)=240, Spd 44+floor(1.1×80)=132 → 696. Matches leaderboard.
- With **level=79** it would be 44+floor(86.9)=130 → no match.
Spot-checked Roland (240/195/151/108), Mousika (180/120/210/186), Nyx (210/144/126/216),
Crolos (162/177/112/121) — all match the leaderboard. So `maxed_lv80` in the JSON uses
`level=80`.

`maxed_lv80` is the **bare growth curve only**. It EXCLUDES free stat points (RPoint
preset / breakthrough), talents, gear, relics, runes, affection, and team-comp bonuses.
Final combat power and the damage formula are server-authoritative
(`UNKNOWN_SERVER_SIDE`).

## 4. Skills
`main_skill` = skill0 (`skill0_type`,`skill0_id`). `modular_default` = [skill1, skill2]
(the two swappable/modular slots). Each is `{st, st_name, id, key:"st.id", name_en}`,
names via `resolver.skill_name`. A `0/0` slot is omitted. Skill IDs cross-reference
`data/sim/skills.json` by the same `st.id` key. Spot-checked Roland: Epee Storm (2.67) ·
Endless Destroy (2.61) · Thorn Cross (2.102) — matches `wiki/Heroes/Heroes.md`.

## 5. RPoint — what the `0,0,0,0`-style field means
**RPoint is the hero's free stat-point allocation preset** — the 4 comma-separated
floats are per-stat fractions `[ATK, DEF, Ruin, Speed]` (PointItem ID map from
`RePoint()` decompiled:80873-80889: 0=ATK 1=DEF 2=Ruin 3=Speed).

It is NOT a per-soldier-type stat split and NOT an adaptation/restraint value. It is
the value behind the in-hero **"Reset / Recommend points"** button
(`{待分配点}` = "Points to Allocate"). The data is **not** uniformly `0,0,0,0` — across
250 rows there are 18 distinct presets; only **9** rows are `0,0,0,0`. Common ones:
`1,0,0,0` (100% ATK, 57 heroes — DPS), `0,1,0,0` (100% DEF, 28), `0,0,0,1` (100% Speed, 18),
`0,0.6,0,0.4` (60% DEF / 40% Speed, 21), `0.7,0,0.3,0` (70% ATK / 30% Ruin, 28),
`0.4,0.6,0,0` and `0.4,0,0.6,0` (23 each).

Two code paths consume it (identical logic):
- **Player UI** `RePoint()` (decompiled:80853-80918): if any value ≠ 0, set each stat
  slider to `ReMainPoint × frac`, with Speed (index 3) taking the remainder.
- **AI build** (decompiled:10437-10477): `num4` (advancement·10 + level-1 +
  breakthrough·{3|5}) is split by RPoint into `Add_AD/Add_DEF/Add_Dmg`, Speed = remainder.

**All-zero fallback** (decompiled:80892-80916 & 10459-10477), keyed off **RST**:
| RST | fallback split |
|---|---|
| 1 Infantry | 60% DEF, remainder Speed |
| 2 Archer | 80% ATK, remainder Ruin |
| 3 Cavalry | 60% DEF, remainder ATK |
| 4 Chariot | 60% Ruin, remainder ATK |

The JSON stores `rpoint.raw`, `rpoint.values`, and the resolved `rpoint.distribution`
(`mode` = `explicit_preset` or `rst_fallback`). 241/250 rows are explicit; 9 fall back.

### Does a hero gain anything extra for fielding its RST soldier type?
**No inherent per-hero bonus.** RST does two things client-side:
1. Sets the single soldier type the hero commands: `hero.SoldierT = heroInfo.RST`
   (decompiled:10428, 17380-17392). A hero is locked to one soldier type = its RST.
2. Seeds the empty-RPoint default stat-point split (table above).

The real soldier-type payoff is **team-level**, and it is already decoded in
`data/sim/troops_meta.json`:
- `soldier_combinations` (TroopsEffect type 1): 2 heroes sharing a soldier type →
  Basic bonus, 3 → Advanced bonus (e.g. 3 Archers → Soldier ATK +10%, Soldier DEF +10%).
- The **restraint triangle** (Infantry→Archer→Cavalry→Infantry; Chariot has none)
  gives restrained soldiers **−25% damage dealt** — a stated rule applied server-side
  (`troops_meta.json.restraint.restrained_damage_modifier.application` =
  `UNKNOWN_SERVER_SIDE`; no client-side 0.75 multiplier exists).
So: no, a hero does not get extra stats merely for using its RST-matching soldier type;
benefits come from team composition and the restraint matchup, not from RST alone.

## 6. Portraits — `portraits.json`
Per hero id → portrait/head sprite asset references. **Keyed by `icon`, not id**
(usually equal, but the loader uses `HeroInfo.icon`).

Asset-path scheme from `GetHeroHeadImg` (decompiled:9744-9792):
| ref | logical path | notes |
|---|---|---|
| full head | `Hero/{icon}/Head_{icon}_{skinId}` | skinId 0 = default skin |
| chibi head | `PlayerHead_Q/QHead_{icon}_{skinId}` | small "Q" version |
| alt skin | `HeadImg > 10000` → skin `num = HeadImg/10000` → `Head_{icon}_{num}` | |

These are **YooAsset logical addresses** passed to `LoadAssetSync<Sprite>()`, not files
on disk. `HeroPosInfo.csv` (keyed by `HeroIcon` == `icon`) supplies the on-screen layout
for the big portrait (posx/posy/size/effect anchors/on-click event), NOT an image
filename; its row is attached as `pos_info`.

### Where the portrait images actually are (and how to get one)
- Sprites live inside the game's bundles at
  `<LAM install>/Lord and Maiden_Data/StreamingAssets/yoo/DefaultPackage/*.bundle`
  — **1278 plain `UnityFS` bundles, unencrypted** (see `notes/01-recon-and-encryption.md`).
- The repo's `extracted/bundles_assets/` directory **exists but is EMPTY** — only the
  XML config TextAssets were ever extracted, not the sprites. **So portraits are NOT
  currently available as plain files.**
- To extract: open the bundles with UnityPy / AssetStudio and pull the `Sprite`
  (or backing `Texture2D`) named `Head_{icon}_0` (full) / `QHead_{icon}_0` (chibi).
  No decryption needed.
- `UNKNOWN` until extracted: the exact `.bundle` file containing a given icon's sprite —
  resolve via the YooAsset `OOY` manifest's asset-path → bundle map.

## 7. UNKNOWN_SERVER_SIDE / open items
- Final hero combat power and the **damage formula** — server-authoritative.
- **RST restraint −25% application** — stated rule, computed server-side
  (`troops_meta.json.restraint`).
- Any **RST-matching "preferred soldier" stat bonus** beyond fielding the type — none
  found client-side; if it exists it is server-side
  (`troops_meta.json.preferred_soldier.matching_bonus_magnitude`).
- **Portrait image bundle mapping** — needs UnityPy extraction (see §6).
- **Summonable vs story/AI-only:** determinable from the taxonomy — the 113 playable
  named heroes are the recruitable roster; the 5 Unknown rows are tutorial filler;
  cards {81,82,83,102} are upgrade items; all id ≥ 1000 are AI/enemy/boss units (not
  summonable). The exact gacha/recruit *pool* per hero (which banner each comes from)
  is not in HeroInfo and was not required here — it would need `Pay.csv` / recruit-pool
  tables and is otherwise server-driven.
