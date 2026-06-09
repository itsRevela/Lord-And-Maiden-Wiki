"""Convert all extracted Resources_AB/Xml configs into clean CSV + JSON, with
localization ({token} -> English) resolved, plus a data/INDEX.md overview.

Config XML shape: <root><ROW>...flat fields...</ROW> <ROW>...</ROW></root>
Language_*.xml shape: <root><Language><Simplified_Text/><English_Text/>.../></root>

Usage: python tools/parse_configs.py
"""
import os
import re
import csv
import glob
import json
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML_DIR = os.path.join(ROOT, "extracted", "xml")
CSV_DIR = os.path.join(ROOT, "data", "csv")
JSON_DIR = os.path.join(ROOT, "data", "json")
for d in (CSV_DIR, JSON_DIR):
    os.makedirs(d, exist_ok=True)

LANGS = ["Simplified_Text", "Traditional_Text", "English_Text", "Japanese_Text", "Korean_Text"]
TOKEN = re.compile(r"\{([^{}]*)\}")


def parse_rows(path):
    """Return (row_tag, [ {field: text}, ... ]). Nested children are joined."""
    tree = ET.parse(path)
    root = tree.getroot()
    rows = []
    row_tag = None
    for rec in list(root):
        if row_tag is None:
            row_tag = rec.tag
        d = {}
        for child in list(rec):
            if list(child):  # nested -> join sub-values
                d[child.tag] = "|".join((c.text or "").strip() for c in child.iter() if c.text)
            else:
                d[child.tag] = (child.text or "").strip()
        if not list(rec) and (rec.text or "").strip():
            d["_text"] = rec.text.strip()
        rows.append(d)
    return row_tag, rows


def build_localization():
    """Merge all Language_*.xml -> {Simplified_Text: {lang: text}}."""
    loc = {}
    for path in glob.glob(os.path.join(XML_DIR, "Language_*.xml")):
        try:
            _tag, rows = parse_rows(path)
        except Exception:
            continue
        for r in rows:
            key = r.get("Simplified_Text", "")
            if key:
                loc.setdefault(key, {k: r.get(k, "") for k in LANGS})
    return loc


def resolve(text, loc):
    """Replace each {token} with its English text where known."""
    if "{" not in text:
        return text
    return TOKEN.sub(lambda m: loc.get(m.group(1), {}).get("English_Text") or m.group(0), text)


def main():
    loc = build_localization()
    json.dump(loc, open(os.path.join(ROOT, "data", "localization.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("localization keys: %d" % len(loc))

    index = ["# Config data index", "",
             "Generated from `extracted/xml/` by `tools/parse_configs.py`. "
             "`{token}` fields are localized via `data/localization.json`.", "",
             "| config | rows | columns |", "|---|---|---|"]
    files = sorted(glob.glob(os.path.join(XML_DIR, "*.xml")))
    total_rows = 0
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            row_tag, rows = parse_rows(path)
        except Exception as e:
            print("  [skip] %s: %s" % (name, e))
            continue
        # stable column order (first-seen) + localized variants for {..} text fields
        cols = []
        for r in rows:
            for k in r:
                if k not in cols:
                    cols.append(k)
        loc_cols = []
        for r in rows:
            for k in list(r):
                if "{" in r[k]:
                    en = resolve(r[k], loc)
                    if en != r[k]:
                        r[k + "_en"] = en
                        if (k + "_en") not in loc_cols:
                            loc_cols.append(k + "_en")
        allcols = cols + [c for c in loc_cols if c not in cols]
        # CSV
        with open(os.path.join(CSV_DIR, name + ".csv"), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=allcols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        # JSON
        json.dump(rows, open(os.path.join(JSON_DIR, name + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        total_rows += len(rows)
        index.append("| %s | %d | %s |" % (name, len(rows), ", ".join(cols[:12]) + (" …" if len(cols) > 12 else "")))

    open(os.path.join(ROOT, "data", "INDEX.md"), "w", encoding="utf-8").write("\n".join(index) + "\n")
    print("parsed %d configs, %d total rows -> data/csv, data/json, data/INDEX.md" % (len(files), total_rows))


if __name__ == "__main__":
    main()
