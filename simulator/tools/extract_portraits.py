"""Extract hero portrait sprites from the Lord & Maiden YooAsset bundles.

The client loads hero heads by logical address (decompiled GetHeroHeadImg):
  full  : Hero/{icon}/Head_{icon}_{skinId}
  chibi : PlayerHead_Q/QHead_{icon}_{skinId}
keyed by HeroInfo.icon. Bundles are plain UnityFS (no decryption). We scan every
bundle once, find Sprite/Texture2D objects named Head_<icon>_0 / QHead_<icon>_0,
and export them as PNG into the web app's public/portraits folder.

Usage (from repo root):
  python -m simulator.tools.extract_portraits
  python -m simulator.tools.extract_portraits --lam "C:\\path\\to\\Lord and Maiden_Data"
"""
import argparse
import io
import os
import re
import sys
import time

DEFAULT_LAM = r"C:\Program Files (x86)\Steam\steamapps\common\LAM\Lord and Maiden_Data"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "public", "portraits")
LOG = os.path.join(os.path.dirname(__file__), "..", "_portraits_log.txt")

NAME_RE = re.compile(r"^(Q?)Head_(\d+)_0$")


def log(msg):
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main():
    import UnityPy

    ap = argparse.ArgumentParser()
    ap.add_argument("--lam", default=DEFAULT_LAM)
    ap.add_argument("--limit", type=int, default=0, help="stop after N bundles (debug)")
    args = ap.parse_args()

    pkg = os.path.join(args.lam, "StreamingAssets", "yoo", "DefaultPackage")
    bundles = sorted(b for b in os.listdir(pkg) if b.endswith(".bundle"))
    if args.limit:
        bundles = bundles[: args.limit]
    os.makedirs(OUT_DIR, exist_ok=True)
    io.open(LOG, "w", encoding="utf-8").close()
    log("portrait extraction start: %d bundles -> %s" % (len(bundles), os.path.abspath(OUT_DIR)))

    full, chibi = {}, {}     # icon -> True once saved
    t0 = time.time()
    for i, b in enumerate(bundles):
        try:
            env = UnityPy.load(os.path.join(pkg, b))
        except Exception as e:           # noqa: BLE001 - bundle may be non-asset
            continue
        for obj in env.objects:
            if obj.type.name not in ("Sprite", "Texture2D"):
                continue
            try:
                data = obj.read()
                name = getattr(data, "m_Name", None) or getattr(data, "name", "")
            except Exception:            # noqa: BLE001
                continue
            m = NAME_RE.match(name or "")
            if not m:
                continue
            is_chibi = m.group(1) == "Q"
            icon = m.group(2)
            target = chibi if is_chibi else full
            if icon in target:
                continue                 # already saved (prefer Sprite/first hit)
            try:
                img = data.image
                if img is None:
                    continue
                fname = ("q_%s.png" % icon) if is_chibi else ("%s.png" % icon)
                img.save(os.path.join(OUT_DIR, fname))
                target[icon] = True
            except Exception as e:       # noqa: BLE001
                continue
        if (i + 1) % 100 == 0:
            log("  %d/%d bundles | full=%d chibi=%d | %.0fs"
                % (i + 1, len(bundles), len(full), len(chibi), time.time() - t0))

    log("DONE: full=%d chibi=%d in %.0fs" % (len(full), len(chibi), time.time() - t0))
    print("portrait extraction done: full=%d chibi=%d" % (len(full), len(chibi)))


if __name__ == "__main__":
    main()
