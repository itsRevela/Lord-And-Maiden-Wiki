"""Genetic optimiser for the full build space of a fixed 3-hero formation.

A hero can slot ANY two skills in its modular slots (the main skill is fixed), so the
joint space is commander(3) x troop-combos(4^3) x skill-loadouts (~C(416,2)^3) ~ 1e16 --
far too large to enumerate. This module evolves a population of full builds
(commander + troop types + the 6 modular skill slots), scoring each by win rate (or a
chosen damage window) using the same Monte-Carlo battle engine, parallelised across
cores. Result is a strong build, NOT a proven global optimum -- it is reported as a
heuristic optimum.
"""
from __future__ import annotations

import os
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict

from . import data as datamod
from .combat import Battle
from .model import BuildSpec, ModelConfig, build_team, fresh_units
from .search import WINDOWS, SearchOptions, sample_opponents, _summ

TROOP_NAMES = {1: "Infantry", 2: "Archer", 3: "Cavalry", 4: "Chariot"}


# genome = (commander:int, troops:tuple3, loadout:tuple3 of tuple2 of (st,id))
def _skill_pool(g):
    return [k for k in g.skills.keys()]


def _main_key(g, hid):
    m = g.hero(hid)["main_skill"]
    return (int(m["st"]), int(m["id"]))


def _rand_loadout_for(rng, pool, main_key):
    a = rng.choice(pool)
    while a == main_key:
        a = rng.choice(pool)
    b = rng.choice(pool)
    while b == main_key or b == a:
        b = rng.choice(pool)
    return (a, b)


def _rand_genome(rng, g, hero_ids):
    pool = _skill_pool(g)
    commander = rng.randrange(3)
    troops = tuple(rng.randrange(1, 5) for _ in range(3))
    loadout = tuple(_rand_loadout_for(rng, pool, _main_key(g, h)) for h in hero_ids)
    return (commander, troops, loadout)


def _seed_genomes(g, hero_ids):
    """Sensible starting points: each hero on its RST troop with default skills,
    one genome per commander choice."""
    seeds = []
    troops = tuple(g.hero(h)["rst"]["id"] for h in hero_ids)
    loadout = tuple(tuple((int(s["st"]), int(s["id"])) for s in g.hero(h).get("modular_default", []))
                    for h in hero_ids)
    # pad loadouts that have <2 default skills with the main skill's neighbours? keep as-is;
    # build_team tolerates short loadouts.
    for cmd in range(3):
        seeds.append((cmd, troops, loadout))
    return seeds


def _specs_from_genome(genome):
    commander, troops, loadout = genome
    return commander, troops, loadout


def _eval_genome(payload):
    """Worker: score one genome vs the opponent pool. Deterministic per genome."""
    g = datamod.load()
    cfg = ModelConfig(**payload["cfg"])
    hero_ids = payload["hero_ids"]
    commander, troops, loadout = payload["commander"], payload["troops"], payload["loadout"]
    opponents = payload["opponents"]
    n_battles = payload["n_battles"]
    seed = payload["seed"]

    specs = tuple(
        BuildSpec(hero_id=hero_ids[i], soldier_type=troops[i],
                  is_commander=(i == commander),
                  skill_keys=tuple((int(k[0]), int(k[1])) for k in loadout[i]))
        for i in range(3)
    )
    player = build_team(g, specs, side=0, cfg=cfg, fight_pos_base=1)
    opp_templates = []
    for opp in opponents:
        ospecs = [BuildSpec(hero_id=hid, soldier_type=tt, is_commander=ic) for (hid, tt, ic) in opp]
        opp_templates.append(build_team(g, ospecs, side=1, cfg=cfg, fight_pos_base=4))

    wins = battles = 0
    window_samples = {w: [] for w in WINDOWS}
    s = seed
    for opp_team in opp_templates:
        for _ in range(n_battles):
            res = Battle(g, cfg, fresh_units(player), fresh_units(opp_team), random.Random(s)).run()
            s += 1
            battles += 1
            if res.winner == 0:
                wins += 1
            wd = res.window_damage("player")
            for w in WINDOWS:
                window_samples[w].append(wd[w])
    win_rate = wins / battles if battles else 0.0
    windows = {w: (sum(window_samples[w]) / len(window_samples[w]) if window_samples[w] else 0.0)
               for w in WINDOWS}
    obj = payload["objective"]
    primary = win_rate if obj == "win" else windows.get(obj, 0.0)
    return {"win_rate": win_rate, "windows": windows, "primary": primary, "battles": battles}


def _crossover(rng, a, b):
    ca, ta, la = a
    cb, tb, lb = b
    commander = ca if rng.random() < 0.5 else cb
    troops = tuple((ta[i] if rng.random() < 0.5 else tb[i]) for i in range(3))
    loadout = tuple((la[i] if rng.random() < 0.5 else lb[i]) for i in range(3))
    return (commander, troops, loadout)


