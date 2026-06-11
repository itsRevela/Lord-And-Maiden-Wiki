# Simulator redesign spec (2026-06-11, user-directed)

Redefines what the sim optimizes. The OLD search permuted commander × troop type with default
skills; the NEW search fixes the commander and the allocation (user inputs) and searches the
build (troops × skills × stone × relic), ranking by win rate and/or casualty rate.

## Fixed user INPUTS (not searched)
- **3 heroes** (existing).
- **Commander**: the user designates which of the 3 is commander. NEVER permuted by the search.
- **Stat allocation per hero**: user picks which stat to max-allocate for each hero slot
  (atk / def / ruin / speed). Maps to `BuildSpec.allocated_stat` (already exists).
- **Core count**: user-configurable worker count. Maps to `SearchOptions.workers` (already exists;
  0 = all cores). Expose to API + UI.
- **Searched-axis toggles**: the user can enable/disable each search axis (troop type, modular
  skills, skill stone, relic) — "all of them should be toggleable". A disabled axis stays at a
  default/user-fixed value.

## SEARCH space (genetic, ranked top-N -- space ~1e16, not exhaustive)
Per hero (commander fixed, allocation fixed):
- **troop type** (1..4) -- if the troop axis is enabled.
- **2 modular skills** (loadout) from the hero's modular pool -- if the skills axis is enabled.
- **skill stone**: one of the hero's TWO equipped modular skills at lv5 (CONSTRAINT: the stone
  MUST match a modular skill), or none -- if the stone axis is enabled. So
  `skill_keys = [modular_0, modular_1] + (stone = modular_0|modular_1 @ lv5 | none)`.
- **relic on/off** (per hero): each hero only ever equips its OWN relic (hero-specific, boosts its
  relic-enhanced skill). Toggle = equip it or not -- if the relic axis is enabled.

Genome (searched dims only): per hero -> (troop, (modular_0, modular_1), stone_choice in {0,1,none},
relic_on in {T,F}). Commander index + per-hero allocated_stat are fixed inputs threaded through.

**POOLS = best categories only (user, 2026-06-11):** since we want TOP builds, restrict the search
pools to the best tier: **only 5-star skills** (rare==5) in the modular/stone pool, max-tier troops,
etc. This shrinks the modular pool from ~200 to the handful of 5★ slottable skills -> the genetic
search converges fast on real top builds. (`_skill_pool` filters to rare==5 + modular-equippable.)

## OBJECTIVE
Compute BOTH per build: **win rate** AND **casualty rate** (player troops lost fraction and/or
player units dead). Rank by the user-selected metric (highest win rate and/or lowest casualties);
show both in the results so the list is sortable by either.

## OUTPUT / UI
- Ranked top-N builds (win rate + casualty rate + early/mid/late/all damage windows).
- **Drill-down**: click a ranked build -> full detail panel: each hero's troop type, 2 modular
  skills, stone (which modular), relic on/off, allocation; resolved stats (atk/def/ruin/speed,
  troops); per-hero damage + casualties; win/loss/draw breakdown; the opponent pool it beat.
- UI inputs: commander selector (radio over the 3), per-hero allocation dropdown, core-count input,
  per-axis search toggles, objective sort toggle (win rate / casualties).

## IMPLEMENTATION DECOMPOSITION
1. **Engine** (`engine/optimize.py` + `model.py`): new genome (drop commander from genome -> fixed
   input; thread allocated_stat per hero; add stone_choice + relic_on to the genome; honor axis
   toggles by fixing disabled dims). Add casualty-rate objective + per-build detail in the result.
   Relic on/off: gate the hero's relic application in `build_team` on a per-hero flag.
2. **API** (`web/server.py`): accept commander_index, allocated_stat[3], workers, axis-toggles,
   objective; return ranked builds each carrying full detail for the drill-down.
3. **UI** (`web/app`): commander radio, allocation dropdowns, core-count field, axis toggles,
   objective sort; results list + click-through detail panel.

Each step is self-contained + testable. Build engine first (verify via `python -m simulator.run`
/ optimize), then API, then UI. Keep the four capture-grounded validators green
(testcase/baseline/dot superseded by validate_shield + pursuit at dg=65; engine logic unchanged --
this is search/UI, not combat math).

## PHASE 2 (user directive 2026-06-11) -- gear system + challenging-opponent generator

DONE so far: #1 stone never empty (always matches a modular), #4 relic always equipped (axis
removed), #7 progress total stable (generations+top_n). Per-hero troop dropdown done. Commits
4033cab/abeac3c/304f0e2/c70df06/4143d45/777e12e.

**PHASE 2 COMPLETE (2026-06-11).** All three ordered steps shipped:
1. Gear-component system -- `g.gear_bonus_from_selection(armor_set_id, messenger_id, acc_left_id,
   acc_right_id)` decomposes the flat bonus into a selected max-tier armor SET (slots 1-6 + 3pc/6pc)
   + magic messenger (slot 11) + 2 accessories; relic always on; flat path kept as fallback. Applies
   to BOTH player + opponents. Anchors stayed green (testcase 7/9, dot 5/7, shield 3/6). Commit 994a2ab.
2. Player axes -- `ALL_AXES = (troop, skills, stone, armor, messenger, accessory)`; relic NOT an axis
   (always on). No empty slots; accessory no-dup-within-hero. Commits 47974b5 (axes) + 01905a5 (UI).
