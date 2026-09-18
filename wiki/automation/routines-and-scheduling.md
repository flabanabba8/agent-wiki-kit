---
title: Routines and Scheduling
type: how-to
tldr: "Routines, /schedule, /loop, cron tools"
sources:
  - raw/docs/official/routines.md
  - raw/docs/official/scheduled-tasks.md
  - raw/docs/official/desktop-scheduled-tasks.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
related: ["[[claude-code-on-the-web]]", "[[desktop-app]]", "[[ci-cd-and-code-review]]", "[[mcp]]", "[[channels]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [routines, schedule-command, loop-command, cron-tasks, scheduled-tasks]
valid_until: 2027-03-15
---

# Routines and Scheduling

Claude Code can run prompts on a schedule in three places. Pick one by where the work must run:

| | Cloud routine | Desktop scheduled task | `/loop` (in-session) |
|---|---|---|---|
| Runs on | Anthropic cloud (or a self-hosted environment) | Your machine | Your machine |
| Machine must be on | No | Yes | Yes |
| Open session needed | No | No | Yes |
| Survives restarts | Yes | Yes | Restored on `--resume`, with exceptions |
| Local files | No (fresh clone) | Yes | Yes |
| MCP | Connectors per routine | Config files and connectors | Inherits from the session |
| Permission prompts | None (autonomous) | Set per task | Inherits from the session |
| Minimum interval | 1 hour | 1 minute | 1 minute |

To react to events as they happen instead of polling, use [[channels]]. For scheduled CI jobs, see [[ci-cd-and-code-review]].

## Routines (cloud)

A **routine** saves a prompt, one or more GitHub repositories, a cloud environment and a set of connectors, and runs them automatically as a full Claude Code cloud session. Routines are a research preview on Pro, Max, Team and Enterprise. They belong to your individual account and are not shared. Commits, PRs and connector actions appear under your identity.

### Create

- **Web:** [claude.ai/code/routines](https://claude.ai/code/routines) → **New routine**.
- **CLI:** `/schedule` (alias `/routines`), for example `/schedule daily PR review at 9am` or `/schedule in 2 weeks, open a cleanup PR that removes the feature flag`. Claude asks follow-up questions and then saves the routine.
- **Desktop:** Code tab → **Routines** → **New routine** → **Cloud**. Choosing **Local** creates a Desktop scheduled task instead.

All three surfaces write to the same account. The form sets:
- **Prompt and model.** Runs are autonomous, with no permission-mode picker and no approvals, so write the prompt to be self-contained with explicit success criteria.
- **Repositories.** Each is cloned from its default branch on every run. Claude pushes to `claude/`-prefixed branches. A push to any other branch is rejected if the branch is protected, has someone else's open PR, or carries commits by other authors.
- **Environment.** Controls network access, environment variables and a cached setup script. The **Default** environment uses **Trusted** network access, limited to an allowlist. Other hosts fail with `403` and `x-deny-reason: host_not_allowed`. To reach more hosts, edit the environment and choose **Custom** or **Full**. See [[claude-code-on-the-web]].
- **Connectors.** All your claude.ai connectors are included by default, and Claude can use every tool in them, writes included, without asking. Remove the ones you don't need. Servers added locally with `claude mcp add` aren't available unless you add them as connectors or commit them in `.mcp.json` (see [[mcp]]).

### Triggers

A routine can combine any number of these:

**Schedule.** Choose hourly, daily, weekdays or weekly, entered in your local time. Runs may start a few minutes late because of a consistent per-routine stagger. For a custom cron, pick the nearest preset and then run `/schedule update`. Expressions more frequent than hourly are rejected. A one-off run fires once at a timestamp and then shows as **Ran**. One-off runs don't count against the daily routine cap.

**API.** Add this on the web only: edit the routine → **Add another trigger** → **API** → **Generate token**. The token is shown once and can be regenerated or revoked.

```bash
curl -X POST https://api.anthropic.com/v1/claude_code/routines/trig_01ABCDEFGHJKLMNOPQRSTUVW/fire \
  -H "Authorization: Bearer sk-ant-oat01-xxxxx" \
  -H "anthropic-beta: experimental-cc-routine-2026-04-01" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"text": "Sentry alert SEN-4521 fired in prod. Stack trace attached."}'
```

The response carries `claude_code_session_id` and `claude_code_session_url`. The optional `text` arrives as a literal string wrapped in a `<routine-fire-payload>` block marked as untrusted data. Claude acts on it only if the routine's prompt says to, for example "Investigate the alert described in the routine-fire-payload block". **Run now** text on the web is wrapped the same way. The `/fire` endpoint is for claude.ai users only and uses a dated beta header.

**GitHub.** The Claude GitHub App must be installed on the repository (`/web-setup` alone doesn't install it). Configure the trigger on the web, or with `/schedule add a GitHub trigger to my nightly review for pull requests opened in acme/webapp`. It supports **Pull request** and **Release** events, either one action (for example `pull_request.opened`) or all actions. PR filters are author, title, body, base branch, head branch, labels, is draft and is merged. Operators are equals, contains, starts with, is one of, is not one of, and matches regex. `matches regex` must match the whole value, so write `.*hotfix.*`. Every event starts a new session. Events are capped per routine and per account per hour during the preview.

### Manage

- Web detail page: **Run now**, a pause/resume toggle under **Repeats**, edit, delete, and run history.
- CLI: `/schedule list`, `/schedule update`, `/schedule run`, or ask something like `/schedule why did my nightly review do nothing this morning?`.
- A green run status means only that the session exited without an infrastructure error. Open the run to check whether the task actually succeeded.

### Limits and troubleshooting

- Routines draw on subscription usage and also have a daily per-account run cap. Organizations with usage credits turned on can keep running on overage.
- When the owner's GitHub connection is missing, a routine skips the run and keeps retrying for up to 72 hours.
- `Unknown command: /schedule` appears when you are signed in with an API key, profile or cloud provider (claude.ai login is required), are inside a web session, or your organization has disabled Claude Code on the web or routines. Owners control the Routines toggle at claude.ai/admin-settings/claude-code.
- If `/schedule` asks you to authenticate, run `/login` with your claude.ai account.

## Desktop scheduled tasks

In the Desktop Code tab → **Routines** → **New routine** → **Local**, set a name, description, instructions (with permission mode, model, working folder and an optional worktree toggle) and a schedule (Manual, Hourly, Daily, Weekdays or Weekly). For other intervals, ask Claude in any Desktop session.

- The app checks the schedule every minute while it is open and the computer is awake. Each task gets a deterministic delay of a few minutes.
- After the app starts or the computer wakes, it runs **one** catch-up for the most recent miss within the last seven days. Add time guards to prompts that care about timing.
- Runs in Manual mode stall on permission prompts. Click **Run now** once and choose "always allow" for each tool the task needs. MCP tools marked `requiresUserInteraction` stall on every run.
- The prompt is stored in `~/.claude/scheduled-tasks/<task-name>/SKILL.md`. A running task can change its own schedule with the `update_scheduled_task` MCP tool.

See [[desktop-app]] for the Desktop app itself.

## `/loop` and session-scoped tasks

`/loop` is a bundled skill that repeats a prompt while the session is open:

| Input | Behaviour |
|---|---|
| `/loop 5m check the deploy` | Fixed interval (`s`/`m`/`h`/`d`, rounded to a clean cron step, minimum one minute) |
| `/loop check whether CI passed and address any review comments` | Claude picks a delay between 1 minute and 1 hour after each iteration |
| `/loop` | Built-in maintenance prompt at a dynamic interval: continue unfinished work, tend the branch's PR, then run cleanup passes |

- A skill can be the prompt (`/loop 20m /review-pr 1234`), but only if Claude is allowed to invoke it. Built-in commands, `disable-model-invocation` skills and MCP prompts arrive as plain text.
- To replace the maintenance prompt, write `.claude/loop.md` (project, takes precedence) or `~/.claude/loop.md`. Edits apply on the next iteration, and content past 25,000 bytes is truncated.
- To stop a self-paced loop, press `Esc` while it waits. Claude can also end it by calling `ScheduleWakeup` with `stop: true`. Fixed-interval loops run until cancelled or until they expire.
- In dynamic mode, Claude may use the Monitor tool to stream a background script's output instead of polling.

**One-time reminders:** say "remind me at 3pm to push the release branch" or "in 45 minutes, check whether the integration tests passed". The task runs once and then deletes itself.

**Tools behind it:** `CronCreate` (5-field cron, prompt, recurring or once), `CronList` and `CronDelete` (by 8-character ID). A session holds up to 50 tasks.

**How tasks fire:**
- Due tasks run between your turns, never mid-response, in local time. Missed fires are not caught up. A task fires once when Claude becomes idle.
- **Jitter:** recurring tasks fire up to 30 minutes late (or up to half the interval if that is under an hour). One-shots set for `:00` or `:30` fire up to 90 seconds early. Pick minutes like `3 9 * * *` for tighter timing.
- **Expiry:** recurring tasks expire 7 days after creation, after one final fire.
- **Cron syntax:** `*`, values, `*/15`, ranges and lists. `L`, `W`, `?` and names like `MON` are not supported. If both day fields are set, a date matches when either one matches.
- Starting a new conversation clears all tasks. `--resume` or `--continue` restores unexpired `CronCreate` tasks but not a self-paced `/loop`. Backgrounding the session carries `/loop` tasks over (see [[worktrees-and-background-work]]).

To disable the scheduler, set `CLAUDE_CODE_DISABLE_CRON=1`.
