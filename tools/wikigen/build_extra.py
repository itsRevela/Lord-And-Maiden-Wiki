"""Extra wiki generators (kept out of build.py to respect file-size limits).

Covers the configs build.py does not: economy/monetization, item sources,
progression unlock gates, PvE dungeons, world structures, hero skins, dating
events, reward boxes and cosmetic reference tables.

`register(write, tbl, R)` is called from build.main() with the shared page
writer, table helper and resolver instance, so every page lands in the same
table-of-contents (build.PAGES) as the core generators.
"""
import re
import collections

from resolver import (load, fmt_num, clean, secs, SOLDIER_TYPE,
                      RACE_NAME, RST_ARCHETYPE, HERO_MAX_LEVEL)


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "x"


def _dash(v, zero=("0", "", "0_0")):
    v = (v or "").strip()
    return "—" if v in zero else v


def _limit(v):
    """A purchase/run limit where 0 (or blank) means unlimited."""
    v = (v or "").strip()
    return "∞" if v in ("0", "") else v


# Translation tables for source columns the game ships only in Chinese.
# (Verified term-by-term; the strings are fully compositional.)
_ACDK_TR = [
    ("上半月", "1st Half"), ("下半月", "2nd Half"),
    ("七夕节", "Qixi Festival"), ("中秋节", "Mid-Autumn Festival"),
    ("元宵节", "Lantern Festival"), ("元旦", "New Year's Day"),
    ("劳动节", "Labor Day"), ("国庆节", "National Day"),
    ("圣诞节", "Christmas"), ("春节", "Spring Festival"),
    ("清明节", "Qingming Festival"), ("端午节", "Dragon Boat Festival"),
    ("除夕", "New Year's Eve"),
    ("玩家社区发帖", "Player Community Post"),
    ("社区回复点赞官方帖", "Community Like Official Post"),
    ("加群", "Join Group"), ("好评", "Positive Review"),
    ("开服", "Server Launch"), ("渠道", "Channel"), ("预约", "Pre-registration"),
    ("礼包码", " Gift Code"), ("专用", "Exclusive"), ("月", "-"),
]
_AIEQUIP_TR = [
    ("弓兵", "Archer "), ("战车", "Chariot "), ("步兵", "Infantry "),
    ("骑兵", "Cavalry "), ("特殊", "Special "), ("通用", "Generic "),
    ("白", "White "), ("绿", "Green "), ("蓝", "Blue "), ("紫", "Purple "), ("橙", "Orange "),
    ("装", "Gear"),
]


def _apply_tr(table, s):
    s = s or ""
    for cn, en in table:
        s = s.replace(cn, en)
    return re.sub(r"\s{2,}", " ", s).strip()


def _tr_acdk(s):
    s = _apply_tr(_ACDK_TR, s).replace("--", "-").replace("(", " (")
    s = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", s)
    s = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", s)
    return re.sub(r"\s{2,}", " ", s).strip().rstrip("-").strip()


def enemy_units(R, s):
    """Condense a multi-wave AI formation to its unique enemy units (for dungeons
    whose formations repeat the same units across 10+ waves)."""
    s = (s or "").strip()
    if not s or s == "0":
        return "—"
    ids = s.partition("_")[0]
    names, seen = [], set()
    for aid in ids.split(","):
        aid = aid.strip()
        row = R.ai.get(aid)
        if not row:
            continue
        for i in (1, 2, 3):
            h = row.get("HeroNum%d" % i, "0")
            if h not in ("0", ""):
                nm = R.hero_name(h)
                if nm not in seen:
                    seen.add(nm)
                    names.append(nm)
    return ", ".join(names) or "—"


def enemy_level(s):
    """First trailing param of an AI formation string is the enemy level."""
    params = (s or "").partition("_")[2]
    lv = params.split("_")[0] if params else ""
    return lv or "—"


def expand_drops(R, s, sep="+"):
    """Weighted-drop list 'pid_count_weight+...' (RelicInfo) -> 'Item xcount'.

    Differs from R.expand_props because each token has a trailing drop weight
    that must not be folded into the count.
    """
    s = (s or "").strip()
    if not s or s == "0":
        return "—"
    out = []
    for tok in s.split(sep):
        parts = tok.split("_")
        if not parts or not parts[0]:
            continue
        pid = parts[0]
        cnt = parts[1] if len(parts) > 1 else "1"
        out.append("%s x%s" % (R.prop_name(pid), fmt_num(cnt)))
    return ", ".join(out)


# --------------------------------------------------------------------------- #
# Progression gates
# --------------------------------------------------------------------------- #
def gen_feature_unlocks(write, tbl, R):
    rows = sorted(load("UnLockFun"), key=lambda r: (R.build_name(r["Buildtype"]), int(r.get("NeedLv") or 0)))
    lines = ["Every game feature/panel and the building level that unlocks it. "
             "Build the listed structure to the required level to open the feature.", ""]
    body = []
    for r in rows:
        bt = (r.get("Buildtype") or "").strip()
        bld = "Special / Event" if bt in ("-1", "0", "") else R.build_name(bt)
        body.append([clean(r.get("funName_en") or r.get("funName")), bld, r.get("NeedLv", "")])
    lines += tbl(["Feature", "Required Building", "Required Lv"], body)
    write("Progression/Feature-Unlocks.md", "Feature Unlock Levels", "Progression", lines)


def gen_building_unlocks(write, tbl, R):
    bu = load("BuildUnLockInfo")
    lines = ["### Buildings unlocked by city progression", "",
             "As the indicated level is reached, the listed buildings become available to construct.", ""]
    body = []
    for r in bu:
        names = []
        for tok in (r.get("unlock") or "").split("+"):
            bid = tok.partition("_")[0].strip()
            if bid:
                names.append(R.build_name(bid))
        body.append([r["lv"], ", ".join(names) or "—"])
    lines += tbl(["Level", "Buildings Unlocked"], body)

    cl = load("CityLvUnlock")
    if cl:
        lines += ["", "### Main city level requirements", "",
                  "Conditions to raise the central city level (NeedAiId = enemy that must be cleared; "
                  "Cloud values are fog-of-war territory tiles).", ""]
        lines += tbl(["City Lv", "Need AI", "Need Cloud", "Unlock Cloud"],
                     [[r["CityLv"], _dash(r["NeedAiId"]), _dash(r["NeedCloud"]), _dash(r["UnlockCloud"])] for r in cl])
    write("Progression/Building-Unlocks.md", "Building & City Unlocks", "Progression", lines)


# --------------------------------------------------------------------------- #
# Items / economy
# --------------------------------------------------------------------------- #
def _pname_or_id(R, pid):
    r = R.prop.get(str(pid).strip())
    return (clean(r.get("name_en") or r.get("name")) or None) if r else None


def _label_ids(R, field):
    """PropSource PropId is an item *group*: single id, comma list, or 'a~b' range.
    Resolve real items to names; show id ranges literally (never a Prop# placeholder).
    """
    field = (field or "").strip()
    if not field:
        return "—"
    out = []
    for part in field.split(","):
        part = part.strip()
        if "~" in part:
            a, _, b = part.partition("~")
            a, b = a.strip(), b.strip()
            try:
                span = int(b) - int(a) + 1
            except ValueError:
                span = 0
            if 0 < span <= 6:
                out.append(", ".join(_pname_or_id(R, i) or str(i) for i in range(int(a), int(b) + 1)))
            else:
                out.append("%s–%s (%s items)" % (_pname_or_id(R, a) or a, _pname_or_id(R, b) or b,
                                                  span if span > 0 else "?"))
        elif part:
            out.append(_pname_or_id(R, part) or part)
    return ", ".join(out)


