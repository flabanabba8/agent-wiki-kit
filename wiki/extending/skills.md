---
title: Skills
type: reference
tldr: "SKILL.md format, frontmatter, scopes, invocation"
sources:
  - raw/docs/official/skills.md
  - raw/docs/official/commands.md
  - raw/docs/official/features-overview.md
  - raw/docs/official/sub-agents.md
related: ["[[subagents]]", "[[plugins]]", "[[hooks]]", "[[claude-md-and-memory]]", "[[slash-commands]]", "[[agent-standards]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [skill-md, custom-slash-commands, skill-frontmatter, bundled-skills]
---

# Skills

A skill is a `SKILL.md` file of instructions that Claude adds to its toolkit. Claude loads it when its description matches the task, or you run it with `/skill-name`. Until a skill runs, only its name and description sit in context, so long reference material costs almost nothing until it is needed.

Custom commands and skills are the same mechanism: `.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both create `/deploy`. Claude Code skills follow the Agent Skills open standard ([[agent-standards]]) and extend it with invocation control, subagent execution and dynamic context injection.

**Use a skill** when you keep pasting the same playbook into chat, or a CLAUDE.md section has become a procedure ([[claude-md-and-memory]]). Use a [[hooks]] entry instead when something must happen every time without Claude's judgment, and a [[subagents]] definition when you need context isolation.

## Create a skill

```bash
mkdir -p ~/.claude/skills/summarize-changes
```

```yaml
---
description: Summarizes uncommitted changes and flags anything risky. Use when the user asks what changed or wants a commit message.
---

## Current changes

!`git diff HEAD`

## Instructions

Summarize the changes above in two or three bullets, then list risks.
```

The directory name becomes the command (`/summarize-changes`). The `` !`git diff HEAD` `` line runs before Claude sees the skill and is replaced by its output.

A skill directory can hold supporting files (`reference.md`, `examples.md`, `scripts/helper.py`). Reference them from `SKILL.md` so Claude knows when to load each one, and keep `SKILL.md` under 500 lines.

## Where skills load

| Location | Path | Loads in |
| :-- | :-- | :-- |
| Enterprise | `.claude/skills/<skill-name>/SKILL.md` in the managed settings directory | All users on machines where it is deployed |
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` | Your projects on this machine, not Cowork or cloud sessions |
| Project | `.claude/skills/<skill-name>/SKILL.md` | Sessions in this repository |
| Nested | `<subdir>/.claude/skills/<skill-name>/SKILL.md` | Sessions started in or below `<subdir>`, or once Claude touches a file there |
| Additional directory | `.claude/skills/` inside a `--add-dir` directory | That session |
| Plugin | `<plugin>/skills/<skill-name>/SKILL.md` | Wherever the plugin is enabled, as `/plugin-name:skill-name` |
| claude.ai account | Skills enabled for your claude.ai account | Cowork, cloud sessions, and terminal sessions signed in with that account |

- Project skills load from the start directory and every parent up to the repository root. `/add-dir` with a subdirectory path loads its nested skills early.
- Skill folders may be symlinks. The folder name `synced` is reserved.
- Files in `.claude/commands/` support the same frontmatter except `name` and `paths`.
- A skill folder containing `.claude-plugin/plugin.json` loads as a plugin named `<name>@skills-dir` ([[plugins]]).
- Edits to `SKILL.md` under the watched skill directories apply in the running session. A top-level skills directory created mid-session needs a restart.
- Cloud sessions and routines don't read `~/.claude/skills/`; enable the skill on your claude.ai account or commit it.
- Account skills sync into terminal sessions signed in with that account: they download to `~/.claude/skills/synced/` at start, refresh about every 10 minutes without a restart, are listed under `claude.ai sync` in `/skills`, and never run `!` commands locally. A few Anthropic skills such as `pdf` and `xlsx` always sync. Syncing needs a `/login` sign-in and feature-flag fetching, so it is off with an API key, `apiKeyHelper`, Bedrock, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `--bare`, `--safe-mode`, a `--setting-sources` list without `user`, or managed settings locking skills to plugin sources. `CLAUDE_CODE_SYNC_SKILLS=1` makes a non-interactive run wait for the download; `syncClaudeAiSkills: false` stops syncing and moves synced skills to `~/.claude/skills/.trash/`.

**Name clashes.** Enterprise beats personal, and personal beats project. Your skill replaces a bundled skill of the same name but not its aliases. A skill beats a `.claude/commands/` file. Plugin skills are namespaced, so both load. With a root `deploy` and a nested one in `apps/web/`, `/deploy` runs the root skill and `/apps/web:deploy` runs the nested one. A synced claude.ai skill that clashes runs only as `/anthropic-skills:<name>`.

## Frontmatter reference

All fields are optional; `description` is recommended. Claude Code reads frontmatter only when the opening `---` is the file's first line. Boolean fields accept `true`/`false`, `yes`/`no`, `on`/`off` and `1`/`0`.

| Field | Description |
| :-- | :-- |
| `name` | Display name in listings; defaults to the directory name, which still sets the command except in plugin skills, where `name` sets the last segment |
| `description` | What the skill does and when to use it. Claude matches on it. Falls back to the first non-empty body line |
| `when_to_use` | Trigger phrases or example requests, appended to `description`. The combined text is truncated at 1,536 characters in the listing |
| `argument-hint` | Autocomplete hint, such as `[issue-number]` |
| `arguments` | Named positional arguments for `$name` substitution. Space-separated string or YAML list |
| `disable-model-invocation` | `true` keeps the skill out of Claude's context and blocks subagent preloading. Default `false` |
| `user-invocable` | `false` hides the skill from the `/` menu and stops `/name` from running it; Claude can still invoke it. Default `true` |
| `allowed-tools` | Tools Claude may use without prompting during the turn that invokes the skill. Clears at your next message. String or YAML list |
| `disallowed-tools` | Tools removed from Claude's pool while the skill is active. Clears at your next message |
| `model` | Model for the rest of the current turn, any `/model` value or `inherit`. With `context: fork`, sets the forked subagent's model |
| `effort` | `low`, `medium`, `high`, `xhigh` or `max`; overrides the session level |
| `context` | `fork` runs the skill in a subagent |
| `agent` | Subagent type used with `context: fork`. Default `general-purpose` |
| `background` | With `context: fork`, `false` waits for the result in the invoking turn. Default `true` |
| `hooks` | Hooks registered on invocation, kept for the rest of the session. `once: true` removes one after its first successful run |
| `paths` | Globs that limit automatic loading to matching files, in the same format as path-specific rules |
| `shell` | `bash` (default) or `powershell` for `!` commands |
| `metadata` | Free-form map for your own tooling; Claude Code ignores it |
| `license` | Agent Skills field; accepted, not acted on |
| `compatibility` | Agent Skills field, up to 500 characters; accepted, not acted on |

Outside Claude Code (claude.ai uploads, the Skills API, `package_skill.py`), only `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools` are allowed; any other key is a hard error.

## Control who invokes a skill

| Frontmatter | You can invoke | Claude can invoke | In context |
| :-- | :-- | :-- | :-- |
| (default) | Yes | Yes | Description always; full skill when invoked |
| `disable-model-invocation: true` | Yes | No | Nothing until you invoke it |
| `user-invocable: false` | No | Yes | Description always; full skill when invoked |

Use `disable-model-invocation: true` for side-effecting workflows such as `/deploy` or `/commit`.

Permission rules also gate the Skill tool ([[permissions-and-modes]]): deny `Skill` to block all skills, or write `Skill(name)` for an exact match and `Skill(name *)` for a prefix.

The `skillOverrides` setting hides skills without editing their files. In the `/skills` menu, `Space` cycles a skill's state, saving the choice to `.claude/settings.local.json`. Plugin skills are managed through `/plugin` instead.

| Value | Listed to Claude | In `/` menu |
| :-- | :-- | :-- |
| `"on"` | Name and description | Yes |
| `"name-only"` | Name only | Yes |
| `"user-invocable-only"` | Hidden | Yes |
| `"off"` | Hidden | Hidden |

## Arguments and substitutions

| Variable | Expands to |
| :-- | :-- |
| `$ARGUMENTS` | Full argument string. If no placeholder receives input, Claude Code appends `ARGUMENTS: <value>` |
| `$ARGUMENTS[N]`, `$N` | Argument at 0-based index N, with shell-style quoting |
| `$name` | Named argument from `arguments` |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_EFFORT}` | Current effort level |
| `${CLAUDE_SKILL_DIR}` | Directory holding this `SKILL.md` |
| `${CLAUDE_PROJECT_DIR}` | Project root |
| `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}` | Plugin install and persistent data directories (plugin skills only) |

Escape a literal dollar before a digit as `\$1.00`. `${CLAUDE_SKILL_DIR}` and `${CLAUDE_PROJECT_DIR}` are also substituted in `allowed-tools`, so `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/render.sh *)` lets a bundled script run without a prompt. Stack skills at the start of a message (`/write-tests /fix-issue 123`) to load the first skill plus up to five more, each receiving the trailing text.

## Dynamic context injection

`` !`command` `` at the start of a line or after whitespace, or a fenced block opened with ```` ```! ````, runs before Claude sees the skill and is replaced by its output.

