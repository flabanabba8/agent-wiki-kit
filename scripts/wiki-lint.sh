#!/usr/bin/env bash
#
# wiki-lint.sh v2 — Automated quality checks for a Karpathy-style LLM wiki
#
# Usage:
#   ./scripts/wiki-lint.sh              # Human-readable report + save to outputs/
#   ./scripts/wiki-lint.sh --json       # JSON output only (for CI)
#   ./scripts/wiki-lint.sh --diff       # Compare against most recent saved report
#   ./scripts/wiki-lint.sh --ci         # Exit 1 if score < threshold (default 80)
#   ./scripts/wiki-lint.sh --ci --threshold 90
#
# CI Integration:
#   # As a git pre-commit hook (.git/hooks/pre-commit):
#   #!/bin/bash
#   ./scripts/wiki-lint.sh --ci --threshold 80
#
#   # As a GitHub Action:
#   - name: Wiki Lint
#     run: ./scripts/wiki-lint.sh --ci --threshold 80
#
# Scoring Formula (v2):
#   Structure  (40pts): -10/broken link, -5/orphan, -5/missing index, -3/missing required field
#   Content    (20pts): -5/thin page, -3/low confidence
#   Metadata   (20pts): proportional to tldr + last_verified + aliases completeness
#   Freshness  (20pts): -2/stale page (>90d), -1/hash-stale source, -5/stale hot.md, -5/stale overview.md
#
set -uo pipefail  # no -e: we handle errors explicitly to avoid grep/find false failures

WIKI_DIR="wiki"
RAW_DIR="raw"
OUTPUT_DIR="outputs"
HASH_FILE="outputs/.source-hashes.tsv"  # one manifest: <raw path>\t<sha256>
# Auto-detect content directories (all wiki/ subdirs that contain .md files)
CONTENT_DIRS=$(find "$WIKI_DIR" -mindepth 1 -maxdepth 1 -type d | sort | tr '\n' ' ')
SCORING_VERSION="v2"
THRESHOLD=80
MODE="human"  # human | json | diff | ci

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) MODE="json"; shift ;;
    --diff) MODE="diff"; shift ;;
    --ci) MODE="ci"; shift ;;
    --threshold) THRESHOLD="$2"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# -maxdepth removed to support nested topic folders
