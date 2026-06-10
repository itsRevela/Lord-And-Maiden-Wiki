# The Great World (Map & Regions)

The **Great World** (also called the "Big World") is the single shared map every player on a server inhabits, outside their own city. It unlocks once your **main keep reaches level 6**, and you toggle between your City and the Great World from the main screen.

## World vs Region
These are **not** the same thing:

- The **Great World** is the entire shared map — a fixed **193 × 193 grid** (plus a special expansion block).
- A **Region** is a single **grid cell** of that map (about 20.5 world units across). It is an internal map/streaming unit, **not** a named area.
- The **"nine-square grid"** in the occupation rules is just the **3 × 3 block of regions** around a point.

So the world is *divided into* regions; a region is one tile of the world.

## What's on the map
The static map is built from ~119,353 object placements:

| Object | Tiles on map |
|---|---|
| Farm | 29,640 |
| Sawmill | 29,608 |
| Iron Mine | 29,511 |
| Quarry | 29,223 |
| Meteoric Iron Mine | 1,280 |
| NPC City / Village | 73 |
| World Boss | 9 |
| Mine (special) | 9 |

Resource nodes (Farm / Sawmill / Quarry / Iron Mine) make up the bulk; **73 NPC Cities/Villages** are the siege targets, **9 World Bosses** and special **Mines** are scattered about, and a mine flagged as a **Core Mine** grants a **Sphere of Influence** when held. For each occupiable target's levels, rewards and defenders see [World Map Objects](World-Map.md); for NPC cities see [NPC Cities](NPC-Cities.md); for player-built structures see [World & Naval Structures](World-Structures.md); for wilderness nodes and treasure boxes see [Wilderness & World Boxes](Wild-Exploration.md).

## Occupation & siege rules
- You can occupy any target in the **nine-square grid** around your main city.
- Holding a **Core Mine** grants a **Sphere of Influence**; the grids adjacent to your sphere then become occupiable — this is how you expand across the map.
- Occupied mines give passive resource income for a limited time; the **Transport Station** raises how long and how many you can hold at once.
- After all defenders are beaten, the target belongs to the **first war-declarer** (whose allies may assist). A city left **offline 14+ days** is randomly relocated.
- **Siege battles** (capturing NPC cities) are **Union-only**: an ally's Sphere must border the target, you must beat all defenders **and break the walls with Chariots**, and city ownership resets on the **1st of each month**. See [Territory Wars & Raids](../Alliance/Territory-Wars-and-Raids.md).

*(The in-game rule pop-ups are images; the authoritative text is on [Game Tips](../Reference/Tips.md) under "Great World" and "Siege Battle".)*

---
*Auto-generated from game data by `tools/wikigen/build.py`. Do not edit by hand.*
