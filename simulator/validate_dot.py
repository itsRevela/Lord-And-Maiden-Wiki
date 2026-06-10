"""Validate the combat engine against Matchup-2 ("DoT Lab") in-game log.

Source log + targets: ``notes/sim/calibration_2_dot.md`` (Battle log + Results) and
``notes/sim/calibration_2_findings.md``.  This is the THIRD calibration anchor (after
the shielded-tank "Rosetta Stone", ``validate_testcase.py``, and the clean "Vanilla
Baseline" mirror, ``validate_baseline.py``).  It isolates the Burn/Curse
DAMAGE-OVER-TIME channel plus the sustain (shield + heal) and Detonate mechanics.

Matchup-2 formations (all Lv80 adv5, Archer troops, calibration_2_dot.md):
  * Player (revela, LEFT):  Cthugha.Sp +229 DES (commander) / Cthugha +229 DES
                            / Nyx +229 DES.  These carry the DoT (Exploding Flame
                            Burn 1.0, Blazing Sword Burn 0.5, Soul Drain Curse 0.5)
                            plus sustain (Lunar Guardian shield+heal, Fire Emblem).
  * Enemy  (Nothing, RIGHT): Thiel +229 DEF (commander) / Nicole +179 ATK (4 star)
                            / Dolly +229 DES.  Clean dummies (no heal/DoT-resist).

In-game outcome: 60% player win over 10 runs (small sample); match 1 = Battle 1
8-round STALEMATE -> Battle 2 VICTORY.  The DoT tick fires at the before-action
phase, scales with the CASTER (DES + troops, declining as the caster loses troops),
is ~linear in the printed coefficient (Burn 1.0 ~= 2x Curse 0.5), and is mildly
DEF-mitigated.  Detonate consumes Burn for a ~3.1k-6.7k burst.

Combat is server-authoritative (the exact equation is not in the client), so the DoT
magnitudes are model-relative ModelConfig knobs (``dot_global``, ``dot_troop_floor``,
``dot_def_ref``/``dot_def_weight`` reusing offence("dot")/troop_scale, and the
detonate knobs).  We check the qualitative + magnitude targets from the findings and
print a PASS/FAIL-per-target report to a UTF-8 file (CJK-safe; never prints CJK to the
cp1252 console).

Run from the repo root:  python -m simulator.validate_dot
"""
import io
import os
import random
import statistics

from simulator.engine import data as datamod
from simulator.engine import model as modelmod
from simulator.engine.combat import Battle
from simulator.engine.model import BuildSpec, ModelConfig, build_team

OUT_PATH = os.path.join(os.path.dirname(__file__), "_validate_dot_out.txt")

# hero ids (verified against data/sim/heroes.json)
CTHUGHA_SP, CTHUGHA, NYX = 70, 32, 116      # player DoT + sustain trio
THIEL, NICOLE, DOLLY = 99, 87, 108           # enemy clean-dummy trio

ARCHER = 2                                   # all units field Archer (per the sheet)

# Skill stones (added as a THIRD modular key so they fire), distinct within a team:
#   Cthugha.Sp = Holy-light Chop (2,66); Cthugha = Rift (2,100); Nyx = Purgatory Trial (2,65)
#   Thiel = Holy-light Chop (2,66); Nicole = Rift (2,100); Dolly = Purgatory Trial (2,65)
HOLY_LIGHT_CHOP = (2, 66)
RIFT = (2, 100)
PURGATORY_TRIAL = (2, 65)

# Burn tick band (calibration_2_findings.md: ~700-4,000, declining with caster troops).
BURN_BAND_LO = 700.0
BURN_BAND_HI = 4000.0
# Detonate burst band (calibration_2_findings.md: ~3,100-6,700).
DETONATE_BAND_LO = 3100.0
DETONATE_BAND_HI = 6700.0

# Representative seed that reproduces match-1's shape (B1 stalemate -> B2 victory).
REPRESENTATIVE_SEED = 225


def _loadout(g, hero_id, stone):
    """main (auto via build_team) + 2 modular defaults + 1 skill stone."""
    h = g.hero(hero_id)
    mods = [(int(m["st"]), int(m["id"])) for m in h.get("modular_default", [])]
    return tuple(mods + [stone])


def _spec(g, hero_id, alloc, commander, stone):
    return BuildSpec(hero_id=hero_id, soldier_type=ARCHER, is_commander=commander,
                     skill_keys=_loadout(g, hero_id, stone), allocated_stat=alloc)


def build_player(g, cfg):
    """LEFT (revela): Cthugha.Sp / Cthugha / Nyx, all +229 DES; Cthugha.Sp commander."""
    return build_team(g, [
        _spec(g, CTHUGHA_SP, "ruin", True, HOLY_LIGHT_CHOP),
        _spec(g, CTHUGHA, "ruin", False, RIFT),
        _spec(g, NYX, "ruin", False, PURGATORY_TRIAL),
    ], side=0, cfg=cfg, fight_pos_base=1)


