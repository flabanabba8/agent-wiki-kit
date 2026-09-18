---
title: Hermes Agent
type: entity
tldr: "Nous Research's agent vs Claude Code"
sources:
  - raw/docs/hermes-agent/docs-context-files.md
  - raw/docs/hermes-agent/docs-configuration.md
  - raw/docs/hermes-agent/docs-skills-system.md
  - raw/docs/hermes-agent/docs-creating-skills.md
  - raw/docs/hermes-agent/docs-mcp-feature.md
  - raw/docs/hermes-agent/docs-mcp-config-reference.md
  - raw/docs/hermes-agent/docs-use-mcp-with-hermes.md
  - raw/docs/hermes-agent/docs-event-hooks.md
  - raw/docs/hermes-agent/docs-plugins.md
  - raw/docs/hermes-agent/docs-build-a-plugin.md
  - raw/docs/hermes-agent/docs-security.md
  - raw/docs/hermes-agent/docs-import-from-other-agents.md
  - raw/docs/hermes-agent/docs-subagent-delegation.md
  - raw/docs/hermes-agent/docs-cli-commands.md
  - raw/docs/hermes-agent/docs-profile-commands.md
  - raw/docs/hermes-agent/source-agent-skill-utils.md
  - raw/docs/hermes-agent/source-tools-skill-linter.md
  - raw/docs/hermes-agent/source-tools-skill-manager-tool.md
  - raw/docs/hermes-agent/source-hermes-cli-subcommands-mcp.md
  - raw/docs/hermes-agent/source-tools-mcp-tool-config.md
  - raw/docs/hermes-agent/source-tools-mcp-tool-transport.md
  - raw/docs/official/memory.md
  - raw/docs/official/settings.md
  - raw/docs/official/permissions.md
  - raw/docs/official/skills.md
  - raw/docs/official/mcp.md
  - raw/docs/official/hooks.md
  - raw/docs/official/sub-agents.md
  - raw/docs/official/plugins.md
related: ["[[openai-codex]]", "[[skills]]", "[[hooks]]", "[[mcp]]", "[[subagents]]", "[[agent-standards]]"]
created: 2026-09-17
updated: 2026-09-17
last_verified: 2026-09-17
confidence: high
aliases: [hermes-agent, nous-research-hermes, hermes-vs-claude-code, hermes-config-yaml, moving-a-claude-code-setup-to-hermes]
valid_until: 2027-03-15
---

# Hermes Agent

Hermes Agent is Nous Research's agent harness. The same agent runs as a terminal REPL (`hermes chat`), a TUI, a desktop app, a web dashboard, cron jobs, and a messaging gateway (Telegram, Discord, Slack, Teams). All state lives in a per-user profile home — `~/.hermes` by default, `HERMES_HOME` elsewhere, picked with `hermes -p <name>`. Read this page if you work with both: every familiar piece is here, but configuration is per user rather than per repo, and a repo must be trusted before it contributes anything.

## Context files

| File | Where Hermes looks |
|---|---|
| `.hermes.md` / `HERMES.md` | Project instructions; walks to the git root |
| `AGENTS.override.md` | Personal per-directory override, usually gitignored |
| `AGENTS.md` | Working directory at startup, plus subdirectories progressively |
| `CLAUDE.md` | Same discovery as `AGENTS.md` |
| `.cursorrules`, `.cursor/rules/*.mdc` | Working directory only |
| `SOUL.md` | `HERMES_HOME/SOUL.md` only |

Only **one** project context type loads per session, first match wins: `.hermes.md` → `AGENTS.override.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`; an `AGENTS.override.md` beside a committed `AGENTS.md` replaces it. `SOUL.md`, the identity and tone file, loads separately and only from the Hermes home — Hermes seeds a default one and never probes the working directory for it.

Discovery scope differs by file type. Inside a git repository the `AGENTS.md` chain from the git root down to the working directory is merged root-first, duplicates dropped, so the deepest file wins; outside one only the working directory is read, so an `AGENTS.md` planted in `/tmp` or `$HOME` cannot leak into unrelated sessions. Mid-session, file paths in tool arguments trigger progressive discovery: the directory and up to five parents are checked once each, and the first `AGENTS.md`, `CLAUDE.md` or `.cursorrules` found is appended to that tool result rather than the system prompt, keeping the cached prompt stable. Claude Code merges its memory files up the tree instead ([[claude-md-and-memory]]).

