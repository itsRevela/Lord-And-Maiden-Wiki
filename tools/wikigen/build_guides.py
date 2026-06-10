"""Community-strategy / mechanics-explainer pages.

These pages are NOT generated from the game's config files — they rebuild player
knowledge from the community Steam guides by **Lofthouse** (archived at
github.com/itsRevela/Lord-And-Maiden-Guides), including information transcribed
from the guides' screenshots. No screenshots are reproduced here; their content is
re-presented as text/tables and, where possible, cross-checked against the
extracted data. Every page carries an attribution banner so the line between
extracted data and player strategy stays clear.

Strategy reflects player experience and may be out of date with current patches.
`register(write, tbl, R)` is called from build.main().
"""

ARCHIVE = "https://github.com/itsRevela/Lord-And-Maiden-Guides"


def _attrib(steam_id, posted):
    url = "https://steamcommunity.com/sharedfiles/filedetails/?id=%s" % steam_id
    return [
        "> 📘 **Community strategy.** Rebuilt from a Steam Community guide by "
        "**Lofthouse** — credit to the original author. This is player experience and "
        "screenshot-transcribed info, not data extracted from the game files, and may be "
        "out of date (originally posted %s). Sources: [original guide](%s) · [archive](%s)." % (posted, url, ARCHIVE),
        "",
    ]


# --------------------------------------------------------------------------- #
def gen_battle_mechanics(write, tbl, R):
    lines = _attrib("2759156753", "2022")
    lines += [
        "How a battle actually plays out, how to read skill descriptions, and how a unit's "
        "fighting stats are built up. For the data-side rules (troop restraint, target %, skill "
        "order) see [Stats, Formulas & Mechanics](Stats-and-Formulas.md); for status-effect "
        "definitions see [Status Effects](Status-Effects.md).", "",
        "## How a fight resolves", "",
        "- A team is **1 Commander + 2 units**. You **win** when the enemy Commander loses all "
        "their troops; you **lose** when your Commander loses all theirs.",
        "- **Pre-battle phase:** many *Strategy* (blue) skills apply here — buffs, debuffs, or "
        "effects that only switch on in later rounds.",
        "- **8 rounds of combat.** Each round, every unit (both teams) acts in order of its "
        "**Speed**. On its turn a unit makes a **normal attack**, then rolls the chance for any "
        "**Chase / Tactical** skills to fire.",
        "- **Targeting:** normal attacks hit **one random enemy**; skills hit random targets "
        "unless the text says otherwise. The **Commander is 25% less likely** to be targeted, "
        "which is why a DPS Commander is usually protected by its two supports.",
        "- **Impasse:** if both Commanders still have troops after 8 rounds, the teams pause ~1 "
        "minute, then you may wait for another 8-round bout, retreat to heal, or re-engage "
        "immediately. (Exact behaviour varies by game mode.)",
        "- Read the **battle log** for a full breakdown; once you build a **Library** you can "
        "simulate battles.", "",
        "> **Key insight:** the damage an enemy deals scales largely with their **troop "
        "numbers**, so cutting the enemy's troop count is the best protection. Skills that give "
        "an early edge (strong first-3-rounds effects) let you thin the enemy while staying safe.", "",
        "## Reading skill descriptions", "",
    ]
    lines += tbl(["Phrase", "What it means"], [
        ["\"Affected by X attribute\"", "The effect scales with that stat — roughly **×** for every "
         "**200** points of the named stat (Attack / Speed / Defence / Destruction)."],
        ["Damage Coefficient X", "Expected damage vs. a normal attack; **1.00 = one normal attack's** worth."],
        ["Healing Coefficient X", "Same idea, for healing."],
        ["Strategy skill (blue)", "Fires before battle or on a stated round; **cannot** be stopped by status effects."],
        ["Tactical skill (purple)", "Has a per-round chance to fire on the unit's turn."],
        ["Passive skill", "Always-on self-buff; cannot be stopped by status effects."],
        ["Chase skill", "Chance to fire **after the unit's normal attack**."],
        ["1 Round Preparation", "The effect applies at the **start of the unit's next turn**, not immediately."],
        ["Counterattack", "Strikes back at any enemy that hits it with a normal attack."],
        ["Aid", "Redirects attacks aimed at allies onto itself."],
        ["Combo attack", "The unit makes its normal attack **twice** in a round (Chase can trigger on both)."],
        ["Shield", "Blocks the first instance of damage taken."],
        ["Splash", "Normal attacks also deal a % of the hit to the other two enemies, **ignoring defence**."],
        ["\"Real damage\" / \"strong attack\"", "A fixed extra hit based only on **troop count + the unit's "
         "in-battle Attack**; triggers on every hit of multi-hit skills."],
        ["\"Burning\" / \"Spell damage\"", "Damages the enemy **before** they take their turn."],
        ["\"Your own troops\"", "Affects only the skill-holder; **\"2/3 of our troops\"** = that many random allies."],
    ])
    lines += [
        "", "## What stats a unit fights with", "",
        "In-battle stat = **Unit stats + Troop stats** (troop stats are boosted by armour, "
        "technology and titles **before** being added). Unit stats come from four sources:", "",
        "1. **Levelling** — each stat grows by its own per-level amount (`stat(L)=base+floor(growth×L)`; see [hero pages](../Heroes/Heroes.md)).",
        "2. **Stat points** — 1 free point per level, plus **10 per Advance** (Advances need hero dupes).",
        "3. **Favorability** — raises **all stats by up to 30** (see [Favorability](../Progression/Favorability.md)).",
        "4. **Race & troop bonus** — **+3%** all stats with 2 same-race units, **+5%** with 3; up to **+10%** to certain stats when all three units use the **same troop type**.", "",
        "### Worked example — how in-battle Attack is built",
        "*(Transcribed from the guide's diagram; the arithmetic and the troop value check out against our "
        "data — 90 is an actual troop Attack stat from [Soldiers](../Soldiers/Soldiers.md).)*", "",
    ]
    lines += tbl(["Component", "Value", "Note"], [
        ["Unit (hero) Attack", "204", "from level + stat points + favorability"],
        ["× team bonus (+3%)", "210.12", "204 × 1.03 (2 same-race units)"],
        ["Troop base Attack", "90", "the assigned troop's Attack stat"],
        ["+ armour / tech / title / etc. boosts", "+81", "stacked %: +12% (10.8) +65.5% (58.95) +6.5% (5.85) +3% (2.7) +3% (2.7)"],
        ["Troop total", "171", "90 + 81"],
        ["**Calculated Attack**", "**381.12**", "210.12 (unit) + 171 (troop)"],
    ])
    lines += [
        "",
        "So **in-battle Attack ≈ (Unit Attack × team/race multiplier) + (Troop Attack × (1 + Σ boosts))**. "
        "The exact boost percentages depend on your armour, technology and title, so this is the *shape* of "
        "the calculation rather than fixed numbers. Defence, Destruction and Speed are built the same way. "
        "*(The in-game \"actual\" value can differ from the calculated one by a fraction due to rounding.)*",
    ]
    write("Mechanics/Battle-Mechanics.md", "Battle Mechanics", "Mechanics", lines)


