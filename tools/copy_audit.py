#!/usr/bin/env python3
"""Copy/rendering/readability auditor for the Lord-And-Maiden wiki.

Emits all findings to a UTF-8 report file. Console-safe (no CJK printed).
Does NOT modify any wiki files.
"""
import os
import re
import sys
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = os.path.join(ROOT, "wiki")
OUT = os.path.join(ROOT, "tools", "audit_findings.txt")

findings = {
    "1_TABLE_VALIDITY": [],
    "2_BROKEN_CONTENT": [],
    "3_LINK_HYGIENE": [],
    "4_CONSISTENCY": [],
    "5_PROSE": [],
}


def add(cat, msg):
    findings[cat].append(msg)


def md_files():
    out = []
    for dp, _, fns in os.walk(WIKI):
        for fn in fns:
            if fn.lower().endswith(".md"):
                out.append(os.path.join(dp, fn))
    return sorted(out)


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def split_cells(line):
    """Split a GFM table row into cells, honoring backslash-escaped pipes
    and inline-code spans (pipes inside `code` do not split cells)."""
    # Strip one leading and one trailing pipe (GFM convention)
    s = line.strip()
    cells = []
    buf = []
    i = 0
    in_code = False
    n = len(s)
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            buf.append(c)
            buf.append(s[i + 1])
            i += 2
            continue
        if c == "`":
            in_code = not in_code
            buf.append(c)
            i += 1
            continue
        if c == "|" and not in_code:
            cells.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    cells.append("".join(buf))
    # Drop the empty leading/trailing cell created by border pipes
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return cells


def raw_pipe_count(line):
    """Count raw unescaped | not inside inline code, for detecting cell splits."""
    s = line.strip()
    cnt = 0
    in_code = False
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            i += 2
            continue
        if c == "`":
            in_code = not in_code
            i += 1
            continue
        if c == "|" and not in_code:
            cnt += 1
        i += 1
    return cnt


SEP_RE = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$")


def is_separator(line):
    s = line.strip()
    if not s:
        return False
    # must contain only | : - and spaces, and at least one dash
    if "-" not in s:
        return False
    return bool(re.fullmatch(r"[\|\s:\-]+", s))


def looks_like_table_row(line):
    s = line.strip()
    return s.startswith("|") or ("|" in s and not s.startswith("```"))


def audit_tables(path, lines):
    """Parse markdown tables and flag column-count mismatches & separator issues."""
    r = rel(path)
    in_fence = False
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        # Detect a table header: a line with pipes followed by a separator line
        if "|" in line and i + 1 < n and is_separator(lines[i + 1]) and not is_separator(line):
            header_line = line
            header_cells = split_cells(header_line)
            ncol = len(header_cells)
            sep_cells = split_cells(lines[i + 1])
            if len(sep_cells) != ncol:
                add("1_TABLE_VALIDITY",
                    f"{r}:{i+2}  SEPARATOR column count ({len(sep_cells)}) != header ({ncol}) | row: {lines[i+1].rstrip()}")
            # walk body rows
            j = i + 2
            while j < n:
                body = lines[j]
                bs = body.strip()
                if bs.startswith("```") or bs.startswith("~~~"):
                    break
                if "|" not in body or bs == "":
                    break
                if is_separator(body):
                    # a second separator inside body = malformed
                    add("1_TABLE_VALIDITY",
                        f"{r}:{j+1}  Unexpected separator row inside table body | row: {body.rstrip()}")
                    j += 1
                    continue
                bcells = split_cells(body)
                if len(bcells) != ncol:
                    add("1_TABLE_VALIDITY",
                        f"{r}:{j+1}  ROW cells ({len(bcells)}) != header ({ncol}) | row: {body.rstrip()}")
                j += 1
            i = j
            continue
        i += 1


PIPE_IN_CELL_HINT = re.compile(r"`[^`]*`")


