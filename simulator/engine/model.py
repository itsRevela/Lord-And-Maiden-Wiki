"""Transparent combat model for the Lord & Maiden battle simulator.

WHY A MODEL (read this): the game resolves combat on its servers and ships only a
replay log to the client, so the exact damage equation is *not* extractable
(``data/sim/combat_rules.json`` -> ``modeling_assumptions_server_side``). This module
therefore implements an **explicit, documented, configurable** rules-based model:

  * Every quantity that IS in the client data (hero/troop stats, skill coefficients,
    trigger probabilities, durations, target counts, the restraint triangle, buff
    families) is used verbatim -- these are FACTS.
  * Every quantity that is server-side is a named, tunable field on ``ModelConfig``
    and is tagged ``ASSUMPTION`` below. Nothing is hidden; nothing is "guessed" in
    the sense of a magic literal buried in code.

Because the same model is applied to every candidate build, the simulator's
*relative* rankings are meaningful even though absolute damage is model-relative.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

from . import data as datamod

# Channel -> the hero attribute that (per the client's "Affected by X" hints)
# scales that channel.  FACT that the hint exists; the per-point coefficient is
# ASSUMPTION (combat_rules: attribute_scaling.coefficient_per_200 UNKNOWN).
CHANNEL_PRIMARY_HERO_STAT = {
    "normal": "atk",     # normal ATK scales with ATK
    "tactical": "speed", # Game-Hints: tactical dmg "Affected By Spd"
    "pursuit": "speed",  # pursuit dmg "Affected By Spd"
    "real": "ruin",      # true damage modelled off Ruin/DES
    "splash": "atk",
}


@dataclass(frozen=True)
class ModelConfig:
    """All server-side unknowns live here as tunable, documented knobs.

    Defaults are chosen to be *neutral and monotonic* (more of a good stat ->
    more effectiveness) rather than to match any secret server constant.
    """

    # --- troop count (Soldiers Quantity).  combat_rules.in_battle_stat:
    #     "max = 2000 + Level*500 + Advance bonus".  Level 80 assumed (maxed). ---
    soldier_qty_base: int = 2000              # FACT (stated base)
    soldier_qty_per_level: int = 500          # FACT (stated)
    hero_level: int = 80                       # FACT (max level)
    advance_soldiers_bonus: int = 0            # ASSUMPTION (advance curve server-side)

    # --- free hero stat points (Advancement/Level/Breakthrough).  Constant per
    #     hero across its builds, so it does not bias build-vs-build ranking. ---
    free_stat_points: int = 150               # ASSUMPTION (AdvLv*10 + (Lv-1) + breakthrough)
    free_stat_mode: str = "rpoint"            # "rpoint" | "primary" | "even"

    # --- scale-free exchange model (ASSUMPTION; monotonic & self-normalising) ---
    # Damage is expressed as a FRACTION of the defender's troop pool removed, so it
    # is independent of absolute stat magnitudes and stays balanced as gear scales:
    #   frac = coef * (att_troops_now / def_troops_max)        # army-size & attrition
    #               * A/(A + def_k*D)                          # stat matchup 0..1
    #               * global_lethality * restraint * dmg_mods
    #   A = soldier.atk * (1 + hero_atk/hero_ref)              # offensive index
    #   D = soldier.def * (1 + hero_def/hero_ref)              # defensive index
    hero_ref: float = 200.0                   # ASSUMPTION ("affected per 200 points" hint)
    global_lethality: float = 0.55            # ASSUMPTION (tunes how decisive a hit is)
    def_k: float = 1.0                        # ASSUMPTION (weight of defender DEF)

    # --- "Affected by X attribute" scaling for stat-mod buffs ---
    affected_per_points: float = 200.0        # ASSUMPTION (community-stated ~+1 unit / 200)

    # --- heal / lifesteal (ASSUMPTION; scales off the unit's HP pool) ---
    heal_hp_fraction_ref: float = 1.0

    # --- normal attack baseline coefficient (a plain auto-attack, no skill) ---
    normal_attack_coef: float = 1.0           # ASSUMPTION (auto-attack coefficient)

    # --- rematch / impasse (FACT: undecided after 8 rounds -> rematch, troop
    #     counts carried over from the end of the previous bout; repeats until a
    #     commander is wiped). max_bouts + stalemate guard are a safety ASSUMPTION
    #     (the exact retreat/continuation policy is server-side). ---
    max_bouts: int = 25                       # safety cap on rematches
    bout_stalemate_frac: float = 0.002        # a bout removing < this total -> draw

    # restraint penalty comes from data (0.75); kept here only to allow override
    restraint_modifier_override: Optional[float] = None


@dataclass
class SoldierStats:
    hp: float
    atk: float
    deff: float
    ruin: float
    march: float


@dataclass
class CombatUnit:
    """A maxed hero + its commanded troops, plus mutable in-battle state."""

    # identity
    hero_id: int
    name: str
    race_id: int
    rst: int                      # commanded soldier type 1..4
    soldier_type: int             # chosen troop type (may equal rst or be varied)
    soldier_type_name: str
    role: str
    is_commander: bool
    fight_pos: int                # 1..6 (1-3 sideA, 4-6 sideB; 1 & 4 commanders)
    side: int                     # 0 or 1

    # maxed hero attributes
    atk: float
    deff: float
    ruin: float
    speed: float

    # commanded troops
    troops_max: int
    soldier: SoldierStats

    # resolved skills (list of skill dicts from data, maxed) by category
    skills: list = field(default_factory=list)

    # gear-derived, read-only bonuses (relic = hero's own; rune/awaken = per skill)
    skill_trigger_bonus: dict = field(default_factory=dict)  # (st,id) -> +trigger prob
    channel_trigger: dict = field(default_factory=dict)      # 'tactical'/'pursuit' -> +prob
    skill_coef_bonus: dict = field(default_factory=dict)     # (st,id) -> +coefficient

    # mutable combat state
    hp: float = 0.0
    hp_max: float = 0.0
    alive: bool = True
    statuses: dict = field(default_factory=dict)  # buff_id -> {"rounds":int, "value":float, "stacks":int}

    def stat(self, key: str) -> float:
        return {"atk": self.atk, "def": self.deff, "ruin": self.ruin, "speed": self.speed}[key]


# ----------------------------------------------------------------------------
#  Build aggregation: BuildSpec -> CombatUnit (all maxed bonuses applied)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class BuildSpec:
    hero_id: int
    soldier_type: int                       # 1..4
    is_commander: bool = False
    skill_keys: Optional[tuple] = None      # ((st,id),...) modular override; None -> hero default


def _distribute_free_points(cfg: ModelConfig, rpoint_values, primary_key):
    """Return {'atk','def','ruin','speed': added_points}."""
    pts = cfg.free_stat_points
    keys = ["atk", "def", "ruin", "speed"]
    if cfg.free_stat_mode == "even" or (cfg.free_stat_mode == "rpoint" and sum(rpoint_values or []) == 0):
        share = pts / 4.0
        return {k: share for k in keys}
    if cfg.free_stat_mode == "primary":
        out = {k: 0.0 for k in keys}
        out[primary_key] = pts
        return out
    # rpoint: distribute proportional to the preset weights [atk,def,ruin,speed]
    total = sum(rpoint_values)
    return {keys[i]: pts * (rpoint_values[i] / total) for i in range(4)}


def _soldier_stats(g: datamod.GameData, cfg: ModelConfig, soldier_type: int,
                   soldier_pct: dict, soldier_flat: dict) -> SoldierStats:
    base = g.troop_max_stats(soldier_type)
    def val(stat_key, base_val):
        pct = soldier_pct.get(stat_key, 0.0)
        flat = soldier_flat.get(stat_key, 0.0)
        return base_val * (1.0 + pct / 100.0) + flat
    return SoldierStats(
        hp=val("HP", base["health"]),
        atk=val("ATK", base["attack"]),
        deff=val("DEF", base["defense"]),
        ruin=val("DES", base["ruin"]),
        march=val("MarchSpd", base["movement_speed"]),
    )


# map combo/talent attr_en -> our soldier stat key
_SOLDIER_ATTR_KEY = {
    "Soldier HP": "HP", "Soldier ATK": "ATK", "Soldier DEF": "DEF",
    "Soldier DES": "DES", "Soldier March Spd": "MarchSpd",
    "Infantry HP": "HP", "Archer ATK": "ATK", "Cavalry DEF": "DEF", "Chariot DES": "DES",
}


def build_team(g: datamod.GameData, specs, side: int, cfg: ModelConfig,
               fight_pos_base: int) -> list:
    """Turn 3 BuildSpecs into 3 CombatUnits with all team-composition bonuses
    (soldier combinations, race combinations, affection, talents) applied."""
    specs = list(specs)
    # team-wide counts for combinations
    soldier_counts: dict = {}
    race_counts: dict = {}
    for s in specs:
        h = g.hero(s.hero_id)
        soldier_counts[s.soldier_type] = soldier_counts.get(s.soldier_type, 0) + 1
        race_counts[h["race"]["id"]] = race_counts.get(h["race"]["id"], 0) + 1

    units = []
    for i, s in enumerate(specs):
        h = g.hero(s.hero_id)
        # --- hero attributes: growth(Lv80) + free points + race combo + affection ---
        m = h["maxed_lv80"]
        atk, deff, ruin, spd = (float(m["attack"]), float(m["defense"]),
                                float(m["ruin"]), float(m["speed"]))
        # free stat points
        primary = {"atk": atk, "def": deff, "ruin": ruin, "speed": spd}
        primary_key = max(primary, key=primary.get)
        rp = (h.get("rpoint") or {}).get("values") or [0, 0, 0, 0]
        add = _distribute_free_points(cfg, rp, primary_key)
        atk += add["atk"]; deff += add["def"]; ruin += add["ruin"]; spd += add["speed"]
        # race combination (All Attributes +5 / +10)
        rc = g.race_combo(h["race"]["id"], race_counts.get(h["race"]["id"], 0))
        if rc:
            bonus = 0
            for e in rc.get("effects", []):
                bonus = max(bonus, int(round(float(e.get("raw_value", e.get("value", 0))))))
            atk += bonus; deff += bonus; ruin += bonus; spd += bonus
        # affection: All Attributes + max (assume maxed)
        aff = g.affection_max_all_attr
        atk += aff; deff += aff; ruin += aff; spd += aff

        # --- soldier % bonuses: soldier combo + matching soldier talent ---
        soldier_pct: dict = {}
        soldier_flat: dict = {}
        sc = g.soldier_combo(s.soldier_type, soldier_counts.get(s.soldier_type, 0))
        if sc:
            for e in sc.get("effects", []):
                key = _SOLDIER_ATTR_KEY.get(e.get("attr_en"))
                if key:
                    soldier_pct[key] = soldier_pct.get(key, 0.0) + float(e.get("percent", 0.0))
        tal = g.soldier_talent_percent(s.soldier_type)
        if tal:
            attr_en, pct = tal
            key = _SOLDIER_ATTR_KEY.get(attr_en)
            if key:
                # maxed_cumulative.percent is already in percent units (30.0 = +30%)
                soldier_pct[key] = soldier_pct.get(key, 0.0) + pct

        # --- maxed EQUIPMENT (hero-generic: best item per slot + set bonuses) ---
        gb = g.gear_bonus
        for k, v in gb["soldier_pct"].items():
            soldier_pct[k] = soldier_pct.get(k, 0.0) + v
        for k, v in gb["soldier_flat"].items():
            soldier_flat[k] = soldier_flat.get(k, 0.0) + v
        atk += gb["hero_flat"].get("atk", 0.0); deff += gb["hero_flat"].get("def", 0.0)
        ruin += gb["hero_flat"].get("ruin", 0.0); spd += gb["hero_flat"].get("speed", 0.0)

        soldier = _soldier_stats(g, cfg, s.soldier_type, soldier_pct, soldier_flat)

        # --- troop count: base + level + commander talent flat + gear Soldiers Qty ---
        troops = cfg.soldier_qty_base + cfg.hero_level * cfg.soldier_qty_per_level + cfg.advance_soldiers_bonus
        if s.is_commander:
            troops += g.commander_talent_flat_soldiers()
        troops += gb["troops"]
        troops = int(troops)

        # --- skills (maxed): main + 2 modular ---
        skill_refs = [h["main_skill"]]
        if s.skill_keys:
            skill_refs += [{"st": st, "id": sid} for (st, sid) in s.skill_keys]
        else:
            skill_refs += h.get("modular_default", [])
        skills = []
        seen = set()
        for ref in skill_refs:
            kk = (int(ref["st"]), int(ref["id"]))
            if kk in seen:
                continue          # a hero cannot equip the same skill twice
            seen.add(kk)
            sk = g.skill(*kk)
            if sk:
                skills.append(sk)
        equipped_keys = [(int(sk["st"]), int(sk["id"])) for sk in skills]

        # --- relic (hero's OWN only), rune (1, best matching an equipped skill),
        #     skill-awaken (per equipped skill): trigger-prob & coefficient bonuses ---
        skill_trigger_bonus: dict = {}
        skill_coef_bonus: dict = {}
        rel = g.relic_bonus_for_hero(s.hero_id)   # hero's OWN relic only
        if rel:
            rk, rkind, rv = rel["key"], rel["kind"], rel["value"]
            if rkind == "trigger":
                skill_trigger_bonus[rk] = skill_trigger_bonus.get(rk, 0.0) + rv
            elif rkind == "coef":
                skill_coef_bonus[rk] = skill_coef_bonus.get(rk, 0.0) + rv
            elif rkind == "attr":
                st_ = rel.get("stat")
                if st_ == "atk": atk += rv
                elif st_ == "def": deff += rv
                elif st_ == "ruin": ruin += rv
                elif st_ == "speed": spd += rv
                elif st_ == "all": atk += rv; deff += rv; ruin += rv; spd += rv
        # one rune: the equipped skill with the best available rune trigger
        best_rune = None
        for kk in equipped_keys:
            rt = g.rune_trigger_for_skill(kk)
            if rt and (best_rune is None or rt > best_rune[1]):
                best_rune = (kk, rt)
        if best_rune:
            skill_trigger_bonus[best_rune[0]] = skill_trigger_bonus.get(best_rune[0], 0.0) + best_rune[1]
        # skill-awaken (maxed) for each equipped skill
        for kk in equipped_keys:
            aw = g.awaken_bonus_for_skill(kk)
            if not aw:
                continue
            if aw["kind"] == "coef":
                skill_coef_bonus[kk] = skill_coef_bonus.get(kk, 0.0) + aw["value"]
            elif aw["kind"] == "attr":
                st_ = aw.get("stat"); v = aw["value"]
                if st_ == "atk": atk += v
                elif st_ == "def": deff += v
                elif st_ == "ruin": ruin += v
                elif st_ == "speed": spd += v
                elif st_ == "all": atk += v; deff += v; ruin += v; spd += v
        channel_trigger = {"tactical": gb["trigger_tactical"], "pursuit": gb["trigger_pursuit"]}

        u = CombatUnit(
            hero_id=s.hero_id, name=h["name_en"], race_id=h["race"]["id"],
            rst=h["rst"]["id"], soldier_type=s.soldier_type,
            soldier_type_name=g.soldier_type_name[s.soldier_type],
            role=(h.get("role") or {}).get("name_en", "?"),
            is_commander=s.is_commander, fight_pos=fight_pos_base + i, side=side,
            atk=atk, deff=deff, ruin=ruin, speed=spd,
            troops_max=troops, soldier=soldier, skills=skills,
            skill_trigger_bonus=skill_trigger_bonus, channel_trigger=channel_trigger,
            skill_coef_bonus=skill_coef_bonus,
        )
        u.hp_max = u.hp = troops * soldier.hp
        units.append(u)
    return units


# ----------------------------------------------------------------------------
#  Damage / heal model  (every line tagged FACT or ASSUMPTION)
# ----------------------------------------------------------------------------
def offensive_index(unit: CombatUnit, channel: str, cfg: ModelConfig) -> float:
    """Per-soldier offensive index for ``channel`` = soldier ATK lifted by the
    channel's primary hero stat (Affected-by-X hint). ASSUMPTION (monotonic)."""
    hero_key = CHANNEL_PRIMARY_HERO_STAT.get(channel, "atk")
    return max(1.0, unit.soldier.atk) * (1.0 + unit.stat(hero_key) / cfg.hero_ref)