def gen_item_sources(write, tbl, R):
    rows = load("PropSource")
    lines = ["Where each item (or item family) can be obtained. Sources are taken directly from the "
             "in-game item tooltip's \"Obtain\" routing.", ""]
    body = []
    for r in rows:
        src = clean(r.get("Source_en") or "")
        parts = [p.split("#")[0].strip() for p in src.split("*") if p.strip()]
        parts = [p for p in parts if p]
        body.append([_label_ids(R, r.get("PropId")), " · ".join(parts) or "—"])
    lines += tbl(["Item / Group", "Sources"], body)
    write("Items/Item-Sources.md", "Item Sources (How to Obtain)", "Items", lines)


# Market tabs (MarketPanel StoreType 1-13). Names, refresh and unlock are recovered
# from the decompiled MarketPanel / UnLockFun / localization (see notes). The 4th
# entry is the per-item gate column header, or None when NeedLv is unused (all 0).
_MARKET_TABS = {
    "1":  ("Manor Shop", "Timed restock (server-set countdown)", "Unlocked with the Manor building", None),
    "2":  ("Gem Shop", "Weekly refresh (Mon 00:00)", "Each item is gated by your Adventure / VIP level", "VIP/Adv Lv"),
    "3":  ("Alliance (Union) Shop", "Weekly refresh (Mon 00:00)", "Opened from the Alliance / Union panel", None),
    "4":  ("Friendship Shop", "Weekly refresh (Mon 00:00)", "Unlocked with the Ruins feature", None),
    "5":  ("Honor Shop (Arena)", "Weekly refresh (Mon 00:00)", "Unlocked with the Arena", None),
    "6":  ("Tournament (Courage) Shop", "Monthly refresh (1st 00:00)", "Unlocked with the Tournament", None),
    "7":  ("Festival (Celebration) Shop", "Monthly refresh (1st 00:00)", "Open only during festival events", None),
    "9":  ("Wilderness Store", "No restock — one-time buys", "Each item is gated by your Wilderness gate progress", "Wild Gate"),
    "10": ("Lord Store", "No restock — one-time buys", "Each item is gated by your Lord level", "Lord Lv"),
    "11": ("Life Shop", "Weekly refresh (Mon 00:00)", "Via the Manor / Life feature", None),
    "12": ("Meteoric Iron Store", "Weekly refresh (Mon 00:00)", "From Primordial Continent / Falling Star content", None),
    "13": ("Island Store", "Weekly refresh (Mon 00:00)", "From island / maritime content", None),
}

# Recharge Shop (ShopPanel) gift_type categories + refresh_type reset windows (Pay.csv).
_SHOP_CATEGORIES = {
    "1": "Subscription Cards (Monthly / Luxury / Permanent)",
    "2": "Growth Funds",
    "3": "Adventure Plan & Starter Packs",
    "4": "Gem Bundles",
    "5": "Level & Milestone Gift Packs",
    "6": "Daily & Spree Packs",
    "7": "7-Day Sign-in Specials",
    "8": "Daily Specials",
    "9": "Lucky Wheel Supply Boxes",
    "10": "Lucky Mystery Box Supply Boxes",
    "12": "Return Sign-in",
    "13": "Hero Growth Support Packs",
    "21": "Themed Bundles",
    "31": "Seasonal Sale",
}
_RESET_WINDOW = {"0": "one-time", "1": "subscription", "2": "daily", "3": "weekly", "4": "monthly", "6": "event"}


def gen_market(write, tbl, R):
    """The Market panel (MarketPanel) — spend earned in-game currencies across 13 tabs.
    Distinct from the Shop (recharge packs); see [Shop](Shop.md)."""
    rows = load("StoreInfo")
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r["storetype"], []).append(r)
    lines = [
        "The **Market** is the in-game panel where you spend **earned** currencies (Gems, Honor / "
        "Union / Friendship / Life Points, Courage Voucher, Island Coin, etc.) on items, across 13 "
        "tabs. It is a **separate panel from the [Shop](Shop.md)** (which sells Rand-Coin recharge packs).", "",
        "## How the Market works",
        "- **Restock / refresh:** most tabs restock **weekly (Monday 00:00)**; the Tournament and "
        "Festival tabs restock **monthly (1st)**; the Manor tab restocks on a **server-set timer**; the "
        "**Wilderness Store** and **Lord Store** never restock (one-time purchases).",
        "- **Buy Limit:** the per-item purchase cap; **∞** = unlimited. The limit **resets each restock** "
        "(so a weekly tab's limits refill every Monday); one-time tabs never refill.",
        "- **Unlock gates:** several tabs only appear once their feature is unlocked (Arena, Tournament, "
        "Ruins, Wilderness, etc.). The Gem / Wilderness / Lord tabs also gate **individual items** by a "
        "level (shown in the right-hand column).",
        "- Tapping a currency's **＋** opens where to get more — Gems → the [Shop](Shop.md), Gold Coin → the Farm.", "",
        "> Two Market tabs are **server-driven and not in the static data**, so they aren't listed below: "
        "the **Traveling Merchant** (a randomly-rotating stock with a manual refresh) and a **Kuroland Badge** tab.", "",
    ]
    for st, items in sorted(by.items(), key=lambda x: int(x[0])):
        meta = _MARKET_TABS.get(st)
        name = meta[0] if meta else ("Market Tab %s" % st)
        curs = []
        for r in items:
            c = R.prop_name(r["pricetype"])
            if c not in curs:
                curs.append(c)
        lines.append("## %s" % name)
        if meta:
            lines.append("**Currency:** %s  ·  **Restock:** %s  ·  **Access:** %s" %
                         (" / ".join(curs), meta[1], meta[2]))
        else:
            lines.append("**Currency:** %s" % " / ".join(curs))
        lines.append("")
        gate = meta[3] if meta else None
        headers = ["Item", "Currency", "Price", "Buy Limit"] + ([gate] if gate else [])
        body = []
        for r in items:
            row = [R.prop_name(r["propId"]), R.prop_name(r["pricetype"]), fmt_num(r["price"]),
                   _limit(r.get("limit"))]
            if gate:
                row.append(_dash(r.get("NeedLv")))
            body.append(row)
        lines += tbl(headers, body)
        lines.append("")
    write("Items/Market.md", "Market (Currency Exchange)", "City & Economy", lines)