- A non-zero exit aborts the whole invocation. Exit 1 from search and comparison commands counts as a normal result; append `|| true` to other commands that may exit non-zero.
- Injected commands never prompt. A deny rule aborts the invocation, and outside auto mode so does any check that doesn't return allow, so pre-approve the command in `allowed-tools`. In auto mode a command that would need approval instead loads the skill with an instruction telling Claude to run it first, except in a forked skill that sets `agent` or a session without the shell tool, which still abort.
- Each command runs under the Bash tool's 2-minute timeout.
- `"disableSkillShellExecution": true` in settings replaces commands from user, project, plugin and additional-directory skills with a placeholder. Bundled and managed skills are unaffected.

## Run a skill in a subagent

`context: fork` starts a subagent of the `agent` type with the skill content as its prompt. It is not a fork of the conversation: the subagent sees no history, so the skill needs an explicit task, not only guidelines. It runs in the background by default; `background: false`, `-p` runs, `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` and a firing scheduled task all wait for it. A background fork gets the narrower background tool set, and `/rewind` does not undo its edits. The inverse pattern, a subagent that preloads skills, is on [[subagents]].

## Content lifecycle

Invoked content enters the conversation as one message and stays; the file is not re-read, so write standing instructions. Workspace trust does not gate `allowed-tools`, so review a repository's skills before running Claude Code there. After auto-compaction, Claude Code re-attaches the latest invocation of each skill, 5,000 tokens each within a 25,000-token budget filled most-recent first.

