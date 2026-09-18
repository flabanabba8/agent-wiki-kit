---
title: Headless Mode (claude -p)
type: how-to
tldr: "Run Claude Code non-interactively in scripts"
sources:
  - raw/docs/official/headless.md
  - raw/docs/official/cli-reference.md
related: ["[[agent-sdk]]", "[[cli-reference]]", "[[permissions-and-modes]]", "[[ci-cd-and-code-review]]", "[[agent-sdk-control]]", "[[hooks]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [claude-p, print-mode, non-interactive-mode, bare-mode, json-output]
---

# Headless Mode (`claude -p`)

`claude -p` (or `--print`) runs Claude Code without the interactive interface. It uses the same tools, agent loop and context management, and fits scripts, build steps and CI. For typed message objects, callbacks and native structured output in Python or TypeScript, use the [[agent-sdk]]. For GitHub Actions and GitLab pipelines, see [[ci-cd-and-code-review]]. Every flag is listed in [[cli-reference]].

```bash
claude -p "What does the auth module do?"
claude -p "Find and fix the bug in auth.py" --allowedTools "Read,Edit,Bash"
```

## Basics

- **Exit status:** 0 on success and non-zero on failure. Invalid flags go to stderr before the run starts. A failure inside the run, such as missing auth, is printed as the result on stdout.
- **Stdin** is read, so piping works: `cat build-error.txt | claude -p 'concisely explain the root cause of this build error' > output.txt`. Piped input is capped at **10MB**. For larger inputs, write a file and reference it.
- **Incompatible flags:** `--bg` is rejected, and so is `--cloud` with a task description.
- **Skills and custom commands** work: put `/skill-name` in the prompt. Terminal-only built-ins such as `/login` don't. `/model`, `/effort`, `/fast`, `/color` and `/rename` take their value as an argument.
- **Session persistence:** add `--no-session-persistence` to keep a run from being saved or resumed.

## Bare mode

`--bare` skips auto-discovery of hooks, skills, custom commands, subagents, plugins, MCP servers, auto memory and CLAUDE.md. It is the recommended mode for scripted and SDK calls because the result doesn't depend on what is in a teammate's `~/.claude` or the repository. The docs say it will become the default for `-p` in a future release.

```bash
claude --bare -p "Summarize README.md" --allowedTools "Read"
```

- Bare mode never reads OAuth or the keychain. Set `ANTHROPIC_API_KEY`, or supply `apiKeyHelper` in `--settings`. Bedrock, Google Cloud's Agent Platform and Foundry read their own credentials.
- Claude gets the Bash, file read and file edit tools. Load anything else explicitly:

| To load | Flag |
|---|---|
| System prompt additions | `--append-system-prompt`, `--append-system-prompt-file` |
| Settings | `--settings <file-or-json>` |
| MCP servers | `--mcp-config <file-or-json>` |
| Custom agents | `--agents <json>` |
| A plugin | `--plugin-dir <path>`, `--plugin-url <url>` |

`--add-dir` directories still load their `.claude/skills/` in bare mode, but not their commands or agents.

> **Security note.** Without `--bare`, a `-p` run in a folder you never trusted still runs the hooks in that project's `.claude/settings.json` and connects the servers in its `.mcp.json`. There is no trust dialog and no per-server approval. Use `--bare` on untrusted checkouts. See [[hooks]] and [[permissions-and-modes]].

## Output formats

| `--output-format` | Output |
|---|---|
| `text` (default) | Plain text |
| `json` | A single object with `result`, `session_id`, usage metadata, `total_cost_usd` and a per-model cost breakdown (costs are client-side estimates) |
| `stream-json` | Newline-delimited JSON events. The last line is a `result` message |

```bash
claude -p "Summarize this project" --output-format json | jq -r '.result'
```

### Structured output

Combine `--output-format json` with `--json-schema`. The schema-shaped data is returned in `structured_output`:

```bash
claude -p "Extract the main function names from auth.py" \
  --output-format json \
  --json-schema '{"type":"object","properties":{"functions":{"type":"array","items":{"type":"string"}}},"required":["functions"]}' \
  | jq '.structured_output'
```

If the schema itself is invalid, Claude Code exits with `Error: --json-schema is not a valid JSON Schema`. The `format` keyword is accepted as an annotation but not enforced.

### Streaming

```bash
claude -p "Write a poem" --output-format stream-json --verbose --include-partial-messages | \
  jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

Useful events and fields:
- **`system/init`** comes first, after any `plugin_install` or hook events. It lists the model, tools, `mcp_servers`, `plugins`, and a `capabilities` array for feature detection. **Fail CI on a non-empty `plugin_errors` or `mcp_server_errors`.** An `--mcp-config` entry that fails validation is skipped and the run still exits cleanly. With `-p`, Claude Code waits up to `MCP_TIMEOUT` (30 seconds by default) for pending MCP servers.
- **`system/api_retry`** reports `attempt`, `max_retries`, `retry_delay_ms`, `error_status` and an `error` category such as `rate_limit`, `overloaded` or `authentication_failed`.
- **Subagent messages** carry the spawning tool call's ID in `parent_tool_use_id`, which is `null` for the main conversation. By default only their `tool_use`/`tool_result` blocks appear. Add `--forward-subagent-text` or `CLAUDE_CODE_FORWARD_SUBAGENT_TEXT` to include text and thinking at every nesting depth.
- **`system/plugin_install`** events are emitted when `CLAUDE_CODE_SYNC_PLUGIN_INSTALL` is set.
- If stdin is `stream-json`, use `--input-format stream-json`. `--replay-user-messages` echoes user messages back and needs both formats set to `stream-json`.

## Budgets and limits

| Flag | Effect |
|---|---|
| `--max-budget-usd 5.00` | Stops once API spend reaches the cap. Subagent spend counts. At the cap, spawning a subagent fails with `Budget limit reached` and running background subagents are stopped |
| `--max-turns 3` | Limits agentic turns and exits with an error at the limit. There is no limit by default |

Both apply in print mode only. For cost tracking in general, see [[costs-and-usage]].

## Permissions in automation

In `-p`, the starting permission mode is **Manual** on every plan. Nobody is there to answer prompts, so set a baseline:

```bash
claude -p "Run the test suite and fix any failures" --allowedTools "Bash,Read,Edit"
claude -p "Apply the lint fixes" --permission-mode acceptEdits
claude -p "Update the dependency pins and run the tests" --permission-mode auto --permission-prompts none
```

- `--allowedTools` uses permission rule syntax. `Bash(git diff *)` is a prefix match. The space before `*` matters, because `Bash(git diff*)` would also match `git diff-index`.
- `--permission-mode` options:
  - `auto`: a classifier reviews most actions.
  - `dontAsk`: anything that would prompt is denied, while reads, read-only commands and allowed tools still run. Good for locked-down CI.
  - `acceptEdits`: file writes and common filesystem commands are auto-approved.
- `--permission-prompts none` fits runs with no one to answer. It doesn't consult or wait on a permission host (an SDK `canUseTool` callback or `--permission-prompt-tool`), and it denies anything that would prompt unless a `PermissionRequest` hook allows it. It tells Claude not to retry, removes `AskUserQuestion`, and cancels MCP elicitations that no `Elicitation` hook answers. Denials appear as `permission_denied` messages and in the result's `permission_denials`.

Details of modes and rule syntax: [[permissions-and-modes]]. For SDK-side callbacks, see [[agent-sdk-control]].

## Multi-step conversations

```bash
claude -p "Review this codebase for performance issues"
claude -p "Now focus on the database queries" --continue

session_id=$(claude -p "Start a review" --output-format json | jq -r '.session_id')
claude -p "Continue that review" --resume "$session_id"
```

`--resume` finds a session ID in any project on the machine, and also accepts the absolute path to a `.jsonl` transcript. With `--continue`, a finished background session can be picked up, but not one that is still running. For more on sessions, see [[sessions-and-checkpoints]].

## System prompt

`--append-system-prompt` adds to the default prompt, and `--system-prompt` replaces it:

```bash
gh pr diff "$1" | claude -p \
  --append-system-prompt "You are a security engineer. Review for vulnerabilities." \
  --output-format json
```

## Process lifecycle

- **Background Bash tasks** that Claude started (dev servers, watchers) are killed about 5 seconds after the final result, once stdin has closed.
- **Background subagents and workflows** keep `-p` open until they finish, up to 10 minutes of continuous idle waiting. Change that with `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` (`0` means no ceiling). **Monitor** watches are waited on until they time out, which is 5 minutes by default.
- **SIGTERM** exits with code 143 and leaves the current turn unfinished. Claude Code kills running Bash process trees, runs `SessionEnd` hooks and exits. A later resume continues the unfinished turn. To end a turn cleanly, send SIGINT (or call the SDK's `interrupt()`) first.
- `claude -p --worktree` skips the workspace trust check and never cleans up its worktree (see [[worktrees-and-background-work]]).

## Recipes

Typo linter in `package.json`:

```json
{ "scripts": { "lint:claude": "git diff main | claude -p \"you are a typo linter. for each typo in this diff, report filename:line on one line and the issue on the next. return nothing else.\"" } }
```

Commit staged changes with narrowly scoped tools:

```bash
claude -p "Look at my staged changes and create an appropriate commit" \
  --allowedTools "Bash(git diff *),Bash(git log *),Bash(git status *),Bash(git commit *)"
```
