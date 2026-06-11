"""Flask API for the Lord & Maiden battle simulator UI.

Serves the playable hero roster and runs combinatorial searches as background jobs
with progress polling. Pairs with the Next.js front-end in simulator/web/.

Run from the repo root:
  python -m simulator.web.server          # http://localhost:5000

Endpoints:
  GET  /api/heroes              -> playable roster (+ portrait availability)
  GET  /api/meta                -> enums / model notes / server-side caveat
  POST /api/simulate            -> {job_id}; body: {heroes:[a,b,c], battles, opponents,
                                    select_optimal_troop, seed}
  GET  /api/opponents           -> cached challenging-opponent pool status {generated, scope, ...}
  POST /api/generate_opponents  -> {job_id}; body: {top_x, scope, max_trios, battles, seed, workers}
  GET  /api/jobs/<job_id>       -> {status, done, total, result?}
  GET  /portraits/<file>        -> hero portrait PNG (fallback 404 -> UI uses avatar)
"""
import os
import threading
import uuid

from flask import Flask, jsonify, request, send_from_directory

from simulator.engine import data as datamod
from simulator.engine.model import ModelConfig
from simulator.engine.optimize import optimize_formation, ALL_AXES
from simulator.engine.opponents import (_candidate_trios, generate_opponents,
                                        load_opponent_cache)
from simulator.engine.search import SearchOptions, run_search

_ALLOC = {"atk", "def", "ruin", "speed"}

app = Flask(__name__)
PORTRAITS_DIR = os.path.join(os.path.dirname(__file__), "public", "portraits")

_G = datamod.load()
_JOBS = {}
_LOCK = threading.Lock()


@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


def _has_portrait(icon):
    return os.path.exists(os.path.join(PORTRAITS_DIR, "%s.png" % icon))


@app.route("/api/heroes")
def heroes():
    out = []
    for h in sorted(_G.heroes.values(), key=lambda x: (-x["star"], x["id"])):
        out.append({
            "id": h["id"], "name": h["name_en"], "star": h["star"],
            "race": h["race"]["name_en"], "rst": h["rst"]["soldier_type_en"],
            "role": (h.get("role") or {}).get("name_en", "?"),
            "icon": h["icon"], "has_portrait": _has_portrait(h["icon"]),
            "main_skill": h["main_skill"]["name_en"],
            "modular": [s["name_en"] for s in h.get("modular_default", [])],
        })
    return jsonify(out)


@app.route("/api/meta")
def meta():
    return jsonify({
        "soldier_types": _G.soldier_type_name,
        "restraint": {"triangle": _G.restraint_triangle,
                      "modifier": _G.restraint_modifier},
        "round_count": _G.round_count,
        "windows": {"early": "rounds 1-2", "mid": "rounds 3-4", "late": "rounds 5+",
                    "all": "all 8 rounds"},
        "caveat": ("Combat is server-authoritative; the exact damage formula is not in "
                   "the game client. This simulator is a transparent, configurable "
                   "rules-based model. Rankings are model-relative but comparable across "
                   "builds (the same model applies to all)."),
    })


@app.route("/portraits/<path:fname>")
def portraits(fname):
    return send_from_directory(PORTRAITS_DIR, fname)


def _run_job(job_id, heroes, opts, mode, objective, extra):
    def progress(done, total):
        with _LOCK:
            _JOBS[job_id]["done"] = done
            _JOBS[job_id]["total"] = total
    try:
        if mode == "optimize":
            report = optimize_formation(
                heroes, opts, progress=progress, objective=objective,
                commander_index=extra["commander_index"],
                allocated_stats=extra["allocated_stats"],
                search_axes=extra["search_axes"], top_n=extra["top_n"],
                troop_types=extra["troop_types"], generations=extra["generations"])
        else:
            report = run_search(heroes, opts, progress=progress)
        with _LOCK:
            _JOBS[job_id]["result"] = report
            _JOBS[job_id]["status"] = "done"
    except Exception as e:  # noqa: BLE001 - surface to client
        with _LOCK:
            _JOBS[job_id]["status"] = "error"
            _JOBS[job_id]["error"] = repr(e)


