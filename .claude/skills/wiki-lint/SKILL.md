---
name: wiki-lint
description: "Run the wiki quality checks. Use when the user says 'lint the wiki', wants a health score, or before committing wiki changes."
user-invocable: true
disable-model-invocation: true
allowed-tools: Bash(./scripts/wiki-lint.sh*) Bash(python3 scripts/lint_identifiers.py*) Bash(./scripts/wiki-temporal.sh*) Read Grep Glob
---

# Lint the wiki

Run `./scripts/wiki-lint.sh` (about 10 seconds, no LLM cost). Scoring: Structure 40 + Content 20 + Metadata 20 + Freshness 20 = 100.

| # | Check | Deduction |
|---|---|---|
| 1 | Broken wikilinks | -10 each (structure) |
| 2 | Orphan pages | -5 each (structure) |
| 3 | Pages missing from index.md | -5 each (structure) |
| 4 | Missing required frontmatter | -3 each (structure) |
| 5 | Missing tldr / last_verified / aliases | proportional (metadata) |
| 6 | Thin pages (<100 words) | -5 each (content) |
| 7 | Low-confidence pages | -3 each (content) |
| 8 | Stale pages (last_verified >90 days) | -2 each (freshness) |
| 9 | Cited raw file changed since verification | -1 each (freshness) |
| 10 | hot.md older than 7 days | -5 (freshness) |
| 11 | Weak links (spot check) | reported |
| 12 | Page size distribution | reported |
| 13 | Wikilink density | reported |
| 14 | Unsourced identifiers: env vars, slash commands, `claude --flags` in no raw file | -2 each (content) |

Other modes: `--json`, `--diff`, `--ci --threshold 90`. Also run `./scripts/wiki-temporal.sh` (expired `valid_until`) and `./.venv/bin/python -m pytest -q tests`.

For a deeper review, run the `wiki-auditor` agent with one lens per instance (stale, duplication, fabrication, code, structure). Legitimate third-party identifiers go in `scripts/lint-identifiers-allow.txt` with a reason.
