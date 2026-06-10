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

This file was reworked to match the in-game battle log ("Rosetta Stone",
``data/sim/calibration.json``).  The damage model is now an absolute-magnitude
formula (it reproduces the log's per-hit Loss values within an order-of-magnitude
band), structured EXACTLY as the calibration notes derived:

    dmg = coef[ch] * off(att,ch) * troop_scale(att)
              * def_mitigation(def)            # =1 for real/assault/splash
              * dmg_dealt_mult(att,ch)
              * dmg_taken_mult(def,ch)
              * restraint(att,def)

Casualties are tracked in three buckets per unit (Health / SlightWound /
SevereWound+Death) so the simulator reproduces the log's (current/max) notation and
its per-unit Kills/Heal/Wound tables.  Because the same model is applied to every
candidate build, the simulator's *relative* rankings remain meaningful.
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
    "tactical": "atk",   # tactical (skill) damage scales mainly with ATK (calibration)
    "pursuit": "speed",  # pursuit dmg "Affected By Spd"
    "real": "atk",       # Ghost-Bone Assault real dmg "Affected By ATK Attribute"
    "splash": "atk",
}


@dataclass(frozen=True)
class ModelConfig:
    """All server-side unknowns live here as tunable, documented knobs.

    Defaults are CALIBRATED against ``data/sim/calibration.json`` (the in-game log)
    so a maxed 55k-troop hero produces per-hit losses in the logged range, while
    remaining neutral/monotonic (more of a good stat -> more effectiveness)."""

    # --- troop count (Soldiers Quantity).  combat_rules.in_battle_stat:
    #     "max = 2000 + Level*500 + Advance bonus".  Level 80 assumed (maxed).
    #     The log shows 55,000 troops per unit at +5 advancement, so the advance
    #     bonus knob is set to land there (FACT target: 55k). ---
    soldier_qty_base: int = 2000              # FACT (stated base)
    soldier_qty_per_level: int = 500          # FACT (stated)
    hero_level: int = 80                       # FACT (max level)
    advance_soldiers_bonus: int = 13000        # ASSUMPTION calibrated -> 55,000 total

    # --- free hero stat points (Advancement/Level/Breakthrough).  Constant per
    #     hero across its builds, so it does not bias build-vs-build ranking. ---
    free_stat_points: int = 150               # ASSUMPTION (AdvLv*10 + (Lv-1) + breakthrough)
    free_stat_mode: str = "rpoint"            # "rpoint" | "primary" | "even"
    # the testcase units allocate +229 into a single stat ("+229 ATK", etc.).
    # When a BuildSpec pins an allocation stat, this many points go there. ---
    allocated_stat_points: int = 229          # FACT (log: "+229 ATK/DEF/DES/ATK SPD")

    # --- ABSOLUTE damage model (calibrated to the log) -----------------------
    # raw = coef * off(att,ch) * troop_scale(att)
    #   off(att,ch) = (soldier_off_stat + hero_stat*hero_off_weight) -- offence index
    #   troop_scale = troops_now / troop_scale_ref  (army-size & attrition factor)
    # mitigation (DEF):  def_ref / (def_ref + DEF_eff),  DEF_eff = hero_def*hero_def_weight
    damage_global: float = 7.0                # ASSUMPTION global lethality scalar (calibrated)
    hero_off_weight: float = 1.0              # ASSUMPTION hero-stat weight in offence
    troop_scale_ref: float = 55000.0          # ASSUMPTION army-size reference (= full troop)
    def_ref: float = 900.0                    # ASSUMPTION DEF mitigation midpoint
    hero_def_weight: float = 1.0              # ASSUMPTION hero-DEF weight in mitigation

    # --- Assault / real damage (flat, DEF-independent).  Log: ~671-726 per hit,
    #     stated "Real DMG Base 32.17+7.2".  We scale the stated base by an army &
    #     ATK factor so it sits in that band. ---
    real_dmg_scale: float = 17.5              # ASSUMPTION scales stated Real-DMG base

    # --- "Affected by X attribute" scaling for stat-mod buffs ---
    affected_per_points: float = 200.0        # ASSUMPTION (community-stated ~+1 unit / 200)

    # --- heal (Self-Heal / Field Therapy) restores Slight->Health.  Log: 0..~5000
    #     per round depending on how wounded the unit is.  Healing Coefficient shown
    #     1.05+0.28 (ally).  We model it as coef * heal_power * (slight pool). ---
    heal_scale: float = 0.45                  # ASSUMPTION heal magnitude scalar

    # --- casualty model (server-side; ASSUMPTION shapes) ---------------------
    # Of each damage instance, a portion goes straight to Severe/Death (permanent),
    # the rest to Slight (recoverable). Between rounds a share of Slight worsens to
    # Severe/Death (lowers max). Calibrated so B1 ends ~80-85% / ~30% Health. ---
    direct_severe_frac: float = 0.012         # ASSUMPTION fraction of a hit -> permanent
    slight_worsen_frac: float = 0.018         # ASSUMPTION per-round Slight->Severe/Death

    # --- normal attack baseline coefficient (a plain auto-attack, no skill) ---
    normal_attack_coef: float = 0.9           # ASSUMPTION (auto-attack coefficient)

    # --- reactions / procs (coefficients are FACT from skills; these gate them) ---
    counter_coef: float = 0.84                # FACT (Reactive Block 0.70+0.14)
    reactive_block_reduction: float = 0.592   # FACT (log: DMG Taken Reduced 59.20%)
    # Stated +33% per stalemate; the model uses a higher effective value so a rematch
    # resolves in ~2 bouts as the log shows (other approximations damp it). The buff
    # also escalates super-linearly here to force a decision (the log's `-1` suffix
    # suggests an escalating stack). ASSUMPTION effective.
    stalemate_dmg_dealt_per_stack: float = 0.85  # FACT base 0.33, ASSUMPTION effective

    # --- prepared-CC EFFECTIVE re-roll bases.  Stated bases are 40% (allies) /
    #     60% (enemies); resist + per-round Purification net the EFFECTIVE activation
    #     down (the log shows the carry firing nearly every round). ASSUMPTION net. ---
    prepared_cc_ally_base: float = 0.22       # 40% stated, netted by purify/resist
    prepared_cc_enemy_base: float = 0.45      # 60% stated, netted by purify/resist

    # --- rematch / impasse (FACT: undecided after 8 rounds -> rematch, troop
    #     counts carried over; repeats until a commander is wiped). ---
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

    # maxed hero attributes (BASE, before in-battle buffs/debuffs)
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
    real_dmg_bonus: dict = field(default_factory=dict)       # (st,id) -> +Real DMG Base flat
    gear_dmg_dealt: float = 0.0    # PVE/PVP DMG Dealt Increased from equipment+messenger
    gear_dmg_taken: float = 0.0    # PVE/PVP DMG Taken Reduced from equipment+messenger

    # mutable combat state -- CASUALTY BUCKETS (troops, not HP-per-soldier).
    # current(Health) + slight(SlightWound) recoverable; max = health+slight.
    # severe_death = permanent losses already removed from troops_max_eff.
    health: float = 0.0           # live fighting troops (the effective "current")
    slight: float = 0.0           # temporarily downed, healable
    severe_death: float = 0.0     # permanent (severe wound + death)
    alive: bool = True
    statuses: dict = field(default_factory=dict)  # buff_id -> {"rounds","value","stacks","ch"}

    # in-battle dynamic attribute modifiers (set during Pre-War Preparation etc.)
    attr_mods: dict = field(default_factory=dict)  # stat -> {"add":float,"locked":bool}

    # per-unit stat tracking (compared to the log's tables)
    stat_kills: float = 0.0       # total enemy Health removed by this unit
    stat_heal: float = 0.0        # total Slight->Health restored to allies by this unit
    stat_slight: float = 0.0      # SlightWound inflicted on enemies
    stat_severe: float = 0.0      # SevereWound inflicted
    stat_death: float = 0.0       # Death inflicted
    stat_skill_dmg: float = 0.0   # damage dealt via skills
    stat_normal_dmg: float = 0.0  # damage dealt via normal attacks
    skills_used: int = 0

    # ---- attribute access (base + in-battle mods) ----------------------
    def base_stat(self, key: str) -> float:
        return {"atk": self.atk, "def": self.deff, "ruin": self.ruin, "speed": self.speed}[key]

    def eff_stat(self, key: str) -> float:
        v = self.base_stat(key)
        m = self.attr_mods.get(key)
        if m:
            v += m.get("add", 0.0)
        return max(0.0, v)

    def stat(self, key: str) -> float:          # back-compat alias
        return self.eff_stat(key)

    # ---- casualty helpers ----------------------------------------------
    @property
    def current(self) -> float:                 # Health (log: left of the slash)
        return self.health

    @property
    def cur_max(self) -> float:                  # Health + Slight (log: right of slash)
        return self.health + self.slight

    def troops_now(self) -> float:
        return self.health

    def troops_frac(self) -> float:
        return 0.0 if self.troops_max <= 0 else self.health / self.troops_max

    # ---- back-compat display aliases (the UI / smoke test print these) ----
    @property
    def hp_max(self) -> float:
        return float(self.troops_max) * self.soldier.hp

    @property
    def hp(self) -> float:
        return self.health * self.soldier.hp


