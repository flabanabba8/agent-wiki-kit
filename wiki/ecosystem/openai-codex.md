---
title: OpenAI Codex CLI
type: entity
tldr: "Codex CLI compared with Claude Code"
sources:
  - raw/docs/changelog-2.1.275-to-2.1.282.md
  - raw/docs/openai-codex/readme.md
  - raw/docs/openai-codex/install.md
  - raw/docs/openai-codex/cli-features.md
  - raw/docs/openai-codex/auth.md
  - raw/docs/openai-codex/agent-approvals-security.md
  - raw/docs/openai-codex/config-basic.md
  - raw/docs/openai-codex/config-advanced.md
  - raw/docs/openai-codex/agents-md.md
  - raw/docs/openai-codex/mcp.md
  - raw/docs/openai-codex/skills.md
  - raw/docs/openai-codex/subagents.md
  - raw/docs/openai-codex/customization.md
  - raw/docs/openai-codex/models.md
  - raw/docs/openai-codex/hooks.md
  - raw/docs/openai-codex/source-hook-payloads-apply-patch.md
  - raw/docs/openai-codex/source-skill-frontmatter-parser.md
  - raw/docs/openai-codex/source-skill-discovery-symlinks.md
  - raw/docs/openai-codex/source-mcp-stdio-cwd.md
  - raw/docs/openai-codex/source-agents-md-symlinks-and-web-search-tool.md
  - raw/docs/official/setup.md
  - raw/docs/official/permission-modes.md
  - raw/docs/official/sandboxing.md
  - raw/docs/official/settings.md
  - raw/docs/official/memory.md
  - raw/docs/official/mcp.md
  - raw/docs/official/skills.md
  - raw/docs/official/sub-agents.md
  - raw/docs/official/headless.md
  - raw/docs/official/cli-reference.md
  - raw/articles/openai-gpt-6-sol-and-luna.md
  - raw/articles/openai-rethinking-skills-gpt-6-astra.md
  - raw/articles/openai-how-agents-are-transforming-work.md
