---
title: Claude Projects
type: how-to
tldr: "One chat that runs parallel cloud threads"
sources:
  - raw/docs/official/claude-projects.md
  - raw/docs/official/claude-code-on-the-web.md
  - raw/docs/official/cloud-environments.md
  - raw/docs/official/mobile.md
  - raw/docs/official/platforms.md
related: ["[[claude-code-on-the-web]]", "[[routines-and-scheduling]]", "[[worktrees-and-background-work]]", "[[slack-and-claude-tag]]", "[[desktop-app]]", "[[agent-teams]]"]
created: 2026-09-25
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
valid_until: 2027-03-25
aliases: [projects, claude-code-projects, project-threads, coordinator-conversation, continue-as-a-project]
---

# Claude Projects

A project is one ongoing conversation where Claude acts as coordinator for a stream of related work: you send tasks, and it starts a **thread** for each. Threads are usually cloud sessions ([[claude-code-on-the-web]]) that run in parallel and keep going with your laptop closed; a thread that needs your computer can run there through Remote Control.

**Availability**: public beta on Pro and Max, rolling out gradually. Not on Team or Enterprise yet, and no organization-level controls during the beta. Projects live at claude.ai/code, the desktop app's Code tab ([[desktop-app]]) and the Claude mobile app, not in the terminal CLI or through Bedrock, Agent Platform or Foundry. The CLI's `claude project` command is unrelated.

## When to use one

Use a project when a goal outlasts one session and keeps producing tasks, such as one change across many repositories, a migration bigger than a session, or document work on uploaded files. Use something else for:

- One task that fits a session: a plain cloud session.
- Work where every task needs your machine: local sessions or agent view ([[worktrees-and-background-work]]).
- A recurring job with no conversation around it: a routine ([[routines-and-scheduling]]).
- Several people steering Claude together in Slack: Claude Tag ([[slack-and-claude-tag]]). A project belongs to one user and can't be shared.

## Parts of a project

- **Project conversation**: one long-running coordinator session. It sees what threads report, not each step, and works from recent messages, recent threads and project memory rather than its full history.
- **Threads**: separate sessions, each with its own context window, one piece of work, its own branch, and a pull request when the work calls for one. A permission prompt waits inside its thread; approving in the project conversation doesn't reach it.
- **Overview pane**: a **Threads** tab grouped as Ready for review, Waiting on you, Working, Landing, Idle and Resolved (threads auto-resolve after a week without activity), plus **Library** (uploaded and produced files), **Pull requests** and **Routines**.

## Create a project

Prerequisites for code work: repositories on github.com (not GitHub Enterprise Server, GitLab or Bitbucket), push access from your connected GitHub account, and the Claude GitHub App installed on each repository. A `/web-setup` token is not enough for project threads. Organizations that enforce SAML SSO need the Claude app authorized before their private repositories appear.

- **From scratch**: **Projects** → **New project** (or claude.ai/code/projects/browse). Only **Name** is required; **Goal** and **Context** (repositories, files, folders, Google Drive folders) are optional. On your first project Claude may take a turn right away, exploring the repository read-only or posting **Setup recommendations** (repositories, routines, threads) you confirm with **Update setup**.
- **From a cloud session**: **Continue as a project** creates a new project from the session; **Move to project** hands its work to an existing project. The original session stays in your list; a session mid-turn keeps running unless you started from the **Set up project** banner.

Before a first batch, write project instructions and send one small task to see how threads report.

## Standing context

| Context | Carries | Set it in |
|---|---|---|
| Project memory | Requirements, decisions and pitfalls as files; every cloud thread reads the `MEMORY.md` index at start | Ask Claude to remember or forget; **Project settings > Memory** |
| Project instructions | Text sent to each new thread and the coordinator, up to 16,000 characters | **Project settings > Memory > Project instructions** |
| Repositories, files, environment | Repos every thread clones, files under `/mnt/project-files`, the cloud environment | **Project settings > Environment**; **Library → Add** |

Project memory is separate from local auto memory and from repository `CLAUDE.md` files ([[claude-md-and-memory]]). Keep repo-specific rules in `CLAUDE.md` and project-wide notes in memory. Settings changes reach new threads only.

**Repositories**: add the one or two most tasks touch and name the rest in instructions; a thread can add another repository to itself mid-task (same prerequisites, same GitHub owner as existing ones, not inherited by later threads). With one repository, threads apply its `.claude/settings.json` permission rules, hooks and `env`; with several, threads start above the clones and read none of those, though `CLAUDE.md`, skills, agents and commands load from every repository. Repository-declared plugins never load: add them under **Project settings > Plugins**.

**Tools in threads**: cloud threads get nothing from your machine. Commit skills to a project repository, add plugins in project settings, use claude.ai connectors for MCP (the coordinator itself has none), and install CLI tools in the environment's setup script. Threads use a default Anthropic-hosted environment until you pick one; environment details are on [[claude-code-on-the-web]].

## Steering and pull requests

Claude routes each message: quick questions answered in place, new work to a new or matching thread, unrelated tasks to separate threads. Tell it how to run the project in plain words ("run at most two threads", "propose threads first", "don't open a PR until I've seen the plan"); it saves these to memory as preferences, not hard caps.

A cloud thread branches from the default branch, opens a pull request when asked or for a concrete fix, then watches it with auto-fix on, pushing CI fixes and answering review comments. Thread cards offer **Resolve conflicts**, **Fix CI**, **Address comments**, **Merge it**, **Review PR** and **Create PR**.

Models: a new project runs Opus everywhere, high effort for threads and low for the coordinator; change **Thread model/effort** and **Coordinator model/effort** in **Project settings > General**.

## Usage and limits

Projects draw on the same plan limits as other sessions, faster: each running thread is a full session, the coordinator spends tokens, and threads watching a PR wake on CI failures and comments. The hard cap is 200 new threads per day across projects. A thread at the plan limit waits and resumes when the limit resets (routine-started threads stop instead); usage credits extend it only if you enabled them ([[costs-and-usage]]). **Project settings > Usage** shows tokens by thread and model. An idle or archived project uses nothing.

**Pause** stops everything; **Archive** hides the project; **Delete** removes threads, memory and files but not pushed branches or PRs.

Other limits: running a thread on your machine needs Remote Control on that folder with Claude Code v2.1.280 or later, and fails while **Require trusted devices** is on. Cloud sandboxes pause between turns and may resume from a fresh clone, so ask Claude to commit and push long work. Threads can't move between projects.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Several threads guessed or stalled | Ask Claude to list each thread's assumptions, resolve bad ones, fix instructions or environment once, retry with one thread |
| "Claude hasn't responded" banner | **Restart Claude** on the banner or in **Project settings > General** |
| "Couldn't start the session — Claude doesn't have GitHub access…" | Install or relink the Claude GitHub App on that repository, then **Check again** |
