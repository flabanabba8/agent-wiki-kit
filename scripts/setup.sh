#!/usr/bin/env bash
# One-command setup for a fresh clone.
#
#   ./scripts/setup.sh                   # venv, semantic index, git hooks, agent configs, health check
#   ./scripts/setup.sh --with-browser    # also install Camoufox (several hundred MB) for unreadable pages
#   ./scripts/setup.sh --with-sources    # also download the primary sources into raw/ (about 400 files)
#
# Nothing here needs an API key. Safe to run again: every step checks before it acts.
set -uo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$R"
BROWSER=0; SOURCES=0
for a in "$@"; do case "$a" in
  --with-browser) BROWSER=1 ;; --with-sources) SOURCES=1 ;;
  -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) echo "unknown option: $a" >&2; exit 2 ;;
esac; done
step() { printf '\n== %s\n' "$1"; }

command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 (3.10 or newer) is required" >&2; exit 1; }
git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "run this inside the git clone" >&2; exit 1; }

step "Python environment and the local embedding model"
bash scripts/mem0/setup.sh >/dev/null || { echo "environment setup failed; run scripts/mem0/setup.sh to see why" >&2; exit 1; }
echo "  .venv ready"

if [ "$BROWSER" = 1 ]; then
  step "Camoufox"
  if command -v uv >/dev/null 2>&1; then uv pip install --python .venv/bin/python -r scripts/camoufox/requirements.txt >/dev/null
  else ./.venv/bin/python -m pip install -q -r scripts/camoufox/requirements.txt; fi
  ./.venv/bin/python -m camoufox fetch >/dev/null 2>&1 && echo "  browser installed" || echo "  browser download failed; rerun: ./.venv/bin/python -m camoufox fetch" >&2
fi

step "Semantic index over wiki/"
./.venv/bin/python scripts/mem0/index_wiki.py 2>/dev/null | tail -1

step "Git hooks (reindex after commits and merges)"
bash scripts/githooks/install.sh >/dev/null 2>&1 && echo "  installed" || echo "  skipped"

step "Configuration for Codex and OpenCode, generated from the Claude Code files"
python3 scripts/agents/sync.py

if [ "$SOURCES" = 1 ]; then
  step "Primary sources (third-party text, kept out of git)"
  python3 scripts/sources.py fetch
fi

step "Health check"
./scripts/doctor.sh
if ! ls raw/docs/official/*.md >/dev/null 2>&1; then
  cat <<'EOF'

The source documents are NOT installed. They belong to other publishers, so they are not in the
repository. To download them (about 400 files):  ./scripts/setup.sh --with-sources
EOF
fi
cat <<'EOF'

Ready. Open this folder in Claude Code, Codex or OpenCode. For Hermes run ./scripts/agents/hermes/setup.sh once.
Try:  ./.venv/bin/python scripts/mem0/query_wiki.py "how do hooks block a tool call"
Optional: ./scripts/install-maintenance-cron.sh schedules the weekly source refresh.
EOF
