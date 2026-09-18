---
title: agent-wiki-kit Harness
type: reference
tldr: "How this wiki repo checks and maintains itself"
sources:
  - scripts/doctor.sh
  - scripts/wiki-lint.sh
  - scripts/lint_identifiers.py
  - scripts/lint-identifiers-allow.txt
  - scripts/wiki-temporal.sh
  - scripts/freshness.py
  - scripts/refetch-docs.sh
  - scripts/changelog-delta.sh
  - scripts/weekly-maintenance.sh
  - scripts/install-maintenance-cron.sh
  - scripts/wiki-eval.py
  - scripts/eval-harvest.py
  - scripts/answer-eval.py
  - evals/wiki-eval.yaml
  - evals/answer-eval.yaml
  - scripts/update-stats.py
  - scripts/hot-compact.py
  - scripts/githooks/install.sh
  - scripts/githooks/reindex.sh
  - scripts/hooks/session-start.sh
  - scripts/hooks/session-end.sh
  - scripts/hooks/guard-raw.sh
  - scripts/hooks/stop-anti-evaporation.sh
  - scripts/hooks/webfetch_camoufox_fallback.py
  - .claude/settings.json
  - .mcp.json
  - .github/workflows/wiki-ci.yml
  - tests/test_freshness.py
  - tests/test_lint_identifiers.py
  - tests/test_temporal.py
  - tests/test_webfetch_fallback.py
  - scripts/agents/sync.py
  - scripts/agents/shared.py
  - scripts/sources.py
related: ["[[mem0]]", "[[camoufox]]", "[[hooks]]", "[[agent-evals]]", "[[settings]]"]
created: 2026-09-15
updated: 2026-09-18
confidence: high
last_verified: 2026-09-18
aliases: [wiki-harness, doctor-sh, wiki-lint, weekly-maintenance, wiki-ci]
---

# agent-wiki-kit Harness

This repo keeps its wiki healthy with scripts, Claude Code hooks, a weekly cron job and CI. Prose rules alone don't hold, so these checks are mechanical. The table is the quick reference. Sections below explain each part.

| Command | What it does |
|---|---|
| `./scripts/doctor.sh [--fix] [--quiet]` | Checks the harness is wired up |
| `./scripts/wiki-lint.sh [--json\|--diff\|--ci --threshold N]` | 14 structural checks with a score out of 100 |
| `python3 scripts/lint_identifiers.py [--lines\|--json\|--ci]` | Flags invented env vars, slash commands and `claude` flags |
| `./scripts/wiki-temporal.sh` | Fails on pages past their `valid_until` date |
| `./scripts/freshness.py [--bump\|--refetch\|--days N\|--json]` | Sorts stale pages by why they're stale |
| `./scripts/refetch-docs.sh [--dry-run]` | Re-downloads the official docs into `raw/docs/official/` |
| `./scripts/changelog-delta.sh [--dry-run]` | Saves new Claude Code changelog versions as a new raw file |
| `./scripts/weekly-maintenance.sh` | Weekly refresh committed to a local branch |
| `./.venv/bin/python scripts/wiki-eval.py [--json\|--ci 0.8]` | Retrieval eval, hit@k and MRR |
| `./.venv/bin/python scripts/answer-eval.py [--limit N\|--model sonnet]` | Answer-quality eval (spends tokens) |
| `./scripts/hot-compact.py [--check]` | Enforces the `hot.md` format |

## doctor.sh

`./scripts/doctor.sh` runs these checks:

1. The `.venv` exists and `mem0` imports.
2. The semantic index manifest is newer than every wiki page.
3. The git reindex hooks are installed.
4. `wiki/hot.md` was updated within the last 7 days.
5. The lint score is at least 90 (full mode only).
6. `wiki-temporal.sh` is clean (full mode only).
7. The installed `claude --version` isn't newer than the newest `raw/docs/changelog-*-to-*.md`.
8. `.claude/settings.json` has no `mcpServers` key, the `mem0-hot` server can import FastMCP, and Camoufox is installed and its browser fetched.
9. The WebFetch fallback hook is wired.
10. Housekeeping: it deletes `outputs/webfetch-fallback` renders older than 30 days, warns about unchecked items in `outputs/reverify-queue.md`, and warns about unmerged `maintenance/*` branches.

`--fix` runs `scripts/mem0/setup.sh`, builds or refreshes the index and installs the git hooks. `--quiet` prints a single summary line. The script exits 1 if any check fails.

## Claude Code hooks (.claude/settings.json)

For hook mechanics, see [[hooks]].

| Event | Script | Effect |
|---|---|---|
| `SessionStart` (`startup\|resume`) | `session-start.sh` | Puts `doctor.sh --quiet`, the `hot.md` date and the last 3 session notes into context |
| `PreToolUse` (`Write\|Edit\|MultiEdit\|NotebookEdit`) | `guard-raw.sh` | Exit 2 blocks edits to an **existing** file under `raw/`; creating a new raw file is allowed. The path is resolved first, so `..` routes and symlinks into `raw/` are caught |
| `Stop` | `stop-anti-evaporation.sh` | Blocks the stop once if wiki pages changed but `wiki/log.md` didn't. `stop_hook_active` stops it from looping |
| `PostToolUse` / `PostToolUseFailure` (`WebFetch`) | `webfetch_camoufox_fallback.py` | Re-renders incomplete pages with Camoufox ([[camoufox]]) |
| `SessionEnd` | `session-end.sh` | Writes a session note to mem0-hot ([[mem0]]) |

