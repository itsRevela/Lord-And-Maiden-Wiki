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
    # FACT (digest multihit-aoe-procs + spec B): affectedByAttr==0 on EVERY direct
    # at=101 effect including pursuit, and calibration_3_findings #4 concluded pursuit
    # DAMAGE scales with ATK (Speed governs trigger/turn-order only).  Was "speed".
    "pursuit": "atk",    # pursuit dmg scales with ATK (Spd only gates trigger/order)
    "real": "atk",       # Ghost-Bone Assault real dmg "Affected By ATK Attribute"
    "splash": "atk",
    "dot": "ruin",       # Burn/Curse DoT scales with the CASTER's DES/Ruin (calibration_2)
}


def level_ratio(sk, level: int) -> float:
    """Scale a skill's per-effect coefficient from lv10 (=maxedValue) down to `level`.

    FACT (decompiled GetSkillUpDes 9940-9949; verified across all 416 skills):
        coef(L) = initVal + L*upVal,  maxedValue == coef(10).
    The per-effect token coefficient stored in skills.json is the lv10/raw per-hit
    value the in-game logs fit, so for main/modular (lv10) this returns 1.0 (no change).
    A lv5 STONE returns the exact ratio (initVal+5*upVal)/(initVal+10*upVal) (~0.745-0.76,
    NOT a flat 75%).  When the skill lacks init/up data, falls back to 1.0 (lv10)."""
    try:
        L = int(level)
    except (TypeError, ValueError):
        return 1.0
    if L >= 10:
        return 1.0
    try:
        init = float(sk.get("initVal"))
        up = float(sk.get("upVal"))
    except (TypeError, ValueError):
        return 1.0
    denom = init + 10.0 * up
    if denom <= 0:
        return 1.0
    return max(0.0, (init + L * up) / denom)


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
    allocated_stat_points: int = 229          # FACT 5★ cap; star-aware in build_team (5★=229/4★=179/3★=129)

    # --- ABSOLUTE damage model (calibrated to BOTH logs) ---------------------
    # raw = coef * off(att,ch) * troop_scale(att) * damage_global
    #   off(att,ch) = (soldier_off_stat + hero_stat*hero_off_weight) -- offence index
    #   troop_scale = troops_now / troop_scale_ref  (army-size & attrition factor)
    # mitigation (DEF):  def_ref / (def_ref + DEF_eff),  DEF_eff = hero_def*hero_def_weight
    #
    # CALIBRATION (2026-06): re-fit to the clean "Vanilla Baseline" mirror
    # (notes/sim/calibration_1_baseline.md/_findings.md -> validate_baseline.py) AND the
    # original shielded-tank Rosetta Stone (validate_testcase.py).  The clean fight pins
    # the normal-hit magnitudes (~4,000-5,600 at these stats) and the DEF curve.  Per the
    # findings, the user ran the mirror TWICE and got one LOSS + one WIN, so the true
    # target is a CLOSE COIN-FLIP (~50%, the +DEF commander only tilts it), NOT a
    # deterministic enemy win.  The fit:
    #   * normal_attack_coef * damage_global = 24.263  (the combined per-hit scalar K
    #     least-squares-fit to the 5 clean round-1 normal-attack readings in the log;
    #     with normal_attack_coef=0.9 -> damage_global=26.959).  relerr ~3.2%; the 5
    #     clean normals land in the logged ~4,000-5,600 band.
    #   * hero_off_weight=0.20: ATK lifts offence enough to reproduce the log's
    #     same-base-hero ATK ordering (ally Dolly+ATK 5,641 > enemy Dolly+DES 4,516) yet
    #     stays modest, so the player's +ATK edge does NOT steamroll the enemy's +DEF edge.
    #   * def_ref=600 + hero_def_weight=2.0: a DEF curve that makes the +DEF commander
    #     meaningfully tankier (at DEF~403 mitigation ~= 600/(600+806) ~ 0.43x vs ~0.63x
    #     at DEF~174) -- enough to TILT the mirror so the enemy wins ~52% (a coin-flip,
    #     matching the user's 1-loss/1-win observation), not to flip it deterministically.
    #     This also leaves validate_testcase at 9/9: there the shielded tank's survival is
    #     driven by capped DMG-Taken-Reduced (max_dmg_taken_reduction), not DEF, so the
    #     DEF curve is orthogonal to that fight.
    # All four remain ASSUMPTION (server-side); the VALUES are calibrated to the logs.
    # RE-FIT (2026-06, wave-based skill firing): using the per-effect token coefficient
    # (x level scaling) per wave instead of the skill's maxedValue roughly HALVES raw
    # skill damage and the per-effect triggerChance gate cuts multi-hit volume, so the
    # global scalars are re-derived TOGETHER (spec E).  damage_global is fit so a clean
    # Niya pursuit (Slayer lv10 coef 0.6) lands ~4,800-5,180 and her Rift lv5 stone
    # (per-effect 0.25 * lv5-ratio 0.75 = 0.1875) lands ~1,550 (calibration_3_pursuit.md),
    # while normal_attack_coef is lowered so the clean baseline normals stay in the logged
    # ~4,000-5,600 band (calibration_1).  Both remain ASSUMPTION (server-side magnitude).
    damage_global: float = 65.0               # CALIBRATED to captured per-hit ground truth (dg=65 universal; strikers = base x (1-Skyland DTR)); see GROUND_TRUTH.md S9
    # Lifted 0.20 -> 0.30 toward the MEASURED clean isolated allocation effect ~1.25x
    # (calibration_1_findings:29-30; build-aggregation digest VALIDATION CORRECTIONS).  At
    # 0.30 the +ATK-vs-+DES offence ratio is ~1.22x (engine was 1.16x), so +ATK heroes
    # out-deal +DEF/+DES as the logs show, WITHOUT cranking it to chase a 2x (that lives in
    # throughput + in-battle buffs).  Re-checked: baseline mirror stays a ~40-50% coin-flip.
    hero_off_weight: float = 0.30             # ASSUMPTION hero-stat weight in offence (fit to ~1.25x clean allocation)
    troop_scale_ref: float = 55000.0          # ASSUMPTION army-size reference (= full troop)
    # Spec B: sub-linear (~sqrt) attacker-attrition curve for DIRECT channels (pursuit log
    # SusaMaki decay backs out exponent ~0.52); 1.0 at full troops so the clean anchors are
    # unchanged.  LABELED ASSUMPTION fit to the logged decay; real/assault/dot keep their
    # own floored factors.
    troop_scale_exp: float = 0.6              # ASSUMPTION attacker-attrition exponent (~sqrt; ~0.52 measured, noisy)
    def_ref: float = 600.0                    # ASSUMPTION DEF mitigation midpoint (tuned so +DEF tilts the mirror to a coin-flip)
    hero_def_weight: float = 2.0              # ASSUMPTION hero-DEF weight in mitigation

    # --- Assault / real damage (flat, DEF-independent).  Log: ~671-726 per hit,
    #     stated "Real DMG Base 32.17+7.2".  We scale the stated base by an army &
    #     ATK factor so it sits in that band. ---
    real_dmg_scale: float = 17.5              # ASSUMPTION scales stated Real-DMG base

    # --- Burn / Curse DAMAGE-OVER-TIME channel (calibrated to calibration_2_dot.md) ---
    # A DoT tick fires at the BEFORE-ACTION phase for the effect's duration, applied
    # to the skill's target count.  The findings pin the shape:
    #   * ~LINEAR in the printed coefficient (Burn coef 1.0 ~= 2x Curse coef 0.5).
    #   * scales with the CASTER (DES/Ruin via offence("dot") + troop_scale), NOT the
    #     target's HP -- ticks fall as the caster loses troops.
    #   * MILDLY DEF-mitigated (its own gentle curve, weaker than the direct channel).
    # tick = coef * off(caster,"dot") * troop_factor(caster) * dot_global * dot_def_mitig
    #   off(caster,"dot") = soldier.atk + Ruin*hero_off_weight  (channel stat = ruin)
    #   troop_factor = dot_troop_floor + (1-dot_troop_floor)*troop_scale(caster)
    #     (a FLOOR so a near-dead caster still ticks for a few hundred, as R8=674 shows)
    #   dot_def_mitig = dot_def_ref / (dot_def_ref + DEF*dot_def_weight)
    # Fit: least-squares over the 8 logged Burn/Curse anchors -> mean rel-err ~13%.
    # All ASSUMPTION (server-side); values calibrated to the log.
    # RE-FIT (spec E): removing the DoT DEF-mitigation curve (~0.5x) and gating the enemy
    # multi-hit over-count both changed the DoT balance, so dot_global is re-derived DOWN
    # (24.2 -> 6.0) so Burn ticks stay in the logged ~700-4,000 band (calibration_2_dot.md;
    # ~98% in band, median ~1,900) and detonate bursts in ~3,100-6,700.
    dot_global: float = 6.0                   # ASSUMPTION global DoT lethality scalar (re-fit; no DEF term now)
    dot_troop_floor: float = 0.15             # ASSUMPTION floor of the caster troop factor
    dot_def_ref: float = 900.0                # ASSUMPTION DoT DEF-mitigation midpoint (mild)
    dot_def_weight: float = 2.0               # ASSUMPTION hero-DEF weight in DoT mitigation
    # Detonate (Element-Burst style, actionType 72 on Exploding Flame, coef 1.6): a
    # chance, when re-casting the Burn skill while the target already carries Burn, to
    # CONSUME the DoT for a burst = dot_detonate_coef * the would-be remaining tick.
    # Log bursts ~3.1k-6.7k; a multiple of the ~1.5-3.5k tick reproduces that band.
    dot_detonate_chance: float = 0.4          # ASSUMPTION detonate trigger chance
    dot_detonate_coef: float = 1.2            # ASSUMPTION burst multiple of remaining tick

    # --- "Affected by X attribute" scaling for stat-mod buffs ---
    affected_per_points: float = 200.0        # ASSUMPTION (community-stated ~+1 unit / 200)
    # DMG-Taken-Reduced (buff 8) scales with the CASTER's DEF.  DERIVED from 2 captured Skyland
    # points (Thiel DEF 589.6 -> 19.32%, DEF 438.4 -> 16.41%, coef 0.08): DTR = coef*(1+DEF/417).
    # Cross-checks Rhea's Star Shield (coef 0.25 + high DEF + 30% relic -> capped). See GROUND_TRUTH.md.
    dtr_def_ref: float = 417.0                # DERIVED (captures); was a spurious x6.0 fudge before

    # --- heal (Self-Heal / Field Therapy) restores Slight->Health.  Log: 0..~5000
    #     per round depending on how wounded the unit is.  Healing Coefficient shown
    #     1.05+0.28 (ally).  We model it as coef * heal_power * (slight pool). ---
    # RE-FIT (spec D): the heal now scales off the HEALER's troops (coef*heal_scale*
    # healer_troops*floored-factor) instead of the target's Slight pool, so the scalar is
    # re-derived to keep restores in the logged ~1.1-1.6k/round band (calibration_2_dot).
    heal_scale: float = 0.063                 # DERIVED from captures: heal = coef x 0.063 x max_troops, capped by recoverable, scales w/ MAX troops (constant as current fell 49k->23k). See GROUND_TRUTH.md

    # --- casualty model (server-side; ASSUMPTION shapes) ---------------------
    # Of each damage instance, a portion goes straight to Severe/Death (permanent),
    # the rest to Slight (recoverable). Between rounds a share of Slight worsens to
    # Severe/Death (lowers max). Calibrated so B1 ends ~80-85% / ~30% Health. ---
    direct_severe_frac: float = 0.012         # ASSUMPTION fraction of a hit -> permanent
    slight_worsen_frac: float = 0.018         # ASSUMPTION per-round Slight->Severe/Death

    # --- normal attack baseline coefficient (a plain auto-attack, no skill) ---
    # RE-FIT (spec E): lowered from 0.9 jointly with the higher damage_global so the
    # combined normal scalar (damage_global*normal_attack_coef ~= 24.2) keeps the clean
    # baseline normals in the logged ~4,000-5,600 band while skills scale up.
    normal_attack_coef: float = 0.46          # ASSUMPTION (auto-attack coefficient; re-fit with damage_global)
    # SKILL first-pick commander weight (documented SERVER-SIDE UNKNOWN: whether the 20/40/40
    # normal-attack weighting also governs damaging-SKILL targeting). Pursuit-log evidence says
    # skills favour strikers over the commander -- the player's STRIKER (Mia) died while the
    # +ATK commander (SusaMaki) survived, and a striker (Dolly) fell on the enemy side too. So
    # skills target the commander LESS than a normal (0.20) does. ASSUMPTION knob; normal
    # attacks keep the FACT 0.20 in _pick_target.
    skill_commander_target_weight: float = 0.2

    # --- reactions / procs (coefficients are FACT from skills; these gate them) ---
    counter_coef: float = 0.84                # FACT (Reactive Block 0.70+0.14)
    reactive_block_reduction: float = 0.592   # FACT (log: DMG Taken Reduced 59.20%)
    # DMG-Taken-Reduced does NOT sum to near-immunity: the log shows Star Shield
    # (displayed "90.17%+30%") leaving the commander at ~74% effective reduction
    # (Magic Spear hit her for 2,139 vs 19,116 on an amplified target; backing out DEF
    # mitigation => ~26% gets through). So the TOTAL reduction is capped here.
    max_dmg_taken_reduction: float = 0.75     # CALIBRATED from log (~74% effective cap)
    # FACT (log L676): a rematch after a stalemate grants "All Hero DMG Dealt +33%"
    # per prior stalemate. Use the logged value verbatim; the match simply takes a
    # few bouts to resolve (faithful, not forced to exactly 2).
    stalemate_dmg_dealt_per_stack: float = 0.33  # FACT (log: Stalemate-1 +33%)

    # --- prepared-CC per-round re-roll bases. FACT from the log: the carry-over
    #     Silence(Prepared) re-rolls each round at 40% (allies) / 60% (enemies),
    #     +flat from skill-stone/rune (shown as "40.00%+12.00%"). ---
    prepared_cc_ally_base: float = 0.40       # FACT (log: ally trigger 40%+flat)
    prepared_cc_enemy_base: float = 0.60      # FACT (log: enemy trigger 60%+flat)

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
    # per-skill equipped LEVEL: (st,id) -> level.  Main/modular = lv10 (=maxedValue);
    # skill STONES = lv5.  Drives coef(L)=initVal+L*upVal in combat (FACT: decompiled
    # GetSkillUpDes 9940-9949; lv10=maxedValue verified across all 416 skills).
    skill_level: dict = field(default_factory=dict)

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
    # readyRound charge state: (st,id) -> True while a prep skill is charging (fires next)
    _charged: dict = field(default_factory=dict)

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
            # Lv80 free-point cap is star-dependent (FACT, decompiled maxed-preview
            # cs:77749-77767): 5★=+229, 4★=+179, 3★=+169 (= AdvLv 3*10 + (Lv-1) 79 +
            # 3*BreakthroughLv 20*3 = 30+79+60 = 169; the old 129 was wrong -- spec C).
            pts = {5: 229.0, 4: 179.0, 3: 169.0}.get(int(h["star"]), float(cfg.allocated_stat_points))
            add = {"atk": 0.0, "def": 0.0, "ruin": 0.0, "speed": 0.0}
            add[s.allocated_stat] = pts
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

        # --- troop count by hero STAR (in-game baseline log, Lv80 advancement 5):
        #     5★=55,000, 4★=51,000 (Nicole), 3★≈47,000 (estimated, -4,000/star). The log
        #     shows NO commander troop bonus (commander Thiel 5★ = 55,000, same as a
        #     non-commander 5★), so the old +commander_talent is dropped. FACT (5★/4★). ---
        troops = {5: 55000, 4: 51000, 3: 49000}.get(
            int(h["star"]),
            cfg.soldier_qty_base + cfg.hero_level * cfg.soldier_qty_per_level + cfg.advance_soldiers_bonus)
        troops += gb["troops"]      # gear Soldiers-Quantity (0 for the baseline gear set)
        troops = int(troops)

        # --- skills: main(lv10) + 2 modular(lv10) + 1 skill STONE(lv5) ---
        # The build sheets field main & modular at max (lv10 = maxedValue) and a skill
        # stone equipped at lv5 (FACT: level-scaling digest).  The validators / loadout
        # helpers always pass the stone as the LAST skill_keys entry, so we mark it lv5;
        # all others are lv10.  level only scales the per-effect coefficient.
        skill_refs = [(h["main_skill"], 10)]
        if s.skill_keys:
            keys = list(s.skill_keys)
            for idx, (st, sid) in enumerate(keys):
                # last equipped key = the skill stone (lv5); the rest are modular (lv10)
                lvl = 5 if idx == len(keys) - 1 else 10
                skill_refs.append(({"st": st, "id": sid}, lvl))
        else:
            skill_refs += [(ref, 10) for ref in h.get("modular_default", [])]
        skills = []
        skill_level: dict = {}
        seen = set()
        for ref, lvl in skill_refs:
            kk = (int(ref["st"]), int(ref["id"]))
            if kk in seen:
                continue          # a hero cannot equip the same skill twice
            seen.add(kk)
            sk = g.skill(*kk)
            if sk:
                skills.append(sk)
                skill_level[kk] = lvl
        equipped_keys = [(int(sk["st"]), int(sk["id"])) for sk in skills]

        # --- relic (hero's OWN only), rune (1, best matching an equipped skill),
        #     skill-awaken (per equipped skill): trigger-prob & coefficient bonuses ---
        skill_trigger_bonus: dict = {}
        skill_coef_bonus: dict = {}
        real_dmg_bonus: dict = {}
        rel = g.relic_bonus_for_hero(s.hero_id)   # hero's OWN relic only
        relic_dmg_dealt = 0.0
        if rel:
            rk, rkind, rv = rel["key"], rel["kind"], rel["value"]
            if rkind == "trigger":
                skill_trigger_bonus[rk] = skill_trigger_bonus.get(rk, 0.0) + rv
            elif rkind == "coef":
                if rv:
                    skill_coef_bonus[rk] = skill_coef_bonus.get(rk, 0.0) + rv
                # Patra-style relic also carries a Real DMG Base add (token id 41)
                rdb = rel.get("real_dmg")
                if rdb:
                    real_dmg_bonus[rk] = real_dmg_bonus.get(rk, 0.0) + rdb
            elif rkind == "dmg_dealt":
                relic_dmg_dealt += rv
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
            if aw["kind"] == "trigger":
                skill_trigger_bonus[kk] = skill_trigger_bonus.get(kk, 0.0) + aw["value"]
            elif aw["kind"] == "coef":
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
            troops_max=troops, soldier=soldier, skills=skills, skill_level=skill_level,
            skill_trigger_bonus=skill_trigger_bonus, channel_trigger=channel_trigger,
            skill_coef_bonus=skill_coef_bonus, real_dmg_bonus=real_dmg_bonus,
            gear_dmg_dealt=gb.get("dmg_dealt", 0.0) + relic_dmg_dealt,
            gear_dmg_taken=gb.get("dmg_taken", 0.0),
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
    """Army-size & attrition factor: a unit hits harder with more live troops.

    Spec B: the linear (exponent 1.0) factor over-penalizes a wounded army; the pursuit
    log implies a SUB-linear (~sqrt) attacker-attrition curve (SusaMaki R1 5441@54k ->
    R3 3363@21.5k => exponent ~0.52).  At FULL troops the factor is 1.0 regardless of the
    exponent, so the clean full-troop calibration anchors are unaffected; only wounded
    attackers change.  troop_scale_exp is a LABELED ASSUMPTION fit to that decay (~0.5)."""
    frac = unit.health / max(1.0, cfg.troop_scale_ref)
    if frac <= 0.0:
        return 0.0
    return frac ** cfg.troop_scale_exp