def gen_shop(write, tbl, R):
    """The Shop panel (ShopPanel) — Rand-Coin recharge & gift packs (Pay.csv).
    Distinct from the [Market](Market.md)."""
    rows = load("Pay")
    by = collections.OrderedDict()
    for r in sorted(rows, key=lambda r: int(r.get("gift_type") or 0)):
        by.setdefault(r.get("gift_type", "0"), []).append(r)
    lines = [
        "The **Shop** is the in-game store for **paid** packs and gift bundles. Prices are in "
        "**Rand Coin** (the premium currency): real money buys Rand Coin in the Recharge panel, and "
        "Rand Coin is then spent on the packs below. It is a **separate panel from the [Market](Market.md)** "
        "(which spends earned currencies). The **Resets** column is how often a pack's purchase limit "
        "refills.", "",
    ]
    for gt, items in by.items():
        lines.append("## %s" % _SHOP_CATEGORIES.get(gt, "Group %s" % gt))
        body = [[clean(r.get("name_en") or r.get("name")), fmt_num(r.get("price")),
                 _RESET_WINDOW.get(r.get("refresh_type"), "—"), _limit(r.get("limit")),
                 R.expand_props(r.get("content"))] for r in items]
        lines += tbl(["Pack", "Price (Rand Coin)", "Resets", "Buy Limit", "Contents"], body)
        lines.append("")
    lines += [
        "## Related shops",
        "Other purchase points in the game, documented on their own pages or driven entirely by the server:", "",
        "- **[Hero Skin Store](../Heroes/Hero-Skins.md)** — buy hero skins with a **Hero Skin Scroll** or "
        "**Rand Coin**; each skin grants a small permanent bonus.",
        "- **[Gift Codes](Gift-Code-Rewards.md)** — redeem developer codes for reward bundles.",
        "- **Lucky Wheel & Lucky Mystery Box** *(time-limited events)* — spin with Lottery Scrolls, then spend "
        "the resulting **Lucky Egg** / **Lucky Crystal** (plus Gems / Rand-Coin pack options) in the event's "
        "exchange shop. Stock is server-driven.",
        "- **Travelogue Merchant** *(world map)* — buy city / fortress **[Travel Notes](Travel-Notes.md)** "
        "collectibles for **Union Points**; per-item daily / weekly / monthly / lifetime limits.",
        "- **Public Square \"Active Store\"** — an event exchange spending **Chinese Rose** (Public Square) or "
        "**Desert Expedition Star** (Desert Expedition minigame).",
    ]
    write("Items/Shop.md", "Shop (Recharge & Gift Packs)", "City & Economy", lines)


def gen_travel_notes(write, tbl, R):
    """The Travelogue Merchant's wares — unique 'Travel Notes' collectibles (PropInfo
    70001-70175) bought with Union Points; each completes a Codex collection set."""
    rows = sorted([r for r in load("PropInfo")
                   if r["id"].isdigit() and 70000 <= int(r["id"]) < 71000],
                  key=lambda r: int(r["id"]))

    def place(r):
        return clean(r.get("name_en") or r.get("name")).replace("-Travel Notes", "").strip()

    lines = [
        "**Travel Notes** are unique collectibles sold by the **Travelogue Merchant** on the world "
        "map (for **Union Points**) — one per world city and per fortress/dungeon you've encountered. "
        "Each is a *Codex Collections* unique item; gathering the listed sets completes the "
        "[Item Collections](../Codex/Item-Collections.md) for permanent bonuses + Power. "
        "All %d are listed below." % len(rows), "",
        "## City Travelogues (%d)" % sum(1 for r in rows if int(r["id"]) < 70100), "",
    ]
    lines += tbl(["ID", "City"], [[r["id"], place(r)] for r in rows if int(r["id"]) < 70100])
    lines += ["", "## Fortress & Dungeon Travelogues (%d)" % sum(1 for r in rows if int(r["id"]) >= 70100), ""]
    lines += tbl(["ID", "Location"], [[r["id"], place(r)] for r in rows if int(r["id"]) >= 70100])
    write("Items/Travel-Notes.md", "Travel Notes (Travelogue Merchant)", "Items", lines)


def gen_choice_chests(write, tbl, R):
    rows = load("SelectProp")
    lines = ["\"Choice\" chests let you pick one (or more) of the listed items when opened.", ""]
    body = [[R.prop_name(r["PropId"]), R.expand_props(r.get("SelectProps"))] for r in rows]
    lines += tbl(["Chest", "Choices"], body)
    write("Items/Choice-Chests.md", "Choice Chests", "Items", lines)


def gen_gift_codes(write, tbl, R):
    rows = load("ACDK")
    lines = ["Reward bundles granted by redeemable gift codes, grouped by code category. "
             "*(The actual redeemable code strings are distributed by the developer and are not "
             "stored in the game files — only the rewards each code category grants are listed here.)*", ""]
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(_tr_acdk(r.get("Name")) or "Code", []).append(r)
    for cat, items in by.items():
        lines.append("## %s" % cat)
        body = [[r["id"], R.expand_props(r.get("Props"))] for r in items]
        lines += tbl(["Entry", "Rewards"], body)
        lines.append("")
    write("Items/Gift-Code-Rewards.md", "Gift Code Rewards", "Items", lines)


# --------------------------------------------------------------------------- #
# PvE & world
# --------------------------------------------------------------------------- #
def gen_relics(write, tbl, R):
    rows = load("RelicInfo")
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r["FbType"], []).append(r)
    lines = ["Relic dungeons (instanced raids). Rewards are weighted random drops; the listed "
             "quantity is the per-drop amount. Multi-player dungeons can be run co-op up to the "
             "listed player cap.", ""]
    for ft, ds in by.items():
        fam = clean(ds[0].get("Name_en") or "").rsplit(" ", 1)[0] or ("Dungeon %s" % ft)
        lines.append("## %s" % fam)
        body = [[clean(r.get("Name_en") or r.get("Name")), _dash(r.get("Cost")),
                 _dash(r.get("MaxPlayerCt")), _limit(r.get("DayMaxCt")),
                 enemy_level(r.get("AiInfo")), enemy_units(R, r.get("AiInfo")),
                 expand_drops(R, r.get("Reward"))] for r in ds]
        lines += tbl(["Dungeon", "Stamina", "Max Players", "Daily Runs", "Enemy Lv", "Enemies", "Rewards"], body)
        lines.append("")
    write("World/Relic-Dungeons.md", "Relic Dungeons", "PvE & World", lines)


def gen_warlord(write, tbl, R):
    rows = load("WarlordChallenge")
    lines = ["The Warlord Challenge — a chain of fixed-formation battles. Each node requires the "
             "listed prior cities to be cleared first.", ""]
    body = []
    for r in rows:
        req = " · ".join("City %s" % c for c in (r.get("fcon") or "").split("_") if c) or "—"
        body.append([r["citynum"], req, enemy_level(r.get("AiInfo")), enemy_units(R, r.get("AiInfo")),
                     R.expand_props(r.get("reward"))])
    lines += tbl(["City", "Requires", "Enemy Lv", "Enemies", "Reward"], body)
    write("World/Warlord-Challenge.md", "Warlord Challenge", "PvE & World", lines)


def gen_npc_cities(write, tbl, R):
    rows = load("SysCityInfo")
    lines = ["Named NPC cities on the world map and their guardian commanders. "
             "Capturing these cities is part of world conquest.", ""]
    body = [[r["CityNum"], clean(r.get("CityName_en") or r.get("CityName")),
             r.get("CityType", ""), clean(r.get("HeroName_en") or r.get("HeroName"))] for r in rows]
    lines += tbl(["#", "City", "Type", "Guardian"], body)
    write("World/NPC-Cities.md", "NPC Cities & Guardians", "PvE & World", lines)


