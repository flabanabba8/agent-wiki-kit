# agent-wiki-kit

A knowledge wiki that maintains itself, plus the harness that keeps it honest. It ships as a working example, a source-backed wiki about Claude Code and agentic systems, and it is built to be pointed at your own subject.

It currently holds **78 wiki pages** in 11 topic folders, cross-linked with **1,200+ wikilinks** and verified against **442 raw source files**. Every claim traces to a primary source, every identifier is checked against those sources, and the same rules are enforced whether you work in Claude Code, OpenAI Codex, OpenCode or Hermes Agent.

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

## Disposable image workers

Routine image inspection sends stateless requests to a vision server you already run on loopback; image generation, and inspection when you pass `--backend codex`, use fresh Codex sessions, even when Claude Code or Hermes coordinates the job. Only text findings, verdicts, and file paths return to the main conversation. The shared project instructions select this workflow automatically for image work.

This optional capability requires Python **3.11+**, Pillow, and an authenticated **Codex CLI** on PATH for generation and Codex review; local inspection also needs a loopback vision server (`VISION_LOCAL_URL`, default `http://127.0.0.1:8081`). The kit does not include a model service, and nothing falls back to another provider automatically. The rest of the wiki still supports Python 3.10.

```bash
./scripts/setup.sh --with-vision
./.venv/bin/python .claude/skills/disposable-vision/scripts/check_environment.py
./.venv/bin/python .claude/skills/disposable-vision/scripts/vision_inspect.py \
  --backend codex --question "What visual defects are present?" --criteria "No clipped edges" screenshot.png
./.venv/bin/python .claude/skills/disposable-vision/scripts/image_reference_generate.py new-art.png \
  --prompt "Create a centered blue potion icon" --criteria "One bottle, no lettering" \
  --reference style.png
```

Inspection caches results by image content, task, criteria and model. Generation runs a separate visual review and returns PASS, FAIL or UNCERTAIN; failed or uncertain outputs remain unaccepted drafts. Generated assets are never installed or published automatically. Image batches and temporary files are bounded; ephemeral sessions do not imply zero server retention.

The skill is already available inside this clone through the existing shared skill directories. For use in other projects, install it into selected user skill directories:

```bash
python3 scripts/agents/install-vision-skill.py --agent all --dry-run
python3 scripts/agents/install-vision-skill.py --agent all
```

The installer supports `claude`, `codex`, `hermes`, or `all`, skips identical copies, and refuses to overwrite differing skills. It does not edit global instructions or credentials. To make it the default outside this clone, add an explicit preference to your agent's global instructions to route image work through `disposable-vision`.

See [.claude/skills/disposable-vision/SKILL.md](.claude/skills/disposable-vision/SKILL.md) for limits, cache controls, review criteria and metrics. Traffic counters include other applications and do not prove exact request sizes. Offline worker and installer tests run in CI without account access. Local live smoke tests exercised inspection, cache reuse, and two-reference native image generation with a separate review on Codex 0.162.0; this is not a broad model-quality benchmark. OpenCode can discover the shared skill, but its execution path has not been live-tested.

### Disposable analysis workers (opt-in)

`.claude/skills/disposable-tasks` runs bounded, read-only Codex workers over logs, code, diffs, documents, datasets, saved browser/game traces and web questions, and returns text findings only. It is off by default: the project instructions tell agents to use local commands for non-image work, and the skill runs only when you ask for it. It needs Python 3.11+ and an authenticated Codex CLI. See [.claude/skills/disposable-tasks/SKILL.md](.claude/skills/disposable-tasks/SKILL.md) for modes, limits and caching.

The task-brief and evidence-reporting conventions draw on [Agent Personas](https://github.com/Sahil-SS9/agent-personas/tree/068a9894bb87291aab5d369404dd27047906b5e9): explicit scope and completion criteria, and separate claims for packaging, native discovery, and observed task behavior. The kit retains its existing native agent formats and imports no upstream runtime or persona catalogue.

## Wiki map

| Folder | Pages | Covers |
|---|---|---|
| **Start** | 3 | What Claude Code is, installation, how the agentic loop works |
| **Using** | 9 | Prompting and workflows, CLAUDE.md and memory, context, permissions, sandboxing, sessions, models, interface, costs |
| **Extending** | 7 | Skills, subagents, agent teams, hooks, MCP, plugins |
| **Automation** | 7 | Worktrees and background work, workflows, routines and scheduling, channels, artifacts, headless mode |
| **Surfaces** | 7 | IDEs, desktop app, web and Remote Control, Chrome and computer use, Slack, CI/CD and code review |
| **Deployment** | 6 | Cloud providers, LLM gateways, settings, enterprise admin, data and privacy, network configuration |
| **Reference** | 7 | CLI, slash commands, environment variables, tools, glossary, what's new, troubleshooting |
| **SDK & API** | 8 | Agent SDK, Managed Agents, Claude models, advanced tool use, context editing and memory tool |
| **Research** | 14 | Agentic patterns, tool design, context engineering, long-running agents, evals, multi-agent systems, trustworthy agents, self-improvement, skill evolution, agent memory |
| **Ecosystem** | 8 | OpenAI Codex, OpenCode, Hermes Agent, open models (OpenRouter, NVIDIA NIM), Camoufox, mem0, context-compression tools, computer-use-linux |
| **Project** | 2 | How the harness works, and how it runs from four agents |

## Project structure

```
agent-wiki-kit/
├── CLAUDE.md                    # the schema: page format, rules, workflows (AGENTS.md is a symlink to it)
├── wiki/                        # the pages, plus index.md, hot.md (session cache) and log.md (append-only)
├── raw/                         # primary sources: fetched locally, never committed
│   └── docs/                    # official/ (217 code.claude.com pages), changelog, vendor docs
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
| `audit-scheduled-jobs` | You want to know if the weekly maintenance cron actually delivered anything |
| `autoresearch` | You want the wiki improved against a rubric, unattended |
| `handoff` | You are ending a long session and want the next one oriented |
| `write-a-skill` | You are adding a skill of your own |

Four subagents do the heavy lifting: `wiki-researcher` (read-only, with web access), `wiki-writer` (no web access), `wiki-auditor` (read-only, one quality lens at a time) and `memory-keeper` (the session cache).

## Stats

| Metric | Value |
|---|---|
| Wiki pages | 78 |
| Words | 129,000+ |
| Wikilinks | 1,269 (75 unique) |
| Raw sources | 442 files |
| Official doc pages snapshotted | 217 |
| Skills | 11 |
| Agents | 4 |
| Health score | 100/100 |

## License

MIT, for this project's own code and wiki text. See `LICENSE`. The documents that `./scripts/sources.py fetch` downloads belong to their publishers and carry their own terms.
