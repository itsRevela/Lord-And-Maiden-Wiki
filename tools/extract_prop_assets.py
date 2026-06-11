"""Extract item (prop) icons and the rarity backdrop textures from the
(unencrypted) YooAsset bundles.

Authoritative mapping (verified in decompiled Assembly-CSharp `eb46ed1b3cbb.cs`):
  * Each prop's icon  = sprite named `m_<id>` under  Assets/Resources_AB/Prop/
  * Rarity backdrop   = LoadAssetSync<Sprite>("PropBox/" + propInfo.Rare)
                        -> Assets/Resources_AB/PropBox/<rare>.png   (rare 0..6)
  * rare>=5 glow      = PropBox/PropLight/<rare>_1/_2/_3            (shine layers)

Output -> extracted/assets/props/
  icons/<name>.png                 item icons (m_<id>.png)
  backdrops/rare_<n>.png           the 7 rarity frames (rare_5 = gold 5*)
  backdrops/glow/<name>.png        high-rarity light layers + LightMask
  backdrops/misc/<name>.png        Select / Title / djk_sj (supporting UI)
  index.json                       id -> {name, name_en, rare, icon, backdrop}
  README.md                        human-readable explanation

Usage: python tools/extract_prop_assets.py
"""
import os
import csv
import glob
import json
import sys

import UnityPy

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\LAM\Lord and Maiden_Data"
YOO = os.path.join(GAME, "StreamingAssets", "yoo", "DefaultPackage")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "extracted", "assets", "props")
CSV = os.path.join(ROOT, "data", "csv", "PropInfo.csv")
NAME_CSV = os.path.join(ROOT, "data", "csv", "Language_PropName.csv")

ICONS = os.path.join(OUT, "icons")
BACK = os.path.join(OUT, "backdrops")
GLOW = os.path.join(BACK, "glow")
MISC = os.path.join(BACK, "misc")
for d in (ICONS, BACK, GLOW, MISC):
    os.makedirs(d, exist_ok=True)

# container-path prefixes we care about (lower-cased for matching)
PFX_PROP = "assets/resources_ab/prop/"
PFX_BOX = "assets/resources_ab/propbox/"


def _clean(s):
    """Strip the game's {tag} braces used in localized strings."""
    return (s or "").replace("{", "").replace("}", "").strip()


def save_image(reader, path):
    """Export a Sprite/Texture2D ObjectReader to a PNG. Returns True on success."""
    try:
        data = reader.read()
        img = data.image  # UnityPy gives a correctly-oriented PIL image
        if img is None:
            return False
        img.save(path)
        return True
    except Exception:
        return False


def classify(rel_lower):
    """Given the path under Resources_AB, decide output (folder, filename) or None."""
    base = os.path.basename(rel_lower)
    name = os.path.splitext(base)[0]
    # --- rarity backdrops: PropBox/<n>.png ---
    if rel_lower.startswith("propbox/"):
        sub = rel_lower[len("propbox/"):]
        if "/" not in sub:                      # directly under PropBox
            if name.isdigit():
                return (BACK, "rare_%s.png" % name)        # rarity frame
            return (MISC, base)                            # Select / Title / djk_sj
        if sub.startswith("proplight/"):
            if base.endswith(".prefab"):
                return None
            return (GLOW, base)                            # 5_1, 6_2, LightMask, ...
        return (MISC, base)
    # --- item icons: Prop/.../m_<id>.png ---
    if rel_lower.startswith("prop/"):
        if name.startswith("m_"):
            return (ICONS, base)
    return None


def extract():
    bundles = sorted(glob.glob(os.path.join(YOO, "*.bundle")))
    print("scanning %d bundles for Prop / PropBox sprites..." % len(bundles))

    # icon priority: a name from top-level Prop/ wins over Prop/64 or Prop/NewAdd
    icon_rank = {}          # filename -> rank already written (lower = better)
    saved_icons, saved_back, saved_glow, saved_misc = set(), set(), set(), set()

    for i, b in enumerate(bundles, 1):
        try:
            env = UnityPy.load(b)
            container = env.container
        except Exception:
            continue
        # cheap pre-filter: skip bundles with nothing relevant
        if not any((p or "").lower().startswith((PFX_PROP, PFX_BOX)) for p in container):
            if i % 100 == 0 or i == len(bundles):
                _progress(i, len(bundles), saved_icons, saved_back, saved_glow, saved_misc)
            continue

        for path, reader in container.items():
            pl = (path or "").lower()
            if not pl.startswith((PFX_PROP, PFX_BOX)):
                continue
            rel = pl.split("resources_ab/", 1)[1]
            dest = classify(rel)
            if not dest:
                continue
            folder, fname = dest
            out_path = os.path.join(folder, fname)

            if folder == ICONS:
                # rank by source depth: Prop/m_x (0) > Prop/NewAdd (1) > Prop/64 etc (2)
                if rel.startswith("prop/") and "/" not in rel[len("prop/"):]:
                    rank = 0
                elif "newadd/" in rel:
                    rank = 1
                else:
                    rank = 2
                if fname in icon_rank and icon_rank[fname] <= rank:
                    continue
                if save_image(reader, out_path):
                    icon_rank[fname] = rank
                    saved_icons.add(fname)
            else:
                already = {BACK: saved_back, GLOW: saved_glow, MISC: saved_misc}[folder]
                if fname in already:
                    continue
                if save_image(reader, out_path):
                    already.add(fname)

        if i % 100 == 0 or i == len(bundles):
            _progress(i, len(bundles), saved_icons, saved_back, saved_glow, saved_misc)
    print()
    return saved_icons, saved_back, saved_glow, saved_misc


