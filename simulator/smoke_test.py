"""End-to-end smoke test: load real data, build two 3-hero teams, run battles.

Run from the repo root:  python -m simulator.smoke_test
Writes a UTF-8 report (CJK-safe) to simulator/_smoke_out.txt.
"""
import io
import os
import random

from simulator.engine import data as datamod
from simulator.engine import model as modelmod
from simulator.engine.combat import Battle
from simulator.engine.model import BuildSpec, ModelConfig, build_team

OUT = io.open(os.path.join(os.path.dirname(__file__), "_smoke_out.txt"), "w", encoding="utf-8")
def w(*a):
    OUT.write(" ".join(str(x) for x in a) + "\n")


def main():
    g = datamod.load()
    cfg = ModelConfig()
    w("=== data loaded ===")
    w("playable heroes:", len(g.heroes), "| skills:", len(g.skills), "| rounds:", g.round_count)

    # pick three real heroes by id (1 Crolos, 2 Saintess Shin, 3 ...)
    ids = sorted(g.heroes)[:3]
    w("player heroes:", [(i, g.hero(i)["name_en"], g.hero(i)["rst"]["soldier_type_en"]) for i in ids])

    # player team: each hero fields its RST soldier type; first is commander
    p_specs = []
    for k, hid in enumerate(ids):
        st = g.hero(hid)["rst"]["id"]
        p_specs.append(BuildSpec(hero_id=hid, soldier_type=st, is_commander=(k == 0)))

    # enemy team: next three heroes
    eids = sorted(g.heroes)[3:6]
    e_specs = []
    for k, hid in enumerate(eids):
        st = g.hero(hid)["rst"]["id"]
        e_specs.append(BuildSpec(hero_id=hid, soldier_type=st, is_commander=(k == 0)))
    w("enemy heroes:", [(i, g.hero(i)["name_en"]) for i in eids])

    # build units and dump their maxed profiles
    p_units = build_team(g, p_specs, side=0, cfg=cfg, fight_pos_base=1)
    e_units = build_team(g, e_specs, side=1, cfg=cfg, fight_pos_base=4)
    w("\n=== player maxed units ===")
    for u in p_units:
        w("  %-16s %-8s ATK %.0f DEF %.0f Ruin %.0f Spd %.0f | troops %d | soldier(hp %.0f atk %.0f def %.0f) | HP %.0f | skills %s"
          % (u.name, u.soldier_type_name, u.atk, u.deff, u.ruin, u.speed, u.troops_max,
             u.soldier.hp, u.soldier.atk, u.soldier.deff, u.hp_max,
             [s["name_en"] for s in u.skills]))

    # run one battle (seeded)
    w("\n=== single battle (seed 0) ===")
    res = Battle(g, cfg, build_team(g, p_specs, 0, cfg, 1), build_team(g, e_specs, 1, cfg, 4),
                 random.Random(0)).run()
    w("winner:", res.winner, "| rounds:", res.rounds_fought)
    w("player dmg/round:", [round(x) for x in res.player_damage_by_round])
    w("enemy  dmg/round:", [round(x) for x in res.enemy_damage_by_round])
    w("player windows:", {k: round(v) for k, v in res.window_damage("player").items()})
    w("player troops left: %.1f%%  enemy troops left: %.1f%%"
      % (res.player_troops_frac_remaining * 100, res.enemy_troops_frac_remaining * 100))

    # Monte-Carlo: 500 battles, win rate + mean window damage
    w("\n=== Monte-Carlo (500 battles) ===")
    n = 500
    wins = 0
    windows = {"early": 0.0, "mid": 0.0, "late": 0.0, "all": 0.0}
    for seed in range(n):
        r = Battle(g, cfg, build_team(g, p_specs, 0, cfg, 1), build_team(g, e_specs, 1, cfg, 4),
                   random.Random(seed)).run()
        if r.winner == 0:
            wins += 1
        for k, v in r.window_damage("player").items():
            windows[k] += v
    w("player win rate: %.1f%%" % (100.0 * wins / n))
    w("mean player window damage:", {k: round(v / n) for k, v in windows.items()})
    w("\nOK")
    OUT.close()


if __name__ == "__main__":
    main()
