# agent-wiki-kit

A knowledge wiki that maintains itself, plus the harness that keeps it honest. It ships as a working example, a source-backed wiki about Claude Code and agentic systems, and it is built to be pointed at your own subject.

It currently holds **75 wiki pages** in 11 topic folders, cross-linked with **1,200+ wikilinks** and verified against **403 raw source files**. Every claim traces to a primary source, every identifier is checked against those sources, and the same rules are enforced whether you work in Claude Code, OpenAI Codex, OpenCode or Hermes Agent.

> [!IMPORTANT]
> **Two things to know before you start.**
>
> 1. **The source documents are not in this repository.** They are other publishers' documentation and papers, so a clone contains none of them. **If you want them, run the install script:**
>    ```bash
>    ./scripts/setup.sh --full            # sources and the Camoufox browser
>    ./scripts/setup.sh --with-sources    # sources only
>    ```
>    The wiki reads fine without them. You need them to verify a page against its sources, to run the freshness checks, or to ingest updates.
> 2. **To build your own project with this kit, ask your agent to do it.** Open this folder in Claude Code, Codex, OpenCode or Hermes and say what you want, for example: *"Use this kit to start a new wiki about Kubernetes networking."* The agent follows the bundled `new-wiki` skill: it agrees the structure with you, clears the example content, keeps the harness, ingests your first sources and proves the checks pass. You are not expected to rewire it by hand.

## How it works

The pattern is Andrej Karpathy's LLM wiki: immutable sources in `raw/`, LLM-maintained pages in `wiki/`, and a schema in `CLAUDE.md` that tells the agent how to keep them consistent. This kit adds the machinery that stops such a wiki from rotting:

- **One home per fact.** Each topic lives on exactly one page. Pages state current facts only, and corrections go in a log, never on the page.
- **No invented names.** Every environment variable, slash command and CLI flag on a page must appear in a source. A lint check enforces it, and it works even without the sources present.
- **Freshness from evidence, not the calendar.** A page is stale when a source it cites has changed, not because 90 days passed.
- **Retrieval that is measured.** A local semantic index (mem0, a small embedding model, no API key) answers questions, and an eval proves it still finds the right page.
- **Rules enforced by hooks, not prose.** Existing sources cannot be edited, wiki edits need a log entry, and unreadable web pages are re-rendered in a real browser automatically.

## Quick start

Requirements: `git` and Python 3.10 or newer. No API key. A basic installation needs about 1.5 GB of disk for the local embedding stack.

### Full installation (recommended)

One command sets up everything: the Python environment, the local semantic index, the git hooks, the **source documents** (about 400 files) and the **Camoufox browser** that reads pages plain HTTP cannot.

```bash
git clone https://github.com/flabanabba8/agent-wiki-kit.git
cd agent-wiki-kit
./scripts/setup.sh --full
```

Allow a few minutes and about 3 GB of disk: 1.5 GB for the Python environment, 1.2 GB for the browser, and about 30 MB of source documents. The script is safe to run again: every step checks before it acts.

### Basic installation

If you only want to read and query the wiki, skip the two large downloads. You can add either later.

```bash
./scripts/setup.sh                  # environment, semantic index, git hooks, health check
./scripts/setup.sh --with-sources   # add the source documents
./scripts/setup.sh --with-browser   # add the Camoufox browser
```

A basic installation tells you at the end what it left out, and `./scripts/doctor.sh` keeps reporting it until you install it.

Then open the folder in your agent and ask a question. The agent searches the wiki first:

```bash
./.venv/bin/python scripts/mem0/query_wiki.py "how do hooks block a tool call"
```

## Make it yours

Ask your agent, in plain words. Some requests that work:

- *"Use this kit to start a new wiki about our payments platform."* This runs the `new-wiki` skill.
- *"Ingest this document into the wiki."* with a URL or a file. This runs the `ingest` skill.
- *"Is the wiki up to date?"* This runs the `freshness-check` skill.
- *"Lint the wiki."* This runs the 14 structural checks and scores the result.

The agent reads `CLAUDE.md` (also served as `AGENTS.md`), which holds the page format, the rules and the workflows. Change that file to change how your wiki is kept.

## The source documents

`raw/` is gitignored except for its README. What the repository does commit is:

| File | Purpose |
|---|---|
| `sources/manifest.tsv` | Where each source came from, and a hash of its content when the wiki was last verified against it |
| `sources/identifiers.txt` | Every environment variable, flag and slash command found in the sources, so the identifier lint runs without them |

```bash
./scripts/sources.py fetch      # download everything in the manifest into raw/
./scripts/sources.py status     # present, missing, or different from the verified snapshot
./scripts/freshness.py          # which pages cite a source that has changed
```

A fetched file that differs from the manifest is not an error. It means upstream changed after the page was checked, and that page is due a second look. After re-verifying, record the new state with `./scripts/sources.py manifest`. If you publish a fork, keep `raw/` ignored: redistributing those documents is between you and their publishers.

## Works from four agents

Claude Code's files are the source of truth, and the same rules hold everywhere.