def defensive_index(unit: CombatUnit, cfg: ModelConfig) -> float:
    """Per-soldier defensive index = soldier DEF lifted by hero DEF. ASSUMPTION."""
    return max(1.0, unit.soldier.deff) * (1.0 + unit.deff / cfg.hero_ref)


def exchange_fraction(attacker: CombatUnit, defender: CombatUnit, coef: float,
                      channel: str, restraint: float, dmg_dealt_mult: float,
                      dmg_taken_mult: float, cfg: ModelConfig) -> float:
    """Fraction of the defender's troop pool removed by one attack instance.

    Scale-free: combines the skill coefficient (FACT), army-size & attrition
    (att troops now / def troops max), the stat matchup A/(A+k*D), restraint
    (FACT 0.75), and the buff multipliers. ``global_lethality`` (ASSUMPTION) sets
    how lethal a single hit is."""
    if coef <= 0 or not defender.alive:
        return 0.0
    A = offensive_index(attacker, channel, cfg)
    if channel in ("real", "splash"):
        matchup = 1.0                         # true damage ignores DEF
    else:
        D = defensive_index(defender, cfg)
        matchup = A / (A + cfg.def_k * D)
    army = attacker.troops_now() / max(1.0, defender.troops_max)
    frac = (coef * army * matchup * cfg.global_lethality
            * restraint * dmg_dealt_mult * dmg_taken_mult)
    return max(0.0, frac)


