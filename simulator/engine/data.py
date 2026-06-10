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

        # --- gear indices (equipment is hero-generic; relic is hero-specific;
        #     rune & skill-awaken are skill-specific) ---
        self._index_gear()

    # ---- gear ----------------------------------------------------------
    def _index_gear(self):
        # relic by OWNER hero id (a hero can only equip its own relic)
        self.relic_by_hero = {}
        for rel in self.gear.get("hero_relics", []):
            hid = rel.get("hero_id")
            if hid not in (None, ""):
                self.relic_by_hero[int(hid)] = rel
        # rune by the skill it boosts; skill-awaken by skill
        self.rune_by_skill = {}
        for rune in self.gear.get("runes", []):
            bs = rune.get("boosted_skill") or {}
            try:
                key = (int(bs["skill_type_id"]), int(bs["skill_id"]))
            except (KeyError, TypeError, ValueError):
                continue
            # keep the highest-trigger rune for a given skill
            prev = self.rune_by_skill.get(key)
            if not prev or float(rune.get("trigger_chance_max_pct") or 0) > float(prev.get("trigger_chance_max_pct") or 0):
                self.rune_by_skill[key] = rune
        self.awake_by_skill = {}
        for aw in self.gear.get("skill_awake", []):
            try:
                key = (int(aw["skill_type_id"]), int(aw["skill_id"]))
            except (KeyError, TypeError, ValueError):
                continue
            self.awake_by_skill[key] = aw
        self._compute_gear_bonus()

    def _slot_items(self):
        """Yield (slot_id, items[]) for the gear slots + accessory slots. Both
        sections may be a list of {slot_id,items} or a dict keyed by slot id."""
        for section in ("equipment", "accessories"):
            sec = self.gear.get(section, [])
            rows = sec.values() if isinstance(sec, dict) else sec
            for row in rows:
                if isinstance(row, dict):
                    yield int(row.get("slot_id", 0)), row.get("items", [])

    # attr_en -> our internal stat keys
    _SOLDIER_ATTR = {"Soldier HP": "HP", "Soldier ATK": "ATK", "Soldier DEF": "DEF",
                     "Soldier DES": "DES", "Soldier March Spd": "MarchSpd"}
    _HERO_ATTR = {"Hero ATK": "atk", "Hero DEF": "def", "Hero DES": "ruin",
                  "Hero ATK Spd": "speed"}

    def _accumulate(self, effects, acc):
        for e in effects or []:
            attr = e.get("attr") or e.get("attr_en") or ""
            kind = e.get("kind") or ""
            try:
                val = float(e.get("value"))
            except (TypeError, ValueError):
                continue
            if attr in self._SOLDIER_ATTR:
                k = self._SOLDIER_ATTR[attr]
                if kind == "percent":
                    acc["soldier_pct"][k] = acc["soldier_pct"].get(k, 0.0) + val
                else:
                    acc["soldier_flat"][k] = acc["soldier_flat"].get(k, 0.0) + val
            elif attr in self._HERO_ATTR:
                acc["hero_flat"][self._HERO_ATTR[attr]] = acc["hero_flat"].get(self._HERO_ATTR[attr], 0.0) + val
            elif attr == "Hero Soldiers Quantity" or attr == "Soldiers Quantity":
                acc["troops"] += val
            elif "Tactical Skill Activation" in attr:
                acc["trigger_tactical"] += val / 100.0 if kind == "percent" else val
            elif "Pursuit Skill Activation" in attr:
                acc["trigger_pursuit"] += val / 100.0 if kind == "percent" else val

    def _compute_gear_bonus(self):
        """Hero-generic 'maxed equipment' = best item per slot (by power) + any set
        bonus that triggers among the chosen pieces. Same for every hero."""
        acc = {"soldier_pct": {}, "soldier_flat": {}, "hero_flat": {},
               "troops": 0.0, "trigger_tactical": 0.0, "trigger_pursuit": 0.0}
        chosen_sets = {}
        for slot_id, items in self._slot_items():
            if not items:
                continue
            best = max(items, key=lambda it: float(it.get("power") or 0))
            self._accumulate(best.get("effects"), acc)
            sid = best.get("set_id")
            if sid not in (None, "", "0"):
                chosen_sets[sid] = chosen_sets.get(sid, 0) + 1
        # set bonuses (3pc / 6pc) for any set with enough chosen pieces
        for sb in self.gear.get("set_bonuses", []):
            sid = str(sb.get("set_id"))
            n = chosen_sets.get(sid, 0)
            if n >= 3:
                self._accumulate(sb.get("three_piece"), acc)
            if n >= 6:
                self._accumulate(sb.get("six_piece"), acc)
        self.gear_bonus = acc

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

    def relic_bonus_for_hero(self, hero_id: int):
        """A hero equips ONLY its own relic (e.g. Patra -> 'Patra Relic'). Returns the
        bonus it grants to the skill it enhances, routed by effect kind:
        {'key':(st,id), 'kind':'trigger'|'coef'|'attr', 'value':float, 'stat':?} or None.
        Most relics give 'Skill Trigger Probability'; some give a coefficient/attribute."""
        rel = self.relic_by_hero.get(int(hero_id))
        if not rel:
            return None
        es = rel.get("enhanced_skill") or {}
        try:
            key = (int(es["skill_type_id"]), int(es["skill_id"]))
        except (KeyError, TypeError, ValueError):
            return None
        val = 0.0
        for tok in rel.get("effect_tokens_max") or []:
            try:
                val = float(tok.get("value"))
            except (TypeError, ValueError):
                pass
        txt = (rel.get("max_bonus") or "").lower()
        if "trigger probability" in txt:
            return {"key": key, "kind": "trigger", "value": val}
        if "coefficient" in txt:
            return {"key": key, "kind": "coef", "value": val}
        stat = None
        for kw, s in (("atk spd", "speed"), ("atk", "atk"), ("def", "def"),
                      ("des", "ruin"), ("ruin", "ruin"), ("spd", "speed"), ("speed", "speed")):
            if kw in txt:
                stat = s
                break
        if "all attribute" in txt:
            stat = "all"
        if stat:
            return {"key": key, "kind": "attr", "value": val, "stat": stat}
        return None

    def rune_trigger_for_skill(self, key):
        """Best rune for an equipped skill -> +trigger_prob (max-level chance), or None."""
        rune = self.rune_by_skill.get(tuple(key))
        if not rune:
            return None
        try:
            return float(rune.get("trigger_chance_max_pct") or 0) / 100.0
        except (TypeError, ValueError):
            return None

    def awaken_bonus_for_skill(self, key):
        """Maxed skill-awaken bonus for an equipped skill. Returns
        {'kind':'coef'|'attr', 'value':float, 'stat':<for attr>} or None."""
        aw = self.awake_by_skill.get(tuple(key))
        if not aw:
            return None
        try:
            val = float(aw.get("max_buff_value"))
        except (TypeError, ValueError):
            return None
        bonus_txt = (aw.get("max_bonus") or "").lower()
        if "coefficient" in bonus_txt:
            return {"kind": "coef", "value": val}
        # attribute increase -> figure out which hero stat
        stat = None
        for kw, s in (("atk", "atk"), ("def", "def"), ("des", "ruin"),
                      ("ruin", "ruin"), ("spd", "speed"), ("speed", "speed")):
            if kw in bonus_txt:
                stat = s
                break
        if "all attribute" in bonus_txt:
            stat = "all"
        return {"kind": "attr", "value": val, "stat": stat}

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
