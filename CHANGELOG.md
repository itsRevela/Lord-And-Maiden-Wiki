# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **Quests/Knowledge-Quiz.md** — documents the daily Knowledge Quiz event (Fantasy Plaza,
  once/day, timed multiple-choice, Life-Point rewards, share-to-chat help feature granting
  Friendship Points up to a daily cap). Investigation confirmed the **question bank is
  server-delivered** (`SCLogic_GetRandomQuestion` reads every question/option/answer from the
  network; localization holds only UI labels), so the actual questions/options/answers are
  **not in the client files** and cannot be data-mined — the page states this explicitly
  rather than guessing. README badge → 186.
- **Servers, Worlds & Regions** section (from a 2-subagent decompiled-code investigation):
  - **World/Servers-and-Realms.md** — the server/realm model (Group-N clusters, status
    lights, NEW/HOT badges, per-server characters, no client transfer), cross-server chat
    channels, the cross-server-mode age gates (Ruins 7d / Divine Demon Trial 10d / Abyss
    14d / Primordial Boss 30d / Friends 30d), and the full 10-point server-merge rules.
  - **World/Great-World.md** — answers "is a World a Region?" definitively: **no** — the
    Great World is the whole shared **193×193 grid**, a **Region** is one ~20.5-unit grid
    cell (the "nine-square grid" = a 3×3 region block). Plus map composition (data-derived
    tile counts: ~119k objects — resource nodes, 73 NPC cities, 9 bosses), Sphere-of-
    Influence/occupation rules, siege rules, and the level-6-keep unlock gate.
  - The community "servers 1–3 mobile / 4+ shared" claim is attributed as community
    knowledge (not found in the client). README badge → 185 pages.
- **Shop & Market documentation overhauled** (from a 3-subagent decompiled-code
  investigation). The game's **Market** (MarketPanel) and **Shop** (ShopPanel) are
  distinct panels, now documented as two pages:
  - **Items/Market.md** — the 13 currency-exchange tabs given their real names
    (Manor, Gem, Alliance/Union, Friendship, Honor/Arena, Tournament/Courage,
    Festival, Wilderness, Lord, Life, Meteoric Iron, Island) with per-tab currency,
    **restock cycle** (weekly Mon / monthly 1st / daily / one-time), per-item unlock
    gates, and notes on the server-driven Traveling Merchant & Kuroland tabs.
  - **Items/Shop.md** — the recharge/gift packs, correctly priced in **Rand Coin**
    (real money → Rand Coin → packs), grouped by their real `gift_type` categories,
    with `refresh_type` reset windows, plus a "Related shops" section (Hero Skin Store,
    Gift Codes, Lucky Wheel/Box, Travelogue Merchant, Public Square Active Store).
  - All mechanics (refresh cadence, limit-reset semantics, per-tab gate meaning, the
    Rand-Coin two-tier model, skin dual-currency) are grounded in the decompiled
    `MarketPanel`/`ShopPanel`/`GetEntryDes` code.
  - Replaces the old flat `Shops.md` / `Recharge-Packs.md`; references updated across
    the Overview, Glossary, Spending Guide and README.
- Hero Leaderboards **"By Role"** section — every hero grouped by role (DPS/Heal/CC/Buff/
  Debuff/Other), ordered by Total stats within each role.

### Fixed (from a 4-subagent inconsistency sweep)
- **Attribute bonuses now render flat vs percent correctly.** `expand_effects` ignored the
  EntryEffect `DataType`; it now matches the in-game `GetEntryDes` formula — DataType 1 = flat
  `+N`, DataType 2 = `+(N/Size×100)%`. E.g. Long Sword reads "Soldier ATK +1, Soldier ATK +2%"
  (was "×1, ×200"). Affects Equipment and Item Collections.
- **Excluded 4 non-hero "card" items** (Universal Advanced/Codex Card, Skill Exp Card,
  Breakthrough Card — placeholder 58/58/58/58 stats) from the hero roster, leaderboards and
  AI-hero list; the real playable count is **118**. Removed their stale roster pages.
- **Unlimited limits now show ∞** (Shops Buy Limit, Recharge Limit, Relic Daily Runs) — the
  `_dash(...) or "∞"` idiom was dead code that always rendered "—".
