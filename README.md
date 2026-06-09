<div align="center">

# 🏰 Lord and Maiden — Community Wiki

**The complete, data-mined reference for *Lord and Maiden*** — every stat, formula,
cost table, skill, and progression curve, pulled straight from the game files.

![Pages](https://img.shields.io/badge/pages-178-1f6feb)
![Heroes](https://img.shields.io/badge/heroes-122-8957e5)
![Source](https://img.shields.io/badge/source-data--mined-2da44e)
![Verified](https://img.shields.io/badge/numbers-verified-2da44e)

</div>

---

*Lord and Maiden* is a strategy / city-management game: grow a city, recruit and level
**122 named heroes**, train four troop types, research technology, and fight a PvE campaign,
world & alliance bosses, trials and PvP. Public information is scarce, so this wiki extracts
the real numbers directly from the game data — **nothing is guessed**, and every figure is
cross-checked against the source files.

## 📖 Start here

| | |
|---|---|
| 🧭 **[Game Overview](wiki/Game-Overview.md)** | What the game is, core systems, and the feature-unlock order. |
| 📐 **[Stats, Formulas & Mechanics](wiki/Mechanics/Stats-and-Formulas.md)** | The math: hero growth, RST, Power, and combat rules. |
| 📖 **[Glossary](wiki/Reference/Glossary.md)** | Every stat abbreviation and game term explained. |
| 🏆 **[Hero Lv 80 Leaderboards](wiki/Heroes/Hero-Leaderboards.md)** | End-game stats for all 122 heroes, ranked. |
| 🗂️ **[Full A–Z index »](wiki/README.md)** | The complete table of contents (every page). |

## 🗂️ Browse by category

**⚔️ Heroes & Combat**
[Hero Roster](wiki/Heroes/Heroes.md) ·
[Lv 80 Leaderboards](wiki/Heroes/Hero-Leaderboards.md) ·
[Skill Catalog](wiki/Heroes/Skills.md) ·
[Hero Talents](wiki/Heroes/Hero-Talents.md) ·
[Lord Talents](wiki/Heroes/Lord-Talents.md) ·
[Hero Skins](wiki/Heroes/Hero-Skins.md) ·
[AI / Enemy Heroes](wiki/Heroes/AI-Heroes.md) ·
[Recommended Teams](wiki/Teams/Recommended-Teams.md)

**🛡️ Military & Mechanics**
[Soldiers (Troops)](wiki/Soldiers/Soldiers.md) ·
[Troop Combinations](wiki/Military/Troop-Combinations.md) ·
[Stats & Formulas](wiki/Mechanics/Stats-and-Formulas.md) ·
[Buffs & Debuffs](wiki/Mechanics/Buffs.md)

**🏙️ City & Economy**
[Buildings](wiki/Buildings/Buildings.md) ·
[Research](wiki/Research/Science.md) ·
[Crafting & Production](wiki/Crafting/Formulas.md) ·
[Shops](wiki/Items/Shops.md) ·
[Recharge & Gift Packs](wiki/Items/Recharge-Packs.md)

**📈 Progression**
[VIP](wiki/Progression/VIP.md) ·
[Favorability](wiki/Progression/Favorability.md) ·
[Style](wiki/Progression/Style.md) ·
[Ship](wiki/Progression/Ship.md) ·
[Lord Outfits](wiki/Progression/Lord-Outfits.md) ·
[Feature Unlocks](wiki/Progression/Feature-Unlocks.md) ·
[Building Unlocks](wiki/Progression/Building-Unlocks.md) ·
[Cumulative Costs](wiki/Progression/Cumulative-Costs.md)

**🎒 Items**
[Items & Resources](wiki/Items/Items.md) ·
[Equipment / Gear](wiki/Items/Equipment.md) ·
[Item Sources](wiki/Items/Item-Sources.md) ·
[Choice Chests](wiki/Items/Choice-Chests.md) ·
[Gift Code Rewards](wiki/Items/Gift-Code-Rewards.md)

**🗺️ PvE & World**
[Campaign](wiki/World/Campaign.md) ·
[Relic Dungeons](wiki/World/Relic-Dungeons.md) ·
[Bosses](wiki/World/Bosses.md) ·
[Trials](wiki/World/Trials.md) ·
[Warlord Challenge](wiki/World/Warlord-Challenge.md) ·
[NPC Cities](wiki/World/NPC-Cities.md) ·
[World Map](wiki/World/World-Map.md) ·
[Wilderness & World Boxes](wiki/World/Wild-Exploration.md) ·
[World & Naval Structures](wiki/World/World-Structures.md)

**🤝 Alliance · 🎴 Codex · 📜 Quests & Lore**
[Alliance Research](wiki/Alliance/Union-Research.md) ·
[Hero Codex](wiki/Codex/Codex.md) ·
[Item Collections](wiki/Codex/Item-Collections.md) ·
[Reward Boxes](wiki/Codex/Reward-Boxes.md) ·
[Quests & Events](wiki/Quests/Quests-and-Events.md) ·
[Minigames](wiki/Quests/Minigames.md) ·
[Story & Plot](wiki/Lore/Story.md) ·
[Dating Events](wiki/Lore/Dating-Events.md) ·
[Maidens](wiki/Characters/Maidens.md)

**📚 Reference**
[Glossary](wiki/Reference/Glossary.md) ·
[Attribute Catalog](wiki/Reference/Attributes.md) ·
[Game Tips](wiki/Reference/Tips.md) ·
[AI Equipment](wiki/Reference/AI-Equipment.md) ·
[Avatar Frames](wiki/Reference/Avatar-Frames.md) ·
[Chat Emojis](wiki/Reference/Emojis.md)

**📘 Strategy & Guides** *(player knowledge, rebuilt from community Steam guides by [Lofthouse](https://github.com/itsRevela/Lord-And-Maiden-Guides) — may be out of date)*
[Battle Mechanics](wiki/Mechanics/Battle-Mechanics.md) ·
[Status Effects](wiki/Mechanics/Status-Effects.md) ·
[Team Building Guide](wiki/Teams/Team-Building.md) ·
[Build Order & City Hall Progression](wiki/Progression/Build-Order.md) ·
[Territory Wars & Raids](wiki/Alliance/Territory-Wars-and-Raids.md) ·
[Event Schedule](wiki/Quests/Event-Schedule.md) ·
[Prestige, Titles & Troop Armour](wiki/Progression/Player-Systems.md) ·
[Spending & Free-to-Play Tips](wiki/Items/Spending-Guide.md)

## ✅ Accuracy

Every page is **generated from the game's own data files** — no hand-typed numbers.
The generator resolves every internal ID to a readable name, and a checker (`verify.py`)
enforces **zero broken links, zero unresolved IDs, and zero untranslated text** on every build.
~11,000+ numeric cells (hero growth, building/research costs, soldier stats, crafting, etc.)
have been independently recomputed against the source — **0 discrepancies** — and the core
formulas are confirmed against the decompiled game code.

> **Server-side caveat:** exact battle damage and total Power are computed on the game's
> servers and are **not** present in the client. This wiki documents every *input* (stats,
> skills, buffs, Power composition) and the published combat rules, but not the hidden
> server damage equation.

## 🛠️ How it's built

The game is **not encrypted** — it uses YooAsset (plain `UnityFS` bundles) + HybridCLR
(game C# ships as plain .NET DLLs). The pipeline is *extraction + decompilation*, then a
data-driven generator turns the configs into Markdown. See
[`notes/`](notes/) for the full methodology and encryption analysis.

```
wiki/        the wiki — read this (start at wiki/README.md or Game-Overview.md)
data/        extracted game configs the wiki is generated from (csv + localization)
tools/       the generator (tools/wikigen/) and extraction scripts
notes/       methodology, recon and formula notes
decompiled/  decompiled C# from the game DLLs   (gitignored)
extracted/   raw bundle/XML outputs             (gitignored)
```

**Regenerate the wiki** (Python 3 + `UnityPy`):

```bash
python tools/wikigen/build.py     # regenerate every page from data/
python tools/wikigen/verify.py    # integrity + accuracy checks (must report PASS)
```

## ⚖️ Disclaimer

A fan-made, educational community reference. *Lord and Maiden*, its assets, names, and
artwork are the property of their respective developer and publisher. This project is not
affiliated with or endorsed by them, and contains no game assets — only factual data
(stats and tables) compiled for player reference.
