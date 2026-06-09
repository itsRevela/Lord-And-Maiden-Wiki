# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **Game Overview & Getting Started** page (grounded intro, core-systems hub,
  currency glossary, feature-unlock order).
- **Hero Stat Leaderboards (Lv 80)** — computed end-game stats for all 122 named
  heroes: Top-15 by ATK/DEF/Ruin/Total plus a full sortable table.
- Skill Catalog **"Used by"** column (reverse index of which heroes carry each skill).
- **Cumulative Costs (to Max)** — total resources + time to max every building and
  to fully complete the tech tree (independently cross-checked).
- **`tools/wikigen/build_extra.py`** — 19 additional wiki pages covering every
  remaining player-facing config: feature/building unlock gates, item sources,
  shops, recharge/gift packs, choice chests, gift-code rewards, relic dungeons,
  warlord challenge, NPC cities, wilderness/world boxes, world & naval structures,
  hero skins, reward boxes, minigames, dating events, avatar frames, AI equipment,
  chat emojis.
- **Crafting → Quick-Add Yields** section (FormulaQuickAdd) — the last uncovered
  content config.
- Per-hero **"Related pages"** cross-link footer (roster → talents / skins / skill catalog).
- `resolver.desc()` — display helper for in-game effect strings that use `_` as a
  label→value separator and `$` between entries.
- Translation tables for source columns the game ships only in Chinese
  (gift-code categories, AI equipment set names, five buff names, one skill clause).
- `verify.py`: now scans for untranslated CJK and catches negative-id placeholders (`#-1`).

### Fixed
- `resolver.skill_name` / `buff_name` used lowercase column keys (`name_en`) while
  `NewSkillInfo` / `Buff` use `Name_en`; skills rendered blank in Recommended Teams.
  Now case-tolerant.
- `resolver.need_build` only resolved the first token of multi-requirement strings
  (`10_4+18_4` → `Academy Lv 4+18_4`) and produced a dangling `Lv ` for the bare-id
  form used by `ScienceInfo`. Now resolves every requirement and the bare-id form.
- Full-width CJK punctuation (`：、～`) leaking from machine-translated source fields
  is normalised to ASCII; runs of whitespace are collapsed.
- `Build#-1` sentinel in Feature Unlocks now renders as "Special / Event".
- Dropped the always-empty "Skills" column from the AI/Enemy Heroes table; skipped
  empty Tips sections.
- Relic-dungeon / warlord enemy columns condensed from per-wave dumps to unique
  units + enemy level.

### Verified
- All numeric tables independently recomputed by audit subagents:
  ~11,000+ cells across heroes (Lv 1–80 growth for all 122), buildings, soldiers,
  research, VIP, favorability, ship, and crafting — **0 discrepancies**.
- Growth formula `stat(L) = base + floor(growth × L)` and RST point-allocation
  confirmed against decompiled game code.
- `verify.py`: 0 broken links, 0 unresolved id placeholders, 0 localization tokens,
  0 untranslated CJK.

## [0.1.0] — initial extraction

### Added
- Data pipeline: extracted 92 XML/CSV configs, 8 ScriptableObjects, and a merged
  `localization.json` (9,983 keys) from the Unity game files (YooAsset bundles +
  HybridCLR `.rawfile` DLLs decompiled with ilspycmd).
- `tools/wikigen/` generator (`resolver.py` + `build.py`) and `verify.py` integrity checker.
- 154 generated wiki pages: heroes (master + 122 per-hero), skills, AI heroes,
  maidens, items, buildings, soldiers, research, crafting, mechanics, formulas,
  talents, VIP, favorability, ship, outfits, buffs, troop combos, codex/collections,
  recommended teams, alliance research, bosses, campaign, trials, world map, quests,
  story, tips, attribute catalog.
- `notes/` documenting recon, the (absent) encryption, and formulas/mechanics.
