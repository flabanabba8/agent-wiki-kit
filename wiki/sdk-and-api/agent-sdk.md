---
title: Claude Agent SDK
type: concept
tldr: "Claude Code's agent loop as a Python/TS library"
sources:
  - raw/docs/official/agent-sdk__overview.md
  - raw/docs/official/agent-sdk__quickstart.md
  - raw/docs/official/agent-sdk__configuration.md
  - raw/docs/official/agent-sdk__agent-loop.md
  - raw/docs/official/agent-sdk__python.md
  - raw/docs/official/agent-sdk__typescript.md
  - raw/docs/official/agent-sdk__claude-code-features.md
  - raw/docs/official/agent-sdk__modifying-system-prompts.md
  - raw/docs/official/agent-sdk__streaming-vs-single-mode.md
  - raw/docs/official/agent-sdk__sessions.md
  - raw/docs/official/agent-sdk__permissions.md
  - raw/docs/official/agent-sdk__migration-guide.md
  - raw/docs/official/agent-sdk__configuration.md
  - raw/docs/official/agent-sdk__typescript.md
related: ["[[agent-sdk-control]]", "[[agent-sdk-deployment]]", "[[managed-agents]]", "[[headless-mode]]", "[[how-claude-code-works]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [agent-sdk-configuration, agent-sdk-options, claude-agent-sdk, claude-code-sdk, agent-sdk-python, agent-sdk-typescript, claude-sdk-client]
---

# Claude Agent SDK

The Agent SDK is Claude Code packaged as a library for Python and TypeScript. Your application gets the same built-in tools, agent loop and context management the CLI uses. Claude plans, calls tools, reads the results and repeats until the task is done, and your code consumes a stream of messages. Both SDKs bundle a native Claude Code binary and run it as a subprocess, so most installs need nothing else. The loop itself is described in [[how-claude-code-works]].

## When to use it

| You want to | Use | What you get |
|---|---|---|
| Embed Claude Code's agent loop in your own Python or TypeScript app, in a process you operate | Agent SDK | The Claude Code binary with its built-in tools, permissions, sessions and hooks |
| Work interactively or run one-off terminal tasks | Claude Code CLI | Built for daily interactive use |
| Call the Claude API directly from your own code | Client SDK | Direct API access from any client SDK language. Write the tool loop yourself or use the beta tool runner; see [[advanced-tool-use]] and [[context-editing-and-memory-tool]] |
| Have Anthropic host the agent | [[managed-agents]] | A hosted harness; the sandbox is Anthropic-managed or self-hosted |

The SDK exists only for Python and TypeScript. From any other language, drive the same loop by running the CLI as a subprocess with `-p` and `--output-format json` ([[headless-mode]]).

## Install and authenticate

You need Node.js 18+ or Python 3.10+.

```bash
npm install @anthropic-ai/claude-agent-sdk   # TypeScript
pip install claude-agent-sdk                 # Python, inside a virtual environment (or: uv add claude-agent-sdk)
export ANTHROPIC_API_KEY=your-api-key
```

- The SDK reads the key from the process environment. It does not load `.env` files.
- For cloud providers, set `CLAUDE_CODE_USE_BEDROCK=1`, `CLAUDE_CODE_USE_VERTEX=1`, `CLAUDE_CODE_USE_FOUNDRY=1`, or `CLAUDE_CODE_USE_ANTHROPIC_AWS=1` with `ANTHROPIC_AWS_WORKSPACE_ID`, and configure that provider's credentials ([[cloud-providers]]).
- Unless Anthropic has approved it, third-party products built on the SDK may not offer claude.ai login or subscription rate limits. Use API-key authentication.
- Two kinds of install come without a bundled binary: a Python source distribution (for example on ARM64 Windows), and a TypeScript install that skips optional dependencies (`npm ci --omit=optional`). Install Claude Code natively. Python finds it on `PATH` (or set `cli_path`); in TypeScript, set `pathToClaudeCodeExecutable`.
- The packages `claude-code-sdk` and `@anthropic-ai/claude-code` are superseded by these. In Python, `ClaudeCodeOptions` becomes `ClaudeAgentOptions`.

## A first agent

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def main():
    async for message in query(
        prompt="Review utils.py for bugs that would cause crashes. Fix any issues you find.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Glob"],  # auto-approve these
            permission_mode="acceptEdits",
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"Done: {message.subtype}")

