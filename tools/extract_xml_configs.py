"""Extract the game's XML/text config TextAssets from the (unencrypted) YooAsset
bundles. The configs live at Assets/Resources_AB/Xml/*.xml and are plain
TextAssets -> dumped verbatim to extracted/xml/.

Usage: python tools/extract_xml_configs.py
"""
import os
import re
import glob
import sys

import UnityPy

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\LAM\Lord and Maiden_Data"
YOO = os.path.join(GAME, "StreamingAssets", "yoo", "DefaultPackage")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extracted", "xml")
os.makedirs(OUT, exist_ok=True)


def manifest_targets():
    """basename(lower) -> filename, for every Resources_AB/Xml asset in the manifest."""
    mb = sorted(glob.glob(os.path.join(YOO, "*.bytes")))
    targets = {}
    if not mb:
        return targets
    raw = open(mb[0], "rb").read()
    for t in re.findall(rb"[ -~]{4,160}", raw):
        s = t.decode()
        if "Resources_AB/Xml/" in s and "." in os.path.basename(s):
            fn = os.path.basename(s)
            targets[os.path.splitext(fn)[0].lower()] = fn
    return targets


def main():
    targets = manifest_targets()
    print("config files listed in manifest: %d" % len(targets))
    bundles = sorted(glob.glob(os.path.join(YOO, "*.bundle")))
    print("scanning %d bundles for TextAssets..." % len(bundles))

    found = {}
    extra_xml = 0
    for i, b in enumerate(bundles, 1):
        try:
            env = UnityPy.load(b)
        except Exception:
            continue
        for obj in env.objects:
            if obj.type.name != "TextAsset":
                continue
            try:
                d = obj.read()
                name = d.m_Name
                script = d.m_Script
                data = script.encode("utf-8", "surrogateescape") if isinstance(script, str) else bytes(script)
            except Exception:
                continue
            key = (name or "").lower()
            if key in targets:
                fn = targets[key]
                with open(os.path.join(OUT, fn), "wb") as f:
                    f.write(data)
                found[key] = fn
            elif data[:64].lstrip()[:1] == b"<":   # XML-looking TextAsset not in manifest list
                fn = (name or ("unnamed_%d" % i)) + ".xml"
                with open(os.path.join(OUT, fn), "wb") as f:
                    f.write(data)
                extra_xml += 1
        if i % 100 == 0 or i == len(bundles):
            sys.stdout.write("\r  %d/%d bundles | %d/%d configs found | %d extra xml   "
                             % (i, len(bundles), len(found), len(targets), extra_xml))
            sys.stdout.flush()
    print()
    missing = sorted(set(targets) - set(found))
    print("extracted %d configs -> %s" % (len(found), OUT))
    if missing:
        print("NOT found as TextAssets (%d, e.g. .asset ScriptableObjects): %s"
              % (len(missing), ", ".join(targets[m] for m in missing[:15])))


if __name__ == "__main__":
    main()
