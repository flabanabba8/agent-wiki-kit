#!/usr/bin/env bash
# Wire this repository into Hermes Agent.
#
# Why a script: Hermes keeps MCP servers, plugins and project trust in the user's ~/.hermes, not in
# the project, so a clone cannot carry them. Run once per machine. Idempotent; undo with --remove.
#   - trusts the repo so its skills load from .agents/skills (a symlink to .claude/skills)
#   - links and enables the agent-wiki-kit plugin: raw/ guard, Camoufox fallback, log reminder
#   - registers the mem0-hot and camoufox MCP servers by absolute path
# Instructions need nothing: Hermes reads AGENTS.md, a symlink to CLAUDE.md.
set -uo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PLUGIN_LINK="${HERMES_HOME:-$HOME/.hermes}/plugins/agent-wiki-kit"
command -v hermes >/dev/null || { echo "hermes is not installed; nothing to do." >&2; exit 1; }
SERVERS="mem0-hot:scripts/mem0/mcp_server.py camoufox:scripts/camoufox/mcp_server.py"

if [ "${1:-}" = "--remove" ]; then
  hermes plugins disable agent-wiki-kit </dev/null >/dev/null 2>&1
  [ -L "$PLUGIN_LINK" ] && rm -f "$PLUGIN_LINK"
  for s in $SERVERS; do printf 'y\n' | hermes mcp remove "${s%%:*}" >/dev/null 2>&1; done
  hermes skills untrust "$R" </dev/null >/dev/null 2>&1
  echo "Removed the agent-wiki-kit plugin, MCP servers and project trust from Hermes."
  exit 0
fi

[ -x "$R/.venv/bin/python" ] || { echo "No .venv yet. Run scripts/mem0/setup.sh first." >&2; exit 1; }
hermes skills trust "$R" </dev/null 2>&1 | tail -2
mkdir -p "$(dirname "$PLUGIN_LINK")" && ln -sfn "$R/scripts/agents/hermes/agent-wiki-kit" "$PLUGIN_LINK"
hermes plugins enable agent-wiki-kit </dev/null >/dev/null 2>&1
# Read the config rather than the rendered table, which wraps differently without a terminal.
if "$R/.venv/bin/python" -c "import sys,yaml,os; d=yaml.safe_load(open(os.path.join(os.environ.get('HERMES_HOME', os.path.expanduser('~/.hermes')),'config.yaml'))) or {}; sys.exit(0 if 'agent-wiki-kit' in ((d.get('plugins') or {}).get('enabled') or []) else 1)" 2>/dev/null; then
  echo "plugin: agent-wiki-kit enabled"
else
  echo "plugin: NOT enabled; run 'hermes plugins enable agent-wiki-kit'" >&2
fi
for s in $SERVERS; do
  name="${s%%:*}"; file="${s#*:}"
  if hermes mcp list </dev/null 2>&1 | grep -q "^ *$name "; then
    echo "mcp: $name already registered"
  else
    # `mcp add` launches the server, lists its tools and asks once whether to enable them.
    printf 'Y\n' | hermes mcp add "$name" --command "$R/.venv/bin/python" --args "$R/$file" 2>&1 | grep -E "Saved|rror" || echo "mcp: $name could not be added" >&2
  fi
done
echo "Done. Start a new Hermes session inside $R."
