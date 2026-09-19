---
title: Agent SDK Control Surfaces
type: reference
tldr: "SDK sessions, permissions, hooks, MCP, subagents"
sources:
  - raw/docs/official/agent-sdk__sessions.md
  - raw/docs/official/agent-sdk__configuration.md
  - raw/docs/official/agent-sdk__file-checkpointing.md
  - raw/docs/official/agent-sdk__permissions.md
  - raw/docs/official/agent-sdk__user-input.md
  - raw/docs/official/agent-sdk__hooks.md
  - raw/docs/official/agent-sdk__mcp.md
  - raw/docs/official/agent-sdk__custom-tools.md
  - raw/docs/official/agent-sdk__subagents.md
  - raw/docs/official/agent-sdk__skills.md
  - raw/docs/official/agent-sdk__plugins.md
  - raw/docs/official/agent-sdk__structured-outputs.md
  - raw/docs/official/agent-sdk__streaming-output.md
  - raw/docs/official/agent-sdk__python.md
  - raw/docs/official/agent-sdk__typescript.md
related: ["[[agent-sdk]]", "[[permissions-and-modes]]", "[[hooks]]", "[[mcp]]", "[[subagents]]", "[[skills]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [agent-sdk-permissions, agent-sdk-hooks, agent-sdk-sessions, can-use-tool, agent-sdk-subagents, set-model-mid-session]
---

# Agent SDK Control Surfaces

How an [[agent-sdk]] application steers a run: sessions, permissions, hooks, MCP and custom tools, subagents, skills, plugins, structured output and streaming. Options are named Python / TypeScript. Only SDK-specific behavior is here; the underlying features are in [[permissions-and-modes]], [[hooks]], [[mcp]], [[subagents]] and [[skills]].

## Sessions

A session is the conversation transcript the SDK writes to `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`, or under `CLAUDE_CONFIG_DIR`. It records the conversation, not the filesystem.

| Need | Use |
|---|---|
| Continue the latest session in this directory after a restart | `continue_conversation=True` / `continue: true` |
| Return to a specific session | Read `session_id` from the result, then pass it as `resume` |
| Branch off without changing the original | `resume` plus `fork_session=True` / `forkSession: true`; Python's `resume_session_at` branches from an earlier message UUID |
| Write nothing to disk | `persistSession: false` (TypeScript). In Python, set `CLAUDE_CODE_SKIP_PROMPT_HISTORY` in `env` |

Resuming works from any working directory while the session file is on the same machine. To resume on another host, attach a `session_store` / `sessionStore` ([[agent-sdk-deployment]]), move the JSONL file, or pass the results you need into a fresh session. For pickers and viewers: `list_sessions()`, `get_session_messages()`, `get_session_info()`, `rename_session()`, `tag_session()` (camelCase in TypeScript). General behavior: [[sessions-and-checkpoints]].

**File checkpointing.** With `enable_file_checkpointing` / `enableFileCheckpointing`, the SDK backs up files before `Write`, `Edit` or `NotebookEdit` changes them. User messages carry checkpoint UUIDs, and `rewind_files()` / `rewindFiles()` restores the files, not the conversation. Bash edits, most subagent edits, directory operations and remote files are untracked.

## Change configuration mid-session

Only a streaming-input session can be reconfigured while it runs. The setters are methods on the object `query()` returns in TypeScript, and on `ClaudeSDKClient` in Python, whose `query()` returns a plain iterator.

| Call | Effect |
|---|---|
| `set_model()` / `setModel()` | Switches the model. With no model (`undefined` or `"default"`) it resets to Claude Code's default, not the `model` from options |
| `set_permission_mode()` / `setPermissionMode()` | Switches the permission mode |
| `applyFlagSettings(settings)` (TypeScript) | Merges settings-file keys, such as `{ effortLevel: "high" }` or tighter `permissions`, into the session's flag layer. Calls shallow-merge top-level keys, so a second `permissions` object replaces the first; `null` clears a key, and a cleared `model` resets to Claude Code's default even when a settings file names one |
| `updateSettings("localSettings", settings)` (TypeScript) | Writes an allowlisted key set, currently `outputStyle`, to `.claude/settings.local.json`. Effective on the next request, and persistent for later sessions that load `local` settings. Rejected on remote transports and when `settingSources` excludes `local` |

Each model keeps its own prompt cache, so the request after a switch recomputes the conversation uncached at the new model's rates. To change the agent's instructions rather than its configuration, send them in the conversation ([[agent-sdk]]).

## Permissions

### Evaluation order

1. **Hooks.** `PreToolUse` hooks run first and can deny outright; a hook `allow` doesn't skip the deny and ask rules.
2. **Deny rules** from `disallowed_tools` and settings block a call even in `bypassPermissions`. A bare name such as `"Bash"` removes the tool from Claude's context entirely, and globs such as `"*"` work here.
3. **Ask rules** from settings route the call to `can_use_tool`, even in `bypassPermissions`, as do the calls no mode auto-approves ([[permissions-and-modes]]).
4. **Permission mode**, set by `permission_mode` and the setter above.
5. **Allow rules** from `allowed_tools` and settings, plus calls needing no approval at all, such as working-directory reads and read-only Bash.
6. **The `can_use_tool` callback** decides whatever is left. In `dontAsk` this step is skipped and the call is denied.

The modes themselves are in [[permissions-and-modes]]. What the SDK adds: `acceptEdits` doesn't approve MCP tools; `plan` sends every edit and file-modifying command to the callback; `dontAsk` pairs with `allowed_tools` for a fixed CI tool surface; `bypassPermissions` also needs `allowDangerouslySkipPermissions: true` in TypeScript. A subagent runs in its parent's mode; its own `permissionMode` applies only when the parent is `default`, `dontAsk` or `plan`, and never grants `bypassPermissions`.

### Rules that trip people up

- `allowed_tools` pre-approves tools without restricting the set: under `bypassPermissions`, `allowed_tools=["Read"]` still lets `Bash` run.
- Rule syntax follows [[permissions-and-modes]]: an allow glob needs a literal `mcp__<server>__` prefix, so `"*"` and `"mcp__*"` are ignored with a warning, and `Edit(path)` rules cover every built-in tool that writes files, with `//path` absolute and `/path` relative to the session's working directory.
- `can_use_tool` never runs for auto-approved calls. For a check that must see every call, use a `PreToolUse` hook.

### Approvals and clarifying questions

The loop pauses until `can_use_tool(tool_name, input, context)` returns.

```python
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

async def can_use_tool(tool_name, input_data, context):
    if await ask_user(f"Allow {tool_name}?"):   # your own UI
        return PermissionResultAllow(updated_input=input_data)
    return PermissionResultDeny(message="User declined")
```

- **Return values.** In TypeScript, return `{ behavior: "allow", updatedInput }` or `{ behavior: "deny", message }`.
- **Approve with changes.** Return a modified `updated_input`; Claude isn't told the input changed.
- **Remember the decision.** Echo entries from `context.suggestions` back in `updated_permissions`; a `localSettings` suggestion writes the rule to `.claude/settings.local.json`.
- **Clarifying questions.** An `AskUserQuestion` call holds 1–4 questions with 2–4 options each. Allow it with an `updated_input` echoing `questions` plus an `answers` map from question text to the chosen label. Include the tool in any explicit `tools` list; it is unavailable inside subagents.
- **Slow approvals.** When an answer may outlast your process, have a `PreToolUse` hook return `defer` and resume the persisted session later.

## Hooks

Programmatic hooks are async callbacks passed in `hooks`. They run in your process, use no context, and also fire inside subagents, where `agent_id` and `agent_type` identify the agent. Filesystem hooks from `settings.json` run alongside them when their setting source loads.

```python
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

async def protect_env(input_data, tool_use_id, context):
    if input_data["tool_input"].get("file_path", "").endswith(".env"):
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                "permissionDecision": "deny", "permissionDecisionReason": "No .env writes"}}
    return {}

options = ClaudeAgentOptions(
    hooks={"PreToolUse": [HookMatcher(matcher="Write|Edit", hooks=[protect_env])]})
```

- **Events in both SDKs:** `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `Stop`, `SubagentStart`, `SubagentStop`, `PreCompact`, `PermissionRequest`, `Notification`. TypeScript adds many more, including `SessionStart`, `SessionEnd`, `PostCompact`, `PermissionDenied` and `TaskCompleted`. In Python, session hooks exist only as settings-file hooks.
- **Matchers.** A matcher tests the tool name (`mcp__<server>__<tool>` for MCP tools), not the arguments; filter on file paths inside the callback.
- **Outputs.** Return `{}` to allow, or the JSON shapes the CLI's hooks use ([[hooks]]): `permissionDecision`, `permissionDecisionReason`, `updatedInput`, `additionalContext`, `updatedToolOutput`, `systemMessage`, `continue`. When hooks disagree, `deny` beats `defer`, `defer` beats `ask`, and `ask` beats `allow`.
- **Async.** Return `async` (`async_` in Python) for non-blocking side effects such as logging.
- **Timeouts.** The default is 600 s for most events and 30 s for `UserPromptSubmit`. Set `timeout` on the matcher to change it. A timed-out callback's output is discarded and the session continues: a timed-out `PreToolUse` leaves the tool unrun, while a timed-out `Stop`, `SubagentStop` or `SessionStart` counts as no decision and your other hooks on the event still apply.

The event catalogue and JSON schema are in [[hooks]].

## MCP servers and custom tools

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "fs": {"command": "npx", "args": ["@modelcontextprotocol/server-filesystem", "./data"]},
        "remote": {"type": "http", "url": "https://mcp.example.com/mcp",
                   "headers": {"Authorization": "Bearer <token>"}},
    },
    allowed_tools=["mcp__fs__*", "mcp__remote__search"],
)
```

- **Where servers come from.** `mcp_servers`, or a project `.mcp.json` via the `project` source; `strict_mcp_config=True` ignores every other source, including claude.ai connectors.
- **Transports.** stdio, `http` and `sse` as in the CLI ([[mcp]]), or an in-process SDK server.
- **Permission.** MCP tools need approval; prefer `allowed_tools` wildcards, since `acceptEdits` doesn't cover MCP tools and `bypassPermissions` approves far more than you need.
- **Status.** The `init` message reports each server as `pending`, `connected`, `failed`, `needs-auth` or `disabled`, and `pending` alone doesn't mean failure. Poll `get_mcp_status()` / `mcpServerStatus()`, and retry with `reconnect_mcp_server()` / `reconnectMcpServer()`.
- **Startup wait.** Servers from settings files or plugins commonly show `pending` at init. The first turn waits for them up to `MCP_TIMEOUT` when `mcp_servers` holds a stdio, HTTP or SSE server, and 2 s otherwise — with tool search on, only for `alwaysLoad` servers. `CLAUDE_CODE_MCP_STARTUP_WAIT_MS` in `env` replaces both deadlines and `0` skips the wait, except for a `permission_prompt_tool_name` server. Pending servers keep connecting in the background.
- **Provenance.** Hook inputs carry `mcp_server`, and `can_use_tool` options `mcpServer`: the server name plus a `source` of `sdk` (registered in-process by your application), `plugin`, or a configuration scope such as `project`, `dynamic` or `managed`. Only the host can register `sdk`, so base trust on `source`, never the name or `mcp__<server>__` prefix.
- **OAuth.** The SDK doesn't run an OAuth browser flow. Complete OAuth in your own app and pass the token in `headers`.
- **Limits.** Connection, tool-call and result-size limits match the CLI's ([[mcp]]), and tool search defers MCP tool schemas by default.

**Custom tools** are in-process MCP servers. Define one with `@tool` (Python) or `tool()` with a Zod schema (TypeScript), wrap it with `create_sdk_mcp_server` / `createSdkMcpServer`, pass it under `mcp_servers`, and allow `mcp__<server>__<tool>`. Handlers return `content` blocks, optionally with `structuredContent` and `isError: true`. They run one at a time unless their annotations set `readOnlyHint` ([[tool-design]]).

## Subagents

Define subagents in `agents`; they override same-named files in `.claude/agents/`. Claude invokes them through the `Agent` tool, and the built-in `general-purpose` agent is available unless removed ([[subagents]]).

Each entry is an `AgentDefinition` (Python) or object (TypeScript):

| Field | Notes |
|---|---|
| `description`, `prompt` | Required: when to use the agent, and its system prompt |
| `tools`, `disallowedTools` | The agent's tool set. Tools left out don't exist for the subagent |
| `model`, `effort` | A model alias (`sonnet`, `opus`, `haiku`, `inherit`) or full model ID, and effort level |
| `skills`, `mcpServers`, `memory` | Skills to preload, MCP servers, memory source |
| `maxTurns`, `background`, `permissionMode` | Turn cap (output is marked partial when hit), forced background run, permission mode |

Field names stay camelCase in Python, too.

- **Context.** A subagent sees only its own prompt, the Agent tool's prompt string, project CLAUDE.md and its tools, never the parent's history; only its final message returns.
- **Background.** Subagents run in the background by default.
- **Limits.** The nesting-depth and concurrency caps apply here too ([[subagents]]), and `max_budget_usd` caps spend ([[agent-sdk-deployment]]). Claude Opus 5 delegates readily, so set them on Opus 5 runs.
- **Detection.** A subagent call is a `tool_use` block named `Agent`, listed as `Task` in `init`; messages from inside one carry `parent_tool_use_id`. To resume a subagent, resume its session and name the `agentId` from the Agent tool result in your prompt.
- **Larger fan-out.** For dozens of agents, use the TypeScript SDK's `Workflow` tool ([[workflows]]).

## Skills, commands and plugins

- **Skills.** Skills are `SKILL.md` files discovered through setting sources; there's no API for registering them in code. `skills="all"`, a list of exact names, or `[]` controls which Claude may invoke. Setting `skills` adds `Skill` to the allowed tools; include `"Skill"` in any explicit `tools` list.
- **Commands.** Send `/<name>` in the prompt to run any command or user-invocable skill, whatever the `skills` list says; `init.slash_commands` lists what's available. `/compact` needs earlier turns to summarize, and `/clear` resets context in a streaming session. A name matching nothing reaches Claude as an ordinary message noting the command didn't run, costing a turn; a built-in the session lacks, such as `/theme`, returns `/theme isn't available in this environment.` without one.
- **Plugins.** `plugins=[{"type": "local", "path": "./my-plugin"}]` loads a plugin's skills, agents, hooks and MCP servers from a local directory (`~` is not expanded). Invoke plugin skills as `/plugin-name:skill-name`, and check `init`'s `plugins` list to confirm each loaded ([[plugins]]).

## Structured output

Pass `output_format={"type": "json_schema", "schema": FeaturePlan.model_json_schema()}` and the result's `structured_output` field holds validated JSON. Schemas use JSON Schema draft-07; with Zod, convert via `z.toJSONSchema(schema, { target: "draft-7" })`. The SDK re-prompts on a mismatch and ends the run with `error_max_structured_output_retries` if nothing validates. Treat a `success` result without `structured_output` as a failure too. It is never streamed as deltas; the CLI equivalent is in [[headless-mode]].

## Streaming output

Set `include_partial_messages=True` / `includePartialMessages: true` for `StreamEvent` messages with raw API events. Accumulate `content_block_delta` events: `text_delta` carries text, `input_json_delta` tool input. Only the main session emits them; in Python, `forward_subagent_text` forwards subagents' complete text blocks instead.