def def_mitigation(defender: CombatUnit, channel: str, cfg: ModelConfig) -> float:
    """Multiplicative DEF mitigation in (0,1].  Real/assault/splash ignore DEF."""
    if channel in ("real", "assault", "splash"):
        return 1.0
    def_eff = defender.eff_stat("def") * cfg.hero_def_weight
    return cfg.def_ref / (cfg.def_ref + def_eff)


def dot_tick(caster: CombatUnit, defender: CombatUnit, coef: float,
             cfg: ModelConfig) -> float:
    """One Burn/Curse tick.  Scales with the CASTER (DES via offence("dot") +
    a floored troop factor), LINEAR in the printed coefficient.  NO DEF mitigation
    (spec D / digest dot-sustain: the server DoT spec has no DEF term and the log shows
    no DEF trend -- high-DEF Thiel is not hit less per caster-troop than low-DEF Nicole;
    `defender` is kept only for signature compatibility).  Calibrated to
    calibration_2_dot.md (see ModelConfig).  All server-side -> ASSUMPTION."""
    off = offence(caster, "dot", cfg)
    troop_factor = cfg.dot_troop_floor + (1.0 - cfg.dot_troop_floor) * troop_scale(caster, cfg)
    return max(0.0, coef * off * troop_factor * cfg.dot_global)


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
                    alive=True, statuses={}, attr_mods={}, _charged={},
                    stat_kills=0.0, stat_heal=0.0, stat_slight=0.0, stat_severe=0.0,
                    stat_death=0.0, stat_skill_dmg=0.0, stat_normal_dmg=0.0, skills_used=0)
        out.append(c)
    return out
