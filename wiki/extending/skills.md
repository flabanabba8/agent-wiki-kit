---
title: Skills
type: reference
tldr: "SKILL.md format, frontmatter, scopes, invocation"
sources:
  - raw/docs/official/skills.md
  - raw/docs/official/commands.md
  - raw/docs/official/features-overview.md
  - raw/docs/official/sub-agents.md
  - raw/docs/changelog-2.1.275-to-2.1.282.md
related: ["[[subagents]]", "[[plugins]]", "[[hooks]]", "[[claude-md-and-memory]]", "[[slash-commands]]", "[[agent-standards]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [skill-md, custom-slash-commands, skill-frontmatter, bundled-skills]
---

# Skills

A skill is a `SKILL.md` file of instructions. Claude loads it when its description matches the task, or you run it with `/skill-name`; until then only its name and description sit in context.

Custom commands and skills are one mechanism: `.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both create `/deploy`. Skills follow the Agent Skills open standard ([[agent-standards]]) with Claude Code extensions.

**Use a skill** for a playbook you keep pasting; use [[hooks]] for what must always happen, and [[subagents]] for context isolation.

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

The directory name becomes the command (`/summarize-changes`).

A skill directory can hold supporting files (`reference.md`, `scripts/helper.py`); reference them from `SKILL.md`, and keep `SKILL.md` under 500 lines.

## Where skills load

| Location | Path | Loads in |
| :-- | :-- | :-- |
| Enterprise | `.claude/skills/<skill-name>/SKILL.md` in the managed settings directory | All users on machines where it is deployed |
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` | Your projects on this machine, not Cowork or cloud sessions |
| Project | `.claude/skills/<skill-name>/SKILL.md` | Sessions in this repository |
| Nested | `<subdir>/.claude/skills/<skill-name>/SKILL.md` | Sessions started in or below `<subdir>`, or once Claude touches a file there |
| Additional directory | `.claude/skills/` inside a `--add-dir` directory | That session |
| Plugin | `<plugin>/skills/<skill-name>/SKILL.md` | Wherever the plugin is enabled, as `/plugin-name:skill-name` |
| claude.ai account | Skills enabled in claude.ai settings | Cowork, cloud, and terminal sessions signed in with that account |

- Project skills load from the start directory and every parent up to the repository root (in a linked worktree, the worktree root; if it has no `.claude/skills`, the main checkout's skills load). `/add-dir` with a subdirectory path loads its nested skills early.
- Skill folders may be symlinks. The folder name `synced` is reserved.
- Files in `.claude/commands/` support the same frontmatter except `name` and `paths`.
- A skill folder containing `.claude-plugin/plugin.json` loads as a plugin named `<name>@skills-dir` ([[plugins]]).
- Edits to `SKILL.md` under the watched skill directories apply in the running session. A top-level skills directory created mid-session needs a restart.
- Cloud sessions and routines don't read `~/.claude/skills/`; enable the skill on your claude.ai account or commit it.
- Account skills sync into terminal sessions signed in with that account: they download to `~/.claude/skills/synced/` at start, refresh about every 10 minutes without a restart, are listed under `claude.ai sync` in `/skills`, and never run `!` commands locally. A few Anthropic skills such as `pdf` and `xlsx` always sync. Syncing needs a `/login` sign-in and feature-flag fetching, so it is off with an API key, `apiKeyHelper`, Bedrock, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `--bare`, `--safe-mode`, a `--setting-sources` list without `user`, or managed settings locking skills to plugin sources. `CLAUDE_CODE_SYNC_SKILLS=1` makes a non-interactive run wait for the download; `syncClaudeAiSkills: false` stops syncing and moves synced skills to `~/.claude/skills/.trash/`.

**Name clashes.** Enterprise beats personal, and personal beats project. Your skill replaces a bundled skill of the same name but not its aliases. A skill beats a `.claude/commands/` file. Plugin skills are namespaced, so both load. With a root `deploy` and a nested one in `apps/web/`, `/deploy` runs the root skill and `/apps/web:deploy` runs the nested one. A synced claude.ai skill shows and runs by its short name unless another command uses it; then it runs only as `/anthropic-skills:<name>`.

## Frontmatter reference

All fields are optional; `description` is recommended. Claude Code reads frontmatter only when the opening `---` is the file's first line, and silently ignores unknown field names (hyphens must match). Boolean fields accept `true`/`false`, `yes`/`no`, `on`/`off` and `1`/`0`.

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
| `metadata`, `license`, `compatibility` | Accepted and ignored (`compatibility` up to 500 characters) |

claude.ai uploads and the Skills API accept only `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`; other keys are errors.

## Control who invokes a skill

| Frontmatter | You can invoke | Claude can invoke | In context |
| :-- | :-- | :-- | :-- |
| (default) | Yes | Yes | Description always; full skill when invoked |
| `disable-model-invocation: true` | Yes | No | Nothing until you invoke it |
| `user-invocable: false` | No | Yes | Description always; full skill when invoked |

Permission rules also gate the Skill tool ([[permissions-and-modes]]): deny `Skill` to block all skills, or write `Skill(name)` for an exact match and `Skill(name *)` for a prefix. A few built-in commands, including `/init` and `/security-review`, are reachable through the Skill tool.

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

Escape a literal dollar before a digit as `\$1.00`. `${CLAUDE_SKILL_DIR}` and `${CLAUDE_PROJECT_DIR}` also expand in `allowed-tools`, e.g. `Bash(${CLAUDE_SKILL_DIR}/scripts/render.sh *)`. Stack skills at the start of a message (`/write-tests /fix-issue 123`) to load the first skill plus up to five more, each receiving the trailing text.

## Dynamic context injection

`` !`command` `` at the start of a line or after whitespace, or a fenced block opened with ```` ```! ````, runs before Claude sees the skill and is replaced by its output.

- A non-zero exit aborts the whole invocation. Exit 1 from search and comparison commands counts as a normal result; append `|| true` to other commands that may exit non-zero.
- Injected commands never prompt. A deny rule aborts the invocation; outside auto mode so does any non-allow result, so pre-approve the command in `allowed-tools`. In auto mode, the skill instead tells Claude to run the command itself.
- Each command runs under the Bash tool's 2-minute timeout.
- `"disableSkillShellExecution": true` in settings replaces commands from user, project, plugin and additional-directory skills with a placeholder. Bundled and managed skills are unaffected.

## Run a skill in a subagent

`context: fork` starts a subagent of the `agent` type with the skill content as its prompt. It is not a fork of the conversation: the subagent sees no history, so the skill needs an explicit task, not only guidelines. It runs in the background by default; `background: false`, `-p` runs, `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` and a firing scheduled task all wait for it. A background fork gets the narrower background tool set, and `/rewind` does not undo its edits. The inverse pattern, a subagent that preloads skills, is on [[subagents]].

## Content lifecycle

Invoked content enters the conversation as one message and stays; the file is not re-read, so write standing instructions. Workspace trust does not gate `allowed-tools`, so review a repository's skills before running Claude Code there. After auto-compaction, Claude Code re-attaches the latest invocation of each skill, 5,000 tokens each within a 25,000-token budget filled most-recent first.

## Bundled skills

Bundled skills are prompt-based and invoked like your own. They include `/batch`, `/claude-api`, `/code-review`, `/dataviz`, `/debug`, `/design`, `/doctor`, `/fewer-permission-prompts`, `/loop`, `/run`, `/run-skill-generator`, `/simplify`, `/update-config`, `/verify` and `/workflow-authoring` (the last only when dynamic workflows are enabled). `/verify` runs only when you invoke it, and `/design` drafts a design canvas ([[artifacts]]). `/run-skill-generator` records a launch recipe at `.claude/skills/run-<name>/` for `/run` and `/verify` to follow. The full list is on [[slash-commands]].

Turn all bundled skills off with `disableBundledSkills`, or hide one with a `skillOverrides` entry of `"off"`. `/doctor` stays typable; hide it with `DISABLE_DOCTOR_COMMAND`.

## Skill listing budget

The listing always contains every skill name, but descriptions are shortened to fit 1% of the model's context window, dropping text from the least-invoked skills first. Each entry is capped at 1,536 characters (`skillListingMaxDescChars`). To make room, raise the budget with `skillListingBudgetFraction` (for example `0.02`) or a fixed `SLASH_COMMAND_TOOL_CHAR_BUDGET`, set low-priority skills to `"name-only"` in `skillOverrides`, and put the key use case first in each description.

`/doctor` estimates the listing's cost, the Skills row in `/context` shows its size after the budget, and `/skill-doctor` reports per-skill context cost and usage ([[context-window]]).

## Test and troubleshoot

- **Measure:** compare realistic prompts in fresh sessions with the skill on and off; `claude plugin eval` ([[plugins]]) automates this.
- **Not triggering:** put the words users say in `description`, ask Claude "What skills are available?", or invoke it with `/skill-name`. Malformed YAML loads the body with empty metadata; run with `--debug`, or `claude plugin validate .claude/skills`.
- **Triggers too often:** narrow the description or set `disable-model-invocation: true`.
- **Personal skills gone:** look in `~/.claude/skills/.trash/` and move the folder back within 30 days.
