"""Verify the generated wiki for integrity & accuracy.

Checks:
  1. Every relative markdown link points to a file that exists.
  2. Unresolved id placeholders (Prop#, Hero#, Build#, Skill#, Tech#, Buff#).
  3. Leftover localization tokens "{...}" that never resolved.
  4. A few cross-checks against source data (hero count, stat formula spot-check).
"""
import os
import re
import csv
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WIKI = os.path.join(ROOT, "wiki")
CSV = os.path.join(ROOT, "data", "csv")

LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PLACEHOLDER = re.compile(r"\b(Prop|Hero|Build|Skill|Tech|Buff)#\d")
TOKEN = re.compile(r"\{[^{}]{1,40}\}")

issues = collections = 0
problems = []


def all_md():
    for dp, _d, fns in os.walk(WIKI):
        for fn in fns:
            if fn.endswith(".md"):
                yield os.path.join(dp, fn)


def check_links():
    bad = 0
    for p in all_md():
        text = open(p, encoding="utf-8").read()
        for m in LINK.finditer(text):
            url = m.group(1).split("#")[0]
            if not url or url.startswith(("http://", "https://", "mailto:")):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(p), urllib.parse.unquote(url)))
            if not os.path.exists(target):
                bad += 1
                if bad <= 25:
                    problems.append("BROKEN LINK in %s -> %s" % (os.path.relpath(p, WIKI), url))
    return bad


def count_re(rx):
    total = collections_local = 0
    per = {}
    for p in all_md():
        text = open(p, encoding="utf-8").read()
        c = len(rx.findall(text))
        if c:
            per[os.path.relpath(p, WIKI)] = c
            total += c
    return total, per


def cross_checks():
    msgs = []
    # hero roster count == named heroes in HeroInfo (have HeroDes)
    hi = list(csv.DictReader(open(os.path.join(CSV, "HeroInfo.csv"), encoding="utf-8-sig")))
    hd = set(r["id"] for r in csv.DictReader(open(os.path.join(CSV, "HeroDes.csv"), encoding="utf-8-sig")))
    named = [h for h in hi if h["id"] in hd]
    roster_files = len(os.listdir(os.path.join(WIKI, "Heroes", "roster")))
    msgs.append("named heroes=%d, roster pages=%d -> %s" %
                (len(named), roster_files, "OK" if len(named) == roster_files else "MISMATCH"))
    # stat formula spot check on a roster page
    import math
    h = next(x for x in named if x["id"] == "2")
    expect80 = int(h["attack"]) + math.floor(float(h["attack_grow"]) * 80)
    page = open(os.path.join(WIKI, "Heroes", "roster", "2-saintess-shin.md"), encoding="utf-8").read()
    ok = ("| 80 | %d |" % expect80) in page
    msgs.append("Lv80 ATK spot-check (hero 2 = %d): %s" % (expect80, "OK" if ok else "FAIL"))
    return msgs


def main():
    print("=== link integrity ===")
    bad = check_links()
    print("broken links: %d" % bad)
    for p in problems[:25]:
        print("  " + p)

    print("\n=== unresolved id placeholders ===")
    tot, per = count_re(PLACEHOLDER)
    print("total: %d" % tot)
    for k, v in sorted(per.items(), key=lambda x: -x[1])[:10]:
        print("  %s: %d" % (k, v))

    print("\n=== leftover {localization} tokens ===")
    tot2, per2 = count_re(TOKEN)
    print("total: %d" % tot2)
    for k, v in sorted(per2.items(), key=lambda x: -x[1])[:10]:
        print("  %s: %d" % (k, v))

    print("\n=== cross-checks ===")
    for m in cross_checks():
        print("  " + m)

    print("\nRESULT: %s" % ("PASS" if bad == 0 else "%d broken links" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
