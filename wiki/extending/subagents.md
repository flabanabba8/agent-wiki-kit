---
title: Subagents
type: reference
tldr: "Built-in and custom subagents, frontmatter"
sources:
  - raw/docs/official/sub-agents.md
  - raw/docs/official/agents.md
  - raw/docs/official/features-overview.md
  - raw/docs/official/hooks.md
related: ["[[agent-teams]]", "[[skills]]", "[[hooks]]", "[[models-and-effort]]", "[[workflows]]", "[[permissions-and-modes]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [custom-agents, agent-tool, forked-subagent, claude-agents-directory]
---

# Subagents

A subagent is a specialized Claude worker that runs in its own context window with its own system prompt, tool access and permissions. Claude delegates a task to it through the Agent tool, the subagent does the work, and only its summary returns to your conversation.

## When to use one

- **Use a subagent** when a side task would flood the conversation with search results, logs or file contents you won't reference again, when you want to enforce tool restrictions, or when the work is self-contained. Define a custom one when you keep spawning the same kind of worker.
- **Stay in the main conversation** for iterative back-and-forth, for phases that share a lot of context, and for quick targeted changes. A non-fork subagent starts fresh and must gather context.
- **Use a skill** for reusable instructions that run in the main context ([[skills]]); use `/btw` for a quick question about what is already in context.
- For many parallel sessions, coordinated teammates or scripted fan-out, see [[worktrees-and-background-work]], [[agent-teams]] and [[workflows]].

## Built-in subagents

| Agent | Model | Tools and purpose |
| :-- | :-- | :-- |
| Explore | Inherits the main model, capped at Opus on the Claude API | Read-only codebase search. Claude picks a thoroughness: quick, medium or very thorough |
| Plan | Inherits the main model | Read-only research during plan mode |
| general-purpose | Follows the model order below | Every tool available to subagents; exploration plus changes |
| claude | Follows the model order below | Catch-all when no specialist fits; default agent for dispatched background sessions |
| statusline-setup | Sonnet | Runs for `/statusline` |
| claude-code-guide | Haiku | Answers questions about Claude Code |

Explore and Plan skip CLAUDE.md files and the parent's git status, and they are one-shot: they return no agent ID, so they can't be resumed. A user or project subagent named `Explore` replaces the built-in one; give it `model: haiku` to keep exploration cheap.

To restrict built-ins, add `Agent(Explore)` to `permissions.deny`, deny `Agent` entirely, set `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` to remove only Explore and Plan, or set `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1` in non-interactive and SDK runs to remove all built-in types.

## Where definitions live

| Location | Scope | Priority |
| :-- | :-- | :-- |
| `.claude/agents/` in the managed settings directory | Organization | 1 (highest) |
| `claude --agents '<json>'` | Current session | 2 |
| `.claude/agents/` | Current project | 3 |
| `~/.claude/agents/` | All your projects | 4 |
| Plugin `agents/` directory | Where the plugin is enabled | 5 (lowest) |

- Directories are scanned recursively; identity comes only from the `name` field. Across nested project directories, the definition closest to the working directory wins. Keep names unique within one directory, because duplicates load in filesystem order.
- In a plugin, a subfolder becomes part of the scoped name: `agents/review/security.md` in `my-plugin` is `my-plugin:review:security`.
- Plugin subagents ignore `hooks`, `mcpServers` and `permissionMode`. Copy the file into `.claude/agents/` if you need them.
- Claude Code watches `~/.claude/agents/` and `.claude/agents/` and picks up edits within seconds. Restart after creating a scope's first `agents` directory, after editing agents in an `--add-dir` directory, or in sessions started with `--disable-slash-commands`.
- To create one, ask Claude to write the file or write it yourself; `/agents` only prints a reminder of these locations.

## File format

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices. Use after code changes.
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer. Analyze the code and give specific, actionable feedback.
```

The body becomes the system prompt. A subagent receives that prompt plus environment details, not the Claude Code system prompt. In non-interactive runs, `--append-subagent-system-prompt` (or `--append-subagent-system-prompt-file`) appends text to every non-fork subagent's prompt.

Claude Code silently skips a file with no `name`, with an opening `---` that isn't the first line, with a `name` starting with `-` or containing `:`, with a `name` but no `description`, or with YAML that doesn't parse. `claude plugin validate .claude/agents` finds parse errors before a session.

## Frontmatter reference

Only `name` and `description` are required.

| Field | Description |
| :-- | :-- |
| `name` | Unique lowercase-and-hyphen identifier. Hooks receive it as `agent_type`. No `:` |
| `description` | When Claude should delegate. Combined descriptions over 15,000 tokens trigger a startup warning |
| `tools` | Allowlist. Inherits every tool available to subagents if omitted |
| `disallowedTools` | Denylist, applied before `tools`. A specifier such as `Bash(git push *)` still removes the whole tool |
| `model` | `sonnet`, `opus`, `haiku`, `fable`, a full model ID, or `inherit` |
| `permissionMode` | `default` (alias `manual`), `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions` or `plan` |
| `maxTurns` | Turn cap; output at the cap is marked partial and the subagent can be resumed |
| `skills` | Skills whose full content is preloaded at startup |
| `mcpServers` | Server names to reuse, or inline server definitions scoped to this subagent |
| `hooks` | Hooks active only while this subagent runs; `Stop` becomes `SubagentStop` |
| `memory` | Persistent memory scope: `user`, `project` or `local` |
| `background` | `true` keeps it in the background even when Claude asks for the foreground |
| `omitClaudeMd` | `true` skips user, project and local CLAUDE.md files |
| `effort` | `low`, `medium`, `high`, `xhigh` or `max` |
| `isolation` | `worktree` runs it in a temporary git worktree branched from your default branch, removed if unchanged |
| `color` | `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink` or `cyan` |
| `initialPrompt` | First user turn, auto-submitted when the agent runs as the main session |
| `experimental` | Map; `cacheTtl: 5m` or `1h` sets this subagent's prompt cache lifetime |

The `--agents` JSON takes a `prompt` field for the system prompt plus `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `mcpServers`, `hooks`, `maxTurns`, `skills`, `initialPrompt`, `memory`, `effort`, `background`, `omitClaudeMd` and `isolation`.

## Model selection order

Claude Code picks a subagent's model from the first source that applies:

1. The per-invocation `model` parameter Claude passes to the Agent tool (kept when the subagent is resumed).
2. The definition's `model` field, where `inherit` means the main conversation's model.
3. `CLAUDE_CODE_SUBAGENT_MODEL`, when set to an alias or model ID.
4. The main conversation's model.

Every value is checked against the organization's `availableModels` allowlist; a blocked family alias runs on the newest permitted version of that family, and other blocked values fall back to the inherited model. `CLAUDE_CODE_SUBAGENT_MODEL` alone does not move Explore or Plan. Add `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` to apply one model to every subagent, teammate and workflow agent, ignoring definitions and per-call values; forks and `context: fork` skills with `model: inherit` still use the main model. `/tasks` shows the model each running subagent uses. Subagents inherit the session's extended-thinking setting, and their context window is sized by their own model. Model aliases and effort are covered in [[models-and-effort]].

## Tools and permissions

Every subagent loses `AskUserQuestion`, `EndConversation`, `EnterPlanMode`, `ExitPlanMode` (unless its mode is `plan`), `ScheduleWakeup`, `TaskOutput`, `WaitForMcpServers` and `Workflow`, plus `Agent` at the depth limit. A background subagent keeps every MCP tool but only these built-ins: `Read`, `Grep`, `Glob`, `Bash`, `PowerShell`, `Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`, `TodoWrite`, `Skill`, `ToolSearch`, `EnterWorktree`, `ExitWorktree`, `Monitor`, `TaskStop`, `SendMessage` and `Artifact`. Forks skip both filters. `tools` and `disallowedTools` accept `mcp__<server>` patterns. If nothing in `tools` resolves, the subagent fails to launch.

`Agent(worker, researcher)` in `tools` limits which types an agent can spawn, but only for an agent running as the main thread with `claude --agent`.

With `permissionMode` unset, a subagent inherits the main conversation's mode. If the main conversation is in `bypassPermissions`, `acceptEdits` or `auto`, that mode wins and the field is ignored. In `default`, `dontAsk` or `plan`, the field applies, except that a subagent can't declare `bypassPermissions`. See [[permissions-and-modes]].

## Skills, MCP, memory and hooks

- **`skills`** injects full skill content at startup. Unlisted skills stay reachable through the Skill tool; remove `Skill` from `tools` to block that. Skills with `disable-model-invocation: true` can't be preloaded.
- **`mcpServers`** inline servers connect when the subagent starts and disconnect when it finishes, keeping their tool descriptions out of the main context. Inline servers from a project agent file load only after you trust that folder. Managed MCP policy applies ([[mcp]]).
- **`memory`** gives a persistent directory: `~/.claude/agent-memory/<name-of-agent>/` (`user`), `.claude/agent-memory/<name-of-agent>/` (`project`, the recommended default) or `.claude/agent-memory-local/<name-of-agent>/` (`local`). The prompt includes the first 200 lines or 25KB of its `MEMORY.md`, and Read, Write and Edit are enabled. It does nothing when auto memory is off.
- **`hooks`** in frontmatter run only while the subagent is active, and for project agents only after you accept workspace trust. Settings hooks also fire inside subagents, and `SubagentStart`/`SubagentStop` match on agent type. Schemas are on [[hooks]].

## Invoke explicitly

- **Natural language:** "Use the code-reviewer subagent to look at my changes."
- **@-mention:** pick the agent from the `@` typeahead, or type `@agent-<name>`. This guarantees that subagent runs.
- **Whole session:** `claude --agent code-reviewer`, or `"agent": "code-reviewer"` in `.claude/settings.json`. Its prompt replaces the default system prompt, CLAUDE.md still loads, and the choice persists on resume.

## Foreground, background and forks

Claude Code chooses per spawn: subagents of an in-process teammate run in the foreground, `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` forces the foreground, and otherwise subagents run in the background. With fork mode on, which is the default in interactive sessions, Claude can't request the foreground. With fork mode off, the default in `-p` and the SDK, Claude runs a subagent in the foreground when it needs the result. Press Ctrl+B to background a running task. Background permission prompts surface in your main session, naming the subagent.

A **fork** inherits the whole conversation, system prompt, tools and model, and shares the parent's prompt cache, so it is cheaper than a fresh subagent when the task needs the same context. Start one with `/subtask <task>`; Claude requests the `fork` type itself when fork mode is on. `CLAUDE_CODE_FORK_SUBAGENT=1` turns fork mode on in `-p` and the SDK, and `0` turns it off everywhere. Deny `Agent(fork)` to block forks. A fork can't spawn forks.

## Nesting and limits

- Subagents can nest up to three layers below the main conversation. Set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` to change the depth; `1` disables nesting.
- Spawning fails with `Concurrent subagent limit reached` when 20 are running. Change it with `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`.
- Subagents auto-compact like the main conversation.

## Context, resume and output

A non-fork subagent starts with its system prompt, Claude's delegation message, the CLAUDE.md hierarchy (except Explore, Plan and `omitClaudeMd`), a git status snapshot, preloaded skills, and a roster of other named agents it can message. It never gets your conversation history, output style or auto memory, so restate rules it must follow in the delegation prompt.

To continue a finished subagent, ask Claude to resume it; Claude sends `SendMessage` to the agent's ID or name, and the subagent keeps its full history. Transcripts live at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl` and are deleted after `cleanupPeriodDays` (30 days by default).

Claude Code scans each final report before Claude reads it, escaping text that imitates harness tags and prepending a `[harness: subagent output matched instruction-shaped pattern(s):` marker line when needed. No message from any agent counts as your approval for a permission prompt.
