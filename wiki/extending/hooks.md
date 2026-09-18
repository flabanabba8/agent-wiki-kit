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
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [claude-code-hooks, pretooluse-hook, hook-events, settings-json-hooks, block-destructive-shell-command, stop-a-command-before-it-runs]
---

# Hooks

A hook is a handler Claude Code runs at a lifecycle event: a shell command, HTTP endpoint, MCP tool call, LLM prompt or agent. A rule in CLAUDE.md or a skill is a request; a `PreToolUse` hook that blocks the action is enforcement.

## Configure

A hook config has three levels: an event, a matcher group, and one or more handlers.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "if": "Bash(rm *)", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-rm.sh", "args": [] }
        ]
      }
    ]
  }
}
```

| Location | Scope |
| :-- | :-- |
| `~/.claude/settings.json` | All your projects |
| `.claude/settings.json` | One project, committable |
| `.claude/settings.local.json` | One project, not committed |
| Managed policy settings | Organization |
| Plugin `hooks/hooks.json` | While the plugin is enabled |
| Skill frontmatter | Rest of the session once the skill is invoked |
| Subagent frontmatter | While that subagent runs |

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
| `PostToolUse` | Tool call succeeded | tool name | No; stderr to Claude |
| `PostToolUseFailure` | Tool call failed | tool name | No; stderr to Claude |
| `PostToolBatch` | Parallel batch resolved, before next model call | none | Yes, stops the loop |
| `Notification` | Claude Code sends a notification | notification type | No |
| `MessageDisplay` | Assistant text streams to screen | none | No |
| `SubagentStart` | Subagent spawned or resumed | agent type | No |
| `SubagentStop` | Subagent finishes | agent type | Yes |
| `TaskCreated` | Task created with `TaskCreate` | none | Yes, rolls back |
| `TaskCompleted` | Task marked completed | none | Yes |
| `Stop` | Claude finishes responding | none | Yes, continues |
| `StopFailure` | Turn ends on an API error | error type | No; output ignored |
| `TeammateIdle` | Agent team teammate about to go idle | none | Yes |
| `InstructionsLoaded` | CLAUDE.md or `.claude/rules/*.md` loaded | load reason | No |
| `ConfigChange` | Settings, managed policy or skill file changes | config source | Yes, except `policy_settings` |
| `CwdChanged` | Working directory changes | none | No |
| `DirectoryAdded` | `/add-dir` or SDK `register_repo_root` | `slash_command`, `register_repo_root` | No |
| `FileChanged` | Watched file changes on disk | literal filenames | No |
| `WorktreeCreate` | Worktree created; replaces git behavior | none | Any non-zero exit fails |
| `WorktreeRemove` | Worktree removed | none | Non-zero fails if the directory remains |
| `PreCompact` | Before compaction | `manual`, `auto` | Yes |
| `PostCompact` | After compaction | `manual`, `auto` | No |
| `PreModelSwitch` | Before a requested model switch | canonical model name | Yes |
| `PostModelSwitch` | After the session's model changes | canonical model name | No |
| `Elicitation` | MCP server requests user input | MCP server name | Yes, denies |
| `ElicitationResult` | User answered an elicitation | MCP server name | Yes, declines |
| `SessionEnd` | Session ends | `clear`, `resume`, `logout`, `prompt_input_exit`, `other` | No |

`Notification` types: `permission_prompt` (~6s), `idle_prompt` (~60s after Claude finishes), `auth_success`, `elicitation_dialog`, `elicitation_url_dialog`, `elicitation_complete`, `elicitation_response`, `agent_needs_input`, `agent_completed`, `quota_auto_resume_fired`, `quota_auto_resume_stale`, `quota_auto_resume_disabled`. Use `PermissionRequest` for an immediate signal. `PreToolUse` doesn't fire for `@`-attached files (use a `Read` deny rule), and `FileChanged` catches writes from any process.

## Matchers and `if`

- `"*"`, `""` or no matcher matches everything. Events marked "none" ignore matchers.
- A matcher of only letters, digits, `_`, `-`, spaces, `,` and `|` is an exact name or list: `Edit|Write`, `code-reviewer`.
- Anything else is an unanchored JavaScript regex: `Edit.*` also matches `NotebookEdit`, so write `^Edit$`.
- MCP tools are `mcp__<server>__<tool>`. Match a whole server with `mcp__memory__.*`; the bare `mcp__memory` matches nothing. Plugin servers use `mcp__plugin_<plugin-name>_<server-name>__<tool>`.
- `if` holds one permission rule, such as `"Bash(git *)"` or `"Edit(*.ts)"`, and skips the handler otherwise. It works only on `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest` and `PermissionDenied`; elsewhere the hook never runs. Matching is best-effort, so enforce hard rules with permissions ([[permissions-and-modes]]).

## Handler types

Common fields: `type`, `if`, `timeout` (seconds), `statusMessage`, and `once` (skill frontmatter only).

- **`command`**: `command`, optional `args`, `async`, `asyncRewake`, `shell` (`bash` or `powershell`). With `args` it runs exec-form — no shell, each element verbatim — so prefer it for path placeholders. Without `args` it runs through `sh -c`.
- **`http`**: `url`, `headers`, `allowedEnvVars`. The input is POSTed as JSON and a 2xx JSON body is read like stdout; status codes alone can't block. `allowedHttpHookUrls` and `httpHookAllowedEnvVars` restrict URLs and header variables.
- **`mcp_tool`**: `server` (for plugin servers `plugin:<plugin-name>:<server-name>`), `tool`, `input` with `${tool_input.file_path}` substitution. Skipped on `Setup` and launch-time `SessionStart`, before servers connect.
- **`prompt`**: `prompt` (with `$ARGUMENTS` for the input JSON), `model` (a fast model by default), `continueOnBlock`. The model returns `{"ok": true}` or `{"ok": false, "reason": "..."}`; on `Stop` it may add `"impossible": true` to end the turn.
- **`agent`** (experimental): like `prompt`, but a subagent with tools such as Read, Grep and Glob gets up to 50 turns.

All five types run on `PermissionDenied`, `PermissionRequest`, `PostToolBatch`, `PostToolUse`, `PostToolUseFailure`, `PreToolUse`, `Stop`, `SubagentStop`, `TaskCompleted`, `TaskCreated`, `TeammateIdle`, `UserPromptExpansion` and `UserPromptSubmit`. `SessionStart` and `Setup` take `command` and `mcp_tool` only; every other event takes `command`, `http` and `mcp_tool`.

Default timeouts: 600 seconds for `command`, `http` and `mcp_tool`, 30 for `prompt`, 60 for `agent`; 30 on `UserPromptSubmit`, `PreModelSwitch` and `PostModelSwitch`, 10 on `MessageDisplay`. `SessionEnd` hooks share a 1.5-second budget (up to 60 via per-hook timeouts, or `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`). A timed-out `PreToolUse` hook doesn't block; a timed-out `PreModelSwitch` hook does.

`"async": true` runs a command hook in the background: it can't block, its `additionalContext` and `systemMessage` reach Claude next turn, and `-p` runs cancel it at teardown. `asyncRewake` also wakes Claude when the hook exits 2.

## Input

Every event sends JSON (stdin for commands, POST body for HTTP) with `session_id`, `prompt_id`, `transcript_path`, `cwd`, `scratchpad_dir`, `permission_mode`, `effort` and `hook_event_name`, plus event fields. Tool events add `tool_name`, `tool_input` and `tool_use_id`; `PostToolUse` adds `tool_response`. `Stop` and `SubagentStop` carry `stop_hook_active` and `last_assistant_message`. File paths are absolute, with backslashes on Windows.

## Exit codes

- **0**: success. Stdout that starts with `{` and ends with `}` is parsed as JSON. Plain stdout becomes context for Claude only on `UserPromptSubmit`, `UserPromptExpansion`, `SessionStart` and `PostModelSwitch`; elsewhere it goes to the debug log.
- **2**: blocking error on events that can block. The message is the JSON reason if given, else stderr. JSON `"allow"` can't override it.
- **Anything else**: non-blocking. The action proceeds with a `hook error` notice, unless valid JSON on stdout decides the outcome. **Exit 1 does not block**, so policy hooks must exit 2.

A mistyped script path also fails non-blocking, silently disabling the gate.

## JSON output

Exit 0 and print one JSON object. Universal fields: `continue` (`false` stops Claude), `stopReason`, `systemMessage` (a user-visible warning), and `terminalSequence` (allowlisted OSC notifications or BEL, since hooks can't write to `/dev/tty`). Output strings are capped at 10,000 characters.

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
- Phrase `additionalContext` as facts; command-like text can trip prompt-injection defenses.

## Environment variables

- `CLAUDE_PROJECT_DIR`: project root where the session started. It doesn't follow worktrees; read `cwd` from the input instead.
- `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA`: plugin install and persistent data directories.
- `CLAUDE_ENV_FILE`: `SessionStart`, `Setup`, `CwdChanged` and `FileChanged` hooks append `export` lines for later Bash commands.
- `CLAUDE_EFFORT` holds the effort level. `CLAUDE_CODE_REMOTE` is `"true"` in remote web sessions. Plugin options arrive as `CLAUDE_PLUGIN_OPTION_<KEY>`.

## Security

Command hooks run with your full user permissions. Interactive sessions hold back settings-file hooks until you accept workspace trust; `-p` and SDK sessions treat the folder as trusted, so before scripting over an unfamiliar repository, review its `.claude/` settings or pass `--settings '{"disableAllHooks": true}'` ([[sandboxing-and-security]]).

## Recipes

Notify when Claude needs you (`~/.claude/settings.json`):

```json
{ "hooks": { "Notification": [ { "matcher": "", "hooks": [ { "type": "command", "command": "notify-send 'Claude Code' 'needs your attention'" } ] } ] } }
```

Format after edits and re-inject context after compaction:

```json
{
  "hooks": {
    "PostToolUse": [ { "matcher": "Edit|Write", "hooks": [ { "type": "command", "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write" } ] } ],
    "SessionStart": [ { "matcher": "compact", "hooks": [ { "type": "command", "command": "echo 'Reminder: use Bun, not npm.'" } ] } ]
  }
}
```

- **direnv:** `direnv export bash > "$CLAUDE_ENV_FILE"` on `SessionStart` and `CwdChanged`.
- **Auto-approve plan exit:** a `PermissionRequest` hook with matcher `ExitPlanMode` printing `{"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}`.
- **Tests before stopping:** a `Stop` hook of `type: "agent"` that verifies the tests pass. `/goal` is a built-in session-scoped Stop hook.

### Stop a destructive shell command before it runs

A `Bash` handler that prints `permissionDecision: "deny"` or exits 2 cancels the command before it executes and tells Claude why; narrow it with `"if": "Bash(rm *)"`. The same shape on `Edit|Write` protects files: exit 2 when `.tool_input.file_path` contains `.env` or `.git/`. Hard guarantees need a deny rule ([[permissions-and-modes]]).

## Debug

- Test a script directly: `echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./my-hook.sh`.
- Start with `claude --debug-file /tmp/claude.log` or run `/debug`; `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose` adds matcher detail.
- JSON ignored: an unconditional `echo` in your shell profile prepends text to stdout; limit it to interactive shells.
- A `Stop` hook stuck blocking: exit early when `stop_hook_active` is true. Claude Code overrides after 8 consecutive blocks (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`).
