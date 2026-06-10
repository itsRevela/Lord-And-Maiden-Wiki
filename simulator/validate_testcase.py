"""Validate the reworked combat engine against the Rosetta-Stone test case.

Builds the EXACT two test-case formations (from data/sim/testcase_entities.json +
calibration.json), runs the MATCH (a sequence of 8-round bouts), and compares the
outcome to the logged ground truth:

  * Battle 1 = Stalemate, Battle 2 = Victory (survivors carry over).
  * Enemy Rhea survives B1 under Star Shield, then falls in B2.
  * Aguria falls mid-B1.
  * Left team ends B1 ~80-85% Health; right ~30%.
  * Patra is the top damage dealer by far.

Combat is server-authoritative (the exact damage equation is not in the client),
so magnitudes are model-relative; where the model cannot reproduce a behaviour the
report says so.  Prints a PASS/FAIL-per-target report to a UTF-8 file (CJK-safe);
NEVER prints CJK to the console.

Run from the repo root:  python -m simulator.validate_testcase
"""
import io
import os
import random

from simulator.engine import data as datamod
from simulator.engine.combat import Battle
from simulator.engine.model import BuildSpec, ModelConfig, build_team

OUT_PATH = os.path.join(os.path.dirname(__file__), "_validate_out.txt")

# hero ids per the prompt / testcase_entities.json
PATRA, RHEA, AGURIA_SP, SATORU, SLIDER_SP = 60, 40, 98, 97, 66

# allocated stats (log "+229 X")
ALLOC = {"atk": "atk", "def": "def", "ruin": "ruin", "speed": "speed"}


def _spec(hero_id, troop, alloc, commander, skill_keys):
    return BuildSpec(hero_id=hero_id, soldier_type=troop, is_commander=commander,
                     skill_keys=tuple(skill_keys), allocated_stat=alloc)


def build_player(g, cfg):
    """Player [A]: Patra (cmd, ATK, Archer) / Rhea (DEF, Infantry) / Slider.Sp (DES, Siege/Chariot)."""
    specs = [
        # Patra: main Ghost Bone(2,81); modular Bone Blade(2,144) + Tactical Burst(3,26);
        # skill-stone Magic Spear(2,125) -- add as a third modular so it can fire.
        _spec(PATRA, 2, "atk", True, [(2, 144), (3, 26), (2, 125)]),
        # Rhea (A): main Star Shield(1,26); modular Sky Tear Arrow(1,76) + Unbounded(1,49);
        # skill-stone Reactive Block(3,16).
        _spec(RHEA, 1, "def", False, [(1, 76), (1, 49), (3, 16)]),
        # Slider.Sp: main Dark Arrive(1,42); modular Noise(1,32) + Piety/Devout(1,56);
        # skill-stone Field Therapy(1,46).
        _spec(SLIDER_SP, 4, "ruin", False, [(1, 32), (1, 56), (1, 46)]),
    ]
    return build_team(g, specs, side=0, cfg=cfg, fight_pos_base=1)


def build_enemy(g, cfg):
    """Enemy [E]: Rhea (cmd, DEF, Cavalry) / Aguria.Sp (ATK, Archer) / Satoru (ATK SPD, Cavalry)."""
    specs = [
        # Enemy Rhea: main Star Shield(1,26); modular Knight Creed(2,110) + Field Therapy(1,46);
        # skill-stone Elf Deer(1,58).
        _spec(RHEA, 3, "def", True, [(2, 110), (1, 46), (1, 58)]),
        # Aguria.Sp: main Swift Thrust(2,111); modular Evil Fruit(2,101) + Tactical Burst(3,26);
        # skill-stone Sacred Feather(3,28).
        _spec(AGURIA_SP, 2, "atk", False, [(2, 101), (3, 26), (3, 28)]),
        # Satoru: main Gray World(1,52); modular Piety/Devout(1,56) + Cocoon Silence(2,99);
        # skill-stone Green Tea(2,59).
        _spec(SATORU, 3, "speed", False, [(1, 56), (2, 99), (2, 59)]),
    ]
    return build_team(g, specs, side=1, cfg=cfg, fight_pos_base=4)