def gen_status_effects(write, tbl, R):
    lines = _attrib("2759156753", "2022")
    lines += [
        "Crowd-control and status definitions used throughout combat. See "
        "[Battle Mechanics](Battle-Mechanics.md) for how skills apply them and "
        "[Buffs & Debuffs](Buffs.md) for the data catalog.", "",
    ]
    lines += tbl(["Status", "Effect"], [
        ["Disarm", "Unit cannot make normal attacks."],
        ["Silence", "Unit cannot use Tactical skills."],
        ["Vertigo", "Disarm **and** Silence combined."],
        ["Stun", "Unit is **Unable to Move** — it cannot act at all for the duration."],
        ["Chaos", "Normal attacks and Tactical/Chase skills target **completely at random** (friend or foe)."],
        ["Forbidden Healing", "Unit cannot be healed."],
        ["Taunt", "Unit must normal-attack the taunter (ignored if the unit is also in Chaos)."],
        ["Immune / In Concentration", "Ignores status effects **during its turn**; does not remove or block them being applied."],
        ["Counterattack", "Automatically hits back at anyone who normal-attacks it; once applied, cannot be prevented."],
        ["Shield", "Absorbs the first instance of damage."],
        ["Purify", "Skills that **remove status effects from allies**."],
        ["Dispel", "Skills that **strip buffs / positive effects from enemies**."],
    ])
    write("Mechanics/Status-Effects.md", "Status Effects", "Mechanics", lines)