def audit_pipe_in_cell(path, lines):
    """Detect likely unescaped pipes inside cell text that would split a cell.
    Heuristic: a table body row whose cell count exceeds header but where an
    extra pipe sits adjacent to alphanumerics (not a clean border)."""
    # This is largely covered by audit_tables mismatch; here we look for
    # pipes glued to text like 'word|word' inside detected table regions.
    r = rel(path)
    in_fence = False
    in_table = False
    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if is_separator(line):
            in_table = True
            continue
        if in_table and "|" not in line:
            in_table = False
        if in_table and "|" in line:
            # find pipes with alnum on both sides (likely accidental)
            for m in re.finditer(r"(?<=[A-Za-z0-9])\|(?=[A-Za-z0-9])", line):
                # ignore if inside inline code
                pre = line[:m.start()]
                if pre.count("`") % 2 == 1:
                    continue
                add("1_TABLE_VALIDITY",
                    f"{r}:{idx+1}  Possible unescaped '|' glued to text (may split cell) | ...{line[max(0,m.start()-15):m.end()+15].strip()}...")


BAD_TOKENS = {
    "None": re.compile(r"(?<![A-Za-z])None(?![A-Za-z])"),
    "nan": re.compile(r"(?<![A-Za-z])nan(?![A-Za-z])"),
    "NaN": re.compile(r"(?<![A-Za-z])NaN(?![A-Za-z])"),
    "0_0": re.compile(r"\b0_0\b"),
    "null": re.compile(r"(?<![A-Za-z])null(?![A-Za-z])"),
    "undefined": re.compile(r"(?<![A-Za-z])undefined(?![A-Za-z])"),
}
BRACE_RE = re.compile(r"\{[^}\n]*\}")
DOUBLE_SPACE_RE = re.compile(r"\S  +\S")  # 2+ spaces between non-space (not leading indent)
TRAILING_X_RE = re.compile(r"\bx\s*(\||$)")
LONE_UNDERSCORE_CELL = re.compile(r"^\s*_\s*$")


def audit_content(path, lines):
    r = rel(path)
    in_fence = False
    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        ln = idx + 1
        # bad tokens (only flag when they appear inside a table cell context or standalone)
        is_row = "|" in line
        for name, rx in BAD_TOKENS.items():
            for m in rx.finditer(line):
                # skip 'None' when it's clearly prose like "None of"
                seg = line[max(0, m.start()-2):m.end()+6]
                add("2_BROKEN_CONTENT",
                    f"{r}:{ln}  raw token '{name}' | ...{line.strip()[:120]}...")
                break  # one report per token-name per line
        # leftover braces
        for m in BRACE_RE.finditer(line):
            inner = m.group(0)
            # skip CSS-ish or legit code if inside inline code
            pre = line[:m.start()]
            if pre.count("`") % 2 == 1:
                continue
            add("2_BROKEN_CONTENT",
                f"{r}:{ln}  leftover braces '{inner[:40]}' | ...{line.strip()[:120]}...")
        # doubled spaces inside cells / prose (ignore the GFM '·  ·' separators? report them lightly)
        # Only report inside table rows to reduce noise from intentional alignment.
        if is_row:
            # examine each cell
            for cell in split_cells(line):
                c = cell.strip()
                if c == "_" :
                    add("2_BROKEN_CONTENT", f"{r}:{ln}  lone underscore cell '_' | ...{line.strip()[:120]}...")
                if re.search(r"\S  +\S", cell) and "·" not in cell:
                    add("2_BROKEN_CONTENT", f"{r}:{ln}  doubled spaces in cell | cell='{c[:60]}'")
        # trailing ' x' with no number e.g. 'Wood x' or 'x ' at end of cell
        for cell in (split_cells(line) if is_row else [line]):
            c = cell.strip()
            if re.search(r"\bx$", c) and not re.search(r"x\d", c) and len(c) > 1:
                # avoid matching words ending in x like 'max','box'
                if re.search(r"[A-Za-z)]\s+x$", c) or re.search(r"\s x$", c):
                    add("2_BROKEN_CONTENT", f"{r}:{ln}  trailing ' x' with no quantity | cell='{c[:60]}'")
        # cut-off mid word: line ending with a hyphen attached to a word and no continuation? skip (markdown)
        # em-dash filling whole column handled in consistency.