related: ["[[open-models]]", "[[permissions-and-modes]]", "[[sandboxing-and-security]]", "[[agent-standards]]", "[[subagents]]", "[[skill-evolution]]", "[[long-running-agents]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [codex-cli, openai-codex, gpt-6-sol, gpt-6-luna, gpt-6-astra-prompting, codex-cli-vs-claude-code, codex-compared-with-claude-code, switching-from-codex-to-claude-code, agents-md]
valid_until: 2027-03-15
---

# OpenAI Codex CLI

Codex CLI is OpenAI's open-source (Apache-2.0) coding agent that runs locally in your terminal. The same agent ships as an IDE extension (VS Code, Cursor, Windsurf), inside the ChatGPT desktop app (`codex app`), and as the cloud agent Codex Web; CLI, extension and desktop app share one configuration. To run Codex on non-OpenAI models, see [[open-models]].

## Install and sign in

| Method | Install (rerun to update) |
|---|---|
| macOS/Linux | `curl -fsSL https://chatgpt.com/codex/install.sh \| sh` |
| Windows | `powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 \| iex"` |
| npm | `npm install -g @openai/codex` |
| Homebrew | `brew install --cask codex` (update: `brew upgrade --cask codex`) |

Requirements: macOS 12+, Ubuntu 20.04+/Debian 10+ or Windows 11; 4 GB RAM (8 GB recommended).

`codex login` signs in with ChatGPT and uses your Plus, Pro, Business, Edu or Enterprise plan. To bill an API key instead, use `printenv OPENAI_API_KEY | codex login --with-api-key`. Codex cloud requires the ChatGPT sign-in.

## Everyday commands

| Command | Purpose |
|---|---|
| `codex` | Interactive TUI in the current repo |
| `codex exec` | Non-interactive run for scripts and CI |
| `codex resume` | Reopen a saved chat |
| `codex --image`, `codex --search` | Attach an image; switch the run to live web search |
| `codex cloud` | Browse and submit Codex cloud tasks |
| `codex mcp add / list / login` | Manage MCP servers |
| `/permissions`, `/model`, `/status`, `/mcp`, `/agent` | TUI commands: approval mode, model and effort, workspace roots, MCP servers, subagent threads |
| `codex sandbox linux [COMMAND]` | Run a command under the Codex sandbox to test it (`macos` and `windows` variants exist too) |

## Sandbox and approvals

`sandbox_mode` sets what commands can technically do (`read-only`, `workspace-write`, `danger-full-access`); `approval_policy` sets when Codex stops to ask (`on-request`, `never`, or a `granular` table). By default the network is off and writes are limited to the workspace — the current directory plus temp dirs such as `/tmp` — and `.git`, `.agents` and `.codex` stay read-only.

| Intent | Flags |
|---|---|
| Auto (default in a version-controlled folder) | `--sandbox workspace-write --ask-for-approval on-request` |
| Read-only browsing | `--sandbox read-only --ask-for-approval on-request` |
| Read-only CI | `--sandbox read-only --ask-for-approval never` |
| Reviewer agent handles approvals | add `-c approvals_reviewer=auto_review` |
| No sandbox, no approvals | `--dangerously-bypass-approvals-and-sandbox` (alias `--yolo`) |

Enforcement: Seatbelt on macOS, `bwrap` plus `seccomp` on Linux, a native Windows sandbox. Enable network with `[sandbox_workspace_write] network_access = true`, and limit domains with `[features.network_proxy]`. `approval_policy = "untrusted"` is not a valid setting and can stop Codex from starting. For per-project command approval, use `[projects."/path"] trust_level = "untrusted"`.

GPT-6 Astra adds asynchronous safety monitoring that can pause a task. In Codex CLI, a paused task ends.

## config.toml

User config lives at `~/.codex/config.toml`; project overrides in `.codex/config.toml` load only in trusted projects. Precedence, highest first:

1. CLI flags and `-c`/`--config`
2. Project `.codex/config.toml`, where the file closest to the working directory wins
3. Profile file `~/.codex/<name>.config.toml`, selected with `--profile`
4. `~/.codex/config.toml`
5. Cloud-managed defaults
6. `/etc/codex/config.toml`
7. Built-in defaults

```toml
model = "gpt-5.6"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "cached"   # cached | indexed | live | disabled

[features]
multi_agent = true      # subagents (default true)
hooks = true            # hooks.json or inline [hooks] (default true)
```

Project config ignores keys that redirect credentials or providers (`openai_base_url`, `model_provider`, `notify`, `otel` and others); set those in the user file. `CODEX_HOME` moves the whole state directory, which defaults to `~/.codex`.

## AGENTS.md

Codex reads one global file from `~/.codex` (`AGENTS.override.md` beats `AGENTS.md`), then walks from the project root down to the working directory taking at most one file per directory: `AGENTS.override.md`, then `AGENTS.md`, then any names in `project_doc_fallback_filenames`. Files are concatenated root-first, so the file closest to your directory wins. Codex stops adding files once the total reaches `project_doc_max_bytes`, which defaults to 32 KiB. Discovery and reading both follow symlinks, so `AGENTS.md` may be a symlink to a file kept elsewhere.

## MCP, skills, subagents

- **MCP:** run `codex mcp add <name> -- <command>` for stdio servers or `codex mcp add <name> --url <url>` for streamable HTTP servers. Both write a `[mcp_servers.<name>]` table. Useful keys include `enabled_tools`, `disabled_tools`, `default_tools_approval_mode` (`auto`, `prompt`, `writes`, `approve`), `startup_timeout_sec` (default 10) and `tool_timeout_sec` (default 60). Codex always asks before tools annotated as destructive. A relative stdio `command` resolves against the session's working directory (or the entry's `cwd`), never the project root, so prefer an absolute path.
- **Skills:** these follow the open Agent Skills standard (see [[agent-standards]]): a `SKILL.md` file with `name` and `description`. Codex scans `.agents/skills` in each directory from the working directory up to the repo root, plus `$HOME/.agents/skills`, `/etc/codex/skills` and the bundled system skills. Invoke one with `$skill-name` or `/skills`. The parser reads only `name`, `description` and `metadata.short-description` and ignores other fields (an unquoted colon is repaired), so a SKILL.md written for another harness loads unchanged. Discovery follows symlinked skill *directories* under the user, repo and admin scopes but skips a symlinked `SKILL.md` *file*. The initial skill list may use at most 2% of the context window, or 8,000 characters when the window size is unknown. Create skills with `$skill-creator`, install them with `$skill-installer`.
- **Subagents:** Codex spawns subagents only when you ask or when AGENTS.md or a skill instructs it to. Built-in agents are `default`, `worker` and `explorer`. Custom agents are TOML files in `~/.codex/agents/` or `.codex/agents/`. Each needs `name`, `description` and `developer_instructions`, and can set `model`, `model_reasoning_effort`, `sandbox_mode` and `mcp_servers`. Global limits go under `[agents]`, for example `max_concurrent_threads_per_session`. Subagents inherit the parent's sandbox policy and any live `/permissions` overrides.

