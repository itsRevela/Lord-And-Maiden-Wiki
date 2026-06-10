"""Generate data/sim/heroes.json + data/sim/portraits.json from the game CSVs.

HARD RULES obeyed:
- All CSVs parsed via resolver.load() => csv.DictReader + encoding='utf-8-sig'.
- No CJK printed to stdout; everything CJK-bearing is written to the UTF-8 JSON files.
- Every value is read from a CSV cell, a resolver helper, or a cited decompiled
  line; nothing is invented. Server-resolved gaps are marked 'UNKNOWN_SERVER_SIDE'.
- json.dump(..., ensure_ascii=False, indent=2).

Cross-checked against:
  wiki/Heroes/Hero-Leaderboards.md   (Lv80 stat numbers -> confirm level arg)
  wiki/Heroes/Heroes.md              (roster, races, archetypes, skills)
  data/sim/troops_meta.json          (RST / restraint / preferred-soldier already decoded)

Decompiled cites (decompiled/Assembly-CSharp/eb46ed1b3cbb.decompiled.cs):
  2701-2760  HeroInfo POCO ([XMLExtension] field map: id/type/rare/RST/RPoint/...).
  9744-9792  GetHeroHeadImg -> portrait asset path scheme (icon based).
  10428      aiHero.SoldierT = heroInfo.RST  (RST = commanded soldier type).
  10435-10477 + 80853-80918  RPoint usage: free stat-point distribution preset.
  9794-9830  AIIsBoss (HeroNum >= 1000 => AI/enemy unit ranges).
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools", "wikigen"))
from resolver import (Resolver, load, SOLDIER_TYPE, RST_ARCHETYPE,
                      SKILL_TYPE_NAME, RACE_NAME, HERO_ROLE, HERO_MAX_LEVEL,
                      HERO_CARDS)

R = Resolver()
OUT_HEROES = os.path.join(ROOT, "data", "sim", "heroes.json")
OUT_PORTRAITS = os.path.join(ROOT, "data", "sim", "portraits.json")

# PointItem ID -> stat, from RePoint() (decompiled:80873-80889): 0=ATK 1=DEF 2=Ruin 3=Speed.
RPOINT_STATS = ["attack", "defense", "ruin", "speed"]


def parse_rpoint(s):
    """RPoint = 4 comma-separated floats: free stat-point allocation preset
    [ATK, DEF, Ruin, Speed]. All-zero => game uses the RST default split.
    Read verbatim; if a token is non-numeric leave it as the raw string."""
    parts = (s or "").split(",")
    vals = []
    for p in parts:
        p = p.strip()
        try:
            vals.append(float(p))
        except ValueError:
            vals.append(None)
    # pad/truncate to 4
    vals = (vals + [0.0, 0.0, 0.0, 0.0])[:4]
    return vals


def rpoint_split(vals, rst):
    """Mirror the client's stat-point distribution logic (decompiled:10452-10477
    & 80871-80918). Returns the per-stat fraction the 'Recommend/Reset' button
    assigns, expressed as {stat: fraction}. Speed (index 3) takes the remainder
    when an explicit preset is used. When the preset is all-zero, the fallback is
    keyed off RST. This is purely a UI convenience preset for distributing the
    hero's free points (ReMainPoint); it grants no stats by itself."""
    nonzero = any(v not in (0.0, None) for v in vals)
    if nonzero:
        atk = vals[0] or 0.0
        df = vals[1] or 0.0
        ru = vals[2] or 0.0
        sp = max(0.0, 1.0 - (atk + df + ru))   # remainder, like Add_Sp = num4 - others
        return {"mode": "explicit_preset",
                "attack": atk, "defense": df, "ruin": ru, "speed": round(sp, 6)}
    # all-zero -> RST fallback (decompiled:10459-10477, 80892-80916)
    if rst == 1:      # Infantry: 60% DEF, remainder Speed
        return {"mode": "rst_fallback", "attack": 0.0, "defense": 0.6,
                "ruin": 0.0, "speed": 0.4}
    if rst == 2:      # Archer: 80% ATK, remainder Ruin
        return {"mode": "rst_fallback", "attack": 0.8, "defense": 0.0,
                "ruin": 0.2, "speed": 0.0}
    if rst == 3:      # Cavalry: 60% DEF, remainder ATK
        return {"mode": "rst_fallback", "attack": 0.4, "defense": 0.6,
                "ruin": 0.0, "speed": 0.0}
    if rst == 4:      # Chariot: 60% Ruin, remainder ATK
        return {"mode": "rst_fallback", "attack": 0.4, "defense": 0.0,
                "ruin": 0.6, "speed": 0.0}
    return {"mode": "none", "attack": 0.0, "defense": 0.0,
            "ruin": 0.0, "speed": 0.0}


