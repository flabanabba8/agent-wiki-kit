---
title: Hooks
type: reference
tldr: "Hook events, exit codes, blocking a command"
sources:
  - raw/docs/official/hooks.md
  - raw/docs/official/hooks-guide.md
  - raw/docs/official/features-overview.md
  - raw/docs/official/sub-agents.md
related: ["[[settings]]", "[[permissions-and-modes]]", "[[subagents]]", "[[skills]]", "[[plugins]]", "[[mcp]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [claude-code-hooks, pretooluse-hook, hook-events, settings-json-hooks, block-destructive-shell-command, stop-a-command-before-it-runs]
---

# Hooks

A hook is a handler Claude Code runs at a lifecycle event: a shell command, HTTP endpoint, MCP tool call, LLM prompt or agent. A rule in CLAUDE.md or a skill is a request; a `PreToolUse` hook that blocks the action is enforcement.

## Configure

A hook config has three levels: an event, a matcher group, and one or more handlers.

```json
{ "hooks": { "PreToolUse": [ { "matcher": "Bash", "hooks": [
  { "type": "command", "if": "Bash(rm *)", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-rm.sh", "args": [] }
] } ] } }
```

Hooks come from `~/.claude/settings.json` (all your projects), `.claude/settings.json` (one project, committable), `.claude/settings.local.json` (uncommitted), managed policy settings (organization-wide), a plugin's `hooks/hooks.json` (while it is enabled), skill frontmatter (the rest of the session once the skill is invoked) and subagent frontmatter (while that subagent runs).

- Hooks merge across sources and matching handlers run in parallel.
- Settings, managed and plugin hooks also fire inside subagents, with `agent_id` and `agent_type` in the input.
- `/hooks` lists configured hooks and their sources, read-only.
- `"disableAllHooks": true` turns hooks off, but only managed settings can disable managed hooks; managed `allowManagedHooksOnly` blocks user, project, local and plugin hooks. Precedence: [[settings]].

## Hook events

"Blocks" is what exit code 2 does.

| Event | Fires | Matcher filters | Blocks |
| :-- | :-- | :-- | :-- |
| `SessionStart` | Session begins or resumes | `startup`, `resume`, `clear`, `compact`, `fork` | No |
| `Setup` | `--init-only`, or `-p` with `--init` or `--maintenance` | `init`, `maintenance` | No |
| `UserPromptSubmit` | Prompt submitted, before Claude sees it | none | Yes, erases the prompt |
| `UserPromptExpansion` | A typed command expands into a prompt | command name | Yes |
| `PreToolUse` | Before a tool call runs | tool name | Yes |
| `PermissionRequest` | Tool call needs a permission decision | tool name | No; use `decision` |
| `PermissionDenied` | Auto mode denies a tool call | tool name | No; JSON `retry` |
| `PostToolUse`, `PostToolUseFailure` | Tool call succeeded, or failed | tool name | No; stderr to Claude |
| `PostToolBatch` | Parallel batch resolved, before next model call | none | Yes, stops the loop |
| `Notification` | Claude Code sends a notification | notification type | No |
| `MessageDisplay` | Assistant text streams to screen | none | No |
| `SubagentStart` | Subagent spawned or resumed | agent type | No |
| `SubagentStop` | Subagent finishes | agent type | Yes |
| `TaskCreated`, `TaskCompleted` | `TaskCreate` ran, or a task is marked done | none | Yes; TaskCreated rolls back |
| `Stop` | Claude finishes responding | none | Yes, continues |
| `StopFailure` | Turn ends on an API error | error type | No; output ignored |
| `TeammateIdle` | Agent team teammate about to go idle | none | Yes |
| `InstructionsLoaded` | CLAUDE.md or `.claude/rules/*.md` loaded | load reason | No |
| `ConfigChange` | Settings, managed policy or skill file changes | config source | Yes, except `policy_settings` |
| `CwdChanged` | Working directory changes | none | No |
| `DirectoryAdded` | `/add-dir` or SDK `register_repo_root` | `slash_command`, `register_repo_root` | No |
| `FileChanged` | Watched file changes on disk | literal filenames | No |
| `WorktreeCreate`, `WorktreeRemove` | Worktree created, replacing git, or removed | none | Non-zero exit fails |
| `PreCompact`, `PostCompact` | Before, after compaction | `manual`, `auto` | Only `PreCompact` |
| `PreModelSwitch`, `PostModelSwitch` | Before a requested switch, after the model changes | canonical model name | Only `PreModelSwitch` |
| `Elicitation`, `ElicitationResult` | MCP server requests input, user answered | MCP server name | Yes, denies or declines |
| `SessionEnd` | Session ends | `clear`, `resume`, `logout`, `prompt_input_exit`, `other` | No |

`Notification` types include `permission_prompt` (~6s), `idle_prompt` (~60s after Claude finishes), `auth_success`, four `elicitation_*` types, `agent_needs_input`, `agent_completed` and three `quota_auto_resume_*` types. Use `PermissionRequest` for an immediate signal. `PreToolUse` doesn't fire for `@`-attached files (use a `Read` deny rule), and `FileChanged` catches writes from any process.

`SessionStart` hooks run in the background at launch, `--continue`, `--resume` and `/clear`, so you can type right away while Claude's first response waits for them; switching conversations with `/resume` inside a session waits instead. `InstructionsLoaded` doesn't fire when `AGENTS.md` is read directly as project instructions, only when a `CLAUDE.md` imports it (`load_reason` `include`) or symlinks to it.

## Matchers and `if`

- `"*"`, `""` or no matcher matches everything. Events marked "none" ignore matchers.
- A matcher of only letters, digits, `_`, `-`, spaces, `,` and `|` is an exact name or list: `Edit|Write`, `code-reviewer`.
- Anything else is an unanchored JavaScript regex: `Edit.*` also matches `NotebookEdit`, so write `^Edit$`.
- MCP tools are `mcp__<server>__<tool>`. Match a whole server with `mcp__memory__.*`; the bare `mcp__memory` matches nothing.
- `if` holds one permission rule, such as `"Bash(git *)"`, and skips the handler otherwise. It works only on `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest` and `PermissionDenied`; elsewhere the hook never runs. Matching is best-effort, so enforce hard rules with permissions ([[permissions-and-modes]]).

## Handler types

Common fields: `type`, `if`, `timeout` (seconds), `statusMessage`, and `once` (skill frontmatter only).

- **`command`**: `command`, optional `args`, `async`, `asyncRewake`, `shell` (`bash` or `powershell`). With `args` it runs exec-form — no shell, each element verbatim — so prefer it for path placeholders; without `args` it runs through `sh -c`.
- **`http`**: `url`, `headers`, `allowedEnvVars`. The input is POSTed as JSON and a 2xx JSON body is read like stdout; status codes alone can't block. `allowedHttpHookUrls` and `httpHookAllowedEnvVars` restrict URLs and header variables.
- **`mcp_tool`**: `server` (plugin servers as `plugin:<plugin-name>:<server-name>`), `tool`, `input` with `${tool_input.file_path}` substitution. Skipped on `Setup` and launch-time `SessionStart`.
- **`prompt`**: `prompt` (with `$ARGUMENTS` for the input JSON), `model` (fast by default), `continueOnBlock`. The model returns `{"ok": true}` or `{"ok": false, "reason": "..."}`; on `Stop` it may add `"impossible": true` to end the turn.
- **`agent`** (experimental): like `prompt`, but a subagent with read-only tools gets up to 50 turns.

All five types run on the tool, permission, task, `Stop`, `SubagentStop`, `PostToolBatch`, `TeammateIdle`, `UserPromptSubmit` and `UserPromptExpansion` events. `SessionStart` and `Setup` take `command` and `mcp_tool` only; every other event takes `command`, `http` and `mcp_tool`.

Default timeouts: 600 seconds for `command`, `http` and `mcp_tool`, 30 for `prompt`, 60 for `agent`; 30 on `UserPromptSubmit`, `PreModelSwitch` and `PostModelSwitch`, 10 on `MessageDisplay`. `SessionEnd` hooks share a 1.5-second budget, raised to the highest per-hook `timeout` in your settings files, up to 60 seconds — a hook without its own `timeout` still keeps 1.5 seconds, and plugin timeouts don't raise the budget. `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` overrides the budget and becomes the per-hook default too. A timed-out `PreToolUse` hook doesn't block; a timed-out `PreModelSwitch` hook does.

`"async": true` runs a command hook in the background: it can't block, its `additionalContext` and `systemMessage` reach Claude next turn, and `-p` runs cancel it at teardown. `asyncRewake` also wakes Claude when the hook exits 2.

## Input

Every event sends JSON (stdin for commands, POST body for HTTP) with `session_id`, `prompt_id`, `transcript_path`, `cwd`, `scratchpad_dir`, `permission_mode`, `effort` and `hook_event_name`, plus event fields. Tool events add `tool_name`, `tool_input` and `tool_use_id`; `PostToolUse` adds `tool_response`. `Stop` and `SubagentStop` carry `stop_hook_active` and `last_assistant_message`. File paths are absolute, with backslashes on Windows.

- MCP tool events also carry `mcp_server`, with the server's `name` and a `source` such as `plugin`, `sdk` or a settings scope. Base trust decisions on `source`, not on the name or the `mcp__<server>__` prefix.
- A Bash command that changes files in a git repository can deliver `tool_response.bashEditDiff` to `PostToolUse`: `changedFiles` (up to 200 paths), `files` (diffs of up to 5) and flags saying how complete the list is. Recording happens in auto and `bypassPermissions` modes, or in every mode when `bashEditDiffEnabled` is `true`. Being best-effort and in public beta, it tells you what to review rather than enforcing a policy.

## Exit codes

- **0**: success. Stdout that starts with `{` and ends with `}` is parsed as JSON. Plain stdout becomes context only on `UserPromptSubmit`, `UserPromptExpansion`, `SessionStart` and `PostModelSwitch`; elsewhere it goes to the debug log.
- **2**: blocking error on events that can block. The message is the JSON reason if given, else stderr. JSON `"allow"` can't override it.
- **Anything else**: non-blocking. The action proceeds with a `hook error` notice, unless valid JSON on stdout decides the outcome. **Exit 1 does not block**, so policy hooks must exit 2, and a mistyped script path silently disables the gate.

## JSON output

Exit 0 and print one JSON object. Universal fields: `continue` (`false` stops Claude), `stopReason`, `systemMessage` (a user-visible warning), and `terminalSequence` (allowlisted OSC notifications or BEL, since hooks can't write to `/dev/tty`).

`additionalContext`, `systemMessage`, `initialUserMessage` and plain stdout are each capped at 10,000 characters, measured per field. Longer output is saved in the session directory and replaced by the file path plus a preview of the first 2,000 characters, which Claude is not told to read, so keep anything it must always see inside the cap. No setting raises this cap.

| Events | Decision fields |
| :-- | :-- |
| `UserPromptSubmit`, `UserPromptExpansion`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Stop`, `SubagentStop`, `ConfigChange`, `PreCompact` | Top-level `decision: "block"` and `reason` |
| `PreToolUse` | `hookSpecificOutput.permissionDecision`: `allow`, `deny`, `ask`, `defer`; plus `permissionDecisionReason`, `updatedInput`, `additionalContext` |
| `PreModelSwitch` | `permissionDecision`: `allow`, `deny`, `ask` |
| `PermissionRequest` | `hookSpecificOutput.decision`: `behavior`, `updatedInput`, `updatedPermissions`, `message`, `interrupt` |
| `PermissionDenied` | `hookSpecificOutput.retry: true` |
| `TeammateIdle`, `TaskCompleted`, `TaskCreated` | Exit 2, `continue: false`, or (TaskCreated) `decision: "block"` |
| `WorktreeCreate` | Path as the last stdout line, or HTTP `worktreePath` |
| `Elicitation`, `ElicitationResult` | `action` and `content` |
| `MessageDisplay` | `displayContent`, display only |
| `SessionStart`, `SubagentStart`, `PostModelSwitch` | `additionalContext`; SessionStart also `initialUserMessage`, `sessionTitle`, `watchPaths`, `reloadSkills` |

- Nest `permissionDecision` and `additionalContext` inside `hookSpecificOutput` with `hookEventName`; top-level copies are silently ignored.
- For `PreToolUse`, the most restrictive answer wins: `deny` > `defer` > `ask` > `allow`. `allow` never overrides deny or ask rules, while `deny` blocks even in `bypassPermissions` mode. `updatedInput` replaces the whole input, and `defer` works only in `-p` runs, pausing with `stop_reason: "tool_deferred"`.
- `PostToolUse` can replace what Claude sees with `updatedToolOutput`, but the tool already ran. Phrase `additionalContext` as facts; command-like text can trip prompt-injection defenses.

## Environment variables

- `CLAUDE_PROJECT_DIR`: project root where the session started. It doesn't follow worktrees; read `cwd` from the input instead.
- `CLAUDE_ENV_FILE`: `SessionStart`, `Setup`, `CwdChanged` and `FileChanged` hooks append `export` lines for later Bash commands.
- `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` give a plugin's install and data directories, `CLAUDE_EFFORT` the effort level, `CLAUDE_CODE_REMOTE` `"true"` in cloud sessions, and `CLAUDE_PLUGIN_OPTION_<KEY>` each plugin option.

## Security

Command hooks run with your full user permissions. Interactive sessions hold back settings-file hooks until you accept workspace trust, but `-p` and SDK sessions treat the folder as trusted, so over an unfamiliar repository review its `.claude/` settings or pass `--settings '{"disableAllHooks": true}'` ([[sandboxing-and-security]]).

## Recipes

- **Format after edits:** a `PostToolUse` hook on `Edit|Write` piping `.tool_input.file_path` into your formatter.
- **Re-inject context after compaction:** a `SessionStart` hook with matcher `compact` that echoes the rule Claude keeps forgetting.
- **direnv:** `direnv export bash > "$CLAUDE_ENV_FILE"` on `SessionStart` and `CwdChanged`.
- **Tests before stopping:** a `Stop` hook of `type: "agent"` that verifies the tests pass. `/goal` is a built-in session-scoped Stop hook.

### Stop a destructive shell command before it runs

A `Bash` handler that prints `permissionDecision: "deny"` or exits 2 cancels the command before it executes and tells Claude why; narrow it with `"if": "Bash(rm *)"`. The same shape on `Edit|Write` protects files. Hard guarantees need a deny rule ([[permissions-and-modes]]).

## Debug

- Test a script directly: `echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./my-hook.sh`.
- Start with `claude --debug-file /tmp/claude.log` or run `/debug`; `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose` adds matcher detail.
- JSON ignored: an unconditional `echo` in your shell profile prepends text to stdout.
- A `Stop` hook stuck blocking: exit early when `stop_hook_active` is true. Claude Code overrides after 8 consecutive blocks (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`).
