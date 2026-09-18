---
title: CLI Reference
type: reference
tldr: "Every claude subcommand and launch flag"
sources:
  - raw/docs/official/cli-reference.md
  - raw/docs/official/env-vars.md
related: ["[[headless-mode]]", "[[slash-commands]]", "[[environment-variables]]", "[[permissions-and-modes]]", "[[worktrees-and-background-work]]", "[[settings]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [claude-flags, claude-command-line, cli-options, claude-subcommands]
---

# CLI Reference

`claude` starts sessions, runs one-shot prompts, and manages installs, authentication, MCP servers, plugins and background sessions. In-session `/` commands are on [[slash-commands]]; scripting patterns (output formats, budgets, unattended permissions) on [[headless-mode]].

`claude --help` doesn't list every flag, so one missing from `--help` can still work. A mistyped subcommand prints the closest match (`claude udpate` → `Did you mean claude update?`) and exits.

## Starting a session

| Invocation | What it does |
|---|---|
| `claude`, `claude "query"` | Interactive session, optionally with an initial prompt |
| `claude -p "query"` | Run the prompt non-interactively, print the result, exit |
| `cat file \| claude -p "query"` | Process piped content |
| `claude -c`, `claude -c -p "query"` | Continue the most recent conversation in this directory, interactively or not |
| `claude -r "<session>" "query"` | Resume a session by ID or name |

## Subcommands

### Install, update, authentication, diagnostics

| Command | Purpose |
|---|---|
| `claude update`, `claude install [version]` | Update to the latest version; install or reinstall the native binary at a version such as `2.1.118`, `stable` or `latest` |
| `claude auth login`, `claude setup-token` | Sign in: `--email` pre-fills the address, `--sso` forces SSO, `--console` bills API usage to Anthropic Console instead of a subscription. Or print a long-lived OAuth token for CI and scripts, not saved, requiring a Claude subscription |
| `claude auth logout`, `claude auth status` | Log out; auth status as JSON (`--text` for human-readable), exit 0 when logged in, 1 when not |
| `claude doctor` | Read-only install and settings diagnostics (install health, settings validation errors, Remote Control eligibility) without starting a session |

### Background sessions

| Command | Purpose |
|---|---|
| `claude agents` | Agent view. `--cwd <path>` filters by directory; `--json` lists active sessions, `--json --all` adds completed. `--permission-mode`, `--model`, `--effort` and `--agent` set defaults for dispatched sessions; `--settings`, `--add-dir`, `--plugin-dir` and `--mcp-config` work as on `claude` |
| `claude attach <id>`, `claude logs <id>`, `claude respawn <id>` | Attach to a background session in this terminal; print its recent output; restart a running or stopped session with its conversation intact, where `--all` restarts every running session, for example after an update |
| `claude stop <id>`, `claude rm <id>` | Stop a background session, also accepted as `claude kill`; remove a session from the list, keeping its transcript on disk. When a worktree blocks removal, the refusal prints the flag to pass: `--discard-unpushed <commit>@<worktree-id>` or `--force-remove-worktree <worktree-id>` |
| `claude daemon status`, `claude daemon stop --any` | Supervisor state, version, socket directory and worker count, exiting 1 when the supervisor isn't running; stop the supervisor and its sessions, where `--keep-workers` leaves sessions running for the next supervisor |

A leading `--dangerously-skip-permissions` or `--allow-dangerously-skip-permissions` still routes `claude ... daemon <subcommand>` to the daemon subcommand; any other leading flag turns `daemon <subcommand>` into a prompt for a new session. See [[worktrees-and-background-work]].

### MCP, plugins, import

| Command | Purpose |
|---|---|
| `claude mcp` | Configure MCP servers (see [[mcp]]) |
| `claude mcp login <name>`, `claude mcp logout <name>` | Run a configured server's OAuth flow from the shell (HTTP, SSE, claude.ai connectors; `--no-browser` prints the URL over SSH); clear a server's stored OAuth credentials |
| `claude plugin` | Manage plugins; alias `claude plugins`. See [[plugins]] |
| `claude import [source]` | Start a session running `/import` to bring configuration from other coding agents; `--dry-run`, `--yes`. Unavailable on Amazon Bedrock, Google Cloud's Agent Platform, Microsoft Foundry, Claude Platform on AWS, and with feature-flag fetching off |

### Admin, cloud, review, cleanup

| Command | Purpose |
|---|---|
| `claude auto-mode defaults`, `claude auto-mode reset` | Print the built-in auto mode classifier rules as JSON, where `--label <prefix>` filters and `claude auto-mode config` prints your effective config; remove the `autoMode` section from user settings, where `-y`/`--yes` skips confirmation and managed and `--settings` rules still apply |
| `claude gateway`, `claude self-hosted-runner` | Run the self-hosted Claude apps gateway (SSO and policy in front of Bedrock, Agent Platform or Foundry), which requires `--config gateway.yaml`; register this machine as a runner for a self-hosted cloud environment, with subcommands `setup`, `doctor`, `orchestrator` |
| `claude remote-control` | Start a Remote Control server with no local interactive session, e.g. `--name "My Project"` |
| `claude ultrareview [target]` | Run ultrareview non-interactively. `--json` for raw output, `--timeout <minutes>` (default 45), `--post` posts findings to a github.com PR (`--no-post` is the default). Exit 0 on success, 1 otherwise |
| `claude project purge [path]` | Delete local state for a project: transcripts, task lists, debug logs, file-edit history, prompt history lines and its `~/.claude.json` entry. `--dry-run`, `-y`/`--yes`, `-i`/`--interactive`, `--all` |

## Flags

### Sessions and resuming

| Flag | Effect |
|---|---|
| `--continue`, `-c` | Load the most recent conversation in this directory, including finished background sessions. Skips `-p`, SDK and `/loop` sessions unless combined with `-p` |
| `--resume`, `-r` | Resume by ID, name, or absolute `.jsonl` transcript path; with no value, open the picker. ID lookup searches this project and its worktrees, then every project on the machine |
| `--fork-session`, `--from-pr` | With `--resume` or `--continue`, create a new session ID; or open a picker filtered to sessions linked to a PR — number, GitHub/GitHub Enterprise URL, GitLab MR URL or Bitbucket URL |
| `--session-id`, `--name`, `-n` | Use a specific UUID; display name shown in `/resume` and the terminal title, resumed with `claude --resume <name>` |
| `--no-session-persistence`, `--teleport` | Don't save the session (print mode only); resume a web session in this terminal |

Session mechanics: [[sessions-and-checkpoints]].

### Model and reasoning

| Flag | Effect |
|---|---|
| `--model` | Alias (`sonnet`, `opus`, `haiku`, `fable`) or full model name. Overrides the `model` setting and `ANTHROPIC_MODEL` |
| `--effort` | `low`, `medium`, `high`, `xhigh`, `max`, or `ultracode` for this session only; `CLAUDE_CODE_EFFORT_LEVEL` overrides it |
| `--fallback-model` | Comma-separated chain tried in order when the primary is overloaded or unavailable, e.g. `sonnet,haiku`. Overrides `fallbackModel` |
| `--advisor <model>`, `--betas` | Enable the advisor tool with `fable`, `opus`, `sonnet`, or a model ID; extra beta headers (API key users only) |
| `--autocompact <auto\|tokens>` | Auto-compact window for this session, e.g. `500k` |

See [[models-and-effort]].

### Permissions and tools

| Flag | Effect |
|---|---|
| `--permission-mode` | `default` (alias `manual`), `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`. Overrides `defaultMode` |
| `--dangerously-skip-permissions`, `--allow-dangerously-skip-permissions` | Same as `--permission-mode bypassPermissions`; or add `bypassPermissions` to the `Shift+Tab` cycle without starting in it |
| `--allowedTools`, `--allowed-tools`, `--disallowedTools`, `--disallowed-tools` | Rules that run without prompting, e.g. `"Bash(git log *)" "Read"`; deny rules, where a bare name removes the tool (`"*"` all tools, `"mcp__*"` all MCP tools) and a scoped rule like `Bash(rm *)` denies matching calls only |
| `--tools` | Restrict built-in tools: `""` none, `"default"`, or a list like `"Bash,Edit,Read"`. Doesn't affect MCP tools |
| `--permission-prompt-tool`, `--permission-prompts` | MCP tool that answers permission prompts in non-interactive mode; in print mode, `host` (default) sends prompts to the SDK host or prompt tool and `none` denies them |
| `--add-dir` | Extra working directories for file access; most `.claude/` configuration isn't discovered there |
| `--restricted` | For evaluation harnesses on shared machines: removes command- and code-running tools and WebFetch unless named in `--tools`, confines file tools to the working directories, loads only managed settings and `--settings`, refuses `bypassPermissions` and cloud sessions. Same as `CLAUDE_CODE_RESTRICTED=1` |

Rule syntax and modes: [[permissions-and-modes]]. Tool names: [[tools-reference]].

### System prompt

- `--system-prompt`, `--system-prompt-file`: replace the entire default prompt with text, or with a file's contents.
- `--append-system-prompt`, `--append-system-prompt-file`: append text, or a file's contents, to the default prompt.
- `--append-subagent-system-prompt`, `--append-subagent-system-prompt-file`: append text, or a file's contents (the two forms can't be combined), to every subagent's prompt except forked subagents (print mode only).
- `--system-prompt-snapshot`: `on` (default) reuses the prompt recorded on the conversation's first request; `off` rebuilds it every request.
- `--exclude-dynamic-system-prompt-sections`: move per-machine sections (cwd, environment, memory paths) into the first user message for cache reuse across machines. Default prompt only; use with `-p`.

