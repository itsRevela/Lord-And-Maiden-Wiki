"""CLI for the Lord & Maiden battle simulator.

Examples (run from the repo root):
  python -m simulator.run --heroes 1 2 3
  python -m simulator.run --heroes 1 2 3 --all-troop-combos --battles 80 --opponents 50
  python -m simulator.run --list-heroes

Writes a full JSON report to simulator/runs/<timestamp>_<heroes>.json and prints an
ASCII summary. Uses all CPU cores by default.
"""
import argparse
import io
import json
import os
import sys
import time

from simulator.engine import data as datamod
from simulator.engine.model import ModelConfig
from simulator.engine.optimize import optimize_formation
from simulator.engine.search import SearchOptions, run_search

RUNS_DIR = os.path.join(os.path.dirname(__file__), "runs")


def _progress(done, total):
    bar = int(30 * done / total)
    pct = 100.0 * done / total
    sys.stdout.write("\r  [%s%s] %d/%d builds (%.0f%%)"
                     % ("#" * bar, "-" * (30 - bar), done, total, pct))
    sys.stdout.flush()
    if done == total:
        sys.stdout.write("\n")


def list_heroes():
    g = datamod.load()
    rows = sorted(g.heroes.values(), key=lambda h: (-h["star"], h["id"]))
    out = io.open(os.path.join(os.path.dirname(__file__), "_heroes_list.txt"), "w", encoding="utf-8")
    out.write("id   star race    rst       role            name\n")
    for h in rows:
        out.write("%-4d %d*   %-7s %-9s %-15s %s\n" % (
            h["id"], h["star"], h["race"]["name_en"], h["rst"]["soldier_type_en"],
            (h.get("role") or {}).get("name_en", "?"), h["name_en"]))
    out.close()
    print("Wrote %d heroes to simulator/_heroes_list.txt" % len(rows))


def main():
    ap = argparse.ArgumentParser(description="Lord & Maiden battle simulator")
    ap.add_argument("--heroes", type=int, nargs=3, metavar="ID",
                    help="the 3 hero ids to optimise (see --list-heroes)")
    ap.add_argument("--battles", type=int, default=60, help="battles per (build, opponent)")
    ap.add_argument("--opponents", type=int, default=40, help="opponent formations to test against")
    ap.add_argument("--all-troop-combos", action="store_true",
                    help="report every troop combo (default: best troop set only)")
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--workers", type=int, default=0, help="0 = all CPU cores")
    ap.add_argument("--top", type=int, default=10, help="how many builds to print")
    ap.add_argument("--optimize", action="store_true",
                    help="genetic search over commander + troops + the 6 modular skills (any skill)")
    ap.add_argument("--objective", default="win", choices=["win", "early", "mid", "late", "all"],
                    help="what --optimize maximises")
    ap.add_argument("--list-heroes", action="store_true")
    args = ap.parse_args()

    if args.list_heroes:
        list_heroes()
        return
    if not args.heroes:
        ap.error("provide --heroes ID ID ID  (or --list-heroes)")

    g = datamod.load()
    for h in args.heroes:
        if h not in g.heroes:
            ap.error("hero id %d is not a playable hero (see --list-heroes)" % h)

    opts = SearchOptions(
        n_battles=args.battles, n_opponents=args.opponents,
        select_optimal_troop=not args.all_troop_combos,
        seed=args.seed, workers=args.workers, cfg=ModelConfig(),
    )
    names = [g.hero(h)["name_en"] for h in args.heroes]
    print("Formation: %s" % " / ".join(names))
    os.makedirs(RUNS_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    t0 = time.time()

    if args.optimize:
        print("  genetic search over commander + troops + 6 modular skills "
              "(objective: %s), on %s cores" % (args.objective, args.workers or os.cpu_count()))
        report = optimize_formation(args.heroes, opts, progress=_progress, objective=args.objective)
        dt = time.time() - t0
        report["elapsed_seconds"] = round(dt, 1)
        fname = os.path.join(RUNS_DIR, "%s_%s_opt.json" % (stamp, "-".join(map(str, args.heroes))))
        with io.open(fname, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("\n=== OPTIMISED BUILD (%.1fs) ===" % dt)
        print("Best: %s" % report["best_label"])
        print("Win rate: %.1f%% | objective(%s) = %s"
              % (100 * report["win_rate"], args.objective,
                 ("%.1f%%" % (100 * report["win_rate"])) if args.objective == "win"
                 else ("%.0f" % report["windows"][args.objective])))
        for h in report["heroes"]:
            print("  %s%s (%s)  main: %s  | modular: %s"
                  % ("[CMD] " if h["is_commander"] else "      ", h["name"], h["troop"],
                     h["main_skill"], " + ".join(h["modular_skills"])))
        print("\nFull report: %s" % fname)
        return

    total_battles = opts.n_battles * opts.n_opponents * 192
    print("  %d builds x %d opponents x %d battles = %d battles, on %s cores"
          % (192, opts.n_opponents, opts.n_battles, total_battles, args.workers or os.cpu_count()))
    report = run_search(args.heroes, opts, progress=_progress)
    dt = time.time() - t0
    report["elapsed_seconds"] = round(dt, 1)
    fname = os.path.join(RUNS_DIR, "%s_%s.json" % (stamp, "-".join(map(str, args.heroes))))
    with io.open(fname, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n=== RESULT (%.1fs) ===" % dt)
    print("Best overall:  %s" % report["best_overall"])
    print("Best by window:")
    for w in ("early", "mid", "late", "all"):
        print("  %-6s -> %s" % (w, report["best_by_window"][w]))
    print("\nTop %d builds by win rate:" % args.top)
    print("  win%%  +/-   bouts  early/mid/late dmg(mean)   build")
    for r in report["ranking"][:args.top]:
        wd = r["windows"]
        print("  %4.1f  %3.1f  %4.1f   %8.0f %8.0f %8.0f   %s" % (
            100 * r["win_rate"], 100 * r["win_rate_ci95"], r["avg_bouts"],
            wd["early"]["mean"], wd["mid"]["mean"], wd["late"]["mean"], r["label"]))
    print("\nFull report: %s" % fname)


if __name__ == "__main__":
    main()