| | How it gets this repo's instructions, skills, MCP servers and rules |
|---|---|
| **Claude Code** | Native: `CLAUDE.md`, `.claude/`, `.mcp.json` |
| **Codex** | `AGENTS.md` and `.agents/skills` symlinks, generated `.codex/`. Trust the project, then approve the hooks once with `/hooks` |
| **OpenCode** | The same symlinks, generated `opencode.json` and `.opencode/agents/`, plus `.opencode/plugins/agent-wiki-kit.js`. No setup |
| **Hermes** | The same symlinks, plus `./scripts/agents/hermes/setup.sh` once per machine, because Hermes keeps MCP servers, plugins and trust per user |

Edit the Claude Code file, run `./scripts/agents/sync.py`, commit both. The memory layer is safe to share: stores are opened per operation behind a lock, so agents running at the same time wait for each other instead of crashing. Details: `wiki/project/cross-agent-setup.md`.

## Wiki map

| Folder | Pages | Covers |
|---|---|---|
| **Start** | 3 | What Claude Code is, installation, how the agentic loop works |
| **Using** | 9 | Prompting and workflows, CLAUDE.md and memory, context, permissions, sandboxing, sessions, models, interface, costs |
| **Extending** | 6 | Skills, subagents, agent teams, hooks, MCP, plugins |
| **Automation** | 7 | Worktrees and background work, workflows, routines and scheduling, channels, artifacts, headless mode |
| **Surfaces** | 6 | IDEs, desktop app, web and Remote Control, Chrome and computer use, Slack, CI/CD and code review |
| **Deployment** | 6 | Cloud providers, LLM gateways, settings, enterprise admin, data and privacy, network configuration |
| **Reference** | 7 | CLI, slash commands, environment variables, tools, glossary, what's new, troubleshooting |
| **SDK & API** | 7 | Agent SDK, Managed Agents, Claude models, advanced tool use, context editing and memory tool |
| **Research** | 14 | Agentic patterns, tool design, context engineering, long-running agents, evals, multi-agent systems, trustworthy agents, self-improvement, skill evolution, agent memory |
| **Ecosystem** | 8 | OpenAI Codex, OpenCode, Hermes Agent, open models (OpenRouter, NVIDIA NIM), Camoufox, mem0, context-compression tools, computer-use-linux |
| **Project** | 2 | How the harness works, and how it runs from four agents |

## Project structure

```
agent-wiki-kit/
├── CLAUDE.md                    # the schema: page format, rules, workflows (AGENTS.md is a symlink to it)
├── wiki/                        # the pages, plus index.md, hot.md (session cache) and log.md (append-only)
├── raw/                         # primary sources: fetched locally, never committed
│   └── docs/                    # official/ (197 code.claude.com pages), changelog, vendor docs
├── sources/                     # manifest.tsv and identifiers.txt: what raw/ contains, without its text
├── scripts/                     # setup.sh, doctor.sh, wiki-lint.sh, sources.py, freshness.py, evals,
│   ├── mem0/                    #   the local semantic index and the scratch-memory MCP server
│   ├── camoufox/                #   the browser fetcher and its MCP server
│   ├── hooks/                   #   the rule scripts every agent calls
│   └── agents/                  #   adapters and the config generator for Codex, OpenCode and Hermes
├── .claude/                     # skills, agents and hooks: the source of truth
├── .agents/ .codex/ .opencode/  # symlinks and generated files for the other agents
├── evals/  tests/               # retrieval and answer evals, unit tests
└── .github/workflows/           # CI: tests, lint, identifier check, and a guard against committed sources
```

## Keeping it healthy

```bash
./scripts/doctor.sh              # everything at a glance; --fix repairs what it can
./scripts/wiki-lint.sh           # 14 structural checks, scored out of 100
./.venv/bin/python -m pytest -q tests
./.venv/bin/python scripts/wiki-eval.py
./scripts/install-maintenance-cron.sh    # optional: weekly source refresh on a local branch
```

## Skills and agents

| Skill | Use it when |
|---|---|
| `new-wiki` | You want your own wiki on another subject |
| `wiki-query` | You have a question the wiki should answer |
| `ingest` | You have a new source to add |
| `wiki-lint` | You want a health score before committing |
| `freshness-check` | You want to know which pages are behind their sources |
| `autoresearch` | You want the wiki improved against a rubric, unattended |
| `handoff` | You are ending a long session and want the next one oriented |
| `write-a-skill` | You are adding a skill of your own |

Four subagents do the heavy lifting: `wiki-researcher` (read-only, with web access), `wiki-writer` (no web access), `wiki-auditor` (read-only, one quality lens at a time) and `memory-keeper` (the session cache).

## Stats

| Metric | Value |
|---|---|
| Wiki pages | 75 |
| Words | 121,000+ |
| Wikilinks | 1,200 (71 unique) |
| Raw sources | 403 files |
| Official doc pages snapshotted | 197 |
| Skills | 8 |
| Agents | 4 |
| Health score | 100/100 |

## License

MIT, for this project's own code and wiki text. See `LICENSE`. The documents that `./scripts/sources.py fetch` downloads belong to their publishers and carry their own terms.
