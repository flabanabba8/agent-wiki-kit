# agent-wiki-kit — a self-maintaining Claude Code knowledge wiki

A source-backed wiki about Claude Code and agentic systems that maintains itself. **Check the wiki before answering from memory.** Why: training data is stale; every wiki claim traces to a file in `raw/`.

This file is also `AGENTS.md` (a symlink), so Claude Code, Codex, OpenCode and Hermes all read the same instructions. See [[cross-agent-setup]].

## Where things live

- `raw/` — primary sources, the verification baseline. They are other people's text, so they are **not in this repository**: `raw/` is gitignored and a fresh clone has none. `./scripts/sources.py fetch` downloads them from `sources/manifest.tsv`, which records each file's origin and a hash of its content when the wiki was last verified against it. `raw/docs/official/` is a snapshot of every code.claude.com page (`./scripts/refetch-docs.sh`); `raw/docs/changelog-*.md` holds CHANGELOG sections (`./scripts/changelog-delta.sh`); vendor docs are in `raw/docs/<vendor>/`; papers and posts in `raw/articles/`. Never edit an existing raw file; add new ones.
- `sources/` — `manifest.tsv` and `identifiers.txt` (every env var, flag and slash command found in `raw/`, so lint check 14 works without the sources). After verifying pages against new or changed sources, run `./scripts/sources.py manifest`.
- `wiki/<folder>/<slug>.md` — pages in 11 topic folders: `start`, `using`, `extending`, `automation`, `surfaces`, `deployment`, `reference`, `sdk-and-api`, `research`, `ecosystem`, `project`. Plus `wiki/index.md` (catalog), `wiki/hot.md` (session cache), `wiki/log.md` (append-only, current month; older months in `wiki/log-YYYY-MM.md`, not indexed).
- `scripts/` — harness (see [[harness]]): `doctor.sh`, `wiki-lint.sh`, `lint_identifiers.py`, `freshness.py`, `weekly-maintenance.sh`, `wiki-eval.py`, `answer-eval.py`, `mem0/`, `camoufox/`, `hooks/`.
- `evals/`, `tests/`, `.github/workflows/wiki-ci.yml` — retrieval and answer evals, unit tests, CI.
- `.claude/` is the source of truth for skills, agents, hooks and (with `.mcp.json`) MCP servers. `.agents/skills` is a symlink to `.claude/skills`. `.codex/`, `.opencode/agents/` and `opencode.json` are generated: edit the Claude Code file, then run `./scripts/agents/sync.py`. Adapters live in `scripts/agents/` and `.opencode/plugins/`.
- `outputs/` — generated reports (gitignored) and `reverify-queue.md`. `.mem0-data/` — local vector store, rebuilt from `wiki/`.

## Page frontmatter (required)

```yaml
---
title: Page Title
type: concept | how-to | reference | comparison | entity | research
tldr: "Under 50 chars"
sources: [raw/docs/official/file.md]
related: ["[[slug]]", "[[slug]]", "[[slug]]"]
created: YYYY-MM-DD
updated: YYYY-MM-DD
confidence: high | medium
last_verified: YYYY-MM-DD
aliases: [search-phrases-people-use]
valid_until: YYYY-MM-DD   # optional: prices, model lineups, version-specific limits
---
```

## Rules

- **One home per fact.** Each topic lives on exactly one page; other pages link to it. There are no source-summary pages: cite raw files in `sources:`. Why: duplicated facts drift apart and cost tokens.
- **Current facts only.** No "changed since", "previously" or "corrected" notes; corrections go in `log.md`. Delete outdated pages instead of deprecating them, and remove their index line and inbound links in the same change. Why: history on pages misleads retrieval and agents.
- **Every env var, slash command and `claude --flag` must appear in `raw/`** or its index `sources/identifiers.txt` (lint check 14). Why: plausible invented names survived for months before this check.
- **Contradictions:** a short `> [!contradiction]` callout only while two current sources disagree; replace it with the fact once one settles it.
- **In Claude Code, pin the model on every subagent.** Pass `model: "opus"` or `"sonnet"` on each Agent call. Why: an unpinned subagent inherits the session's model, and a fan-out on the most expensive model can exhaust a usage limit mid-task.
- Filenames and slugs are kebab-case and unique across folders. Check `aliases` and `./.venv/bin/python scripts/mem0/query_wiki.py` before creating a page.

## Workflows

- **Query:** `./.venv/bin/python scripts/mem0/query_wiki.py "<question>"` (semantic recall; deprecated pages rank last) → `wiki/index.md` if needed → read pages → answer with `[[slug]]` citations. If the wiki lacks the answer, check `raw/docs/official/` (grep `llms.txt`; run `./scripts/sources.py fetch` if `raw/` is empty), then the web. A page fetch that comes back as a JavaScript shell or bot wall is re-rendered in Camoufox automatically in Claude Code (WebFetch), OpenCode (webfetch) and Hermes (web_extract); read the saved file the notice points to. Codex has no page-fetch tool: use the `camoufox` MCP tool `fetch_page` there. In every agent, shell `curl` bypasses the fallback; use `./.venv/bin/python scripts/camoufox/fetch.py <url>` instead. File any durable finding into its owning page (anti-evaporation).
- **Ingest:** save the source to `raw/` with a SOURCE header (`<!-- SOURCE: <url> | fetched: <date> -->`) → find the page that owns the topic → update it (create a page only if no page owns the topic) → `wiki/index.md` → append `wiki/log.md` → `wiki/hot.md` → `./.venv/bin/python scripts/mem0/index_wiki.py` → `./scripts/sources.py manifest --accept <the new raw files>`.
- **Check:** `./scripts/wiki-lint.sh` (14 checks), `./scripts/wiki-temporal.sh`, `./.venv/bin/python -m pytest -q tests`, `./.venv/bin/python scripts/wiki-eval.py`. CI runs tests, lint ≥90, temporal and identifier checks on push.
- **Freshness:** a weekly cron job (`scripts/weekly-maintenance.sh`) refetches docs and the changelog on a local `maintenance/<date>` branch and lists pages whose cited sources changed in `outputs/reverify-queue.md`. `./scripts/freshness.py` classifies stale pages, using `sources/manifest.tsv` to tell whether a cited source changed. `./scripts/doctor.sh [--fix]` checks the whole harness.

## Memory layers

- **Wiki** — durable, citable knowledge; the source of truth.
- **mem0-hot** (MCP `remember`/`recall`) — ephemeral cross-session notes; a SessionEnd hook records a state note that SessionStart prints. Promote anything durable into a wiki page.

## Other agents

The same rules hold in every agent, enforced by the same scripts: an existing file under `raw/` is never edited (new files are fine), and wiki edits need a `wiki/log.md` entry. Claude Code uses hooks in `.claude/settings.json`; Codex uses `.codex/hooks.json` (trust the project, then review the hooks once with `/hooks`); OpenCode uses `.opencode/plugins/agent-wiki-kit.js`; Hermes keeps everything per user, so run `./scripts/agents/hermes/setup.sh` once per machine. The mem0 stores are opened per operation behind a lock, so several agents can use them at the same time. Details and what each agent cannot do: [[cross-agent-setup]].

## hot.md format

Emoji-coded lines under 120 chars, newest first, at most 30 (`./scripts/hot-compact.py` enforces it): `✅ completed | 📝 created | 🔧 fixed | ⚠️ gotcha | 🔄 in-progress | ❌ blocked | 💡 decision`