def gen_wild(write, tbl, R):
    lines = ["### Wilderness unlock nodes", "",
             "Story/territory-gated wilderness points: clear the formation to unlock the area and "
             "claim the reward.", ""]
    wu = load("WildUnLockInfo")
    body = [[r["Aiid"], _dash(r.get("Pos")), R.expand_ai(r.get("AiInfo")), R.expand_props(r.get("Awards"))]
            for r in wu]
    lines += tbl(["Node", "Position", "Enemy", "Reward"], body)

    # WildObjPos: hundreds of map coordinates -> summarise by type/level
    wo = load("WildObjPos")
    if wo:
        agg = collections.Counter((r["ObjType"], r["ObjLv"]) for r in wo)
        lines += ["", "### Wild resource objects (map spawns)", "",
                  "Counts of harvestable/occupiable world objects by type and level "
                  "(individual map coordinates omitted).", ""]
        lines += tbl(["Obj Type", "Level", "Count on Map"],
                     [[t, lv, n] for (t, lv), n in sorted(agg.items(), key=lambda x: (int(x[0][0]), int(x[0][1])))])

    # WorldBoxInfo: 500 rows -> group by reward bundle
    wb = load("WorldBoxInfo")
    if wb:
        agg = collections.Counter()
        for r in wb:
            agg[(r["BoxType"], r.get("Awards", ""))] += 1
        lines += ["", "### World treasure boxes", "",
                  "Reward bundles found in world boxes, with how many boxes grant each bundle.", ""]
        lines += tbl(["Box Type", "Reward", "# Boxes"],
                     [[bt, R.expand_props(aw), n] for (bt, aw), n in
                      sorted(agg.items(), key=lambda x: -x[1])])
    write("World/Wild-Exploration.md", "Wilderness & World Boxes", "PvE & World", lines)


def gen_world_structures(write, tbl, R):
    wbld = load("WorldBuild")
    lines = ["### Buildable world structures", "",
             "Camps and siege structures players/alliances can build on the world map.", ""]
    body = [[clean(r.get("Name_en") or r.get("Name")), r.get("Lv", ""), fmt_num(r.get("HP")),
             secs(r.get("BuildTime")), r.get("MaxCount", ""), R.expand_props(r.get("BuildRes"))]
            for r in wbld]
    lines += tbl(["Structure", "Lv", "HP", "Build Time", "Max", "Cost"], body)

    sf = load("SeaFightBuildInfo")
    if sf:
        lines += ["", "### Naval battle structures", ""]
        for r in sf:
            t1 = clean(r.get("title1_en") or r.get("title1"))
            i1 = clean(r.get("info1_en") or r.get("info1"))
            if t1 and t1 != "0":
                lines.append("- **%s** — %s" % (t1, i1))
            t2 = clean(r.get("title2_en") or r.get("title2"))
            i2 = clean(r.get("info2_en") or r.get("info2"))
            if t2 and t2 != "0":
                lines.append("- **%s** — %s" % (t2, i2))
    write("World/World-Structures.md", "World & Naval Structures", "PvE & World", lines)


# --------------------------------------------------------------------------- #
# Heroes
# --------------------------------------------------------------------------- #
def gen_hero_skins(write, tbl, R):
    rows = load("HeroSkin")
    lines = ["Purchasable hero skins. Each skin also grants a small permanent stat bonus. "
             "Skins are bought with **Rand Coin** (the real-money recharge currency) or unlocked "
             "with a **Hero Skin Scroll**; the Price column is the Rand Coin cost.", ""]
    body = [[R.hero_name(r["HeroNum"]), r.get("SkinId", ""), fmt_num(r.get("Price")),
             clean(R.resolve_tokens(r.get("Effects_en") or r.get("Effects")))] for r in rows]
    lines += tbl(["Hero", "Skin", "Price (Rand Coin)", "Bonus"], body)
    write("Heroes/Hero-Skins.md", "Hero Skins", "Heroes & Lord", lines)


# --------------------------------------------------------------------------- #
# Codex / reward boxes
# --------------------------------------------------------------------------- #
def gen_reward_boxes(write, tbl, R):
    lines = []
    ab = load("AnnalsBox")
    if ab:
        lines += ["## Annals Boxes", "",
                  "Milestone reward chests unlocked by reaching a points threshold.", ""]
        lines += tbl(["Box Type", "Box", "Need", "Reward"],
                     [[r["BoxType"], r["BoxId"], fmt_num(r.get("NeedVal")), R.expand_props(r.get("reward"))]
                      for r in ab])
    asx = load("AssessBox")
    if asx:
        lines += ["", "## Assessment Boxes", "",
                  "Rating/assessment reward chests by threshold.", ""]
        lines += tbl(["Box", "Need", "Reward"],
                     [[r["BoxId"], fmt_num(r.get("NeedVal")), R.expand_props(r.get("Props"))] for r in asx])
    mp = load("MainPlotAward")
    if mp:
        lines += ["", "## Main Plot Chapter Rewards", "",
                  "First-clear rewards per story chapter (three escalating enemy formations each).", ""]
        lines += tbl(["Chapter", "Reward", "Enemy (Easy)", "Enemy (Mid)", "Enemy (Hard)"],
                     [[r["chapter"], R.expand_props(r.get("Awards")), R.expand_ai(r.get("AiInfo1")),
                       R.expand_ai(r.get("AiInfo2")), R.expand_ai(r.get("AiInfo3"))] for r in mp])
    write("Codex/Reward-Boxes.md", "Reward Boxes", "Codex & Collections", lines)


# --------------------------------------------------------------------------- #
# Quests & events
# --------------------------------------------------------------------------- #
def gen_minigames(write, tbl, R):
    lines = ["### Lucky-board minigame", "",
             "A weighted board/wheel event. Landing on a tile triggers the event with the listed "
             "relative weight.", ""]
    mj = load("MarioJeux")
    lines += tbl(["Event Type", "Reward", "Weight"],
                 [[r["EventType"], R.expand_props(r.get("Props")), r.get("Weight", "")] for r in mj])
    acc = load("MarioJeuxAccAwards")
    if acc:
        lines += ["", "### Accumulative rewards", "",
                  "Bonus rewards for the cumulative number of rolls/steps taken.", ""]
        lines += tbl(["Count", "Reward"],
                     [[r["AcCount"], R.expand_props(r.get("Props"))] for r in acc])
    write("Quests/Minigames.md", "Minigames", "Quests & Events", lines)


# --------------------------------------------------------------------------- #
# Lore
# --------------------------------------------------------------------------- #
def gen_dating(write, tbl, R):
    rows = load("DatePlot")
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r["DateId"], []).append(r)
    lines = ["Dialogue scripts from the dating/affinity events. Narration is shown in italics; "
             "spoken lines are attributed where the speaker is identifiable.", ""]
    for did, plot in by.items():
        lines.append("## Date Event %s" % did)
        plot = sorted(plot, key=lambda r: int(r.get("plotId") or 0))
        for r in plot:
            txt = clean(r.get("content_en") or "")
            if not txt:
                continue
            sp = (r.get("speaker") or "0").strip()
            if sp not in ("0", "") and sp in R.hero:
                lines.append("**%s:** %s" % (R.hero_name(sp), txt))
            else:
                lines.append("*%s*" % txt)
        lines.append("")
    write("Lore/Dating-Events.md", "Dating Events", "Characters & Lore", lines)


