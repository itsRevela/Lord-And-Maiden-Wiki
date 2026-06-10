"""3v3 match resolver for the Lord & Maiden simulator (reworked to the in-game log).

A MATCH is a sequence of 8-round BATTLES (bouts).  Each battle runs three phase
groups, exactly as the transcribed battle log ("Rosetta Stone") shows:

  1. Passive Exertion  -- register passive skills (Counterattack, Reactive Block,
     Tactical Burst, Purification, Assault carriers, ...).
  2. Pre-War Preparation -- fire ALL Strategic skills + apply their shields, attribute
     buffs/debuffs, prepared CC, heal-over-time and dmg-amp BEFORE round 1.
  3. Rounds 1..8 -- the actual exchanges, with prepared-CC re-rolls, reactions/procs
     (Assault pursuit, Counterattack, Reactive Block, Tactical Burst, Purification),
     Aid/Taunt targeting, inter-round wound worsening and healing.

Undecided after 8 rounds -> Stalemate -> immediate rematch with Health carried over
AND a stacking "All Hero DMG Dealt +33% per prior stalemate" buff, until a commander
is wiped.

Casualties use three buckets (Health / SlightWound / SevereWound+Death); damage
removes Health (a small part straight to Severe/Death), between rounds a share of
Slight worsens to Severe/Death, and healing moves Slight back to Health (blocked by
Heal Ban).  Server-side unknowns are ModelConfig knobs, never hidden literals.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import data as datamod
from . import model as modelmod
from .model import CombatUnit, ModelConfig


# ---- buff-id families (from data/sim status + testcase_entities) -----------
CONTROL_STUN = {114, 83}            # cannot act
CONTROL_SILENCE = {116}             # active silence THIS round (116 direct or re-rolled)
CONTROL_DISARM = {115, 84}          # no normal attack
CONTROL_CHAOS = {117, 86}           # attacks random side
PREPARED_SILENCE = {85}             # re-rolls each round
HEAL_BAN = {119}
TAUNT = {118}
ASSIST = {120}
ASSAULT = {70}                      # bearer adds a flat Real-DMG pursuit per attack
COUNTER = {81}                      # 概率反击 (Reactive Block / Counterattack)
DMG_TAKEN_REDUCED = {8}
DMG_TAKEN_INCREASED = {7}
DMG_DEALT_INCREASED = {5}
DMG_DEALT_DECREASED = {6}
TACTICAL_DMG_DEALT = {31}
SELF_HEAL = {107}
PURIFICATION = {139}
SUPERCONDUCTING = {125}             # Tactical Burst marker
PROVOKED = {200}                    # synthetic id: a unit forced to attack its taunter
STALEMATE_BUFF = {201}             # synthetic id: +33% All-Hero DMG Dealt per stalemate
REACTIVE_BLOCK_HIT = {202}          # synthetic transient: this hit gets -59.20% taken

# attribute-mod action ids -> hero stat key (and whether it's a reduction)
ATTR_INCREASE = {9: "atk", 10: "def", 11: "ruin", 12: "speed", 13: "all"}
ATTR_REDUCE = {21: "atk", 22: "def", 23: "ruin", 24: "speed", 28: "all"}

PURIFIABLE = CONTROL_STUN | CONTROL_SILENCE | CONTROL_DISARM | CONTROL_CHAOS | TAUNT | PROVOKED


@dataclass
class BattleResult:
    winner: int                       # 0 = player side, 1 = enemy side, -1 = draw/impasse
    rounds_fought: int                # rounds in the FIRST 8-round bout
    bouts_fought: int = 1             # number of 8-round bouts until decided
    player_damage_by_round: list = field(default_factory=list)
    enemy_damage_by_round: list = field(default_factory=list)
    total_player_damage: float = 0.0  # across all bouts
    total_enemy_damage: float = 0.0
    player_units_alive: int = 0
    enemy_units_alive: int = 0
    player_troops_frac_remaining: float = 0.0
    enemy_troops_frac_remaining: float = 0.0
    stalemates: int = 0
    bout_outcomes: list = field(default_factory=list)   # "stalemate"/"win"/"loss" per bout

    def window_damage(self, which: str = "player"):
        """Sum of damage in early(1-2)/mid(3-4)/late(5+)/all windows."""
        dmg = self.player_damage_by_round if which == "player" else self.enemy_damage_by_round
        n = len(dmg)
        early = sum(dmg[0:2])
        mid = sum(dmg[2:4])
        late = sum(dmg[4:n])
        return {"early": early, "mid": mid, "late": late, "all": sum(dmg)}


class Battle:
    def __init__(self, g: datamod.GameData, cfg: ModelConfig,
                 player_units, enemy_units, rng: random.Random):
        self.g = g
        self.cfg = cfg
        self.rng = rng
        self.sides = {0: list(player_units), 1: list(enemy_units)}
        self.round_dmg = {0: [0.0] * g.round_count, 1: [0.0] * g.round_count}
        self.stalemates = 0           # prior stalemate count (escalation stacks)

    # ---- helpers -------------------------------------------------------
    def _opp(self, side: int) -> int:
        return 1 - side

    def _alive(self, side: int):
        return [u for u in self.sides[side] if u.alive]

    def _commander(self, side: int):
        for u in self.sides[side]:
            if u.is_commander:
                return u
        return None

    def _has(self, u: CombatUnit, ids) -> bool:
        return any(bid in u.statuses and u.statuses[bid]["rounds"] != 0 for bid in ids)

    def _status_value(self, u: CombatUnit, ids) -> float:
        """Sum of all active values for the given buff-id family (stacks summed)."""
        tot = 0.0
        for bid in ids:
            st = u.statuses.get(bid)
            if st and st["rounds"] != 0:
                tot += st.get("value", 0.0) * st.get("stacks", 1)
        return tot

    def _apply_status(self, u: CombatUnit, buff_id, rounds: int, value: float = 0.0,
                      stack: bool = False, channel: str = None):
        if buff_id is None:
            return
        buff_id = int(buff_id)
        cur = u.statuses.get(buff_id)
        if cur:
            cur["rounds"] = max(cur["rounds"], rounds)
            if stack:
                cur["stacks"] = cur.get("stacks", 1) + 1
            cur["value"] = max(cur.get("value", 0.0), value)
            if channel:
                cur["ch"] = channel
        else:
            u.statuses[buff_id] = {"rounds": rounds, "value": value,
                                   "stacks": 1, "ch": channel}

    def _add_attr(self, u: CombatUnit, stat: str, add: float, locked: bool = False):
        """Apply an in-battle attribute modifier.  'cannot be replaced' = locked."""
        keys = ["atk", "def", "ruin", "speed"] if stat == "all" else [stat]
        for k in keys:
            cur = u.attr_mods.get(k)
            if cur and cur.get("locked") and not locked:
                continue                      # a locked stronger mod blocks replacement
            base = cur.get("add", 0.0) if cur else 0.0
            u.attr_mods[k] = {"add": base + add, "locked": locked or (cur and cur.get("locked", False))}

    # ---- passive exertion ----------------------------------------------
    def _passive_exertion(self):
        for side in (0, 1):
            for u in self.sides[side]:
                if not u.alive:
                    continue
                for sk in u.skills:
                    if int(sk["st"]) != 3:        # 3 = Passive
                        continue
                    for eff in sk.get("effects", []):
                        at = eff.get("actionType")
                        val = float(eff.get("coefficient") or eff.get("flatMagnitude") or 0.0)
                        if at in (81,):              # counterattack / reactive block
                            self._apply_status(u, 81, rounds=99, value=val or 0.84)
                        elif at == 8:                # reactive block dmg-taken-reduced (chance)
                            self._apply_status(u, 8202, rounds=99,
                                               value=self.cfg.reactive_block_reduction)
                        elif at == 125:              # tactical burst marker (superconducting)
                            self._apply_status(u, 125, rounds=99, value=float(sk.get("maxedValue") or 0.4))
                        elif at == 139:              # purification (per-round cleanse chance)
                            self._apply_status(u, 139, rounds=99, value=float(sk.get("maxedValue") or 0.4))

    # ---- pre-war preparation (fire all Strategic skills before round 1) ----
    def _pre_war_preparation(self):
        # ordered by Speed desc so deterministic-ish; server order is UNKNOWN.
        order = sorted([u for s in (0, 1) for u in self._alive(s)],
                       key=lambda u: (-u.eff_stat("speed"), self.rng.random()))
        for u in order:
            for sk in u.skills:
                if int(sk["st"]) != 1:            # 1 = Strategic
                    continue
                self._fire_strategic(u, sk)
        # stalemate escalation buff carried into this bout
        if self.stalemates > 0:
            inc = self.cfg.stalemate_dmg_dealt_per_stack * self.stalemates
            for s in (0, 1):
                for u in self._alive(s):
                    self._apply_status(u, 201, rounds=99, value=inc)

    def _fire_strategic(self, caster: CombatUnit, sk):
        for eff in sk.get("effects", []):
            at = eff.get("actionType")
            tcat = eff.get("targetCategoryName") or ""
            tcount = eff.get("targetCount") or 1
            coef = float(eff.get("coefficient") or 0.0)
            flat = float(eff.get("flatMagnitude") or 0.0)
            chance = float(eff.get("triggerChance") or 1.0)
            dur = self._eff_duration(eff, default=3)
            # protective HoTs (Purification, Self-Heal, DMG-Taken-Reduced) prefer the
            # commander/carry, which is how a real player allocates them.
            if at in (139, 107) and "enemy" not in tcat.lower():
                targets = self._pick_ally_priority(caster, tcount)
            else:
                targets = self._pick_targets(caster, tcat, tcount)
            for tgt in targets:
                self._apply_prep_effect(caster, tgt, at, coef, flat, chance, dur)

    def _apply_prep_effect(self, caster, tgt, at, coef, flat, chance, dur):
        # attribute increase/reduce (resolved to an absolute add via Affected-by)
        if at in ATTR_INCREASE or at in ATTR_REDUCE:
            stat = ATTR_INCREASE.get(at) or ATTR_REDUCE.get(at)
            sign = 1.0 if at in ATTR_INCREASE else -1.0
            # add scales off the source's relevant attribute (Affected-by hint);
            # magnitude resolved through affected_per_points. ASSUMPTION shape.
            mag = (coef * self._affected_scale(caster) + flat) * 6.0
            self._add_attr(tgt, stat, sign * mag, locked=False)
            return
        if at == 8:                       # DMG Taken Reduced (shield-type)
            self._apply_status(tgt, 8, rounds=dur,
                               value=self._affected_pct(caster, coef) + self._flat_pct(flat))
            return
        if at == 7:                       # DMG Taken Increased
            self._apply_status(tgt, 7, rounds=dur,
                               value=self._affected_pct(caster, coef) + self._flat_pct(flat))
            return
        if at == 5:                       # DMG Dealt Increased
            self._apply_status(tgt, 5, rounds=dur,
                               value=self._affected_pct(caster, coef) + self._flat_pct(flat))
            return
        if at == 31:                      # Tactical Skill DMG Dealt Increased
            self._apply_status(tgt, 31, rounds=dur,
                               value=self._affected_pct(caster, coef) + self._flat_pct(flat))
            return
        if at == 107:                     # Self-Heal (HoT) -> mark with heal coef
            self._apply_status(tgt, 107, rounds=dur, value=coef or 0.7)
            return
        if at == 85:                      # prepared Silence -> per-round re-roll
            self._apply_status(tgt, 85, rounds=dur, value=chance)
            return
        if at == 119:                     # Heal Ban
            self._apply_status(tgt, 119, rounds=dur, value=1.0)
            return
        if at == 115:                     # Disarm (e.g. Gray World self-disarm)
            self._apply_status(tgt, 115, rounds=dur, value=1.0)
            return
        if at == 120:                     # Assist / Protect (Star Shield)
            self._apply_status(tgt, 120, rounds=dur, value=1.0)
            return
        if at == 70:                      # Assault carrier (rare in prep)
            self._apply_status(caster, 70, rounds=dur,
                               value=flat or float(coef) or 22.0)
            return
        if at == 139:                     # Purification (HoT cleanse, e.g. Devout)
            self._apply_status(tgt, 139, rounds=dur, value=max(chance, 0.4))
            return

    # ---- scaling helpers (Affected-by-X) -------------------------------
    def _affected_scale(self, u: CombatUnit) -> float:
        """A magnitude unit derived from the source's stat pool / affected_per_points."""
        return max(1.0, (u.eff_stat("ruin") + u.eff_stat("def")) / self.cfg.affected_per_points)

    def _affected_pct(self, u: CombatUnit, coef: float) -> float:
        """Percent value (as fraction) for an 'Affected By X' buff, e.g. Star Shield."""
        if coef <= 0:
            return 0.0
        # coef * (1 + stat/affected_per_points) -- bigger DEF/DES -> bigger %
        scale = 1.0 + (u.eff_stat("def") + u.eff_stat("ruin")) / (2 * self.cfg.affected_per_points)
        return coef * scale * 6.0

    def _flat_pct(self, flat: float) -> float:
        return flat                       # already a fraction-style flat add

    def _eff_duration(self, eff, default: int = 2) -> int:
        rt = eff.get("rawTokens")
        if rt and len(rt) > 9:
            try:
                d = int(float(rt[9]))
                if d > 0:
                    return d
            except (ValueError, TypeError):
                pass
        d = eff.get("duration")
        try:
            d = int(d)
            if d > 0:
                return d
        except (ValueError, TypeError):
            pass
        return default

    # ---- damage multipliers --------------------------------------------
    def _dmg_dealt_mult(self, u: CombatUnit, channel: str) -> float:
        m = 1.0
        m += self._status_value(u, DMG_DEALT_INCREASED)
        m -= self._status_value(u, DMG_DEALT_DECREASED)
        m += self._status_value(u, STALEMATE_BUFF)
        m += u.gear_dmg_dealt
        if channel == "tactical":
            m += self._status_value(u, TACTICAL_DMG_DEALT)
        return max(0.05, m)

    def _dmg_taken_mult(self, u: CombatUnit, channel: str, reactive_hit: bool = False) -> float:
        m = 1.0
        m += self._status_value(u, DMG_TAKEN_INCREASED)
        m -= self._status_value(u, DMG_TAKEN_REDUCED)
        m -= u.gear_dmg_taken
        if reactive_hit:
            m -= self.cfg.reactive_block_reduction
        return max(0.02, m)

    # ---- damage application (casualty buckets) -------------------------
    def _deal(self, attacker: CombatUnit, defender: CombatUnit, coef: float,
              channel: str, round_idx: int, is_skill: bool, real_base: float = 0.0):
        if not defender.alive:
            return 0.0
        cfg = self.cfg
        if channel in ("real", "assault"):
            # flat Real DMG, DEF-independent.  Loss = RealBase * scale * troop_scale,
            # amplified only by dmg-dealt (NOT mitigated by shields/DEF).
            raw = real_base * cfg.real_dmg_scale * (0.5 + 0.5 * modelmod.troop_scale(attacker, cfg))
            dealt = raw * self._dmg_dealt_mult(attacker, channel)
        else:
            raw = (coef * modelmod.offence(attacker, channel, cfg)
                   * modelmod.troop_scale(attacker, cfg) * cfg.damage_global)
            restraint = modelmod.restraint_mult(self.g, attacker, defender, cfg)
            mitig = modelmod.def_mitigation(defender, channel, cfg)
            reactive = False
            if channel == "normal" and self._has(defender, COUNTER) \
                    and self.rng.random() < 0.30:
                reactive = True            # Reactive Block proc on this hit
            dealt = (raw * mitig * restraint
                     * self._dmg_dealt_mult(attacker, channel)
                     * self._dmg_taken_mult(defender, channel, reactive_hit=reactive))
        dealt = max(0.0, dealt)
        applied = self._apply_casualties(defender, dealt)
        # tracking
        attacker.stat_kills += applied
        if is_skill:
            attacker.stat_skill_dmg += applied
        elif channel == "normal":
            attacker.stat_normal_dmg += applied
        self.round_dmg[attacker.side][round_idx] += applied
        return applied

    def _apply_casualties(self, defender: CombatUnit, dealt: float):
        """Remove `dealt` from Health.  A small part goes straight to Severe/Death
        (permanent, lowers max); the rest becomes Slight (recoverable)."""
        dealt = min(dealt, defender.health)
        if dealt <= 0:
            return 0.0
        severe = dealt * self.cfg.direct_severe_frac
        slight = dealt - severe
        defender.health -= dealt
        defender.slight += slight
        defender.severe_death += severe
        if defender.health <= 1e-6:
            defender.health = 0.0
            defender.alive = False
        return dealt

    def _heal(self, caster: CombatUnit, target: CombatUnit, coef: float):
        """Restore Slight -> Health.  Blocked by Heal Ban; 0 when no Slight."""
        if not target.alive or self._has(target, HEAL_BAN):
            return
        if target.slight <= 0:
            return
        amount = coef * self.cfg.heal_scale * target.slight
        amount = min(amount, target.slight)
        target.slight -= amount
        target.health += amount
        caster.stat_heal += amount

    # ---- targeting -----------------------------------------------------
    def _pick_target(self, attacker: CombatUnit):
        """Normal-attack target: Provoked/Taunt overrides, then Assist redirect,
        then 20/40/40 striker weighting."""
        foes = self._alive(self._opp(attacker.side))
        if not foes:
            return None
        # Provoked: forced to attack the taunter (stored on the provoked unit)
        prov = attacker.statuses.get(200)
        if prov and prov["rounds"] != 0:
            tid = prov.get("value")
            for f in foes:
                if f.hero_id == tid and f.alive:
                    return f
        # 20/40/40 weighting
        weights = [0.2 if f.is_commander else 0.4 for f in foes]
        tot = sum(weights) or 1.0
        r = self.rng.random() * tot
        acc = 0.0
        chosen = foes[-1]
        for f, w in zip(foes, weights):
            acc += w
            if r <= acc:
                chosen = f
                break
        # Assist redirect: if a striker is targeted and an ally is in Aid state,
        # the aider soaks the hit (Star Shield's Assist).
        if not chosen.is_commander:
            aiders = [f for f in foes if self._has(f, ASSIST) and f is not chosen]
            if aiders:
                return self.rng.choice(aiders)
        return chosen

    def _pick_ally_priority(self, caster: CombatUnit, count: int):
        """Ally targets for protective buffs: commander first, then highest-offence
        (the carry), then the rest -- a sensible player allocation. ASSUMPTION."""
        allies = self._alive(caster.side)
        if not allies:
            return []
        allies = sorted(allies, key=lambda u: (not u.is_commander,
                                               -u.eff_stat("atk")))
        count = max(1, min(count or 1, len(allies)))
        return allies[:count]

    def _pick_attack_targets(self, caster: CombatUnit, category: str, count: int):
        """Damaging-skill targeting. The log shows damage is SPREAD, not piled on the
        squishiest: in Battle 1 the shielded enemy commander still took ~33k (much via
        Assault, which bypasses her shield) while a tankier striker survived. So we
        weight toward squishier targets but give every enemy a real floor share
        (weighted sampling WITHOUT replacement). A purely "focus-squishiest" rule
        under-damages the commander and wrongly needs an extra bout to wipe her.
        ASSUMPTION shape; commander/inherit categories fall back to the normal picker."""
        cat = (category or "").lower()
        if "commander" in cat or "inherit" in cat or cat == "":
            return self._pick_targets(caster, category, count)
        pool = self._alive(self._opp(caster.side))
        if not pool:
            return []
        # squishiness weight = dmg_taken_mult * mitigation, + a floor so the
        # heavily-shielded commander is never fully skipped (she still eats Assault),
        # but skills still lean toward the killable strikers. Weighted sampling
        # without replacement (Efraimidis-Spirakis).
        def weight(d):
            w = self._dmg_taken_mult(d, "tactical") * modelmod.def_mitigation(d, "tactical", self.cfg)
            return max(w, 0.0) + 0.35      # ASSUMPTION floor share for any enemy
        keyed = sorted(pool, key=lambda d: self.rng.random() ** (1.0 / weight(d)), reverse=True)
        count = max(1, min(count or 1, len(keyed)))
        return keyed[:count]

    def _pick_targets(self, caster: CombatUnit, category: str, count: int):
        cat = (category or "").lower()
        if "enemy commander" in cat or "commander" in cat:
            pool = [u for u in self._alive(self._opp(caster.side)) if u.is_commander] \
                   or self._alive(self._opp(caster.side))
        elif "enemy" in cat or cat in ("2",):
            pool = self._alive(self._opp(caster.side))
        elif "self" in cat or "own" in cat:
            pool = [caster] if caster.alive else []
        elif "assist" in cat or "protect" in cat:
            pool = [u for u in self._alive(caster.side) if u is not caster] or self._alive(caster.side)
        else:                              # our troops / inherit
            pool = self._alive(caster.side)
        if not pool:
            return []
        count = max(1, min(count or 1, len(pool)))
        return self.rng.sample(pool, count)

    # ---- skill firing (tactical/pursuit, in-round) ---------------------
    def _channel_for(self, sk) -> str:
        return {2: "tactical", 4: "pursuit"}.get(int(sk["st"]), "tactical")

    def _skill_real_base(self, caster: CombatUnit, sk, key) -> float:
        """Ghost-Bone-style Assault: the skill grants an Assault buff with a Real DMG
        base (effect 70).  Returns the flat base (+ relic Real-DMG bonus) or 0."""
        base = 0.0
        for eff in sk.get("effects", []):
            if eff.get("actionType") == 70:
                base = float(eff.get("flatMagnitude") or 0.0)
        if base:
            base += caster.real_dmg_bonus.get(key, 0.0)
        return base

    def _fire_skill(self, caster: CombatUnit, sk, round_idx: int):
        chan = self._channel_for(sk)
        key = (int(sk["st"]), int(sk["id"]))
        coef = float(sk.get("maxedValue") or 0.0) + caster.skill_coef_bonus.get(key, 0.0)
        real_base = self._skill_real_base(caster, sk, key)
        caster.skills_used += 1
        for eff in sk.get("effects", []):
            at = eff.get("actionType")
            if not eff.get("isAction"):
                continue                     # buffs/debuffs handled below or as state
            tcat = eff.get("targetCategoryName") or ""
            tcount = eff.get("targetCount") or 1
            ecoef = float(eff.get("coefficient") or 0.0)
            # the skill's maxed coefficient (+ relic/awaken) already represents the
            # leveled damage power; fall back to the per-effect coefficient only when
            # the skill has no maxedValue.  (calibration: maxedValue is the per-hit coef)
            use_coef = coef if coef > 0 else ecoef
            if at == 101:                    # ATK enemy
                for tgt in self._pick_attack_targets(caster, tcat or "enemy", tcount):
                    self._deal(caster, tgt, use_coef, chan, round_idx, is_skill=True)
                    if real_base:            # Assault pursuit on every attack
                        self._deal(caster, tgt, 0.0, "real", round_idx,
                                   is_skill=False, real_base=real_base)
                    self._maybe_counter(caster, tgt, round_idx)
            elif at == 102:                  # heal allies
                for tgt in self._pick_targets(caster, tcat or "our", tcount):
                    self._heal(caster, tgt, ecoef or coef or 0.6)
            elif at in (121, 122):           # purify own / dispel enemy
                for tgt in self._pick_targets(caster, tcat or "our", tcount):
                    self._cleanse(tgt)
        # the skill's inflicted status (Buff/Dbuff field) -> apply to action target
        self._apply_skill_statuses(caster, sk)

    def _apply_skill_statuses(self, caster: CombatUnit, sk):
        """Apply the non-action buff/debuff effects of a tactical skill (Disarm,
        Stun, Heal Ban, Silence, Taunt, attribute mods)."""
        for eff in sk.get("effects", []):
            if eff.get("isAction"):
                continue
            at = eff.get("actionType")
            tcat = eff.get("targetCategoryName") or ""
            tcount = eff.get("targetCount") or 1
            chance = float(eff.get("triggerChance") or 1.0)
            dur = self._eff_duration(eff, default=2)
            if at == 70:                      # Assault buff on self (handled at cast)
                self._apply_status(caster, 70, rounds=dur,
                                   value=float(eff.get("flatMagnitude") or 22.0))
                continue
            # resolve targets: "inherit action target" -> an enemy we just hit
            if "inherit" in tcat.lower() or tcat == "":
                pool = self._alive(self._opp(caster.side))
                targets = self.rng.sample(pool, min(tcount, len(pool))) if pool else []
            else:
                targets = self._pick_targets(caster, tcat, tcount)
            for tgt in targets:
                if at == 115:                 # Disarm
                    if self.rng.random() < chance:
                        self._apply_status(tgt, 115, rounds=dur, value=1.0)
                elif at == 114:               # Stun
                    if self.rng.random() < chance:
                        self._apply_status(tgt, 114, rounds=dur, value=1.0)
                elif at == 116:               # Silence (direct)
                    if self.rng.random() < chance:
                        self._apply_status(tgt, 116, rounds=dur, value=1.0)
                elif at == 119:               # Heal Ban
                    self._apply_status(tgt, 119, rounds=dur, value=1.0)
                elif at == 118:               # Taunts -> mark target Provoked toward caster
                    self._apply_status(tgt, 118, rounds=dur, value=1.0)
                    self._apply_status(tgt, 200, rounds=dur, value=caster.hero_id)
                elif at == 8:                 # DMG Taken Reduced (e.g. Knight Creed)
                    self._apply_status(tgt, 8, rounds=dur, value=self._affected_pct(caster, float(eff.get("coefficient") or 0.0)))

    def _maybe_counter(self, attacker: CombatUnit, defender: CombatUnit, round_idx: int):
        """If the defender carries Counterattack, it strikes back at 0.84x a normal."""
        pass    # counters fire only on NORMAL attacks (see _unit_turn); skills don't provoke

    def _cleanse(self, unit: CombatUnit):
        for bid in list(unit.statuses.keys()):
            if bid in PURIFIABLE:
                unit.statuses[bid]["rounds"] = 0

    # ---- per-unit turn -------------------------------------------------
    def _trigger_prob(self, sk, unit) -> float:
        p = sk.get("skillP")
        if p is None:
            p = sk.get("triggerProbAtMax", 1.0)
        try:
            p = float(p)
        except (ValueError, TypeError):
            p = 1.0
        key = (int(sk["st"]), int(sk["id"]))
        p += unit.skill_trigger_bonus.get(key, 0.0)
        p += unit.channel_trigger.get(self._channel_for(sk), 0.0)
        return max(0.0, min(1.0, p))

    def _unit_turn(self, u: CombatUnit, round_idx: int, round_no: int):
        if not u.alive:
            return
        # prepared CC re-rolls happen at round start (see _round_start_cc)
        if self._has(u, CONTROL_STUN):
            return                                   # stunned: cannot act
        # Tactical skills, unless silenced
        if not self._has(u, CONTROL_SILENCE):
            burst_used = False                       # Tactical Burst recasts once/turn
            for sk in u.skills:
                if int(sk["st"]) != 2:
                    continue
                if round_no < self._skill_from_round(sk):
                    continue
                if self.rng.random() < self._trigger_prob(sk, u):
                    self._fire_skill(u, sk, round_idx)
                    # Tactical Burst: chance to recast ONE tactical per turn
                    if not burst_used and self._has(u, SUPERCONDUCTING):
                        burst = u.statuses[125].get("value", 0.4)
                        if self.rng.random() < burst:
                            self._fire_skill(u, sk, round_idx)
                            burst_used = True
        # Normal attack, unless disarmed
        did_normal = False
        if not self._has(u, CONTROL_DISARM):
            tgt = self._pick_target(u)
            if tgt:
                self._deal(u, tgt, self.cfg.normal_attack_coef, "normal", round_idx, is_skill=False)
                did_normal = True
                # Counterattack: target strikes back at 0.84x a normal
                if tgt.alive and self._has(tgt, COUNTER):
                    self._deal(tgt, u, self.cfg.normal_attack_coef * self.cfg.counter_coef,
                               "normal", round_idx, is_skill=False)
                # Assault pursuit also fires on the bearer's normal attack
                if self._has(u, ASSAULT):
                    rb = u.statuses[70].get("value", 22.0)
                    self._deal(u, tgt, 0.0, "real", round_idx, is_skill=False, real_base=rb)
        # Pursuit skills (after normal attack), probability
        if did_normal:
            for sk in u.skills:
                if int(sk["st"]) == 4 and round_no >= self._skill_from_round(sk):
                    if self.rng.random() < self._trigger_prob(sk, u):
                        self._fire_skill(u, sk, round_idx)

    def _skill_from_round(self, sk) -> int:
        for eff in sk.get("effects", []):
            fr = eff.get("fromRound")
            if fr:
                try:
                    return int(fr)
                except (ValueError, TypeError):
                    pass
        return 1

    # ---- round-start phases --------------------------------------------
    def _round_start(self, round_no: int):
        for side in (0, 1):
            for u in self._alive(side):
                # 1. prepared-Silence/CC re-roll (per round, BEFORE purification so a
                #    purify can immediately cleanse a freshly-rolled control)
                self._reroll_prepared_cc(u)
                # 2. Purification re-roll (cleanse one debuff incl. the fresh silence)
                pur = u.statuses.get(139)
                if pur and pur["rounds"] != 0 and self.rng.random() < pur.get("value", 0.4):
                    self._cleanse_one(u)
                # 3. Self-Heal HoT (Field Therapy) -- restores Slight->Health
                heal = u.statuses.get(107)
                if heal and heal["rounds"] != 0:
                    self._heal(u, u, heal.get("value", 0.7))
                # 4. worsen a share of Slight -> Severe/Death (lowers max)
                if u.slight > 0:
                    worsen = u.slight * self.cfg.slight_worsen_frac
                    u.slight -= worsen
                    u.severe_death += worsen

    def _cleanse_one(self, unit: CombatUnit):
        for bid in list(unit.statuses.keys()):
            if bid in PURIFIABLE and unit.statuses[bid]["rounds"] != 0:
                unit.statuses[bid]["rounds"] = 0
                return

    def _reroll_prepared_cc(self, unit: CombatUnit):
        st = unit.statuses.get(85)
        if not st or st["rounds"] == 0:
            return
        # Stated bases are 40% (allies) / 60% (enemies); resist + purification net
        # the EFFECTIVE per-round activation down (ModelConfig knobs).  Side 0 (player)
        # uses the ally base, side 1 (enemy) the enemy base.
        base = (self.cfg.prepared_cc_enemy_base if unit.side == 1
                else self.cfg.prepared_cc_ally_base)
        # active this round only if the re-roll succeeds; modelled by toggling a
        # transient silence (116) for this round.
        if self.rng.random() < base:
            self._apply_status(unit, 116, rounds=1, value=1.0)

    def _tick_statuses(self, side: int):
        for u in self.sides[side]:
            for bid, st in list(u.statuses.items()):
                if 0 < st["rounds"] < 90:
                    st["rounds"] -= 1
        # attribute mods do not expire mid-bout in this model (prep buffs last the
        # first 3 rounds in-game; we keep them for the bout -- ASSUMPTION).

    # ---- one 8-round bout ----------------------------------------------
    def _run_bout(self):
        rounds = self.g.round_count
        self.round_dmg = {0: [0.0] * rounds, 1: [0.0] * rounds}
        self._passive_exertion()
        self._pre_war_preparation()
        decided = False
        ri = 0
        for ri in range(rounds):
            round_no = ri + 1
            self._round_start(round_no)
            order = sorted(
                [u for s in (0, 1) for u in self._alive(s)],
                key=lambda u: (-u.eff_stat("speed"), self.rng.random()),
            )
            for u in order:
                if u.alive:
                    self._unit_turn(u, ri, round_no)
            self._tick_statuses(0)
            self._tick_statuses(1)
            if self._is_over():
                decided = True
                break
        return ri + 1, decided, self.round_dmg[0], self.round_dmg[1]

    def _reset_for_rematch(self):
        """Carry Health over; reset transient state for a fresh engagement.
        Slight is partially recovered between bouts (rest period) -- ASSUMPTION:
        Slight folds back into Health (the log shows units re-enter at their B1-end
        Health, not max, so we keep severe_death permanent and zero Slight)."""
        for side in (0, 1):
            for u in self.sides[side]:
                u.statuses = {}
                u.attr_mods = {}
                u.slight = 0.0
                if u.health <= 0:
                    u.alive = False

    # ---- main loop -----------------------------------------------------
    def run(self) -> BattleResult:
        first_rounds = 0
        first_d0 = first_d1 = None
        total0 = total1 = 0.0
        bouts = 0
        outcomes = []
        while bouts < self.cfg.max_bouts:
            bouts += 1
            if bouts > 1:
                self._reset_for_rematch()
                if not (self._alive(0) and self._alive(1)):
                    break
            rf, decided, d0, d1 = self._run_bout()
            if bouts == 1:
                first_rounds, first_d0, first_d1 = rf, list(d0), list(d1)
            total0 += sum(d0)
            total1 += sum(d1)
            if decided:
                outcomes.append("decided")
                break
            # undecided after 8 rounds -> Stalemate -> rematch with +33% per stalemate
            outcomes.append("stalemate")
            self.stalemates += 1
            if (sum(d0) + sum(d1)) < self.cfg.bout_stalemate_frac * self._total_troops_max():
                break        # truly nothing happening -> stop as draw
        return self._result(first_rounds, bouts, first_d0 or [], first_d1 or [],
                            total0, total1, outcomes)

    def _total_troops_max(self) -> float:
        return sum(u.troops_max for s in (0, 1) for u in self.sides[s]) or 1.0

    def _is_over(self) -> bool:
        for side in (0, 1):
            cmd = self._commander(side)
            if cmd is None or not cmd.alive:
                return True
            if not self._alive(side):
                return True
        return False

    def _result(self, rounds_fought, bouts_fought, first_d0, first_d1,
                total0, total1, outcomes) -> BattleResult:
        def frac(side):
            us = self.sides[side]
            tot = sum(u.troops_max for u in us) or 1.0
            return sum(u.health for u in us) / tot
        p_alive = len(self._alive(0))
        e_alive = len(self._alive(1))
        pc, ec = self._commander(0), self._commander(1)
        if pc and not pc.alive and (not ec or ec.alive):
            winner = 1
        elif ec and not ec.alive and (not pc or pc.alive):
            winner = 0
        else:
            pf, ef = frac(0), frac(1)
            winner = 0 if pf > ef else (1 if ef > pf else -1)
        return BattleResult(
            winner=winner, rounds_fought=rounds_fought, bouts_fought=bouts_fought,
            player_damage_by_round=first_d0, enemy_damage_by_round=first_d1,
            total_player_damage=total0, total_enemy_damage=total1,
            player_units_alive=p_alive, enemy_units_alive=e_alive,
            player_troops_frac_remaining=frac(0),
            enemy_troops_frac_remaining=frac(1),
            stalemates=self.stalemates,
            bout_outcomes=outcomes,
        )
