# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **Knowledge-Quiz answer monitor** (`tools/lam_question_monitor.py`) — a live scanner that
  reads the (unencrypted) server→client stream and, on each daily-quiz question, prints the
  correct answer; it self-learns and runs until stopped.
  - **`tools/lam_question_capture.py`** — Phase-1 raw capture + best-effort decoder, built to
    verify the protocol before the monitor. Reuses the battle sniffer's TCP framing / gzip /
    `Proto` / flow-reassembly stack.
  - **Protocol (reverse-engineered from `eb46ed1b3cbb.cs` + a live capture):** the quiz pushes
    `SCLogic_GetRandomQuestion` with the question and every option sent as `{translation-key}`
    strings (resolved via `data/localization.json`) — and **no correct-answer id**. The answer
    is only revealed *after* you submit, in `SCLogic_SelectQuestionAnser` (`rightId`). Verified
    byte-exact (`_unparsed_tail_bytes == 0`).
  - **Answer engine:** canonicalises each question/option to its Simplified translation key
    (language-proof), looks the answer up in `data/quiz_answer_key.json`, and **learns** every
    revealed `rightId` by correlating it with the last question — so coverage grows toward the
    full pool with play. Bootstrapped from a captured Mia→Vanessa answer.
- **Prop (item) asset extractor** (`tools/extract_prop_assets.py`) — pulls all 676 item icons
  and the 7 rarity backdrops (`PropBox/0–6`, `5` = gold ★5) + ★5/★6 glow layers from the
  bundles to `extracted/assets/props/`, with an `index.json` mapping every prop → icon + backdrop.
- **Battle Simulator** (`simulator/`) — a configurable, multi-core Monte-Carlo model of
  the game's 3v3, 8-round combat that ranks the best build for a chosen 3-hero formation.
  - **Phase-1 catalogue → `data/sim/*.json`** (machine-readable): all 416 skills (decoded
    12-token `Effect`/`Buff` layout: actionType/fromRound/targetCat/targetCount/coef…),
    76 status effects with behaviours, equipment/accessories/relics/runes/skill-awaken maxed
    values, troop T6 stats + soldier & race combination effects + affection + talents, 113
    playable heroes (maxed Lv 80 stats, skill loadout, RST), and the combat-rules model.
    Cited reference docs live in `notes/sim/*.md`.
  - **Key finding:** combat is **server-authoritative** — the client only replays a battle
    log (`FightBehaviour`/`BehaviourRet`), so the exact damage formula is **not** in the
    client. The simulator is therefore a *transparent* rules-based model; every server-side
    unknown is a documented, tunable `ModelConfig` knob (tagged `ASSUMPTION`), and rankings
    are model-relative but comparable across builds.
  - **Engine** (`simulator/engine/`): maxed-build aggregation + a scale-free exchange damage
    model (troops = HP), an 8-round resolver with the **rematch** mechanic (undecided after 8
    rounds → fresh bout, troop counts carried over, until a commander is wiped), turn order by
    ATK Spd, activation order Passive→Strategic→Tactical→Normal→Pursuit, restraint ×0.75,
    20/40/40 targeting, status effects; and a combinatorial multi-core search (commander ×
    troop combos × opponent pool) ranked by win rate and early/mid/late/all damage windows.
    Validated unbiased (mirror match ≈ 50 %).
  - **UI:** Next.js dashboard (hero pickers with datamined portraits, commander toggle,
    options, live progress, ranked results, JSON export) + a Flask API + a UnityPy portrait
    extractor (113/113 heroes). Combat catalogue → proper wiki pages is the remaining step.
  - **Simulator redesign (Phase 2)** — reframed the search around the question players actually
    ask: *with my fixed 3 heroes and commander, which skills / matching skill-stone / gear give the
    highest win-rate (or lowest casualties)?*
    - **Gear-component system** (`data.gear_bonus_from_selection`): the flat gear bonus is now
      decomposed into selectable, per-hero components — a max-tier **armor set** (slots 1-6 + its
      3-/6-piece bonus), a **magic messenger** (slot 11), and **two accessories** — plus an
      always-on hero **relic** and skill-aligned runes. A single hero's two accessory slots can't
      hold the same item (cross-hero duplicates are fine). Applies to **both** the player's
      formation and opponents; the old flat path remains as a fallback.
    - **Genetic optimizer** (`engine/optimize.py`): fixed commander + per-hero stat allocation;
      toggleable search axes (troop · modular skills · skill stone · armor · messenger ·
      accessory — relic always equipped); 5★/max-tier pools only with no empty slots; win or
      casualty objective; ranked top-N with a per-build drill-down (allocation, main/modular skills,
      stone, armor set, messenger, accessories, relic).
    - **Challenging-opponent generator** (`engine/opponents.py`): a "Generate challenging opponents"
      button builds a cached pool — stage A ranks hero trios with a strong fixed build, stage B
      genetically optimizes the top-X into fully-geared formations — cached to disk
      (`simulator/opponent_cache.json`, survives restart) and loaded as the search's opponent pool
      (falls back to a sampled set when absent). API: `GET /api/opponents`,
      `POST /api/generate_opponents`. Exhaustive enumeration (~10²⁴ battles) is infeasible, so the
      two-stage approach is by design.
    - **Translation fix:** skill display names now resolve via the game's authoritative
      `Language_SkillName.csv` (corrected 5 drifted names, e.g. *Devout → Piety*), so UI builds
      match the in-game skill names. Four calibration anchors held across the redesign
      (testcase 7/9, dot 5/7, shield 3/6, pursuit ~88%).
