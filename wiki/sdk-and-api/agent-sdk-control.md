---
title: Agent SDK Control Surfaces
type: reference
tldr: "SDK sessions, permissions, hooks, MCP, subagents"
sources:
  - raw/docs/official/agent-sdk__sessions.md
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
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [agent-sdk-permissions, agent-sdk-hooks, agent-sdk-sessions, can-use-tool, agent-sdk-subagents]
---

# Agent SDK Control Surfaces

This page covers how an [[agent-sdk]] application steers a run: sessions, permissions and approvals, hook callbacks, MCP and custom tools, subagents, skills and plugins, structured output, and streaming. Options are named Python / TypeScript. The underlying Claude Code features are documented in [[permissions-and-modes]], [[hooks]], [[mcp]], [[subagents]] and [[skills]]; this page covers only what is specific to the SDK.

## Sessions

A session is the conversation transcript the SDK writes to `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`, or under `CLAUDE_CONFIG_DIR` when that is set. It records the conversation, not the state of the filesystem.

| Need | Use |
|---|---|
| One-shot task | A single `query()` call |
| Multi-turn chat in one process | `ClaudeSDKClient` (Python) or `continue: true` (TypeScript) |
| After a restart, continue the latest session in this directory | `continue_conversation=True` / `continue: true` |
| Return to a specific session | Read `session_id` from the result, then pass it as `resume` |
| Branch off without changing the original | `resume` plus `fork_session=True` / `forkSession: true`. In Python, `resume_session_at` branches from an earlier message UUID |
| Write nothing to disk | `persistSession: false` (TypeScript). In Python, set `CLAUDE_CODE_SKIP_PROMPT_HISTORY` in `env` |

You can resume from any working directory, as long as the session file is on the same machine. To resume on another host, attach a `session_store` / `sessionStore` ([[agent-sdk-deployment]]), move the JSONL file, or pass the results you need into a fresh session. `list_sessions()`, `get_session_messages()`, `get_session_info()`, `rename_session()` and `tag_session()` (camelCase in TypeScript) are for building session pickers and transcript viewers. General session behavior is in [[sessions-and-checkpoints]].

**File checkpointing.** Set `enable_file_checkpointing` / `enableFileCheckpointing` and the SDK backs up files before `Write`, `Edit` or `NotebookEdit` changes them. User messages carry checkpoint UUIDs, and `rewind_files()` / `rewindFiles()` restores the files (the conversation is not rewound). Bash edits, most subagent edits, directory operations and remote files are not tracked, and checkpointing can't be combined with a session store.

## Permissions

### Evaluation order

1. **Hooks.** `PreToolUse` hooks run first and can deny a call outright. A hook `allow` does not skip the deny and ask rules.
2. **Deny rules** from `disallowed_tools` and settings. They block a call even in `bypassPermissions`. A bare name such as `"Bash"` removes the tool from Claude's context entirely. Globs such as `"*"` and `"mcp__*"` are allowed in deny rules.
3. **Ask rules** from settings route the call to `can_use_tool`, even in `bypassPermissions`. `AskUserQuestion`, MCP tools that require user interaction, and connector tools your organization set to `ask` always reach the callback.
4. **Permission mode** (see the table below).
5. **Allow rules** from `allowed_tools` and settings. Calls that need no approval at all, such as reads inside the working directories and read-only Bash, also resolve here.
6. **The `can_use_tool` callback** decides whatever is left. In `dontAsk` this step is skipped and the call is denied.

No mode or allow rule ever auto-approves an `rm` or `rmdir` that targets a critical path.

### Modes

| Mode | Behavior |
|---|---|
| `default` | No approvals from the mode itself. Unresolved calls go to `can_use_tool` |
| `acceptEdits` | Auto-approves edits and `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed` inside the working directory or added directories. Does not approve MCP tools |
| `plan` | Explores without editing. Edits and file-modifying shell commands always go to the callback |
| `dontAsk` | Denies anything that would prompt, and never calls the callback. Pair it with `allowed_tools` for a fixed tool surface |
| `auto` | A model classifier approves or denies prompts |
| `bypassPermissions` | Approves everything that reaches the mode step. TypeScript also requires `allowDangerouslySkipPermissions: true`. Not allowed when running as root on Unix |

To change mode mid-session, call `set_permission_mode()` / `setPermissionMode()`. A subagent runs in its parent's mode. Its own `permissionMode` applies only when the parent is in `default`, `dontAsk` or `plan`, and a subagent never gets `bypassPermissions` from its definition.

### Rules that trip people up