## Hooks

Hooks run scripts or MCP tools at lifecycle points. They are on by default (`[features] hooks = false` turns them off) and live in `hooks.json` or inline `[hooks]` tables in `config.toml`, at user (`~/.codex/`) and project (`<repo>/.codex/`) level; plugins bundle their own, and administrators can pin hooks in `requirements.toml`. Every matching hook from every layer runs, and project hooks load only in a trusted project.

A non-managed hook runs only after you trust that exact definition. Trust is recorded against its hash, so editing a hook skips it until you trust it again. `/hooks` lists sources, reviews changes, and trusts or disables hooks; `--dangerously-bypass-hook-trust` skips the check for one invocation. Managed hooks (system, MDM, cloud or `requirements.toml`) are trusted by policy.

Events: `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `Stop` and `Interrupt`. Handlers are `command` (`timeout` in seconds, default 600; `SessionEnd` and `Interrupt` default to 1 and cap at 3; optional `statusMessage`, `additionalContextLimit`, `commandWindows`, `async: true`) or `mcp_tool` (an already-connected `server` and `tool`, with `${field.nested}` argument templates); `prompt` and `agent` handlers are skipped. Commands run in the session `cwd`, so repo-local hooks should resolve paths from the git root.

A command hook receives JSON on stdin: `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`, plus `permission_mode` and `turn_id` on turn-scoped events and event fields such as `tool_name`, `tool_input`, `tool_response` and `prompt`. Model-visible output is capped around 2,500 tokens and spilled to a file beyond that.

A `matcher` is a regex (`"*"`, `""` or none matches all). It filters the tool name on tool events, `trigger` on compaction events, `source` on `SessionStart`, `reason` on `SessionEnd` and agent type on subagent events; `UserPromptSubmit`, `Stop` and `Interrupt` ignore it. `apply_patch` also matches `Edit` or `Write`, and `spawn_agent` also matches `Agent`.

`PreToolUse` blocks with `hookSpecificOutput.permissionDecision: "deny"` plus a reason, the older `{"decision": "block", "reason": …}`, or exit code 2; `"allow"` plus `updatedInput` rewrites the call. File edits arrive as `apply_patch` with the whole patch in `tool_input.command` and **no file-path field**, so path checks must parse the `*** Add File:` / `*** Update File:` / `*** Delete File:` lines.

`PostToolUse` can add context with `hookSpecificOutput.additionalContext`; its `decision: "block"` can't undo side effects but replaces the tool result with the hook's feedback. A `Stop` hook's `decision: "block"` makes Codex continue with the `reason` as a new prompt (`stop_hook_active` marks such turns); `continue: false` wins. Hosted tools such as `web_search` bypass hooks and some tool paths opt out, so treat hooks as a guardrail, not an enforcement boundary.

## Models

| Model | API ID | Role | API price per 1M tokens (in / out) |
|---|---|---|---|
| GPT-6 Astra | `gpt-6-astra` | OpenAI's best model; not in Codex cloud | — |
| GPT-6 Sol | `gpt-6-sol` | Cheaper frontier tier | $2 / $10 |
| GPT-6 Luna | `gpt-6-luna` | Fastest, cheapest tier | $0.10 / $0.50 |

GPT-6 Sol and Luna are in Codex for Plus, Pro, Business, Enterprise and Edu users. The Codex models page also lists `gpt-5.6-terra` (balanced), `gpt-5.6-sol` (the Sol model available in Codex cloud) and `gpt-5.3-codex-spark`, a text-only research preview for ChatGPT Pro. Switch with `/model` or `--model`. Reasoning efforts range from `low`, `medium`, `high`, `xhigh` and `max` up to `ultra` where the model supports it.

GPT-6 cached input reads are 90% off, and changing effort or toggling tools keeps the cache. OpenAI reports GPT-6 Sol (max) at 68.8% on DeepSWE v1.1, 1.1 points under Claude Fable 5 (xhigh), at about 80% lower cost per task.

**Prompting GPT-6 Astra.** Prune instructions written for weaker models:

- In AGENTS.md, point to docs by situation ("database.md for schema changes") instead of "read X before every edit", and drop reminders to run tests: Astra tests on its own.
- Astra can stop early for review. Define "done" in the request (run it, inspect, fix failures) and pre-approve safe workflows, such as a local test suite, in AGENTS.md.
- Soften strong "ask first" boundaries; Astra may take them too literally.
- Repo instructions steer other contributors' models too: guidance that helps Sol or Luna can overconstrain Astra.

Skill-description guidance from the same post is on [[skill-evolution]].

**Adoption.** Codex is the primary AI tool in every OpenAI department and generates 99.8% of OpenAI's internal output tokens; non-developer users grew 137x (individuals) and 189x (organizations) since August 2025. Task horizons: [[long-running-agents]].

## Codex CLI compared with Claude Code

| Area | Codex CLI | Claude Code |
|---|---|---|
| Instruction file | `AGENTS.md` (+ `AGENTS.override.md`), 32 KiB cap | `CLAUDE.md`, `CLAUDE.local.md`, `~/.claude/CLAUDE.md`. Reads `AGENTS.md` when the project has no CLAUDE.md, or both via **Project instructions** in `/config`; ignores `AGENTS.override.md` ([[claude-md-and-memory]]) |
| Config format | TOML: `~/.codex/config.toml`, `.codex/config.toml`, profile files | JSON: `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed settings |
| Autonomy controls | `sandbox_mode` × `approval_policy`, optional `auto_review` reviewer | Permission modes `default` (Manual), `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions` plus allow/ask/deny rules ([[permissions-and-modes]]) |
| OS sandbox | On by default: Seatbelt, `bwrap` + `seccomp`, Windows sandbox; network off | Opt-in via `/sandbox`: Seatbelt on macOS, `bubblewrap` + `socat` on Linux/WSL2 ([[sandboxing-and-security]]) |
| MCP config | `[mcp_servers.*]` in config.toml; `codex mcp add` | `.mcp.json` (project), `~/.claude.json` (local/user); `claude mcp add` ([[mcp]]) |
| Skills | `.agents/skills`, `~/.agents/skills`; `$name` | `.claude/skills/<name>/SKILL.md`, `~/.claude/skills/`; both follow the Agent Skills standard ([[skills]]) |
| Subagents | TOML in `.codex/agents/`; built-ins `default`, `worker`, `explorer` | Markdown in `.claude/agents/`, `~/.claude/agents/`; built-ins include Explore, Plan, general-purpose ([[subagents]]) |
| Hooks | `hooks.json` or inline `[hooks]`, user and project level, each definition trusted by hash | `hooks` in settings files and plugins, no per-hook trust step ([[hooks]]) |
| Non-interactive | `codex exec` | `claude -p` ([[headless-mode]]) |
