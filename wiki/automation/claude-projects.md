---
title: Projects
type: how-to
tldr: "One conversation coordinating cloud threads"
sources:
  - raw/docs/official/claude-projects.md
  - raw/docs/official/agents.md
related: ["[[claude-code-on-the-web]]", "[[routines-and-scheduling]]", "[[worktrees-and-background-work]]", "[[costs-and-usage]]", "[[claude-md-and-memory]]"]
created: 2026-09-19
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [claude-projects, project-threads, coordinate-cloud-sessions, claude-code-projects]
valid_until: 2027-03-15
---

# Projects

A **project** is one ongoing conversation in which Claude coordinates a stream of related work. You describe what needs doing; Claude starts a **thread** for each piece. Each thread is a cloud session — Claude Code running in Anthropic's cloud ([[claude-code-on-the-web]]) — with its own context window, branch and pull request. Threads run in parallel, keep going after you close the laptop, and report back to the conversation.

Projects are in public beta on Pro and Max, rolling out first to accounts that have used cloud sessions and have no existing projects in claude.ai chat or Cowork; they are not on Team or Enterprise yet. If **Projects** is missing from the sidebar at claude.ai/code or the desktop app's Code tab, the rollout hasn't reached you.

## When to use one

Parallelism isn't the point — several features give you that. In a project Claude starts and tracks the sessions, each from the same standing context, and the work lives in the cloud as long as it lasts.

Create one for a goal that outlasts a session and keeps producing tasks: one lint config across many services, an area you keep feeding bugs and stack traces, a migration, a document set you keep questioning. One task that fits in a session is just a cloud session you start yourself; work needing tools only your machine can reach belongs in a local session, or agent view for several at once ([[worktrees-and-background-work]]); a scheduled task with no conversation around it belongs in a routine of its own ([[routines-and-scheduling]]); and several people steering Claude together in Slack means Claude Tag ([[slack-and-claude-tag]]).

Threads work on github.com repositories and on files, folders and Google Drive folders you upload, never on anything that exists only on your machine. A project needs no repository at all: its threads still research, write documents, and write and run code in their own sandbox, delivering files to the **Library** tab.

## How a project is organized

The **project conversation** is one long-running session where Claude coordinates: it decides what becomes a thread and sees what threads report, not every step. **Threads** are the workers, one piece of work each. The **Overview pane** tracks them, with tabs for **Library** (files added and produced), **Pull requests** and **Routines**. Every thread starts with the project's repositories and files, its instructions and memory, each repository's `CLAUDE.md`, skills and plugins, your claude.ai connectors and a cloud environment — and nothing from your own machine.

## Create one

**Prerequisites.** Pro or Max with **Projects** in your sidebar. For code work: the repository on github.com (not GitHub Enterprise Server, GitLab or Bitbucket), push access from your connected GitHub account, and the Claude GitHub App installed on it — a `/web-setup` token suffices for ordinary cloud sessions but not for threads. Check the environment only if the work needs extra domains, a secret or a tool that isn't preinstalled.

GitHub setup is mostly one-time: connect your account once, and install the App per repository or for a whole organization, where only an owner can complete the install. Where an organization enforces SAML SSO, authorize the app for it too, or its private repositories never appear. A missing step is named on the dialog and the project page, with a link to the fix.

**From scratch:** **Projects** → **New project**. Only **Name** is required; **Goal** is one line Claude works toward and **Context** the repositories, files and folders threads read, both addable later. On your first project Claude takes a turn of its own unless you send a message first: it may start a read-only exploration thread and post **Setup recommendations** — repositories, routines and threads, each switched on — that you trim before **Update setup**.

**From a cloud session already doing the work:** **Continue as a project** in that session's menu creates a project named after it and posts setup recommendations. The original session keeps running mid-turn, so stop it if you don't want both. **Move to project** instead brings the session's work into an existing project.

## Work in it

**Sending work.** Paste tasks, updates and loose thoughts into the conversation as they arrive. Claude answers quick questions in place, sends new work to a new thread or to the thread already working in that area, and splits unrelated tasks into separate threads. Each new thread appears as a card under your message; its full results stay in the thread. Sometimes Claude lists **Suggested threads** for you to start instead.

**Pull requests.** Unless told otherwise, a thread branches from the repository's default branch, opens a pull request when you ask or on its own for a concrete change, then watches it with auto-fix on even when auto-fix is off for your other cloud sessions, pushing fixes when CI fails and replying when checks pass. The card's buttons send the thread an instruction as a message from you (**Resolve conflicts**, **Fix CI**, **Address comments**, **Merge it**), open the pull request on GitHub, or turn an idle thread's pushed branch into one directly.

**Overview.** Threads are grouped under **Ready for review**, **Waiting on you** (needs a reply or approval, or failed), **Working**, **Landing** (approved or queued to merge), **Idle** and **Resolved** — marked done by you, by Claude once you took the last step, or after a week of no activity. The **Overview** button shows a dot when a thread is waiting on you.

**Opening a thread** shows its transcript, where you steer it from its own message box, answer a pending permission prompt, or interrupt with **Stop**. A follow-up in the conversation reaches a thread only if Claude matches it to that one. Threads run in auto mode where the model supports it, so most tool calls don't ask ([[permissions-and-modes]]); a prompt that does appear waits inside the thread, and telling Claude in the conversation to go ahead doesn't reach it.