3. Challenging-opponent generator -- `engine/opponents.py` two-stage (rank trios w/ strong fixed
   build -> optimize top-X -> cache to `simulator/opponent_cache.json`, gitignored). Main search loads
   the cache as its pool (`use_opponent_cache`, stage B opts out to avoid a feedback loop); falls back
   to the weak sampled set when absent. API: GET /api/opponents, POST /api/generate_opponents. UI:
   "Challenging opponents" panel (top-X / scope / battles-per-trio / shared progress bar / cache
   status). Verified end-to-end over HTTP (0/53->53/53, 3 geared formations cached; main search then
   ranks vs that pool, win 0.88->0.67 vs the stronger set). Commits ebf0ab2 (engine) + 5f73b5c (API+UI).

REALITY CHECK (logged for posterity): the requested EXHAUSTIVE opponent search (all C(113,3)~230k
trios x troops x C(128,2)^3 skills x stones x runes x messengers x accessories x armor sets x 10
battles) is ~10^24 battles -- impossible (millions of years). Per-trio build search alone ~10^12.
So opponent generation MUST be tiered, NOT exhaustive.

ORDERED BUILD (user-confirmed):
1. **Gear-component system** (prereq for everything else). Today the engine applies ONE flat
   `g.gear_bonus` to all units. Decompose `g.gear` (has equipment, set_bonuses, accessories,
   hero_relics, runes) into SELECTABLE components: highest-tier ARMOR SETS (same-prefix sets +
   their set bonus), MAGIC MESSENGERS (PosType 11, ids 3601-3649), ACCESSORIES (2 slots), RUNES
   (highest tier, name-aligned to each equipped skill). Each applied per-BuildSpec; relic always
   on (hero's own, max). Keep a "best flat" fallback. Validate the four anchors stay green.
   **Applies to BOTH the user's formation AND opponents** (user-confirmed) -- every unit, friendly
   or enemy, is built through this system; no flat shortcut for enemies.
   **Constraints (formation rules):**
   - ACCESSORIES: a single hero's TWO accessory slots cannot hold the same accessory (no dup
     within a hero), BUT the same accessory MAY appear across different heroes in the formation
     (cross-hero duplicates are allowed). (Contrast with skill stones, which are no-dup per TEAM.)
   - SKILLS: no duplicate skill within a hero (main + 2 modular + stone, stone matches a modular).
   - ARMOR: same-prefix set; never empty.
2. **Player search axes** (#2/#3/#5): add armor-set + messenger + accessory(2) as toggleable
   genome axes (rune auto-aligns to skills; relic always on); 5-star/max-tier pools only; no empty
   slots; no duplicate skill in a formation.
3. **Generate challenging opponents** (new button before "Start search", same progress bar):
   - STAGE A: rank hero trios (5-star filter optional) using a strong FIXED per-hero build
     (recommended skills+stone+relic+best gear), recommended (rpoint) allocation, 10 battles vs a
     reference set; keep the user's top-X.
   - STAGE B: run the full genetic build-optimization ONLY on the top-X survivors.
   - CACHE the top-X to disk (JSON under notes/sim or simulator/) -> survives refresh/restart;
     the main search loads it as the opponent pool. Opponents follow #1/#2/#4/#5 (full max builds,
     best armor, relic on, no empty slots) -- so they're genuinely challenging (#8/#9).
   - Decisions: rank-trios-then-optimize-top-X; build the gear system FIRST.
   Stat allocation for opponents = each hero's recommended (rpoint) preset.

This is a sizable focused build (gear system -> axes -> generator). The current sim
(commits above) keeps working meanwhile on the redesigned single-formation optimizer.

### Gear data map (de-risked 2026-06-11) -- the build plan is concrete now
`g.gear` contents + how to turn each into a selectable component:
- **Armor sets** = `g.gear["set_bonuses"]` (35 sets, rarity 2-6). Max tier (rarity 6) = 7 sets:
  King, Victory, Thunder, Sunshine, Daybreak Bow, Ares Spear, Fate. Each has `three_piece` +
  `six_piece` effect lists. AXIS: pick one max-tier set per hero -> apply its 6-piece (full set)
  bonus. ("same-prefix" = one set_name, so a full set is inherently same-prefix.)
- **Magic messengers** = `g.gear["equipment"]["11"]["items"]` (slot 11 "Magic Messenger", ids
  3601+, each with `effects` + rarity/power; some carry a `set_id`). AXIS: pick one (max-tier).
- **Accessories** = `g.gear["accessories"]["left"]["items"]` (7) + `["right"]["items"]` (9),
  rarity 3-5. AXIS: pick one left + one right (max-tier); NO identical item in a hero's two slots
  (cross-hero dup OK). Pools are largely distinct already.
- **Runes** = `g.gear["runes"]` (105, rarity 4-5), each `boosted_skill`. AUTO (not an axis): for
  each equipped skill, attach the highest-tier rune whose boosted_skill matches.
- **Relic** = `g.gear["hero_relics"]` (hero's own, enhanced_skill). ALWAYS on (max).
IMPLEMENTATION: replace the single flat `_compute_gear_bonus` path with a per-BuildSpec
`gear` selection {armor_set_id, messenger_id, acc_left_id, acc_right_id} -> accumulate effects
(reuse `_accumulate`) + auto runes + always relic. Keep the flat path as a default/fallback so
the four anchors stay green (validate after). Then add armor_set/messenger/accessory(2) to the
optimize genome as toggleable axes; the opponent generator uses the same gear selection.
