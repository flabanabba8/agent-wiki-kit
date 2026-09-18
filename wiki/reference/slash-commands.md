---
title: Slash Commands
type: reference
tldr: "Every built-in / command, grouped by task"
sources:
  - raw/docs/official/commands.md
related: ["[[cli-reference]]", "[[skills]]", "[[context-window]]", "[[sessions-and-checkpoints]]", "[[models-and-effort]]", "[[troubleshooting]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [slash-command-list, claude-commands, in-session-commands, built-in-commands]
---

# Slash Commands

Commands control Claude Code from inside a session: switch models, manage permissions, clear context, run a workflow. Type `/` to see what's available, or `/` plus letters to filter. Launch-time flags are on [[cli-reference]]; your own commands are skills ([[skills]]); MCP servers can expose prompts as commands too ([[mcp]]).

## How commands behave

- **Position.** A command is recognized only at the start of a message; the text after it becomes its arguments. Skills are the exception: `/skill-a /skill-b do XYZ` loads every leading skill (up to six), each receiving the trailing text.
- **Mid-response.** A command sent while Claude is responding queues until the turn ends. Some run immediately, such as `/status`, `/tasks` and `/usage`; in fullscreen rendering, dialogs such as `/theme` and `/help` open immediately too.
- **Availability.** Not every command appears for every user; platform, plan, provider and policy decide. Unavailable ones are left out of the menu and return `Unknown command`.
- **Menu matching.** The top suggestion is highlighted only when your letters match a name or alias from the start of the name or of a word in it, ignoring `:`, `_` and `-`: `/adddir` highlights `/add-dir`, `/new` highlights `/clear`. After a typo nothing is highlighted and `Enter` submits your text as typed.
- **Hidden commands** such as `/heapdump` appear only once you type the full name.

**(S)** marks a bundled skill (a prompt handed to Claude), **(W)** a bundled workflow that fans work out across subagents in the background. `<arg>` is required, `[arg]` optional.

## Session and context

| Command | Purpose |
| :--- | :--- |
| `/clear [name]` | New conversation with empty context; the name labels the previous one in `/resume`. Aliases `/reset`, `/new` |
| `/compact [instructions]` | Summarize the conversation to free context, with optional focus |
| `/autocompact [auto\|<tokens>]` | Set how full the window gets before auto-compaction (e.g. `500k`); saved to user settings |
| `/context [all]` | Colored grid of context usage with optimization suggestions; `all` expands the breakdown |
| `/resume [session]` | Resume by ID or name, or open the picker (background sessions marked `bg`). Alias `/continue` |
| `/branch [name]` | Branch the conversation here and switch into it; the original stays in `/resume` |
| `/fork [prompt]` | Copy the conversation into a new background session and keep working here |
| `/subtask <task>` | Spawn a forked subagent that inherits the conversation; its result returns here |
| `/rewind` | Roll code and/or conversation back to a checkpoint, or summarize from a message. Aliases `/checkpoint`, `/undo` |
| `/rename [name]` | Rename the session (auto-generates a name when omitted) |
| `/btw [question]` | Side question that doesn't enter the conversation history |
| `/recap` | One-line summary of the session |
| `/goal [condition\|clear]` | Set a completion condition and keep working across turns until an evaluator says it holds; `clear` drops it — [[prompting-and-workflows]] |
| `/cd <path>` | Move the session to another working directory, keeping the conversation |
| `/add-dir <path>` | Add a working directory for file access |
| `/copy [N]` | Copy the Nth-latest response; picker for code blocks, `w` writes to a file |
| `/export [filename]` | Export the conversation as plain text |
| `/exit` | Exit; in an attached background session, detach. Alias `/quit` |

Context management is on [[context-window]]; resuming and rewinding on [[sessions-and-checkpoints]].

## Model, effort, planning

| Command | Purpose |
| :--- | :--- |
| `/model [model]` | Switch model and save it as the default; in the picker press `s` for this session only, left/right arrows adjust effort |
| `/effort [level\|auto\|status]` | `low` to `xhigh`, `max`, `ultracode`, or `auto`; `max` and `ultracode` apply to the session only |
| `/fast [on\|off]` | Toggle fast mode |
| `/advisor [model\|off]` | Enable or disable the advisor tool (`fable`, `opus`, `sonnet`, or a model ID) |
| `/plan [description]` | Enter plan mode, optionally starting on a task |

See [[models-and-effort]].

## Permissions, settings, project setup

| Command | Purpose |
| :--- | :--- |
| `/permissions` | Allow, ask and deny rules by scope, working directories, recent auto mode denials, and an **Auto mode** tab for classifier rules. Alias `/allowed-tools` |
| `/auto-mode-setup` | Draft `autoMode.environment` entries from your project into user settings (Pro, Max, Team) |
| `/sandbox` | Toggle sandbox mode on supported platforms |
| `/config [key=value ...]` | Open settings, or set keys directly (`/config theme=dark`); `/config --help` lists keys. Alias `/settings` |
| `/status` | Settings on the Status tab: version, model, account, connectivity |
| `/init` | Generate a starter `CLAUDE.md`; `CLAUDE_CODE_NEW_INIT=1` gives an interactive flow covering skills, hooks and memory files |
| `/memory` | Edit `CLAUDE.md` files, toggle and view auto memory |
| `/import [codex\|gemini\|cursor] [--dry-run] [--yes]` | Import instruction files, MCP servers, commands, subagents and skills from OpenAI Codex, Gemini CLI or Cursor |
| `/hooks` | View hook configurations |
| `/keybindings` | Open your keybindings file |
| `/privacy-settings` | View and update privacy settings (Pro and Max) |

See [[permissions-and-modes]], [[settings]] and [[claude-md-and-memory]].

## Skills, plugins, MCP, agents

| Command | Purpose |
| :--- | :--- |
| `/skills` | List skills; type to filter, `t` sorts by tokens, `Space`/`Enter` cycles visibility |
| `/reload-skills` | Re-scan skill and command directories without restarting |
| `/skill-doctor` | Per-skill context cost and usage, to find skills to turn off |
| `/plugin [subcommand]` | Plugin menu, or `list`, `install`, `enable`, `disable` directly |
| `/reload-plugins [--force]` | Apply plugin changes without restarting; `--force` accepts a prompt-cache reset |
| `/mcp [reconnect <server>\|enable\|disable [<server>\|all]]` | Manage MCP connections and OAuth |
| `/agents` | Prints a reminder to ask Claude to create or manage subagents, or edit `.claude/agents/` or `~/.claude/agents/` |
| `/list-agents` | Subagents, teammates and sessions Claude can message. Alias `/peers` |
| `/workflows` | Watch, pause, resume or save workflows |
| `/workflow-authoring` | (S) Reference for writing dynamic workflow scripts |
| `/fewer-permission-prompts` | (S) Scan transcripts and add a read-only allowlist to project `.claude/settings.json` |

## Parallel, background, scheduled, cloud

| Command | Purpose |
| :--- | :--- |
| `/tasks` | Background work in this session, including finished subagents. Alias `/bashes` |
| `/background [prompt]` | Detach the session as a background agent. Alias `/bg` |
| `/stop` | Stop the attached background session (transcript and worktree kept) |
| `/batch <instruction>` | (S) Split a large change into 5 to 30 units, each run by a background subagent in its own worktree, opening a PR |
| `/loop [interval] [prompt]` | (S) Repeat a prompt while the session stays open; omit the interval to let Claude self-pace. Alias `/proactive` |
| `/schedule [description]` | Create, update, list or run cloud routines. Alias `/routines` |
| `/deep-research <question>` | (W) Fan out web searches, cross-check sources, write a cited report |
| `/teleport` | Pull a Claude Code on the web session into this terminal. Alias `/tp` |
| `/remote-control` | Make this session available through Remote Control. Alias `/rc` |
| `/remote-env` | Default environment for cloud agents |
| `/autofix-pr [prompt]` | Cloud session watching this branch's PR that pushes fixes for CI failures and review comments |
| `/desktop` | Continue in the Desktop app (macOS, x64 Windows). Alias `/app` |

See [[worktrees-and-background-work]], [[workflows]] and [[routines-and-scheduling]].

## Review and shipping

| Command | Purpose |
| :--- | :--- |
| `/diff` | Review working-tree changes, including Claude's edits |
| `/code-review [low\|medium\|high\|xhigh\|max\|ultra] [--fix] [--comment] [pr#\|branch\|path]` | (S) Find correctness bugs and cleanups; `--fix` applies them, `--comment` posts to the PR or MR, `ultra` runs a cloud review. Alias `/review` |
| `/ultrareview [PR or branch]` | Alias of `/code-review ultra` |
| `/simplify [target]` | (S) Four parallel agents review reuse, simplification, efficiency and abstraction level, then apply fixes. No bug hunting |
| `/security-review` | Review the branch diff against origin's default branch for vulnerabilities (needs an `origin` remote) |
| `/verify` | (S) Build, run and observe the app to confirm a change works |
| `/run` | (S) Launch and drive the app |
| `/run-skill-generator` | (S) Write a per-project skill teaching `/run` and `/verify` to launch the app |
| `/install-github-app` | Install the Claude GitHub App, optionally with Actions workflows (github.com only) |

See [[ci-cd-and-code-review]].

## Diagnostics and feedback

| Command | Purpose |
| :--- | :--- |
| `/doctor` | (S) Setup checkup that diagnoses and can fix installation, settings, unused extensions, slow hooks and oversized `CLAUDE.md`. Alias `/checkup` |
| `/debug [description]` | (S) Turn on debug logging and analyze the session log |
| `/heapdump` | (Hidden) Write a heap snapshot and memory breakdown; share only the `-diagnostics.json` file |
| `/feedback [report]` | Send product feedback; with no argument, opens the queue of Claude-drafted reports where available |
| `/bug [report]` | Report a bug or share the conversation after a consent screen. Alias `/share` |
| `/insights` | HTML report analyzing your recent sessions |
| `/release-notes` | Changelog in a version picker |

See [[troubleshooting]].

## Account, usage, providers

| Command | Purpose |
| :--- | :--- |
| `/login`, `/logout` | Sign in to or out of your Anthropic account |
| `/usage` | Session cost, plan limits and activity. Aliases `/cost`, `/stats` |
| `/usage-credits` | Configure usage credits, or request them from an admin |
| `/rate-limit-options` | (Hidden) Ways to keep working when a claude.ai limit blocks a request |
| `/upgrade` | Open the plan upgrade page |
| `/passes` | Share a free week of Claude Code (eligible accounts) |
| `/setup-bedrock` | (Hidden until `CLAUDE_CODE_USE_BEDROCK=1`) Amazon Bedrock setup wizard |
| `/setup-vertex` | (Hidden until `CLAUDE_CODE_USE_VERTEX=1`) Google Cloud's Agent Platform setup wizard |

See [[costs-and-usage]].

## Interface

| Command | Purpose |
| :--- | :--- |
| `/theme` | Color theme, including `auto`, daltonized, ANSI and custom themes |
| `/tui [default\|fullscreen]` | Switch renderer and relaunch with the conversation intact |
| `/focus` | Toggle the focus view (fullscreen only) |
| `/scroll-speed` | Mouse-wheel scroll speed (fullscreen only) |
| `/statusline` | Configure the status line |
| `/color [color\|default]` | Prompt bar color for this session |
| `/terminal-setup` | Install a Shift+Enter newline binding and related terminal fixes |
| `/voice [hold\|tap\|off]` | Voice dictation |
| `/powerup` | Interactive lessons teaching features with animated demos ([[interface]]) |

See [[interface]].

## Integrations, design, misc

| Command | Purpose |
| :--- | :--- |
| `/ide` | Manage IDE integrations |
| `/chrome` | Claude in Chrome settings |
| `/install-slack-app` | Install the Claude Slack app |
| `/web-setup` | Connect GitHub to Claude Code on the web using local `gh` credentials |
| `/artifacts` | List, attach, open or copy links to your artifacts |
| `/design [brief]` | (S) Draft artboards on a canvas artifact you can edit, export or implement ([[artifacts]]) |
| `/design-sync [hint]` | (S) Upload your repo's React design system to Claude Design |
| `/design-login` | Authorize design-system access for `/design-sync` |
| `/dataviz [request]` | (S) Chart and dashboard design guidance |
| `/claude-api [subcommand]` | (S) Claude API and Managed Agents reference; subcommands `migrate`, `upgrade`, `managed-agents-onboard`, `prompt-audit`, `cost-optimize`, `build-eval`, `hillclimb` |
| `/team-onboarding` | Onboarding guide from 30 days of your usage |
| `/mobile` | QR code for the mobile app. Aliases `/ios`, `/android` |
| `/stickers`, `/radio` | Order stickers; open Claude FM in the browser |

Replacements: for `/pr-comments`, ask Claude to read the PR comments; for `/vim`, `/config` → Editor mode; for `/ultraplan`, plan mode.
