---
title: Agent Teams
type: how-to
tldr: "Coordinated Claude sessions led by one lead"
sources:
  - raw/docs/official/agent-teams.md
  - raw/docs/official/agents.md
  - raw/docs/official/costs.md
  - raw/docs/official/sub-agents.md
  - raw/docs/official/hooks.md
related: ["[[subagents]]", "[[hooks]]", "[[multi-agent-systems]]", "[[worktrees-and-background-work]]", "[[costs-and-usage]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [teammates, team-lead, claude-code-experimental-agent-teams, teammate-mode]
---

# Agent Teams

An agent team is a group of Claude Code sessions working together. One session is the **team lead**: it spawns teammates, assigns tasks and synthesizes results. **Teammates** are separate Claude Code instances, each with its own context window, that message each other directly and share a task list. You can talk to any teammate without going through the lead. Agent teams are experimental and disabled by default.

## When to use a team

Teams pay off when parallel exploration adds real value and teammates can work independently:

- Research and review, where teammates investigate different angles and challenge each other's findings
- New modules or features, where each teammate owns a separate piece
- Debugging with competing hypotheses tested in parallel
- Cross-layer changes, with frontend, backend and tests owned by different teammates

For sequential work, same-file edits or tightly coupled tasks, a single session or [[subagents]] is more effective.

| | Subagents | Agent teams |
| :-- | :-- | :-- |
| Context | Own window; results return to the caller | Own window; fully independent |
| Communication | Report back to the caller | Teammates message each other directly |
| Coordination | Main agent manages all work | Shared task list plus messages |
| Token cost | Lower: results summarized back | Higher: each teammate is a full instance |

## Enable teams

Set the variable in your environment or in `settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Teammates spawn only in interactive sessions. In `-p` runs and the Agent SDK, Claude doesn't spawn teammates.

While teams are enabled, any subagent Claude spawns from the main conversation with a `name` launches as a teammate, unless the call is a fork or passes `isolation` on the call itself. Claude names subagents on its own, so teams can form when you didn't ask for one. Set the variable to `0` to get ordinary subagents back; the change applies to the next spawn without a restart. A value of `1` in project, local, `--settings` or managed settings overrides a `0` in user settings.

## Start a team

Describe the task and the teammates you want:

```text
I'm designing a CLI tool that tracks TODO comments across a codebase. Spawn three
teammates to explore it: one on UX, one on technical architecture, one playing
devil's advocate.
```

If Claude uses subagents instead, ask again and explicitly request an agent team. Teammates appear in the agent panel below the prompt:

- **Up/Down** selects a teammate; **Enter** opens its transcript so you can message it; **Escape** clears the selection or interrupts the viewed teammate's turn.
- Press `x` on a selected teammate to stop it, and Ctrl+T to toggle the task list.
- Once every agent is idle, idle rows hide after 30 seconds. More than three idle teammates collapse into one `N idle agents` row. Hidden teammates keep running and stay addressable by name.

While you view a teammate, plain text and skills go to that teammate, but built-in commands run in the lead. `/model` and `/fast` change only the lead; `/effort` affects the viewed teammate's later turns.

## Display modes

- **In-process** (default): all teammates run in your terminal. Works anywhere.
- **Split panes**: each teammate gets its own pane. Requires tmux, or iTerm2 with the `it2` CLI and the Python API enabled. Not supported in VS Code's integrated terminal, Windows Terminal or Ghostty.

Set `teammateMode` in `~/.claude/settings.json` to `"in-process"`, `"auto"` (split panes when inside tmux or iTerm2 with `it2`), `"tmux"` (split panes, detecting tmux or iTerm2) or `"iterm2"`. For one session, pass `claude --teammate-mode auto`.

## Models, roles and definitions

Claude Code picks each teammate's model from the first source that applies:

1. The model your spawn prompt names for that teammate
2. The `model` of the subagent definition the teammate was spawned from (`inherit` means the lead's model)
3. `CLAUDE_CODE_SUBAGENT_MODEL`, unless set to `inherit`
4. The lead's current model

`CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` skips the first two sources. Teammates inherit the lead's effort level. The full subagent order is on [[subagents]].

To define a reusable role, write a subagent definition and name it in the spawn prompt: "Spawn a teammate using the security-reviewer agent type to audit the auth module." Claude Code applies parts of the definition:

- **`tools`** limits the teammate's tools. In-process teammates also get `SendMessage` and, where available, the task tools.
- **`model`** applies when the spawn prompt names no model.
- **Body** is appended to an in-process teammate's system prompt and replaces a split-pane teammate's prompt.
- **`skills`** is not applied; teammates load skills from project and user settings.
- **`mcpServers`** applies only to split-pane teammates; an in-process teammate loads MCP servers from your project and user settings instead.

When Claude messages an in-process teammate that has stopped, Claude Code brings it back in the same session, restores the conversation saved for it and hands it the message as its next prompt. A definition from a project's `.claude/agents/` or an `--add-dir` directory is re-applied only if you have trusted the folder the agent file sits in — trusting a parent folder doesn't count — and until then the teammate returns with none of its tools or instructions, keeping only what every in-process teammate gets.

## Tasks, messages and plans

- **Task list.** The lead creates tasks and teammates work through them. Tasks are pending, in progress or completed, and can depend on other tasks. The lead can assign a task, or a teammate self-claims the next unassigned, unblocked one. File locking prevents double claims.
- **Messaging.** Messages arrive automatically, so the lead doesn't poll. When a teammate stops, it notifies the lead with its final answer. Message one teammate by name; there is no broadcast, so everyone gets one message per recipient. Name teammates in your spawn prompt to reference them later.
- **Plans.** A teammate spawned while the lead is in plan mode works read-only until its plan is ready, then sends an approval request that the lead grants automatically.
- **Shutdown.** "Ask the researcher teammate to shut down." The teammate can approve or reject with an explanation. Shared team directories are cleaned up when the session ends.

Teammates load CLAUDE.md, MCP servers and skills like a normal session, plus the spawn prompt, but not the lead's conversation history. Put task-specific detail in the spawn prompt.

## Permissions

Teammates start in the lead's permission mode, except `dontAsk`, which they don't inherit. If the lead runs with `--dangerously-skip-permissions`, so do all teammates. You can change one teammate's mode after it spawns, not at spawn time. Teammate permission prompts appear in the lead session. A message from another agent never counts as your approval, and in auto mode the classifier reviews every inter-agent message before delivery. See [[permissions-and-modes]].

## Quality gates with hooks

- `TeammateIdle`: exit 2 sends feedback and keeps the teammate working.
- `TaskCreated`: exit 2 rolls back the task and returns the message.
- `TaskCompleted`: exit 2 keeps the task open, for example until tests pass.

Payloads and decision fields are on [[hooks]].

## Where state lives

Each session has exactly one team, named `session-` plus the first eight characters of the session ID. Claude Code creates and updates it automatically.

- Team config: `~/.claude/teams/{team-name}/config.json`, holding a `members` array; removed when the session ends. Don't edit it; runtime updates overwrite changes. A project file such as `.claude/teams/teams.json` is not recognized.
- Mailboxes: `~/.claude/teams/{team-name}/inboxes/{agent-name}.json`.
- Task list: `~/.claude/tasks/{team-name}/`, kept locally for resumed sessions and swept by `cleanupPeriodDays`.

## Practical guidance

- **Size:** start with 3 to 5 teammates; three focused teammates often beat five scattered ones. Aim for 5 to 6 tasks per teammate, each a self-contained deliverable.
- **Files:** two teammates editing one file overwrite each other. Teams don't isolate teammates in worktrees, so give each teammate its own set of files ([[worktrees-and-background-work]]).
- **Start with research and review** before parallel implementation.
- **Steer:** check progress and redirect. If the lead starts implementing instead of waiting, tell it: "Wait for your teammates to complete their tasks before proceeding."
- **Cost:** token use grows roughly linearly with active teammates. Use Sonnet for teammates, keep spawn prompts focused and shut teammates down when done. An in-process teammate's prompt cache lasts five minutes by default; `subagentPromptCacheTtl` set to `1h` keeps it for an hour at a higher write rate ([[costs-and-usage]]).
- **Permission friction:** pre-approve common operations before spawning.

## Limitations

- `/resume` and `/rewind` don't restore in-process teammates, and after a resume Claude can't bring one back by messaging it either; spawn new ones instead.
- Task status can lag and block dependent tasks; check the work and update the status or nudge the teammate.
- Shutdown waits for the current request or tool call to finish.
- No nested teams: only the lead manages the team, and it can't hand off leadership.
- An in-process teammate's own subagents run in the foreground; a definition with `background: true` errors.
- Teammates may stop early after errors. Open the teammate and give instructions, or spawn a replacement.
- If a tmux session outlives the team, find it with `tmux ls` and end it with `tmux kill-session -t <session-name>`.

For the research on when multi-agent setups help or fail, see [[multi-agent-systems]].
