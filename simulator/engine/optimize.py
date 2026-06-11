"""Genetic optimiser for the build space of a fixed 3-hero formation.

The COMMANDER and each hero's STAT ALLOCATION are fixed user inputs (NOT permuted). The
search evolves, per hero, the build over these toggleable axes:
  * troop type (1..4)
  * 2 modular skills (the main skill is fixed)
  * skill stone: one of the hero's TWO equipped modular skills @ lv5, or none -- the stone
    MUST match a modular skill (it reinforces it); modelled as a trigger-prob boost on that
    modular (cfg.stone_trigger_bonus, ASSUMPTION) since build_team de-dups identical skills.
  * relic on/off (the hero's OWN relic)

Pools are restricted to the BEST tier ("top builds"): only 5-star (rare==5) modular-equippable
skills; max-tier troops. The space is still large, so this is a genetic search returning a
RANKED top-N of strong builds (heuristic, not a proven global optimum), scored by win rate or
casualty rate via the Monte-Carlo engine, parallelised across `workers` cores.
"""
from __future__ import annotations

import os
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict

from . import data as datamod
from .combat import Battle
from .model import BuildSpec, ModelConfig, build_team, fresh_units
from .search import WINDOWS, SearchOptions, sample_opponents

TROOP_NAMES = {1: "Infantry", 2: "Archer", 3: "Cavalry", 4: "Chariot"}
ALL_AXES = ("troop", "skills", "stone", "relic")
# genome = (troops:tuple3 int, loadout:tuple3 of (k,k), stones:tuple3 int{-1,0,1}, relics:tuple3 bool)


def _skill_pool(g):
    """Best-category modular pool: 5-star (rare==5) AND modular-equippable (skillStone)."""
    return [k for k, sk in g.skills.items()
            if int(sk.get("rare") or 0) == 5 and sk.get("skillStone")]


def _main_key(g, hid):
    m = g.hero(hid)["main_skill"]
    return (int(m["st"]), int(m["id"]))


def _default_modular(g, hid, pool, main_key, rng):
    mods = [(int(s["st"]), int(s["id"])) for s in g.hero(hid).get("modular_default", [])]
    mods = [m for m in mods if m in pool and m != main_key]
    while len(mods) < 2:
        c = rng.choice(pool)
        if c != main_key and c not in mods:
            mods.append(c)
    return (mods[0], mods[1])


def _rand_loadout_for(rng, pool, main_key):
    a = rng.choice(pool)
    while a == main_key:
        a = rng.choice(pool)
    b = rng.choice(pool)
    while b == main_key or b == a:
        b = rng.choice(pool)
    return (a, b)


def _ctx(g, hero_ids, rng, axes, troop_types=None):
    pool = _skill_pool(g)
    mains = [_main_key(g, h) for h in hero_ids]
    # default/fixed troop per hero: the user's choice if given (1..4), else the hero's RST.
    # When the troop axis is OFF this is used verbatim; when ON it's the seed/starting point.
    tt = troop_types or [None, None, None]
    def_troops = tuple(int(tt[i]) if (i < len(tt) and tt[i] in (1, 2, 3, 4)) else g.hero(hero_ids[i])["rst"]["id"]
                       for i in range(3))
    return {
        "pool": pool, "mains": mains, "axes": set(axes),
        "def_troops": def_troops,
        "def_loadout": tuple(_default_modular(g, hero_ids[i], pool, mains[i], rng)
                             for i in range(3)),
    }


def _rand_genome(rng, ctx):
    troops = (tuple(rng.randrange(1, 5) for _ in range(3))
              if "troop" in ctx["axes"] else ctx["def_troops"])
    loadout = (tuple(_rand_loadout_for(rng, ctx["pool"], ctx["mains"][i]) for i in range(3))
               if "skills" in ctx["axes"] else ctx["def_loadout"])
    stones = (tuple(rng.choice((-1, 0, 1)) for _ in range(3))
              if "stone" in ctx["axes"] else (-1, -1, -1))
    relics = (tuple(rng.random() < 0.5 for _ in range(3))
              if "relic" in ctx["axes"] else (True, True, True))
    return (troops, loadout, stones, relics)