Startup files are capped at `context_file_max_chars` when set, otherwise a cap scaling with the model's context window (floor 20,000 chars, ceiling 500,000); an oversized file keeps 70% head plus 20% tail with a marker between. Progressive hints use a fixed 32,000-char preview cap. A file slower than `context_file_read_timeout` (default 5 seconds) is skipped.

Every project context file, startup or progressive, is scanned for prompt injection (instruction overrides, hidden HTML, credential exfiltration, invisible characters), and a hit **blocks the file** — nothing loads and the prompt says so. Your own `SOUL.md` is exempt, warning instead and flagged in `/context`, unless a profile distribution owns it.

## Configuration

Configuration is per user, and there is no project-level config file: `~/.hermes/config.yaml` holds settings, `~/.hermes/.env` holds secrets, one pair per profile. Precedence, highest first: CLI arguments, `config.yaml`, `.env`, built-in defaults, with an admin able to pin values via a managed directory. `hermes config set` routes `UPPER_SNAKE` names to `.env` and dotted keys to `config.yaml`. A repo contributes skills and plugins, never settings — the contrast with Claude Code's layered `settings.json` files ([[settings]]).

## Skills

Skills follow the open Agent Skills standard ([[agent-standards]], [[skills]]); each is also a `/<name>` slash command. `~/.hermes/skills/` is the source of truth, and `skills.external_dirs` adds more roots — a shared `~/.agents/skills`, say, with `~` and `${VAR}` expanded and missing directories skipped silently.

A repo can vendor skills in `<root>/.hermes/skills/` or `<root>/.agents/skills/`, the root being the nearest ancestor holding `.git`. They stay dormant until you trust the repo once with `hermes skills trust` (`untrust` revokes; trusted roots live in `skills.trusted_project_dirs`, and `skills.project_discovery: false` disables the scan). Because a `git pull` can outrun that one-time decision, every project skill is re-scanned as its content changes and a `dangerous` verdict quarantines it. Precedence is project → profile-local → external dirs, first name wins.

Only `name` and `description` are required and validated, and a new skill's description must fit the 60-character system-prompt budget. Also recognized: `version`, `author`, `license`, `platforms`, `environments`, `required_environment_variables`, `required_credential_files`, and a `metadata.hermes` block (`tags`, `related_skills`, `category`, `requires_tools`/`requires_toolsets`, `fallback_for_tools`/`fallback_for_toolsets`, `session_platforms`, `config`, `blueprint`). Unknown fields are ignored, so a SKILL.md written for another harness loads unchanged. An advisory linter runs on `skill_manage` creates and `references/` writes. It warns — never blocks — about description length and marketing adjectives, a `name` that does not match its directory, missing `version`/`author`/`license`/`metadata.hermes.tags`, a missing "When to Use" section, shell-utility names in prose instead of native tools, dangling `references/` links, ungated POSIX-only scripts and reference sprawl.

## MCP servers

