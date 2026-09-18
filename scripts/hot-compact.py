#!/usr/bin/env python3
"""hot-compact.py — enforce hot.md's format mechanically instead of by hand.

Rules from CLAUDE.md: emoji-coded lines, under 120 characters, at most 30 entries, newest first.
Drops exact duplicates (same text ignoring the date), keeps the newest 30, sets `updated:` to
today. Over-long lines are reported, not truncated: a cut sentence can change its meaning.

Usage: ./scripts/hot-compact.py [--check]   (--check exits 1 if anything would change or is too long)
"""
import datetime, re, subprocess, os, sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or os.getcwd()
P = os.path.join(ROOT, "wiki", "hot.md")
CAP, MAXLEN = 30, 120
ANCHOR = "## Compressed Observations (newest first)\n\n"

s = open(P, encoding="utf-8").read()
head, rest = s.split(ANCHOR, 1)
block, sep, tail = rest.partition("\n\n")
lines = [l for l in block.split("\n") if l.strip()]
seen, kept = set(), []
for l in lines:
    key = re.sub(r"^\S+\s+\d{4}-\d{2}-\d{2}\s+", "", l).strip().lower()
    if key in seen:
        continue
    seen.add(key)
    kept.append(l)
dropped = len(lines) - len(kept[:CAP])
kept = kept[:CAP]
too_long = [l for l in kept if len(l) >= MAXLEN]
new = head + ANCHOR + "\n".join(kept) + sep + tail
if new != s or dropped:
    new = re.sub(r"^updated:.*$", f"updated: {datetime.date.today()}", new, count=1, flags=re.M)
changed = new != s
if "--check" in sys.argv:
    print(f"hot.md: {len(kept)} entries, {dropped} would be dropped, {len(too_long)} too long")
    for l in too_long:
        print(f"  TOO LONG ({len(l)}): {l}")
    sys.exit(1 if (changed or too_long) else 0)
open(P, "w", encoding="utf-8").write(new)
print(f"hot.md: {len(kept)} entries kept, {dropped} dropped, {len(too_long)} too long")
for l in too_long:
    print(f"  TOO LONG ({len(l)}): {l}")
