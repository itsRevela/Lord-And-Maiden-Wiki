"""Challenging-opponent pool generator + disk cache (phase-2 step 4).

Exhaustively build-searching every hero trio is ~10^24 battles -- infeasible (see
SIM_REDESIGN_SPEC.md). So this is TWO-STAGE:
  A) RANK candidate hero trios using a STRONG FIXED per-hero build (recommended modular skills +
     a matching skill stone + relic + best-tier gear, rpoint allocation), `battles` runs vs a
     reference opponent set -> keep the user's top-X.
  B) genetically OPTIMISE each top-X survivor's full build (the expensive search only on finalists).
The top-X optimised formations are cached to disk (survives refresh/restart) and loaded as the
opponent pool for the main single-formation search. Opponents are fully built (no empty slots,
best armor/messenger/accessories, relic on) -- genuinely challenging.
"""
import itertools
import json
import os
import random
from concurrent.futures import ProcessPoolExecutor, as_completed

from . import data as datamod
from .combat import Battle
from .model import BuildSpec, ModelConfig, build_team, fresh_units
from .optimize import (_default_modular, _main_key, _repair_loadout, _skill_pool,
                       optimize_formation)
from .search import SearchOptions, sample_opponents

CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "opponent_cache.json")
_RP = {"attack": "atk", "defense": "def", "ruin": "ruin", "speed": "speed"}


def _rpoint_alloc(g, hid):
    """The hero's recommended (rpoint) primary stat -> allocated_stat."""
    d = ((g.hero(hid).get("rpoint") or {}).get("distribution")) or {}
    if not d:
        return "atk"
    best = max(_RP, key=lambda k: d.get(k, 0.0))
    return _RP[best] if d.get(best, 0.0) > 0 else "atk"


def _def_gear(g):
    armor = g.max_tier_armor_sets(); msgr = g.messenger_items()
    accl = g.accessory_items("left"); accr = g.accessory_items("right")
    return {"armor_set_id": armor[0][0] if armor else None,
            "messenger_id": msgr[0][0] if msgr else None,
            "acc_left_id": accl[0][0] if accl else None,
            "acc_right_id": accr[0][0] if accr else None}


def _strong_team_specs(g, trio, gear, cmd_index=0):
    """A strong FIXED build for ALL 3 opponent heroes that obeys per-FORMATION skill uniqueness
    (no modular/stone shared across heroes, no modular == any main). Each hero: recommended
    modular skills + a stone reinforcing modular 0 + relic + best-tier gear + rpoint allocation.
    The recommended modulars are picked per hero then repaired across the trio (same rule as the
    player optimizer), so opponents are valid in-game formations -- not just challenging (#9)."""
    pool = _skill_pool(g)
    mains = [_main_key(g, h) for h in trio]
    raw = tuple(_default_modular(g, hid, pool, mains[k], random.Random(hid))
                for k, hid in enumerate(trio))
    loadout = _repair_loadout(random.Random(sum(trio) + 1), raw, {"pool": pool, "mains": mains})
    specs = []
    for k, hid in enumerate(trio):
        m0, m1 = loadout[k]
        keys = (m0, m1, m0)         # 2 modular + stone reinforcing modular 0
        specs.append(BuildSpec(hero_id=hid, soldier_type=int(g.hero(hid)["rst"]["id"]),
                               is_commander=(k == cmd_index), skill_keys=keys,
                               allocated_stat=_rpoint_alloc(g, hid), relic_on=True, gear=gear))
    return specs


def build_opponent_team(g, formation, cfg):
    """Build an opponent CombatUnit team from a cached/full formation (list of 3 hero dicts:
    {hero_id, troop, is_commander, skill_keys?, allocated_stat?, gear?}) OR legacy tuples
    (hero_id, troop, is_commander) -> minimal build."""
    specs = []
    for slot in formation:
        if isinstance(slot, dict):
            specs.append(BuildSpec(
                hero_id=int(slot["hero_id"]), soldier_type=int(slot["troop"]),
                is_commander=bool(slot.get("is_commander")),
                skill_keys=tuple(tuple(k) for k in slot["skill_keys"]) if slot.get("skill_keys") else None,
                allocated_stat=slot.get("allocated_stat"),
                relic_on=bool(slot.get("relic_on", True)), gear=slot.get("gear")))
        else:
            hid, tt, ic = slot
            specs.append(BuildSpec(hero_id=int(hid), soldier_type=int(tt), is_commander=bool(ic)))
    return build_team(g, specs, side=1, cfg=cfg, fight_pos_base=4)


# ---- stage A: rank candidate trios with a strong fixed build ----
def _rank_payload(payload):
    g = datamod.load()
    cfg = ModelConfig(**payload["cfg"])
    trio = payload["trio"]; gear = payload["gear"]
    specs = _strong_team_specs(g, trio, gear)
    player = build_team(g, specs, side=0, cfg=cfg, fight_pos_base=1)
    refs = [build_opponent_team(g, opp, cfg) for opp in payload["refs"]]
    wins = n = 0
    s = payload["seed"]
    for ref in refs:
        for _ in range(payload["battles"]):
            if Battle(g, cfg, fresh_units(player), fresh_units(ref), random.Random(s)).run().winner == 0:
                wins += 1
            n += 1; s += 1
    return trio, (wins / n if n else 0.0)


