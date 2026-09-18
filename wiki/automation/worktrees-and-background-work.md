---
title: Worktrees and Background Work
type: how-to
tldr: "Parallel sessions: worktrees, agent view, --bg"
sources:
  - raw/docs/official/worktrees.md
  - raw/docs/official/agent-view.md
  - raw/docs/official/agents.md
  - raw/docs/official/cli-reference.md
related: ["[[subagents]]", "[[agent-teams]]", "[[workflows]]", "[[sessions-and-checkpoints]]", "[[hooks]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [git-worktrees, agent-view, claude-agents, background-sessions, parallel-sessions]
valid_until: 2027-03-15
---

# Worktrees and Background Work

Claude Code has two tools for running several sessions on one machine at once. A **git worktree** gives a session its own checkout so its edits don't collide with other sessions. **Agent view** (`claude agents`) is one screen where you dispatch, watch and attach to **background sessions** that keep running with no terminal attached. Agent view is a research preview.

Pick the approach by who coordinates the work:

| Approach | Use when |
|---|---|
| [[subagents]] | A side task would flood your main conversation; Claude delegates it and collects a summary |
| Agent view | You have several independent tasks to hand off and check back on later |
| [[agent-teams]] | Claude should split a project, assign pieces and keep workers in sync (experimental, off by default) |
| [[workflows]] | A script should hold the plan: dozens to hundreds of agents, cross-checked results |

Worktrees support all of these. `/batch` is a skill that splits one large change into 5 to 30 worktree-isolated subagents, each opening a pull request. Running many sessions multiplies token usage.

## Worktrees

### Start a session in a worktree

```bash
claude --worktree feature-auth     # or -w; omit the name for a generated one
claude --worktree "#1234"          # branch from a PR/MR number or URL -> .claude/worktrees/pr-1234
```

- The worktree goes in `.claude/worktrees/<name>/` on a new branch `worktree-<name>`. Add `.claude/worktrees/` to `.gitignore`.
- Interactive runs need workspace trust in that directory. `claude -p --worktree` skips the trust check.
- If you pass a name whose directory already exists, Claude Code opens that worktree instead of creating one.
- Mid-session, ask Claude to "work in a worktree" and it uses the `EnterWorktree` tool (`ExitWorktree` to leave). If Claude wants to enter a path outside `.claude/worktrees/`, you are always asked, and only `bypassPermissions` mode skips that prompt.
- A worktree is a fresh checkout, so install dependencies there. To copy gitignored files such as `.env` into each new worktree, list them in `.worktreeinclude` at the project root (`.gitignore` syntax; only files that are both matched and gitignored get copied).

### Base branch

Set `worktree.baseRef` in settings:

| Value | Branches from |
|---|---|
| `"fresh"` (default) | The remote default branch (`origin/HEAD`). Claude Code fetches it if it is more than 24 hours old, and falls back to local `HEAD` if there is no remote |
| `"head"` | Your current local `HEAD`, including unpushed commits. Use it when subagents must work on in-progress changes |

You can't set it to a branch name. To start from a specific branch, run `git worktree add ../dir existing-branch` and start `claude` in that directory.

### Isolation enforcement

While a session is in a worktree, Claude Code blocks four kinds of tool call, and the same checks apply to every subagent it spawns:
- `Edit`/`Write`/`NotebookEdit` calls that target the main checkout.
- Bash, PowerShell or Monitor commands whose working directory is (or can't be shown not to be) the main checkout.
- Git pointed at the main checkout (`git -C`, `--git-dir`, `GIT_DIR`, `GIT_WORK_TREE`, or `cd` then git).
- Commands whose git usage it can't verify from the command text. This check can't be turned off.

A worktree shares three things with the main checkout: the `.git` directory (so `git commit` works with the sandbox on), plugins installed at project scope, and "don't ask again" Bash approvals, which are saved to the main checkout's `.claude/settings.local.json`.

In [[hooks]], `${CLAUDE_PROJECT_DIR}` stays at the original project root. Read the `cwd` field of the hook input to get the worktree path.

### Subagents in worktrees

Ask Claude to "use worktrees for your agents", or add `isolation: worktree` to a custom subagent's frontmatter. Claude Code deletes a subagent worktree that finishes with no changes. One with changes stays until the periodic sweep can remove it without losing work.

### Cleanup

- **When you exit an interactive session**: a clean, unnamed worktree is removed together with its branch. A named session, or a worktree that holds work, asks whether to keep or remove it.
- **`-p` runs** never clean up. Run `git worktree remove <path>`, and if git says it is locked, run `git worktree unlock` first.
- **The periodic sweep** removes subagent and background-session worktrees older than `cleanupPeriodDays`. It skips any worktree with changes or unpushed commits, any worktree you made with `git worktree add`, and any worktree without Claude Code's marker. While an agent runs, Claude Code holds a `git worktree lock` on its worktree.
- When you resume a session, it returns to its worktree. If the worktree directory is gone, the session continues in the launch directory. `--fork-session` starts in the launch directory.

### Non-git VCS

For SVN, Perforce or Mercurial, configure `WorktreeCreate` and `WorktreeRemove` hooks. The create hook reads `name` from stdin JSON and prints the directory path it created. Claude Code does not process `.worktreeinclude` in that case. Have the hook create directories outside any git repository, or Claude Code refuses to use them.

### Common worktree errors

| Symptom | Fix |
|---|---|
| Git LFS files show up as pointer files | The repository's own filter drivers (for example from `git lfs install --local`) are skipped during creation. Run `git lfs pull` in the worktree |
| `Refusing to use <path> as an isolation worktree` | Follow the message's ending. The common case, `launch from the parent checkout`, means you should launch from the main checkout |
| Creation fails on a symlinked path | `.claude`, `.claude/worktrees` or the target is a symlink. Remove the symlink |

## Background sessions and agent view

### Get work into the background

| From | How |
|---|---|
| Shell | `claude --bg "investigate the flaky test"` (the prompt is positional; `--bg` can't be combined with `-p`). Add `--name`, `--agent code-reviewer`, `--model`, or `--resume <session-id>` |
| Shell, no model | `claude --bg --exec 'pytest -x'` runs a PTY-backed shell job |
| Inside a session | `/background` or `/bg` (optionally followed by a prompt), or `←` on an empty prompt |
| Copy of a session | `/fork` copies the conversation into a new background session while the original keeps going. `/subtask` starts a forked subagent instead |
| Agent view | Type a prompt and press `Enter`. Each prompt starts a new session |

Each background session is its own Claude Code process, run by a **supervisor** service. Sessions keep running after you close agent view or your shell, and they survive sleep. Shutting the machine down stops them. When you background a session, in-flight shell commands, background subagents, dynamic workflows and `/loop` tasks move with it. A running monitor can't move, so Claude Code shows a `Background this session?` dialog.

### File isolation

Before it edits files, a background session moves into its own worktree under `.claude/worktrees/`. It skips that step if it is already in a linked worktree, if the directory isn't a git repository and no `WorktreeCreate` hook is configured, or if the write is outside the working directory. To opt a repository out, set:

```json
{ "worktree": { "bgIsolation": "none" } }
```

In its worktree, Claude commits without asking and pushes when a remote exists. It may open a draft PR, and it never pushes to `main`/`master`, force-pushes or merges. Git instructions in your task or CLAUDE.md take precedence.

### Using agent view

```bash
claude agents                                   # all projects
claude agents --cwd ~/projects/my-app           # one project
claude agents --permission-mode plan --model opus --effort high   # dispatch defaults
```

Rows are grouped under Ready for review, Needs input, Working and Completed. States are Working, Needs input, Idle, Completed, Failed and Stopped. The icon shape shows whether the process is alive (`✻`), exited (`∙`), or a `/loop` sleeping between runs (`✢`).

| Key | Action |
|---|---|
| `Space` | Peek at the latest output or pending question, and reply inline |
| `Enter` / `→` | Attach to the full session (`←` on an empty prompt detaches) |
| `Ctrl+X` twice | Stop, then delete |
| `Ctrl+T` / `Ctrl+R` / `Ctrl+S` | Pin / rename / group by directory |
| `?` | Show all shortcuts |

In the dispatch input, `@<repo>` targets a child repository, a first word or `@name` that matches a subagent runs that subagent, `! <cmd>` starts a shell job, and a bare `/resume` brings back a past session. Filters include `s:blocked`, `a:<name>` and `#<PR>`. Detaching never stops a session. Run `/stop` inside it to end it.

A session dispatched from `claude agents` opened in a shell, or from `claude --bg`, starts the way a new `claude` in that directory would. `/bg` and `←` keep the session's current permission mode.

### Manage from the shell

| Command | Purpose |
|---|---|
| `claude agents --json [--all]` | Session list as JSON: `state` is `working`, `blocked`, `done`, `failed` or `stopped`. This is the supported interface; files under `~/.claude/jobs/` are not |
| `claude attach <id>` / `claude logs <id>` | Attach to a session / print its recent output |
| `claude stop <id>` / `claude respawn <id>` (`--all`) | Stop / restart onto the current binary |
| `claude rm <id>` | Remove a session. The worktree is kept if it has uncommitted changes or unpushed commits |
| `claude daemon status` / `claude daemon stop --any --keep-workers` | Inspect / restart a stalled supervisor without killing sessions |

Each session gets `CLAUDE_JOB_DIR`, and writes to `$CLAUDE_JOB_DIR/tmp` don't prompt. The supervisor stops a session's process after about an hour idle and unattached, and attaching starts it again from where it left off.

To turn agent view off, set `disableAgentView: true` or `CLAUDE_CODE_DISABLE_AGENT_VIEW`.

### Gotchas

- Deleting a session in agent view removes its Claude-created worktree, uncommitted changes included. Commit first.
- Each session draws on your subscription usage separately, so ten sessions use quota roughly ten times as fast.
- After a reboot, sessions show as failed (within 48 hours) or stopped. Attach or reply to resume them.
- `Could not resolve authentication method` on dispatch: run `claude daemon stop --any --keep-workers`, then dispatch again.

For resuming and naming sessions in general, see [[sessions-and-checkpoints]]. To run agents from a script instead, see [[headless-mode]].