def gen_team_building(write, tbl, R):
    lines = _attrib("2759156753", "2022")
    lines += [
        "How to put a team together. For the developer's ready-made comps see "
        "[Recommended Teams](Recommended-Teams.md); for hero stats see the "
        "[Roster](../Heroes/Heroes.md) and [Lv 80 Leaderboards](../Heroes/Hero-Leaderboards.md).", "",
        "## The 1 + 2 template",
        "A team is **1 Commander + 2 units**. The Commander is **25% less likely to be targeted** "
        "and is your win/lose anchor, so the usual build is:", "",
        "- **Commander → a DPS hero** (kept relatively safe by the targeting rule).",
        "- **Support slot 1 → defence / healing** (e.g. Pomon, Rhea, Lafayette SP).",
        "- **Support slot 2 → a debuffer** (e.g. Slider SP, Moussika, Saintess Shin).", "",
        "…but ultimately use the best units and skills you actually have.", "",
        "## Which troop for which unit",
        "Each unit is assigned **one troop type**. Rough profiles:", "",
    ]
    lines += tbl(["Troop", "Profile", "Good for"], [
        ["Archer", "High Attack, low HP/Defence, ok speed", "**DPS Commander** — research higher-tier Archers first to kill faster."],
        ["Infantry", "High HP, ok Defence, low Attack", "Support units **when you run healing** (healing scales with HP)."],
        ["Cavalry", "Fast, balanced, ok damage", "Supports that still need to deal damage, or when you want speed."],
        ["Siege / Chariot", "High Destruction, slow, low Defence", "Debuffers — but so slow it is often better skipped."],
    ])
    lines += [
        "",
        "You start on Tier 1 troops and unlock higher tiers in the [Academy](../Research/Science.md). "
        "**Prioritise Archer tiers** (Tier 4 is the practical baseline; Tier 5 takes an enormous amount of time).", "",
        "## See also",
        "- [Build Order & City Hall Progression](../Progression/Build-Order.md) — research priorities.",
        "- [Battle Mechanics](../Mechanics/Battle-Mechanics.md) — how the fight is resolved.",
    ]
    write("Teams/Team-Building.md", "Team Building Guide", "Teams & Builds", lines)


def gen_build_order(write, tbl, R):
    lines = _attrib("2768347161", "2022")
    lines += [
        "A long-term progression plan. The hard requirements below are **confirmed by the game "
        "data** (City Hall maxes at **level 25**, and each level's prerequisites are in the "
        "[Buildings](../Buildings/Buildings.md) *Requires* column); the priorities are community advice.", "",
        "## City Hall progression",
        "Your **City Hall** gates everything and maxes at **level 25**. To raise it to level *N* the "
        "data requires the **Academy** (and, through it, the **Dwelling** → **Adventurer's Guild** "
        "chain) at level *N−1*, **plus one other building** at *N−1* that changes each level. In short, "
        "each City Hall level bring up:", "",
        "1. **Dwelling** to City-Hall level *(only one needed)*.",
        "2. **Adventurer's Guild** — needs the Dwelling done first.",
        "3. **Academy** — needs the Adventurer's Guild done first.",
        "4. **One extra pre-set building** (see the City Hall *Requires* column on [Buildings](../Buildings/Buildings.md)).", "",
        "## Using your two build queues",
        "- Run **queue 1** through steps 1 → 2 → 3 (Dwelling, Adventurer's Guild, Academy).",
        "- Run **queue 2** on the **Alliance Hall** first (more alliance build-help), then step 4.",
        "- Keep **both** queues always advancing toward the next City Hall upgrade.",
        "- **Speed up Academy upgrades** when you can — you can't research while the Academy is upgrading.", "",
        "## Research priorities (Academy)",
        "*(Full tech tables on [Research](../Research/Science.md).)*", "",
        "- **Economy:** rush **Research Speed** and **Build Speed** — best long-term value. Max the cheap "
        "early techs, but don't over-invest in resource/production techs.",
        "- **Trade:** rush **Carriage** (caravan load) until you can comfortably hit the daily trade limit.",
        "- **Military:** rush **Archer** tiers — aim for **Tier 4** (Tier 5 costs an enormous amount of time).", "",
        "## See also",
        "- [Building & City Unlocks](Building-Unlocks.md) and [Feature Unlock Levels](Feature-Unlocks.md).",
        "- [Cumulative Costs](Cumulative-Costs.md) — total resources/time to max everything.",
    ]
    write("Progression/Build-Order.md", "Build Order & City Hall Progression", "Progression", lines)


