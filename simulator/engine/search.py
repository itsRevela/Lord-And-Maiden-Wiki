"""Combinatorial Monte-Carlo search for the Lord & Maiden simulator.

Given 3 user-selected heroes, enumerate every build (which hero commands x each
hero's troop type), evaluate each against a shared pool of opponent formations over
many seeded battles, and rank by battle effectiveness per round-window
(early 1-2 / mid 3-4 / late 5+ / all). Uses every CPU core.

The unit of parallel work is ONE player build vs the full opponent pool, so each
task is substantial and returns a compact summary (win rate + window distribution),
keeping inter-process payloads small.
"""
from __future__ import annotations

import itertools
import math
import os
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field

from . import data as datamod
from .combat import Battle
from .model import BuildSpec, ModelConfig, build_team, fresh_units

WINDOWS = ("early", "mid", "late", "all")


# ---------------------------------------------------------------------------
#  Plan / result containers
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class BuildPlan:
    """A concrete player build over the 3 user heroes (in user-given order)."""
    hero_ids: tuple            # (h0, h1, h2)
    commander_index: int       # 0..2
    troop_types: tuple         # (t0, t1, t2) each 1..4

    def specs(self):
        return tuple(
            BuildSpec(hero_id=h, soldier_type=self.troop_types[i],
                      is_commander=(i == self.commander_index))
            for i, h in enumerate(self.hero_ids)
        )


def _pct(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * q
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] * (hi - k) + sorted_vals[hi] * (k - lo)


def _summ(samples):
    n = len(samples)
    if n == 0:
        return {"n": 0, "mean": 0.0, "std": 0.0, "p10": 0.0, "p50": 0.0, "p90": 0.0}
    s = sorted(samples)
    mean = sum(s) / n
    var = sum((x - mean) ** 2 for x in s) / n
    return {"n": n, "mean": mean, "std": math.sqrt(var),
            "p10": _pct(s, 0.10), "p50": _pct(s, 0.50), "p90": _pct(s, 0.90)}


# ---------------------------------------------------------------------------
#  Worker: evaluate one build vs all opponents
# ---------------------------------------------------------------------------
def _eval_build(payload):
    """Runs in a worker process. payload is a plain dict (picklable)."""
    g = datamod.load()
    cfg = ModelConfig(**payload["cfg"])
    plan = BuildPlan(tuple(payload["hero_ids"]), payload["commander_index"],
                     tuple(payload["troop_types"]))
    opponents = payload["opponents"]          # list of list[ (hero_id, troop, is_cmd) ]
    n_battles = payload["n_battles"]
    base_seed = payload["seed"]

    player_template = build_team(g, plan.specs(), side=0, cfg=cfg, fight_pos_base=1)
    opp_templates = []
    for opp in opponents:
        ospecs = [BuildSpec(hero_id=hid, soldier_type=tt, is_commander=ic)
                  for (hid, tt, ic) in opp]
        opp_templates.append(build_team(g, ospecs, side=1, cfg=cfg, fight_pos_base=4))

    wins = 0
    battles = 0
    bouts_total = 0
    win_by_opp = []
    window_samples = {w: [] for w in WINDOWS}
    seed = base_seed
    for oi, opp_team in enumerate(opp_templates):
        owins = 0
        for b in range(n_battles):
            rng = random.Random(seed)
            seed += 1
            res = Battle(g, cfg, fresh_units(player_template),
                         fresh_units(opp_team), rng).run()
            battles += 1
            bouts_total += res.bouts_fought
            if res.winner == 0:
                wins += 1
                owins += 1
            wd = res.window_damage("player")
            for w in WINDOWS:
                window_samples[w].append(wd[w])
        win_by_opp.append(owins / n_battles if n_battles else 0.0)

    win_rate = wins / battles if battles else 0.0
    # Wald 95% CI for the win-rate (binomial proportion)
    ci = 1.96 * math.sqrt(max(0.0, win_rate * (1 - win_rate) / battles)) if battles else 0.0
    return {
        "plan": {"hero_ids": list(plan.hero_ids),
                 "commander_index": plan.commander_index,
                 "troop_types": list(plan.troop_types)},
        "battles": battles,
        "win_rate": win_rate,
        "win_rate_ci95": ci,
        "avg_bouts": bouts_total / battles if battles else 0.0,
        "win_rate_min_vs_opp": min(win_by_opp) if win_by_opp else 0.0,
        "win_rate_worst_quartile": _pct(sorted(win_by_opp), 0.25) if win_by_opp else 0.0,
        "windows": {w: _summ(window_samples[w]) for w in WINDOWS},
    }


# ---------------------------------------------------------------------------
#  Opponent pool
# ---------------------------------------------------------------------------
def sample_opponents(g: datamod.GameData, n: int, seed: int, exclude=()):
    """Sample n distinct 3-hero opponent formations from the playable roster.
    Each opponent hero fields its RST soldier type; slot 0 is the commander.
    Higher-star heroes are weighted up so the pool leans 'meta'."""
    rng = random.Random(seed)
    ids = [h for h in g.heroes if h not in set(exclude)]
    weights = [max(1, g.hero(h)["star"]) ** 2 for h in ids]
    teams = []
    seen = set()
    attempts = 0
    while len(teams) < n and attempts < n * 50:
        attempts += 1
        trio = tuple(sorted(rng.choices(ids, weights=weights, k=3)))
        if len(set(trio)) != 3 or trio in seen:
            continue
        seen.add(trio)
        team = [(hid, g.hero(hid)["rst"]["id"], (k == 0)) for k, hid in enumerate(trio)]
        teams.append(team)
    return teams