def _mutate(rng, genome, g, hero_ids, rate=0.3):
    pool = _skill_pool(g)
    commander, troops, loadout = genome
    if rng.random() < rate:
        commander = rng.randrange(3)
    troops = list(troops)
    loadout = [list(pair) for pair in loadout]
    for i in range(3):
        if rng.random() < rate:
            troops[i] = rng.randrange(1, 5)
        if rng.random() < rate:
            mk = _main_key(g, hero_ids[i])
            slot = rng.randrange(2)
            other = loadout[i][1 - slot]
            ns = rng.choice(pool)
            tries = 0
            while (ns == mk or ns == other) and tries < 10:
                ns = rng.choice(pool); tries += 1
            loadout[i][slot] = ns
    return (commander, tuple(troops), tuple(tuple(p) for p in loadout))


def optimize_formation(hero_ids, opts: SearchOptions, progress=None,
                       pop_size=44, generations=24, objective="win",
                       ga_battles=18, ga_opponents=12, elite=6):
    """Evolve the best full build. ``progress(done,total)`` over generations."""
    g = datamod.load()
    hero_ids = [int(h) for h in hero_ids]
    rng = random.Random(opts.seed)
    cfg_dict = asdict(opts.cfg)
    opponents = sample_opponents(g, max(ga_opponents, opts.n_opponents), opts.seed, exclude=hero_ids)
    ga_opp = opponents[:ga_opponents]

    population = _seed_genomes(g, hero_ids)
    while len(population) < pop_size:
        population.append(_rand_genome(rng, g, hero_ids))

    cache = {}
    workers = opts.workers or (os.cpu_count() or 2)

    def evaluate(genomes):
        todo = [gm for gm in genomes if gm not in cache]
        if not todo:
            return
        payloads = []
        for gm in todo:
            c, t, l = gm
            payloads.append({"hero_ids": hero_ids, "commander": c, "troops": list(t),
                             "loadout": [list(p) for p in l], "opponents": ga_opp,
                             "n_battles": ga_battles, "cfg": cfg_dict, "objective": objective,
                             "seed": opts.seed + (hash(gm) & 0xffff) * 131})
        if workers <= 1:
            for gm, pl in zip(todo, payloads):
                cache[gm] = _eval_genome(pl)
        else:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                futs = {ex.submit(_eval_genome, pl): gm for gm, pl in zip(todo, payloads)}
                for fut in as_completed(futs):
                    cache[futs[fut]] = fut.result()

    best_history = []
    for gen in range(generations):
        evaluate(population)
        population.sort(key=lambda gm: (cache[gm]["primary"], cache[gm]["win_rate"]), reverse=True)
        best_history.append(cache[population[0]]["primary"])
        if progress:
            progress(gen + 1, generations)
        if gen == generations - 1:
            break
        # next generation: elitism + tournament offspring
        nxt = population[:elite]
        while len(nxt) < pop_size:
            p1 = _tournament(rng, population, cache)
            p2 = _tournament(rng, population, cache)
            child = _mutate(rng, _crossover(rng, p1, p2), g, hero_ids)
            nxt.append(child)
        population = nxt

    # final high-fidelity re-eval of the winner vs the FULL opponent pool
    best = population[0]
    c, t, l = best
    final = _eval_genome({
        "hero_ids": hero_ids, "commander": c, "troops": list(t),
        "loadout": [list(p) for p in l], "opponents": opponents,
        "n_battles": opts.n_battles, "cfg": cfg_dict, "objective": objective,
        "seed": opts.seed + 777,
    })
    return _assemble_opt(g, hero_ids, best, final, opponents, opts, objective,
                         generations, pop_size, best_history)


def _tournament(rng, population, cache, k=3):
    cand = rng.sample(population, min(k, len(population)))
    return max(cand, key=lambda gm: cache[gm]["primary"])


def _skill_name(g, key):
    sk = g.skill(*key)
    return sk["name_en"] if sk else "Skill#%s.%s" % key


def _assemble_opt(g, hero_ids, best, stats, opponents, opts, objective,
                  generations, pop_size, history):
    commander, troops, loadout = best
    heroes = []
    for i, hid in enumerate(hero_ids):
        h = g.hero(hid)
        heroes.append({
            "id": hid, "name": h["name_en"], "is_commander": (i == commander),
            "troop": TROOP_NAMES[troops[i]],
            "main_skill": h["main_skill"]["name_en"],
            "modular_skills": [_skill_name(g, k) for k in loadout[i]],
        })
    label = " / ".join(
        ("[CMD] " if hi["is_commander"] else "") + "%s(%s)" % (hi["name"], hi["troop"])
        for hi in heroes)
    return {
        "_about": ("Heuristic genetic optimisation over the full build space (commander + "
                   "troop types + the 6 modular skill slots). A hero can slot any skills. "
                   "This is a strong build, not a proven global optimum. Combat model is "
                   "server-side; see notes/sim/combat_rules.md."),
        "mode": "optimize",
        "objective": objective,
        "heroes": heroes,
        "best_label": label,
        "win_rate": stats["win_rate"],
        "windows": stats["windows"],
        "ga": {"generations": generations, "population": pop_size,
               "best_primary_history": history},
        "options": {"seed": opts.seed},
    }
