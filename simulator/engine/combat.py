"""8-round 3v3 battle resolver for the Lord & Maiden simulator.

Implements the *stated* combat rules (round count, turn order by ATK Spd,
activation order Passive>Strategic>Tactical>Normal>Pursuit, restraint x0.75,
20/40/40 targeting, status-effect behaviours from status_effects.json) on top of
the transparent ``model.py`` damage model. Server-side unknowns are resolved by
``ModelConfig`` knobs, never by hidden literals.

A battle is one Monte-Carlo sample: skill triggers, target picks and procs are
drawn from a seeded RNG, so repeated samples form a distribution.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import data as datamod
from . import model as modelmod
from .model import CombatUnit, ModelConfig


# status categories we act on (from data/sim/status_effects.json)
def _cat(g: datamod.GameData, buff_id: int) -> str:
    b = g.buff(buff_id)
    return (b or {}).get("category", "other")


# which buff ids mean which control state
CONTROL_STUN = {114, 83}        # cannot act
CONTROL_SILENCE = {116, 85}     # no tactical skills
CONTROL_DISARM = {115, 84}      # no normal attack
CONTROL_CHAOS = {117, 86}       # attacks random side
TAUNT = {118}
HEAL_BAN = {119}
DOT_BUFFS = {108: "burn", 109: "curse"}
SHIELD = {73}


@dataclass
class BattleResult:
    winner: int                       # 0 = player side, 1 = enemy side, -1 = draw/impasse
    rounds_fought: int                # rounds in the FIRST 8-round bout
    bouts_fought: int = 1             # number of 8-round bouts until decided
    # damage by the player side per round of the FIRST bout (windows use this, as
    # the early/mid/late optimisation is about the canonical 8-round structure)
    player_damage_by_round: list = field(default_factory=list)
    enemy_damage_by_round: list = field(default_factory=list)
    total_player_damage: float = 0.0  # across all bouts
    total_enemy_damage: float = 0.0
    player_units_alive: int = 0
    enemy_units_alive: int = 0
    player_troops_frac_remaining: float = 0.0
    enemy_troops_frac_remaining: float = 0.0

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
        self.round_dmg = {0: [], 1: []}
        # pre-apply passive skills as permanent statuses
        for side in (0, 1):
            for u in self.sides[side]:
                self._apply_passives(u)

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

    def _apply_status(self, u: CombatUnit, buff_id: int, rounds: int, value: float = 0.0):
        if buff_id is None:
            return
        cur = u.statuses.get(buff_id)
        if cur:
            cur["rounds"] = max(cur["rounds"], rounds)
            cur["stacks"] = cur.get("stacks", 1) + 1
            cur["value"] = max(cur.get("value", 0.0), value)
        else:
            u.statuses[buff_id] = {"rounds": rounds, "value": value, "stacks": 1}

    def _apply_passives(self, u: CombatUnit):
        for sk in u.skills:
            if int(sk["st"]) != 3:    # 3 = Passive
                continue
            bid = (sk.get("buff") or {}).get("id")
            if bid:
                self._apply_status(u, int(bid), rounds=99, value=float(sk.get("maxedValue") or 0.0))

    # ---- buff-driven damage multipliers --------------------------------
    def _dmg_dealt_mult(self, u: CombatUnit, channel: str) -> float:
        m = 1.0
        # general DMG dealt up/down (5/6) + channel-specific (29 normal,31 tactical,33 pursuit)
        chan_up = {"normal": 29, "tactical": 31, "pursuit": 33}.get(channel)
        for bid, st in u.statuses.items():
            if st["rounds"] == 0:
                continue
            if bid == 5:
                m += st.get("value", 0.0) or 0.10
            elif bid == 6:
                m -= st.get("value", 0.0) or 0.10
            elif chan_up and bid == chan_up:
                m += st.get("value", 0.0) or 0.10
        return max(0.1, m)

    def _dmg_taken_mult(self, u: CombatUnit, channel: str) -> float:
        m = 1.0
        chan_take_down = {"normal": 36, "tactical": 38, "pursuit": 40}.get(channel)
        for bid, st in u.statuses.items():
            if st["rounds"] == 0:
                continue
            if bid == 7:               # DMG taken increased
                m += st.get("value", 0.0) or 0.10
            elif bid == 8:             # DMG taken reduced
                m -= st.get("value", 0.0) or 0.10
            elif chan_take_down and bid == chan_take_down:
                m -= st.get("value", 0.0) or 0.10
        return max(0.1, m)

    # ---- damage application -------------------------------------------
    def _deal(self, attacker: CombatUnit, defender: CombatUnit, coef: float,
              channel: str, round_idx: int):
        if not defender.alive or coef <= 0:
            return 0.0
        # shield absorbs one instance entirely
        if self._has(defender, SHIELD):
            sh = defender.statuses[73]
            if sh.get("stacks", 1) > 0:
                sh["stacks"] -= 1
                if sh["stacks"] <= 0:
                    sh["rounds"] = 0
                return 0.0
        restraint = modelmod.restraint_mult(self.g, attacker, defender, self.cfg)
        frac = modelmod.exchange_fraction(
            attacker, defender, coef, channel, restraint,
            self._dmg_dealt_mult(attacker, channel),
            self._dmg_taken_mult(defender, channel), self.cfg)
        dealt = frac * defender.hp_max          # express in HP (troop-pool) units
        defender.hp -= dealt
        if defender.hp <= 0:
            defender.hp = 0.0
            defender.alive = False
        self.round_dmg[attacker.side][round_idx] += dealt
        # lifesteal (blood sucking 106) on attacker
        if self._has(attacker, {106}):
            attacker.hp = min(attacker.hp_max, attacker.hp + dealt * 0.4)
        return dealt

    def _heal(self, caster: CombatUnit, target: CombatUnit, coef: float):
        if not target.alive or self._has(target, HEAL_BAN):
            return
        # heal scales off the caster's HP pool (Soldiers' HP) -- ASSUMPTION
        amount = coef * caster.hp_max * 0.10 * self.cfg.heal_hp_fraction_ref
        target.hp = min(target.hp_max, target.hp + amount)

    # ---- targeting -----------------------------------------------------
    def _pick_target(self, attacker: CombatUnit):
        foes = self._alive(self._opp(attacker.side))
        if not foes:
            return None
        # taunt override
        taunters = [f for f in foes if self._has(f, TAUNT)]
        if taunters:
            return self.rng.choice(taunters)
        # 20/40/40 weighting: commander 0.2, strikers 0.4 each (renormalised to alive)
        weights = [0.2 if f.is_commander else 0.4 for f in foes]
        tot = sum(weights)
        r = self.rng.random() * tot
        acc = 0.0
        for f, w in zip(foes, weights):
            acc += w
            if r <= acc:
                return f
        return foes[-1]

    def _pick_targets(self, caster: CombatUnit, category: str, count: int):
        if category in ("enemy",) or category == "Enemy Troops":
            pool = self._alive(self._opp(caster.side))
        elif "Commander" in (category or ""):
            pool = [u for u in self._alive(self._opp(caster.side)) if u.is_commander] or self._alive(self._opp(caster.side))
        else:  # our troops / self / assist
            pool = self._alive(caster.side)
        if not pool:
            return []
        count = max(1, min(count or 1, len(pool)))
        return self.rng.sample(pool, count)

    # ---- skill firing --------------------------------------------------
    def _channel_for(self, sk) -> str:
        return {2: "tactical", 4: "pursuit"}.get(int(sk["st"]), "tactical")

    def _fire_skill(self, caster: CombatUnit, sk, round_idx: int):
        chan = self._channel_for(sk)
        key = (int(sk["st"]), int(sk["id"]))
        coef = float(sk.get("maxedValue") or 0.0) + caster.skill_coef_bonus.get(key, 0.0)
        fired = False
        for eff in sk.get("effects", []):
            at = eff.get("actionType")
            tcat = eff.get("targetCategoryName") or ""
            tcount = eff.get("targetCount") or 1
            ecoef = coef if coef > 0 else float(eff.get("coefficient") or 0.0)
            if at == 101:                              # ATK enemy
                for tgt in self._pick_targets(caster, tcat or "enemy", tcount):
                    self._deal(caster, tgt, ecoef, chan, round_idx)
                fired = True
            elif at == 102:                            # heal allies
                for tgt in self._pick_targets(caster, tcat or "our", tcount):
                    self._heal(caster, tgt, ecoef)
                fired = True
            elif at in (121, 122):                     # purify own / dispel enemy
                tgts = self._pick_targets(caster, tcat or ("our" if at == 121 else "enemy"), tcount)
                for tgt in tgts:
                    self._cleanse(tgt, enemy=(at == 122))
                fired = True
            else:                                       # a buff/debuff id
                self._apply_buff_effect(caster, at, eff, tcat, tcount)
                fired = True
        # the skill's single Buff/Dbuff field (status it inflicts/grants)
        bid = (sk.get("buff") or {}).get("id")
        if bid:
            b = self.g.buff(int(bid))
            positive = (b or {}).get("type", 0) >= 0
            cat = "our" if positive else "enemy"
            for tgt in self._pick_targets(caster, cat, 1):
                self._apply_status(tgt, int(bid), rounds=2, value=float(sk.get("maxedValue") or 0.0))
        return fired

    def _apply_buff_effect(self, caster, buff_id, eff, tcat, tcount):
        if not buff_id:
            return
        b = self.g.buff(int(buff_id))
        positive = (b or {}).get("type", 0) >= 0
        cat = tcat or ("our" if positive else "enemy")
        rounds = eff.get("rawTokens", [None] * 12)
        dur = 2
        try:
            dur = int(float(rounds[9])) or 2
        except (ValueError, TypeError, IndexError):
            dur = 2
        for tgt in self._pick_targets(caster, cat, tcount):
            self._apply_status(tgt, int(buff_id), rounds=dur, value=float(eff.get("coefficient") or 0.0))

    def _cleanse(self, unit: CombatUnit, enemy: bool):
        # remove debuffs (own purify) or buffs (enemy dispel)
        for bid, st in list(unit.statuses.items()):
            b = self.g.buff(bid)
            t = (b or {}).get("type", 0)
            if enemy and t > 0:
                st["rounds"] = 0
            if (not enemy) and t < 0:
                st["rounds"] = 0

    # ---- per-unit turn -------------------------------------------------
    def _unit_turn(self, u: CombatUnit, round_idx: int, round_no: int):
        if not u.alive:
            return
        if self._has(u, CONTROL_STUN):
            return                                   # stunned: cannot act
        # Strategic (once per applicable round, gated by fromRound)
        for sk in u.skills:
            if int(sk["st"]) == 1:
                fr = self._skill_from_round(sk)
                if round_no >= fr:
                    self._fire_skill(u, sk, round_idx)
        # Tactical (probability), unless silenced
        if not self._has(u, CONTROL_SILENCE):
            for sk in u.skills:
                if int(sk["st"]) == 2 and round_no >= self._skill_from_round(sk):
                    if self.rng.random() < self._trigger_prob(sk, u):
                        self._fire_skill(u, sk, round_idx)
        # Normal attack, unless disarmed
        did_normal = False
        if not self._has(u, CONTROL_DISARM):
            tgt = self._pick_target(u)
            if tgt:
                self._deal(u, tgt, self.cfg.normal_attack_coef, "normal", round_idx)
                did_normal = True
        # Pursuit (after normal attack), probability
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

    def _trigger_prob(self, sk, unit=None) -> float:
        p = sk.get("skillP")
        if p is None:
            p = sk.get("triggerProbAtMax", 1.0)
        try:
            p = float(p)
        except (ValueError, TypeError):
            p = 1.0
        if unit is not None:
            key = (int(sk["st"]), int(sk["id"]))
            p += unit.skill_trigger_bonus.get(key, 0.0)            # relic / rune
            p += unit.channel_trigger.get(self._channel_for(sk), 0.0)  # gear 131/132
        return max(0.0, min(1.0, p))

    # ---- DoT before-action phase --------------------------------------
    def _before_action(self, side: int, round_idx: int):
        for u in self._alive(side):
            for bid, kind in DOT_BUFFS.items():
                st = u.statuses.get(bid)
                if st and st["rounds"] != 0:
                    dmg = (st.get("value", 0.0) or 0.5) * u.hp_max * 0.02   # ASSUMPTION
                    u.hp -= dmg
                    if u.hp <= 0:
                        u.hp = 0.0
                        u.alive = False

    def _tick_statuses(self, side: int):
        for u in self.sides[side]:
            for bid, st in u.statuses.items():
                if 0 < st["rounds"] < 90:
                    st["rounds"] -= 1

    def _start_new_bout(self):
        """Reset transient state for a rematch, CARRYING troop counts (HP) over.
        Statuses are cleared and passives re-applied -- a fresh engagement.
        Buff carry-over between bouts is UNKNOWN_SERVER_SIDE (assume reset)."""
        for side in (0, 1):
            for u in self.sides[side]:
                u.statuses = {}
                if u.alive:
                    self._apply_passives(u)

    def _run_bout(self):
        """One 8-round bout in place; returns (rounds_fought, decided, dmg0, dmg1)."""
        rounds = self.g.round_count
        dmg = {0: [0.0] * rounds, 1: [0.0] * rounds}
        self.round_dmg = dmg
        decided = False
        ri = 0
        for ri in range(rounds):
            round_no = ri + 1
            self._before_action(0, ri)
            self._before_action(1, ri)
            # ordered by Speed desc; equal-speed ties broken RANDOMLY (server
            # tie-break UNKNOWN_SERVER_SIDE) so neither side is favoured.
            order = sorted(
                [u for s in (0, 1) for u in self._alive(s)],
                key=lambda u: (-u.speed, self.rng.random()),
            )
            for u in order:
                self._unit_turn(u, ri, round_no)
            self._tick_statuses(0)
            self._tick_statuses(1)
            if self._is_over():
                decided = True
                break
        return ri + 1, decided, dmg[0], dmg[1]

    # ---- main loop: bouts of 8 rounds until a commander is wiped --------
    def run(self) -> BattleResult:
        first_rounds = 0
        first_d0 = first_d1 = None
        total0 = total1 = 0.0
        bouts = 0
        decided = False
        while bouts < self.cfg.max_bouts:
            bouts += 1
            if bouts > 1:
                self._start_new_bout()
            rf, decided, d0, d1 = self._run_bout()
            if bouts == 1:
                first_rounds, first_d0, first_d1 = rf, list(d0), list(d1)
            bout0, bout1 = sum(d0), sum(d1)
            total0 += bout0
            total1 += bout1
            if decided:
                break
            # undecided after a full 8 rounds: rematch (troops carried). If the
            # bout barely scratched either side, it's a stalemate -> stop as draw.
            if (bout0 + bout1) < self.cfg.bout_stalemate_frac * self._total_hp_max():
                break
        return self._result(first_rounds, bouts, first_d0 or [], first_d1 or [],
                            total0, total1)

    def _total_hp_max(self) -> float:
        return sum(u.hp_max for s in (0, 1) for u in self.sides[s]) or 1.0

    def _is_over(self) -> bool:
        for side in (0, 1):
            cmd = self._commander(side)
            if cmd is None or not cmd.alive:
                return True
            if not self._alive(side):
                return True
        return False

    def _result(self, rounds_fought: int, bouts_fought: int,
                first_d0: list, first_d1: list,
                total0: float, total1: float) -> BattleResult:
        def frac(side):
            us = self.sides[side]
            tot = sum(u.hp_max for u in us) or 1.0
            return sum(u.hp for u in us) / tot
        p_alive = len(self._alive(0))
        e_alive = len(self._alive(1))
        pc, ec = self._commander(0), self._commander(1)
        if pc and not pc.alive and (not ec or ec.alive):
            winner = 1
        elif ec and not ec.alive and (not pc or pc.alive):
            winner = 0
        else:
            # impasse hit max_bouts/stalemate: decide by remaining troop fraction
            pf, ef = frac(0), frac(1)
            winner = 0 if pf > ef else (1 if ef > pf else -1)
        return BattleResult(
            winner=winner, rounds_fought=rounds_fought, bouts_fought=bouts_fought,
            player_damage_by_round=first_d0, enemy_damage_by_round=first_d1,
            total_player_damage=total0, total_enemy_damage=total1,
            player_units_alive=p_alive, enemy_units_alive=e_alive,
            player_troops_frac_remaining=frac(0),
            enemy_troops_frac_remaining=frac(1),
        )
