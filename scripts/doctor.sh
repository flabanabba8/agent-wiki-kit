#!/usr/bin/env bash
#
# doctor.sh — verify the agent-wiki-kit self-maintenance harness is actually wired up.
#
# Why: the wiki's content pipeline (ingest/query/lint) is prompt-driven, but its
# *maintenance* depends on machinery that silently disappears on a fresh clone:
# the mem0 .venv, the semantic index, the git reindex hooks, a fresh hot.md.
# All four can be missing for weeks without any visible symptom, so this checks them out loud.
#
# Usage:
#   ./scripts/doctor.sh            # report (exit 1 if anything is red)
#   ./scripts/doctor.sh --fix      # also install git hooks + build .venv/index if missing
#   ./scripts/doctor.sh --quiet    # one-line summary (used by the SessionStart hook)
#
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

FIX=0; QUIET=0
for a in "$@"; do case "$a" in --fix) FIX=1;; --quiet) QUIET=1;; esac; done

RED=0; WARN=0; LINES=()
ok()   { LINES+=("  ok    $1"); }
warn() { LINES+=("  WARN  $1"); WARN=$((WARN+1)); }
bad()  { LINES+=("  FAIL  $1"); RED=$((RED+1)); }

# 1. mem0 venv --------------------------------------------------------------
if [ -x .venv/bin/python ] && .venv/bin/python -c "import mem0" 2>/dev/null; then
  ok ".venv present (mem0 importable)"
else
  if [ "$FIX" = 1 ]; then
    bash scripts/mem0/setup.sh >/dev/null 2>&1 && ok ".venv built by --fix" || bad ".venv build failed (run scripts/mem0/setup.sh)"
  else
    bad ".venv missing → query_wiki.py / mem0-hot MCP are dead. Run: scripts/mem0/setup.sh"
  fi
fi

# 2. semantic index freshness ----------------------------------------------
MANIFEST=".mem0-data/wiki-manifest.json"
if [ -f "$MANIFEST" ]; then
  NEWER=$(find wiki -name '*.md' -newer "$MANIFEST" | wc -l)
  if [ "$NEWER" -eq 0 ]; then
    ok "semantic index current (manifest newer than every wiki page)"
  else
    if [ "$FIX" = 1 ] && [ -x .venv/bin/python ]; then
      .venv/bin/python scripts/mem0/index_wiki.py >/dev/null 2>&1 && ok "index refreshed by --fix ($NEWER pages)" || bad "index refresh failed"
    else
      warn "semantic index stale: $NEWER wiki page(s) newer than manifest. Run: ./.venv/bin/python scripts/mem0/index_wiki.py"
    fi
  fi
else
  if [ "$FIX" = 1 ] && [ -x .venv/bin/python ]; then
    .venv/bin/python scripts/mem0/index_wiki.py >/dev/null 2>&1 && ok "index built by --fix" || bad "index build failed"
  else
    bad "no semantic index (.mem0-data/wiki-manifest.json). Run: ./.venv/bin/python scripts/mem0/index_wiki.py"
  fi
fi

# 3. git reindex hooks ------------------------------------------------------
if [ -L .git/hooks/post-commit ] && [ -L .git/hooks/post-merge ]; then
  ok "git reindex hooks installed (post-commit, post-merge)"
else
  if [ "$FIX" = 1 ]; then
    bash scripts/githooks/install.sh >/dev/null 2>&1 && ok "git hooks installed by --fix" || bad "git hook install failed"
  else
    warn "git reindex hooks not installed → index drifts after commits. Run: scripts/githooks/install.sh"
  fi
fi

# 4. hot.md age -------------------------------------------------------------
HOT_UPD=$(grep -m1 '^updated:' wiki/hot.md | awk '{print $2}')
if [ -n "$HOT_UPD" ]; then
  AGE=$(( ( $(date +%s) - $(date -d "$HOT_UPD" +%s) ) / 86400 ))
  if [ "$AGE" -le 7 ]; then ok "hot.md updated ${AGE}d ago"; else warn "hot.md is ${AGE}d old (cap 7d) — update it before ending the session"; fi
fi

# 5. lint threshold (full mode only: lint takes ~14 s, too slow for every session start) --
if [ "$QUIET" = 0 ] && [ -x scripts/wiki-lint.sh ]; then
  LINT_JSON=$(./scripts/wiki-lint.sh --json 2>/dev/null)
  SCORE=$(printf '%s' "$LINT_JSON" | grep -m1 '"health_score"' | grep -oE '[0-9]+' | head -1)
  STALE=$(printf '%s' "$LINT_JSON" | grep -m1 '"stale_pages"' | grep -oE '[0-9]+' | head -1)
  if [ -n "$SCORE" ]; then
    if [ "$SCORE" -ge 90 ]; then ok "lint score $SCORE/100 (stale: ${STALE:-?})"; else warn "lint score $SCORE/100 (stale pages: ${STALE:-?}) — run ./scripts/freshness.py"; fi
  fi
fi

# 6. temporal validity (full mode only) ---------------------------------------
if [ "$QUIET" = 0 ] && [ -x scripts/wiki-temporal.sh ]; then
  if ./scripts/wiki-temporal.sh >/dev/null 2>&1; then ok "temporal check clean"; else warn "wiki-temporal.sh reports expired/broken supersedes|valid_until"; fi
fi

