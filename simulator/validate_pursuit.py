"""Measurement harness for Matchup-3 ("Pursuit & Throughput") vs the in-game log.

NOT a pass/fail calibration of reverted mechanics -- a SCOREBOARD for the recalibration:
it builds Matchup-3's exact formations (calibration_3_pursuit.md) and reports the metrics the
in-game log pins, so competing calibrations can be compared:
  * player win-rate (in-game 100% over 10 runs) and single-battle (no-rematch) rate
  * median first-bout rounds (in-game 4) and enemy-commander-Thiel-wiped rate
  * Niya Assault (real-channel) hit band ~350-850 declining with caster troops
  * pursuit throughput (Niya hits/round) and per-hero damage shape (Niya/SusaMaki top; +ATK>+DEF/DES)

Run from repo root:  python -m simulator.validate_pursuit
"""
import io
import os
import random
import statistics

from simulator.engine import data as datamod
from simulator.engine.combat import Battle
from simulator.engine.model import BuildSpec, ModelConfig, build_team

OUT_PATH = os.path.join(os.path.dirname(__file__), "_validate_pursuit_out.txt")

SUSAMAKI, NIYA, MIA = 28, 117, 46            # player pursuit/combo trio (all +229 ATK)
THIEL, NICOLE, DOLLY = 99, 87, 108           # enemy: Thiel +DEF (cmd) / Nicole +ATK 4* / Dolly +DES
ARCHER = 2
HOLY_LIGHT_CHOP = (2, 66); RIFT = (2, 100); PURGATORY_TRIAL = (2, 65)  # distinct stones per team

ASSAULT_BAND_LO, ASSAULT_BAND_HI = 350.0, 850.0   # Niya Real DMG Base 32.29 -> log 468..757


def _loadout(g, hero_id, stone):
    h = g.hero(hero_id)
    mods = [(int(m["st"]), int(m["id"])) for m in h.get("modular_default", [])]
    return tuple(mods + [stone])


def _spec(g, hid, alloc, cmd, stone):
    return BuildSpec(hero_id=hid, soldier_type=ARCHER, is_commander=cmd,
                     skill_keys=_loadout(g, hid, stone), allocated_stat=alloc)


def build_player(g, cfg):
    return build_team(g, [
        _spec(g, SUSAMAKI, "atk", True, HOLY_LIGHT_CHOP),
        _spec(g, NIYA, "atk", False, RIFT),
        _spec(g, MIA, "atk", False, PURGATORY_TRIAL),
    ], side=0, cfg=cfg, fight_pos_base=1)


def build_enemy(g, cfg):
    return build_team(g, [
        _spec(g, THIEL, "def", True, HOLY_LIGHT_CHOP),
        _spec(g, NICOLE, "atk", False, RIFT),
        _spec(g, DOLLY, "ruin", False, PURGATORY_TRIAL),
    ], side=1, cfg=cfg, fight_pos_base=4)


def run_match(g, cfg, seed, hit_probe=None):
    p = build_player(g, cfg); e = build_enemy(g, cfg)
    b = Battle(g, cfg, p, e, random.Random(seed))
    if hit_probe is not None:
        _o = b._deal
        def spy(a, d, coef, ch, ri, is_skill, real_base=0.0, _o=_o):
            ap = _o(a, d, coef, ch, ri, is_skill, real_base=real_base)
            hit_probe.append((a.name, ch, ri, round(ap)))
            return ap
        b._deal = spy
    snaps = []; bouts = 0
    while bouts < cfg.max_bouts:
        bouts += 1
        if bouts > 1:
            b._reset_for_rematch()
            if not (b._alive(0) and b._alive(1)):
                break
        rf, decided, d0, d1 = b._run_bout()
        pc, ec = b._commander(0), b._commander(1)
        res = ("Victory" if (ec and not ec.alive and (not pc or pc.alive))
               else "Defeat" if (pc and not pc.alive) else "Decided" if decided else "Stalemate")
        snaps.append({"bout": bouts, "rounds": rf, "result": res,
                      "thiel_dead": not b.sides[1][0].alive,
                      "perhero": {u.name: round(u.stat_kills) for s in (0, 1) for u in b.sides[s]}})
        if decided:
            break
        b.stalemates += 1
    return b, snaps