def _seed_genomes(rng, ctx):
    """Sensible starting points: default troops + default modular skills, no stone, relic on;
    plus a few with each hero's stone on slot 0."""
    base = (ctx["def_troops"], ctx["def_loadout"], (-1, -1, -1), (True, True, True))
    seeds = [base]
    if "stone" in ctx["axes"]:
        seeds.append((ctx["def_troops"], ctx["def_loadout"], (0, 0, 0), (True, True, True)))
    return seeds


def _specs(hero_ids, genome, commander, allocated):
    troops, loadout, stones, relics = genome
    specs = []
    for i in range(3):
        mods = [tuple(k) for k in loadout[i]]
        keys = list(mods)
        st = stones[i]
        if st in (0, 1) and st < len(mods):
            keys.append(mods[st])   # stone == a modular skill (reinforces it); last entry @ lv5
        specs.append(BuildSpec(hero_id=hero_ids[i], soldier_type=int(troops[i]),
                               is_commander=(i == commander),
                               skill_keys=tuple(keys),
                               allocated_stat=allocated[i],
                               relic_on=bool(relics[i])))
    return tuple(specs)


def _eval_genome(payload):
    """Worker: score one genome vs the opponent pool. Deterministic per genome."""
    g = datamod.load()
    cfg = ModelConfig(**payload["cfg"])
    hero_ids = payload["hero_ids"]
    genome = payload["genome"]
    specs = _specs(hero_ids, genome, payload["commander"], payload["allocated"])
    player = build_team(g, specs, side=0, cfg=cfg, fight_pos_base=1)
    opp_templates = [build_team(g, [BuildSpec(hero_id=hid, soldier_type=tt, is_commander=ic)
                                    for (hid, tt, ic) in opp], side=1, cfg=cfg, fight_pos_base=4)
                     for opp in payload["opponents"]]
    n_battles = payload["n_battles"]
    wins = battles = 0
    troops_rem = 0.0; units_lost = 0
    window_samples = {w: [] for w in WINDOWS}
    s = payload["seed"]
    for opp_team in opp_templates:
        for _ in range(n_battles):
            res = Battle(g, cfg, fresh_units(player), fresh_units(opp_team), random.Random(s)).run()
            s += 1; battles += 1
            if res.winner == 0:
                wins += 1
            troops_rem += res.player_troops_frac_remaining
            units_lost += (3 - res.player_units_alive)
            wd = res.window_damage("player")
            for w in WINDOWS:
                window_samples[w].append(wd[w])
    win_rate = wins / battles if battles else 0.0
    casualty_rate = 1.0 - (troops_rem / battles if battles else 1.0)   # frac of player troops lost
    avg_units_lost = units_lost / battles if battles else 0.0
    windows = {w: (sum(v) / len(v) if v else 0.0) for w, v in window_samples.items()}
    obj = payload["objective"]
    if obj == "win":
        primary = win_rate
    elif obj == "casualty":
        primary = 1.0 - casualty_rate            # higher = fewer casualties = better
    else:
        primary = windows.get(obj, 0.0)
    return {"win_rate": win_rate, "casualty_rate": casualty_rate,
            "avg_units_lost": avg_units_lost, "windows": windows,
            "primary": primary, "battles": battles}


def _crossover(rng, a, b):
    ta, la, sa, ra = a
    tb, lb, sb, rb = b
    troops = tuple((ta[i] if rng.random() < 0.5 else tb[i]) for i in range(3))
    loadout = tuple((la[i] if rng.random() < 0.5 else lb[i]) for i in range(3))
    stones = tuple((sa[i] if rng.random() < 0.5 else sb[i]) for i in range(3))
    relics = tuple((ra[i] if rng.random() < 0.5 else rb[i]) for i in range(3))
    return (troops, loadout, stones, relics)


