---
title: Claude Code Overview
type: concept
tldr: "What Claude Code is and where it runs"
sources:
  - raw/docs/official/overview.md
  - raw/docs/official/platforms.md
  - raw/docs/official/quickstart.md
  - raw/docs/official/setup.md
  - raw/docs/official/claude-projects.md
related: ["[[install-and-setup]]", "[[how-claude-code-works]]", "[[prompting-and-workflows]]", "[[claude-md-and-memory]]", "[[cli-reference]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [what-is-claude-code, claude-code-intro, claude-code-surfaces, getting-started-with-claude-code]
---

# Claude Code Overview

Claude Code is Anthropic's agentic coding tool. It reads your codebase, edits files, runs commands, and connects to your development tools. It works across many files and tools at once, so it can build features, fix bugs, write tests, resolve merge conflicts, write commits and PRs, and automate chores. It isn't limited to code: it can do anything you can do from a command line, such as writing docs, running builds, or searching and reorganizing a notes folder.

Every surface runs the same engine. Your repo's CLAUDE.md files, settings, and MCP servers work in all of them. For how the engine works (the agentic loop, tools, and context), see [[how-claude-code-works]].

## What you need

- **An account.** You need a Claude Pro, Max, Team, or Enterprise subscription, or a Claude Console account. The free claude.ai plan doesn't include Claude Code.
- **Or a cloud provider.** The terminal CLI, VS Code, and JetBrains also work through Amazon Bedrock, Google Cloud's Agent Platform, or Microsoft Foundry (see [[cloud-providers]]).
- **The desktop app** needs a paid subscription. It bundles Claude Code, so you don't install the CLI separately.

Install steps, login, and updates are covered in [[install-and-setup]].

## Surfaces at a glance

| Surface | Best for | Notes | Details |
|---|---|---|---|
| Terminal CLI | Terminal workflows, scripting, remote servers | The most complete surface. Scripting (`claude -p`) and the Agent SDK are CLI-only | [[cli-reference]], [[headless-mode]] |
| VS Code (and Cursor) | Working inside the editor | Inline diffs, @-mentions, plan review, conversation history | [[ide-integrations]] |
| JetBrains IDEs | IntelliJ, PyCharm, WebStorm, and others | Diff viewer and selection sharing. Needs the CLI installed separately | [[ide-integrations]] |
| Desktop app | Visual review, parallel sessions | Diff viewer, app preview, scheduled tasks. Computer use and Dispatch on Pro and Max | [[desktop-app]] |
| Web (claude.ai/code) | Long tasks that need little steering, repos you don't have locally | Cloud sessions keep running after you disconnect | [[claude-code-on-the-web]] |
| Mobile (Claude app for iOS and Android) | Starting and monitoring tasks away from your desk | Thin client for cloud sessions, Remote Control, and Dispatch | [[claude-code-on-the-web]] |

For a longer body of work, a **project** is one conversation in which Claude coordinates parallel cloud sessions that share repositories, instructions and memory, and reports back ([[claude-projects]]).

You can mix surfaces on the same project. Configuration, project memory, and MCP servers are shared across the local surfaces.

## Integrations

| Integration | What it does | Details |
|---|---|---|
| Claude in Chrome | Controls your browser with your logged-in sessions to test web apps and fill forms | [[chrome-and-computer-use]] |
| GitHub Actions / GitLab CI/CD | Runs Claude in CI for PR review, issue triage, and maintenance | [[ci-cd-and-code-review]] |
| Code Review | Reviews every PR automatically | [[ci-cd-and-code-review]] |
| Slack / Claude Tag | `@Claude` in channels turns bug reports into PRs | [[slack-and-claude-tag]] |
| MCP servers | Connect Jira, Google Drive, Notion, databases, or internal APIs | [[mcp]] |

## Work when you're away from the terminal

| Option | Trigger | Runs on | Details |
|---|---|---|---|
| Remote Control | Drive a running session from claude.ai/code or the mobile app | Your machine | [[claude-code-on-the-web]] |
| `claude --cloud` / `claude --teleport` | Send a task to the cloud, or pull a cloud session into your terminal | Anthropic cloud | [[claude-code-on-the-web]] |
| Channels | Push events from Telegram, Discord, iMessage, or your own webhooks | Your machine (CLI) | [[channels]] |
| Routines | A schedule, an API call, or a GitHub event | Cloud, even with your computer off | [[routines-and-scheduling]] |
| `/loop`, desktop scheduled tasks | Repeating prompts | Your machine | [[routines-and-scheduling]] |
| Background agents (`claude agents`) | Several full sessions watched from one screen | Your machine | [[worktrees-and-background-work]] |

## What it looks like

```bash
cd your-project
claude                                                  # interactive session
claude "write tests for the auth module, run them, and fix any failures"
tail -200 app.log | claude -p "Slack me if you see any anomalies"
git diff main --name-only | claude -p "review these changed files for security issues"
```

Claude Code follows the Unix philosophy: pipe logs into it, chain it with other tools, or run it in CI.

## Customize and extend

- **Instructions:** CLAUDE.md or AGENTS.md files, plus auto memory, carry project knowledge across sessions ([[claude-md-and-memory]]).
- **Skills:** package repeatable workflows such as a deploy or PR review ([[skills]]).
- **Hooks:** run shell commands at fixed points, such as formatting after each edit ([[hooks]]).
- **Subagents and teams:** delegate work to separate contexts ([[subagents]], [[agent-teams]]).
- **Plugins:** bundle all of the above for sharing ([[plugins]]).
- **Agent SDK:** build your own agents on Claude Code's tools ([[agent-sdk]]).

## Where to go next

1. [[install-and-setup]]: install, log in, and start a first session.
2. [[how-claude-code-works]]: the loop, the tools, and what Claude can access.
3. [[prompting-and-workflows]]: explore, plan, implement, commit, and verify.
4. [[claude-md-and-memory]] and [[context-window]]: the two things that most affect result quality.
5. [[permissions-and-modes]]: control what Claude can do without asking.
6. [[troubleshooting]] when something breaks.