The settings file also pre-approves read-only tools, `git`, and the lint, eval, doctor, freshness and Camoufox fetch commands. `.mcp.json` declares the `mem0-hot` and `camoufox` MCP servers. For how settings files combine, see [[settings]].

The same scripts enforce these rules in Codex, OpenCode and Hermes through thin adapters, and `doctor.sh` warns when the files generated for those agents are stale. See [[cross-agent-setup]].

## wiki-lint.sh: 14 checks

1. Broken wikilinks: a double-bracket target with no matching file
2. Orphan pages that nothing links to
3. Pages missing from `wiki/index.md`
4. Required frontmatter: `title`, `type`, `sources`, `created`, `updated`, `confidence`
5. Recommended frontmatter: `tldr`, `last_verified`, `aliases`
6. Thin pages under 100 words
7. `confidence: low`
8. `last_verified` older than 90 days
9. A cited raw file whose hash changed after `last_verified` (hashes kept in `outputs/.source-hashes.tsv`)
10. `hot.md` or `overview.md` not updated for 7 days
11. Weak links, where neither page mentions the other (a sample of 20)
12. Page size distribution
13. Fewer than 2 outgoing links on a page
14. Unsourced identifiers, taken from `lint_identifiers.py --lines`

The score is out of 100:

| Category | Points | Deductions |
|---|---|---|
| Structure | 40 | 10 per broken link, 5 per orphan, 5 per unindexed page, 3 per missing field |
| Content | 20 | 5 per thin page, 3 per low-confidence page, 2 per unsourced identifier |
| Metadata | 20 | Proportional to how many pages have tldr, last_verified and aliases |
| Freshness | 20 | 2 per stale page, 1 per changed source, 5 for a stale `hot.md`, 5 for a stale `overview.md` |

Each run saves `outputs/lint-<date>.md` and `.json`.

`lint_identifiers.py` scans `wiki/*/*.md` for three kinds of identifier: `CLAUDE_*`/`ANTHROPIC_*` env vars, slash commands written in inline code, and `claude ... --flag` patterns. Anything that doesn't appear in `raw/`, `scripts/`, `.claude/`, `.mcp.json` or `CLAUDE.md` gets flagged. Legitimate exceptions go in `scripts/lint-identifiers-allow.txt`, one per line with a reason.

## Sources are fetched, not shipped

`raw/` holds other publishers' documentation and papers, so it is gitignored and a clone has none of it. `scripts/sources.py` stands in for it:

| Command | What it does |
|---|---|
| `sources.py fetch` | Downloads every source in `sources/manifest.tsv` into `raw/`. Official docs go through `refetch-docs.sh`, changelog files are sliced from the upstream CHANGELOG by version range, and a page that comes back as a JavaScript shell is retried in Camoufox |
| `sources.py status` | Counts sources that match the manifest, differ from it, or are missing |
| `sources.py changed`, `sources.py new` | Paths that differ from the verified snapshot, and files the manifest does not list yet. Weekly maintenance uses both |
| `sources.py manifest` | Rebuilds the manifest and `sources/identifiers.txt` from `raw/`; `--accept` re-records named files only |

The manifest hashes each file's **body**, not its bytes: the SOURCE header carries the fetch date, so a byte hash could never match a refetch. Unchanged upstream text therefore matches exactly, and changed text is reported. A difference is not an error. It means nobody has checked the page against the new text yet. The comparison ignores blank lines, trailing spaces and bare code fences. Rendered web pages such as engineering posts are fetched as text but never compared, because the verified copy was converted to Markdown and no refetch reproduces it; published articles do not drift.

`sources/identifiers.txt` lists every environment variable, flag and slash-style token found in `raw/`. Lint check 14 reads it, so the no-invented-names rule still holds in a fresh clone and in CI, where no sources exist. CI also fails if anything under `raw/` other than its README is committed.

## Freshness and source refresh

`freshness.py` sorts pages whose `last_verified` is past the window (90 days by default) into four groups:

| Group | Meaning | What to do |
|---|---|---|
| `drifted` | A cited raw file differs from its snapshot in `sources/manifest.tsv`, or, if you track `raw/` in git, has a commit newer than `last_verified` beyond its creation commit | Re-verify by hand, then `sources.py manifest --accept` |
| `snapshot` | Cites a `raw/docs/` file fetched longer ago than the window | Refresh with `--refetch`, then re-check |
| `unfetched` | The cited source is in the manifest but not on disk | `./scripts/sources.py fetch` |
| `frozen` | Sources are unchanged | `--bump` sets `last_verified` to today |
| `no-src` | No raw sources listed | Judgement call |