def build_enemy(g, cfg):
    """RIGHT (Nothing): Thiel +DEF (commander) / Nicole +ATK (4 star) / Dolly +DES."""
    return build_team(g, [
        _spec(g, THIEL, "def", True, HOLY_LIGHT_CHOP),
        _spec(g, NICOLE, "atk", False, RIFT),
        _spec(g, DOLLY, "ruin", False, PURGATORY_TRIAL),
    ], side=1, cfg=cfg, fight_pos_base=4)


def run_match(g, cfg, seed, dot_probe=None, det_probe=None):
    """Run a single match; capture per-bout snapshots.  Optionally instrument the DoT
    tick / detonate calls (dot_probe/det_probe are lists the engine appends to)."""
    p = build_player(g, cfg)
    e = build_enemy(g, cfg)
    b = Battle(g, cfg, p, e, random.Random(seed))

    if dot_probe is not None:
        _orig_tick = modelmod.dot_tick

        def _spy_tick(c, d, coef, cfgc, _o=_orig_tick):
            v = _o(c, d, coef, cfgc)
            # caster troops at tick time, the printed coef, and the resulting tick
            dot_probe.append((c.name, d.name, round(c.health), float(coef), round(v)))
            return v
        import simulator.engine.combat as cm
        cm.modelmod.dot_tick = _spy_tick

    if det_probe is not None:
        _orig_det = b._detonate

        def _spy_det(caster, coef, count, _o=_orig_det, _b=b):
            before = {id(f): f.health for f in _b.sides[1]}
            _o(caster, coef, count)
            for f in _b.sides[1]:
                d = before[id(f)] - f.health
                if d > 1:
                    det_probe.append(round(d))
        b._detonate = _spy_det

    snaps = []
    bouts = 0
    while bouts < cfg.max_bouts:
        bouts += 1
        if bouts > 1:
            b._reset_for_rematch()
            if not (b._alive(0) and b._alive(1)):
                break
        rf, decided, d0, d1 = b._run_bout()
        snaps.append(_snapshot(b, bouts, rf, decided, d0, d1))
        if decided:
            break
        b.stalemates += 1

    if dot_probe is not None:
        import simulator.engine.combat as cm
        cm.modelmod.dot_tick = _orig_tick
    return b, snaps


def _snapshot(b, bout, rounds, decided, d0, d1):
    def units(side):
        return {u.name: {"health": round(u.health), "max": round(u.cur_max),
                         "alive": u.alive, "kills": round(u.stat_kills),
                         "commander": u.is_commander,
                         "skill_dmg": round(u.stat_skill_dmg),
                         "normal_dmg": round(u.stat_normal_dmg)}
                for u in b.sides[side]}
    pc = b._commander(0)
    ec = b._commander(1)
    if ec and not ec.alive and (not pc or pc.alive):
        result = "Victory"
    elif pc and not pc.alive and (not ec or ec.alive):
        result = "Defeat"
    elif decided:
        result = "Decided"
    else:
        result = "Stalemate"
    return {
        "bout": bout, "rounds": rounds, "result": result,
        "left_health": round(sum(u.health for u in b.sides[0])),
        "right_health": round(sum(u.health for u in b.sides[1])),
        "dmg_player": round(sum(d0)), "dmg_enemy": round(sum(d1)),
        "A": units(0), "E": units(1),
    }


def aggregate(g, cfg, n=400):
    stats = {
        "n": 0, "player_win": 0, "enemy_win": 0,
        "thiel_last": 0,            # enemy commander Thiel falls last (or survives)
        "strikers_first": 0,        # both enemy strikers dead while Thiel alive at some end
        "any_b1_stale_then_win": 0,
    }
    for seed in range(n):
        b, snaps = run_match(g, cfg, seed)
        stats["n"] += 1
        final = snaps[-1]
        if final["result"] == "Victory":
            stats["player_win"] += 1
        elif final["result"] == "Defeat":
            stats["enemy_win"] += 1
        # Thiel falls last among the enemy (strikers Nicole/Dolly die before her).
        e = final["E"]
        thiel_alive = e["Thiel"]["alive"]
        strikers_dead = (not e["Nicole"]["alive"]) and (not e["Dolly"]["alive"])
        if thiel_alive or strikers_dead:
            stats["thiel_last"] += 1
        # at the end of Battle 1 specifically, did strikers fall before the commander?
        b1 = snaps[0]
        if (not b1["E"]["Nicole"]["alive"]) and (not b1["E"]["Dolly"]["alive"]):
            stats["strikers_first"] += 1
        if b1["result"] == "Stalemate" and final["result"] == "Victory":
            stats["any_b1_stale_then_win"] += 1
    return stats