def gen_territory_wars(write, tbl, R):
    lines = _attrib("2767325455", "2022")
    lines += [
        "Everything about guild **Territory Wars** and **Raids** — registering, the weekly war "
        "schedule, ownership rules, rewards, how a war resolves, and siege tactics.", "",
        "## What they are",
        "Your whole guild fights a large number of strong NPC enemies for control of a territory. "
        "**Wars** run at fixed times Fri–Sun; **Raids** can be started by the guild leader/captain "
        "any time Mon–Thu. The fighting is identical between them.", "",
        "## Registering",
        "- **War registration window:** Mon 00:00 UTC → **Fri 10:00 UTC** (in-game time is UTC).",
        "- The guild leader/captain spends **League Points** (earned from member donations) to register.",
        "- If two guilds register for the same territory they **compete** for it — avoid territories "
        "already registered by others (unless you're blocking weaker guilds from first-clear rewards).",
        "- **Raids:** one available per guild on each of Mon/Tue/Wed/Thu; the leader/captain starts it any time.", "",
        "## Weekly war schedule", "",
    ]
    lines += tbl(["Time (UTC)", "War"], [
        ["Fri 12:00", "Toll Gate wars"],
        ["Sat 12:00", "Small City wars"],
        ["Sat 13:30", "Big City war"],
        ["Sun 12:00", "Chronos war"],
    ])
    lines += [
        "", "## Ownership rules",
        "A guild can hold at most: **2 Toll Gates**, **2 Small Cities**, **1 Big City**, and **Chronos**. "
        "Tiers are gated — you must own at least one of the tier below to register for the next "
        "(Toll Gate: free · Small City: needs ≥1 Toll Gate · Big City: needs ≥1 Small City · Chronos: needs the Big City).", "",
        "> ⚠️ **A guild loses ALL territory each war period (Fri–Sun).** To keep playing for them you must "
        "**abandon and re-register** before registration closes Fri 10:00 UTC — and abandon/re-register "
        "**highest tier first** (Chronos → Big → Small → Toll), or the tier gating blocks you. Only register "
        "for territories that still have first-clear rewards.", "",
        "## Rewards",
        "- **First Clear** (one-time, per territory): a generous bundle of summons, gems, prestige, speedups and "
        "resources, mailed to **every** guild member whether they fought or not.",
        "- **Participation:** earn **10,000+ integral** (attacker + defender combined counts) for the **Winning** "
        "reward (if the guild wins) or the **Failure** reward (if it loses — barely smaller, so joining unwinnable "
        "wars/raids just for the Failure reward is viable).",
        "- **Occupation:** while held, the territory mails resources to the guild storehouse **daily**. "
        "*(In-game shorthand: 400,000 food = 40W.)*",
        "- Rewards are mailed once the **1-hour** war period ends. Exact amounts differ per territory tier — check in-game.", "",
        "## How a war actually resolves",
        "- The war opens at the scheduled time for **1 hour**. Toll-gate + small-city wars expect both cleared "
        "in that hour — if weak, focus one and farm 10,000 integral in the other.",
        "- Rule of thumb: clear a Small City in **~25 min** and you're ready for the Big City.",
        "- You have a **home fort** to refill troops without leaving; leaving costs a **1-minute** rejoin penalty.",
        "- **Toll-gate wars have no fort** — only scattered field enemies. Otherwise: clear the scattered enemies "
        "*outside* the fort first, then assault the fort — a **gauntlet of enemy teams** using troops **one tier "
        "higher** than the outside enemies.",
        "- Most enemy teams are commanded by **Rhea** with a **Cautious** skill (reduces damage dealt & taken by "
        "her side). The **final enemy** of each fort is a **Lord** with **Goddess Bless** (stronger than Cautious "
        "+ 3 rounds of immunity) plus heavy damage/shields/CC.",
        "- Lords per fort: Toll Gate **0** · Small City **1** (end) · Big City **2** (mid + end) · Chronos **3** (⅓, ⅔, end).",
        "- **Capturing:** after all enemies are defeated, keep teams **inside the enemy fort** until the capture "
        "bar hits **100%**. The guild then claims the territory and rewards at the end of the hour.", "",
        "## Siege warfare",
        "- A team whose **Commander uses Siege** troops and is **close enough to the fort** can bombard it directly "
        "(no need to clear scattered enemies first). The siege button fires every **30 s**, hitting a random fort team.",
        "- Siege damage scales with **Destruction** (units + troops + tech) and **troop numbers**.",
        "- Fort enemies sometimes strike the siege team back. Mitigate with a **1-troop Commander** team (same race "
        "for +5% stats): the Commander has a single low-tier troop so the team loses instantly with no real losses, "
        "returns home, refills the supports, and redeploys.",
    ]
    write("Alliance/Territory-Wars-and-Raids.md", "Territory Wars & Raids", "Alliance", lines)