def classify(row):
    """Classify a HeroInfo row into (is_named_hero, playable, category, reason).

    is_named_hero follows resolver.is_named_hero (in HeroDes, not a card). playable
    is the simulator-selectable flag: named heroes are playable EXCEPT the 'Unknown'
    placeholder heroes (41-45), which are in HeroDes but are tutorial/filler shells
    (uniform 28/28/28/28 base, 0.7 grow) and are tagged playable:false per task."""
    hid = row["id"]
    name_en = (row["name_en"] or "").strip()
    low = name_en.lower()
    if hid in HERO_CARDS:
        return (False, False, "card",
                "HeroDes 'card' item (advancement/codex/skill/breakthrough), not a hero")
    if R.is_named_hero(hid):
        if "unknown" in low or "test" in low:
            return (True, False, "filler",
                    "in HeroDes but a placeholder/filler shell (name contains "
                    "Unknown/test, uniform stats) - not selectable in the simulator")
        return (True, True, "named_hero", "in HeroDes; real recruitable hero")
    # not a named hero. id>=1000 => AI/enemy unit.
    iid = int(hid)
    if iid >= 1000:
        return (False, False, "ai_unit",
                "HeroNum >= 1000 = AI/enemy formation unit (decompiled:9794 AIIsBoss)")
    if "unknown" in low or "test" in low:
        return (False, False, "filler",
                "placeholder/filler hero (name contains Unknown/test), not in HeroDes")
    return (False, False, "non_hero", "not in HeroDes and not an AI/card row")