# --------------------------------------------------------------------------- #
# Reference / cosmetics
# --------------------------------------------------------------------------- #
def gen_avatar_frames(write, tbl, R):
    rows = load("HeadBoxEffect")
    lines = ["Avatar frames (head-box effects) and how to obtain them.", ""]
    body = []
    for r in rows:
        lt = r.get("limitTime", "0")
        dur = secs(lt) if lt not in ("0", "") else "Permanent"
        body.append([clean(r.get("Name_en") or r.get("Name")),
                     clean(R.resolve_tokens(r.get("getdes_en") or r.get("getdes"))),
                     _dash(r.get("BuyPrice")), dur])
    lines += tbl(["Frame", "How to Obtain", "Buy Price", "Duration"], body)
    write("Reference/Avatar-Frames.md", "Avatar Frames", "Reference", lines)


def gen_ai_equipment(write, tbl, R):
    rows = load("AiEquip")
    lines = ["Equipment loadouts worn by AI/enemy formations.", ""]
    body = []
    for r in rows:
        gear = [R.prop_name(r["Pos%d" % i]) for i in range(1, 9)
                if r.get("Pos%d" % i, "0") not in ("0", "")]
        body.append([r["AiEquipNum"], _apply_tr(_AIEQUIP_TR, r.get("Des")),
                     _dash(r.get("RecLv")), "★" + str(r.get("Rare", "")), ", ".join(gear) or "—"])
    lines += tbl(["Set", "Description", "Rec. Lv", "Rarity", "Gear"], body)
    write("Reference/AI-Equipment.md", "AI Equipment Sets", "Reference", lines)


def gen_emojis(write, tbl, R):
    rows = load("Emoji")
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r.get("type", "0"), []).append(r)
    lines = ["Chat emojis available in the game, grouped by pack. "
             "(Many emojis are illustrated stickers whose names are not localised.)", ""]
    for t, es in by.items():
        en = [clean(r.get("name_en")) for r in es if clean(r.get("name_en"))]
        label = ", ".join(en) if en else "*(illustrated stickers — names not localised)*"
        lines.append("- **Pack %s** (%d emojis): %s" % (t, len(es), label))
    write("Reference/Emojis.md", "Chat Emojis", "Reference", lines)


# --------------------------------------------------------------------------- #
# Overview / synthesis pages
# --------------------------------------------------------------------------- #
def gen_overview(write, tbl, R):
    lines = [
        "**Lord and Maiden** is a strategy / city-management game: you grow a city of "
        "buildings, recruit and level a roster of named heroes, train four troop types, "
        "research technology, and fight through a PvE campaign, world & alliance bosses, "
        "trials and PvP — solo and in an alliance. Every number on this wiki is extracted "
        "directly from the game's data files.", "",
        "## Core Systems", "",
        "- **[Heroes](Heroes/Heroes.md)** — %d named heroes (max level %d), each with growth "
        "stats, skills, talents and lore. See the **[Lv 80 Leaderboards](Heroes/Hero-Leaderboards.md)** "
        "to compare end-game stats." % (sum(1 for h in load("HeroInfo") if R.is_named_hero(h["id"])), HERO_MAX_LEVEL),
        "- **[Skills](Heroes/Skills.md)** — Strategic / Tactical / Passive / Pursuit, with awaken levels.",
        "- **[City & Buildings](Buildings/Buildings.md)** — per-level costs, times and unlocks.",
        "- **[Soldiers](Soldiers/Soldiers.md)** & **[Troop Combinations](Military/Troop-Combinations.md)** — 4 types, tiered.",
        "- **[Research](Research/Science.md)** & **[Alliance Research](Alliance/Union-Research.md)**.",
        "- **[Crafting](Crafting/Formulas.md)**, **[Market](Items/Market.md)** (currency exchange), "
        "**[Shop](Items/Shop.md)** (recharge), **[Item Sources](Items/Item-Sources.md)**.",
        "- **PvE**: **[Campaign](World/Campaign.md)**, **[Relic Dungeons](World/Relic-Dungeons.md)**, "
        "**[Bosses](World/Bosses.md)**, **[Trials](World/Trials.md)**, **[Warlord Challenge](World/Warlord-Challenge.md)**.",
        "- **Progression**: **[VIP](Progression/VIP.md)**, **[Favorability](Progression/Favorability.md)**, "
        "**[Feature Unlocks](Progression/Feature-Unlocks.md)**.",
        "- **Reference**: **[Stats & Formulas](Mechanics/Stats-and-Formulas.md)** (start here for the math).", "",
    ]
    # currency glossary (the pricetype props used across shops)
    si = load("StoreInfo")
    cur = []
    seen = set()
    for r in sorted(si, key=lambda x: int(x.get("pricetype") or 0)):
        pt = r.get("pricetype")
        if pt and pt not in seen:
            seen.add(pt)
            cur.append([R.prop_name(pt)])
    if cur:
        lines += ["## Currencies", "",
                  "Currencies the game spends across its shops (full price lists in "
                  "the **[Market](Items/Market.md)** and the **[Shop](Items/Shop.md)**):", ""]
        lines += tbl(["Currency"], cur)
        lines.append("")
    # early progression order
    uf = sorted(load("UnLockFun"), key=lambda r: (int(r.get("NeedLv") or 0), r.get("Buildtype") or ""))
    if uf:
        lines += ["## Feature Unlock Order", "",
                  "The sequence features open up as you progress (also on "
                  "**[Feature Unlocks](Progression/Feature-Unlocks.md)**):", ""]
        body = []
        for r in uf:
            bt = (r.get("Buildtype") or "").strip()
            bld = "Special / Event" if bt in ("-1", "0", "") else R.build_name(bt)
            body.append([r.get("NeedLv", ""), clean(r.get("funName_en") or r.get("funName")), bld])
        lines += tbl(["Req. Lv", "Feature", "Building"], body)
    write("Game-Overview.md", "Game Overview & Getting Started", "Overview", lines)


