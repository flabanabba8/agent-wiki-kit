---
title: Tools Reference
type: reference
tldr: "Built-in tools, prompts, and key behaviors"
sources:
  - raw/docs/official/tools-reference.md
  - raw/docs/official/env-vars.md
related: ["[[permissions-and-modes]]", "[[how-claude-code-works]]", "[[subagents]]", "[[hooks]]", "[[mcp]]", "[[environment-variables]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [built-in-tools, tool-names, claude-code-tools, tool-permissions]
---

# Tools Reference

Built-in tools are the actions Claude takes: read and edit files, run commands, search the web, spawn subagents. The tool names below are the exact strings used in permission rules, subagent `tools` lists, `--allowedTools`/`--disallowedTools`, skill `allowed-tools` and hook matchers. Add more tools through MCP servers ([[mcp]]). Skills run through the existing `Skill` tool and add no tool entries.

**Reading the Prompts column.** It shows whether the tool asks first in Manual mode for paths inside the working directory. File tools marked No (`Read`, `Grep`, `Glob`) still prompt for paths outside the working and additional directories. `Bash` is Yes, but a built-in set of read-only commands runs without a prompt. On Pro, Max and Team plans sessions start in auto mode, where a classifier makes most of these decisions ([[permissions-and-modes]]).

## Tool list

| Tool | What it does | Prompts |
| :--- | :--- | :--- |
| **Files and code** | | |
| `Read` | Read files, images, PDFs, notebooks | No |
| `Write` | Create or overwrite a file | Yes |
| `Edit` | Exact string replacement in a file | Yes |
| `NotebookEdit` | Modify Jupyter notebook cells | Yes |
| `Glob` | Find files by name pattern (absent by default on macOS, Linux, WSL) | No |
| `Grep` | Search file contents with ripgrep (absent by default on macOS, Linux, WSL) | No |
| `LSP` | Definitions, references, type errors via a language server | No |
| **Shell** | | |
| `Bash` | Run shell commands | Yes |
| `PowerShell` | Run PowerShell commands natively | Yes |
| `Monitor` | Run a background command or WebSocket and feed each event to Claude | Yes |
| **Web** | | |
| `WebFetch` | Fetch a URL and extract content with a prompt | Yes |
| `WebSearch` | Web search returning titles and URLs | Yes |
| **Agents and orchestration** | | |
| `Agent` | Spawn a subagent (or a teammate when agent teams are on) | No |
| `SendMessage` | Message a teammate, a resumable subagent, or another local session | No |
| `ListAgents` | List agents and sessions Claude can message | No |
| `TaskStop` | Stop a background task, teammate or named agent | No |
| `TaskOutput` | Read a background task's output (deprecated: `Read` the output file instead) | No |
| `Workflow` | Run a dynamic workflow script across many subagents | Yes |
| `Skill` | Run a skill in the main conversation | Yes |
| **Planning and interaction** | | |
| `AskUserQuestion` | Ask multiple-choice questions | No |
| `EnterPlanMode` | Switch to plan mode | No |
| `ExitPlanMode` | Present a plan for approval and leave plan mode | Yes |
| `EnterWorktree` | Create or enter a git worktree; prompts only for a `path` outside `.claude/worktrees/` | Yes |
| `ExitWorktree` | Leave the worktree session | No |
| **Task tracking** | | |
| `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate` | Session task list (see availability below) | No |
| `TodoWrite` | Checklist alternative when `CLAUDE_CODE_ENABLE_TASKS=0` | No |
| **Scheduling** | | |
| `CronCreate`, `CronDelete`, `CronList` | Session-scoped scheduled prompts, restored on resume if unexpired | No |
| `ScheduleWakeup` | Pick the next iteration time of a self-paced `/loop` (1 minute to 1 hour) | No |
| `RemoteTrigger` | Create, update, run, list cloud routines; backs `/schedule` | No |
| **MCP** | | |
| `ListMcpResourcesTool`, `ReadMcpResourceTool` | List and read MCP resources | No |
| `ToolSearch` | Load deferred tools when tool search is on | No |
| `WaitForMcpServers` | Wait for servers still connecting (only when tool search is off) | No |
| **Output and delivery** | | |
| `Artifact` | Publish HTML or Markdown as a private claude.ai page | Yes |
| `SendUserFile` | Send files to your device (Remote Control or cloud sessions) | No |
| `PushNotification` | Desktop notification, plus phone push over Remote Control | No |
| `ShareOnboardingGuide` | Upload `ONBOARDING.md` for `/team-onboarding` | Yes |
| `ReportFindings` | Structured code-review findings | No |
| `SendFeedback` | Draft a feedback report you review before sending | No |
| `EndConversation` | End the session in rare abuse cases or an explicit demo | No |

Cloud-backed tools (`PushNotification`, `RemoteTrigger`, `SendUserFile`, `Monitor`, `SendFeedback`, `EndConversation`) are unavailable on Amazon Bedrock, Google Cloud's Agent Platform and Microsoft Foundry. To see what a running session has, ask Claude `What tools do you have access to?`; run `/mcp` for exact MCP tool names. The advisor is a server tool with no name usable in rules.

## Rule formats

| Rule | Applies to |
| :--- | :--- |
| `Bash(npm run *)` | Bash, Monitor |
| `PowerShell(Get-ChildItem *)` | PowerShell |
| `Read(~/secrets/**)` | Read, Grep, Glob, LSP |
| `Edit(/src/**)` | Edit, Write, NotebookEdit |
| `Skill(deploy *)` | Skill |
| `Agent(Explore)` | Agent |
| `WebFetch(domain:example.com)` | WebFetch |
| `WebSearch` | WebSearch (no specifier) |

Other tools take only the bare name. An `Edit(...)` allow rule also grants read on that path; a `Read(...)` deny rule also blocks Edit and Write there. Hook `matcher` fields use bare tool names ([[hooks]]).

## Bash

- Each command runs in a separate process. A `cd` in the main session carries over while it stays inside the project or an added directory; set `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1` to reset every time. Subagents never carry `cd` over.
- Exports don't persist between commands. Activate virtualenvs before launch, or set `CLAUDE_ENV_FILE` (or populate it from a SessionStart hook). Aliases and functions from `~/.zshrc`, `~/.bashrc` or `~/.profile` are captured at startup.
- **Timeouts:** Claude passes a per-call `timeout`. `BASH_DEFAULT_TIMEOUT_MS` defaults to two minutes and `BASH_MAX_TIMEOUT_MS` caps requests at ten.
- **Output:** a valid result arrives inline up to about 30,000 characters; beyond that Claude gets a file path plus a preview. A failure arrives inline up to about 10,000 characters as a head-and-tail excerpt. `BASH_MAX_OUTPUT_LENGTH` (max 150,000) sizes the read-back window; the `bashOutputMaxChars` setting (up to 128,000) sizes the inline ceiling too. Exit code 1 counts as valid only for `grep`, `rg`, `egrep`, `fgrep`, `find`, `diff`, `test`, `[`, `git diff` and `git grep`.
- **Background:** `run_in_background: true` starts a background task, listed and stopped in `/tasks`. A command that hits its timeout moves to the background unless it starts with `sleep`. A foreground subagent's commands stop at its final response. In `-p` runs, background commands end shortly after the final result.
- **Memory cap (Linux, WSL):** `CLAUDE_CODE_TOOL_MEMORY_LIMIT=4G` caps Bash, PowerShell and Monitor commands together through a cgroup. The kernel kills a command that exceeds it without naming the cap.

## Edit, Write, Read, NotebookEdit

- **Edit** replaces `old_string` with `new_string` exactly, with no regex or fuzzy matching. The match must be unique unless `replace_all: true`. Claude Opus 4.6, Claude Haiku 4.5 and older models must read the file first. Newer models can edit an unread file when reading it wouldn't prompt. A file changed on disk can still be edited when `old_string` matches the current content unambiguously.
- Viewing a single file with `cat`, `nl`, `bat`, `batcat`, `head`, `tail`, `sed -n 'X,Yp'`, `grep`, `egrep`, `fgrep` or `rg` (no pipes or redirects) satisfies read-before-edit. It doesn't change permissions.
- **Write** overwrites the whole file. Existing files follow the same read rules as Edit, except notebooks and partially read files, which always need a read.
- **Read** returns numbered lines from an absolute path. Oversized whole-file reads return a first page with a `PARTIAL view` notice; use `offset` and `limit` for more. Images are resized to fit model limits. PDFs over 10 pages are read in `pages` ranges of up to 20. Notebooks return cells with outputs, refusing files over 100 MB. Read doesn't list directories.
- **NotebookEdit** targets one cell by `cell_id` in `replace` (default), `insert` (needs `cell_type`) or `delete` mode, governed by `Edit(...)` rules.

## Glob and Grep

On macOS, Linux and WSL, both tools are left out by default; Claude searches with `find` and `grep` through Bash, which run embedded `bfs` and `ugrep`. You get them back by naming them in `--tools` or `--allowedTools`, by removing Bash (a deny rule, `--disallowedTools` or `--restricted`), or in a subagent that lists them without Bash.

- **Glob:** `**` recursion, results sorted by modification time, capped at 100 files. It includes gitignored files unless `CLAUDE_CODE_GLOB_NO_IGNORE=false`.
- **Grep:** ripgrep regex syntax (escape metacharacters, e.g. `interface\{\}`). Modes are `files_with_matches` (default), `content` and `count`; filter with `glob` or `type`; `multiline: true` spans lines. It respects `.gitignore`.

## WebFetch and WebSearch

- **WebFetch** converts HTML to Markdown and runs your prompt over the page with a small, fast model, so results are lossy. Refetch with a sharper prompt or use `curl` for the raw page. HTTP is upgraded to HTTPS. Responses are cached 15 minutes (`CLAUDE_CODE_WEBFETCH_CACHE_TTL_MS`), downloads fail after five minutes (`CLAUDE_CODE_WEBFETCH_DEADLINE_MS`), and a cross-host redirect is returned to Claude instead of followed.
- In Manual and `acceptEdits` modes WebFetch prompts, except for domains your rules decide and a built-in set of documentation domains. **Yes, and don't ask again** saves a `WebFetch(domain:...)` rule to `.claude/settings.local.json`. Sandboxed commands don't inherit the preapproved domains.
- **WebSearch** makes up to eight backend searches per call and accepts `allowed_domains` or `blocked_domains` (not both). A session allows 200 searches across all subagents (`CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION`); `/clear` resets the count. It is unavailable on Amazon Bedrock and needs an Anthropic-hosted deployment on Foundry.

## Agent

A subagent works in its own context and returns one text result; the parent never sees its intermediate calls. If the definition sets neither `tools` nor `disallowedTools`, it inherits every tool available to subagents; with both set, `disallowedTools` wins. Launching doesn't prompt, but each tool call is checked. Background subagents raise their prompts in your main session, and `Esc` denies just that call. A subagent stopped by `maxTurns` returns partial output that Claude can resume. Details are on [[subagents]].

## Monitor and PowerShell

- **Monitor** runs a script in the background and delivers each output line as an event, or opens a `ws://`/`wss://` WebSocket via a `ws` input (`url`, `protocols`). Every watch has a deadline: 5 minutes by default, 30 at most, 10 in single-prompt `-p` runs. It uses Bash permission rules. Private, link-local and cloud-metadata addresses are denied. It is off when `DISABLE_TELEMETRY` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` is set.
- **PowerShell** is enabled automatically on Windows without Git Bash and on by default for claude.ai and Console accounts with Git Bash. It is opt-in on Linux, macOS and WSL (`CLAUDE_CODE_USE_POWERSHELL_TOOL=1`, PowerShell 7 `pwsh` on `PATH`). It runs with `-ExecutionPolicy Bypass` at process scope unless `CLAUDE_CODE_POWERSHELL_RESPECT_EXECUTION_POLICY=1`. Profiles aren't loaded and Windows sandboxing isn't supported. Hooks that inspect shell commands should match `Bash|PowerShell`.

## Availability notes

- **Task tools** (`TaskCreate`, `TaskGet`, `TaskUpdate`, `TaskList`, `TodoWrite`) are provided by default only on Claude 3.x, Opus 4 through 4.7, Sonnet 4 through 4.6 and Haiku 4.5. On other models, opt in with `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` or by naming a task tool in `--allowedTools` or `--tools`. Background sessions and Claude Code on the web provide them on every model.
- **EndConversation** appears only in interactive terminal sessions on Opus 4.8, Sonnet 5, Fable 5 or later, never in `-p`, the SDK, the VS Code panel, the web, bare mode or third-party providers. Deny rules can't remove it while other tools remain. An ended session accepts only `/clear`, `/resume`, `/help`, `/exit` and `/feedback`.
- **LSP** stays inactive until you install a code intelligence plugin and the server binary, and never runs in cloud sessions.
- **SendFeedback** drafts are saved under `~/.claude/feedback/drafts/` and sent only from `/feedback`. Turn drafting off with the `feedbackDrafts` setting or `CLAUDE_CODE_SEND_FEEDBACK=0`.
