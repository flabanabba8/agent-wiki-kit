---
title: Costs and Usage
type: how-to
tldr: "Track spend, limits, and cut token use"
sources:
  - raw/docs/official/costs.md
  - raw/docs/official/statusline.md
  - raw/docs/official/commands.md
related: ["[[models-and-effort]]", "[[context-window]]", "[[enterprise-admin]]", "[[headless-mode]]", "[[agent-teams]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [usage-limits, token-costs, cost-command, reduce-token-usage, usage-credits]
valid_until: 2027-03-15
---

# Costs and Usage

Claude Code consumes tokens on every request, and each request carries the conversation so far. How that turns into a bill depends on how you sign in:

- **Pro, Max, Team, and Enterprise subscriptions** draw from a usage allowance with a rolling five-hour window and a weekly window, shared with Claude chat and Cowork. Usage credits let you keep working past the allowance.
- **Claude Console API keys and cloud providers** (Bedrock, Agent Platform, Foundry) bill per token to the organization.

The docs report that across enterprise deployments the average is "around \$13 per developer per active day and \$150-250 per developer per month, with costs remaining below \$30 per active day for 90% of users". Start with a pilot group to establish your own baseline.

## Check your usage

`/usage` is the main view; `/cost` and `/stats` are aliases (`/stats` opens on the Stats tab).

- **Session block:** total cost, API and wall-clock duration, lines changed, and tokens per model with cache read and write. The dollar figure is a local estimate at list price and resets on `/clear`. For API accounts, the Console Usage page is authoritative. Subscribers can ignore the dollar figure for billing.
- **`Prompt cache (main)` line:** request count, the share of input served from cache, misses (with a likely cause when known), and whether the cache is warm.
- **Plan usage breakdown** (subscriptions): recent usage attributed to skills, subagents, plugins, and individual MCP servers; flags for behaviors such as long context or cache misses that account for 10% or more; and the heaviest `/loop` or scheduled tasks. Press `d` or `w` to switch between 24 hours and 7 days. The breakdown is computed from local history on this machine.
- **Usage-credits row:** this month's usage-credits spend against your spend limit, when credits are on.
- **Rate-limited endpoint:** `/usage` shows the last data it loaded within 60 minutes. Press `r` to retry.

Related tools:

- `/insights` writes an HTML report on how you work, covering friction points and suggestions, from up to 200 recent sessions. It saves to `~/.claude/usage-data/report.html`, and its analysis also consumes tokens.
- A status line can show spend continuously from `cost.total_cost_usd`, `rate_limits.five_hour.used_percentage`, `rate_limits.seven_day.used_percentage`, and `context_window.used_percentage`. See [[interface]].
- In automation, cap a `claude -p` run with `--max-budget-usd` ([[headless-mode]]).

## Usage credits and limit messages

`/usage-credits` requires a claude.ai login. On Pro and Max it opens **Settings > Usage**, where you turn credits on and set a monthly spend limit. Team and Enterprise members with billing access land on **Admin settings > Usage**. Members without billing access send their admins a request instead. Fast mode and, on some plans, Fable bill only to usage credits ([[models-and-effort]]).

| Message | Meaning and fix |
|:--|:--|
| "You've hit your session limit" / "weekly limit" | The seat allowance window is used up for all models, so switching models won't help. Wait for the reset shown, or use usage credits. `/rate-limit-options` can wait and continue automatically |
| "You've hit your Opus limit" / "Sonnet limit" | A model-specific limit; switching to another family with `/model` keeps you working |
| "individual spend limit", "org's monthly spend limit", "team's shared budget" | Usage credits reached a spend cap; an admin raises it in **Admin settings > Usage** |
| Context or auto-compact warning | Not a billing limit; the conversation is nearly full ([[context-window]]) |

## Managing spend for an organization

| Setup | See spend | Cap spend | Per-user data |
|:--|:--|:--|:--|
| Claude for Teams or Enterprise | Spend report in org analytics | Spend limits in admin settings (org, group, or member) | Spend report CSV; Enterprise Analytics API |
| Claude Console (API) | Console usage page | Workspace spend limits on the auto-created "Claude Code" workspace | Console dashboard; Claude Code Analytics API |
| Bedrock, Agent Platform, Foundry | Cloud billing console | Cloud budget controls | OpenTelemetry, a Claude apps gateway, or an LLM gateway |

OpenTelemetry export works on every setup. To make `/usage`, the status line, and telemetry show contracted rather than list prices, deploy the `modelPricing` managed setting; `/usage` then notes `at your organization's configured rates`. Rollout and analytics details are in [[enterprise-admin]].

Per-user rate-limit recommendations for API organizations:

| Team size | TPM per user | RPM per user |
|:--|:--|:--|
| 1-5 | 200k-300k | 5-7 |
| 5-20 | 100k-150k | 2.5-3.5 |
| 20-50 | 50k-75k | 1.25-1.75 |
| 50-100 | 25k-35k | 0.62-0.87 |
| 100-500 | 15k-20k | 0.37-0.47 |
| 500+ | 10k-15k | 0.25-0.35 |

These limits apply at the organization level, so per-user allocations shrink as teams grow and fewer members work concurrently.

## Why usage climbs in a long session

- **Long context:** each request resends the whole conversation, re-read at the cached rate, so a one-line question late in a long session still costs the full history.
- **Cache misses:** the first message after a break longer than the cache lifetime reprocesses everything. The lifetime is one hour on a subscription, five minutes while drawing on usage credits, and five minutes by default on API keys and cloud providers.
- **Idle-time triggers:** scheduled tasks, cross-session messages, and goal check-ins can start turns on an idle session, each sending the full context. Set `crossSessionInbound` to `hold` to queue inbound messages, and set `CLAUDE_CODE_GOAL_CHECKIN_MINUTES` to `0` to turn check-ins off.
- **Agent teammates** consume tokens until they exit. Teams "use approximately 7x more tokens than standard sessions when teammates run in plan mode" ([[agent-teams]]).
- **Compaction** is itself a large request. `/clear` costs nothing.
- **Background work** such as summarizing past sessions for `claude --resume` uses a small amount of tokens, "typically under \$0.04 per session".

## Reduce token usage

- **Clear between tasks.** `/rename`, then `/clear`, then `/resume` later. Stale context is paid for on every message.
- **Compact with focus.** `/compact Focus on code samples and API usage`, or add a `# Compact instructions` section to CLAUDE.md.
- **Match the model to the job.** Sonnet handles most coding; reserve Opus for hard reasoning; use `model: haiku` for simple subagents. Lower the effort level for simple work.
- **Trim MCP overhead.** Tool definitions are deferred by default, but CLI tools such as `gh` and `aws` are cheaper still. Disable unused servers in `/mcp` and check `/context`.
- **Use code intelligence plugins** for typed languages; go-to-definition replaces grep-and-read loops.
- **Preprocess with hooks.** A `PreToolUse` hook can rewrite `npm test` to show only failures, shrinking tens of thousands of tokens to hundreds.
- **Move workflow instructions from CLAUDE.md into skills**, which load on demand. Keep CLAUDE.md under about 200 lines.
- **Delegate verbose work to subagents**, such as test runs, log processing, and doc fetching, so only a summary returns.
- **Write specific prompts.** "Add input validation to the login function in auth.ts" beats "improve this codebase".
- **Plan first and stop early.** Use plan mode for complex tasks, press `Esc` when Claude heads the wrong way, and `/rewind` to recover.
