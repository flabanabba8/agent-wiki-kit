---
title: Hooks
type: reference
tldr: "Hook events, exit codes, blocking a command"
sources:
  - raw/docs/official/hooks.md
  - raw/docs/official/hooks-guide.md
  - raw/docs/official/features-overview.md
  - raw/docs/official/sub-agents.md
  - raw/docs/changelog-2.1.275-to-2.1.282.md
related: ["[[settings]]", "[[permissions-and-modes]]", "[[subagents]]", "[[skills]]", "[[plugins]]", "[[mcp]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [claude-code-hooks, pretooluse-hook, hook-events, settings-json-hooks, block-destructive-shell-command, stop-a-command-before-it-runs]
---

# Hooks

A hook is a handler (shell command, HTTP endpoint, MCP tool call, LLM prompt or agent) run at a lifecycle event. A blocking `PreToolUse` hook enforces what a CLAUDE.md rule only requests.

## Configure

A hook config has three levels: an event, a matcher group, and one or more handlers.

```json
{ "hooks": { "PreToolUse": [ { "matcher": "Bash", "hooks": [
  { "type": "command", "if": "Bash(rm *)", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-rm.sh", "args": [] }
] } ] } }
```

| Location | Scope |
| :-- | :-- |
| `~/.claude/settings.json` | All your projects |
| `.claude/settings.json` | One project, committable |
| `.claude/settings.local.json` | One project, not committed |
| Managed policy settings | Organization |
| Plugin `hooks/hooks.json` | While the plugin is enabled |
| Skill frontmatter | Rest of session after invocation |
| Subagent frontmatter | While that subagent runs |

- Hooks merge across sources and matching handlers run in parallel.
- Settings, managed and plugin hooks also fire inside subagents (input carries `agent_id`, `agent_type`).
- `/hooks` lists configured hooks read-only and says where each is defined.
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

- `"*"`, `""` or no matcher matches everything; events marked "none" ignore matchers.
- Letters, digits, `_`, `-`, spaces, `,` and `|` only: an exact name or list (`Edit|Write`). Anything else is an unanchored JavaScript regex (write `^Edit$`).
- MCP tools are `mcp__<server>__<tool>`. Match a whole server with `mcp__memory__.*`; the bare `mcp__memory` matches nothing. Plugin servers use `mcp__plugin_<plugin-name>_<server-name>__<tool>`.
- `if` holds one permission rule, such as `"Bash(git *)"`, and skips the handler otherwise. It works only on `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest` and `PermissionDenied`; elsewhere the hook never runs. Matching is best-effort, so enforce hard rules with permissions ([[permissions-and-modes]]).

## Handler types

Common fields: `type`, `if`, `timeout` (seconds), `statusMessage`, and `once` (skill frontmatter only).

- **`command`**: `command`, optional `args`, `async`, `asyncRewake`, `shell` (`bash` or `powershell`). With `args` it runs exec-form — no shell, each element verbatim — so prefer it for path placeholders; without `args` it runs through `sh -c`.
- **`http`**: `url`, `headers`, `allowedEnvVars`. The input is POSTed as JSON and a 2xx JSON body is read like stdout; status codes alone can't block. `allowedHttpHookUrls` and `httpHookAllowedEnvVars` restrict URLs and header variables.
- **`mcp_tool`**: `server` (for plugin servers `plugin:<plugin-name>:<server-name>`), `tool`, `input` with `${tool_input.file_path}` substitution. Skipped on `Setup` and launch-time `SessionStart`; on blocking events such as `PreToolUse` it waits for a still-connecting server, up to the MCP connect timeout.
- **`prompt`**: `prompt` (with `$ARGUMENTS` for the input JSON), `model` (a fast model by default), `continueOnBlock`. The model returns `{"ok": true}` or `{"ok": false, "reason": "..."}`; on `Stop` it may add `"impossible": true` to end the turn.
- **`agent`** (experimental): like `prompt`, but a subagent with Read, Grep and Glob gets up to 50 turns.

All five types run on `PermissionDenied`, `PostToolBatch`, `PostToolUse`, `PostToolUseFailure`, `PreToolUse`, `Stop`, `SubagentStop`, `TaskCompleted`, `TaskCreated`, `TeammateIdle`, `UserPromptExpansion` and `UserPromptSubmit`. `PermissionRequest` takes every type but `agent`, which is skipped there. `SessionStart` and `Setup` take `command` and `mcp_tool` only; every other event takes `command`, `http` and `mcp_tool`.

Default timeouts: 600 s for `command`, `http`, `mcp_tool`; 30 for `prompt`; 60 for `agent`; 30 on `UserPromptSubmit` and the model-switch events; 10 on `MessageDisplay`. `SessionEnd` hooks share a 1.5-second budget (up to 60 via per-hook timeouts, or `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`, which also sets each untimed hook's timeout). A timed-out `PreToolUse` hook doesn't block; a timed-out `PreModelSwitch` hook does.

`"async": true` runs a command hook in the background: it can't block, its context reaches Claude next turn, and `-p` teardown cancels it. `asyncRewake` also wakes Claude when the hook exits 2.

## Input

Every event sends JSON (stdin for commands, POST body for HTTP) with `session_id`, `prompt_id`, `transcript_path`, `cwd`, `scratchpad_dir`, `permission_mode`, `effort` and `hook_event_name`, plus event fields. Tool events add `tool_name`, `tool_input` and `tool_use_id`; `PostToolUse` adds `tool_response`. `Stop` and `SubagentStop` carry `stop_hook_active` and `last_assistant_message`. File paths are absolute, with backslashes on Windows.

- MCP tool events add `mcp_server` (`name`, `source`); base trust on `source`, not the name.
- A Bash `PostToolUse` can carry `tool_response.bashEditDiff` (`changedFiles` and diffs; see `bashEditDiffEnabled` on [[settings]]), a best-effort beta unfit for policy.
- A subagent using `SubagentHandback` (auto mode) delivers its report as that tool's `tool_input.message`, not in `last_assistant_message` or the Agent result's `content`.
- `SubagentStop` also fires for internal agents such as `/btw`, often with an empty `agent_type` that only catch-all matchers match.

## Exit codes

- **0**: success. Stdout that starts with `{` and ends with `}` is parsed as JSON. Plain stdout becomes context only on `UserPromptSubmit`, `UserPromptExpansion`, `SessionStart` and `PostModelSwitch`; elsewhere it goes to the debug log.
- **2**: blocking error on events that can block. The message is the JSON reason if given, else stderr. JSON `"allow"` can't override it.
- **Anything else**: non-blocking. The action proceeds with a `hook error` notice, unless valid JSON on stdout decides the outcome. **Exit 1 does not block**, so policy hooks must exit 2.

A mistyped script path fails non-blocking, silently disabling the gate.

## JSON output

Exit 0 and print one JSON object. Universal fields: `continue` (`false` stops Claude), `stopReason`, `systemMessage` (a user-visible warning), and `terminalSequence` (allowlisted OSC notifications or BEL, since hooks can't write to `/dev/tty`). Each output string is capped at 10,000 characters; longer text is saved to a file and Claude gets the path plus a 2,000-character preview, with no setting to raise the cap.

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
- For `PreToolUse`, the most restrictive answer wins: `deny` > `defer` > `ask` > `allow`. `allow` never overrides deny or ask rules, while `deny` blocks even in `bypassPermissions` mode. `updatedInput` replaces the whole input. `defer` works only in `-p` runs, pausing with `stop_reason: "tool_deferred"` for the caller to resume.
- `PostToolUse` can replace what Claude sees with `updatedToolOutput`, but the tool already ran.
- Phrase `additionalContext` as facts, not commands (prompt-injection defenses).

## Environment variables

- `CLAUDE_PROJECT_DIR`: project root where the session started (it doesn't follow worktrees; read `cwd`).
- `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA`: plugin install and persistent data directories.
- `CLAUDE_ENV_FILE`: `SessionStart`, `Setup`, `CwdChanged` and `FileChanged` hooks append `export` lines for later Bash commands.
- `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` give a plugin's install and data directories, `CLAUDE_EFFORT` the effort level, `CLAUDE_CODE_REMOTE` `"true"` in cloud sessions, and `CLAUDE_PLUGIN_OPTION_<KEY>` each plugin option.

## Security

Command hooks run with your full user permissions. Interactive sessions wait for workspace trust before running settings-file hooks; `-p` and SDK sessions don't, so in unfamiliar repositories pass `--settings '{"disableAllHooks": true}'` ([[sandboxing-and-security]]).

## Recipes

Format after edits and re-inject context after compaction:

```json
{
  "hooks": {
    "PostToolUse": [ { "matcher": "Edit|Write", "hooks": [ { "type": "command", "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write" } ] } ],
    "SessionStart": [ { "matcher": "compact", "hooks": [ { "type": "command", "command": "echo 'Reminder: use Bun, not npm.'" } ] } ]
  }
}
```

- **direnv:** `direnv export bash > "$CLAUDE_ENV_FILE"` on `SessionStart`/`CwdChanged`.
- **Auto-approve plan exit:** a `PermissionRequest` hook with matcher `ExitPlanMode` printing `{"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}`.

### Stop a destructive shell command before it runs

A `Bash` handler that prints `permissionDecision: "deny"` or exits 2 cancels the command and tells Claude why; narrow it with `"if": "Bash(rm *)"`. On `Edit|Write`, exit 2 when `.tool_input.file_path` contains `.env` to protect files. Hard guarantees need a deny rule ([[permissions-and-modes]]).

## Debug

- Test a script by piping sample JSON into it.
- Start with `claude --debug-file /tmp/claude.log` or run `/debug`; `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose` adds matcher detail.
- JSON ignored: a shell-profile `echo` prepends text to stdout.
- A `Stop` hook stuck blocking: exit early when `stop_hook_active` is true. Claude Code overrides after 8 consecutive blocks (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`).
