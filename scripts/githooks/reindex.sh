#!/usr/bin/env bash
# Auto-reindex the mem0 'wiki' store when wiki/*.md changes — kills index drift (the
# "edit a page, forget to re-index → stale recall" failure mode). Installed as BOTH
# post-commit and post-merge via scripts/githooks/install.sh.
#
# Uses the reflog (HEAD@{1}) so one script serves both hooks: after a commit, HEAD@{1}
# is the pre-commit HEAD; after a merge/pull, it's the pre-merge HEAD. Either way we diff
# that range for wiki/*.md and reindex incrementally (cheap — only changed pages re-embed)
# in the BACKGROUND so the commit/pull returns instantly. Safe no-op if .venv is missing.
set -uo pipefail

REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
PY="$REPO/.venv/bin/python"
IDX="$REPO/scripts/mem0/index_wiki.py"

BASE="$(git rev-parse --quiet --verify 'HEAD@{1}' 2>/dev/null || true)"
if [ -n "$BASE" ]; then
  CHANGED="$(git diff --name-only "$BASE" HEAD -- "$REPO/wiki/" 2>/dev/null | grep -E '\.md$' || true)"
else
  CHANGED="$(git -C "$REPO" ls-files 'wiki/*.md')"   # first commit: index everything
fi
[ -n "$CHANGED" ] || exit 0   # no wiki markdown touched → nothing to do

if [ ! -x "$PY" ]; then
  echo "[mem0] wiki changed but no .venv — run scripts/mem0/setup.sh, then scripts/mem0/index_wiki.py" >&2
  exit 0
fi

mkdir -p "$REPO/.mem0-data"
echo "[mem0] wiki changed → incremental reindex in background (log: .mem0-data/reindex.log)"
nohup "$PY" "$IDX" >"$REPO/.mem0-data/reindex.log" 2>&1 &
exit 0