# ----------------------------------------------------------------------------
#  Build aggregation: BuildSpec -> CombatUnit (all maxed bonuses applied)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class BuildSpec:
    hero_id: int
    soldier_type: int                       # 1..4
    is_commander: bool = False
    skill_keys: Optional[tuple] = None      # ((st,id),...) modular override; None -> hero default
    allocated_stat: Optional[str] = None    # 'atk'|'def'|'ruin'|'speed' -- log "+229 X"


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
        # free stat points: if the build pins an allocation stat (log "+229 X"),
        # dump cfg.allocated_stat_points there; otherwise use the rpoint preset.
        if s.allocated_stat in ("atk", "def", "ruin", "speed"):
            add = {"atk": 0.0, "def": 0.0, "ruin": 0.0, "speed": 0.0}
            add[s.allocated_stat] = float(cfg.allocated_stat_points)
        else:
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
        real_dmg_bonus: dict = {}
        rel = g.relic_bonus_for_hero(s.hero_id)   # hero's OWN relic only
        if rel:
            rk, rkind, rv = rel["key"], rel["kind"], rel["value"]
            if rkind == "trigger":
                skill_trigger_bonus[rk] = skill_trigger_bonus.get(rk, 0.0) + rv
            elif rkind == "coef":
                skill_coef_bonus[rk] = skill_coef_bonus.get(rk, 0.0) + rv
                # Patra-style relic also carries a Real DMG Base add (token id 41)
                rdb = rel.get("real_dmg")
                if rdb:
                    real_dmg_bonus[rk] = real_dmg_bonus.get(rk, 0.0) + rdb
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
            skill_coef_bonus=skill_coef_bonus, real_dmg_bonus=real_dmg_bonus,
            gear_dmg_dealt=gb.get("dmg_dealt", 0.0), gear_dmg_taken=gb.get("dmg_taken", 0.0),
        )
        u.health = float(troops)
        u.slight = 0.0
        u.severe_death = 0.0
        units.append(u)
    return units