def build_hero(row):
    hid = row["id"]
    is_named, playable, category, reason = classify(row)

    base = {k: int(row[k]) for k in ("attack", "defense", "ruin", "speed")}
    grow = {("%s_grow" % k): float(row["%s_grow" % k])
            for k in ("attack", "defense", "ruin", "speed")}
    # Lv80 stats: hero_stat_at(base, grow, level) with level=HERO_MAX_LEVEL (=80).
    # CONFIRMED: level=80 reproduces wiki/Heroes/Hero-Leaderboards.md exactly
    # (e.g. Saintess Shin ATK 44 + floor(1.1*80)=132); level=79 would give 130.
    maxed = {
        "attack": R.hero_stat_at(row["attack"], row["attack_grow"], HERO_MAX_LEVEL),
        "defense": R.hero_stat_at(row["defense"], row["defense_grow"], HERO_MAX_LEVEL),
        "ruin": R.hero_stat_at(row["ruin"], row["ruin_grow"], HERO_MAX_LEVEL),
        "speed": R.hero_stat_at(row["speed"], row["speed_grow"], HERO_MAX_LEVEL),
    }

    rst = int(row["RST"]) if row["RST"].strip().lstrip("-").isdigit() else 0
    rpoint_vals = parse_rpoint(row["RPoint"])

    def skref(st, sid):
        st, sid = (st or "0").strip(), (sid or "0").strip()
        if st == "0" and sid == "0":
            return None
        return {"st": int(st), "st_name": SKILL_TYPE_NAME.get(st, "—"),
                "id": int(sid), "key": "%s.%s" % (st, sid),
                "name_en": R.skill_name(st, sid)}

    main_skill = skref(row["skill0_type"], row["skill0_id"])
    modular = [s for s in (skref(row["skill1_type"], row["skill1_id"]),
                           skref(row["skill2_type"], row["skill2_id"])) if s]

    race_id = row["type"].strip()
    hero = {
        "id": int(hid),
        "name_en": R.hero_name(hid),
        "name_raw": row["name"],
        "is_named_hero": is_named,
        "playable": playable,
        "category": category,
        "category_reason": reason,
        "race": {"id": int(race_id) if race_id.isdigit() else race_id,
                 "name_en": RACE_NAME.get(race_id, "—")},
        "star": int(row["rare"]),
        "rst": {"id": rst, "soldier_type_en": SOLDIER_TYPE.get(str(rst), "—"),
                "archetype_en": RST_ARCHETYPE.get(str(rst), "—")},
        "role": {"id": (R.herodes.get(hid, {}) or {}).get("HeroJob")
                 if is_named else None,
                 "name_en": R.hero_role(hid) if is_named else "—"},
        "icon": int(row["icon"]) if row["icon"].strip().isdigit() else row["icon"],
        "base": base,
        "grow": grow,
        "maxed_lv80": maxed,
        "maxed_lv80_total": sum(maxed.values()),
        "main_skill": main_skill,
        "modular_default": modular,
        "rpoint": {
            "raw": row["RPoint"],
            "values": rpoint_vals,
            "_meaning": "Free stat-point allocation preset [ATK,DEF,Ruin,Speed] used "
                        "by the hero's point Reset/Recommend button (decompiled "
                        "RePoint 80853-80918; AI Add_* 10437-10477). NOT extra stats; "
                        "just the default distribution of ReMainPoint. All-zero => RST "
                        "fallback split.",
            "distribution": rpoint_split(rpoint_vals, rst),
        },
    }
    return hero, category


def build_portraits(rows):
    """Per hero id -> portrait asset references.

    Asset path scheme from GetHeroHeadImg (decompiled:9744-9792). All paths are
    YooAsset *logical* addresses passed to LoadAssetSync<Sprite>(); the actual
    sprites live inside the game's UnityFS bundles, keyed by hero ICON (not id):
      full head  : "Hero/{icon}/Head_{icon}_{skinId}"
      chibi head : "PlayerHead_Q/QHead_{icon}_{skinId}"
    skinId 0 = default skin. HeadImg>10000 selects an alternate skin via
    num=HeadImg/10000 (i.e. logical "Head_{icon}_{num}").

    Cross-ref HeroPosInfo.csv: keyed by HeroIcon (== HeroInfo.icon), holds the
    on-screen layout for the big portrait (posx/posy/size/effect anchors), not an
    image filename. We attach its row for completeness.
    """
    pos_by_icon = {}
    for r in load("HeroPosInfo"):
        pos_by_icon.setdefault(r["HeroIcon"], r)   # first row per icon

    portraits = {}
    for row in rows:
        hid = row["id"]
        icon = row["icon"].strip()
        pos = pos_by_icon.get(icon)
        portraits[hid] = {
            "id": int(hid),
            "name_en": R.hero_name(hid),
            "icon": int(icon) if icon.isdigit() else icon,
            "asset_refs": {
                "head_full": "Hero/%s/Head_%s_0" % (icon, icon),
                "head_chibi": "PlayerHead_Q/QHead_%s_0" % icon,
                "head_full_skin_template": "Hero/%s/Head_%s_{skinId}" % (icon, icon),
                "head_chibi_skin_template": "PlayerHead_Q/QHead_%s_{skinId}" % icon,
            },
            "pos_info": ({
                "skin_id": int(pos["SkinId"]),
                "posx": int(pos["posx"]), "posy": int(pos["posy"]),
                "size": pos["size"],
                "effect_pos1": pos["EffectPos1"], "effect_pos2": pos["EffectPos2"],
                "enjoy_pos": pos["EnjoyPos"], "on_click": pos["OnClick"],
                "_source": "data/csv/HeroPosInfo.csv (keyed by HeroIcon)",
            } if pos else None),
        }
    return portraits