asyncio.run(main())
```

In TypeScript the loop is `for await (const message of query({ prompt, options: { allowedTools, permissionMode } }))`, and you check `message.type` instead of using `isinstance`. Run the script with `npx tsx agent.ts` or `python agent.py`.

## The message stream

`query()` returns an async iterator. In one turn, Claude responds with tool calls, the SDK runs them and the results go back to Claude. The loop ends when Claude replies with no tool calls.

| Message | Meaning |
|---|---|
| `SystemMessage`, subtype `init` | Session metadata: tools, MCP server status, skills, `slash_commands`. Other subtypes include `compact_boundary` |
| `AssistantMessage` | One per content block (text or a tool call). Blocks from the same response share a message ID |
| `UserMessage` | Tool results sent back to Claude, plus any input you stream in mid-loop |
| `StreamEvent` | Raw API deltas. Only sent with `include_partial_messages` / `includePartialMessages` |
| `ResultMessage` | End of the loop: `result` text, `usage`, `total_cost_usd`, `num_turns`, `session_id`, `stop_reason` |

In TypeScript, assistant and user messages wrap the API message, so the content is at `message.message.content`. A few system events can arrive after the result, so iterate to the end instead of breaking out early.

Check `ResultMessage.subtype` before reading `result`, which is present only on `success`:

| Subtype | Cause |
|---|---|
| `success` | Finished normally |
| `error_max_turns` | Hit `max_turns` / `maxTurns`, which counts tool-use turns |
| `error_max_budget_usd` | Hit `max_budget_usd` / `maxBudgetUsd`. Counts the call's own spend, subagents included, not totals restored from a resumed session |
| `error_during_execution` | The loop was interrupted, including by a session crash |
| `error_max_structured_output_retries` | No output matched the schema ([[agent-sdk-control]]) |

After yielding an error result, a single-shot `query()` raises, so wrap the loop in `try`. To detect a refusal, check for `stop_reason == "refusal"`.

When Claude Code refuses to start for a known reason (for example `cwd_unavailable`, `bypass_root`, `org_pin_mismatch` or `cli_version_too_old`), the TypeScript SDK (v0.3.274+) can receive an `error_during_execution` result with zeroed totals and a `startup_failure_reason` field, so your app can offer the fix instead of retrying. Only some failures produce it by default; set `CLAUDE_CODE_STARTUP_FAILURE_RESULTS=1` in `env` to get it for every reason.

## Key options

In Python, options go in `ClaudeAgentOptions` with snake_case names. In TypeScript, they go in the `options` object (type `Options`) with camelCase names. Every field is optional. A session also reads settings files and environment variables.

| Option (Python) | Purpose |
|---|---|
| `allowed_tools` / `disallowed_tools` | Pre-approve or deny tools. Allowing a tool does not limit Claude to that set |
| `tools` | Restrict which built-in tools exist in the session |
| `permission_mode`, `can_use_tool` | How much oversight there is, and the approval callback |
| `system_prompt` | A custom string, `{"type": "preset", "preset": "claude_code", "append": "..."}`, `{"type": "custom", "prompt": "..."}` or `{"type": "file", "path": "..."}` |
| `setting_sources`, `settings` | Which filesystem settings load (`"user"`, `"project"`, `"local"`), and an extra settings file path or inline JSON string (TypeScript also takes an object) that overrides all of them; only managed policy ranks higher |
| `model`, `fallback_model`, `effort`, `thinking` | Model and reasoning depth. `effort` runs from `low` to `max` ([[models-and-effort]]) |
| `max_turns`, `max_budget_usd`, `task_budget` | Stop conditions ([[agent-sdk-deployment]]) |
| `cwd`, `add_dirs`, `env` | Working directory, extra directories, subprocess environment |
| `mcp_servers`, `agents`, `skills`, `plugins`, `hooks` | Extensions ([[agent-sdk-control]]) |
| `resume`, `continue_conversation`, `fork_session`, `session_store` | Sessions |
| `output_format`, `include_partial_messages` | Structured output and streaming |

- **Model.** Without `model` (or a model from settings or the environment), a session uses Claude Code's default model ([[models-and-effort]]). `model` takes an alias or full name. `fallback_model` takes one model or a comma-separated chain, used when the primary is overloaded or unavailable. The primary is retried at the start of each user turn. In TypeScript, a fallback equal to `model` throws at startup.
- **No sampling parameters.** `temperature`, `top_p` and `max_tokens` have no options. Use `effort` or a spend cap, or call the Messages API directly.
- **`env`.** Python merges your values over the inherited environment. TypeScript replaces the environment, so spread `process.env` into it. Unset, the subprocess inherits your environment in both.
- **`cwd`.** Defaults to your process's working directory and has no setter; start another session to change it. It decides which project settings, hooks and skills load and which project a stored session belongs to. `add_dirs` / `additionalDirectories` grants file access outside it, not configuration.
- **Caps.** `max_turns=0` means no limit. `max_budget_usd=0` is rejected at startup. With streaming input, the session survives a cap result: the turn count restarts for each queued message, while the budget keeps accumulating until `/clear`.

### Two defaults that surprise people

- **System prompt.** If you don't set `system_prompt`, the SDK uses a minimal prompt that covers tool calling only, not Claude Code's prompt, whereas `claude -p` uses the full Claude Code prompt. For CLI-like behavior, use the `claude_code` preset, optionally with `append`. For an agent with a different identity, surface or permission model, write your own prompt and add back the tool and safety guidance it needs.
- **The system prompt is recorded per session.** Claude Code records the prompt on a session's first request and reuses it until the session is compacted, so a different `append` or custom prompt passed on `resume` or `continue` takes effect only after compaction or in a new session. To change instructions mid-session, put them in the next user message or return `additionalContext` from a `UserPromptSubmit` or `PostToolUse` hook. While iterating on wording, set `snapshot: false` on the preset or custom object form to rebuild the prompt every request (TypeScript SDK v0.3.257+, Python v0.2.153+); keep recording on in production, because turning it off breaks prompt-cache reuse.
- **Filesystem settings.** If you omit `setting_sources`, the SDK loads user, project and local settings, CLAUDE.md files, rules, skills, agents and commands, just as the CLI does. Pass `[]` for isolation. Managed policy, `~/.claude.json` and auto memory load either way ([[agent-sdk-deployment]] covers multi-tenant isolation).

## query() or ClaudeSDKClient

| | `query()` | `ClaudeSDKClient` (Python) |
|---|---|---|
| Session | New session per call | One session across calls |
| Interrupts | No | Yes, with `interrupt()` |
| Continuing a chat | Through `continue_conversation` or `resume` | Automatic |
| Good for | One-off tasks, CI | Chat UIs, flows that branch on Claude's reply |

The client also has `set_permission_mode()`, `set_model()`, `rewind_files()`, `get_mcp_status()` and `reconnect_mcp_server()`. TypeScript has no client object. Instead, pass `continue: true` or `resume` on later `query()` calls, and call methods such as `setPermissionMode()` on the object `query()` returns.

Mid-session setters need streaming input. `set_model()` with no argument switches to Claude Code's default model, not the `model` you passed; each model has its own prompt cache, so the next request after a switch is uncached. TypeScript adds `applyFlagSettings()`, which applies settings-file keys at runtime, and `updateSettings()`, which writes one allowlisted key to disk: `outputStyle` to `"localSettings"` (takes effect on the next request) or `effortLevel` to `"userSettings"` (saved as the default for the current model; the running session keeps its effort, and `max` is not written).

Streaming input means passing an async generator of user messages as `prompt`. It is the recommended mode for interactive apps, because it supports image attachments, queued messages, interrupts and approvals mid-session.

## Keeping context and cost down

Context builds up across turns: the system prompt, tool definitions, history and tool output. Stable prefixes are prompt-cached. Near the limit, the SDK compacts automatically and emits `compact_boundary`. Compaction can drop early instructions, so put rules that must last in CLAUDE.md rather than in the first prompt. Send noisy subtasks to subagents, limit tools to what the task needs, keep MCP tool search on, and use a lower `effort` for simple agents. [[context-window]] explains how Claude Code manages context.

## Branding and terms

Products may use "Claude Agent" or "{YourAgentName} Powered by Claude". They may not use "Claude Code" or "Claude Code Agent", or copy Claude Code's look. Use of the SDK is governed by Anthropic's Commercial Terms of Service.
