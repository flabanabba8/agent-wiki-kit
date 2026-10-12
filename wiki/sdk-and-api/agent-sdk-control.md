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
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [agent-sdk-permissions, agent-sdk-hooks, agent-sdk-sessions, can-use-tool, agent-sdk-subagents]
---

# Agent SDK Control Surfaces

How an [[agent-sdk]] application steers a run. Options are named Python / TypeScript. The underlying features are documented in [[permissions-and-modes]], [[hooks]], [[mcp]], [[subagents]] and [[skills]]; this page covers only what is specific to the SDK.

## Sessions

A session is the transcript the SDK writes to `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl` (under `CLAUDE_CONFIG_DIR` when set). It records the conversation, not the filesystem.

| Need | Use |
|---|---|
| Continue the latest session in this directory after a restart | `continue_conversation=True` / `continue: true` |
| Return to a specific session | Read `session_id` from the result, then pass it as `resume` |
| Branch off without changing the original | `resume` plus `fork_session=True` / `forkSession: true`; Python's `resume_session_at` branches from an earlier message UUID |
| Write nothing to disk | `persistSession: false` (TypeScript). In Python, set `CLAUDE_CODE_SKIP_PROMPT_HISTORY` in `env` |

You can resume from any working directory on the same machine. To resume on another host, attach a `session_store` / `sessionStore` ([[agent-sdk-deployment]]) or move the JSONL file. `list_sessions()`, `get_session_messages()`, `get_session_info()`, `rename_session()` and `tag_session()` (camelCase in TypeScript) build session pickers and viewers. General session behavior is in [[sessions-and-checkpoints]].

**File checkpointing.** With `enable_file_checkpointing` / `enableFileCheckpointing`, the SDK backs up files before `Write`, `Edit` or `NotebookEdit` change them. User messages carry checkpoint UUIDs; `rewind_files()` / `rewindFiles()` restores files, not the conversation. Bash edits, most subagent edits, directory operations and remote files aren't tracked, and it can't be combined with a session store.

## Change configuration mid-session

Only a streaming-input session can be reconfigured while it runs. The setters are methods on the object `query()` returns in TypeScript, and on `ClaudeSDKClient` in Python, whose `query()` returns a plain iterator.

1. **Hooks.** `PreToolUse` hooks run first and can deny a call. A hook `allow` doesn't skip deny and ask rules.
2. **Deny rules** from `disallowed_tools` and settings block even in `bypassPermissions`. A bare name such as `"Bash"` removes the tool from context. Globs such as `"mcp__*"` work here.
3. **Ask rules** from settings route the call to `can_use_tool`, even in `bypassPermissions`. `AskUserQuestion`, MCP tools needing user interaction, and connector tools your organization set to `ask` always reach the callback.
4. **Permission mode** (see the table below).
5. **Allow rules** from `allowed_tools` and settings. Calls needing no approval (reads in working directories, read-only Bash) also resolve here.
6. **The `can_use_tool` callback** decides the rest; `dontAsk` denies instead.

Each model keeps its own prompt cache, so the request after a switch recomputes the conversation uncached at the new model's rates. To change the agent's instructions rather than its configuration, send them in the conversation ([[agent-sdk]]).

## Permissions

| Mode | Behavior |
|---|---|
| `default` | No approvals from the mode itself. Unresolved calls go to `can_use_tool` |
| `acceptEdits` | Auto-approves edits and `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed` inside the working directory or added directories. Does not approve MCP tools |
| `plan` | Explores without editing. Edits and file-modifying shell commands always go to the callback |
| `dontAsk` | Denies anything that would prompt, and never calls the callback. Pair it with `allowed_tools` for a fixed tool surface |
| `auto` | A model classifier approves or denies prompts |
| `bypassPermissions` | Approves everything that reaches the mode step. TypeScript also requires `allowDangerouslySkipPermissions: true`. On Linux and macOS, as root or under `sudo` outside a recognized sandbox, the query fails before the first turn |

Change mode mid-session with `set_permission_mode()` / `setPermissionMode()`. A subagent runs in its parent's mode; its own `permissionMode` applies only under a `default`, `dontAsk` or `plan` parent, and never grants `bypassPermissions`.