def main():
    g = datamod.load(); cfg = ModelConfig()
    out = io.open(OUT_PATH, "w", encoding="utf-8")
    w = lambda *a: out.write(" ".join(str(x) for x in a) + "\n")
    n = 400
    pw = sbw = thiel = 0; first_rounds = []; perhero_tot = {}
    for seed in range(n):
        _, snaps = run_match(g, cfg, seed)
        fin = snaps[-1]; first_rounds.append(snaps[0]["rounds"])
        if fin["result"] == "Victory":
            pw += 1
            if len(snaps) == 1:
                sbw += 1
        if fin["thiel_dead"]:
            thiel += 1
        for k, v in fin["perhero"].items():
            perhero_tot[k] = perhero_tot.get(k, 0) + v
    # hit samples
    assault = []; assault_series = []; vol_niya = []
    for seed in range(60):
        hits = []; run_match(g, cfg, seed, hit_probe=hits); per = {}
        for (nm, ch, ri, ap) in hits:
            if nm == "Niya" and ch in ("real", "assault"):
                assault.append(ap); assault_series.append((ri, ap))
            if nm == "Niya":
                per[ri] = per.get(ri, 0) + 1
        vol_niya += list(per.values())
    a_med = statistics.median(assault) if assault else 0
    a_band = (sum(1 for x in assault if ASSAULT_BAND_LO <= x <= ASSAULT_BAND_HI) / len(assault)) if assault else 0
    corr = 0.0
    if len(assault_series) > 5:
        try:
            corr = statistics.correlation([r for r, _ in assault_series], [v for _, v in assault_series])
        except Exception:
            corr = 0.0
    vN = statistics.median(vol_niya) if vol_niya else 0
    rmed = statistics.median(first_rounds) if first_rounds else 0
    rate = lambda x: 100.0 * x / n
    w("=== Matchup-3 'Pursuit & Throughput' scoreboard (in-game: 100%% win, ~4 rounds) ===")
    w("player win=%.1f%%  single-battle(no-rematch)=%.1f%%  Thiel wiped=%.1f%%  median rounds=%.1f"
      % (rate(pw), rate(sbw), rate(thiel), rmed))
    w("Niya Assault: median=%.0f  in[%d,%d]=%.0f%%  round-corr=%.2f (neg=declines)  | Niya hits/round med=%.1f"
      % (a_med, ASSAULT_BAND_LO, ASSAULT_BAND_HI, 100 * a_band, corr, vN))
    w("per-hero kills/match: " + ", ".join("%s=%d" % (k, v // n) for k, v in
        sorted(perhero_tot.items(), key=lambda x: -x[1])))
    w("(in-game per-hero kills: Niya 65355 / SusaMaki 60241 / Mia 35349 / Dolly 40032 / Thiel 30845 / Nicole 59382)")
    # scoreboard verdicts (informational; pursuit goal = win>=90 & Thiel wiped>=90)
    targets = [
        ("Player win >=90%%", rate(pw) >= 90.0, "%.1f%%" % rate(pw)),
        ("Single-battle win >=85%%", rate(sbw) >= 85.0, "%.1f%%" % rate(sbw)),
        ("Enemy commander Thiel wiped >=90%%", rate(thiel) >= 90.0, "%.1f%%" % rate(thiel)),
        ("Median first-bout rounds <=6 (log 4)", rmed <= 6.0, "%.1f" % rmed),
        ("Niya Assault band >=60%%", a_band >= 0.60, "%.0f%%" % (100 * a_band)),
        ("Assault declines (corr<=-0.2)", corr <= -0.2, "%.2f" % corr),
        ("Niya throughput >=4 hits/round", vN >= 4.0, "%.1f" % vN),
    ]
    npass = sum(1 for _, ok, _ in targets if ok)
    w("")
    for name, ok, det in targets:
        w("  [%s] %-40s -- %s" % ("PASS" if ok else "FAIL", name, det))
    w("SUMMARY: %d/%d  (pursuit goal: player win + Thiel wiped both >=90%%)" % (npass, len(targets)))
    out.close()
    print("Pursuit scoreboard -> %s (%d/%d; player win %.1f%%)" % (OUT_PATH, npass, len(targets), rate(pw)))
    return npass, len(targets)


if __name__ == "__main__":
    main()
