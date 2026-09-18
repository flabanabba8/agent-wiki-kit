---
title: Sessions and Checkpoints
type: how-to
tldr: "Resume, name, branch, rewind, transcripts"
sources:
  - raw/docs/official/sessions.md
  - raw/docs/official/checkpointing.md
related: ["[[context-window]]", "[[worktrees-and-background-work]]", "[[headless-mode]]", "[[permissions-and-modes]]", "[[cli-reference]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [resume-session, continue-conversation, rewind, checkpoints, fork-session]
---

# Sessions and Checkpoints

A **session** is a saved conversation tied to a project directory. The CLI writes it continuously to a local transcript, so you can close the terminal, run `/clear`, or crash, and then pick up where you left off. **Checkpoints** are automatic snapshots of Claude's file edits, one per prompt, that let you rewind code, conversation, or both. The desktop app, the web, and the VS Code extension keep their own session history; this page covers the CLI.

## Resume a session

| Command | What it does |
|:--|:--|
| `claude --continue` | Reopen the most recent conversation in the current directory |
| `claude --resume` | Open the session picker |
| `claude --resume <name>` | Resume a named session (opens the picker if the name is ambiguous) |
| `claude --resume <session-id>` | Resume by ID, from any directory on this machine |
| `claude --resume <transcript-path>` | Resume from an absolute `.jsonl` path |
| `claude --from-pr <number>` | Picker filtered to sessions linked to that pull request |
| `/resume [name]` | Switch conversations from inside a session |

Sessions created with `claude -p` or the Agent SDK are hidden from the picker and from `claude --continue`; resume them by ID. Sessions whose first prompt was `/loop` are hidden too. `claude --continue` won't attach to a background session that is still running; use `claude agents` for that (see [[worktrees-and-background-work]]).

**What comes back on resume:**

- Full history, including tool calls. A tool that was mid-run when the process died doesn't re-run.
- The model the session was using, unless `--model`, `ANTHROPIC_MODEL`, or a pinned-family variable picks one, or the model is retired or excluded by `availableModels`.
- An `--agent` selection, an active goal, and unexpired scheduled tasks.
- The permission mode, when you resume from a terminal with `--continue` or an exact `--resume`. Exceptions: `bypassPermissions` and `plan` sessions start in the normal starting mode, and `auto` returns only if you still qualify. The picker and `/resume` don't restore the stored mode. See [[permissions-and-modes]].

**What doesn't come back:** background Bash and monitor tasks. Also the launch flags `--mcp-config`, `--settings`, `--plugin-dir`, `--fallback-model`, and `--add-dir` (pass them again) and directories added with `/add-dir`. Settings files are re-read, so configuration stored there needs nothing extra.

**Resume from summary.** On Pro and Max, resuming a session idle for more than about an hour and larger than 100,000 tokens opens a dialog, because the prompt cache has expired and the next request reprocesses everything once.

- **Resume from summary** runs `/compact` so later requests carry a summary.
- **Resume full session as-is** keeps every detail at full per-request cost.
- **Don't ask me again** stops the dialog from appearing.

## The session picker

Rows show the session name, AI-generated title, or first prompt, plus age, git branch, and size.

| Key | Action |
|:--|:--|
| `Enter` / `Space` | Resume / preview |
| `Ctrl+R` | Rename the highlighted session |
| `/` or typing | Search; paste a GitHub, GitLab, or Bitbucket PR/MR URL to find the session that created it |
| `Ctrl+W` | Widen to all worktrees of this repository |
| `Ctrl+A` | Widen to every project on this machine |
| `Ctrl+B` | Filter to the current git branch |
| `→` / `←` | Expand or collapse grouped entries |

A session from another worktree resumes in place. For an unrelated project, the picker copies a `cd` plus resume command to your clipboard instead.

## Name your sessions

Named sessions are easy to find and resume. Name one at startup with `claude -n auth-refactor`, during a session with `/rename auth-refactor` (the name shows on the prompt bar), or from the picker with `Ctrl+R`. Accepting a plan in plan mode titles an unnamed session from the plan. Unnamed sessions get a generated title from the first prompt, and that title also works with `--resume`. The default display name, such as `my-app-3f`, is not a resume handle. If you pick a name another live session already uses, Claude Code appends a two-word suffix to yours.

## Branch a session

`/branch [name]` copies the conversation so far into a new session and switches you into it, leaving the original untouched. From the shell, add `--fork-session`:

```bash
claude --continue --fork-session
```

- **Permissions:** an in-process `/branch` keeps your "allow for this session" grants. A `--fork-session` process starts without them.
- **Background work:** running background subagents and Bash commands keep running, and their output lands in the branch.
- **Remote Control:** connected clients follow you into the branch.
- **Concurrent use:** resuming one session in two terminals without forking interleaves both into a single transcript.

## Checkpoints and `/rewind`

Every prompt that starts a turn creates a checkpoint of the files Claude's editing tools touched. Snapshots are kept for the 100 most recent checkpoints, survive resume, and are swept with other session data after about 30 days (`cleanupPeriodDays`).

Open the rewind menu with `/rewind` (aliases `/checkpoint`, `/undo`) or `Esc` `Esc` on an empty prompt. Pick a prompt, then an action:

| Action | Effect |
|:--|:--|
| Restore code and conversation | Revert both to that point |
| Restore conversation | Rewind messages, keep current files |
| Restore code | Revert files, keep the conversation |
| Summarize from here | Compress this point onward into a summary |
| Summarize up to here | Compress everything before this point, keep later messages |
| Never mind | Exit without changes |

Summarizing doesn't touch files. To steer a summary, highlight a Summarize option and type instructions in its **add context (optional)** field. After restoring the conversation, the original prompt comes back into the input so you can edit and resend it. If you ran `/clear` earlier in the same process, the top entry `/resume <session-id> (previous session)` returns to the cleared conversation.

**Checkpoints don't capture:**

- Files changed by Bash commands (`rm`, `mv`, `cp`, scripts)
- Edits by subagents, except a foreground forked skill; revert those with git
- Changes made outside Claude Code or by other sessions
- Messages you queued that joined a running turn; rewind to the prompt that started the turn
- Symlinked or hard-linked files, which are skipped with a `Restored the code, but skipped N files` warning

Checkpoints are session-level undo, not version control. Keep committing with git.

## Managing context inside a session

- `/clear` starts an empty context and saves the old conversation for `/resume`.
- `/compact [instructions]` replaces history with a focused summary.
- `/context` shows what is using space.

When to use which is covered in [[context-window]].

## Export and storage

- **Human-readable copy:** `/export [filename]` copies or saves the conversation as plain text.
- **For scripts:** use `claude -p --output-format json`, or send a follow-up to an existing session:

  ```bash
  claude -p --resume <session-id> --output-format json "summarize what we changed" | jq -r '.result'
  ```

  Hooks and status line commands also receive a `transcript_path` field. See [[headless-mode]].
- **Location:** transcripts are JSONL at `~/.claude/projects/<project>/<session-id>.jsonl`, where `<project>` is the working directory path with non-alphanumerics replaced by `-`. The line format is internal and changes between releases, so don't parse it directly.

| To | Set |
|:--|:--|
| Move storage off `~/.claude` | `CLAUDE_CONFIG_DIR` |
| Choose the `<project>` directory name (requires `CLAUDE_CONFIG_DIR`) | `CLAUDE_CODE_PROJECT_DIR_NAME` |
| Change the 30-day retention | `cleanupPeriodDays` in settings |
| Stop writing transcripts | `CLAUDE_CODE_SKIP_PROMPT_HISTORY` |
| Skip persistence for one `-p` run | `--no-session-persistence` |

To delete a project's transcripts and related state early, run `claude project purge`. All session flags are listed in [[cli-reference]].
