---
title: How Claude Code Works
type: concept
tldr: "Agentic loop, tools, access, sessions"
sources:
  - raw/docs/official/how-claude-code-works.md
  - raw/docs/official/features-overview.md
  - raw/docs/official/platforms.md
  - raw/docs/official/best-practices.md
related: ["[[overview]]", "[[context-window]]", "[[tools-reference]]", "[[sessions-and-checkpoints]]", "[[permissions-and-modes]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [agentic-loop, claude-code-architecture, agentic-harness, how-claude-code-works-internally]
---

# How Claude Code Works

Claude Code is an **agentic harness** around Claude. It supplies the tools, the context management, and the execution environment that turn a language model into a coding agent. The model reasons and the tools act. Everything below is the same on every surface ([[overview]]). Surfaces differ only in where code runs and how you interact.

## The agentic loop

A task moves through three phases that blend together: **gather context → take action → verify results**, repeated until the task is done.

- The loop adapts to the request. A question may only need context gathering. A bug fix cycles through all three phases many times. A refactor may lean heavily on verification.
- Claude chains dozens of actions, and each tool result shapes the next decision.
- You're part of the loop. Interrupt, redirect, or add context at any point.

For "fix the failing tests", Claude might run the suite, read the errors, search for the relevant source, read it, edit it, and run the tests again.

**Steering while it works:**

- `Esc` stops Claude immediately. The running tool call is canceled and queued messages are sent next.
- Typing a correction and pressing `Enter` sends it without stopping the current tool. Claude reads it once that action finishes.

## Models

Claude Code uses Claude models to read code in any language, understand how components connect, and plan multi-step changes. Switch with `/model` mid-session or `claude --model <name>` at launch. Aliases, effort levels, and defaults are in [[models-and-effort]].

## Tools

Without tools Claude can only produce text. The built-in tools fall into five categories:

| Category | What Claude can do |
|---|---|
| File operations | Read files, edit code, create files, rename and reorganize |
| Search | Find files by pattern, search content with regex, explore codebases |
| Execution | Run shell commands, start servers, run tests, use git |
| Web | Search the web, fetch documentation, look up error messages |
| Code intelligence | See type errors and warnings after edits, jump to definitions, find references (needs a code intelligence plugin) |

There are also orchestration tools for spawning subagents, asking you questions, and similar tasks. The full per-tool list, including which tools prompt for permission, is in [[tools-reference]].

**Extensions layer on top of the loop:** [[skills]] add knowledge and workflows, [[mcp]] connects external services, [[hooks]] automate fixed lifecycle points, and [[subagents]] take delegated work in their own context. [[plugins]] package these for sharing.

| Extension | Loads | Context cost |
|---|---|---|
| CLAUDE.md | Session start, full content | Every request |
| Skills | Descriptions at start, body when used | Low until used |
| MCP servers | Tool names at start, schemas on demand | Low until a tool is used |
| Subagents | When spawned | Isolated from the main session |
| Hooks | On trigger, run externally | Zero unless they return context |

## What Claude can access

When you run `claude` in a directory, Claude Code can reach:

- **Your project:** files in the directory and its subdirectories, plus files elsewhere with your permission.
- **Your terminal:** any command you could run, including build tools, git, package managers, and scripts.
- **Your git state:** current branch, uncommitted changes, and recent commits.
- **CLAUDE.md and auto memory:** persistent instructions and learned notes. The first 200 lines or 25KB of `MEMORY.md` load at session start ([[claude-md-and-memory]]).
- **Extensions you configured:** MCP servers, skills, subagents, and Claude in Chrome.

Because it sees the whole project, Claude makes coordinated edits across files, runs tests, and commits when asked. An inline assistant sees only the current file.

## Where code runs

| Environment | Where code runs | Use case |
|---|---|---|
| Local | Your machine | Default. Full access to your files, tools, and environment |
| Cloud | Anthropic-managed VMs, or self-hosted environments your org operates | Offload tasks, work on repos you don't have locally ([[claude-code-on-the-web]]) |
| Remote Control | Your machine, controlled from a browser or phone | Use the web UI while files and execution stay local |

## Session lifecycle at a glance

- **Saved locally.** Each message, tool use, and result is written to a plaintext JSONL file under `~/.claude/projects/`. Files are snapshotted before Claude edits them.
- **Independent.** Each new session starts with a fresh context window and no earlier conversation. Knowledge carries over only through CLAUDE.md and auto memory.
- **Tied to a directory.** `/resume` lists sessions from the current worktree by default. Switching git branches changes the files Claude sees but keeps the conversation. For parallel sessions, use git worktrees ([[worktrees-and-background-work]]).
- **Resume vs fork.** `claude --continue` and `claude --resume` reopen the same session ID and append to it. `--fork-session` and `/branch` copy the history into a new session ID and leave the original unchanged.
- **Context fills and compacts.** Conversation, file reads, command output, CLAUDE.md, and skills all share one window. As it nears the limit, Claude Code clears older tool outputs, then summarizes. Put durable rules in CLAUDE.md. Details are in [[context-window]].

Naming, the picker, and rewind are covered in [[sessions-and-checkpoints]].

## Safety: checkpoints and permissions

- **Checkpoints** make file edits reversible. Press `Esc` twice to rewind, or ask Claude to undo. They cover only file changes made through Claude's edit tools and are separate from git. Actions on remote systems (databases, APIs, deployments) can't be checkpointed.
- **Permission modes** decide what runs without asking. `Shift+Tab` cycles through them: **Auto** (a classifier blocks risky actions; the starting mode on Pro, Max, and Team for interactive terminal and VS Code sessions), **Manual** (asks before edits and shell commands), **Accept edits**, and **Plan** (explore and propose, no source edits). You can also allow specific commands in `.claude/settings.json`. See [[permissions-and-modes]] and [[sandboxing-and-security]].

## Working with it

- **It's a conversation.** Start with what you want and refine when the first attempt is off. You don't need to start over.
- **Delegate, don't dictate.** Give the symptom, the relevant area, and the goal. Claude chooses which files to read and which commands to run.
- **Ask Claude Code about itself.** Questions like "how do I set up hooks?" work. `/init` drafts a CLAUDE.md, and `/doctor` diagnoses setup problems.

Practical prompting patterns are in [[prompting-and-workflows]].
