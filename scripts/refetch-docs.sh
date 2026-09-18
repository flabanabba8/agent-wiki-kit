#!/usr/bin/env bash
#
# refetch-docs.sh — snapshot the official Claude Code docs into raw/docs/official/.
#
# Why: code.claude.com serves an llms.txt index and every page as plain Markdown
# (https://code.claude.com/docs/en/<slug>.md), so a refresh is a curl loop — no
# browser automation needed.
# Each run overwrites raw/docs/official/<slug>.md and records the date in
# raw/docs/official/MANIFEST.txt; wiki-lint's hash check then flags derived pages,
# and scripts/freshness.py stops classing them as `snapshot`.
#
# This is the ONE sanctioned way raw/ content changes: a dated re-snapshot of a
# primary source, never an LLM edit. Existing hand-curated raw files are untouched.
#
# Usage: ./scripts/refetch-docs.sh [--dry-run]
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

BASE="https://code.claude.com/docs"
OUT="raw/docs/official"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
mkdir -p "$OUT"

INDEX=$(curl -sL --max-time 30 "$BASE/llms.txt") || { echo "failed to fetch llms.txt" >&2; exit 1; }
[ -n "$INDEX" ] || { echo "empty llms.txt" >&2; exit 1; }
printf '%s\n' "$INDEX" > "$OUT/llms.txt"

# Only English pages; the index lists https://code.claude.com/docs/en/<slug>.md
mapfile -t URLS < <(printf '%s\n' "$INDEX" | grep -oE 'https://code\.claude\.com/docs/en/[A-Za-z0-9_./-]+\.md' | sort -u)
echo "llms.txt lists ${#URLS[@]} English pages"
[ "$DRY" = 1 ] && { printf '  %s\n' "${URLS[@]}"; exit 0; }

OK=0; FAIL=0; TODAY=$(date +%F)
for u in "${URLS[@]}"; do
  slug="${u#$BASE/en/}"; slug="${slug%.md}"
  f="$OUT/${slug//\//__}.md"
  body=$(curl -sL --max-time 30 "$u") && [ -n "$body" ] || { echo "  FAIL $u" >&2; FAIL=$((FAIL+1)); continue; }
  {
    echo "<!-- SOURCE: $u | publisher: Anthropic (code.claude.com) | fetched: $TODAY | via scripts/refetch-docs.sh -->"
    printf '%s\n' "$body"
  } > "$f"
  OK=$((OK+1))
done

{
  echo "# Official Claude Code docs snapshot"
  echo "fetched: $TODAY"
  echo "pages: $OK ok, $FAIL failed"
  echo "index: $BASE/llms.txt"
  echo "claude_code_version_at_fetch: $(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
} > "$OUT/MANIFEST.txt"
echo "saved $OK pages to $OUT ($FAIL failed) — manifest: $OUT/MANIFEST.txt"
echo "next: ./scripts/wiki-lint.sh (hash check) and ./scripts/freshness.py — wiki pages citing raw/docs/claude-code-full-docs.md should migrate their sources: to the per-page files here as they are re-verified."
[ "$FAIL" -eq 0 ]