def _progress(i, n, ic, bk, gl, mi):
    sys.stdout.write("\r  %d/%d bundles | icons:%d backdrops:%d glow:%d misc:%d   "
                     % (i, n, len(ic), len(bk), len(gl), len(mi)))
    sys.stdout.flush()


def load_propinfo():
    """id -> (name_cn, name_en, rare, icon)."""
    rows = {}
    with open(CSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows[r["id"]] = (_clean(r.get("name")), _clean(r.get("name_en")),
                             r.get("rare", "").strip(), _clean(r.get("icon")))
    return rows


def write_index(icons, backdrops, glow, misc):
    info = load_propinfo()
    items = []
    missing_icon = 0
    for pid, (cn, en, rare, icon) in sorted(info.items(), key=lambda kv: int(kv[0])):
        icon_file = "icons/%s.png" % icon if icon else ""
        have = bool(icon) and (icon + ".png") in icons
        if not have:
            missing_icon += 1
        rare_i = rare if rare.lstrip("-").isdigit() else ""
        back = "backdrops/rare_%s.png" % rare_i if rare_i != "" and ("rare_%s.png" % rare_i) in backdrops else ""
        items.append({
            "id": int(pid),
            "name_en": en, "name": cn,
            "rare": int(rare_i) if rare_i != "" else None,
            "icon": icon,
            "icon_file": icon_file if have else None,
            "backdrop_file": back or None,
        })
    index = {
        "_meta": {
            "source": "Lord and Maiden — YooAsset bundles (Assets/Resources_AB)",
            "icon_path_in_game": "Assets/Resources_AB/Prop/m_<id>.png",
            "backdrop_rule": "rarity backdrop = PropBox/<rare>  (rare 0..6; 5 = gold/5-star)",
            "glow_rule": "rare>=5 items add PropBox/PropLight/<rare>_1/_2/_3 shine layers",
            "rarity_backdrops": sorted(backdrops),
            "glow_layers": sorted(glow),
            "counts": {"props_total": len(items), "icons_extracted": len(icons),
                       "props_missing_icon_file": missing_icon},
        },
        "items": items,
    }
    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    return len(items), missing_icon


def write_readme(icons, backdrops, glow, misc, n_items, missing):
    md = f"""# Prop (item) assets

Extracted from the **Lord and Maiden** YooAsset bundles (plain `UnityFS`, no
encryption — see `notes/01-recon-and-encryption.md`). Regenerate with:

```
python tools/extract_prop_assets.py
```

## Layout
| Folder | What | Count |
|---|---|---|
| `icons/` | Item icons, `m_<id>.png` (the sprite each prop's `icon` field points to) | {len(icons)} |
| `backdrops/rare_0.png … rare_6.png` | The 7 rarity frames placed *behind* an item | {len(backdrops)} |
| `backdrops/glow/` | Extra shine layers for ★5/★6 items (`<rare>_1/_2/_3`, `LightMask`) | {len(glow)} |
| `backdrops/misc/` | Supporting `PropBox` UI (`Select`, `Title`, `djk_sj`) | {len(misc)} |
| `index.json` | Every prop → `name`, `rare`, `icon`, `icon_file`, `backdrop_file` | {n_items} props |

## How the game composites an item slot (from decompiled `eb46ed1b3cbb.cs`)
```
slot "Rare" Image .sprite = LoadAssetSync<Sprite>("PropBox/" + propInfo.Rare)   // backdrop
slot icon   Image .sprite = LoadAssetSync<Sprite>("Prop/" + propInfo.icon)      // m_<id>
if (propInfo.Rare >= 5)                                                          // gold/red glow
    "Light"   = PropBox/PropLight/<Rare>_3
    "StarImg2"= PropBox/PropLight/<Rare>_2
    stars     = PropBox/PropLight/<Rare>_1
```

So to render e.g. a **Hero Summon Scroll** the way the game does: draw
`backdrops/rare_<rare>.png`, then overlay `icons/m_<id>.png` on top (plus the
`glow/` layers if the item is ★5+).

## Rarity → backdrop
| rare | file | tier |
|---|---|---|
| 0 | `rare_0.png` | common (grey) |
| 1 | `rare_1.png` | |
| 2 | `rare_2.png` | |
| 3 | `rare_3.png` | |
| 4 | `rare_4.png` | |
| 5 | `rare_5.png` | **gold / 5★** |
| 6 | `rare_6.png` | top (red) |

## Notes
- {missing} of {n_items} `PropInfo` rows have no dedicated icon file present
  (many share an icon, or are non-inventory entries such as gear/card IDs that
  use other art). `index.json` flags these with `icon_file: null`.
- Icon name collisions across `Prop/`, `Prop/NewAdd/`, `Prop/64/` are resolved
  in favour of the top-level `Prop/` sprite.
"""
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write(md)


def main():
    if not os.path.isdir(YOO):
        print("game bundles not found at:\n  %s" % YOO)
        sys.exit(1)
    icons, back, glow, misc = extract()
    n_items, missing = write_index(icons, back, glow, misc)
    write_readme(icons, back, glow, misc, n_items, missing)
    print("icons: %d | rarity backdrops: %d | glow: %d | misc: %d"
          % (len(icons), len(back), len(glow), len(misc)))
    print("rarity backdrops:", ", ".join(sorted(back)))
    print("index.json + README.md -> %s" % OUT)


if __name__ == "__main__":
    main()