`refetch-docs.sh` downloads `https://code.claude.com/docs/llms.txt` and every English page with curl, writing each to `raw/docs/official/<slug>.md` (nested paths use `__`) and recording the run in `MANIFEST.txt`. It is the only sanctioned way to overwrite existing raw files. `changelog-delta.sh` compares the upstream `CHANGELOG.md` with the newest ingested version and writes a new `raw/docs/changelog-<first>-to-<last>.md`.

`weekly-maintenance.sh` skips the week if tracked files have uncommitted changes. Otherwise it does this on a new `maintenance/YYYY-MM-DD` branch:

1. Refetches the official docs and runs the changelog delta.
2. Writes `outputs/reverify-queue.md`, listing each page that cites a changed official doc plus any new changelog file.
3. Runs `freshness.py --bump`, reindexes and runs lint.
4. Commits the result and switches back to the original branch.

It never pushes. `./scripts/install-maintenance-cron.sh` installs the cron entry, which runs Mondays at 06:17 and logs to `outputs/.maintenance.log`.

## Evals

For eval concepts, see [[agent-evals]].

- **Retrieval eval.** `evals/wiki-eval.yaml` holds 40 questions with `k: 5`, 14 of them marked `hard`. `wiki-eval.py` runs each question through the same search and deprecated-page ordering as `query_wiki.py`. A question passes if any expected page is in the top k, or is ranked first for `top1` questions. It reports hit@k, MRR and a hard-subset rate, lists expected pages that don't exist, and writes `outputs/eval-<date>.json`.
- **Harvesting real queries.** `eval-harvest.py` lists queries from `outputs/.query-log.jsonl` that aren't in the eval yet. `eval-harvest.py --add "query" page [page ...]` appends one as a labelled question.
- **Answer eval.** `evals/answer-eval.yaml` holds 8 questions. `answer-eval.py` answers each with `claude -p` in this repo, with hooks disabled and read-only tools. It passes an answer only if it cites one of the `must_cite` pages as a double-bracket citation and contains every `must_mention` string. Grading is deterministic, and the script refuses to run on a Fable model. Results go to `outputs/answer-eval-<date>.json`.

## Stats and hot.md

`build-index.py` regenerates `wiki/index.md` from each page's folder, slug and `tldr`, so the catalog cannot fall behind the pages; `--check` fails when it is stale.

- **`hot-compact.py`** enforces the `hot.md` rules. It drops duplicate entries (ignoring dates), keeps the newest 30, sets `updated:` and reports lines of 120 characters or more without cutting them. `--check` exits 1 if it would change anything.
- **`update-stats.py`** recomputes page, word, link, raw-file, skill and agent counts, plus lint and eval results, and rewrites the counts in `README.md`, `wiki/meta/wiki-stats.md` and `wiki/hot.md` (`--check` for CI). Its README and `hot.md` patterns still look up the older folder keys (`concepts`, `entities`, `workflows`, `how-to`, `comparisons`, `sources`, `reference`, `meta`), which are not in its `DIRS` list. Against the current layout it raises `KeyError` before writing anything.

## Git hooks, CI and tests

- **Git hooks.** `scripts/githooks/install.sh` symlinks `reindex.sh` as both `post-commit` and `post-merge`. After each commit or merge, the hook diffs `HEAD@{1}..HEAD` for `wiki/*.md` changes and, if there are any, runs `index_wiki.py` in the background with output to `.mem0-data/reindex.log`.
- **CI.** `.github/workflows/wiki-ci.yml` runs on every push and pull request with Python 3.12: `python -m pytest -q tests`, `./scripts/wiki-lint.sh --ci --threshold 90`, `./scripts/wiki-temporal.sh` and `python scripts/lint_identifiers.py --ci`.
- **Tests.** `tests/` holds 55 tests, all using throwaway directories or monkeypatched network calls:
  - `test_freshness.py`: frozen vs drifted classification
  - `test_temporal.py`: exit codes for `valid_until`
  - `test_lint_identifiers.py`: flagging, the allowlist, CI exit code, and backtick-slash false positives
  - `test_webfetch_fallback.py`: summary and raw-HTML heuristics, the blocked-domain cache, and ignoring tools other than WebFetch
  - `test_weekly_maintenance.py`: every path `weekly-maintenance.sh` stages is committable, and a failed `git add` is not silent
  - `test_store_lock.py`: a second process waits for the mem0 store instead of crashing, gets a clear error if it stays busy, and a dead holder never wedges it
  - `test_agent_adapters.py`: the raw guard holds for every agent's argument names, patch bodies, `..` routes and symlinks, and the Hermes plugin stays silent outside this repo
  - `test_agent_sync.py`: generated Codex and OpenCode files match the Claude Code originals, every skill is strict YAML, and the OpenCode plugin enforces the rules under Node
  - `test_sources.py`: no third-party source is tracked in git, every source has an origin, the identifier lint passes with no sources, and the body hash ignores the fetch-date header

## Memory layers

- **The wiki** (`wiki/`) is the durable, citable record.
- **The mem0 `wiki` index** makes it searchable, and you can rebuild it at any time.
- **`mem0-hot`** holds short-lived session notes.

Details are on [[mem0]].