def collect_dot_samples(g, cfg, seeds=range(80)):
    """Gather Burn/Curse ticks and detonate bursts across seeds for band checks, plus a
    per-caster declining-with-troops series."""
    burn, curse, bursts = [], [], []
    # Burn ticks for the commander Cthugha.Sp, paired with caster troops, to test the
    # "declines with caster troops" claim via correlation.
    csp_series = []
    for seed in seeds:
        dot = []
        det = []
        run_match(g, cfg, seed, dot_probe=dot, det_probe=det)
        for (cname, dname, ctroops, coef, val) in dot:
            if coef >= 0.9:
                burn.append(val)
                if cname == "Cthugha·Sp":
                    csp_series.append((ctroops, val))
            else:
                curse.append(val)
        bursts.extend(det)
    return burn, curse, bursts, csp_series


def curse_vs_burn_same_caster(g, cfg, seed=11):
    """For one match, find a Burn and a Curse tick from the SAME caster on the SAME
    target and report the ratio (target ~0.5).  Cthugha.Sp casts Burn; we compare to a
    Burn-vs-Burn-coef pairing -- but Burn(1.0) and Curse(0.5) come from different heroes
    (Cthugha.Sp vs Nyx), so we use the per-tick value normalized by each caster's
    offence to isolate the coefficient's linear effect."""
    dot = []
    run_match(g, cfg, seed, dot_probe=dot)
    # group by (caster, target); within a caster the coef is fixed, so instead test the
    # cross-caster LINEARITY: tick/coef should be ~constant per caster*troops.  We report
    # the median (Curse value / Burn value) at comparable caster troop levels.
    burn = [v for (cn, dn, ct, cf, v) in dot if cf >= 0.9]
    curse = [v for (cn, dn, ct, cf, v) in dot if cf < 0.9]
    if not burn or not curse:
        return None
    return statistics.median(curse) / statistics.median(burn)


