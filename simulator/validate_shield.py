"""Capture-grounded SHIELD/SUSTAIN validator (replaces the imprecise Rosetta transcription).

Targets are derived from 20 real wire-captured battles (notes/sim/captures/anchors/, the
shielded-Thiel experiment): the user's current heroes SusaMaki/Niya/Mia (+0) vs Thiel/Nicole/
Dolly with ONLY Thiel adjusted into a sustain tank -- modular Skyland(1,19) + Self-Healing(1,27),
skill-stone Holy-Light-Chop(2,66), max DEF.  This exercises the engine's shield (DMG-Taken-Reduced
buff 8, DEF-scaled), heal (buff 107), DEF-buff, and the grind/kill-cascade -- the same mechanics the
old testcase tested, but on clean ground truth at dg=65 instead of a hand transcription.

Measured targets (n=20, all dg=65-confirmed):
  player win  13/20 = 65%   (loss 30%, draw 5%)
  rounds      mean 4.70, median 4
  Thiel (enemy cmd) survives to end: 7/20 = 35%
  enemy units dead 2.50/3, player units dead 0.80/3
  damage ratio player/enemy ~1.50
  per-hero dmg: SusaMaki 76123, Niya 52778, Mia 37812 | Thiel 51854, Nicole 25856, Dolly 33321

Run:  python -m simulator.validate_shield
"""
import io
import os
import random
import statistics

from simulator.engine import data as datamod
from simulator.engine.combat import Battle
from simulator.engine.model import BuildSpec, ModelConfig, build_team

OUT_PATH = os.path.join(os.path.dirname(__file__), "_validate_shield_out.txt")
ARCHER = 2
SUSAMAKI, NIYA, MIA, THIEL, NICOLE, DOLLY = 28, 117, 46, 99, 87, 108

# captured ground-truth targets (band = measured +/- tolerance)
TARGETS = {
    "win_rate": (0.55, 0.75),          # 65%
    "rounds_median": (4, 5),           # 4-5
    "thiel_survive": (0.25, 0.45),     # 35%
    "enemy_dead": (2.2, 2.8),          # 2.50
    "player_dead": (0.5, 1.1),         # 0.80
    "dmg_ratio": (1.30, 1.70),         # 1.50
}
PER_HERO = {SUSAMAKI: 76123, NIYA: 52778, MIA: 37812, THIEL: 51854, NICOLE: 25856, DOLLY: 33321}


def _loadout(g, hid, stone):
    h = g.hero(hid)
    mods = [(int(m["st"]), int(m["id"])) for m in h.get("modular_default", [])]
    return tuple(mods + [stone])


def _spec(hid, alloc, cmd, skills):
    return BuildSpec(hero_id=hid, soldier_type=ARCHER, is_commander=cmd,
                     skill_keys=tuple(skills), allocated_stat=alloc)


def build_player(g, cfg):
    return build_team(g, [
        _spec(SUSAMAKI, None, True, _loadout(g, SUSAMAKI, (2, 66))),
        _spec(NIYA, None, False, _loadout(g, NIYA, (2, 100))),
        _spec(MIA, None, False, _loadout(g, MIA, (2, 65))),
    ], side=0, cfg=cfg, fight_pos_base=1)


def build_enemy(g, cfg):
    # Thiel = sustain tank: main Binding Slash + modular Skyland(1,19)+Self-Healing(1,27)
    # + stone Holy-Light-Chop(2,66), max DEF.  Nicole/Dolly: default loadout, +0.
    return build_team(g, [
        _spec(THIEL, "def", True, [(1, 19), (1, 27), (2, 66)]),
        _spec(NICOLE, None, False, _loadout(g, NICOLE, (2, 100))),
        _spec(DOLLY, None, False, _loadout(g, DOLLY, (2, 65))),
    ], side=1, cfg=cfg, fight_pos_base=4)


def main(n=400):
    g = datamod.load(); cfg = ModelConfig()
    from collections import Counter, defaultdict
    res = Counter(); rounds = []; tsurv = 0; ed = []; pd_ = []
    pdmg = []; edmg = []; hd = defaultdict(list)
    for s in range(n):
        p = build_player(g, cfg); e = build_enemy(g, cfg)
        b = Battle(g, cfg, p, e, random.Random(s)); r = b.run()
        res["win" if r.winner == 0 else "loss" if r.winner == 1 else "draw"] += 1
        rounds.append(r.rounds_fought)
        th = [u for u in b.sides[1] if u.hero_id == THIEL][0]
        if th.alive:
            tsurv += 1
        ed.append(sum(1 for u in b.sides[1] if not u.alive))
        pd_.append(sum(1 for u in b.sides[0] if not u.alive))
        pdmg.append(r.total_player_damage); edmg.append(r.total_enemy_damage)
        for u in b.sides[0] + b.sides[1]:
            hd[u.hero_id].append(u.stat_kills)
    m = statistics.mean
    got = {
        "win_rate": res["win"] / n,
        "rounds_median": statistics.median(rounds),
        "thiel_survive": tsurv / n,
        "enemy_dead": m(ed),
        "player_dead": m(pd_),
        "dmg_ratio": m(pdmg) / m(edmg),
    }
    lines = []
    npass = 0
    for k, (lo, hi) in TARGETS.items():
        ok = lo <= got[k] <= hi
        npass += ok
        lines.append("  [%s] %-14s = %.2f  (target %.2f-%.2f)" % ("PASS" if ok else "FAIL", k, got[k], lo, hi))
    NAME = {28: "SusaMaki", 117: "Niya", 46: "Mia", 99: "Thiel", 87: "Nicole", 108: "Dolly"}
    lines.append("  per-hero damage (engine vs captured):")
    for hid, cap in PER_HERO.items():
        v = m(hd[hid]); r = v / cap
        lines.append("    %-9s %6.0f vs %6d  (%.2f)" % (NAME[hid], v, cap, r))
    report = "SHIELD/SUSTAIN validator (capture-grounded, n=%d)\n" % n + "\n".join(lines)
    report += "\nSUMMARY: %d/%d targets PASS" % (npass, len(TARGETS))
    with io.open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("validation report -> %s (%d/%d PASS)" % (OUT_PATH, npass, len(TARGETS)))


if __name__ == "__main__":
    main()
