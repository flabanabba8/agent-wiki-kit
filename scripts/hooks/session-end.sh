#!/usr/bin/env bash
# SessionEnd hook: record where this session left the repo, so the next session starts oriented.
# Why: the mem0-hot scratch layer existed but nothing ever wrote to it. This writes one factual
# note per session: branch, last commit, uncommitted files, latest log entry, re-verify queue.
# The note goes to .mem0-data/hot-recent.jsonl (read instantly by session-start.sh) and, in the
# background, to the mem0-hot store (searchable later with the `recall` MCP tool).
cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}" || exit 0
mkdir -p .mem0-data
BRANCH=$(git branch --show-current 2>/dev/null)
LAST=$(git log -1 --format='%h %s' 2>/dev/null | cut -c1-90)
DIRTY=$(git status --porcelain 2>/dev/null | wc -l)
LOGH=$(grep '^## ' wiki/log.md 2>/dev/null | tail -1 | sed 's/^## //' | cut -c1-110)
QN=$(grep -c '^- \[ \]' outputs/reverify-queue.md 2>/dev/null || echo 0)
NOTE="Session ended $(date '+%F %H:%M') on $BRANCH at $LAST; $DIRTY uncommitted file(s); latest log entry: $LOGH; re-verify queue: $QN."
python3 - "$NOTE" <<'PY'
import json, sys, datetime
path = ".mem0-data/hot-recent.jsonl"
try:
    lines = open(path, encoding="utf-8").read().splitlines()[-19:]
except OSError:
    lines = []
lines.append(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "note": sys.argv[1]}))
open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
if [ -x .venv/bin/python ]; then
  setsid nohup .venv/bin/python scripts/mem0/remember_cli.py "$NOTE" >/dev/null 2>&1 < /dev/null &
fi
exit 0