- **Reference/Game-Hints.md** — catalogues the game's in-game hint/help systems (Hero Info →
  Details per-hero, loading-screen Tips, feature "?" buttons, skill/talent tooltips, system
  pop-ups) and consolidates the **battle rules & calculations** they reveal. Surfaces several
  clarifications not previously captured (from `Language_SysTip`): "Affected by X attribute"
  refers to the **caster**, **healing scales with Soldiers' HP**, "**2 of our troops**" = 2
  *other* allies, **5★ summon rate-up = 50%** it's the featured one, Codex submission destroys
  the hero/item, World-level EXP cap, siege auto-bombard, etc. Cross-linked to Battle Mechanics,
  Skill Stones, Hero Advancement and Tips. README badge → 191.
- **Hero Equipment, Skill Stones, Left/Right Accessories, and Hero Advancement** — four
  interlocking hero systems, from a 3-subagent decompiled-code investigation:
  - **Items/Equipment.md** rebuilt into the full **Hero Equipment** reference: the 8 gear
    slots, a new **Set Bonuses** section (28 sets, 3-piece/6-piece, decoded from the
    `timeinfo` field), **Left vs Right Accessory** slots labelled with their offense/defense
    split, the Magic Messenger slot, and upgrade(=re-craft)/obtain notes — on top of the
    existing per-slot catalog.
  - **Heroes/Skill-Stones.md** — the skill-stone system: a 4th skill slot per hero, customize
    chests (3★/4★/5★, 50-fragment combine), the strict equip rules (1 Strategic stone per team;
    +1 Tactical/Passive/Pursuit; no duplicate Strategic), Lv 1–5 + shared awaken, non-destructive
    unequip, and sources.
  - **Heroes/Hero-Advancement.md** — the Level → Advance → Breakthrough tracks: Advance (AdvLv
    to ★, +10 pts each, dupe costs 1/1/2/2/3 or Universal Advance Card, +max-soldier table),
    Breakthrough (★4/★5, Lv 60→80, +3/+5 pts each, Breakthrough Card), the stat-point formula
    `AdvLv×10 + (Lv−1) + (5 or 3)×BreakLv`, and the four advancement cards.
  - Added Glossary entries (Skill Stone, Advance/Breakthrough; clarified gear vs Codex "Set
    bonus"); linked from roster footers + README. README badge → 190. Server-side unknowns
    (exact dupe/upgrade costs) flagged, not guessed.
- **Heroes/Runes.md** — the Rune system, from a decompiled-code investigation. Runes are
  hero equipment (PropInfo type 9, 485 items = **105 kinds**) in a hero's **Rune slot**;
  each rune raises the **trigger chance of one specific Tactical/Pursuit skill**. Documents:
  one-rune-per-hero, **no set bonuses** (only PropType-3 gear has 3/6-piece sets), levels
  (★4 Lv1–4 / ★5 Lv1–5), must-be-max-to-equip, upgrade with **Runes-Fragment**, dismantle →
  fragment, and box sources (4★ Random: Abyss/Union War; 5★ Random: Union Store/Abyss/Union
  War; 5★ Customize: Tournament/Lucky Wheel/Mystery Box). Full ★5/★4 catalog of every rune's
  boosted skill + Lv1→max trigger bonus. Server-side unknowns flagged.
  - Data caveat handled: the rune `Effect` reuses EntryEffect #45 (mislabeled "Soldier March
    Spd"); the page uses the authoritative "Skill Trigger Probability" reading instead.
  - Added a Glossary "Rune" entry; linked from roster footers + README. README badge → 188.
- **Heroes/Relics.md** — the Hero Relic (equipment) system, from a decompiled-code
  investigation. Relics are per-hero artifacts (PropInfo type 5, 98 of them) that enhance
  the owning hero's **Talent Skill**, equipped in the hero's Relic slot. Documents the full
  lifecycle (obtain via Relic Summon / boxes / **50 Ruby → a chosen 5★**; **upgrade with
  duplicates** to max; **must be max level to equip**; **dismantle → Ruby**), the Lv1–4 (★4)
  / Lv1–5 (★5) scaling, the `★ × level × 1800` Score, and the Lord-13 unlock gate — plus a
  full ★5/★4 table of every hero's relic bonus at Lv 1 and at max. Server-side unknowns
  (exact upgrade dupe counts, Ruby yield, gacha rates) are flagged, not guessed.
- Distinct from the existing **Relic Dungeons** (World) page; the Glossary "Relic" entry was
  corrected (relics are hero Talent-Skill artifacts, not standalone companions). Linked from
  the per-hero roster footers and README. README badge → 187.
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

### Changed
- **Battle Simulator combat engine reworked to match real in-game mechanics**, validated
  against a transcribed in-game battle log ("Rosetta Stone", `data/sim/calibration.json`).
  The transparent/configurable design is kept — the server damage formula stays
  `UNKNOWN_SERVER_SIDE` and every server-side constant remains a documented `ModelConfig`
  knob (tagged `ASSUMPTION`); rankings stay model-relative. Why: the old scale-free exchange
  model could not reproduce the log's phase structure, casualty tiers, or buff dynamics.
  - **Phase structure:** added **Passive Exertion** → **Pre-War Preparation** (all Strategic
    skills + shields/attribute buffs-debuffs/prepared-CC/heal-over-time fire *before* round 1)
    → Rounds 1–8 (`simulator/engine/combat.py`).
  - **Casualty model:** per unit tracks Health / SlightWound / (Severe+Death); damage removes
    Health→Slight (a small share straight to Severe/Death), between rounds a share of Slight
    worsens to Severe/Death (lowers max), healing moves Slight→Health (blocked by Heal Ban);
    defeated at Health 0; per-unit Kills/Heal/Slight/Severe/Death tracked.
  - **Stalemate escalation:** undecided after 8 rounds → Stalemate → rematch with Health
    carried over **and** a stacking "All Hero DMG Dealt +33%/stalemate" buff.
  - **Buff engine:** general + per-channel DMG-Dealt/Taken multipliers (Star Shield, Noise,
    Green Tea, Tactical-DMG, stalemate, gear PVE/PVP DMG) that stack and dominate; attribute
    add/percent with "cannot be replaced"; durations + expiry.
  - **Prepared CC** (per-round re-roll: Silence/Disarm/Stun/Heal-Ban), **reactions/procs**
    (Assault flat Real-DMG pursuit, Counterattack 0.84×, Reactive Block, Tactical Burst,
    Purification), and **Aid/Taunt→Provoked** targeting.
  - **Damage model:** absolute-magnitude `coef·offence·troop_scale·def_mitigation·
    dmg_dealt·dmg_taken·restraint`; real/assault/splash ignore DEF; counter = 0.84×normal.
    Coefficients from `skills.json` maxedValue (+ wired relic Real-DMG/coef, rune, awaken).
  - **Magic Messengers (slot 11)** now feed hero ATK/DEF/DES + ATK Spd flats and PVE/PVP
    DMG-Dealt/Taken into the model via `data.py` `gear_bonus` (extended `_accumulate`).
  - **Validation:** new `simulator/validate_testcase.py` builds the exact two test-case
    formations, runs the match, and reports PASS/FAIL per ground-truth target to a UTF-8 file
    (CJK-safe). Currently **9/9 targets PASS**; mirror match stays ≈ 51 % (no side bias);
    `smoke_test` and the CLI search/optimise paths still run. `BattleResult`/`build_team`/
    `fresh_units`/`Battle.run()` interfaces preserved (back-compat `hp`/`hp_max` display
    aliases added) so the UI and search are unaffected.
- **Battle Simulator damage knobs re-fit to a SECOND in-game log + star-based troop counts.**
  Why: the model was originally fit to one shielded-tank fight; a new clean "Vanilla
  Baseline" mirror log (`notes/sim/calibration_1_baseline.md` / `_findings.md`) revealed (a)
  troop count is set by hero star, not a flat advance bonus, and (b) the DEF curve was too
  weak. The findings record that the user ran the mirror twice (one loss, one win), so the
  matchup is a **close coin-flip** — the +DEF commander only *tilts* it, it is not a
  deterministic enemy win.
  - **Troop count by star (FACT, `model.py build_team`):** 5★ = 55,000, 4★ = 51,000,
    3★ ≈ 47,000; **no commander troop bonus** (the old flat-55k + `commander_talent` +3,000
    was wrong). This alone dropped `validate_testcase.py` from 9/9 to 8/9 ("Aguria falls
    mid-B1" landed at the 49% boundary), which the damage re-fit below restores.
  - **Damage knobs re-calibrated to satisfy BOTH logs** (`ModelConfig`, all `ASSUMPTION`,
    values calibrated): `damage_global` 7.0 → **26.959** and `hero_off_weight` 1.0 → **0.20**
    (combined per-hit scalar `normal_attack_coef·damage_global = 24.263`, least-squares-fit to
    the log's 5 clean round-1 normal-attack readings, relerr ~3% — they land in the logged
    ~4,000–5,600 band); `def_ref` 900 → **600** and `hero_def_weight` 1.0 → **2.0** (a stronger
    DEF curve). The key tension — DEF strong enough to make the +DEF commander tankier yet not
    so strong it deterministically flips the mirror or breaks the shielded fight — resolves at
    a ~52% enemy-win coin-flip, because the shielded tank's survival is driven by **capped
    DMG-Taken-Reduced**, not DEF, so the DEF curve is orthogonal to that fight (`validate_testcase.py`
    stays 9/9; DEF-reduced Aguria still dies on schedule).
  - **New `simulator/validate_baseline.py`** builds Matchup-1's exact formations (Thiel 99 /
    Nicole 87 4★ / Dolly 108, Archer, player all +ATK vs enemy +DEF/+ATK/+DES) and reports
    PASS/FAIL per target to a UTF-8 file: **6/6 PASS** — close coin-flip (enemy win ~51%, target
    40–60%), +DEF commander tilts survival, single ~3.2-round battle, normals in band, kill
    leaders ≈ enemy Thiel top-2 / ally Dolly #1, both teams heavily attrited. Known gap: the
    engine ends a battle at commander death, so it leaves more striker troops standing than the
    log's near-total wipe (model ends ~22–25% Health vs log ~7%/12%); the heavy-attrition signal
    is faithful, the depth is not. The −15.08% DMG-Dealt-Reduced rider on Soul Bound/Radiant
    Slash (skill actionType 6) is small and left unmodelled. `validate_testcase.py` back to
    **9/9**; mirror ≈ 54%/46% (unbiased); `smoke_test` and the CLI `run` path still work.
- **Battle Simulator: real Burn/Curse DoT + sustain + Detonate, calibrated to a THIRD
  in-game log** (`notes/sim/calibration_2_dot.md` / `_findings.md`, "DoT Lab"). Why: the
  DoT channel was previously absent (a placeholder); this log gives the first real Burn/Curse
  tick data, so it is now modeled from the skills' own effect tokens.
  - **DoT tick (`model.dot_tick`, ticks at the before-action phase in `combat._dot_tick_phase`)**
    for the effect's duration on the skill's target count: `coef · offence(caster,"dot") ·
    troop_factor(caster) · dot_global · dot_def_mitig`. It scales with the **caster** (DES via
    the new `"dot" → "ruin"` channel-stat entry, reusing `offence`/`troop_scale`), is **linear
    in the printed coefficient** (Burn 1.0 ≈ 2× Curse 0.5), and is **mildly DEF-mitigated** (its
    own gentle `dot_def_ref/(dot_def_ref+DEF·dot_def_weight)` curve). New `ModelConfig` knobs,
    all `ASSUMPTION` (server-side), least-squares-fit to the log's 8 Burn/Curse anchors (mean
    rel-err ~13%): `dot_global=24.2`, `dot_troop_floor=0.15` (a floor so a near-dead caster
    still ticks a few hundred, as R8=674 shows), `dot_def_ref=900`, `dot_def_weight=2.0`.
  - **Sustain wired:** Shield (actionType 73, buff Shield) is now an **absorb-one-instance**
    buff on allies (consumed by the next DEF-mitigated hit; Real/Assault bypass it, per the
    log); Lunar Guardian's heal (102) is forced to target allies (its token mislabels the
    category as "the target enemy"); Tactical-Skill-DMG-Taken-Increased (37) and ATK-Reduced
    (14) are applied. These produce the log's 8-round Battle-1 stalemate.
  - **Detonate** (Element-Burst, actionType 72 on Exploding Flame): with `dot_detonate_chance`
    (0.4) it **consumes** an enemy's active Burn for a burst = `dot_detonate_coef`(1.2)·burst-coef·
    a fresh tick — landing in the logged ~3.1k–6.7k band. Approximate (exact server burst is
    UNKNOWN_SERVER_SIDE); documented as `ASSUMPTION`.
  - **New `simulator/validate_dot.py`** builds Matchup-2's exact formations (Cthugha·Sp 70 /
    Cthugha 32 / Nyx 116, all +229 DES, vs Thiel 99 +DEF / Nicole 87 4★ +ATK / Dolly 108 +DES,
    Archer, distinct stones) and reports **7/7 PASS** to a UTF-8 file: player win **64.5%**
    (target ~50–65%; in-game 60%, n=10), a representative seed (225) reproduces **Battle 1
    8-round stalemate → Battle 2 victory** with only the +DEF commander Thiel surviving B1,
    Burn ticks 81% in the 700–4,000 band (median ~2,875) with a **0.90** caster-troops↔tick
    correlation (declines as troops fall), **Curse/Burn ≈ 0.47** (~0.5×), Detonate median
    ~5,512 in band, and **Thiel falls last 98%** of matches (strikers die first).
  - The shared baseline/Rosetta damage knobs were **not** retouched: the testcase and baseline
    teams use none of the new actions (73/108/109/72/37/14), so `validate_testcase.py` stays
    **9/9** and `validate_baseline.py` stays **6/6**; `smoke_test` and the CLI `run` path still
    work (the smoke fixture's 0% win rate is pre-existing — an arbitrary unbalanced matchup).

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