def gen_event_schedule(write, tbl, R):
    lines = _attrib("2768347161", "2022")
    lines += [
        "Events run on a repeating **12-day pattern**. Most have a simple objective that pays "
        "resources, speedups and **100 gems**, run for 2 days, and can be completed each day. "
        "Some add a **leaderboard** for extra end rewards; **exchange-shop** events (Vigorous "
        "Development) and **seasonal** events let you spend earned currency on a reward shop. "
        "A full calendar is in the in-game Events menu. *(Data-side configs on "
        "[Quests & Events](Quests-and-Events.md).)*", "",
    ]
    lines += tbl(["Day", "Active events"], [
        ["1", "Luck Adventure (summon units) · End the War with War (defeat rebels)"],
        ["2", "End the War with War · Thriving (increase prosperity)"],
        ["3", "Hoarding Grain and Grass (gather resources) · Thriving"],
        ["4", "Hoarding Grain and Grass · Go All Out (spend vitality — leaderboard)"],
        ["5", "Go All Out · An Irresistible Force (train troops)"],
        ["6", "An Irresistible Force · Vigorous Development (tasks → exchange-shop medals)"],
        ["7", "Vigorous Development · Lasting Political Stability (barbarian towers) · Treasures Fill the Home (spend gems — leaderboard) · Speedup event (leaderboard)"],
        ["8", "Vigorous Development · Lasting Political Stability · Treasures Fill the Home · Speedup event"],
        ["9", "Vigorous Development · Lasting Political Stability · Treasures Fill the Home · Speedup event"],
        ["10", "Luck Adventure · The Caravan Trade (trade via caravans)"],
        ["11", "Luck Adventure · The Caravan Trade"],
        ["12", "Luck Adventure · The Caravan Trade"],
    ])
    write("Quests/Event-Schedule.md", "Event Schedule", "Quests & Events", lines)


def gen_player_systems(write, tbl, R):
    lines = _attrib("2768347161", "2022")
    lines += [
        "Three account-power systems that aren't in the extracted config tables, captured here "
        "from player knowledge and the guide's screenshots.", "",
        "## Prestige",
        "Prestige grants an escalating **daily gift** and passive **stat benefits** at each level.", "",
        "**Daily gift by prestige level** *(transcribed from the guide's screenshot; counts are as shown, "
        "item identities inferred from the in-game icons — levels 1–17, the track continues beyond):*", "",
    ]
    # Prestige daily-gift counts from the guide screenshot (levels 1-17).
    # box value (each of three 10,000 resource boxes) == prestige level.
    speedup = {1: "—", 2: "—"}
    for n in range(3, 18):
        speedup[n] = n - 2
    vit = {1: "—", 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4,
           10: 5, 11: 5, 12: 5, 13: 6, 14: 7, 15: 8, 16: 9, 17: 10}
    gems = {n: ("—" if n < 10 else (1 if n < 13 else (2 if n < 16 else 3))) for n in range(1, 18)}
    rows = [[n, speedup[n], vit[n], "%d each" % n, gems[n]] for n in range(1, 18)]
    lines += tbl(["Prestige Lv", "5-min Speedups", "Vitality (×50)", "Resource boxes (×10,000, three types)", "Gems"], rows)
    lines += [
        "",
        "**Passive benefits.** Each prestige level raises a set of stats; the categories (from the "
        "benefits screenshot) are: Hero-card cap, Food/Wood/Stone **production**, Food/Wood/Stone/Iron "
        "**gathering speed**, Recruitment speed, Research speed, Training & Hospital capacity, Build speed, "
        "Hero EXP gain, Vitality cap, and unit **Destruction / Health / Defence / March speed**. Values climb "
        "each level (e.g. resource production reaches up to ~50% and the hero-card cap up to ~90 at the top "
        "levels shown). Check the in-game prestige screen for the exact figure at your level.", "",
        "## Title & Astral Badges",
        "**Astral Badges** raise your **Title**, which buffs troop stats, and are also spent in the "
        "**Title Shop**. They drop from **Barbarian Towers** and **World Bosses**, and the Title Shop "
        "sells a limited weekly amount.", "",
        "> *Outdated:* an old trick farmed badges via repeated 1-troop-commander PvP (both players got "
        "1 badge per battle up to the daily cap). **This has been patched.**", "",
        "## Troop exoskeleton (cosmetic armour)",
        "Each troop type has a cosmetic armour bought for **5,888 gems**. Once owned it can be **upgraded** "
        "for **gold + Hearts** (Hearts come from World Bosses at a low rate, or the Title Shop's ~15/week each, "
        "so it's slow):", "",
        "- **Levels 1–14:** 15 Hearts per upgrade.   **Level 15+:** 30 Hearts per upgrade.",
        "- Upgrades only raise each troop's **secondary** stats — they shore up the stat a troop is weak in "
        "(Archers gain no Attack, Cavalry no Defence, Infantry no HP, Siege no Destruction).",
    ]
    write("Progression/Player-Systems.md", "Prestige, Titles & Troop Armour", "Progression", lines)