def _mutate(rng, genome, ctx, rate=0.3):
    troops, loadout, stones, relics = genome
    troops = list(troops); loadout = [list(p) for p in loadout]
    stones = list(stones); relics = list(relics)
    pool = ctx["pool"]
    for i in range(3):
        if "troop" in ctx["axes"] and rng.random() < rate:
            troops[i] = rng.randrange(1, 5)
        if "skills" in ctx["axes"] and rng.random() < rate:
            slot = rng.randrange(2)
            other = loadout[i][1 - slot]; mk = ctx["mains"][i]
            ns = rng.choice(pool); tries = 0
            while (ns == mk or ns == other) and tries < 10:
                ns = rng.choice(pool); tries += 1
            loadout[i][slot] = ns
        if "stone" in ctx["axes"] and rng.random() < rate:
            stones[i] = rng.choice((-1, 0, 1))
        if "relic" in ctx["axes"] and rng.random() < rate:
            relics[i] = not relics[i]
    return (tuple(troops), tuple(tuple(p) for p in loadout), tuple(stones), tuple(relics))


def _tournament(rng, population, cache, k=3):
    cand = rng.sample(population, min(k, len(population)))
    return max(cand, key=lambda gm: cache[gm]["primary"])


def optimize_formation(hero_ids, opts: SearchOptions, progress=None,
                       commander_index=0, allocated_stats=None, search_axes=ALL_AXES,
                       troop_types=None, objective="win", top_n=20,
                       pop_size=44, generations=24, ga_battles=18, ga_opponents=12, elite=6):
    """Evolve + rank the best builds for a FIXED commander + allocation. Returns top-N."""
    g = datamod.load()
    hero_ids = [int(h) for h in hero_ids]
    if len(set(hero_ids)) != 3:
        raise ValueError("a formation cannot field the same hero twice")
    commander_index = int(commander_index)
    allocated = tuple((allocated_stats or [None, None, None])[i] for i in range(3))
    rng = random.Random(opts.seed)
    cfg_dict = asdict(opts.cfg)
    ctx = _ctx(g, hero_ids, rng, search_axes, troop_types)
    opponents = sample_opponents(g, max(ga_opponents, opts.n_opponents), opts.seed, exclude=hero_ids)
    ga_opp = opponents[:ga_opponents]

    population = _seed_genomes(rng, ctx)
    while len(population) < pop_size:
        population.append(_rand_genome(rng, ctx))

    cache = {}
    workers = opts.workers or (os.cpu_count() or 2)

    def _payload(gm, opp, nb, sd):
        return {"hero_ids": hero_ids, "genome": gm, "commander": commander_index,
                "allocated": list(allocated), "opponents": opp, "n_battles": nb,
                "cfg": cfg_dict, "objective": objective, "seed": sd}

    def evaluate(genomes):
        todo = [gm for gm in genomes if gm not in cache]
        if not todo:
            return
        payloads = [_payload(gm, ga_opp, ga_battles, opts.seed + (hash(gm) & 0xffff) * 131)
                    for gm in todo]
        if workers <= 1:
            for gm, pl in zip(todo, payloads):
                cache[gm] = _eval_genome(pl)
        else:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                futs = {ex.submit(_eval_genome, pl): gm for gm, pl in zip(todo, payloads)}
                for fut in as_completed(futs):
                    cache[futs[fut]] = fut.result()

    history = []
    for gen in range(generations):
        evaluate(population)
        population.sort(key=lambda gm: (cache[gm]["primary"], cache[gm]["win_rate"]), reverse=True)
        history.append(cache[population[0]]["primary"])
        if progress:
            progress(gen + 1, generations)
        if gen == generations - 1:
            break
        nxt = population[:elite]
        seen = set(nxt)
        while len(nxt) < pop_size:
            child = _mutate(rng, _crossover(rng, _tournament(rng, population, cache),
                                            _tournament(rng, population, cache)), ctx)
            if child not in seen:
                nxt.append(child); seen.add(child)
        population = nxt

    # de-dup, take the unique top-N, re-eval each at full fidelity vs the FULL opponent pool
    uniq = []
    seen = set()
    for gm in population:
        if gm not in seen:
            seen.add(gm); uniq.append(gm)
        if len(uniq) >= top_n:
            break
    # full-fidelity re-eval of the top-N -- parallelised (was sequential -> slow tail), with
    # progress continuing past the GA generations so the UI bar doesn't sit "stuck" at 24/24.
    fin_payloads = [_payload(gm, opponents, opts.n_battles, opts.seed + 777 + i)
                    for i, gm in enumerate(uniq)]
    ranked = []
    if workers <= 1:
        for gm, pl in zip(uniq, fin_payloads):
            ranked.append((gm, _eval_genome(pl)))
            if progress:
                progress(generations + len(ranked), generations + len(uniq))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_eval_genome, pl): gm for gm, pl in zip(uniq, fin_payloads)}
            for fut in as_completed(futs):
                ranked.append((futs[fut], fut.result()))
                if progress:
                    progress(generations + len(ranked), generations + len(uniq))
    ranked.sort(key=lambda gf: (gf[1]["primary"], gf[1]["win_rate"]), reverse=True)
    return _assemble(g, hero_ids, commander_index, allocated, ranked, opts, objective,
                     search_axes, generations, pop_size, history)