### Rules that trip people up

- `allowed_tools` pre-approves; it doesn't restrict. Under `bypassPermissions`, `allowed_tools=["Read"]` still lets `Bash` run. Block with `disallowed_tools`.
- Allow-rule globs need a literal server prefix. `mcp__github__*` works, but `"*"` or `"mcp__*"` in an allow rule is ignored with a warning.
- `Edit(path)` rules cover every built-in tool that writes files. `//path` means an absolute path; `/path` is relative to the session's working directory.
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
- **Approve with changes.** Return a modified `updated_input`; Claude isn't told.
- **Remember the decision.** Echo entries from `context.suggestions` back in `updated_permissions`. A `localSettings` suggestion writes the rule to `.claude/settings.local.json`.
- **Clarifying questions.** An `AskUserQuestion` call holds 1–4 questions with 2–4 options each; answer with a map from question text to chosen label. Include it in any explicit `tools` list. Subagents can't use it.
- **Slow approvals.** If a person may answer later than your process can wait, have a `PreToolUse` hook return `defer` and resume the session later.

## Hooks

Programmatic hooks are async callbacks passed in `hooks`. They run in your process, use no context, and also fire inside subagents (`agent_id` and `agent_type` identify the agent). Filesystem hooks from `settings.json` run alongside them when their source is loaded.

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
- **Matchers.** A matcher tests the tool name (MCP tools are `mcp__<server>__<tool>`), not arguments; filter paths inside the callback.
- **Outputs.** Return `{}` to allow. In `hookSpecificOutput`, `PreToolUse` sets `permissionDecision` (`allow`, `deny`, `ask`, `defer`), `permissionDecisionReason` and `updatedInput`; `PostToolUse` sets `additionalContext` or `updatedToolOutput`. Top-level `systemMessage` shows the user a message; `continue` stops or continues the agent. When hooks disagree, `deny` beats `defer`, `defer` beats `ask`, and `ask` beats `allow`.
- **Async.** Return `async` (`async_` in Python) for non-blocking side effects such as logging.
- **Timeouts.** The default is 600 s for most events and 30 s for `UserPromptSubmit`; set `timeout` on the matcher. A timed-out callback is cancelled and its output discarded. On `PreToolUse` the tool doesn't run; on `UserPromptSubmit` the prompt is blocked; on `Stop`, `SubagentStop` and `SessionStart` it counts as no decision or output, and your other hooks' decisions still apply.

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

- **Sources.** `mcp_servers`, or `.mcp.json` via the `project` source. `strict_mcp_config=True` ignores every other source, including claude.ai connectors.
- **Transports.** stdio (a command), `http` or `sse` (a URL), or an in-process SDK server.
- **Permission.** MCP tools need approval. Prefer `allowed_tools` wildcards: `acceptEdits` doesn't cover MCP tools.
- **Status.** The `init` message reports each server as `pending`, `connected`, `failed`, `needs-auth` or `disabled`; `pending` alone isn't failure. Poll `get_mcp_status()` / `mcpServerStatus()`, and retry with `reconnect_mcp_server()` / `reconnectMcpServer()`.
- **First-turn wait.** If `mcp_servers` holds a stdio, HTTP or SSE server, the first turn waits up to `MCP_TIMEOUT` for pending servers (including `.mcp.json` and plugin servers). Otherwise it waits up to 2 s, and with tool search on (the default) only for `alwaysLoad` servers. Set `CLAUDE_CODE_MCP_STARTUP_WAIT_MS` in `env` to set the wait for every pending server (`0` skips it); servers still pending keep connecting in the background.
- **Provenance.** Hook inputs carry `mcp_server` and TypeScript `can_use_tool` options carry `mcpServer`, with `name` and `source` (`sdk`, `plugin`, `dynamic` for `mcp_servers` entries, or a config scope such as `project`). Base trust on `source`, never on the name or tool prefix.
- **OAuth.** The SDK runs no browser flow; complete OAuth in your app and pass the token in `headers`.
- **Limits.** Connections time out after 30 s (`MCP_TIMEOUT`); tool calls have `MCP_TOOL_TIMEOUT`. Results over 25,000 tokens go to a file (`MAX_MCP_OUTPUT_TOKENS`). Tool search defers MCP tool schemas by default.