# 7. Claude Code version vs newest the wiki records --------------------------
if command -v claude >/dev/null 2>&1; then
  INST=$(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
  WIKI=$(ls raw/docs/changelog-*-to-*.md 2>/dev/null | sed -E 's/.*-to-([0-9.]+)\.md$/\1/' | sort -V | tail -1)
  if [ -n "$INST" ] && [ -n "$WIKI" ]; then
    if [ "$INST" = "$WIKI" ] || [ "$(printf '%s\n%s' "$INST" "$WIKI" | sort -V | tail -1)" = "$WIKI" ]; then
      ok "Claude Code $INST; wiki records up to $WIKI"
    else
      warn "Claude Code $INST installed; wiki's newest recorded version is $WIKI — changelog ingest overdue (run scripts/changelog-delta.sh)"
    fi
  fi
fi

# 8. project MCP servers actually loadable --------------------------------------
# Why: servers declared under mcpServers in .claude/settings.json are ignored by Claude Code, and
# mcp 2.x breaks the FastMCP import. Both failures are silent.
if grep -q '"mcpServers"' .claude/settings.json 2>/dev/null; then
  bad ".claude/settings.json has mcpServers — Claude Code ignores it; move servers to .mcp.json"
fi
if [ -f .mcp.json ]; then
  if [ -x .venv/bin/python ] && grep -q mem0-hot .mcp.json; then
    if .venv/bin/python -c "from mcp.server.fastmcp import FastMCP" 2>/dev/null; then
      ok "mem0-hot MCP server importable (.mcp.json)"
    else
      bad "mem0-hot MCP server cannot import FastMCP (mcp 2.x?). Run: uv pip install --python .venv/bin/python 'mcp>=1.2,<2'"
    fi
  fi
  if grep -q '"camoufox"' .mcp.json; then
    if ! .venv/bin/python -c "import camoufox, mcp.server.fastmcp" 2>/dev/null; then
      warn "Camoufox is not installed (optional) → JavaScript-rendered and bot-walled pages stay unreadable. Run: ./scripts/setup.sh --with-browser"
    elif ! .venv/bin/python -m camoufox path >/dev/null 2>&1; then
      warn "Camoufox browser not downloaded (optional). Run: .venv/bin/python -m camoufox fetch"
    else
      ok "camoufox MCP server importable and browser fetched (.mcp.json)"
    fi
  fi
else
  warn "no .mcp.json — mem0-hot recall tools are unavailable"
fi

# 9. automatic WebFetch -> Camoufox fallback hook -----------------------------------
if jq -e '.hooks.PostToolUse[]? | select(.matcher == "WebFetch") | .hooks[] | select(.command | test("webfetch_camoufox_fallback"))' .claude/settings.json >/dev/null 2>&1 \
   && [ -f scripts/hooks/webfetch_camoufox_fallback.py ]; then
  ok "WebFetch -> Camoufox fallback hook wired (PostToolUse)"
else
  warn "WebFetch -> Camoufox fallback hook missing from .claude/settings.json; JS-rendered pages won't be re-rendered automatically"
fi

# 10a. primary sources: not in the repo, fetched on demand -----------------------------
SRC=$(python3 scripts/sources.py status 2>/dev/null | head -1)
case "$SRC" in
  *" 0 match | 0 differ |"*) warn "source documents not installed → pages cannot be checked against raw/. Run: ./scripts/setup.sh --with-sources" ;;
  "") warn "scripts/sources.py status failed" ;;
  *) ok "$SRC" ;;
esac

# 10. other agents: Codex, OpenCode and Hermes read symlinks and generated files ------
if [ "$(readlink AGENTS.md 2>/dev/null)" = "CLAUDE.md" ] && [ "$(readlink .agents/skills 2>/dev/null)" = "../.claude/skills" ]; then
  if python3 scripts/agents/sync.py --check >/dev/null 2>&1; then
    ok "other agents in sync (AGENTS.md, .agents/skills, .codex/, .opencode/, opencode.json)"
  elif [ "$FIX" = 1 ]; then
    python3 scripts/agents/sync.py >/dev/null 2>&1 && ok "regenerated Codex and OpenCode configs from the Claude Code originals"
  else
    warn "Codex/OpenCode configs are stale → run ./scripts/agents/sync.py (agents, MCP servers or skills changed)"
  fi
else
  warn "AGENTS.md or .agents/skills symlink missing → Codex sees no instructions or skills. See wiki/project/cross-agent-setup.md"
fi

# 11. housekeeping: prune old fallback renders; surface maintenance work ------------
find outputs/webfetch-fallback -type f -mtime +30 -delete 2>/dev/null
if [ -f outputs/reverify-queue.md ]; then
  QN=$(grep -c '^- \[ \]' outputs/reverify-queue.md 2>/dev/null || echo 0)
  if [ "${QN:-0}" -gt 0 ]; then warn "$QN page(s) queued for re-verification by weekly maintenance (outputs/reverify-queue.md)"; else ok "re-verification queue empty"; fi
fi
if git show-ref --quiet --heads 2>/dev/null && git branch --list 'maintenance/*' | grep -q .; then
  warn "unmerged weekly maintenance branch(es): $(git branch --list 'maintenance/*' | tr -d ' *' | tr '\n' ' ')"
fi

# --- report -----------------------------------------------------------------
if [ "$QUIET" = 1 ]; then
  echo "doctor: ${RED} fail, ${WARN} warn$( [ $((RED+WARN)) -gt 0 ] && echo ' — run ./scripts/doctor.sh for details')"
else
  echo "agent-wiki-kit doctor — $(date +%F)"
  printf '%s\n' "${LINES[@]}"
  echo "  → $RED fail, $WARN warn"
fi
[ "$RED" -eq 0 ]