def gen_hero_leaderboards(write, tbl, R):
    heroes = [h for h in load("HeroInfo") if R.is_named_hero(h["id"])]
    rows = []
    for h in heroes:
        a = R.hero_stat_at(h["attack"], h["attack_grow"], HERO_MAX_LEVEL)
        d = R.hero_stat_at(h["defense"], h["defense_grow"], HERO_MAX_LEVEL)
        ru = R.hero_stat_at(h["ruin"], h["ruin_grow"], HERO_MAX_LEVEL)
        sp = R.hero_stat_at(h["speed"], h["speed_grow"], HERO_MAX_LEVEL)
        nm = R.hero_name(h["id"])
        link = "[%s](roster/%s-%s.md)" % (nm, h["id"], _slug(nm))
        rows.append({"h": h, "nm": nm, "link": link, "A": a, "D": d, "R": ru, "S": sp,
                     "T": a + d + ru + sp, "role": R.hero_role(h["id"])})
    lines = ["End-game (Lv %d) computed stats for every named hero, using "
             "`stat(80) = base + floor(growth × 80)`. **Total** is the sum of all four stats "
             "(Attack + Defense + Ruin + Speed). Use this to compare heroes at the "
             "level cap." % HERO_MAX_LEVEL, ""]
    # top tables per stat
    for key, label in [("A", "Attack"), ("D", "Defense"), ("R", "Ruin"), ("S", "Speed"), ("T", "Total Stats")]:
        top = sorted(rows, key=lambda x: -x[key])[:15]
        lines += ["## Top 15 by %s (Lv %d)" % (label, HERO_MAX_LEVEL), ""]
        lines += tbl(["#", "Hero", "★", "Role", label],
                     [[i + 1, r["link"], r["h"]["rare"], r["role"], format(r[key], ",")] for i, r in enumerate(top)])
        lines.append("")
    # full table sorted by total
    lines += ["## All Heroes — Lv %d Stats" % HERO_MAX_LEVEL, ""]
    full = sorted(rows, key=lambda x: -x["T"])
    lines += tbl(["Hero", "★", "Race", "Role", "Archetype", "ATK", "DEF", "Ruin", "Speed", "Total"],
                 [[r["link"], r["h"]["rare"], RACE_NAME.get(r["h"]["type"], r["h"]["type"]), r["role"],
                   RST_ARCHETYPE.get(r["h"]["RST"], r["h"]["RST"]).split(" (")[0],
                   format(r["A"], ","), format(r["D"], ","), format(r["R"], ","),
                   format(r["S"], ","), format(r["T"], ",")]
                  for r in full])
    lines.append("")
    # by role, each ordered by Total
    lines += ["## By Role (Lv %d)" % HERO_MAX_LEVEL, "",
              "Every hero grouped by combat role, ordered by Total stats within each role.", ""]
    by_role = collections.OrderedDict()
    for r in sorted(rows, key=lambda x: -x["T"]):
        by_role.setdefault(r["role"], []).append(r)
    role_order = ["DPS", "Heal", "CC (Control)", "Buff", "Debuff"]
    for role in role_order + [x for x in by_role if x not in role_order]:
        rs = by_role.get(role)
        if not rs:
            continue
        label = "Other / Unspecified" if role in ("—", "") else role
        lines += ["### %s (%d)" % (label, len(rs)), ""]
        lines += tbl(["Hero", "★", "Race", "Archetype", "ATK", "DEF", "Ruin", "Speed", "Total"],
                     [[r["link"], r["h"]["rare"], RACE_NAME.get(r["h"]["type"], r["h"]["type"]),
                       RST_ARCHETYPE.get(r["h"]["RST"], r["h"]["RST"]).split(" (")[0],
                       format(r["A"], ","), format(r["D"], ","), format(r["R"], ","),
                       format(r["S"], ","), format(r["T"], ",")]
                      for r in rs])
        lines.append("")
    write("Heroes/Hero-Leaderboards.md", "Hero Stat Leaderboards (Lv 80)", "Heroes & Lord", lines)


def gen_cumulative_costs(write, tbl, R):
    """Total resources + time to fully max each building and the whole tech tree
    (sum of every per-level cost). Pure summation from BuildNeed / ScienceInfo."""
    def _i(v):
        try:
            return int(float(v or 0))
        except ValueError:
            return 0

    lines = ["Total resources and time to take each system from start to its **maximum level** — "
             "the sum of every per-level cost. Useful for long-term planning. "
             "Times are raw build/research time before any speedups.", ""]

    # buildings
    bn = load("BuildNeed")
    by_b = collections.OrderedDict()
    for r in bn:
        by_b.setdefault(r["id"], []).append(r)
    lines += ["## Buildings — cost to max level", ""]
    body = []
    tot = {k: 0 for k in ("food", "wood", "stone", "iron", "time")}
    for bid, lvls in by_b.items():
        agg = {k: sum(_i(l.get(k)) for l in lvls) for k in tot}
        for k in tot:
            tot[k] += agg[k]
        body.append([R.build_name(bid), max(_i(l["lv"]) for l in lvls),
                      fmt_num(str(agg["food"])), fmt_num(str(agg["wood"])),
                      fmt_num(str(agg["stone"])), fmt_num(str(agg["iron"])), secs(agg["time"])])
    body.append(["**All buildings (total)**", "—",
                 "**%s**" % fmt_num(str(tot["food"])), "**%s**" % fmt_num(str(tot["wood"])),
                 "**%s**" % fmt_num(str(tot["stone"])), "**%s**" % fmt_num(str(tot["iron"])),
                 "**%s**" % secs(tot["time"])])
    lines += tbl(["Building", "Max Lv", "Food", "Wood", "Stone", "Iron", "Total Time"], body)
    lines.append("")

    # research
    sci = load("ScienceInfo")
    by_s = collections.OrderedDict()
    for r in sci:
        by_s.setdefault(r["id"], []).append(r)
    lines += ["## Research — cost to fully complete the tech tree", ""]
    body = []
    tot = {k: 0 for k in ("food", "wood", "stone", "iron", "time")}
    for sid, lvls in by_s.items():
        agg = {k: sum(_i(l.get(k)) for l in lvls) for k in tot}
        for k in tot:
            tot[k] += agg[k]
        nm = clean(lvls[0].get("name_en") or lvls[0].get("name"))
        body.append([nm, max(_i(l["lv"]) for l in lvls),
                      fmt_num(str(agg["food"])), fmt_num(str(agg["wood"])),
                      fmt_num(str(agg["stone"])), fmt_num(str(agg["iron"])), secs(agg["time"])])
    body.append(["**Entire tech tree (total)**", "—",
                 "**%s**" % fmt_num(str(tot["food"])), "**%s**" % fmt_num(str(tot["wood"])),
                 "**%s**" % fmt_num(str(tot["stone"])), "**%s**" % fmt_num(str(tot["iron"])),
                 "**%s**" % secs(tot["time"])])
    lines += tbl(["Tech", "Max Lv", "Food", "Wood", "Stone", "Iron", "Total Time"], body)
    write("Progression/Cumulative-Costs.md", "Cumulative Costs (to Max)", "Progression", lines)


# --------------------------------------------------------------------------- #
# Equipment & glossary
# --------------------------------------------------------------------------- #
_GEAR_SLOT = {"1": "Weapon", "2": "Armor", "3": "Pants", "4": "Helmet",
              "5": "Bracers", "6": "Boots", "7": "Accessory", "8": "Accessory"}


def gen_equipment(write, tbl, R):
    """Player equipment = PropInfo type 3. Effect decodes via the EntryEffect
    attribute catalog; Value is the gear's Power."""
    gear = [r for r in load("PropInfo") if r.get("type") == "3"]
    by_slot = collections.OrderedDict()
    for r in gear:
        by_slot.setdefault(r.get("PosType", "?"), []).append(r)
    lines = ["Player equipment, grouped by slot. Each piece grants the listed attribute bonuses "
             "(decoded against the [Attribute catalog](../Reference/Attributes.md)) and Power. "
             "Rarity runs ★1 (White) → ★6 (Red).", ""]
    for slot in sorted(by_slot, key=lambda x: int(x) if x.isdigit() else 99):
        items = sorted(by_slot[slot], key=lambda r: (int(r.get("rare") or 0), int(r["id"])))
        lines.append("## %s" % _GEAR_SLOT.get(slot, "Slot " + slot))
        body = [[r["id"], clean(r.get("name_en") or r.get("name")), "★" + (r.get("rare") or "?"),
                 R.expand_effects(r.get("Effect")), fmt_num(r.get("Value"))] for r in items]
        lines += tbl(["ID", "Name", "Rarity", "Bonuses", "Power"], body)
        lines.append("")
    write("Items/Equipment.md", "Equipment / Gear", "Items", lines)