mapfile -t PAGES < <(find $CONTENT_DIRS -name "*.md" 2>/dev/null | sort | uniq)
TOTAL=${#PAGES[@]}

is_meta_link() { [[ "$1" == "wikilinks" ]]; }

# ═══════════════════════════════════════════════════════════════════════
#  TIER 1: STRUCTURAL CHECKS (zero LLM cost)
# ═══════════════════════════════════════════════════════════════════════

# ── 1. Broken wikilinks ───────────────────────────────────────────────
declare -a BROKEN_LINKS=()
mapfile -t ALL_LINKS < <(grep -roh '\[\[[a-z0-9-]*\]\]' "$WIKI_DIR"/ 2>/dev/null | sort -u | sed 's/\[\[//;s/\]\]//')
for link in "${ALL_LINKS[@]}"; do
  is_meta_link "$link" && continue
  found=$(find $CONTENT_DIRS -name "$link.md" 2>/dev/null | head -1)
  [[ -z "$found" ]] && BROKEN_LINKS+=("$link")
done

# ── 2. Orphan pages ──────────────────────────────────────────────────
declare -a ORPHANS=()
for f in "${PAGES[@]}"; do
  slug=$(basename "$f" .md)
  count=$(grep -rl "\[\[$slug\]\]" "$WIKI_DIR"/ 2>/dev/null | grep -v "$f" | wc -l)
  [[ $count -eq 0 ]] && ORPHANS+=("$slug")
done

# ── 3. Index completeness ────────────────────────────────────────────
declare -a NOT_INDEXED=()
for f in "${PAGES[@]}"; do
  slug=$(basename "$f" .md)
  grep -q "\[\[$slug\]\]" "$WIKI_DIR/index.md" 2>/dev/null || NOT_INDEXED+=("$slug")
done

# ── 4. Required frontmatter fields ──────────────────────────────────
declare -a MISSING_FM=()
REQUIRED_FIELDS=(title type sources created updated confidence)
for f in "${PAGES[@]}"; do
  if ! head -1 "$f" | grep -q "^---"; then
    MISSING_FM+=("$f: no frontmatter"); continue
  fi
  for field in "${REQUIRED_FIELDS[@]}"; do
    grep -q "^${field}:" "$f" || MISSING_FM+=("$f: missing $field")
  done
done

# ── 5. Recommended frontmatter fields ───────────────────────────────
NO_TLDR=0; NO_VERIFIED=0; NO_ALIASES=0
for f in "${PAGES[@]}"; do
  grep -q "^tldr:" "$f" || NO_TLDR=$((NO_TLDR+1))
  grep -q "^last_verified:" "$f" || NO_VERIFIED=$((NO_VERIFIED+1))
  grep -q "^aliases:" "$f" || NO_ALIASES=$((NO_ALIASES+1))
done

# ── 6. Thin pages (<100 words) ──────────────────────────────────────
declare -a THIN_PAGES=()
for f in "${PAGES[@]}"; do
  words=$(wc -w < "$f")
  [[ $words -lt 100 ]] && THIN_PAGES+=("$f ($words words)")
done

# ── 7. Low confidence pages ─────────────────────────────────────────
declare -a LOW_CONF=()
for f in "${PAGES[@]}"; do
  grep -q "^confidence: low" "$f" && LOW_CONF+=("$f")
done

# ── 8. Stale pages (last_verified > 90 days ago) ────────────────────
declare -a STALE_PAGES=()
NINETY_DAYS_AGO=$(date -d "90 days ago" +%Y-%m-%d 2>/dev/null || date -v-90d +%Y-%m-%d 2>/dev/null || echo "")
if [[ -n "$NINETY_DAYS_AGO" ]]; then
  for f in "${PAGES[@]}"; do
    verified=$(grep "^last_verified:" "$f" 2>/dev/null | head -1 | sed 's/last_verified: *//')
    if [[ -n "$verified" && "$verified" < "$NINETY_DAYS_AGO" ]]; then
      STALE_PAGES+=("$f (verified: $verified)")
    fi
  done
fi

# ── 9. Content hash verification ────────────────────────────────────
#    Hash every raw source file. Compare against stored hashes.
#    Flag wiki pages whose cited sources have changed since last_verified.
declare -a HASH_STALE=()
declare -A STORED_HASH=() NEW_HASH=()
if [[ -f "$HASH_FILE" ]]; then
  while IFS=$'\t' read -r hp hh; do [[ -n "$hp" ]] && STORED_HASH["$hp"]="$hh"; done < "$HASH_FILE"
fi
for f in "${PAGES[@]}"; do
  # Extract sources from frontmatter
  in_sources=0
  while IFS= read -r line; do
    [[ "$line" == "sources:" ]] && in_sources=1 && continue
    [[ $in_sources -eq 1 && "$line" =~ ^[[:space:]]*-[[:space:]]*(.*) ]] || { [[ $in_sources -eq 1 && ! "$line" =~ ^[[:space:]] ]] && break; continue; }
    [[ $in_sources -eq 0 ]] && continue
    src="${BASH_REMATCH[1]}"
    src="${src%\"}" ; src="${src#\"}"  # strip quotes
    [[ "$src" == *"[["* ]] && continue  # skip wikilinks in sources field
    [[ ! -f "$src" ]] && continue

    # Hash the raw source once per run, however many pages cite it
    if [[ -n "${NEW_HASH[$src]:-}" ]]; then
      current_hash="${NEW_HASH[$src]}"
    else
      current_hash=$(sha256sum "$src" 2>/dev/null | cut -d' ' -f1)
      NEW_HASH["$src"]="$current_hash"
    fi
    stored_hash="${STORED_HASH[$src]:-}"

    if [[ -n "$stored_hash" ]]; then
      if [[ "$current_hash" != "$stored_hash" ]]; then
        # Source changed — check if wiki page was verified after
        src_mtime=$(stat -c %Y "$src" 2>/dev/null || stat -f %m "$src" 2>/dev/null || echo 0)
        verified=$(grep "^last_verified:" "$f" 2>/dev/null | head -1 | sed 's/last_verified: *//')
        if [[ -n "$verified" ]]; then
          verified_epoch=$(date -d "$verified" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$verified" +%s 2>/dev/null || echo 0)
          if [[ $src_mtime -gt $verified_epoch ]]; then
            HASH_STALE+=("$f (source: $src changed)")
          fi
        fi
      fi
    fi
  done < "$f"
done
mkdir -p "$(dirname "$HASH_FILE")"
for hp in "${!NEW_HASH[@]}"; do printf '%s\t%s\n' "$hp" "${NEW_HASH[$hp]}"; done | sort > "$HASH_FILE.tmp" && mv "$HASH_FILE.tmp" "$HASH_FILE"

# ── 10. hot.md / overview.md currency ────────────────────────────────
HOT_STALE=0; OVERVIEW_STALE=0
SEVEN_DAYS_AGO=$(date -d "7 days ago" +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d 2>/dev/null || echo "")
if [[ -n "$SEVEN_DAYS_AGO" ]]; then
  for special in "$WIKI_DIR/hot.md" "$WIKI_DIR/overview.md"; do
    [[ ! -f "$special" ]] && continue
    updated=$(grep "^updated:" "$special" 2>/dev/null | head -1 | sed 's/updated: *//')
    if [[ -n "$updated" && "$updated" < "$SEVEN_DAYS_AGO" ]]; then
      if [[ "$special" == *"hot.md" ]]; then HOT_STALE=1
      else OVERVIEW_STALE=1; fi
    fi
  done
fi

# ── 11. Semantic link relevance (lightweight) ────────────────────────
#    For each wikilink in a page, check if the target page mentions
#    the source page's title or slug. Flag links where neither direction
#    has a textual mention.
declare -a WEAK_LINKS=()
LINK_SAMPLE_SIZE=20  # spot-check, not exhaustive
LINK_COUNT=0
for f in "${PAGES[@]}"; do
  [[ $LINK_COUNT -ge $LINK_SAMPLE_SIZE ]] && break
  slug=$(basename "$f" .md)
  title=$(grep "^title:" "$f" 2>/dev/null | head -1 | sed 's/title: *//;s/"//g')
  # Get outgoing links from this page
  mapfile -t outlinks < <(grep -oh '\[\[[a-z0-9-]*\]\]' "$f" 2>/dev/null | sed 's/\[\[//;s/\]\]//' | head -5)
  for target in "${outlinks[@]}"; do
    is_meta_link "$target" && continue
    target_file=""
    for d in $CONTENT_DIRS; do [[ -f "$d/$target.md" ]] && target_file="$d/$target.md" && break; done
    [[ -z "$target_file" ]] && continue
    # Does target mention source's slug or title (case-insensitive)?
    if ! grep -qi "$slug\|$title" "$target_file" 2>/dev/null; then
      # Does source mention target's title?
      target_title=$(grep "^title:" "$target_file" 2>/dev/null | head -1 | sed 's/title: *//;s/"//g')
      if ! grep -qi "$target\|$target_title" "$f" 2>/dev/null; then
        WEAK_LINKS+=("$f -> [[$target]]")
      fi
    fi
    LINK_COUNT=$((LINK_COUNT+1))
  done
done

# ── 12. Page size distribution ───────────────────────────────────────
SIZE_LT100=0; SIZE_100_300=0; SIZE_300_600=0; SIZE_600PLUS=0
for f in "${PAGES[@]}"; do
  w=$(wc -w < "$f")
  if [[ $w -lt 100 ]]; then SIZE_LT100=$((SIZE_LT100+1))
  elif [[ $w -lt 300 ]]; then SIZE_100_300=$((SIZE_100_300+1))
  elif [[ $w -lt 600 ]]; then SIZE_300_600=$((SIZE_300_600+1))
  else SIZE_600PLUS=$((SIZE_600PLUS+1))
  fi
done

# ── 13. Wikilink density (warn if <2 outgoing links per page) ────────
declare -a LOW_DENSITY=()
for f in "${PAGES[@]}"; do
  outlinks=$(grep -oh '\[\[[a-z0-9-]*\]\]' "$f" 2>/dev/null | wc -l)
  if [[ $outlinks -lt 2 ]]; then
    LOW_DENSITY+=("$(basename "$f" .md) ($outlinks links)")
  fi
done

# ── 14. Unsourced identifiers (env vars, slash commands, claude flags in no raw file) ──
declare -a UNSOURCED=()
if command -v python3 >/dev/null 2>&1 && [[ -f scripts/lint_identifiers.py ]]; then
  mapfile -t UNSOURCED < <(python3 scripts/lint_identifiers.py --lines 2>/dev/null)
fi

# ── Stats ────────────────────────────────────────────────────────────
TOTAL_WIKILINKS=$(grep -roh '\[\[[a-z0-9-]*\]\]' "$WIKI_DIR"/ 2>/dev/null | wc -l)
UNIQUE_WIKILINKS=$(grep -roh '\[\[[a-z0-9-]*\]\]' "$WIKI_DIR"/ 2>/dev/null | sort -u | wc -l)
TOTAL_WORDS=$(find "$WIKI_DIR" -name "*.md" -exec cat {} + 2>/dev/null | wc -w)
RAW_COUNT=$(find "$RAW_DIR" -name "*.md" 2>/dev/null | wc -l)

# ═══════════════════════════════════════════════════════════════════════
#  SCORING (v2)
# ═══════════════════════════════════════════════════════════════════════
#
#  Structure  (40pts): -10/broken link, -5/orphan, -5/missing index, -3/missing field
#  Content    (20pts): -5/thin page, -3/low confidence, -2/unsourced identifier
#  Metadata   (20pts): proportional to tldr + last_verified + aliases completeness
#  Freshness  (20pts): -2/stale page, -1/hash-stale source, -5/stale hot.md, -5/stale overview.md

STRUCTURE_DEDUCT=$(( ${#BROKEN_LINKS[@]}*10 + ${#ORPHANS[@]}*5 + ${#NOT_INDEXED[@]}*5 + ${#MISSING_FM[@]}*3 ))
STRUCTURE_SCORE=$(( 40 - (STRUCTURE_DEDUCT > 40 ? 40 : STRUCTURE_DEDUCT) ))

CONTENT_DEDUCT=$(( ${#THIN_PAGES[@]}*5 + ${#LOW_CONF[@]}*3 + ${#UNSOURCED[@]}*2 ))
CONTENT_SCORE=$(( 20 - (CONTENT_DEDUCT > 20 ? 20 : CONTENT_DEDUCT) ))

if [[ $TOTAL -gt 0 ]]; then
  TLDR_PCT=$(( (TOTAL - NO_TLDR) * 100 / TOTAL ))
  VERIFIED_PCT=$(( (TOTAL - NO_VERIFIED) * 100 / TOTAL ))
  ALIASES_PCT=$(( (TOTAL - NO_ALIASES) * 100 / TOTAL ))
  METADATA_SCORE=$(( (TLDR_PCT + VERIFIED_PCT + ALIASES_PCT) * 20 / 300 ))
else METADATA_SCORE=0; fi

FRESHNESS_DEDUCT=$(( ${#STALE_PAGES[@]}*2 + ${#HASH_STALE[@]}*1 + HOT_STALE*5 + OVERVIEW_STALE*5 ))
FRESHNESS_SCORE=$(( 20 - (FRESHNESS_DEDUCT > 20 ? 20 : FRESHNESS_DEDUCT) ))

HEALTH_SCORE=$(( STRUCTURE_SCORE + CONTENT_SCORE + METADATA_SCORE + FRESHNESS_SCORE ))
DATE=$(date +%Y-%m-%d)

# ── Issue counts ─────────────────────────────────────────────────────
ERRORS=0; WARNINGS=0
[[ ${#BROKEN_LINKS[@]} -gt 0 ]] && ERRORS=$((ERRORS + ${#BROKEN_LINKS[@]}))
[[ ${#ORPHANS[@]} -gt 0 ]] && ERRORS=$((ERRORS + ${#ORPHANS[@]}))
[[ ${#NOT_INDEXED[@]} -gt 0 ]] && ERRORS=$((ERRORS + ${#NOT_INDEXED[@]}))
[[ ${#MISSING_FM[@]} -gt 0 ]] && ERRORS=$((ERRORS + ${#MISSING_FM[@]}))
[[ ${#THIN_PAGES[@]} -gt 0 ]] && WARNINGS=$((WARNINGS + ${#THIN_PAGES[@]}))
[[ ${#LOW_CONF[@]} -gt 0 ]] && WARNINGS=$((WARNINGS + ${#LOW_CONF[@]}))
[[ $NO_TLDR -gt 0 ]] && WARNINGS=$((WARNINGS + 1))
[[ $NO_VERIFIED -gt 0 ]] && WARNINGS=$((WARNINGS + 1))
[[ $NO_ALIASES -gt 0 ]] && WARNINGS=$((WARNINGS + 1))
[[ ${#STALE_PAGES[@]} -gt 0 ]] && WARNINGS=$((WARNINGS + ${#STALE_PAGES[@]}))
[[ ${#HASH_STALE[@]} -gt 0 ]] && WARNINGS=$((WARNINGS + ${#HASH_STALE[@]}))
[[ $HOT_STALE -eq 1 ]] && WARNINGS=$((WARNINGS + 1))
[[ $OVERVIEW_STALE -eq 1 ]] && WARNINGS=$((WARNINGS + 1))
[[ ${#WEAK_LINKS[@]} -gt 0 ]] && WARNINGS=$((WARNINGS + ${#WEAK_LINKS[@]}))
[[ ${#LOW_DENSITY[@]} -gt 0 ]] && WARNINGS=$((WARNINGS + ${#LOW_DENSITY[@]}))
[[ ${#UNSOURCED[@]} -gt 0 ]] && WARNINGS=$((WARNINGS + ${#UNSOURCED[@]}))

# ═══════════════════════════════════════════════════════════════════════
#  OUTPUT
# ═══════════════════════════════════════════════════════════════════════

json_output() {
  cat <<ENDJSON
{
  "date": "$DATE",
  "scoring_version": "$SCORING_VERSION",
  "health_score": $HEALTH_SCORE,
  "structure_score": $STRUCTURE_SCORE,
  "content_score": $CONTENT_SCORE,
  "metadata_score": $METADATA_SCORE,
  "freshness_score": $FRESHNESS_SCORE,
  "errors": $ERRORS,
  "warnings": $WARNINGS,
  "total_pages": $TOTAL,
  "total_words": $TOTAL_WORDS,
  "total_wikilinks": $TOTAL_WIKILINKS,
  "unique_wikilinks": $UNIQUE_WIKILINKS,
  "raw_sources": $RAW_COUNT,
  "broken_links": ${#BROKEN_LINKS[@]},
  "orphan_pages": ${#ORPHANS[@]},
  "not_indexed": ${#NOT_INDEXED[@]},
  "missing_frontmatter": ${#MISSING_FM[@]},
  "thin_pages": ${#THIN_PAGES[@]},
  "low_confidence": ${#LOW_CONF[@]},
  "stale_pages": ${#STALE_PAGES[@]},
  "hash_stale": ${#HASH_STALE[@]},
  "hot_stale": $HOT_STALE,
  "overview_stale": $OVERVIEW_STALE,
  "weak_links": ${#WEAK_LINKS[@]},
  "low_density": ${#LOW_DENSITY[@]},
  "unsourced_identifiers": ${#UNSOURCED[@]},
  "checks": 14,
  "missing_tldr": $NO_TLDR,
  "missing_last_verified": $NO_VERIFIED,
  "missing_aliases": $NO_ALIASES,
  "size_distribution": {
    "lt100": $SIZE_LT100,
    "100_300": $SIZE_100_300,
    "300_600": $SIZE_300_600,
    "600plus": $SIZE_600PLUS
  }
}
ENDJSON
}

human_output() {
  echo "============================================"
  echo "  WIKI LINT — $DATE ($SCORING_VERSION)"
  echo "============================================"
  echo ""
  echo "  HEALTH SCORE: $HEALTH_SCORE/100"
  echo "    Structure:  $STRUCTURE_SCORE/40"
  echo "    Content:    $CONTENT_SCORE/20"
  for u in "${UNSOURCED[@]}"; do echo "      UNSOURCED: $u"; done
  echo "    Metadata:   $METADATA_SCORE/20"
  echo "    Freshness:  $FRESHNESS_SCORE/20"
  echo ""
  echo "  Pages: $TOTAL | Words: $TOTAL_WORDS | Links: $TOTAL_WIKILINKS ($UNIQUE_WIKILINKS unique) | Raw: $RAW_COUNT"
  echo ""

  if [[ $ERRORS -gt 0 ]]; then
    echo "  ERRORS ($ERRORS):"
    for l in "${BROKEN_LINKS[@]}"; do echo "    BROKEN LINK: [[$l]]"; done
    for o in "${ORPHANS[@]}"; do echo "    ORPHAN: $o"; done
    for n in "${NOT_INDEXED[@]}"; do echo "    NOT INDEXED: $n"; done
    for m in "${MISSING_FM[@]}"; do echo "    MISSING FIELD: $m"; done
    echo ""
  fi

  if [[ $WARNINGS -gt 0 ]]; then
    echo "  WARNINGS ($WARNINGS):"
    for t in "${THIN_PAGES[@]}"; do echo "    THIN PAGE: $t"; done
    for c in "${LOW_CONF[@]}"; do echo "    LOW CONFIDENCE: $c"; done
    for s in "${STALE_PAGES[@]}"; do echo "    STALE (>90d): $s"; done
    for h in "${HASH_STALE[@]}"; do echo "    SOURCE CHANGED: $h"; done
    [[ $HOT_STALE -eq 1 ]] && echo "    STALE: wiki/hot.md (updated >7 days ago)"
    [[ $OVERVIEW_STALE -eq 1 ]] && echo "    STALE: wiki/overview.md (updated >7 days ago)"
    for w in "${WEAK_LINKS[@]}"; do echo "    WEAK LINK: $w"; done
    for ld in "${LOW_DENSITY[@]}"; do echo "    LOW DENSITY: $ld"; done
    [[ $NO_TLDR -gt 0 ]] && echo "    MISSING TLDR: $NO_TLDR pages"
    [[ $NO_VERIFIED -gt 0 ]] && echo "    MISSING LAST_VERIFIED: $NO_VERIFIED pages"
    [[ $NO_ALIASES -gt 0 ]] && echo "    MISSING ALIASES: $NO_ALIASES pages"
    echo ""
  fi

  if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
    echo "  ALL CHECKS PASSED"
    echo ""
  fi

  echo "  Size: <100w: $SIZE_LT100 | 100-300w: $SIZE_100_300 | 300-600w: $SIZE_300_600 | 600+w: $SIZE_600PLUS"
  echo ""
  echo "============================================"
}

save_report() {
  mkdir -p "$OUTPUT_DIR"
  local report="$OUTPUT_DIR/lint-$DATE.md"
  local jsonfile="$OUTPUT_DIR/lint-$DATE.json"
  json_output > "$jsonfile"

  {
    echo "# Wiki Lint Report — $DATE"
    echo ""
    echo "**Scoring: $SCORING_VERSION** — Structure 40 + Content 20 + Metadata 20 + Freshness 20 = 100"
    echo ""
    echo "## Health Score: $HEALTH_SCORE/100"
    echo ""
    echo "| Category | Score | Deductions |"
    echo "|----------|-------|-----------|"
    echo "| Structure | $STRUCTURE_SCORE/40 | broken:${#BROKEN_LINKS[@]} orphan:${#ORPHANS[@]} unindexed:${#NOT_INDEXED[@]} fields:${#MISSING_FM[@]} |"
    echo "| Content | $CONTENT_SCORE/20 | thin:${#THIN_PAGES[@]} lowconf:${#LOW_CONF[@]} |"
    echo "| Metadata | $METADATA_SCORE/20 | no-tldr:$NO_TLDR no-verified:$NO_VERIFIED no-aliases:$NO_ALIASES |"
    echo "| Freshness | $FRESHNESS_SCORE/20 | stale:${#STALE_PAGES[@]} hash:${#HASH_STALE[@]} hot:$HOT_STALE overview:$OVERVIEW_STALE |"
    echo ""
    echo "## Stats"
    echo ""
    echo "| Metric | Count |"
    echo "|--------|-------|"
    echo "| Pages | $TOTAL |"
    echo "| Words | $TOTAL_WORDS |"
    echo "| Wikilinks | $TOTAL_WIKILINKS ($UNIQUE_WIKILINKS unique) |"
    echo "| Raw sources | $RAW_COUNT |"
    echo "| Errors | $ERRORS |"
    echo "| Warnings | $WARNINGS |"
    echo "| Weak links (sampled) | ${#WEAK_LINKS[@]} |"
    echo ""
    if [[ $ERRORS -gt 0 || $WARNINGS -gt 0 ]]; then
      echo "## Issues"
      echo ""
      for l in "${BROKEN_LINKS[@]}"; do echo "- **ERROR** Broken link: \`[[$l]]\`"; done
      for o in "${ORPHANS[@]}"; do echo "- **ERROR** Orphan: \`$o\`"; done
      for n in "${NOT_INDEXED[@]}"; do echo "- **ERROR** Not indexed: \`$n\`"; done
      for m in "${MISSING_FM[@]}"; do echo "- **ERROR** $m"; done
      for t in "${THIN_PAGES[@]}"; do echo "- **WARN** Thin: $t"; done
      for c in "${LOW_CONF[@]}"; do echo "- **WARN** Low confidence: \`$c\`"; done
      for s in "${STALE_PAGES[@]}"; do echo "- **WARN** Stale: $s"; done
      for h in "${HASH_STALE[@]}"; do echo "- **WARN** Source changed: $h"; done
      [[ $HOT_STALE -eq 1 ]] && echo "- **WARN** wiki/hot.md updated >7 days ago"
      [[ $OVERVIEW_STALE -eq 1 ]] && echo "- **WARN** wiki/overview.md updated >7 days ago"
      for w in "${WEAK_LINKS[@]}"; do echo "- **INFO** Weak link: $w"; done
      for ld in "${LOW_DENSITY[@]}"; do echo "- **INFO** Low link density: $ld"; done
      [[ $NO_TLDR -gt 0 ]] && echo "- **WARN** $NO_TLDR pages missing tldr"
      [[ $NO_VERIFIED -gt 0 ]] && echo "- **WARN** $NO_VERIFIED pages missing last_verified"
      [[ $NO_ALIASES -gt 0 ]] && echo "- **WARN** $NO_ALIASES pages missing aliases"
      echo ""
    fi
    echo "## Size Distribution"
    echo ""
    echo "| Range | Count |"
    echo "|-------|-------|"
    echo "| <100 words | $SIZE_LT100 |"
    echo "| 100-300 | $SIZE_100_300 |"
    echo "| 300-600 | $SIZE_300_600 |"
    echo "| 600+ | $SIZE_600PLUS |"
    echo ""
    echo "---"
    echo "*Generated by wiki-lint.sh ($SCORING_VERSION)*"
  } > "$report"

  echo "  Report saved: $report"
  echo "  JSON saved:   $jsonfile"
}

diff_output() {
  # Find previous report (not today's)
  local prev
  prev=$(ls -t "$OUTPUT_DIR"/lint-*.json 2>/dev/null | grep -v "lint-$DATE.json" | head -1)
  [[ -z "$prev" || ! -f "$prev" ]] && prev=$(ls -t "$OUTPUT_DIR"/lint-*.json 2>/dev/null | head -1)
  if [[ -z "$prev" || ! -f "$prev" ]]; then
    echo "No previous lint report found in $OUTPUT_DIR/"
    echo "Run without --diff first to create a baseline."
    exit 0
  fi

  local prev_date prev_score prev_pages prev_words prev_errors prev_warnings
  prev_date=$(basename "$prev" .json | sed 's/lint-//')
  prev_score=$(grep '"health_score"' "$prev" | grep -o '[0-9]*')
  prev_pages=$(grep '"total_pages"' "$prev" | grep -o '[0-9]*')
  prev_words=$(grep '"total_words"' "$prev" | grep -o '[0-9]*')
  prev_errors=$(grep '"errors"' "$prev" | head -1 | grep -o '[0-9]*')
  prev_warnings=$(grep '"warnings"' "$prev" | head -1 | grep -o '[0-9]*')
  prev_stale=$(grep '"stale_pages"' "$prev" | grep -o '[0-9]*' || echo 0)
  prev_thin=$(grep '"thin_pages"' "$prev" | grep -o '[0-9]*' || echo 0)

  local d_score=$((HEALTH_SCORE - prev_score))
  local d_pages=$((TOTAL - prev_pages))
  local d_words=$((TOTAL_WORDS - prev_words))
  local d_errors=$((ERRORS - prev_errors))
  local d_warnings=$((WARNINGS - prev_warnings))
  local d_stale=$((${#STALE_PAGES[@]} - prev_stale))
  local d_thin=$((${#THIN_PAGES[@]} - prev_thin))

  fmt() { local v=$1; [[ $v -gt 0 ]] && echo "+$v" || echo "$v"; }

  echo "============================================"
  echo "  WIKI LINT DIFF — $prev_date → $DATE"
  echo "============================================"
  echo ""
  echo "  Score:    $prev_score → $HEALTH_SCORE ($(fmt $d_score))"
  echo "  Pages:    $prev_pages → $TOTAL ($(fmt $d_pages))"
  echo "  Words:    $prev_words → $TOTAL_WORDS ($(fmt $d_words))"
  echo "  Errors:   $prev_errors → $ERRORS ($(fmt $d_errors))"
  echo "  Warnings: $prev_warnings → $WARNINGS ($(fmt $d_warnings))"
  echo "  Stale:    $prev_stale → ${#STALE_PAGES[@]} ($(fmt $d_stale))"
  echo "  Thin:     $prev_thin → ${#THIN_PAGES[@]} ($(fmt $d_thin))"
  echo ""

  # Highlight new issues
  if [[ $d_errors -gt 0 ]]; then echo "  ✗ $d_errors new error(s)"; fi
  if [[ $d_stale -gt 0 ]]; then echo "  ✗ $d_stale new stale page(s)"; fi
  if [[ $d_score -gt 0 ]]; then echo "  ✓ Score improved by $d_score points"
  elif [[ $d_score -lt 0 ]]; then echo "  ✗ Score degraded by $((-d_score)) points"
  else echo "  = Score unchanged"; fi
  echo ""
  echo "============================================"
}

# ── MAIN ────────────────────────────────────────────────────────────
case "$MODE" in
  json)
    json_output
    ;;
  diff)
    save_report
    diff_output
    ;;
  ci)
    json_output
    save_report >/dev/null 2>&1
    if [[ $HEALTH_SCORE -lt $THRESHOLD ]]; then
      echo "FAIL: Health score $HEALTH_SCORE < threshold $THRESHOLD" >&2
      exit 1
    fi
    ;;
  human)
    human_output
    save_report
    ;;
esac
