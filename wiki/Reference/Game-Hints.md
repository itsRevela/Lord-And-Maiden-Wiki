# In-Game Hints & Help

The game explains itself through several **hint / help systems**. This page catalogues where they live and collects the **battle-related rules and calculations** they reveal (several of which are otherwise hard to find).

## Where the game explains things
- **Hero Info → Details (per hero):** tap a hero, then **Details** — the **Race** label opens a race description, and the panel shows that hero's **actual in-battle stats**. How those stats are built (Unit + Troop, with all bonuses) is worked through on [Battle Mechanics](../Mechanics/Battle-Mechanics.md), and where the hero's free stat points come from is on [Hero Advancement](../Heroes/Hero-Advancement.md).
- **Loading-screen & topic tips:** rotating hints grouped by subject — the full set is on [Game Tips](Tips.md).
- **Feature "?" buttons:** most panels have a help/`?` icon that explains that feature.
- **Skill & talent tooltips:** tapping a skill or talent shows its effect, type and awaken table — see the [Skill Catalog](../Heroes/Skills.md) and [Hero Talents](../Heroes/Hero-Talents.md).
- **System pop-ups:** confirmation/clarification messages that appear during play; the gameplay-relevant ones are collected below.

## Battle rules & calculations the hints explain

### Stats
- A unit's **in-battle stat = its own (hero) stat + its troop's stat** (the troop value is itself boosted by armour, technology and titles first). See the worked example on [Battle Mechanics](../Mechanics/Battle-Mechanics.md).
- **"Affected by X Attribute"** in a skill always refers to the **caster** — the hero equipped with the skill — not the target.
- The **healing** from a skill is **affected by the Soldiers' HP** attribute (so healers want high-HP troops).
- A **Damage/Healing Coefficient** is measured against a normal attack: **1.00 = one normal attack's** worth.

### Combat
- **Troop restraint:** Infantry → Archer → Cavalry → Infantry; a restrained troop deals **−25% damage**.
- **Level suppression:** higher-level soldiers deal extra damage to lower-level soldiers (separate from restraint).
- **Targeting (no Taunt):** Commander 20%, each Striker 40%; skill activation order is Passive → Strategic → Tactical → Normal ATK → Pursuit.
- **Chaos** only affects normal attacks and damage-dealing Tactical skills (and Pursuits they trigger).
- **Leaving a battle counts as a loss.**

### Skills
- The **same effect from different skill types stacks** (added together); the **same effect from the same type does not** (only the highest applies).
- **"2 of our troops"** targets **2 *other* allied troops, excluding the caster** itself.
- A team may field only **one Strategic skill stone**, and **no two identical Strategic skills** (innate + stones counted together). See [Skill Stones](../Heroes/Skill-Stones.md).

### Summoning, progression & modes
- **Rate-up summons:** when a **5★ Hero or 5★ Relic** appears in a summon, there is a **50% chance it is the featured (selected) one**.
- **Codex submission destroys** the submitted hero / prop / equipment permanently.
- Past the **World Level** cap a hero gains only EXP and **cannot raise its Lord level** further.
- **Specialty transport** rewards increase with **City Hall level**.
- A maximum of **3 Divine Demon Cards of the same type** can be deployed.
- **Siege:** long-press the bombardment button for **auto-bombard**, and a **Giant Trebuchet auto-fires** once the siege begins (see [Territory Wars](../Alliance/Territory-Wars-and-Raids.md)).
- With **cross-server players** present, server-wide **first-clear** rewards are not counted.

*Sourced from the game's in-game tip/help text (Tips and system-hint data); combat itself is resolved server-side, so these are the rules the client states rather than the full damage formula.*

---
*Auto-generated from game data by `tools/wikigen/build.py`. Do not edit by hand.*
