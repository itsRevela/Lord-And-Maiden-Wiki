"""Data layer for the Lord & Maiden battle simulator.

Loads the machine-readable catalogue under ``data/sim/*.json`` (produced by the
Phase-1 decode) and exposes typed lookups for the engine. Pure I/O + indexing;
no game logic lives here.

Combat reality: the game's damage equation is server-authoritative and absent from
the client (see ``data/sim/combat_rules.json`` -> ``modeling_assumptions_server_side``).
Everything here is an *input* or a *stated rule*, never the hidden formula.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

# data/sim lives two levels up from this file: simulator/engine/ -> repo root
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SIM_DIR = os.path.join(_REPO_ROOT, "data", "sim")


def _load(name: str):
    path = os.path.join(SIM_DIR, name + ".json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class GameData:
    """In-memory index over the seven sim data files."""

    def __init__(self) -> None:
        self.heroes_raw = _load("heroes")
        self.skills_raw = _load("skills")
        self.gear = _load("gear")
        self.troops_meta = _load("troops_meta")
        self.status = _load("status_effects")
        self.rules = _load("combat_rules")

        # --- heroes: only the playable roster the user can pick from ---
        self.heroes = {
            int(h["id"]): h
            for h in self.heroes_raw["heroes"]
            if h.get("playable")
        }

        # --- skills indexed by (skill_type, skill_id) ---
        self.skills = {(int(s["st"]), int(s["id"])): s for s in self.skills_raw}

        # --- status effects by int id ---
        self.buffs = {int(k): v for k, v in self.status.items()}

        # --- troops: T6 (max-tier) stats by soldier type id 1..4 ---
        self.troops = {int(k): v for k, v in self.troops_meta["troops"].items()}

        # --- restraint triangle + modifier (stated rule) ---
        r = self.rules["restraint"]
        self.restraint_triangle = r["triangle"]          # {"Infantry":"Archer",...}
        self.restraint_modifier = float(r["restrained_side_modifier"])  # 0.75
        self.soldier_type_name = {int(k): v for k, v in r["soldier_type_enum"].items()}
        self.soldier_name_to_id = {v: k for k, v in self.soldier_type_name.items()}

        self.round_count = int(self.rules["round_count"])

    # ---- lookups -------------------------------------------------------
    def hero(self, hid: int) -> dict:
        return self.heroes[int(hid)]

    def skill(self, st: int, sid: int):
        return self.skills.get((int(st), int(sid)))

    def skill_by_key(self, key: dict):
        """key = a hero's {'st':, 'id':} skill ref."""
        return self.skill(key["st"], key["id"])

    def buff(self, bid: int):
        return self.buffs.get(int(bid))

    def troop(self, soldier_type_id: int) -> dict:
        return self.troops[int(soldier_type_id)]

    def troop_max_stats(self, soldier_type_id: int) -> dict:
        return self.troops[int(soldier_type_id)]["max_tier_stats"]

    # ---- team-composition bonuses -------------------------------------
    def soldier_combo(self, soldier_type_id: int, matching_count: int):
        """Return the active soldier-combination effects given how many of the
        3 heroes field this soldier type (0/1 -> none, 2 -> basic, 3 -> advanced)."""
        by = self.troops_meta["soldier_combinations"]["by_soldier_type"]
        row = by.get(str(soldier_type_id))
        if not row:
            return None
        if matching_count >= 3:
            return row.get("advanced")
        if matching_count == 2:
            return row.get("basic")
        return None

    def race_combo(self, race_id: int, matching_count: int):
        by = self.troops_meta["race_combinations"]["by_race"]
        row = by.get(str(race_id))
        if not row:
            return None
        if matching_count >= 3:
            return row.get("advanced")
        if matching_count == 2:
            return row.get("basic")
        return None

    @property
    def affection_max_all_attr(self) -> int:
        return int(self.troops_meta["affection"]["max_bonus"])  # +30

    def commander_talent_flat_soldiers(self) -> int:
        """Type-1 (Commander) talent maxed = flat Soldiers Quantity bonus."""
        t = self.troops_meta["talents"]["by_type"].get("1")
        if not t:
            return 0
        return int(t.get("maxed_cumulative", {}).get("flat", 0))

    def soldier_talent_percent(self, soldier_type_id: int):
        """Types 2-5 maxed = a percent bonus to one stat of that soldier type.
        Returns (attr_en, percent) or None. Talent namespace is internal:
        53=Infantry HP, 19=Archer ATK, 25=Cavalry DEF, 52=Chariot DES."""
        # talent type 2->Infantry,3->Archer,4->Cavalry,5->Chariot (by convention);
        # resolve by matching the talent whose effect targets this soldier type.
        mapping = {1: "2", 2: "3", 3: "4", 4: "5"}  # soldier_type_id -> talent_type
        tt = mapping.get(int(soldier_type_id))
        if not tt:
            return None
        t = self.troops_meta["talents"]["by_type"].get(tt)
        if not t:
            return None
        mc = t.get("maxed_cumulative", {})
        pct = mc.get("percent")
        if pct is None:
            return None
        return (t.get("effect_namespace_attr_en", ""), float(pct))


@lru_cache(maxsize=1)
def load() -> GameData:
    """Cached singleton accessor."""
    return GameData()


if __name__ == "__main__":
    g = load()
    out = []
    out.append("playable heroes: %d" % len(g.heroes))
    out.append("skills: %d" % len(g.skills))
    out.append("status effects: %d" % len(g.buffs))
    out.append("troop types: %s" % sorted(g.troops))
    out.append("round count: %d" % g.round_count)
    out.append("restraint modifier: %.2f" % g.restraint_modifier)
    out.append("affection max all-attr: +%d" % g.affection_max_all_attr)
    out.append("commander talent flat soldiers: +%d" % g.commander_talent_flat_soldiers())
    # write to UTF-8 to dodge cp1252 console
    with open(os.path.join(os.path.dirname(__file__), "_data_check.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("data.py self-check written to _data_check.txt")
