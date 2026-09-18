#!/usr/bin/env bash
# Temporal-validity check (reason 3) — borrowed from mem0/Graphiti temporal memory.
# Flags pages past their `valid_until:` date. (`supersedes:` is no longer used: outdated pages are
# deleted, so a supersedes target would normally not exist.)
# Standalone (does not affect wiki-lint.sh scoring). Run before/after volatile-page edits.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WIKI="$ROOT/wiki"
TODAY="$(date +%F)"
broken=0 expired=0 links=0

while IFS= read -r -d '' f; do
  base_name="$(basename "$f")"

  vu="$(grep -m1 -E '^valid_until:' "$f" 2>/dev/null | sed -E 's/^valid_until:[[:space:]]*//; s/["'\'']//g')"
  # A deprecated page's valid_until is historical (when the claim stopped being true), not a to-do.
  if grep -qE '^status:[[:space:]]*deprecated' "$f" 2>/dev/null; then vu=""; fi
  if [ -n "${vu:-}" ] && [[ "$vu" < "$TODAY" ]]; then
    echo "EXPIRED valid_until: $base_name ($vu < $TODAY)"
    expired=$((expired + 1))
  fi
done < <(find "$WIKI" -name '*.md' -print0)

echo
echo "Temporal check: $expired expired."
if [ "$expired" -eq 0 ]; then
  echo "OK"
  exit 0
fi
# Non-zero so scripts/doctor.sh (and CI) can tell a clean run from a dirty one.
exit 1