# ----------------------------------------------------------------------------
#  Damage / heal model  (every line tagged FACT or ASSUMPTION)
# ----------------------------------------------------------------------------
def offence(unit: CombatUnit, channel: str, cfg: ModelConfig) -> float:
    """Per-instance offence index = soldier offence stat lifted by the channel's
    primary hero stat (Affected-by-X hint). ASSUMPTION (monotonic)."""
    hero_key = CHANNEL_PRIMARY_HERO_STAT.get(channel, "atk")
    return max(1.0, unit.soldier.atk) + unit.eff_stat(hero_key) * cfg.hero_off_weight


def troop_scale(unit: CombatUnit, cfg: ModelConfig) -> float:
    """Army-size & attrition factor: a unit hits harder with more live troops."""
    return unit.health / max(1.0, cfg.troop_scale_ref)


def def_mitigation(defender: CombatUnit, channel: str, cfg: ModelConfig) -> float:
    """Multiplicative DEF mitigation in (0,1].  Real/assault/splash ignore DEF."""
    if channel in ("real", "assault", "splash"):
        return 1.0
    def_eff = defender.eff_stat("def") * cfg.hero_def_weight
    return cfg.def_ref / (cfg.def_ref + def_eff)


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
    if g.restraint_triangle.get(d_name) == a_name:
        return mod
    return 1.0


def fresh_units(units):
    """Cheap per-battle clone: copy each unit at full Health, alive, empty statuses.
    Static fields (soldier, skills, stats) are shared read-only."""
    out = []
    for u in units:
        c = replace(u, health=float(u.troops_max), slight=0.0, severe_death=0.0,
                    alive=True, statuses={}, attr_mods={},
                    stat_kills=0.0, stat_heal=0.0, stat_slight=0.0, stat_severe=0.0,
                    stat_death=0.0, stat_skill_dmg=0.0, stat_normal_dmg=0.0, skills_used=0)
        out.append(c)
    return out