def restraint_mult(g: datamod.GameData, attacker: CombatUnit, defender: CombatUnit,
                   cfg: ModelConfig) -> float:
    """0.75 if attacker's soldier type is restrained by defender's; else 1.0.
    FACT: the triangle and 0.75 are stated (Tips.csv Id=350). Application point is
    ASSUMPTION (applied to the restrained side's outgoing damage)."""
    mod = cfg.restraint_modifier_override
    if mod is None:
        mod = g.restraint_modifier
    a_name = g.soldier_type_name[attacker.soldier_type]
    d_name = g.soldier_type_name[defender.soldier_type]
    # attacker is restrained (countered) when defender's type beats attacker's,
    # i.e. triangle[defender] == attacker
    if g.restraint_triangle.get(d_name) == a_name:
        return mod
    return 1.0


# small helpers bolted onto CombatUnit (kept here to avoid import cycle noise)
def _troops_now(self) -> float:
    return 0.0 if self.hp_max <= 0 else self.troops_max * (self.hp / self.hp_max)


CombatUnit.troops_now = _troops_now


def fresh_units(units):
    """Cheap per-battle clone: copy each unit with full HP, alive, empty statuses.
    Static fields (soldier, skills, stats) are shared read-only; combat never
    mutates them, so this is safe and far faster than rebuilding the team."""
    return [replace(u, hp=u.hp_max, alive=True, statuses={}) for u in units]