The replacement flags are mutually exclusive; append flags combine with either. Appending keeps the default tool guidance and safety instructions, so replace only when the identity or permission model differs — then supply whatever the task still needs. Switchable personas are output styles ([[interface]]); project conventions go in CLAUDE.md ([[claude-md-and-memory]]).

The built prompt is recorded on a conversation's first request and reused, including after `--resume` or `--continue`, until compaction or a new conversation. Pass `--system-prompt-snapshot off` while iterating on prompt text across `--continue` runs; bare mode doesn't record unless you pass `--system-prompt-snapshot on`.

### Print mode and output

- `--print`, `-p`, `--verbose`: non-interactive mode; full turn-by-turn output, which overrides `viewMode`.
- `--output-format`, `--input-format`, `--json-schema`: output `text`, `json`, `stream-json`; input `text`, `stream-json`; validated JSON output matching a schema after the run.
- `--max-turns`, `--max-budget-usd`: cap agentic turns, exiting with an error at the limit; spend cap including subagent spend.
- `--include-partial-messages`, `--include-hook-events`: partial streaming events; hook lifecycle events in the stream (both require stream-json).
- `--replay-user-messages`, `--forward-subagent-text`, `--prompt-suggestions`: re-emit stdin user messages (stream-json in and out); subagent text and thinking blocks with `parent_tool_use_id`; emit `prompt_suggestion` messages (also needs `--verbose`) — all require stream-json.
- `--init`, `--maintenance`, `--init-only`: run Setup hooks with the `init` or `maintenance` matcher first (print mode); or run Setup and `SessionStart` hooks, then exit.
- `--bare`: skip discovery of hooks, skills, commands, subagents, plugins, MCP servers, auto memory and CLAUDE.md; only Bash, file read and file edit tools. Sets `CLAUDE_CODE_SIMPLE`.

