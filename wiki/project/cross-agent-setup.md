---
title: Using This Repo from Codex, OpenCode and Hermes
type: how-to
tldr: "One harness, four agents: what is shared and how"
sources:
  - raw/docs/openai-codex/hooks.md
  - raw/docs/openai-codex/skills.md
  - raw/docs/openai-codex/agents-md.md
  - raw/docs/openai-codex/subagents.md
  - raw/docs/openai-codex/source-skill-frontmatter-parser.md
  - raw/docs/openai-codex/source-skill-discovery-symlinks.md
  - raw/docs/openai-codex/source-mcp-stdio-cwd.md
  - raw/docs/openai-codex/source-hook-payloads-apply-patch.md
  - raw/docs/openai-codex/source-agents-md-symlinks-and-web-search-tool.md
  - raw/docs/opencode/docs-rules.md
  - raw/docs/opencode/docs-skills.md
  - raw/docs/opencode/docs-mcp-servers.md
  - raw/docs/opencode/docs-plugins.md
  - raw/docs/opencode/docs-permissions.md
  - raw/docs/opencode/docs-agents.md
  - raw/docs/opencode/src-plugin-hooks-index-ts.md
  - raw/docs/hermes-agent/docs-context-files.md
  - raw/docs/hermes-agent/docs-skills-system.md
  - raw/docs/hermes-agent/docs-event-hooks.md
  - raw/docs/hermes-agent/docs-plugins.md
  - raw/docs/hermes-agent/docs-mcp-config-reference.md
  - raw/docs/hermes-agent/docs-subagent-delegation.md
  - raw/docs/hermes-agent/docs-security.md
  - scripts/agents/sync.py
  - scripts/agents/shared.py
  - scripts/agents/adapter.py
  - scripts/agents/hermes/setup.sh
  - scripts/mem0/config.py
  - raw/docs/official/memory.md
related: ["[[harness]]", "[[openai-codex]]", "[[opencode]]", "[[hermes-agent]]", "[[agent-standards]]", "[[camoufox]]"]
created: 2026-09-17
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [use-this-repo-from-codex, opencode-and-hermes-setup, agents-md-symlink, cross-agent-compatibility, share-skills-between-coding-agents]
---

# Using This Repo from Codex, OpenCode and Hermes

This repository was built for Claude Code, and it works the same way from [[openai-codex]], [[opencode]] and [[hermes-agent]]. The wiki, the raw sources and every script are plain files and shell, so they were always portable. What needed work was the integration layer: instructions, skills, MCP servers, subagents, and above all the hooks that enforce this repo's rules. How the harness itself works is on [[harness]].

**Claude Code's files are the source of truth.** The other agents read symlinks where a symlink is enough, and generated files where their format differs. Nothing is maintained by hand twice.

## What each agent reads

| Layer | Claude Code | Codex | OpenCode | Hermes |
|---|---|---|---|---|
| Instructions | `CLAUDE.md` | `AGENTS.md` (symlink) | `AGENTS.md` (symlink) | `AGENTS.md` (symlink) |
| Skills | `.claude/skills/` | `.agents/skills` (symlink) | `.claude/skills/` and `.agents/skills` | `.agents/skills`, once the repo is trusted |
| MCP servers | `.mcp.json` | `.codex/config.toml` (generated) | `opencode.json` (generated) | `~/.hermes/config.yaml`, per user |
| Rules as hooks | `.claude/settings.json` | `.codex/hooks.json` (generated) | `.opencode/plugins/agent-wiki-kit.js` | user-level plugin, linked by the setup script |
| Subagents | `.claude/agents/*.md` | `.codex/agents/*.toml` (generated) | `.opencode/agents/*.md` (generated) | none: Hermes has no definition format |

Two facts make the symlinks necessary rather than optional. Codex reads only `AGENTS.md` and scans only `.agents/skills`. OpenCode and Hermes load the **first** instruction file they find, so a separate `AGENTS.md` would shadow `CLAUDE.md` and then drift from it. Codex follows a symlinked skills folder but skips a symlinked `SKILL.md` file, so link the folder, never the files. Claude Code can read `AGENTS.md` too, but only when no `CLAUDE.md` sits at or above the working directory; with both present it reads `CLAUDE.md` alone, so the symlink does not load these instructions twice.

All four agents ignore SKILL.md frontmatter fields they do not know, so Claude-only fields such as `user-invocable` and `argument-hint` are harmless. The frontmatter must still be **strict YAML**: Claude Code tolerates an unquoted value containing `: ` and Codex repairs it, but OpenCode silently drops the whole skill. A test now parses every skill strictly.

## Setup