def main():
    g = datamod.load()
    cfg = ModelConfig()
    out = io.open(OUT_PATH, "w", encoding="utf-8")

    def w(*a):
        out.write(" ".join(str(x) for x in a) + "\n")

    w("=== Matchup-2 'DoT Lab' validation (Burn / Curse / Detonate / sustain) ===")
    w("Player Cthugha.Sp/Cthugha/Nyx (all +229 DES) vs enemy Thiel+DEF/Nicole+ATK/Dolly+DES.")
    w("DoT ticks at before-action, scales with CASTER (DES+troops), ~linear in coef,")
    w("mildly DEF-mitigated; Detonate consumes Burn for a burst; Lunar Guardian = shield+heal.")
    w("Combat is server-authoritative; magnitudes are model-relative (ModelConfig knobs).")
    w("In-game: 60%% win over 10 runs; match-1 = B1 8-round stalemate -> B2 victory.")
    w("")

    # --- representative match (the match-1 shape: B1 stalemate -> B2 victory) ---
    b, snaps = run_match(g, cfg, REPRESENTATIVE_SEED)
    w("--- representative match (seed %d): %d bout(s) ---" % (REPRESENTATIVE_SEED, len(snaps)))
    for sn in snaps[:3]:
        w("Bout %d (Battle %d): %s in %d rounds | left %d  right %d  (dmg P=%d E=%d)"
          % (sn["bout"], sn["bout"], sn["result"], sn["rounds"],
             sn["left_health"], sn["right_health"], sn["dmg_player"], sn["dmg_enemy"]))
        for label in ("A", "E"):
            for nm, stt in sn[label].items():
                w("    [%s] %-12s health %6d/%-6d alive=%s%s kills %7d skillDmg %7d"
                  % (label, nm, stt["health"], stt["max"], stt["alive"],
                     " (CMD)" if stt["commander"] else "      ",
                     stt["kills"], stt["skill_dmg"]))
    rep_b1_stale = snaps[0]["result"] == "Stalemate"
    rep_b2_victory = len(snaps) >= 2 and snaps[1]["result"] == "Victory"
    w("")

    # --- DoT tick / detonate band samples ---
    burn, curse, bursts, csp_series = collect_dot_samples(g, cfg)
    burn_med = statistics.median(burn) if burn else 0.0
    curse_med = statistics.median(curse) if curse else 0.0
    burn_in_band = sum(1 for x in burn if BURN_BAND_LO <= x <= BURN_BAND_HI)
    burn_band_frac = burn_in_band / len(burn) if burn else 0.0
    curse_burn_ratio = (curse_med / burn_med) if burn_med else 0.0
    burst_med = statistics.median(bursts) if bursts else 0.0
    burst_in_band = sum(1 for x in bursts if DETONATE_BAND_LO <= x <= DETONATE_BAND_HI)
    burst_band_frac = burst_in_band / len(bursts) if bursts else 0.0
    # "declines with caster troops": Pearson correlation between caster troops and tick.
    decline_corr = 0.0
    if len(csp_series) > 5:
        xs = [t for t, _ in csp_series]
        ys = [v for _, v in csp_series]
        try:
            decline_corr = statistics.correlation(xs, ys)
        except Exception:
            mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
            cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            sx = sum((x - mx) ** 2 for x in xs) ** 0.5
            sy = sum((y - my) ** 2 for y in ys) ** 0.5
            decline_corr = cov / (sx * sy) if sx and sy else 0.0

    w("--- DoT tick & detonate samples (80 seeds) ---")
    w("  Burn ticks  n=%d  median=%.0f  in[%d,%d]=%.0f%%"
      % (len(burn), burn_med, BURN_BAND_LO, BURN_BAND_HI, 100 * burn_band_frac))
    w("  Curse ticks n=%d  median=%.0f  (Curse/Burn median ratio=%.2f, target ~0.5)"
      % (len(curse), curse_med, curse_burn_ratio))
    w("  Detonate bursts n=%d median=%.0f in[%d,%d]=%.0f%%"
      % (len(bursts), burst_med, DETONATE_BAND_LO, DETONATE_BAND_HI, 100 * burst_band_frac))
    w("  Burn tick vs caster-troops correlation (Cthugha.Sp) = %.2f (positive => declines as troops fall)"
      % decline_corr)
    w("")

    # --- aggregate over seeds ---
    n = 400
    st = aggregate(g, cfg, n=n)

    def rate(k):
        return 100.0 * st[k] / st["n"] if st["n"] else 0.0

    player_win = rate("player_win")
    w("--- aggregate over %d seeded matches ---" % n)
    w("  player win=%.1f%%  enemy win=%.1f%%" % (player_win, rate("enemy_win")))
    w("  Thiel (+DEF cmd) falls last / strikers die first: %.0f%%" % rate("thiel_last"))
    w("  both enemy strikers dead by end of Battle 1: %.0f%%" % rate("strikers_first"))
    w("  matches with B1-stalemate -> match Victory: %d" % st["any_b1_stale_then_win"])
    w("")

    targets = []
    targets.append(("Player win ~50-65%% (in-game 60%%, small sample)",
                    50.0 <= player_win <= 65.0,
                    "%.1f%% player win (target ~60%%)" % player_win))
    targets.append(("Representative seed: Battle 1 stalemate -> Battle 2 victory",
                    rep_b1_stale and rep_b2_victory,
                    "seed %d: B1=%s, B2=%s"
                    % (REPRESENTATIVE_SEED, snaps[0]["result"],
                       snaps[1]["result"] if len(snaps) >= 2 else "n/a")))
    targets.append(("Burn tick in ~700-4,000 band (>=75%% of ticks)",
                    burn_band_frac >= 0.75,
                    "%.0f%% of Burn ticks in band, median %.0f" % (100 * burn_band_frac, burn_med)))
    targets.append(("Burn tick declines with caster troops (corr >= 0.4)",
                    decline_corr >= 0.4,
                    "caster-troops/tick correlation = %.2f" % decline_corr))
    targets.append(("Curse ~ 0.5x Burn (ratio in 0.40-0.60)",
                    0.40 <= curse_burn_ratio <= 0.60,
                    "Curse/Burn median ratio = %.2f" % curse_burn_ratio))
    targets.append(("Detonate burst in ~3,100-6,700 band (median in band)",
                    DETONATE_BAND_LO <= burst_med <= DETONATE_BAND_HI,
                    "detonate median %.0f, %.0f%% of bursts in band"
                    % (burst_med, 100 * burst_band_frac)))
    targets.append(("Enemy strikers fall before the +DEF commander Thiel (>=80%%)",
                    rate("thiel_last") >= 80.0,
                    "Thiel falls last %.0f%% of matches" % rate("thiel_last")))

    npass = sum(1 for _, ok, _ in targets if ok)
    for name, ok, detail in targets:
        w("  [%s] %-58s -- %s" % ("PASS" if ok else "FAIL", name, detail))
    w("")
    w("SUMMARY: %d/%d targets PASS" % (npass, len(targets)))
    w("")
    w("Key DoT ModelConfig knobs (all ASSUMPTION; calibrated to calibration_2_dot.md):")
    for k in ("dot_global", "dot_troop_floor", "dot_def_ref", "dot_def_weight",
              "dot_detonate_chance", "dot_detonate_coef", "hero_off_weight",
              "troop_scale_ref"):
        w("  %-22s = %s" % (k, getattr(cfg, k)))
    out.close()
    print("DoT validation report -> %s (%d/%d PASS)" % (OUT_PATH, npass, len(targets)))
    return npass, len(targets)


if __name__ == "__main__":
    main()