### Configuration loading

- `--settings`, `--setting-sources`: settings file path or inline JSON, overriding matching keys for the session (file up to 2 MiB); load only some sources: `user`, `project`, `local`.
- `--mcp-config`, `--strict-mcp-config`: load MCP servers from JSON files or strings (with `-p`, waits for pending servers up to `MCP_TIMEOUT`); use only servers from `--mcp-config`.
- `--plugin-dir`, `--plugin-url`: load a plugin directory, `.zip`, or folder of plugins for this session, repeated per path; fetch a plugin `.zip` from a URL.
- `--agent`, `--agents`, `--disable-slash-commands`: run the session as a named agent (overrides the `agent` setting); define subagents as JSON, where invalid JSON exits at startup; disable all skills and commands.
- `--safe-mode`: load no customizations (CLAUDE.md, skills, plugins, hooks, MCP servers, output styles, themes, keybindings, status line, LSP servers, auto memory). Auth, model, built-in tools and permissions work; managed policy still applies. Sets `CLAUDE_CODE_SAFE_MODE`.

### Background, worktrees, cloud, remote

- `--bg`, `--background`: start as a background agent and return the session ID; can't be combined with `-p`. `--exec` runs a shell command as a PTY-backed background job.
- `--worktree`, `-w`, `--tmux`: start in a git worktree at `<repo>/.claude/worktrees/<name>`, accepting `#<number>`, a GitHub PR URL or a GitLab MR URL; create a tmux session for it, where `--tmux=classic` forces classic tmux over iTerm2 panes.
- `--cloud`, `--environment <environment-id>`: with a task, create a web session; with a session ID or URL plus `-p`, queue a follow-up (`--remote` is a deprecated alias). Or create the cloud session on a self-hosted environment (`ccpool_` IDs), where `--ref <branch>` sets the checkout base.
- `--remote-control`, `--rc`: interactive session with Remote Control enabled; `--remote-control-session-name-prefix <prefix>` prefixes auto-generated names.
- `--teammate-mode`, `--channels`: agent team display `in-process` (default), `auto`, `tmux`, `iterm2`; listen for channel notifications from `plugin:<name>@<marketplace>` entries, where `--dangerously-load-development-channels` enables channels off the approved allowlist, for development.

### IDE, browser, display, debugging

- `--ide`: connect to the IDE on startup when exactly one is available.
- `--chrome`, `--no-chrome`: enable or disable Claude in Chrome.
- `--ax-screen-reader`: flat, screen-reader friendly output.
- `--debug`, `--debug-file <path>`: debug mode, where category filters bind only in `=` form, e.g. `--debug='mcp,startup'`; write debug logs to a file, which implies debug mode.
- `--version`, `-v`: print the version.

## Examples

```bash
claude -p --max-budget-usd 5.00 --output-format json "Check for type errors"  # spend cap, JSON out
claude -w feature-auth --tmux  # isolated feature work in its own worktree and tmux session
```
