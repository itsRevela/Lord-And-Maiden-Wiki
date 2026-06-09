"""Dump the .asset ScriptableObjects (MonoBehaviour configs not stored as XML)
to data/scriptableobjects/*.json.

Tries the bundle's embedded TypeTree first; if the IL2CPP build stripped type
trees, falls back to UnityPy's TypeTreeGenerator using the game's managed DLLs
(extracted/dlls/).

Usage: python tools/extract_scriptableobjects.py
"""
import os
import glob
import sys
import json

import UnityPy

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\LAM\Lord and Maiden_Data"
YOO = os.path.join(GAME, "StreamingAssets", "yoo", "DefaultPackage")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DLLS = os.path.join(ROOT, "extracted", "dlls")
OUT = os.path.join(ROOT, "data", "scriptableobjects")
os.makedirs(OUT, exist_ok=True)

TARGETS = {"AiInfoList", "TradeList", "SimpHeroActionData", "TotalDecData",
           "UnionFightDecBuilds_1", "UnionFightDecBuilds_2", "UnionFightDecBuilds_3",
           "SideQuestsList"}

# optional typetree generator (fallback when bundles have no embedded typetree)
GEN = None
def get_generator(version):
    global GEN
    if GEN is not None:
        return GEN
    try:
        from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
        g = TypeTreeGenerator(version)
        # load all managed dlls we extracted
        for dll in glob.glob(os.path.join(DLLS, "*.dll")):
            try:
                g.load_dll(open(dll, "rb").read())
            except Exception:
                pass
        GEN = g
    except Exception as e:
        print("  (typetree generator unavailable: %r)" % e)
        GEN = False
    return GEN


def dump(obj, name):
    # 1) embedded typetree
    try:
        tt = obj.read_typetree()
        json.dump(tt, open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, default=str)
        return "embedded"
    except Exception:
        pass
    # 2) generated typetree from DLLs
    gen = get_generator(obj.assets_file.unity_version)
    if gen:
        try:
            d = obj.read()
            cls = getattr(getattr(d, "m_Script", None), "read", lambda: None)()
            clsname = getattr(cls, "m_ClassName", None) or name
            ns = getattr(cls, "m_Namespace", "") or ""
            asm = (getattr(cls, "m_AssemblyName", "") or "").replace(".dll", "")
            for assembly in ([asm] if asm else []) + ["Assembly-CSharp", "eb46ed1b3cbb"]:
                try:
                    nodes = gen.get_nodes(assembly, (ns + "." + clsname) if ns else clsname)
                    if nodes:
                        tt = obj.read_typetree(nodes)
                        json.dump(tt, open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8"),
                                  ensure_ascii=False, indent=1, default=str)
                        return "generated(%s)" % assembly
                except Exception:
                    continue
        except Exception:
            pass
    return None


def main():
    bundles = sorted(glob.glob(os.path.join(YOO, "*.bundle")))
    print("scanning %d bundles for %d ScriptableObjects..." % (len(bundles), len(TARGETS)))
    found = {}
    for i, b in enumerate(bundles, 1):
        if len(found) == len(TARGETS):
            break
        try:
            env = UnityPy.load(b)
        except Exception:
            continue
        for obj in env.objects:
            if obj.type.name != "MonoBehaviour":
                continue
            try:
                name = obj.read().m_Name
            except Exception:
                continue
            if name in TARGETS and name not in found:
                how = dump(obj, name)
                found[name] = how or "FAILED"
                print("  %-26s -> %s" % (name, found[name]))
        if i % 100 == 0:
            sys.stdout.write("\r  ...%d/%d bundles, %d/%d found   " % (i, len(bundles), len(found), len(TARGETS)))
            sys.stdout.flush()
    print()
    miss = TARGETS - set(found)
    print("done. dumped: %d -> %s" % (sum(1 for v in found.values() if v != "FAILED"), OUT))
    if miss:
        print("not located in bundles:", miss)
    fails = [k for k, v in found.items() if v == "FAILED"]
    if fails:
        print("located but could not deserialize:", fails)


if __name__ == "__main__":
    main()
