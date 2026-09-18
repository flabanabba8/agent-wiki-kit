#!/usr/bin/env bash
#
# changelog-delta.sh — save Claude Code CHANGELOG sections newer than the newest ingested one.
#
# Why: Claude Code ships almost daily; the wiki's changelog coverage fell behind within a day.
# The newest ingested version is read from raw/docs/changelog-<from>-to-<to>.md filenames.
# Writes raw/docs/changelog-<first>-to-<last>.md (a NEW immutable raw file) and prints the
# versions, so the ingest workflow knows what to summarize. Exit 0 with no file if up to date.
#
# Usage: ./scripts/changelog-delta.sh [--dry-run]
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
URL="https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

LAST=$(ls raw/docs/changelog-*-to-*.md 2>/dev/null | sed -E 's/.*-to-([0-9.]+)\.md$/\1/' | sort -V | tail -1)
[ -n "$LAST" ] || { echo "no raw/docs/changelog-*-to-*.md found; ingest a baseline first" >&2; exit 1; }
TMP=$(mktemp); trap 'rm -f "$TMP"' EXIT
curl -sL --max-time 60 "$URL" -o "$TMP" && [ -s "$TMP" ] || { echo "failed to fetch $URL" >&2; exit 1; }

python3 - "$LAST" "$DRY" "$URL" "$TMP" <<'PY'
import re, sys, datetime
last, dry, url, src = sys.argv[1], sys.argv[2] == "1", sys.argv[3], sys.argv[4]
text = open(src, encoding="utf-8").read()
ver = lambda v: tuple(int(x) for x in v.split("."))
parts = re.split(r"(?m)^## (\d+\.\d+\.\d+)[^\n]*$", text)
sections = [(parts[i], parts[i + 1]) for i in range(1, len(parts) - 1, 2)]
new = [(v, b) for v, b in sections if ver(v) > ver(last)]
if not new:
    print(f"up to date: newest ingested {last}")
    sys.exit(0)
new.sort(key=lambda vb: ver(vb[0]))
first, newest = new[0][0], new[-1][0]
print(f"new versions after {last}: {', '.join(v for v, _ in new)}")
if dry:
    sys.exit(0)
path = f"raw/docs/changelog-{first}-to-{newest}.md"
with open(path, "w", encoding="utf-8") as f:
    f.write(f"<!-- SOURCE: {url} | publisher: Anthropic | versions {first} to {newest} | fetched: {datetime.date.today()} | via scripts/changelog-delta.sh -->\n\n")
    for v, b in reversed(new):
        f.write(f"## {v}\n{b.rstrip()}\n\n")
print(f"saved {path}")
PY