- **Claude Code:** nothing. Hooks and MCP servers load from the project.
- **Codex:** trust the project, then open `/hooks` once and approve the four hooks. Codex records trust against each hook's exact definition, so any change to `.codex/hooks.json` re-arms that review. The MCP servers in `.codex/config.toml` load once the project is trusted.
- **OpenCode:** nothing. `opencode.json`, the plugin, the agents and the skills are all discovered from the project.
- **Hermes:** run `./scripts/agents/hermes/setup.sh` once per machine. Hermes keeps MCP servers, plugins and project trust in the user's home, and has no project-level config file, so a clone cannot carry them. The script trusts the repo so its skills load, links and enables the plugin, and registers both MCP servers by absolute path. It is idempotent, and `--remove` undoes all of it.

After changing a Claude Code agent, the MCP servers or a skill's `disable-model-invocation`, run `./scripts/agents/sync.py` and commit the result. `./scripts/doctor.sh` warns when the generated files are stale, `--fix` regenerates them, and a test fails in CI.

## One rule, four adapters

Each agent's hook system has its own payload, so each adapter translates its payload and then calls the **same** rule script Claude Code uses. The rule and its message exist once.

| Rule | Shared script | Claude Code | Codex | OpenCode | Hermes |
|---|---|---|---|---|---|
| An existing `raw/` file is never edited | `scripts/hooks/guard-raw.sh --path` | `PreToolUse` | `PreToolUse` on `apply_patch` | `tool.execute.before`, which throws | `pre_tool_call`, which returns a block |
| Unreadable pages are re-rendered in Camoufox | `webfetch_camoufox_fallback.py --url` | `PostToolUse` on WebFetch | not possible | `tool.execute.after` on `webfetch` | `transform_tool_result` on `web_extract` |
| Wiki edits need a `wiki/log.md` entry | `stop-anti-evaporation.sh` | `Stop` | `Stop` | appended once to an edit's result | `pre_llm_call` context |
| Harness health at session start | `session-start.sh` | `SessionStart` | `SessionStart` | first system prompt | first-turn `pre_llm_call` context |

`scripts/agents/shared.py` holds the translation: it finds every file a write would touch, whatever the agent calls the argument, and reads the file names out of a patch body. That matters because Codex reports an edit only as patch text in `tool_input.command`, with no file path field, and OpenCode's `apply_patch` does the same in `patchText`. Creating a new raw file is always allowed, which is why OpenCode uses a plugin rather than a declarative `permission.edit` rule: a deny on `raw/*` would also stop ingest from adding sources.

Codex hooks run from wherever Codex was started, and a relative MCP command resolves against that directory, not the project root. Every generated command therefore locates the repository itself with `git rev-parse --show-toplevel`, so the setup works from any subdirectory and no committed file carries an absolute path.

## What each agent cannot do

- **Codex has no automatic Camoufox fallback.** It has no page-fetch tool, and its hosted web search does not pass through hooks. Use the `camoufox` MCP tool `fetch_page`, or `scripts/camoufox/fetch.py`. See [[camoufox]].
- **Only Claude Code honors `disable-model-invocation`.** OpenCode gets the same effect from a generated `permission.skill` rule that asks before loading those skills. Codex and Hermes have no equivalent here, so they may load them unprompted.
- **Hermes has no subagent definitions.** Its `delegate_task` tool takes a goal and context inline. Child agents still inherit these instructions.
- **No agent guards shell writes.** A `sed -i` on a raw file through the shell tool bypasses the guard everywhere, Claude Code included. Hermes's documentation makes the same point about its own path protections.
- **OpenCode's session banner uses an experimental hook,** so it may change. The raw guard and the fallback use stable hooks.

## Sharing the memory layer

Embedded Qdrant takes an exclusive lock on its store and fails at once if another process holds it, so two agents running the mem0 server used to crash the second one. Every caller now takes a blocking cross-process lock, opens the store, does one operation and closes it again. A second agent waits a moment instead of failing, and the long-lived MCP server keeps its embedding model loaded while reopening only the client. Set `WIKI_MEM0_LOCK_WAIT` to change how long a caller waits; an index rebuild holds the lock for its whole run. See [[mem0]].

## How this was verified

| Agent | Evidence |
|---|---|
| Codex | Its model-visible prompt contained the instructions and all seven skills; both MCP servers listed from a subdirectory; a real model's edit to a raw file was rejected with this repo's message and the file's hash was unchanged |
| OpenCode | Resolved config showed both MCP servers, the plugin, four agents with their deny rules and the skill rule; both servers connected; the plugin's hooks were fired under Node with OpenCode-shaped input |
| Hermes | Its plugin validator passed with three hooks; its own dispatcher blocked writes and patches to raw files and injected the health line; both MCP servers passed its connection test; all seven project skills listed as enabled |

Running the Codex hook from inside `wiki/` exposed a bug that affected Claude Code too: a path such as `../raw/x.md` slipped past the guard, because the path was compared before being normalised. The guard now resolves the path first, and tests cover `..` routes and symlinks into `raw/`.