Servers are declared under `mcp_servers` in `config.yaml` ([[mcp]] covers Claude Code's `.mcp.json`). A stdio entry takes `command`, `args`, `env` and an optional `cwd`; an HTTP server takes `url` and `headers`. Both accept `enabled`, `timeout`, `connect_timeout`, `lazy`, `supports_parallel_tool_calls`, `trust: untrusted` (approve every write-capable call), `auth: oauth`, TLS settings, `sampling`, `elicitation`, and a `tools` block whose `include`/`exclude` lists accept exact names or fnmatch globs (`include` wins over `exclude`) while `resources` and `prompts` toggle the utility wrappers. `hermes mcp add <name> --command <cmd> --args …` (or `--url <url>`) writes an entry, with `--env KEY=VALUE`, `--auth oauth|header` and `--preset`; `/reload-mcp` applies edits mid-session.

Any string in an entry interpolates `${VAR}` or Cursor's `${env:VAR}` from the profile's secret scope, plus `${userHome}`, `${workspaceFolder}`, `${workspaceFolderBasename}` and `${pathSeparator}`; an unset variable keeps its literal placeholder. A bare `command` is resolved on the subprocess `PATH`, but one containing a path separator is passed through untouched, so a relative command resolves against the subprocess working directory — the entry's `cwd` when set, otherwise the directory Hermes itself runs in.

> [!contradiction] Two official pages disagree on the registered tool-name prefix: the MCP config reference documents `mcp__<server>__<tool>` (double underscores, "matches the convention used by Claude Code, Codex, and OpenCode"), the MCP feature page `mcp_<server>_<tool>` (`mcp_filesystem_read_file`). Both agree non-alphanumeric characters become underscores and filters use the original names.

## Hooks

Hermes has four hook systems where Claude Code has one ([[hooks]]):

| System | Declared in | Notes |
|---|---|---|
| Gateway hooks | `HOOK.yaml` + `handler.py` in `~/.hermes/hooks/<name>/` | Gateway only; observes `session:*`, `agent:*`, `command:*` |
| Plugin hooks | `ctx.register_hook(event, cb)` in a plugin | In-process, CLI and gateway; transforms live here |
| Shell hooks | `hooks:` in the profile `config.yaml` | Subprocesses, every surface; can block |
| Outbound webhooks | `hooks.outbound:` in `config.yaml` | Signed POSTs of lifecycle events to HTTP endpoints |

A shell hook entry takes `matcher` (a regex, honored on tool-scoped events only), `command` (shlex-split, `shell=False`), `timeout` (default 60 seconds, clamped at 300) and `fail_closed`. Each firing pipes JSON to stdin — `hook_event_name`, `tool_name`, `tool_input`, `session_id`, `cwd`, `profile`, and an `extra` dict of event-specific fields (the tool fields are null on non-tool events) — and parses stdout as JSON. A `pre_tool_call` hook blocks with either accepted shape, `{"decision": "block", "reason": …}` (the Claude Code spelling) or `{"action": "block", "message": …}`, or by exiting with code **2** and writing the reason to stderr; `{"action": "modify", "args": {…}}` rewrites the arguments instead. Hooks fail open by default — a spawn error, timeout or unparseable stdout warns and the action proceeds — while `fail_closed: true` (also spelled `failClosed`) turns each into a block, on `pre_tool_call` only.

Each `(event, command)` pair is approved once, recorded in `~/.hermes/shell-hooks-allowlist.json`. Three bypasses skip the prompt, any one sufficient: `--accept-hooks`, `HERMES_ACCEPT_HOOKS=1`, `hooks_auto_accept: true`; non-TTY surfaces need one or new hooks silently stay unregistered. The allowlist keys on the command string, not a hash, so editing the script keeps its consent — `hermes hooks doctor` flags mtime drift.

`post_tool_call` output is ignored: you cannot fix up a result there. Rewriting one needs the plugin hook `transform_tool_result`, whose first string return replaces the result before the model sees it. Context injection goes through `pre_llm_call`, once per turn: a `{"context": …}` return, or a plain string, is appended to that turn's user message and never to the system prompt, so the prompt cache survives.

## Plugins

A plugin is a directory with a `plugin.yaml` manifest and a `register(ctx)` entry point adding tools, hooks, slash commands, CLI subcommands, bundled skills or whole backends. User plugins live in `~/.hermes/plugins/`; project plugins in `./.hermes/plugins/` are off unless Hermes starts with `HERMES_ENABLE_PROJECT_PLUGINS=true`. General plugins are discovered but load nothing until their name is in `plugins.enabled` (`plugins.disabled` wins); bundled platforms, backends, memory and context engines are exceptions, activated by their own config keys. Unknown `plugin.yaml` fields are ignored by design, and `hermes plugins doctor [path] [--ci]` replays discovery, manifest parsing and `register(ctx)` to report invalid hook names, callbacks without `**kwargs`, and declared-versus-registered drift. Compare [[plugins]].

## Path protection

`write_file` and `patch` refuse a fixed, code-shipped set of protected paths — credential stores such as `~/.ssh` and `~/.aws`, `.env`-style files, Hermes secret stores, Windows device-namespace paths — with no approval prompt and no chat override. The only configurable control is `HERMES_WRITE_SAFE_ROOT`, an **allowlist**: set it (roots separated by `:` on Unix) and every write outside those prefixes is hard-blocked, Hermes's own state included. There is no configurable write-deny list, so you cannot fence off one directory the way a Claude Code `Edit(...)` deny rule does ([[permissions-and-modes]]). Protected paths stay blocked inside the safe root, and `terminal` can still overwrite them as the same OS user.

## Importing a Claude Code setup

`hermes import-agent claude-code` reads the user-level `~/.claude` directory (`--source` points elsewhere) and prints a per-item plan first: `--dry-run` never writes, `--yes` applies non-interactively, `--overwrite` replaces conflicts, `--sync` re-imports later changes.

| Claude Code | Hermes |
|---|---|
| Global `CLAUDE.md` | Memory entries in `~/.hermes/memories/MEMORY.md` |
| `permissions.allow` `Bash(...)` rules | `command_allowlist` (`Bash(npm run test:*)` becomes `npm run test*`) |
| `permissions.deny` `Bash(...)` rules | `approvals.deny` |
| `mcpServers` from `~/.claude.json` and `settings.json` | `mcp_servers` |
| `skills/<name>/` dirs holding a `SKILL.md` | Copied to `~/.hermes/skills/claude-code-imports/<name>/` |
| `commands/*.md` slash commands | Skipped, with a note to convert them into skills |

Non-`Bash` permission rules are reported as unmapped, and hooks and agents are not imported at all. Credential files are never read; MCP environment variables and headers with secret-looking names are stripped and listed so you re-add them deliberately. Memories and patterns merge rather than replace. `hermes import-agent codex` does the same for `~/.codex` ([[openai-codex]]).

## Delegation

`delegate_task` spawns child agents with a fresh conversation and their own terminal sessions; the parent passes `goal` and `context` (plus optional `images` and an `output_schema`), and only the child's final summary re-enters the parent's context. A `tasks` batch runs in parallel; top-level calls run in the background. Children inherit the parent's toolsets and cannot be granted more; `clarify`, `memory`, `send_message` and `cronjob` are blocked for them, and `delegate_task` itself survives only for `role="orchestrator"` children. Each child's system prompt embeds the workspace's project context files (`SOUL.md` excluded).

There is no custom subagent definition format — no per-agent Markdown or TOML file, no per-call model or toolset parameter — so children are configured globally under `delegation:`: `model`, `provider`, `base_url`, `max_iterations` (default 250), `max_concurrent_children`, `max_spawn_depth` (default 1, flat; up to 3 for orchestrator trees), `orchestrator_enabled`, `child_timeout_seconds` (default 0, no wall-clock cap; a stall monitor still fires) and `worktree_isolation`. Claude Code's per-agent definition files are the main structural difference ([[subagents]]).

## Hermes Agent compared with Claude Code

| Area | Hermes Agent | Claude Code |
|---|---|---|
| Instruction files | First match of `.hermes.md`, `AGENTS.override.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, plus global `SOUL.md`; injection-scanned | `CLAUDE.md`, `CLAUDE.local.md`, `~/.claude/CLAUDE.md`, merged ([[claude-md-and-memory]]) |
| Config | Per profile: `config.yaml` + `.env`; no project file | User, project, local and managed `settings.json` ([[settings]]) |
| Skills | `~/.hermes/skills/`, `skills.external_dirs`, project dirs after `hermes skills trust` | `.claude/skills/`, `~/.claude/skills/`, plugin skills ([[skills]]) |
| MCP | `mcp_servers` in `config.yaml`; `hermes mcp add` | `.mcp.json`, `~/.claude.json`; `claude mcp add` ([[mcp]]) |
| Hooks | Four systems; shell hooks consented per `(event, command)` | One: `hooks` in settings files and plugins ([[hooks]]) |
| Plugins | `~/.hermes/plugins/`, `plugin.yaml` + `register(ctx)`, opt-in | Marketplace plugins bundling commands, agents, skills, hooks ([[plugins]]) |
| Subagents | `delegate_task` only; global `delegation:` settings | Markdown agents in `.claude/agents/`, own model and tools ([[subagents]]) |
| Write protection | Fixed protected paths plus a `HERMES_WRITE_SAFE_ROOT` allowlist | allow/ask/deny rules including `Edit(...)` paths ([[permissions-and-modes]]) |