## Bundled skills

Bundled skills are prompt-based and invoked like your own: `/batch`, `/code-review`, `/debug`, `/design`, `/loop`, `/run`, `/simplify`, `/verify` and others listed on [[slash-commands]]. `/verify` runs only when you invoke it, `/design` drafts a design canvas ([[artifacts]]), and `/run-skill-generator` records a launch recipe at `.claude/skills/run-<name>/` for `/run` and `/verify` to follow.

Turn all bundled skills off with `disableBundledSkills`, or hide one with a `skillOverrides` entry of `"off"`. `/doctor` stays typable; hide it with `DISABLE_DOCTOR_COMMAND`.

## Skill listing budget

The listing always contains every skill name, but descriptions are shortened to fit 1% of the model's context window, dropping text from the least-invoked skills first. Each entry is capped at 1,536 characters (`skillListingMaxDescChars`). To make room, raise the budget with `skillListingBudgetFraction` (for example `0.02`) or a fixed `SLASH_COMMAND_TOOL_CHAR_BUDGET`, set low-priority skills to `"name-only"` in `skillOverrides`, and put the key use case first in each description.

`/doctor` estimates the listing's cost, the Skills row in `/context` shows its size after the budget, and `/skill-doctor` reports per-skill context cost and usage ([[context-window]]).

## Test and troubleshoot

- **Measure, don't eyeball.** Run realistic prompts in fresh sessions with the skill enabled and disabled; `claude plugin eval` automates this for a plugin's skills ([[plugins]]). Triggering only tells you Claude found the skill, not that the output was right.
- **Not triggering:** put the words users say in `description`, ask Claude "What skills are available?", or invoke it with `/skill-name`. Malformed YAML loads the body with empty metadata; run `claude plugin validate .claude/skills`.
- **Triggers too often:** narrow the description or set `disable-model-invocation: true`.