def _skill_name(g, key):
    sk = g.skill(*key)
    return sk["name_en"] if sk else "Skill#%s.%s" % key


def _build_detail(g, hero_ids, commander, allocated, genome, stats):
    troops, loadout, stones, relics = genome
    heroes = []
    for i, hid in enumerate(hero_ids):
        h = g.hero(hid)
        mods = [tuple(k) for k in loadout[i]]
        st = stones[i]
        heroes.append({
            "id": hid, "name": h["name_en"], "is_commander": (i == commander),
            "troop": TROOP_NAMES[int(troops[i])],
            "allocation": allocated[i] or "none",
            "main_skill": h["main_skill"]["name_en"],
            "modular_skills": [_skill_name(g, k) for k in mods],
            "skill_stone": (_skill_name(g, mods[st]) if st in (0, 1) and st < len(mods) else "none"),
            "relic": "on" if relics[i] else "off",
        })
    label = " / ".join(
        ("[CMD] " if hi["is_commander"] else "") + "%s(%s)" % (hi["name"], hi["troop"])
        for hi in heroes)
    return {"heroes": heroes, "label": label,
            "win_rate": stats["win_rate"], "casualty_rate": stats["casualty_rate"],
            "avg_units_lost": stats["avg_units_lost"], "windows": stats["windows"]}


def _assemble(g, hero_ids, commander, allocated, ranked, opts, objective, axes,
              generations, pop_size, history):
    builds = [_build_detail(g, hero_ids, commander, allocated, gm, st) for gm, st in ranked]
    return {
        "_about": ("Genetic top-N over a FIXED commander + allocation. Searches troop/modular "
                   "skills/skill-stone(matches a modular)/relic over BEST-tier (5-star) pools. "
                   "Heuristic ranking, not a proven global optimum. Combat model is server-side; "
                   "see notes/sim/combat_rules.md."),
        "mode": "optimize",
        "objective": objective,
        "commander_index": commander,
        "allocation": list(allocated),
        "search_axes": list(axes),
        "builds": builds,                          # ranked top-N, each with full detail
        "best_label": builds[0]["label"] if builds else "",
        "win_rate": builds[0]["win_rate"] if builds else 0.0,
        "windows": builds[0]["windows"] if builds else {},
        "ga": {"generations": generations, "population": pop_size, "best_primary_history": history},
        "options": {"seed": opts.seed},
    }
