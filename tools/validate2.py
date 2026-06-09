import os, re

WIKI = "wiki"


def npipes(l):
    s = l.strip()
    cnt = 0
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            i += 2
            continue
        if c == "|":
            cnt += 1
        i += 1
    return cnt


def is_sep(s):
    s = s.strip()
    return ("-" in s) and re.fullmatch(r"[|\s:\-]+", s) is not None


issues = []
for dp, _, fns in os.walk(WIKI):
    for fn in fns:
        if not fn.endswith(".md"):
            continue
        p = os.path.join(dp, fn).replace("\\", "/")
        with open(p, encoding="utf-8") as f:
            lines = f.readlines()
        in_fence = False
        i = 0
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith("```"):
                in_fence = not in_fence
                i += 1
                continue
            if in_fence:
                i += 1
                continue
            sep = lines[i + 1] if i + 1 < len(lines) else ""
            if "|" in lines[i] and is_sep(sep) and not is_sep(lines[i]):
                hp = npipes(lines[i])
                spn = npipes(sep)
                if hp != spn:
                    issues.append((p, i + 2, "sep!=hdr", hp, spn, sep.strip()[:80]))
                j = i + 2
                while j < len(lines):
                    b = lines[j]
                    bs = b.strip()
                    if "|" not in b or bs == "" or is_sep(b) or bs.startswith("```"):
                        break
                    bp = npipes(b)
                    if bp != hp:
                        issues.append((p, j + 1, "row!=hdr", hp, bp, b.rstrip()[:80]))
                    j += 1
                i = j
                continue
            i += 1

with open("tools/naive_tables.txt", "w", encoding="utf-8") as o:
    o.write("naive table issues: %d\n" % len(issues))
    for it in issues[:300]:
        o.write("%s:%s  %s hdr=%s got=%s :: %s\n" % it)
print("naive table issues:", len(issues))

tagrx = re.compile(r"</?(?:br|td|tr|table|div|span|font|sub|sup|h[1-6])\b[^>]*>", re.I)
html = []
for dp, _, fns in os.walk(WIKI):
    for fn in fns:
        if not fn.endswith(".md"):
            continue
        p = os.path.join(dp, fn).replace("\\", "/")
        in_fence = False
        with open(p, encoding="utf-8") as f:
            for nn, line in enumerate(f, 1):
                if line.strip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                if tagrx.search(line):
                    html.append((p, nn, line.strip()[:80]))
print("stray HTML lines:", len(html))
with open("tools/html.txt", "w", encoding="utf-8") as o:
    for it in html[:100]:
        o.write("%s:%s  %s\n" % it)