- `allowed_tools` pre-approves tools; it does not restrict the tool set. Under `bypassPermissions`, `allowed_tools=["Read"]` still lets `Bash` run. Use `disallowed_tools` to block tools.
- Allow-rule globs need a literal server prefix. `mcp__github__*` works, but `"*"` or `"mcp__*"` in an allow rule is ignored with a warning.
- `Edit(path)` rules cover every built-in tool that writes files. `//path` means an absolute path; `/path` is relative to the session's working directory.
- `can_use_tool` never runs for auto-approved calls. For a check that must see every call, use a `PreToolUse` hook.

### Approvals and clarifying questions

The loop pauses until `can_use_tool(tool_name, input, context)` returns:

```python
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

async def can_use_tool(tool_name, input_data, context):
    if tool_name == "AskUserQuestion":
        return PermissionResultAllow(updated_input={
            "questions": input_data["questions"],
            "answers": {"How should I format the output?": "Summary"},
        })
    if await ask_user(f"Allow {tool_name}?"):   # your own UI
        return PermissionResultAllow(updated_input=input_data)
    return PermissionResultDeny(message="User declined")
```

- **Return values.** In TypeScript, return `{ behavior: "allow", updatedInput }` or `{ behavior: "deny", message }`.
- **Approve with changes.** Return a modified `updated_input`. Claude is not told the input changed.
- **Remember the decision.** Echo entries from `context.suggestions` back in `updated_permissions`. A `localSettings` suggestion writes the rule to `.claude/settings.local.json`.
- **Clarifying questions.** An `AskUserQuestion` call holds 1–4 questions with 2–4 options each. Answer with a map from question text to the chosen option label. Include `AskUserQuestion` in any explicit `tools` list. It is not available inside subagents.
- **Slow approvals.** If a person may take longer to answer than your process can wait, have a `PreToolUse` hook return `defer`, then resume the persisted session later.

## Hooks

Programmatic hooks are async callbacks passed in `hooks`. They run in your process and use no context. They also fire inside subagents, where `agent_id` and `agent_type` identify the agent. Filesystem hooks from `settings.json` run alongside them when their setting source is loaded.

```python
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

async def protect_env(input_data, tool_use_id, context):
    if input_data["tool_input"].get("file_path", "").endswith(".env"):
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Cannot write .env files",
        }}
    return {}

options = ClaudeAgentOptions(
    hooks={"PreToolUse": [HookMatcher(matcher="Write|Edit", hooks=[protect_env])]}
)
```

- **Events in both SDKs:** `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `Stop`, `SubagentStart`, `SubagentStop`, `PreCompact`, `PermissionRequest`, `Notification`. TypeScript adds many more, including `SessionStart`, `SessionEnd`, `PostCompact`, `PermissionDenied` and `TaskCompleted`. In Python, session hooks exist only as settings-file hooks.
- **Matchers.** A matcher tests the tool name, not the arguments. MCP tools are named `mcp__<server>__<tool>`. Filter on file paths inside the callback.
- **Outputs.** Return `{}` to allow. In `hookSpecificOutput`, `PreToolUse` sets `permissionDecision` (`allow`, `deny`, `ask` or `defer`), `permissionDecisionReason` and `updatedInput`; `PostToolUse` sets `additionalContext` or `updatedToolOutput`. The top-level `systemMessage` shows a message to the user, and `continue` controls whether the agent keeps running. When hooks disagree, `deny` beats `defer`, `defer` beats `ask`, and `ask` beats `allow`.
- **Async.** Return `async` (`async_` in Python) for side effects such as logging that shouldn't block the agent.
- **Timeouts.** The default is 600 s for most events and 30 s for `UserPromptSubmit`. Set `timeout` on the matcher to change it. If a `PreToolUse` hook times out, the tool doesn't run.

The full event catalogue and JSON schema are in [[hooks]].

## MCP servers and custom tools

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "filesystem": {"command": "npx", "args": ["@modelcontextprotocol/server-filesystem", "/Users/me/projects"]},
        "remote": {"type": "http", "url": "https://mcp.example.com/mcp", "headers": {"Authorization": "Bearer <token>"}},
    },
    allowed_tools=["mcp__filesystem__*", "mcp__remote__search"],
)
```

- **Where servers come from.** `mcp_servers`, or a project `.mcp.json` loaded through the `project` source. `strict_mcp_config=True` ignores every other source, including claude.ai connectors.
- **Transports.** stdio (a command), `http` or `sse` (a URL), or an in-process SDK server.
- **Permission.** MCP tools need approval. Prefer `allowed_tools` wildcards: `acceptEdits` doesn't cover MCP tools, and `bypassPermissions` approves far more than you need.
- **Status.** The `init` message reports each server as `pending`, `connected`, `failed`, `needs-auth` or `disabled`, and `pending` alone doesn't mean failure. Poll `get_mcp_status()` / `mcpServerStatus()`, and retry with `reconnect_mcp_server()` / `reconnectMcpServer()`.
- **OAuth.** The SDK doesn't run an OAuth browser flow. Complete OAuth in your own app and pass the token in `headers`.
- **Limits.** Connections time out after 30 s (`MCP_TIMEOUT`), and tool calls have their own timeout (`MCP_TOOL_TIMEOUT`). Results over 25,000 tokens are saved to a file (raise the limit with `MAX_MCP_OUTPUT_TOKENS`). Tool search defers MCP tool schemas by default.