- Hero Skins price relabeled **Price (Rand Coin)** with a note (skins use Rand Coin or a Hero
  Skin Scroll, not Gems — verified against the decompiled skin-purchase code).
- Removed inaccurate "(seconds)" claims on Crafting and Stats-and-Formulas (those Time columns
  render human-readable durations).
- Buff **Type 0** now labeled "neutral (0)" and documented in the legend.
- VIP "EXP Req." labeled **(cumulative)**; Shops intro no longer claims every shop has a single
  identifying currency (Shop 1 uses two); README badges updated (182 pages, 118 heroes).
- **Glossary greatly expanded** (17 → ~70 terms + a 16-row currency table), reorganised into
  six categories (Stats & hero terms, Battle & skills, City/economy/troops, Progression &
  collections, PvE/World/Alliance, Currencies). Driven by a 4-subagent sweep of the whole
  wiki for newcomer-ambiguous jargon; every definition is grounded in the wiki/data
  (uncertain terms were left out rather than guessed). Added e.g. Commander/Striker,
  troop restraint, wound states, Impact/Init/+Lv, Real damage, Splash, Vit vs Stamina,
  Great World, Union, Lord/Lord Level, Prestige, Title/Astral Badges, Territory tiers,
  Integral, Sphere of Influence, and a name-aliases note (Chase=Pursuit, Strategy=Strategic, …).

### Fixed
- Glossary "Ruin / DES / DMG" entry rendered with stray backslashes (`Ruin \ DES \ DMG`) due
  to invalid escapes in the generator — now correct.
- Maidens page header was inaccurate ("higher weight = stronger"): Weight is the inverse
  summon draw-weight (★6 = 1, ★1 = 30); corrected to clarify rarity drives strength.
- Added **Stun** to the Status Effects page (it appears throughout skills but was missing).
- **Strategy & Guides** — 8 community-strategy pages rebuilt (in the wiki's voice, with
  attribution) from Lofthouse's archived Steam guides, kept in a separate `build_guides.py`
  module and clearly banner-marked as player knowledge rather than extracted data:
  Battle Mechanics, Status Effects, Team Building, Build Order & City Hall Progression,
  Territory Wars & Raids, Event Schedule, Prestige/Titles/Troop-Armour, and Spending &
  F2P Tips. Information from the guides' screenshots was transcribed (no images reproduced)
  and cross-checked against the data where possible — e.g. the in-battle **Attack
  composition** worked example was verified (`204×1.03 + (90+81) = 381.12`, and the troop
  value 90 matches a real SoldierInfo stat), and the City-Hall-25 progression is confirmed
  by `need_build`. The root README gained a "Strategy & Guides" navigation block.
- **Game Overview & Getting Started** page (grounded intro, core-systems hub,
  currency glossary, feature-unlock order).
- **Hero Stat Leaderboards (Lv 80)** — computed end-game stats for all 122 named
  heroes: Top-15 by ATK/DEF/Ruin/Total plus a full sortable table.
- Skill Catalog **"Used by"** column (reverse index of which heroes carry each skill).
- **Cumulative Costs (to Max)** — total resources + time to max every building and
  to fully complete the tech tree (independently cross-checked).
- **Equipment / Gear** page — all player gear (PropInfo type 3) by slot, with
  decoded attribute bonuses (via the EntryEffect catalog) and Power.
- **Glossary** — stat abbreviations and game-specific jargon (Ruin/DES/DMG, RST,
  Power composition, troop types, currencies, …).
- Hero pages now cross-link to the recommended teams and codex sets that feature
  them, plus the Lv 80 leaderboards.
- Campaign page gained an **Enemy Lv** column (decoded from the AI-formation params).

### Changed
- Rewrote the root `README.md` as a proper wiki landing page: welcome, "Start here"
  quick links, browse-by-category navigation into every section, link to the full
  generated index, an accuracy statement, and a condensed "how it's built" section.
- Hero Codex set bonuses are now decoded (e.g. "Infantry HP +2") instead of showing
  raw `EffectType`/`EffectVal`; required heroes link to their pages.
- Skill Catalog gained a legend for the `Max Use` / `Ready Rd` columns.
- `verify.py` now also validates the root README's links so page renames can't silently
  break the front page.
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