**Custom tools** are in-process MCP servers. Define one with `@tool` (Python) or `tool()` with a Zod schema (TypeScript), wrap it with `create_sdk_mcp_server` / `createSdkMcpServer`, pass it under `mcp_servers`, and allow `mcp__<server>__<tool>`. Handlers return `content` blocks, optionally with `structuredContent` and `isError: true`. They run one at a time unless their annotations set `readOnlyHint` ([[tool-design]]).

## Subagents

Define subagents in `agents`; they override same-named files in `.claude/agents/`. Claude invokes them through the `Agent` tool, and the built-in `general-purpose` agent is available unless removed ([[subagents]]).

Each entry is an `AgentDefinition`:

| Field | Notes |
|---|---|
| `description`, `prompt` | Required: when to use the agent, and its system prompt |
| `tools`, `disallowedTools` | The agent's tool set. Tools left out don't exist for the subagent |
| `model`, `effort` | A model alias (`sonnet`, `opus`, `haiku`, `inherit`) or full model ID, and effort level |
| `skills`, `mcpServers`, `memory` | Skills to preload, MCP servers, memory source |
| `maxTurns`, `background`, `permissionMode` | Turn cap (output is marked partial when hit), forced background run, permission mode |

Field names are camelCase in Python too.

- **Context.** A subagent sees only its own prompt, the Agent tool's prompt string, project CLAUDE.md and its tools, never the parent's history. Only its final message returns.
- **Background.** Subagents run in the background by default.
- **Limits.** Cap the tree with `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (default 3), `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (default 20) and `max_budget_usd`, which counts the call's own spend including subagents. Claude Opus 5 delegates readily, so set these limits on Opus 5 runs.
- **Detection.** A subagent call is a `tool_use` block named `Agent` (listed as `Task` in `init`). Messages from inside it carry `parent_tool_use_id`. To resume one, resume its session and name the `agentId` from the Agent tool result in your prompt.
- **Larger fan-out.** For dozens of agents, use the TypeScript SDK's `Workflow` tool ([[workflows]]).

## Skills, commands and plugins

- **Skills.** Skills are `SKILL.md` files discovered through setting sources, not registered in code. `skills="all"`, a list of names, or `[]` controls which Claude may invoke. Setting `skills` allows `Skill`; include `"Skill"` in any explicit `tools` list.
- **Commands.** Send `/<name>` in the prompt to run any command or user-invocable skill, whatever the `skills` list says. `init.slash_commands` lists what's available. A `/<name>` that matches nothing goes to Claude as an ordinary message (costing a turn); a built-in unavailable in the SDK, such as `/theme`, returns an "isn't available" result without a turn. `/compact` needs earlier turns, and `/clear` resets context in a streaming session.
- **Plugins.** `plugins=[{"type": "local", "path": "./my-plugin"}]` loads a plugin's skills, agents, hooks and MCP servers from a local directory (`~` isn't expanded). Invoke skills as `/plugin-name:skill-name`; `init.plugins` confirms each loaded. See [[plugins]].

## Structured output

Pass `output_format={"type": "json_schema", "schema": ...}`. The result's `structured_output` field holds validated JSON. Schemas use JSON Schema draft-07; with Zod, convert via `z.toJSONSchema(schema, { target: "draft-7" })`. The SDK re-prompts on mismatch and finally ends with `error_max_structured_output_retries`. Treat a `success` result without `structured_output` as a failure too. It isn't streamed as deltas. CLI equivalent: [[headless-mode]].

## Streaming output

Set `include_partial_messages=True` / `includePartialMessages: true` to receive raw API events as `StreamEvent` messages. Accumulate `content_block_delta` events: a `text_delta` carries text, and an `input_json_delta` carries tool input. Stream events come only from the main session. In Python, `forward_subagent_text` forwards subagents' complete text blocks.
