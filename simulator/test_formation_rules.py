"""Formation build-validity rules (user-confirmed 2026-06-11).

THE RULE: one copy of each skill per FORMATION. Counting every hero's main + 2 modular + stone
together as a single team-wide pool, no skill may appear on two heroes. Main skills are
hero-locked, so a modular skill also may not equal ANY hero's main. (A stone reinforces one of
its OWN hero's modulars, so within a hero the stone == a modular is intended, not a duplicate.)

These tests reproduce the bug where the optimizer put "Demon Sword" (modular + stone) on two
heroes in the same formation, then lock the invariant down for the optimizer AND the
challenging-opponent generator.
"""
import random

import pytest

from simulator.engine import data as datamod
from simulator.engine import optimize
from simulator.engine.search import SearchOptions

TRIO = [60, 122, 119]   # Patra / Yaya.Sp / Crolos.Sp -- the trio from the bug report
AXES = ("troop", "skills", "stone", "armor", "messenger", "accessory")


def _loadout_picks(loadout):
    return [tuple(k) for pair in loadout for k in pair]


def _assert_formation_unique(loadout, mains):
    picks = _loadout_picks(loadout)
    assert len(picks) == len(set(picks)), "same modular skill on two heroes in one formation"
    assert not (set(picks) & set(mains)), "a modular skill equals a hero's (locked) main skill"


def test_repair_loadout_dedupes_across_formation():
    """A deliberately-colliding loadout must be repaired to 6 distinct picks, none a main."""
    g = datamod.load()
    rng = random.Random(1)
    ctx = optimize._ctx(g, TRIO, rng, AXES)
    # force the worst case: every hero gets the SAME two skills, one of which is a main
    a, b = ctx["pool"][0], ctx["pool"][1]
    main0 = ctx["mains"][0]
    colliding = ((main0, a), (a, b), (a, b))
    fixed = optimize._repair_loadout(rng, colliding, ctx)
    _assert_formation_unique(fixed, ctx["mains"])


def test_rand_formation_loadout_always_valid():
    g = datamod.load()
    ctx = optimize._ctx(g, TRIO, random.Random(2), AXES)
    for seed in range(200):
        lo = optimize._rand_formation_loadout(random.Random(seed), ctx)
        _assert_formation_unique(lo, ctx["mains"])


def test_random_genomes_stay_formation_unique():
    """The bug: _rand_genome/_crossover/_mutate produced cross-hero duplicate skills. After the
    fix, every genome the GA can build must satisfy the per-formation uniqueness rule."""
    g = datamod.load()
    rng = random.Random(3)
    ctx = optimize._ctx(g, TRIO, rng, AXES)
    for _ in range(500):
        child = optimize._mutate(
            rng, optimize._crossover(rng, optimize._rand_genome(rng, ctx),
                                     optimize._rand_genome(rng, ctx)), ctx)
        _assert_formation_unique(child[1], ctx["mains"])


def test_optimize_formation_output_has_no_duplicate_skills():
    """End-to-end: the ranked builds the UI shows must never repeat a skill across heroes."""
    opts = SearchOptions(n_battles=4, n_opponents=4, workers=1, seed=5)
    rep = optimize.optimize_formation(
        TRIO, opts, commander_index=0, allocated_stats=["atk", "atk", "atk"],
        search_axes=("skills", "stone"), objective="win", top_n=5,
        pop_size=10, generations=3, ga_battles=3, ga_opponents=3, use_opponent_cache=False)
    for b in rep["builds"]:
        per_hero = []
        mains = []
        for h in b["heroes"]:
            mains.append(h["main_skill"])
            per_hero.append({h["main_skill"], *(h.get("modular_skills") or []),
                             *( [h["skill_stone"]] if h.get("skill_stone") else [] )})
        # pairwise disjoint across heroes
        for i in range(3):
            for j in range(i + 1, 3):
                shared = per_hero[i] & per_hero[j]
                assert not shared, "build %r repeats skill(s) %r across heroes" % (b["label"], shared)


def test_strong_opponent_team_is_formation_unique():
    """The challenging-opponent generator's fixed strong build must also obey the rule."""
    from simulator.engine import opponents as opp
    g = datamod.load()
    specs = opp._strong_team_specs(g, TRIO, opp._def_gear(g))
    # collect modular keys (skill_keys = 2 modular + stone-reinforcing-modular0)
    mains = {optimize._main_key(g, h) for h in TRIO}
    picks = []
    for s in specs:
        picks.extend(tuple(k) for k in s.skill_keys[:2])   # the 2 modular slots
    assert len(picks) == len(set(picks)), "opponent generator repeats a modular skill across heroes"
    assert not (set(picks) & mains), "opponent generator modular equals a main skill"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