def main():
    rows = load("HeroInfo")
    heroes = []
    counts = {}
    for row in rows:
        hero, cat = build_hero(row)
        heroes.append(hero)
        counts[cat] = counts.get(cat, 0) + 1
    heroes.sort(key=lambda h: h["id"])

    named = [h for h in heroes if h["is_named_hero"]]

    doc = {
        "_about": "Hero roster for the Lord & Maiden battle simulator. Every "
                  "HeroInfo.csv row is included and tagged. 'is_named_hero' = real "
                  "recruitable hero (present in HeroDes, excluding the 4 card items "
                  "{81,82,83,102}). 'playable' heroes are the simulator's selectable "
                  "roster; AI/enemy units (id>=1000), card items, and 'Unknown' "
                  "filler rows are tagged playable:false.",
        "_source": "data/csv/HeroInfo.csv (DictReader, utf-8-sig). Names via "
                   "resolver.hero_name/skill_name; role via resolver.hero_role.",
        "_stat_model": {
            "formula": "stat(L) = base + floor(grow * L)",
            "max_level": HERO_MAX_LEVEL,
            "maxed_lv80_level_arg": HERO_MAX_LEVEL,
            "_confirmed": "Lv80 stats use level=80 (NOT 79). Verified against "
                          "wiki/Heroes/Hero-Leaderboards.md: it is generated with "
                          "R.hero_stat_at(base, grow, HERO_MAX_LEVEL) and the published "
                          "numbers match level=80 exactly (e.g. Saintess Shin ATK "
                          "44+floor(1.1*80)=132). level=79 would give 130 (no match).",
            "_note": "These are bare growth-curve stats. They EXCLUDE freely-assigned "
                     "stat points (RPoint preset / breakthrough points), talents, gear, "
                     "relics, runes, affection and team-comp bonuses. Final combat power "
                     "and damage are resolved server-side (UNKNOWN_SERVER_SIDE).",
        },
        "enums": {
            "race": dict(RACE_NAME),
            "soldier_type_rst": dict(SOLDIER_TYPE),
            "rst_archetype": dict(RST_ARCHETYPE),
            "skill_type": dict(SKILL_TYPE_NAME),
            "role": dict(HERO_ROLE),
        },
        "rpoint_explained": {
            "field": "HeroInfo.RPoint = 4 comma-separated floats",
            "meaning": "Per-stat fraction preset [ATK, DEF, Ruin, Speed] for "
                       "auto-distributing the hero's FREE stat points (ReMainPoint = "
                       "advancement+level+breakthrough points). It is the value behind "
                       "the in-hero 'Reset/Recommend points' button.",
            "stat_index_map": {str(i): RPOINT_STATS[i] for i in range(4)},
            "logic": "If any value != 0: assign ReMainPoint*frac to ATK/DEF/Ruin and "
                     "give Speed the remainder (decompiled RePoint 80871-80889; AI "
                     "Add_* 10452-10457). If all zero: fall back to an RST-keyed default "
                     "(decompiled 80892-80916): RST1 60%DEF/rest Speed, RST2 80%ATK/rest "
                     "Ruin, RST3 60%DEF/rest ATK, RST4 60%Ruin/rest ATK.",
            "is_per_soldier_split": "Partly: it is NOT a per-soldier-type stat split and "
                                    "NOT an adaptation/restraint value. It is a free-point "
                                    "allocation recommendation. Its all-zero fallback is "
                                    "keyed off RST, which is the only link to soldier type.",
            "grants_extra_stats": False,
            "rst_fielding_bonus": "No. A hero gains NO inherent extra stats merely for "
                                  "fielding its RST-matching soldier type. RST sets which "
                                  "single soldier type the hero commands (hero.SoldierT = "
                                  "heroInfo.RST, decompiled:10428) and seeds the empty-"
                                  "RPoint default split. The real soldier-type payoff is "
                                  "TEAM-level: 2/3 heroes sharing a soldier type trigger "
                                  "the Basic/Advanced soldier combinations in "
                                  "data/sim/troops_meta.json (soldier_combinations). The "
                                  "soldier restraint triangle (-25% to restrained "
                                  "soldiers) is a stated rule applied server-side "
                                  "(UNKNOWN_SERVER_SIDE) - see troops_meta.json.restraint.",
            "source": "decompiled/Assembly-CSharp/eb46ed1b3cbb.decompiled.cs "
                      "10437-10477 (AI build) and 80853-80918 (player UI RePoint).",
        },
        "counts": {
            "total_rows": len(heroes),
            "named_heroes": len(named),
            "playable": sum(1 for h in heroes if h["playable"]),
            "by_category": counts,
        },
        "heroes": heroes,
    }

    portraits_map = build_portraits(rows)
    portraits_doc = {
        "_about": "Per hero id -> portrait/head sprite asset references for the "
                  "Lord & Maiden simulator. Paths are YooAsset logical addresses "
                  "(LoadAssetSync<Sprite>), keyed by HeroInfo.icon, NOT plain files "
                  "on disk yet.",
        "_asset_scheme": {
            "source": "GetHeroHeadImg decompiled:9744-9792",
            "full_head": "Hero/{icon}/Head_{icon}_{skinId}",
            "chibi_head": "PlayerHead_Q/QHead_{icon}_{skinId}",
            "skin_id_default": 0,
            "alt_skin": "HeadImg>10000 picks skin num=HeadImg/10000 -> Head_{icon}_{num}",
            "key_is_icon": "icon == HeroInfo.icon (often == id, but use icon).",
        },
        "_extraction_status": {
            "plain_files_present": False,
            "where_they_live": "Inside the game's YooAsset UnityFS bundles at "
                               "<LAM install>/Lord and Maiden_Data/StreamingAssets/yoo/"
                               "DefaultPackage/*.bundle (1278 plain UnityFS bundles, "
                               "unencrypted - see notes/01-recon-and-encryption.md).",
            "repo_extracted_dir": "extracted/bundles_assets/ exists but is EMPTY - only "
                                  "the XML config TextAssets were extracted, not sprites.",
            "to_get_a_portrait": "Open the bundles with UnityPy/AssetStudio and pull the "
                                 "Sprite/Texture2D named 'Head_{icon}_0' (full) or "
                                 "'QHead_{icon}_0' (chibi). No decryption needed.",
            "note": "UNKNOWN until extracted: exact .bundle file containing a given "
                    "icon's sprite (resolve via the YooAsset OOY manifest's "
                    "asset-path -> bundle map).",
        },
        "portraits": portraits_map,
    }

    os.makedirs(os.path.dirname(OUT_HEROES), exist_ok=True)
    with open(OUT_HEROES, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    with open(OUT_PORTRAITS, "w", encoding="utf-8") as f:
        json.dump(portraits_doc, f, ensure_ascii=False, indent=2)

    # ASCII-only confirmation
    print("wrote", OUT_HEROES)
    print("wrote", OUT_PORTRAITS)
    print("rows:", len(heroes), "named:", len(named),
          "playable:", doc["counts"]["playable"])
    print("by_category:", counts)
    # spot-check Saintess Shin (id 2) Lv80 vs wiki (132/192/240/132)
    ss = next(h for h in heroes if h["id"] == 2)
    print("id2 Saintess Shin Lv80:", ss["maxed_lv80"], "total", ss["maxed_lv80_total"])


if __name__ == "__main__":
    main()
