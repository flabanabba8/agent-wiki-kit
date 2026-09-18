#!/usr/bin/env bash
# PreToolUse hook (matcher: Write|Edit|MultiEdit|NotebookEdit).
# Enforces the CLAUDE.md rule "raw/ is immutable" mechanically: block edits to an
# EXISTING file under raw/. Creating a new raw file (ingest) is allowed.
# Exit 2 = block; stderr is shown to the model as the reason.
#
# Other agents (Codex, OpenCode, Hermes) call the same rule through their own adapters:
#   guard-raw.sh --path FILE [--path FILE ...]     # exit 2 + reason on stderr if any is blocked
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
check() {
  local file="$1" abs
  [ -n "$file" ] || return 0
  case "$file" in /*) abs="$file" ;; *) abs="$ROOT/$file" ;; esac
  # Normalise before comparing: wiki/../raw/x.md and symlinked routes into raw/ must not slip past.
  abs="$(realpath -m -- "$abs" 2>/dev/null || printf '%s' "$abs")"
  case "$abs" in
    "$ROOT"/raw/*)
      if [ -e "$abs" ]; then
        echo "BLOCKED: $file is an existing raw/ source. raw/ is the immutable verification baseline — never edit it. To refresh a scraped doc use ./scripts/freshness.py --refetch; to add a source create a NEW file." >&2
        return 2
      fi
      ;;
  esac
  return 0
}
if [ "${1:-}" = "--path" ]; then
  while [ $# -gt 0 ]; do
    [ "$1" = "--path" ] && { shift; check "${1:-}" || exit 2; }
    shift || true
  done
  exit 0
fi
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)
check "$FILE" || exit 2
exit 0
