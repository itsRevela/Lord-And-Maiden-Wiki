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


def gen_shops(write, tbl, R):
    rows = load("StoreInfo")
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r["storetype"], []).append(r)
    lines = ["All purchasable goods across the game's shops, grouped by shop. "
             "The currency column doubles as the shop's identity (e.g. Honor Points = Arena shop, "
             "Union Points = Alliance shop).", ""]
    for st, items in sorted(by.items(), key=lambda x: int(x[0])):
        curs = []
        for r in items:
            c = R.prop_name(r["pricetype"])
            if c not in curs:
                curs.append(c)
        lines.append("## Shop %s — %s" % (st, " / ".join(curs)))
        body = [[R.prop_name(r["propId"]), R.prop_name(r["pricetype"]), fmt_num(r["price"]),
                 _dash(r.get("limit")) or "∞", _dash(r.get("NeedLv"))] for r in items]
        lines += tbl(["Item", "Currency", "Price", "Buy Limit", "Unlock Lv"], body)
        lines.append("")
    write("Items/Shops.md", "Shops & Stores", "City & Economy", lines)


def gen_recharge(write, tbl, R):
    rows = load("Pay")
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r.get("gift_type", "0"), []).append(r)
    lines = ["Paid packs and gift bundles. *Price* is the value shown in-game. "
             "Contents are resolved to the items granted.", ""]
    for gt, items in by.items():
        lines.append("## Pack Group %s" % gt)
        body = [[clean(r.get("name_en") or r.get("name")), fmt_num(r.get("price")),
                 _dash(r.get("limit")) or "∞", R.expand_props(r.get("content"))] for r in items]
        lines += tbl(["Pack", "Price", "Limit", "Contents"], body)
        lines.append("")
    write("Items/Recharge-Packs.md", "Recharge & Gift Packs", "City & Economy", lines)


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
                 _dash(r.get("MaxPlayerCt")), _dash(r.get("DayMaxCt")) or "∞",
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
    lines = ["Purchasable hero skins. Each skin also grants a small permanent stat bonus.", ""]
    body = [[R.hero_name(r["HeroNum"]), r.get("SkinId", ""), fmt_num(r.get("Price")),
             clean(R.resolve_tokens(r.get("Effects_en") or r.get("Effects")))] for r in rows]
    lines += tbl(["Hero", "Skin", "Price (Gems)", "Bonus"], body)
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
        "- **[Crafting](Crafting/Formulas.md)**, **[Shops](Items/Shops.md)**, **[Item Sources](Items/Item-Sources.md)**.",
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
                  "**[Shops](Items/Shops.md)** and **[Recharge Packs](Items/Recharge-Packs.md)**):", ""]
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
                     "T": a + d + ru, "role": R.hero_role(h["id"])})
    lines = ["End-game (Lv %d) computed stats for every named hero, using "
             "`stat(80) = base + floor(growth × 80)`. Speed is a turn-order stat and is listed "
             "separately from the offensive/defensive total. Use this to compare heroes at the "
             "level cap." % HERO_MAX_LEVEL, ""]
    # top tables per stat
    for key, label in [("A", "Attack"), ("D", "Defense"), ("R", "Ruin"), ("T", "ATK+DEF+Ruin Total")]:
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
def register(write, tbl, R):
    gen_overview(write, tbl, R)
    gen_hero_leaderboards(write, tbl, R)
    gen_cumulative_costs(write, tbl, R)
    gen_feature_unlocks(write, tbl, R)
    gen_building_unlocks(write, tbl, R)
    gen_item_sources(write, tbl, R)
    gen_shops(write, tbl, R)
    gen_recharge(write, tbl, R)
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
