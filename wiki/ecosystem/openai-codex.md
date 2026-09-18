---
title: OpenAI Codex CLI
type: entity
tldr: "Codex CLI compared with Claude Code"
sources:
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
related: ["[[open-models]]", "[[permissions-and-modes]]", "[[sandboxing-and-security]]", "[[agent-standards]]", "[[subagents]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [codex-cli, openai-codex, codex-cli-vs-claude-code, codex-compared-with-claude-code, switching-from-codex-to-claude-code, agents-md]
valid_until: 2027-03-15
---

# OpenAI Codex CLI

Codex CLI is OpenAI's open-source (Apache-2.0) coding agent that runs locally in your terminal. The same agent ships as an IDE extension (VS Code, Cursor, Windsurf), inside the ChatGPT desktop app (`codex app`), and as the cloud agent Codex Web; CLI, extension and desktop app share one configuration. Read this page if you work with both Codex and Claude Code, or if you're porting a setup from one to the other. To run Codex on non-OpenAI models, see [[open-models]].

## Install and sign in

| Method | Install | Update |
|---|---|---|
| macOS/Linux installer | `curl -fsSL https://chatgpt.com/codex/install.sh \| sh` | same command |
| Windows installer | `powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 \| iex"` | same command |
| npm | `npm install -g @openai/codex` | same command |
| Homebrew | `brew install --cask codex` | `brew upgrade --cask codex` |

System requirements: macOS 12+, Ubuntu 20.04+/Debian 10+, or Windows 11 via WSL2 (native Windows has its own sandbox); 4 GB of RAM minimum, 8 GB recommended; Git 2.23+ optional.

`codex login` signs in with ChatGPT and uses your Plus, Pro, Business, Edu or Enterprise plan. To bill usage to an API key at standard rates instead, pipe it in with `printenv OPENAI_API_KEY | codex login --with-api-key`. Codex cloud requires the ChatGPT sign-in.

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

Two settings work together. `sandbox_mode` sets what commands can technically do (`read-only`, `workspace-write`, `danger-full-access`); `approval_policy` sets when Codex stops to ask (`on-request`, `never`, or a `granular` table). By default the network is off and writes are limited to the workspace — the current directory plus temp dirs such as `/tmp` — and even inside writable roots `.git`, `.agents` and `.codex` stay read-only.

| Intent | Flags |
|---|---|
| Auto (default in a version-controlled folder) | `--sandbox workspace-write --ask-for-approval on-request` |
| Read-only browsing | `--sandbox read-only --ask-for-approval on-request` |
| Read-only CI | `--sandbox read-only --ask-for-approval never` |
| Reviewer agent handles approvals | add `-c approvals_reviewer=auto_review` |
| No sandbox, no approvals | `--dangerously-bypass-approvals-and-sandbox` (alias `--yolo`) |

Enforcement is per OS: Seatbelt (`sandbox-exec`) on macOS, `bwrap` plus `seccomp` on Linux, a separate sandbox on native Windows. Turn on network access with `[sandbox_workspace_write] network_access = true`. To limit which domains that access can reach, also enable `[features.network_proxy]`. `approval_policy = "untrusted"` is not a valid setting and can stop Codex from starting. For per-project command approval, use `[projects."/path"] trust_level = "untrusted"`.

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

Project config ignores keys that redirect credentials or providers (`openai_base_url`, `model_provider`, `model_providers`, `notify`, `profile`, `otel` and others). Set those in the user file. `CODEX_HOME` moves the whole state directory, which defaults to `~/.codex`.

## AGENTS.md

Codex reads `AGENTS.md` before doing any work. It first reads one global file from `~/.codex`, where `AGENTS.override.md` beats `AGENTS.md`, then walks from the project root down to the working directory taking at most one file per directory: `AGENTS.override.md`, then `AGENTS.md`, then any names in `project_doc_fallback_filenames`. Files are concatenated root-first, so the file closest to your directory wins. Codex stops adding files once the total reaches `project_doc_max_bytes`, which defaults to 32 KiB. Discovery and reading both follow symlinks, so `AGENTS.md` may be a symlink to a file kept elsewhere.

## MCP, skills, subagents

- **MCP:** run `codex mcp add <name> -- <command>` for stdio servers or `codex mcp add <name> --url <url>` for streamable HTTP servers. Both write a `[mcp_servers.<name>]` table. Useful keys include `enabled_tools`, `disabled_tools`, `default_tools_approval_mode` (`auto`, `prompt`, `writes`, `approve`), `startup_timeout_sec` (default 10) and `tool_timeout_sec` (default 60). Codex always asks before destructive MCP tool calls, meaning tools annotated as destructive. A stdio entry's `command` is spawned as written, so a relative command resolves against the session's working directory (or the entry's own `cwd`), never the project root — prefer an absolute path.
- **Skills:** these follow the open Agent Skills standard (see [[agent-standards]]): a `SKILL.md` file with `name` and `description`. Codex scans `.agents/skills` in each directory from the working directory up to the repo root, plus `$HOME/.agents/skills`, `/etc/codex/skills` and the bundled system skills. Invoke one with `$skill-name` or `/skills`. The parser reads only `name`, `description` and `metadata.short-description`; every other frontmatter field is ignored (and a value with an unquoted colon is repaired rather than rejected), so a SKILL.md written for another harness loads unchanged. Discovery follows symlinked skill *directories* under the user, repo and admin scopes but skips a symlinked `SKILL.md` *file*. The initial skill list may use at most 2% of the context window, or 8,000 characters when the window size is unknown. Create skills with `$skill-creator`, install them with `$skill-installer`.
- **Subagents:** Codex spawns subagents only when you ask or when AGENTS.md or a skill instructs it to. Built-in agents are `default`, `worker` and `explorer`. Custom agents are TOML files in `~/.codex/agents/` or `.codex/agents/`. Each needs `name`, `description` and `developer_instructions`, and can set `model`, `model_reasoning_effort`, `sandbox_mode` and `mcp_servers`. Global limits go under `[agents]`, for example `max_concurrent_threads_per_session`. Subagents inherit the parent's sandbox policy and any live `/permissions` overrides.

## Hooks

Hooks run scripts or MCP tools at lifecycle points. They are on by default (`[features] hooks = false` turns them off) and are declared in a `hooks.json` file or in inline `[hooks]` tables inside `config.toml`, at user level (`~/.codex/`) and project level (`<repo>/.codex/`); enabled plugins bundle their own, and administrators can pin hooks in `requirements.toml`. Every matching hook from every source runs — a higher-precedence layer adds to the lower ones rather than replacing them — and project hooks load only when the project `.codex/` layer is trusted.

Before a non-managed hook runs you must review and trust that exact definition, and trust is recorded against the definition's hash, so editing a trusted hook re-arms the review and the hook is skipped until you trust it again. `/hooks` lists sources, reviews changes, and trusts or disables individual hooks; `--dangerously-bypass-hook-trust` skips the requirement for one invocation. Managed hooks (system, MDM, cloud or `requirements.toml`) are trusted by policy and cannot be disabled from the hook browser.

Events: `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `Stop` and `Interrupt`. Each event holds matcher groups, and each group holds handlers: a `command` handler (with `timeout` in seconds, default 600 — `SessionEnd` and `Interrupt` default to 1 second and cap at 3 — plus optional `statusMessage`, `additionalContextLimit`, `commandWindows` and `async: true` to run in the background) or an `mcp_tool` handler naming an already-connected `server` and `tool` with `${field.nested}` argument templates. `prompt` and `agent` handlers are parsed and skipped. Commands run with the session `cwd` as their working directory, so repo-local hooks should resolve from the git root rather than a relative path.

Each command hook receives one JSON object on stdin: `session_id`, `transcript_path`, `cwd`, `hook_event_name` and `model`, plus `permission_mode` and `turn_id` on turn-scoped events and the event's own fields — `tool_name`, `tool_use_id`, `tool_input` and (on `PostToolUse`) `tool_response`; `prompt`; `source`; `trigger`; `reason`; `agent_id`/`agent_type`; `stop_hook_active` and `last_assistant_message`. Model-visible hook output is capped around 2,500 tokens by default and spilled to a file on disk beyond that.

A `matcher` is a regex; `"*"`, `""` or an omitted matcher matches every occurrence. It filters the tool name on `PreToolUse`, `PermissionRequest` and `PostToolUse`, the compaction `trigger` on `PreCompact`/`PostCompact`, the start `source` on `SessionStart`, the end `reason` on `SessionEnd` and the subagent type on `SubagentStart`/`SubagentStop`; it is ignored for `UserPromptSubmit`, `Stop` and `Interrupt`. `apply_patch` also matches `Edit` or `Write`, and `spawn_agent` also matches `Agent`.

A `PreToolUse` hook has three ways to block a call: `hookSpecificOutput.permissionDecision: "deny"` with a `permissionDecisionReason`, the older `{"decision": "block", "reason": …}`, or exit code 2 with the reason on stderr. `permissionDecision: "allow"` plus `updatedInput` rewrites the call instead. File edits arrive as `apply_patch` with the entire patch text in `tool_input.command` and **no file-path field**, so a hook that cares about paths must parse the patch's `*** Add File:` / `*** Update File:` / `*** Delete File:` lines; a rewrite must return a replacement `command` string.

After a call, `PostToolUse` can inject model-visible context with `hookSpecificOutput.additionalContext`. Its `decision: "block"` (or exit code 2) cannot undo the side effects, but it replaces the tool result with the hook's feedback and continues from there; `continue: false` stops normal processing of the original result. A `Stop` hook's `decision: "block"` likewise does not reject the turn — Codex keeps going and turns the `reason` into a new continuation prompt, with `stop_hook_active` marking a turn already continued that way; a `continue: false` from any matching `Stop` hook wins over continuation decisions. Hosted tools such as web search (`web_search`) are not on the local function-tool hook path, so no hook sees them, and some specialized tool paths opt out: treat tool hooks as a guardrail, not an enforcement boundary.

## Models

The Codex models page recommends `gpt-6-astra` (not in Codex cloud), `gpt-5.6-sol` (available in cloud), `gpt-5.6-terra` (balanced) and `gpt-5.6-luna` (fastest and cheapest). It also lists `gpt-5.3-codex-spark`, a text-only research preview for ChatGPT Pro that isn't on ChatGPT web. Switch with `/model` or `--model`. Reasoning efforts range from `low`, `medium`, `high`, `xhigh` and `max` up to `ultra` where the model supports it.

## Codex CLI compared with Claude Code

Area by area; the Claude Code column comes from the official Claude Code docs.

| Area | Codex CLI | Claude Code |
|---|---|---|
| Install | `install.sh`, npm `@openai/codex`, `brew install --cask codex` | `curl -fsSL https://claude.ai/install.sh \| bash`, `brew install --cask claude-code`, `winget install Anthropic.ClaudeCode` |
| Instruction file | `AGENTS.md` (+ `AGENTS.override.md`), 32 KiB cap | `CLAUDE.md`, `CLAUDE.local.md`, `~/.claude/CLAUDE.md`. It does not read `AGENTS.md` directly: put `@AGENTS.md` in CLAUDE.md or symlink it ([[claude-md-and-memory]]) |
| Config format | TOML: `~/.codex/config.toml`, `.codex/config.toml`, profile files | JSON: `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed settings |
| Autonomy controls | `sandbox_mode` × `approval_policy`, optional `auto_review` reviewer | Permission modes `default` (Manual), `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions` plus allow/ask/deny rules ([[permissions-and-modes]]) |
| OS sandbox | On by default: Seatbelt, `bwrap` + `seccomp`, Windows sandbox; network off | Opt-in via `/sandbox`: Seatbelt on macOS, `bubblewrap` + `socat` on Linux/WSL2 ([[sandboxing-and-security]]) |
| MCP config | `[mcp_servers.*]` in config.toml; `codex mcp add` | `.mcp.json` (project), `~/.claude.json` (local/user); `claude mcp add` ([[mcp]]) |
| Skills | `.agents/skills`, `~/.agents/skills`; `$name` | `.claude/skills/<name>/SKILL.md`, `~/.claude/skills/`; both follow the Agent Skills standard ([[skills]]) |
| Subagents | TOML in `.codex/agents/`; built-ins `default`, `worker`, `explorer` | Markdown in `.claude/agents/`, `~/.claude/agents/`; built-ins include Explore, Plan, general-purpose ([[subagents]]) |
| Hooks | `hooks.json` or inline `[hooks]`, user and project level, each definition trusted by hash | `hooks` in settings files and plugins, no per-hook trust step ([[hooks]]) |
| Non-interactive | `codex exec` | `claude -p` ([[headless-mode]]) |
| Resume | `codex resume` | `claude -c`, `claude -r "<session>"` |