# ---------------------------------------------------------------------------
#  Build enumeration
# ---------------------------------------------------------------------------
def enumerate_builds(hero_ids, select_optimal_troop: bool):
    """All (commander, troop-combo) builds. We always enumerate the full troop
    space (4^3=64) x commander (3) = 192 builds, because finding the optimal troop
    set REQUIRES evaluating them. The toggle only changes how results are reported
    (best-only vs full troop breakdown)."""
    hero_ids = tuple(hero_ids)
    plans = []
    for cmd in range(3):
        for combo in itertools.product((1, 2, 3, 4), repeat=3):
            plans.append(BuildPlan(hero_ids, cmd, combo))
    return plans


# ---------------------------------------------------------------------------
#  Orchestrator
# ---------------------------------------------------------------------------
@dataclass
class SearchOptions:
    n_battles: int = 60                 # battles per (build, opponent)
    n_opponents: int = 40               # opponent formations in the pool
    select_optimal_troop: bool = True
    seed: int = 12345
    workers: int = 0                    # 0 -> all cores
    cfg: ModelConfig = field(default_factory=ModelConfig)


def run_search(hero_ids, opts: SearchOptions, progress=None):
    """Run the full search. ``progress(done, total)`` is called as builds finish.
    Returns a results dict ready for JSON export."""
    g = datamod.load()
    hero_ids = [int(h) for h in hero_ids]
    plans = enumerate_builds(hero_ids, opts.select_optimal_troop)
    opponents = sample_opponents(g, opts.n_opponents, opts.seed, exclude=hero_ids)

    cfg_dict = asdict(opts.cfg)
    payloads = []
    for i, p in enumerate(plans):
        payloads.append({
            "hero_ids": list(p.hero_ids),
            "commander_index": p.commander_index,
            "troop_types": list(p.troop_types),
            "opponents": opponents,
            "n_battles": opts.n_battles,
            "cfg": cfg_dict,
            "seed": opts.seed + i * 1_000_003,
        })

    workers = opts.workers or (os.cpu_count() or 2)
    total = len(payloads)
    results = []
    done = 0
    if workers <= 1:
        for pl in payloads:
            results.append(_eval_build(pl))
            done += 1
            if progress:
                progress(done, total)
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_eval_build, pl) for pl in payloads]
            for fut in as_completed(futs):
                results.append(fut.result())
                done += 1
                if progress:
                    progress(done, total)

    return _assemble(g, hero_ids, opponents, opts, results)


def _troop_name(g, t):
    return g.soldier_type_name[t]


def _assemble(g, hero_ids, opponents, opts: SearchOptions, results):
    heroes_meta = [{"id": h, "name": g.hero(h)["name_en"],
                    "star": g.hero(h)["star"],
                    "race": g.hero(h)["race"]["name_en"],
                    "rst": g.hero(h)["rst"]["soldier_type_en"],
                    "role": (g.hero(h).get("role") or {}).get("name_en", "?")}
                   for h in hero_ids]

    # annotate each result with human-readable plan + a per-window score
    for r in results:
        pl = r["plan"]
        r["label"] = " / ".join(
            "%s%s(%s)" % ("[CMD] " if i == pl["commander_index"] else "",
                          g.hero(pl["hero_ids"][i])["name_en"],
                          _troop_name(g, pl["troop_types"][i]))
            for i in range(3))
        r["commander_name"] = g.hero(pl["hero_ids"][pl["commander_index"]])["name_en"]
        r["troop_names"] = [_troop_name(g, t) for t in pl["troop_types"]]

    # primary ranking = win rate (robustness: worst-quartile win rate as tiebreak)
    ranked = sorted(results, key=lambda r: (r["win_rate"], r["win_rate_worst_quartile"]),
                    reverse=True)

    # best build per focus window (by that window's mean damage among top win-rate)
    by_window = {}
    for w in WINDOWS:
        by_window[w] = sorted(
            results, key=lambda r: (r["windows"][w]["mean"], r["win_rate"]), reverse=True
        )[0]["label"]

    # best per commander choice and per "optimal troop" view
    best_overall = ranked[0]
    out = {
        "_about": ("Battle-effectiveness ranking for a fixed 3-hero formation. "
                   "Combat is server-authoritative; this is a transparent rules-based "
                   "model (see notes/sim/combat_rules.md). Rankings are model-relative "
                   "but comparable across builds since the same model applies to all."),
        "heroes": heroes_meta,
        "options": {"n_battles": opts.n_battles, "n_opponents": opts.n_opponents,
                    "select_optimal_troop": opts.select_optimal_troop,
                    "seed": opts.seed, "total_builds": len(results),
                    "battles_per_build": opts.n_battles * opts.n_opponents,
                    "total_battles": opts.n_battles * opts.n_opponents * len(results)},
        "opponent_pool": [[g.hero(o[0])["name_en"] for o in team] for team in opponents],
        "best_overall": best_overall["label"],
        "best_by_window": by_window,
        "ranking": ranked,
    }
    if opts.select_optimal_troop:
        # collapse to the single best troop assignment per commander choice
        seen_cmd = {}
        for r in ranked:
            c = r["plan"]["commander_index"]
            if c not in seen_cmd:
                seen_cmd[c] = r
        out["best_per_commander"] = [seen_cmd[c]["label"] for c in sorted(seen_cmd)]
    return out
