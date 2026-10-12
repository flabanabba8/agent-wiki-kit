#!/usr/bin/env bash
# SessionStart hook: surface harness health + hot.md age into the session context.
# stdout of a SessionStart hook is injected as context, so keep it to a few lines.
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 0
[ -x scripts/doctor.sh ] || exit 0
echo "[agent-wiki-kit] $(./scripts/doctor.sh --quiet 2>/dev/null)"
HOT=$(grep -m1 '^updated:' wiki/hot.md 2>/dev/null | awk '{print $2}')
[ -n "$HOT" ] && echo "[agent-wiki-kit] hot.md last updated $HOT — read wiki/hot.md then wiki/index.md before answering."
# Bounded recovery snapshot: the newest log headings and hot.md lines, so a session can tell
# what just happened without reading either file. Entries are candidates, not a reading order.
LOGHEAD=$(grep -m3 '^## ' wiki/log.md 2>/dev/null | cut -c1-110)
[ -n "$LOGHEAD" ] && { echo "[agent-wiki-kit] newest log entries:"; echo "$LOGHEAD" | sed 's/^/  /'; }
HOTHEAD=$(sed -n '/^## Compressed Observations/,$p' wiki/hot.md 2>/dev/null | grep -m5 -E '^[^#[:space:]]' | cut -c1-120)
[ -n "$HOTHEAD" ] && { echo "[agent-wiki-kit] newest hot.md lines:"; echo "$HOTHEAD" | sed 's/^/  /'; }
if [ -f .mem0-data/hot-recent.jsonl ]; then
  echo "[agent-wiki-kit] recent sessions (mem0-hot; search older notes with the recall tool):"
  tail -3 .mem0-data/hot-recent.jsonl | python3 -c "import sys,json; [print('  -', json.loads(l)['note']) for l in sys.stdin if l.strip()]" 2>/dev/null
fi
exit 0