def run_match(g, cfg, seed):
    """Run a single match (player vs enemy) and capture per-bout snapshots."""
    p = build_player(g, cfg)
    e = build_enemy(g, cfg)
    b = Battle(g, cfg, p, e, random.Random(seed))
    # we want per-bout (battle 1 / battle 2) details, so run bouts manually.
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
    return b, snaps


def _snapshot(b, bout, rounds, decided, d0, d1):
    def units(side):
        return {u.name: {"health": round(u.health), "max": round(u.cur_max),
                          "alive": u.alive, "kills": round(u.stat_kills),
                          "heal": round(u.stat_heal),
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
    left_health = sum(u.health for u in b.sides[0])
    right_health = sum(u.health for u in b.sides[1])
    left_max = sum(u.troops_max for u in b.sides[0])
    right_max = sum(u.troops_max for u in b.sides[1])
    return {
        "bout": bout, "rounds": rounds, "result": result,
        "left_health": round(left_health), "left_max": left_max,
        "right_health": round(right_health), "right_max": right_max,
        "left_frac": left_health / left_max if left_max else 0,
        "right_frac": right_health / right_max if right_max else 0,
        "dmg_player": round(sum(d0)), "dmg_enemy": round(sum(d1)),
        "A": units(0), "E": units(1),
    }


def aggregate(g, cfg, n=200):
    """Run n seeded matches; aggregate the qualitative targets."""
    stats = {
        "b1_stalemate": 0, "b2_victory": 0, "match_victory": 0,
        "rhea_e_survives_b1": 0, "rhea_e_falls_b2": 0, "aguria_falls_b1": 0,
        "patra_top_dealer_b1": 0, "n": 0, "matches_with_2bouts": 0,
        "left_frac_b1_sum": 0.0, "right_frac_b1_sum": 0.0,
        # of matches that stalemated B1, how many the player then WINS (the rematch):
        "b1_stale_then_win": 0, "b1_stale_count": 0,
        "win_at_bout2": 0,
    }
    example = None
    for seed in range(n):
        b, snaps = run_match(g, cfg, seed)
        stats["n"] += 1
        if example is None:
            example = snaps
        if len(snaps) >= 2:
            stats["matches_with_2bouts"] += 1
        b1 = snaps[0]
        # battle 1 stalemate?
        b1_stale = b1["result"] == "Stalemate"
        if b1_stale:
            stats["b1_stalemate"] += 1
            stats["b1_stale_count"] += 1
        stats["left_frac_b1_sum"] += b1["left_frac"]
        stats["right_frac_b1_sum"] += b1["right_frac"]
        # enemy Rhea survives B1
        if b1["E"]["Rhea"]["alive"]:
            stats["rhea_e_survives_b1"] += 1
        # Aguria falls in B1
        if not b1["E"]["Aguria·Sp"]["alive"]:
            stats["aguria_falls_b1"] += 1
        # Patra top dealer in B1 (kills)
        a_kills = {nm: b1["A"][nm]["kills"] for nm in b1["A"]}
        if a_kills and max(a_kills, key=a_kills.get) == "Patra" \
                and b1["A"]["Patra"]["kills"] >= 1.5 * max(
                    (v for nm, v in a_kills.items() if nm != "Patra"), default=0):
            stats["patra_top_dealer_b1"] += 1
        # battle 2 victory / match victory
        final = snaps[-1]
        if final["result"] == "Victory":
            stats["match_victory"] += 1
            if len(snaps) >= 2 and snaps[1]["result"] == "Victory":
                stats["b2_victory"] += 1
                stats["win_at_bout2"] += 1
            if b1_stale:
                stats["b1_stale_then_win"] += 1
            # enemy Rhea fallen at the end
            if not final["E"]["Rhea"]["alive"]:
                stats["rhea_e_falls_b2"] += 1
    return stats, example


def main():
    g = datamod.load()
    cfg = ModelConfig()
    out = io.open(OUT_PATH, "w", encoding="utf-8")

    def w(*a):
        out.write(" ".join(str(x) for x in a) + "\n")

    w("=== Rosetta-Stone test-case validation ===")
    w("Combat is server-authoritative; magnitudes are model-relative (ModelConfig knobs).")
    w("")

    # one detailed example match (seed 0)
    b, snaps = run_match(g, cfg, 0)
    w("--- example match (seed 0): %d bout(s) (showing first 3) ---" % len(snaps))
    for sn in snaps[:3]:
        w("Bout %d (Battle %d): %s in %d rounds | left %d/%d (%.0f%%)  right %d/%d (%.0f%%)"
          % (sn["bout"], sn["bout"], sn["result"], sn["rounds"],
             sn["left_health"], sn["left_max"], 100 * sn["left_frac"],
             sn["right_health"], sn["right_max"], 100 * sn["right_frac"]))
        for side, label in ((0, "A"), (1, "E")):
            for nm, st in sn[side and "E" or "A"].items():
                w("    [%s] %-12s health %6d/%-6d alive=%s kills %7d heal %5d skillDmg %7d normalDmg %6d"
                  % (label, nm, st["health"], st["max"], st["alive"],
                     st["kills"], st["heal"], st["skill_dmg"], st["normal_dmg"]))
    w("")

    # aggregate over many seeds
    n = 200
    st, _ = aggregate(g, cfg, n=n)
    w("--- aggregate over %d seeded matches ---" % n)

    def rate(k):
        return 100.0 * st[k] / st["n"] if st["n"] else 0.0

    left_frac = st["left_frac_b1_sum"] / st["n"]
    right_frac = st["right_frac_b1_sum"] / st["n"]

    # of matches that reached a B1 stalemate, the player wins the rematch this often:
    rematch_win = (100.0 * st["b1_stale_then_win"] / st["b1_stale_count"]
                   if st["b1_stale_count"] else 0.0)
    bout2_win = rate("win_at_bout2")

    targets = []
    targets.append(("Battle 1 = Stalemate", rate("b1_stalemate") >= 60.0,
                    "%.0f%% of matches B1 stalemate" % rate("b1_stalemate")))
    targets.append(("Battle 2+ = Victory (rematch after B1 stalemate)", rematch_win >= 60.0,
                    "%.0f%% of B1-stalemate matches end in Victory (%.0f%% exactly at bout 2)"
                    % (rematch_win, bout2_win)))
    targets.append(("Match ends in player Victory", rate("match_victory") >= 60.0,
                    "%.0f%% match victory" % rate("match_victory")))
    targets.append(("Enemy Rhea survives Battle 1 (Star Shield)", rate("rhea_e_survives_b1") >= 60.0,
                    "%.0f%% Rhea(E) alive end of B1" % rate("rhea_e_survives_b1")))
    targets.append(("Enemy Rhea falls by end of match (B2)", rate("rhea_e_falls_b2") >= 50.0,
                    "%.0f%% Rhea(E) dead at match end" % rate("rhea_e_falls_b2")))
    targets.append(("Aguria falls mid-Battle 1", rate("aguria_falls_b1") >= 50.0,
                    "%.0f%% Aguria dead end of B1" % rate("aguria_falls_b1")))
    targets.append(("Left team ends B1 ~80-85%% Health", 0.62 <= left_frac <= 0.95,
                    "left B1 end = %.0f%% (target ~84%%)" % (100 * left_frac)))
    targets.append(("Right team ends B1 ~30%% Health", 0.15 <= right_frac <= 0.50,
                    "right B1 end = %.0f%% (target ~32%%)" % (100 * right_frac)))
    targets.append(("Patra is top damage dealer by far (B1)", rate("patra_top_dealer_b1") >= 70.0,
                    "%.0f%% Patra top dealer" % rate("patra_top_dealer_b1")))

    npass = sum(1 for _, ok, _ in targets if ok)
    for name, ok, detail in targets:
        w("  [%s] %-45s -- %s" % ("PASS" if ok else "FAIL", name, detail))
    w("")
    w("SUMMARY: %d/%d targets PASS" % (npass, len(targets)))
    w("")
    w("Key ModelConfig knobs:")
    for k in ("advance_soldiers_bonus", "damage_global", "hero_off_weight",
              "troop_scale_ref", "def_ref", "real_dmg_scale", "heal_scale",
              "direct_severe_frac", "slight_worsen_frac", "normal_attack_coef",
              "allocated_stat_points", "counter_coef", "reactive_block_reduction"):
        w("  %-24s = %s" % (k, getattr(cfg, k)))
    out.close()
    print("validation report -> %s (%d/%d PASS)" % (OUT_PATH, npass, len(targets)))
    return npass, len(targets)


if __name__ == "__main__":
    main()
