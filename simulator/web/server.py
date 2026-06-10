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
  GET  /api/jobs/<job_id>       -> {status, done, total, result?}
  GET  /portraits/<file>        -> hero portrait PNG (fallback 404 -> UI uses avatar)
"""
import os
import threading
import uuid

from flask import Flask, jsonify, request, send_from_directory

from simulator.engine import data as datamod
from simulator.engine.model import ModelConfig
from simulator.engine.optimize import optimize_formation
from simulator.engine.search import SearchOptions, run_search

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


def _run_job(job_id, heroes, opts, mode, objective):
    def progress(done, total):
        with _LOCK:
            _JOBS[job_id]["done"] = done
            _JOBS[job_id]["total"] = total
    try:
        if mode == "optimize":
            report = optimize_formation(heroes, opts, progress=progress, objective=objective)
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
    mode = body.get("mode", "rank")           # "rank" | "optimize"
    objective = body.get("objective", "win")  # win | early | mid | late | all
    opts = SearchOptions(
        n_battles=int(body.get("battles", 60)),
        n_opponents=int(body.get("opponents", 40)),
        select_optimal_troop=bool(body.get("select_optimal_troop", True)),
        seed=int(body.get("seed", 12345)),
        workers=int(body.get("workers", 0)),
        cfg=ModelConfig(),
    )
    job_id = uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[job_id] = {"status": "running", "done": 0,
                         "total": 24 if mode == "optimize" else 192, "mode": mode}
    threading.Thread(target=_run_job, args=(job_id, heroes, opts, mode, objective),
                     daemon=True).start()
    return jsonify({"job_id": job_id})


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