@app.route("/api/simulate", methods=["POST", "OPTIONS"])
def simulate():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.get_json(force=True) or {}
    heroes = [int(x) for x in body.get("heroes", [])]
    if len(heroes) != 3 or any(h not in _G.heroes for h in heroes):
        return jsonify({"error": "provide exactly 3 valid playable hero ids"}), 400
    if len(set(heroes)) != 3:
        return jsonify({"error": "the 3 heroes must be distinct — a formation can't field the "
                                 "same hero twice (SP / 4-star / 5-star name-variants are separate heroes)"}), 400
    mode = body.get("mode", "optimize")       # "optimize" (new default) | "rank" (legacy)
    objective = body.get("objective", "win")  # win | casualty | early | mid | late | all

    # --- new optimize inputs: fixed commander + per-hero allocation + toggleable axes ---
    commander_index = int(body.get("commander_index", 0))
    if not 0 <= commander_index <= 2:
        return jsonify({"error": "commander_index must be 0, 1, or 2"}), 400
    raw_alloc = body.get("allocated_stats") or [None, None, None]
    allocated_stats = []
    for a in (list(raw_alloc) + [None, None, None])[:3]:
        a = (a or "").lower() if isinstance(a, str) else None
        allocated_stats.append(a if a in _ALLOC else None)
    axes = body.get("search_axes")
    search_axes = tuple(x for x in (axes if isinstance(axes, list) else ALL_AXES) if x in ALL_AXES) \
        or ALL_AXES
    top_n = max(1, min(int(body.get("top_n", 20)), 50))
    raw_tt = body.get("troop_types") or [None, None, None]
    troop_types = []                          # per-hero troop (1..4) used when troop axis is OFF
    for t in (list(raw_tt) + [None, None, None])[:3]:
        try:
            t = int(t)
        except (TypeError, ValueError):
            t = None
        troop_types.append(t if t in (1, 2, 3, 4) else None)

    opts = SearchOptions(
        n_battles=int(body.get("battles", 60)),
        n_opponents=int(body.get("opponents", 40)),
        select_optimal_troop=bool(body.get("select_optimal_troop", True)),
        seed=int(body.get("seed", 12345)),
        workers=int(body.get("workers", 0)),     # 0 = all cores; user-configurable
        cfg=ModelConfig(),
    )
    generations = int(body.get("generations", 24))
    extra = {"commander_index": commander_index, "allocated_stats": allocated_stats,
             "search_axes": search_axes, "top_n": top_n, "generations": generations,
             "troop_types": troop_types}
    job_id = uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[job_id] = {"status": "running", "done": 0,
                         "total": (generations + top_n) if mode == "optimize" else 192, "mode": mode}
    threading.Thread(target=_run_job, args=(job_id, heroes, opts, mode, objective, extra),
                     daemon=True).start()
    return jsonify({"job_id": job_id})


def _cache_summary(cache):
    """Compact view of the opponent cache for the UI (labels only, no full builds)."""
    if not cache:
        return {"generated": 0, "scope": None, "top_x": None, "formations": []}
    return {"generated": cache.get("generated", 0), "scope": cache.get("scope"),
            "top_x": cache.get("top_x"),
            "formations": [{"label": f.get("label", "?")} for f in cache.get("formations", [])]}


@app.route("/api/opponents")
def opponents_status():
    return jsonify(_cache_summary(load_opponent_cache()))


def _run_opp_job(job_id, opts, params):
    def progress(done, total, label=None):
        with _LOCK:
            _JOBS[job_id]["done"] = done
            _JOBS[job_id]["total"] = total
            if label is not None:
                _JOBS[job_id]["label"] = label
    try:
        cache = generate_opponents(
            opts, progress=progress, top_x=params["top_x"], scope=params["scope"],
            max_trios=params["max_trios"], ref_n=params["ref_n"], battles=params["battles"],
            opt_generations=params["opt_generations"], opt_pop=params["opt_pop"])
        with _LOCK:
            _JOBS[job_id]["result"] = _cache_summary(cache)
            _JOBS[job_id]["status"] = "done"
    except Exception as e:  # noqa: BLE001 - surface to client
        with _LOCK:
            _JOBS[job_id]["status"] = "error"
            _JOBS[job_id]["error"] = repr(e)


@app.route("/api/generate_opponents", methods=["POST", "OPTIONS"])
def generate_opponents_route():
    if request.method == "OPTIONS":
        return ("", 204)
    body = request.get_json(force=True) or {}
    top_x = max(1, min(int(body.get("top_x", 40)), 100))
    scope = body.get("scope", "5star")
    if scope not in ("5star", "all"):
        scope = "5star"
    max_trios = max(50, min(int(body.get("max_trios", 600)), 5000))
    battles = max(2, min(int(body.get("battles", 10)), 50))
    ref_n = max(4, min(int(body.get("ref_n", 12)), 40))
    opt_generations = max(4, min(int(body.get("generations", 12)), 60))
    opt_pop = max(8, min(int(body.get("pop_size", 24)), 80))
    opts = SearchOptions(
        n_battles=int(body.get("n_battles", 24)), n_opponents=ref_n,
        seed=int(body.get("seed", 12345)), workers=int(body.get("workers", 0)),
        cfg=ModelConfig())
    # exact, stable progress total (#7): trios actually evaluated + top_x optimised finalists
    n_trios = len(_candidate_trios(_G, scope, max_trios, opts.seed))
    params = {"top_x": top_x, "scope": scope, "max_trios": max_trios, "battles": battles,
              "ref_n": ref_n, "opt_generations": opt_generations, "opt_pop": opt_pop}
    job_id = uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[job_id] = {"status": "running", "done": 0, "total": n_trios + top_x,
                         "mode": "generate_opponents"}
    threading.Thread(target=_run_opp_job, args=(job_id, opts, params), daemon=True).start()
    return jsonify({"job_id": job_id, "total": n_trios + top_x})


@app.route("/api/jobs/<job_id>")
def job_status(job_id):
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return jsonify({"error": "unknown job"}), 404
        # shallow copy without mutating
        resp = {k: v for k, v in job.items()}
    return jsonify(resp)


if __name__ == "__main__":
    # reloader off: it conflicts with the ProcessPoolExecutor used by the search
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True)
