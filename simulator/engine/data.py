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

    # attr_en -> our internal stat keys.  Includes the soldier-type-specific gear keys
    # (spec C: latent today since best-by-power picks generic 'Soldier ATK' names, but a
    # free correctness improvement aligning with model._SOLDIER_ATTR_KEY).
    _SOLDIER_ATTR = {"Soldier HP": "HP", "Soldier ATK": "ATK", "Soldier DEF": "DEF",
                     "Soldier DES": "DES", "Soldier March Spd": "MarchSpd",
                     "Infantry HP": "HP", "Infantry ATK": "ATK", "Infantry DEF": "DEF",
                     "Infantry DES": "DES", "Archer HP": "HP", "Archer ATK": "ATK",
                     "Archer DEF": "DEF", "Archer DES": "DES", "Cavalry HP": "HP",
                     "Cavalry ATK": "ATK", "Cavalry DEF": "DEF", "Cavalry DES": "DES",
                     "Chariot HP": "HP", "Chariot ATK": "ATK", "Chariot DEF": "DEF",
                     "Chariot DES": "DES"}
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
            # PVE/PVP DMG Dealt/Taken from equipment + magic messenger.  Spec C: split
            # PVE vs PVP at decode and apply only the PVE sum in these PvE battles (the
            # logs are PvE practice fights); 'PVP'-tagged percents do not apply.  An
            # untagged 'DMG Dealt/Taken' is treated as PVE (context-neutral).
            elif "DMG Dealt" in attr:
                if "PVP" in attr.upper():
                    pass
                else:
                    acc["dmg_dealt"] += val / 100.0 if kind == "percent" else val
            elif "DMG Taken" in attr:
                if "PVP" in attr.upper():
                    pass
                else:
                    acc["dmg_taken"] += val / 100.0 if kind == "percent" else val

    def _compute_gear_bonus(self):
        """Hero-generic 'maxed equipment' = best item per slot (by power) + any set
        bonus that triggers among the chosen pieces. Same for every hero."""
        acc = {"soldier_pct": {}, "soldier_flat": {}, "hero_flat": {},
               "troops": 0.0, "trigger_tactical": 0.0, "trigger_pursuit": 0.0,
               "dmg_dealt": 0.0, "dmg_taken": 0.0}
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

    # ---- per-build SELECTABLE gear components (phase-2 gear system) ----
    @staticmethod
    def _empty_gear_acc():
        return {"soldier_pct": {}, "soldier_flat": {}, "hero_flat": {},
                "troops": 0.0, "trigger_tactical": 0.0, "trigger_pursuit": 0.0,
                "dmg_dealt": 0.0, "dmg_taken": 0.0}

    def gear_bonus_from_selection(self, armor_set_id=None, messenger_id=None,
                                  acc_left_id=None, acc_right_id=None):
        """Per-build gear bonus from a SELECTED armor set (its pieces in slots 1-6 + the
        3pc/6pc set bonus), a magic messenger (slot 11), and two accessories (left/right).
        Same dict shape as the flat ``gear_bonus``; omitted components contribute nothing."""
        acc = self._empty_gear_acc()
        eq = self.gear.get("equipment", {})
        if armor_set_id not in (None, "", "0"):
            sid = str(armor_set_id); npieces = 0
            for slot in ("1", "2", "3", "4", "5", "6"):
                items = (eq.get(slot) or {}).get("items", [])
                piece = next((it for it in items if str(it.get("set_id")) == sid), None)
                if piece:
                    self._accumulate(piece.get("effects"), acc); npieces += 1
            for sb in self.gear.get("set_bonuses", []):
                if str(sb.get("set_id")) == sid:
                    if npieces >= 3:
                        self._accumulate(sb.get("three_piece"), acc)
                    if npieces >= 6:
                        self._accumulate(sb.get("six_piece"), acc)
        if messenger_id not in (None, "", "0"):
            m = next((it for it in (eq.get("11") or {}).get("items", [])
                      if str(it.get("id")) == str(messenger_id)), None)
            if m:
                self._accumulate(m.get("effects"), acc)
        accs = self.gear.get("accessories", {})
        for side, aid in (("left", acc_left_id), ("right", acc_right_id)):
            if aid not in (None, "", "0"):
                a = next((it for it in (accs.get(side) or {}).get("items", [])
                          if str(it.get("id")) == str(aid)), None)
                if a:
                    self._accumulate(a.get("effects"), acc)
        return acc

    def max_tier_armor_sets(self):
        """[(set_id, set_name)] for the highest-rarity armor sets (the 'best tier' pool)."""
        sbs = self.gear.get("set_bonuses", [])
        if not sbs:
            return []
        maxr = max(int(s.get("rarity") or 0) for s in sbs)
        return [(str(s.get("set_id")), s.get("set_name")) for s in sbs
                if int(s.get("rarity") or 0) == maxr]

    def _max_tier_items(self, items):
        if not items:
            return []
        maxr = max(int(i.get("rarity") or 0) for i in items)
        return [(str(i.get("id")), i.get("name")) for i in items
                if int(i.get("rarity") or 0) == maxr]

    def messenger_items(self):
        return self._max_tier_items((self.gear.get("equipment", {}).get("11") or {}).get("items", []))

    def accessory_items(self, side):
        return self._max_tier_items((self.gear.get("accessories", {}).get(side) or {}).get("items", []))

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
        # parse tokens by buff id (spec C: route by buff_id, not keyword -- 21/98 relics
        # whose bonus is DMG Dealt/Taken / Real DMG Base / Tactical-Pursuit DMG matched no
        # keyword and were dropped).  buff_id namespace:
        #   2=DMG Coefficient, 41=Real DMG Base, 45/1=trigger probability,
        #   5/6=DMG Dealt +/-, 7/8=DMG Taken -/+, 31/33=tactical/pursuit dmg-dealt,
        #   4=blood-sucking.
        coef_val = 0.0
        real_dmg = 0.0
        trigger_val = 0.0
        dmg_dealt = 0.0
        last_val = 0.0
        for tok in rel.get("effect_tokens_max") or []:
            try:
                tv = float(tok.get("value"))
            except (TypeError, ValueError):
                continue
            last_val = tv
            bid = str(tok.get("buff_id"))
            if bid == "2":
                coef_val = tv
            elif bid == "41":
                real_dmg = tv
            elif bid in ("45", "1"):
                trigger_val = tv
            elif bid in ("5", "31", "33"):
                dmg_dealt += tv / 100.0 if tv > 1.0 else tv
            elif bid == "6":
                dmg_dealt -= tv / 100.0 if tv > 1.0 else tv
        val = last_val
        txt = (rel.get("max_bonus") or "").lower()
        if "trigger probability" in txt or trigger_val:
            return {"key": key, "kind": "trigger", "value": trigger_val or val}
        if "coefficient" in txt or coef_val:
            return {"key": key, "kind": "coef",
                    "value": coef_val or val, "real_dmg": real_dmg}
        # standalone Real DMG Base relic (no coefficient text)
        if real_dmg:
            return {"key": key, "kind": "coef", "value": 0.0, "real_dmg": real_dmg}
        # DMG Dealt/Tactical/Pursuit dmg-dealt relic -> hero-wide dmg_dealt channel
        if dmg_dealt:
            return {"key": key, "kind": "dmg_dealt", "value": dmg_dealt}
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
        {'kind':'trigger'|'coef'|'attr', 'value':float, 'stat':<for attr>} or None.

        Spec C / build-aggregation digest fixes:
          * Route Skill/Effect-Trigger-Probability awakens (buff_id 45/1) into trigger
            (135/187 were dropped); match 'trigger probability'/'probability' BEFORE the
            stat fallback.
          * De-route Healing-Coefficient (buff_id 3): require the bare 'dmg coefficient'
            (or non-healing 'coefficient') for kind='coef' so heal-coef awakens stop
            boosting damage.
          * Fix the 'All Attributes Reduced' sign (buff_id 18): apply as negative."""
        aw = self.awake_by_skill.get(tuple(key))
        if not aw:
            return None
        try:
            val = float(aw.get("max_buff_value"))
        except (TypeError, ValueError):
            return None
        bonus_txt = (aw.get("max_bonus") or "").lower()
        # 1. trigger-probability awakens (the dominant dropped class) -> trigger bonus.
        if "probability" in bonus_txt:
            # the awaken value is a percent (e.g. 8.00) -> fraction
            return {"kind": "trigger", "value": val / 100.0 if val > 1.0 else val}
        # 2. healing coefficient is NOT a damage coef -> drop it from the coef channel.
        if "healing" in bonus_txt and "coefficient" in bonus_txt:
            return None
        if "coefficient" in bonus_txt:
            return {"kind": "coef", "value": val}
        # 3. attribute increase/reduce -> figure out which hero stat (+ sign).
        sign = -1.0 if "reduced" in bonus_txt else 1.0
        stat = None
        for kw, s in (("atk", "atk"), ("def", "def"), ("des", "ruin"),
                      ("ruin", "ruin"), ("spd", "speed"), ("speed", "speed")):
            if kw in bonus_txt:
                stat = s
                break
        if "all attribute" in bonus_txt:
            stat = "all"
        return {"kind": "attr", "value": sign * val, "stat": stat}

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