def gen_spending(write, tbl, R):
    lines = _attrib("2768347161", "2022")
    lines += [
        "Where money and free-to-play effort go furthest. For the raw price tables see "
        "the [Market](Market.md) and the [Shop](Shop.md). *(Prices show in USD for "
        "English players; other-currency conversions can be unfavourable.)*", "",
        "## Best value purchases",
        "*(Figures below are from the guide's store screenshots and may differ from the current build — "
        "see the [Shop](Shop.md) page for the data-extracted contents.)*", "",
        "- **Growth Fund** (~$14.99, advertised \"2000% value\") — pays gems at each **City Hall milestone** "
        "(e.g. 700 + 3,200 gems at CH 5, then ~800 at CH 6, ~900 at CH 7, ~1,200 at CH 8, and onward). The "
        "**best gem value**.",
        "- **$5 Monthly Card** (~$4.99) — **980 gems instantly + 300 gems/day** (≈9,980 over the month) and "
        "**doubles your upgradeable soldiers**. The best ongoing value.",
        "- **Prestige gift pack (Pomon)** (~$4.99, one-time, \"+1700% value\") — grants the hero **Pomon**, "
        "**150,000 ×3 resources**, and **Prestige Lv.4**; a strong early hero that smooths the early game "
        "(skip if you rerolled a good starter on mobile).",
        "- **$15 Monthly Card** / **Adventures of Santo** — fine for spenders, weaker value than the $5 card.",
        "- Beyond those, little else is worth buying for value.", "",
        "## Free-to-play: second / aid account",
        "At **City Hall 10** you can build the **Trading Post** to send resources to a guild member. Players "
        "commonly raise **alt accounts** (mobile) to mail resources to their main daily — freeing the main's "
        "gathering teams to **mine gems** in the world instead.",
        "- The world **gem-gathering cap** rises with City Hall level, maxing at **400 at City Hall 25** "
        "(fills after gathering ~500 gems in a day).", "",
        "> *Cross-server note:* the game also ships as **\"Trip in Another World\"** (Steam) and "
        "**\"Lord of the Other World\"** (mobile). Servers 1–3 are mobile-only; Server 4+ is shared. "
        "Accounts are locked to the server they're created on; regional chat is cross-server and the "
        "in-game translator works well.",
    ]
    write("Items/Spending-Guide.md", "Spending & Free-to-Play Tips", "City & Economy", lines)


# --------------------------------------------------------------------------- #
def register(write, tbl, R):
    gen_battle_mechanics(write, tbl, R)
    gen_status_effects(write, tbl, R)
    gen_team_building(write, tbl, R)
    gen_build_order(write, tbl, R)
    gen_territory_wars(write, tbl, R)
    gen_event_schedule(write, tbl, R)
    gen_player_systems(write, tbl, R)
    gen_spending(write, tbl, R)
