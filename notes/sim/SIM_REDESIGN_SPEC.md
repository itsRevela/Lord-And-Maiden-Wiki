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
