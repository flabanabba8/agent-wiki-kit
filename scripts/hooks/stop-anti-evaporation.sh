#!/usr/bin/env bash
# Stop hook: enforce the anti-evaporation rule. If wiki pages changed this session
# but wiki/log.md did not, block the stop once with a reminder (stop_hook_active
# guard prevents a loop). Advisory only — the model can log and stop again.
INPUT=$(cat)
[ "$(printf '%s' "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null)" = "true" ] && exit 0
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 0
CHANGED=$(git status --porcelain -- wiki/ 2>/dev/null | grep -vE 'wiki/(log|hot|index)\.md' | wc -l)
[ "$CHANGED" -gt 0 ] || exit 0
LOGGED=$(git status --porcelain -- wiki/log.md 2>/dev/null | wc -l)
if [ "$LOGGED" -eq 0 ]; then
  echo "Anti-evaporation: $CHANGED wiki page(s) changed but wiki/log.md was not appended. Append a dated log entry, update wiki/hot.md, and re-run ./.venv/bin/python scripts/mem0/index_wiki.py before stopping." >&2
  exit 2
fi
exit 0
