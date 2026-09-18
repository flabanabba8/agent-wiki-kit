#!/usr/bin/env bash
# Install the tracked git hooks into .git/hooks/ as symlinks, so edits to the tracked
# scripts propagate automatically and a fresh clone just re-runs this once.
set -euo pipefail

REPO="$(git rev-parse --show-toplevel)"
HOOKS="$REPO/.git/hooks"
mkdir -p "$HOOKS"
chmod +x "$REPO/scripts/githooks/reindex.sh"

for h in post-commit post-merge; do
  # relative target: .git/hooks/ -> ../../scripts/githooks/reindex.sh
  ln -sfn ../../scripts/githooks/reindex.sh "$HOOKS/$h"
  echo "installed $h -> scripts/githooks/reindex.sh"
done
echo "Done. Wiki edits now auto-reindex the mem0 store on commit/merge."