def gen_glossary(write, tbl, R):
    sections = [
        ("Stats & hero terms", [
            ("A/D/R/S", "Shorthand for **A**ttack / **D**efense / **R**uin / **S**peed (e.g. the Base and Growth columns on hero pages)."),
            ("ATK / AD", "Attack — the hero/troop's offensive power stat."),
            ("DEF", "Defense — reduces incoming damage."),
            ("Ruin / DES / DMG", "The same destruction/penetration offensive stat: **Ruin** in stat tables, **DES** / **DMG** in skill & buff text, **R** in the leaderboards."),
            ("Speed / SP", "Determines turn order in battle; not part of the offensive/defensive total."),
            ("RST", "A hero's recommended troop type **and** how surplus stat points are auto-allocated when it leads troops (also shown as *Archetype*). See [Stats & Formulas](../Mechanics/Stats-and-Formulas.md)."),
            ("RPoint / Allocable Points", "Free stat points you assign to a hero — 1 per level, +10 per Advance, +3/+5 per Breakthrough (4-star/5-star). Also called *Available Points*."),
            ("Hero role (Job)", "DPS / Heal / CC (Control) / Buff / Debuff — the hero's combat role (the data field is *Job*)."),
            ("Race & same-race bonus", "Heroes are Human / Orc / Elf; a team with 2 same-race heroes gets +3% all stats, 3 same-race gets +5%."),
            ("Awaken", "Levelling a skill to raise its effect; per-level effects are on each hero's page."),
            ("Advance (Adv) Lv", "A hero-advancement level (needs hero dupes); each Advance grants +10 stat points and raises Codex set bonuses."),
            ("Breakthrough", "Once a hero is fully Advanced and at its level cap, a Breakthrough (Breakthrough Card or same-star dupe) raises the cap and grants extra Allocable Points."),
            ("Power", "Overall-strength rating. Total Power = Building + Science + Hero + Skill + Lord + Codex Power (computed server-side); most tables list each source's Power."),
        ]),
        ("Battle & skills", [
            ("Commander", "The lead hero of a 3-unit team; you lose if it loses all its troops, and it is **25% less likely** to be targeted (~20% vs 40% / 40% for the two Strikers)."),
            ("Striker", "The two non-Commander units in a team (each ~40% likely to be targeted)."),
            ("Impasse", "If both Commanders still have troops after the 8 rounds, the fight pauses ~1 minute and you choose to fight again, retreat, or re-engage."),
            ("Troop restraint", "Rock-paper-scissors: Infantry -> Archer -> Cavalry -> Infantry; a restrained troop deals **-25% damage**."),
            ("Level suppression", "Higher-level soldiers deal extra damage to lower-level soldiers (separate from troop restraint)."),
            ("Wound states", "Battle injuries - *Slightly-Wounded* soldiers recover, *Severely-Wounded* need the Hospital, and any over the Hospital cap die."),
            ("Skill types", "**Strategic / Strategy (blue)** fire pre-battle or on a set round; **Tactical (purple)** roll each round; **Passive** are always-on; **Pursuit / Chase** fire after a normal attack. See [Skill Catalog](../Heroes/Skills.md)."),
            ("Impact / Init / +Lv", "Skill-table columns: Impact = base power coefficient; Init = level-1 value; +Lv = gain per awaken level."),
            ("Max Use / Ready Rd", "Skill-table columns: Max Use = uses per battle (0 = unlimited); Ready Rd = first round it can fire (0 = from round 1)."),
            ("Damage / Healing Coefficient", "Effect strength vs a normal attack; **1.00 = one normal attack's** worth."),
            ("\"Affected by X attribute\"", "The skill scales with that stat - roughly **x** per **200** points of it."),
            ("Real damage", "A fixed extra hit based only on troop count + the unit's in-battle Attack; bypasses the normal damage calc."),
            ("Splash", "A normal attack also deals a % of the hit to the other two enemies, ignoring defence."),
            ("Counterattack", "Strikes back at anyone who normal-attacks the unit; once applied it can't be prevented."),
            ("Aid / Assist", "Redirects attacks aimed at allies onto the Aid unit."),
            ("Combo", "The unit makes its normal attack twice in a round."),
            ("Shield", "Absorbs the first instance of damage."),
            ("Status effects", "Disarm, Silence, Vertigo, Chaos, Taunt, Stun, Concentration/Immune, Forbidden Healing, etc. - full list on [Status Effects](../Mechanics/Status-Effects.md)."),
            ("Name aliases", "Data and player guides name some things differently: **Chase = Pursuit**, **Strategy = Strategic**, **Aid = Assist**, **Concentration/Immune = Focused**, **Chaos = \"undifferentiated ATK\"**, **Dispel = \"dissolves beneficial effect\"**, **Role = Job**, **RST = Archetype**."),
            ("Library", "A building that lets you simulate battles."),
        ]),
        ("City, economy & troops", [
            ("Great World", "The shared open world map (resource nodes, world bosses, sieges) - distinct from your own City; many techs boost *Great World* gathering separately."),
            ("Union", "The game's word for a guild / alliance - Union Hall, Union Research, Union Points and Union Camp all belong to it."),
            ("Lord / Lord Level", "Your player avatar (separate from heroes); the Lord levels up via Lord Exp, wears Lord Equipment / Outfits, and has its own talents."),
            ("Reserve Soldiers Capacity", "The maximum total soldiers you can hold in reserve (scales with City Hall level)."),
            ("Number of Troops", "How many separate armies/marches you can send at once (rises with City Hall level, 1 -> 5)."),
            ("Move Spd / Load", "Per-troop stats: Move Spd = world-map march speed; Load = how much resource one soldier carries when gathering."),
            ("Recruit / Cure", "Recruit = train new soldiers (cost + time per soldier); Cure = heal wounded soldiers at the Hospital."),
            ("Queue", "A slot for a simultaneous task - Build, Research, Planting and Make/Manufacturing queues each cap how many of that task run at once."),
            ("Maiden", "An assignable worker NPC (Peasant Woman / Craftsman / Researcher / Angler) placed in a building for output; higher rarity = stronger. See [Maidens](../Characters/Maidens.md)."),
            ("Work Effect / Work Cost", "A Maiden's output (Work Effect) and the upkeep it consumes (Work Cost)."),
            ("Specialty", "The six trade goods (Animal Skin, Silk, Spices, Lindera Tea, Marble, Jewelry) crafted in tiers for maritime trade."),
            ("\"Stuff\"", "In-game term for equipment-crafting raw materials (Tungsten Gold, Light Silk, Leather, etc.)."),
            ("Vit / Vitality", "Energy for Great World actions (base cap ~1,500, +1 every 60s); refilled by Vit Potions. Distinct from a dungeon's Stamina cost."),
            ("Stamina / Cost", "The action-point cost to run a dungeon or activity."),
        ]),
        ("Progression & collections", [
            ("VIP", "Spending-based account tier granting cumulative buffs and daily bonuses. See [VIP](../Progression/VIP.md)."),
            ("Favorability / GoodFeel", "Hero affinity track granting a global all-hero stat bonus (up to +30 all stats). See [Favorability](../Progression/Favorability.md)."),
            ("Prestige", "An account track: **Prestige level** grants escalating daily gifts + passive stat bonuses; **Prestige Points** (from raiding Barbarian Camps) govern refugee recruitment. See [Player Systems](../Progression/Player-Systems.md)."),
            ("Title / Astral Badges", "Astral Badges (from Barbarian Towers / World Bosses) raise your **Title** - which buffs troop stats - and are spent in the Title Shop."),
            ("Troop Exoskeleton", "Cosmetic troop armour (bought for gems) upgraded with gold + Hearts to add a troop's weaker secondary stats."),
            ("Style / Charm", "A level track whose milestones grant city-output and soldier bonuses. See [Style](../Progression/Style.md)."),
            ("Lord Outfit / Fashion", "Cosmetic Lord outfit sets (Headwear + Clothing + Accessory); only one set's stats are active at a time, but Fashion Points from all owned sets stack into a ranking. See [Lord Outfits](../Progression/Lord-Outfits.md)."),
            ("Set bonus", "The permanent stat bonus (+ Power) from completing a Codex collection; hero-codex bonuses scale with Advance level."),
            ("Relic", "A summonable companion/unit type (via Relic Summon Scrolls), separate from heroes."),
            ("Magic Messenger", "A summonable pet/companion that grants hero ATK / DEF / DES and attack-speed bonuses."),
            ("Cloud", "Fog-of-war world-map territory tiles (referenced by city / wilderness unlock requirements)."),
        ]),
        ("PvE, World & Alliance", [
            ("Relic Dungeon", "Instanced co-op raids (Goblin Ruins, Abyss, etc.) with weighted random drops, a stamina cost and a player cap. See [Relic Dungeons](../World/Relic-Dungeons.md)."),
            ("World Boss / Alliance Boss", "Open-world bosses with multi-wave formations - solo (World Boss) or guild co-op (Alliance Boss, more waves)."),
            ("Barbarian Tower / Camp / Fortress", "World-map PvE enemy sites you raid for resources, EXP, Astral Badges and Prestige Points."),
            ("Trials (Assess)", "Sequential fixed-formation fights with a troop cap; score thresholds grant Trials Credentials."),
            ("Warlord Challenge", "A chain of fixed-formation battles vs NPC cities, each gated behind clearing earlier ones."),
            ("Territory tiers", "Guild-war territories, low -> high: **Toll Gate** -> **Small City** -> **Big City** -> **Chronos**; each needs the tier below and has more end-fort Lords. See [Territory Wars](../Alliance/Territory-Wars-and-Raids.md)."),
            ("Raid vs War", "Same fight; **Wars** run at fixed times Fri-Sun, **Raids** can be started by the guild any time Mon-Thu."),
            ("Integral", "Your participation score in a war; 10,000+ qualifies for the Winning / Failure reward."),
            ("League Points", "Guild currency (from member donations) spent to register for a war territory."),
            ("First Clear", "A one-time reward for the first clear of a stage / territory (war first-clears are mailed to the whole guild)."),
            ("Fort / Siege", "The defended strongpoint in a war (a gauntlet of teams); Siege troops can bombard it directly from nearby."),
            ("Sphere of Influence", "The occupiable zone gained by holding a Core Mine; the **nine-square grid** around your city/sphere is what you can occupy or (with an allied border) siege."),
            ("\"Lv/params\" (e.g. `15_0.8_1.0`)", "Enemy-formation suffix: the first number is the enemy **level**; the rest are stat-scaling multipliers."),
        ]),
    ]
    lines = ["A reference for the recurring terms, stat abbreviations and game-specific jargon used "
             "across this wiki, grouped by topic. Combat keywords are defined in full on "
             "[Battle Mechanics](../Mechanics/Battle-Mechanics.md) and [Status Effects](../Mechanics/Status-Effects.md).", ""]
    for title, terms in sections:
        lines.append("## %s" % title)
        lines += tbl(["Term", "Meaning"], [[t, d] for t, d in sorted(terms, key=lambda x: x[0].lower())])
        lines.append("")
    lines.append("## Currencies")
    lines.append("What each currency is for (earned currencies are spent in the "
                 "[Market](../Items/Market.md); Rand Coin in the [Shop](../Items/Shop.md)):")
    lines.append("")
    lines += tbl(["Currency", "Use / source"], [
        ["Gems", "Premium currency - summons, shop, speedups."],
        ["Gold Coin", "Basic soft currency - crafting and the general store."],
        ["Speedup Points", "Shorten build / research timers (5 min each)."],
        ["Honor Points", "Arena / PvP exchange currency (Honor shop)."],
        ["Union Points", "Alliance-shop currency (from Union help / donate / siege)."],
        ["Friendship Points", "Friend/social exchange currency."],
        ["Life Points", "From Manor planting & Knowledge Quiz; spent in the Life shop."],
        ["Courage Voucher", "Tournament exchange currency."],
        ["Island Coin", "Island / maritime content currency."],
        ["Meteoric Iron Mine", "From Primordial / Falling Star content; buys premium crafting materials."],
        ["Celebration Badge", "Event exchange currency."],
        ["Intelligence Points", "From Hero Dispatch; an exchange currency."],
        ["Adventurer Points", "Raise your Adventure Level (granted by most packs)."],
        ["Astral Badges", "Raise your Title (Title shop)."],
        ["Lord Exp", "Levels up your Lord."],
        ["Vit (Vitality)", "Energy spent on Great World (world-map) actions."],
    ])
    write("Reference/Glossary.md", "Glossary", "Reference", lines)


# --------------------------------------------------------------------------- #
def register(write, tbl, R):
    gen_overview(write, tbl, R)
    gen_hero_leaderboards(write, tbl, R)
    gen_cumulative_costs(write, tbl, R)
    gen_equipment(write, tbl, R)
    gen_glossary(write, tbl, R)
    gen_feature_unlocks(write, tbl, R)
    gen_building_unlocks(write, tbl, R)
    gen_item_sources(write, tbl, R)
    gen_market(write, tbl, R)
    gen_shop(write, tbl, R)
    gen_travel_notes(write, tbl, R)
    gen_choice_chests(write, tbl, R)
    gen_gift_codes(write, tbl, R)
    gen_relics(write, tbl, R)
    gen_warlord(write, tbl, R)
    gen_npc_cities(write, tbl, R)
    gen_wild(write, tbl, R)
    gen_world_structures(write, tbl, R)
    gen_hero_skins(write, tbl, R)
    gen_reward_boxes(write, tbl, R)
    gen_minigames(write, tbl, R)
    gen_dating(write, tbl, R)
    gen_avatar_frames(write, tbl, R)
    gen_ai_equipment(write, tbl, R)
    gen_emojis(write, tbl, R)