def audit_links(path, lines, all_files_set):
    r = rel(path)
    base = os.path.dirname(path)
    in_fence = False
    link_rx = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in link_rx.finditer(line):
            target = m.group(2).strip()
            if target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:"):
                continue
            if target.startswith("#"):
                continue  # same-page anchor; not validating anchors here
            # strip anchor and query
            tgt = target.split("#", 1)[0].split("?", 1)[0]
            tgt = unquote(tgt)
            if tgt == "":
                continue
            # resolve relative
            resolved = os.path.normpath(os.path.join(base, tgt))
            if not os.path.exists(resolved):
                add("3_LINK_HYGIENE",
                    f"{r}:{idx+1}  broken relative link -> '{target}' (resolved: {rel(resolved) if resolved.startswith(ROOT) else resolved})")


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


def audit_consistency(path, lines, title_map):
    r = rel(path)
    in_fence = False
    prev_level = 0
    first_h1 = None
    heading_levels = []
    for idx, line in enumerate(lines):
        s = line.rstrip("\n")
        st = s.strip()
        if st.startswith("```") or st.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(s)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 1 and first_h1 is None:
                first_h1 = text
            if prev_level and level > prev_level + 1:
                add("4_CONSISTENCY",
                    f"{r}:{idx+1}  heading level jumps from h{prev_level} to h{level} | '{text[:60]}'")
            prev_level = level
    if first_h1:
        title_map.setdefault(first_h1, []).append(r)


def audit_emdash_columns(path, lines):
    """Flag tables where an entire column is just em-dash / dash placeholder."""
    r = rel(path)
    in_fence = False
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        if "|" in line and i + 1 < n and is_separator(lines[i + 1]) and not is_separator(line):
            header = split_cells(line)
            ncol = len(header)
            col_vals = [[] for _ in range(ncol)]
            j = i + 2
            while j < n:
                b = lines[j]
                bs = b.strip()
                if "|" not in b or bs == "" or is_separator(b):
                    break
                if bs.startswith("```"):
                    break
                cells = split_cells(b)
                for k in range(min(ncol, len(cells))):
                    col_vals[k].append(cells[k].strip())
                j += 1
            for k in range(ncol):
                vals = col_vals[k]
                if len(vals) >= 3 and all(v in ("—", "-", "–", "") for v in vals):
                    add("2_BROKEN_CONTENT",
                        f"{r}:{i+1}  entire column '{header[k].strip()[:30]}' is dash/em-dash placeholder ({len(vals)} rows)")
            i = j
            continue
        i += 1


def main():
    files = md_files()
    all_files_set = set(os.path.normpath(f) for f in files)
    title_map = {}
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
        audit_tables(f, lines)
        audit_pipe_in_cell(f, lines)
        audit_content(f, lines)
        audit_links(f, lines, all_files_set)
        audit_consistency(f, lines, title_map)
        audit_emdash_columns(f, lines)

    # duplicate titles
    for title, paths in sorted(title_map.items()):
        if len(paths) > 1:
            add("4_CONSISTENCY",
                f"DUPLICATE H1 TITLE '{title}' in: {', '.join(paths)}")

    with open(OUT, "w", encoding="utf-8") as out:
        out.write("LORD AND MAIDEN WIKI - COPY/RENDERING AUDIT\n")
        out.write(f"Files scanned: {len(files)}\n\n")
        for cat in ["1_TABLE_VALIDITY", "2_BROKEN_CONTENT", "3_LINK_HYGIENE", "4_CONSISTENCY", "5_PROSE"]:
            items = findings[cat]
            out.write(f"\n===== {cat} ({len(items)}) =====\n")
            for it in items:
                out.write(it + "\n")

    # console-safe summary (ASCII counts only)
    print("Files scanned:", len(files))
    for cat in findings:
        print(cat, "=>", len(findings[cat]))
    print("Report written to", rel(OUT))


if __name__ == "__main__":
    main()