**Models and context.** A new project runs Opus everywhere, high effort for threads and low for the conversation; **Project settings > General** changes both. You don't manage context windows: threads compact automatically and the conversation works from recent messages, recent threads and memory rather than its full history, so anything that must never be dropped belongs in memory ([[context-window]]).

**Tuning.** Tell Claude how to coordinate — "Propose threads and wait for my go-ahead", "Run at most two threads at a time", "Answer that here instead of starting a thread". Claude saves such preferences to project memory itself, but they are instructions rather than enforced settings, so a thread limit given this way is no hard cap.

## Standing context

| Context | Carries | Set it |
|---|---|---|
| Project memory | Requirements, decisions and pitfalls, as files. Every thread reads the `MEMORY.md` index at start and opens the rest on demand | Ask Claude to remember or forget something; edit them in **Project settings > Memory** |
| Project instructions | Up to 16,000 characters sent to each new thread and the coordinator | **Project settings > Memory**, or ask Claude |
| Repositories, files, environment | What threads clone, what they read under `/mnt/project-files`, where they run | **Project settings > Environment**; files from **Add** on **Library** |

Project memory is separate from the auto memory Claude Code keeps on your machine and from the repositories' `CLAUDE.md` files, which each thread reads from its clone ([[claude-md-and-memory]]): put rules about a repository in its `CLAUDE.md` and notes about the project in memory. A useful instruction brief says what the project is for, which repositories and branch to work from, how a thread checks its own work, and what needs your go-ahead.

**Which repositories to add.** One you add is cloned into every thread with its `CLAUDE.md` and skills loaded, whether or not the task touches it. One you leave off can still be added by the thread that needs it, but mid-task, so its `CLAUDE.md` and skills weren't there at start and the next thread starts without it. Either way it needs the same GitHub prerequisites, and Claude can add only repositories from an owner the project already uses. Across many repositories, add the one or two nearly every task touches and name the rest in the instructions.

**What threads pick up.** Every repository's `CLAUDE.md`, skills, agents, commands and enabled plugins load; when two repositories disagree about a plugin, **Project settings > Plugins** wins. Permission rules, hooks and `env` come only from the `.claude/settings.json` in the directory the thread starts in: inside the repository when the project has one, above the clones when it has several, where no repository's file supplies them. Hooks an enabled plugin provides run either way.

**Environment and tooling.** Threads start in the project's cloud environment, a default Anthropic-hosted one until you pick another; change it when threads need an internal API, a private registry or a token, and install command-line tools in its setup script. Commit skills, subagents and commands to a project repository ([[skills]]); threads also load the skills enabled for your claude.ai account and the plugins in **Project settings > Plugins** ([[plugins]]). Their MCP tools come from all your claude.ai connectors ([[mcp]]); the coordinator has none, so send work needing one as a task.

## Settings, pausing and deletion

Project settings live at claude.ai/code or in the desktop app, not in `settings.json`. They save as you change them, and changes to instructions, repositories, plugins and environment reach new threads only. Besides the standing context above, they hold the name, icon and goal, both models and effort levels, token use by thread and model, a **Restart Claude** control, and these three:

- **Pause** interrupts every running thread and the conversation: no new threads start, routines don't run, and the project accepts no messages until you resume. A paused thread continues when you next message it.
- **Archive** hides the project and archives its threads, stopping any that were running or watching a pull request, and its routines don't run. Unarchiving the project from the Projects page leaves its threads archived until you unarchive each one.
- **Delete** permanently removes the project, its threads, memory and files and turns off its routines. Branches and pull requests already on GitHub are untouched.

## Usage and cost

A project counts against the same plan limits as your other sessions and uses them faster, noticeably so on Pro. Three things draw on the plan: each running thread as a full session, with no fixed number and an enforced cap of 200 new threads per day across your projects; the coordinator's own tokens; and idle threads that wake when CI fails or a review comment arrives, unless you ask them to stop watching. An idle or archived project with nothing running costs nothing.

A thread that reaches your five-hour or weekly limit shows **Service is busy** and continues after the reset, so work you left running spends your next window unless you press **Stop** or pause the project; a thread a routine started stops with a limit error instead. Going past plan limits needs usage credits turned on for your account, which a thread can't do for you ([[costs-and-usage]]). To spend less, start a fresh thread rather than reviving a large idle one — a follow-up to a thread idle longer than the prompt-cache lifetime re-reads its whole conversation — and pick a smaller model or lower effort.

## Limitations

- Available at claude.ai/code, in the desktop app and in the mobile apps, not in the terminal CLI and not on Amazon Bedrock, Google Cloud's Agent Platform or Microsoft Foundry.
- A local session can't be part of a project, and a thread can't be moved or copied to another project or out on its own.
- A project belongs to one user: no sharing of it or its threads, and no organization-level controls during the beta.
- A thread's sandbox pauses between turns. If it can't be resumed the thread continues from a fresh clone, so ask Claude to commit and push during long tasks or uncommitted work can be lost.