def _candidate_trios(g, scope, max_trios, seed, exclude=()):
    ex = set(exclude)
    ids = [h for h in g.heroes if h not in ex]
    if scope == "5star":
        ids = [h for h in ids if g.hero(h)["star"] >= 5]
    rng = random.Random(seed)
    if scope == "all" or len(ids) <= 26:           # full enumeration if feasible
        trios = list(itertools.combinations(sorted(ids), 3))
        if max_trios and len(trios) > max_trios:
            trios = rng.sample(trios, max_trios)
        return [tuple(t) for t in trios]
    # large roster -> sample distinct trios
    seen = set(); out = []
    weights = [max(1, g.hero(h)["star"]) ** 2 for h in ids]
    attempts = 0
    while len(out) < (max_trios or 600) and attempts < (max_trios or 600) * 40:
        attempts += 1
        t = tuple(sorted(rng.sample(ids, 3)))
        if t not in seen:
            seen.add(t); out.append(t)
    return out


def _trio_label(g, trio):
    """Human-readable matchup label for progress display: 'HeroA / HeroB / HeroC'."""
    def nm(hid):
        h = g.hero(int(hid)) or {}
        return h.get("name_en") or h.get("name") or str(hid)
    return " / ".join(nm(h) for h in trio)


def generate_opponents(opts: SearchOptions, progress=None, top_x=40, scope="5star",
                       max_trios=600, ref_n=12, battles=10,
                       opt_generations=12, opt_pop=24, exclude=()):
    """Two-stage strong-opponent pool. Returns {generated, scope, formations:[...]} and caches it."""
    g = datamod.load()
    cfg_dict = __import__("dataclasses").asdict(opts.cfg)
    gear = _def_gear(g)
    refs = sample_opponents(g, ref_n, opts.seed, exclude=exclude)   # reference set (legacy tuples)
    trios = _candidate_trios(g, scope, max_trios, opts.seed, exclude=exclude)
    workers = opts.workers or (os.cpu_count() or 2)
    total = len(trios) + top_x
    payloads = [{"trio": list(t), "gear": gear, "refs": refs, "battles": battles,
                 "cfg": cfg_dict, "seed": opts.seed + i * 101} for i, t in enumerate(trios)]
    scored = []
    if workers <= 1:
        for i, pl in enumerate(payloads):
            scored.append(_rank_payload(pl))
            if progress and i % 5 == 0:
                progress(len(scored), total, "Ranking trios · " + _trio_label(g, pl["trio"]))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_rank_payload, pl) for pl in payloads]
            for fut in as_completed(futs):
                res = fut.result()
                scored.append(res)
                if progress:
                    progress(len(scored), total, "Ranking trios · " + _trio_label(g, res[0]))
    scored.sort(key=lambda ts: ts[1], reverse=True)
    survivors = [t for t, _ in scored[:top_x]]

    # stage B: optimise each survivor's full build (commander = slot 0)
    formations = []
    for j, trio in enumerate(survivors):
        sub = SearchOptions(n_battles=max(8, opts.n_battles // 3), n_opponents=ref_n,
                            seed=opts.seed + 7, workers=workers, cfg=opts.cfg)
        rep = optimize_formation(list(trio), sub, commander_index=0,
                                 allocated_stats=[_rpoint_alloc(g, h) for h in trio],
                                 search_axes=("troop", "skills", "stone", "armor", "messenger", "accessory"),
                                 objective="win", top_n=1, use_opponent_cache=False,
                                 generations=opt_generations, pop_size=opt_pop,
                                 ga_battles=8, ga_opponents=min(8, ref_n))
        formations.append(_formation_from_build(g, trio, rep["builds"][0]))
        if progress:
            progress(len(trios) + j + 1, total,
                     "Optimizing finalist %d/%d · %s" % (j + 1, len(survivors), _trio_label(g, trio)))

    cache = {"scope": scope, "top_x": top_x, "generated": len(formations), "formations": formations}
    save_opponent_cache(cache)
    return cache


def _formation_from_build(g, trio, build):
    """Serialize an optimized build (optimize_formation detail) into a cacheable opponent
    formation: per-hero full BuildSpec params (keys/gear ids) + a display label."""
    NM = {"Infantry": 1, "Archer": 2, "Cavalry": 3, "Chariot": 4}
    armor = {v: k for k, v in g.max_tier_armor_sets()}
    msgr = {v: k for k, v in g.messenger_items()}
    accl = {v: k for k, v in g.accessory_items("left")}
    accr = {v: k for k, v in g.accessory_items("right")}
    out = []
    for hero in build["heroes"]:
        hid = hero["id"]
        keys = _keys_from_names(g, hero["modular_skills"]) or \
            [(int(s["st"]), int(s["id"])) for s in g.hero(hid).get("modular_default", [])]
        stone = _keys_from_names(g, [hero["skill_stone"]])
        skill_keys = keys[:2] + (stone[:1] if stone else keys[:1])     # 2 modular + stone
        acc = hero.get("accessories") or ["", ""]
        out.append({
            "hero_id": hid, "troop": NM.get(hero["troop"], 2),
            "is_commander": hero["is_commander"],
            "skill_keys": [list(k) for k in skill_keys],
            "allocated_stat": (hero.get("allocation") if hero.get("allocation") != "none" else None),
            "relic_on": True,
            "gear": {"armor_set_id": armor.get(hero.get("armor_set")),
                     "messenger_id": msgr.get(hero.get("messenger")),
                     "acc_left_id": accl.get(acc[0]), "acc_right_id": accr.get(acc[1])},
            "label": ("[CMD] " if hero["is_commander"] else "") + "%s(%s)" % (hero["name"], hero["troop"]),
        })
    return {"label": " / ".join(o["label"] for o in out), "heroes": out}


def _keys_from_names(g, names):
    """Resolve skill display names -> (st,id) keys (best-effort, cached index)."""
    if not hasattr(_keys_from_names, "_idx"):
        _keys_from_names._idx = {sk.get("name_en"): (int(k[0]), int(k[1]))
                                 for k, sk in g.skills.items()}
    idx = _keys_from_names._idx
    return [idx[n] for n in names if n in idx]


def save_opponent_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)


def load_opponent_cache():
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None