**Custom tools** are in-process MCP servers. Define a tool with `@tool` (Python) or `tool()` with a Zod schema (TypeScript), wrap it with `create_sdk_mcp_server` / `createSdkMcpServer`, pass it under `mcp_servers`, and allow `mcp__<server>__<tool>`. Handlers return `content` blocks, and optionally `structuredContent` and `isError: true`. Custom tools run one at a time unless you set `readOnlyHint` in their annotations, which lets Claude run them in parallel. Guidance on designing tools is in [[tool-design]].

## Subagents

Define subagents in `agents`; they override same-named files in `.claude/agents/`. Claude invokes them through the `Agent` tool. The built-in `general-purpose` agent is always available unless you set `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1`.

```python
from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "Glob", "Agent"],
    agents={
        "code-reviewer": AgentDefinition(
            description="Reviews code for quality and security. Use for code reviews.",
            prompt="You are a code reviewer. Report issues with file and line.",
            tools=["Read", "Grep", "Glob"],
            model="sonnet",
            maxTurns=20,
        )
    },
)
```

| Field | Notes |
|---|---|
| `description`, `prompt` | Required: when to use the agent, and its system prompt |
| `tools`, `disallowedTools` | The agent's tool set. Tools left out don't exist for the subagent |
| `model`, `effort` | A model alias such as `sonnet`, `opus`, `haiku` or `inherit`, or a full model ID |
| `skills`, `mcpServers`, `memory` | Skills to preload, MCP servers, memory source |
| `maxTurns`, `background`, `permissionMode` | Turn cap (output is marked partial when hit), forced background run, permission mode |

Field names stay camelCase in Python, too.

- **Context.** A subagent sees only its own prompt, the Agent tool's prompt string, project CLAUDE.md and its tools. It never sees the parent's history, and only its final message returns to the parent.
- **Background.** Subagents run in the background by default.
- **Limits.** Cap the tree with `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (default 3), `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (default 20) and `max_budget_usd`. Claude Opus 5 delegates readily, so set these limits on Opus 5 runs.
- **Detection.** A subagent call is a `tool_use` block named `Agent`, which the `init` tools list shows as `Task`. Messages from inside a subagent carry `parent_tool_use_id`. To resume a subagent, resume its session and name the `agentId` from the Agent tool result in your prompt.
- **Larger fan-out.** For runs coordinating dozens of agents, use the `Workflow` tool in the TypeScript SDK ([[workflows]]).

## Skills, commands and plugins

- **Skills.** Skills are `SKILL.md` files discovered through setting sources; there's no API for registering them in code. `skills="all"`, a list of exact names, or `[]` controls which skills Claude may invoke. Setting `skills` adds `Skill` to the allowed tools; if you also pass a `tools` list, include `"Skill"` in it.
- **Commands.** Send `/<name>` in the prompt to run any command or user-invocable skill, whatever the `skills` list says. `init.slash_commands` lists what's available. `/compact` needs earlier turns to summarize, and `/clear` resets context in a streaming session.
- **Plugins.** `plugins=[{"type": "local", "path": "./my-plugin"}]` loads a plugin's skills, agents, hooks and MCP servers from a local directory (`~` is not expanded). Invoke plugin skills as `/plugin-name:skill-name`, and check the `plugins` list in `init` to confirm each plugin loaded. See [[plugins]].

## Structured output

```python
options = ClaudeAgentOptions(
    output_format={"type": "json_schema", "schema": FeaturePlan.model_json_schema()}
)
```

The result's `structured_output` field holds validated JSON. Schemas use JSON Schema draft-07; with Zod, convert via `z.toJSONSchema(schema, { target: "draft-7" })`. The SDK re-prompts when output doesn't match. If it still can't produce valid output, the run ends with `error_max_structured_output_retries`. Treat a `success` result that has no `structured_output` as a failure too. Structured output is not streamed as deltas. For the CLI equivalent, see [[headless-mode]].

## Streaming output

Set `include_partial_messages=True` / `includePartialMessages: true` to receive `StreamEvent` messages carrying raw API events. Accumulate `content_block_delta` events: a `text_delta` carries text, and an `input_json_delta` carries tool input. Stream events come only from the main session; subagent output isn't sent as deltas. In Python, `forward_subagent_text` forwards subagents' complete text blocks instead.
