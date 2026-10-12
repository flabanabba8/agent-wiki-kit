---
title: Models and Effort
type: reference
tldr: "Pick model, effort, fast mode, advisor"
sources:
  - raw/docs/official/model-config.md
  - raw/docs/official/fast-mode.md
  - raw/docs/official/advisor.md
  - raw/docs/official/sub-agents.md
  - raw/docs/models-overview-2026-09.md
  - raw/docs/changelog-2.1.275-to-2.1.282.md
  - raw/docs/whats-new-opus-5-5.md
  - raw/articles/anthropic-claude-opus-5-5.md
  - raw/articles/what-a-task-costs-on-opus-5-5.md
  - raw/articles/getting-the-most-out-of-opus-5-5.md
  - raw/docs/changelog-2.1.283-to-2.1.296.md
related: ["[[claude-models]]", "[[costs-and-usage]]", "[[subagents]]", "[[context-window]]", "[[cloud-providers]]", "[[workflows]]"]
created: 2026-09-15
updated: 2026-10-11
confidence: high
last_verified: 2026-09-25
aliases: [model-selection, effort-level, fast-mode, advisor-tool, opusplan, which-model-to-use, flagged-message-model-switch]
valid_until: 2027-03-15
---

# Models and Effort

Which model a session runs, how hard it reasons, fast mode, the advisor, and fallbacks. The lineup itself (IDs, limits, pricing) is in [[claude-models]].

## Aliases

| Alias | Selects |
|:--|:--|
| `default` | Clears any override and uses your account's default (below) |
| `best` | What `fable` resolves to where Fable is available, otherwise `opus` |
| `fable` | Fable 5.1 (Fable 5 in Claude apps gateway sessions) |
| `opus` / `sonnet` / `haiku` | Latest Opus / Sonnet / Haiku for your provider |
| `sonnet[1m]`, `opus[1m]` | The 1M-token context variant |
| `opusplan` | `opus` in plan mode, `sonnet` for execution, which puts code edits on Sonnet; measure it before making it a default |

| Provider | `opus` | `sonnet` |
|:--|:--|:--|
| Anthropic API | Opus 5.5 | Sonnet 5 |
| Claude Platform on AWS | Opus 5.5 | Sonnet 4.6 |
| Amazon Bedrock, Google Cloud's Agent Platform | Opus 5.5 | Sonnet 4.5 |
| Microsoft Foundry | Opus 4.6 | Sonnet 4.5 |

The **account default** is Opus 5.5 on Pro, Max, Team, Enterprise, the Anthropic API, Claude Platform on AWS, Bedrock, and Agent Platform, and Sonnet 4.5 on Foundry. An admin-set organization default model replaces it. Fable is never a default: choose it with `/model fable` or `claude --model fable`, and Fable 5 by ID (`/model claude-fable-5`). On some plans Fable bills to usage credits, and the picker asks for consent once. To pin exact versions on cloud providers, use `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, and `ANTHROPIC_DEFAULT_FABLE_MODEL` (see [[cloud-providers]]). Allowlists (`availableModels`) are an admin topic in [[enterprise-admin]].

## Setting the model

Highest priority first:

1. `/model <alias|name>` in the session, or `/model` for the picker
2. `claude --model <alias|name>`
3. `ANTHROPIC_MODEL`
4. The `model` key in settings
5. `ANTHROPIC_DEFAULT_MODEL`, the default for new sessions when nothing above sets one

In the picker, `Enter` switches and saves the choice as your default in `~/.claude/settings.json` (as does typing `/model sonnet`), while `s` switches for this session only. `--model` and `ANTHROPIC_MODEL` apply only to the launched session. Resumed sessions keep their original model unless a launch flag or variable overrides it. An unexpected startup model usually comes from a project or managed `model` value (the header names the file) or `ANTHROPIC_MODEL`.

## Choosing a model and effort

Model choice sets the price of every token, including in subagents that inherit the main model, so it moves the bill more than effort does ([[costs-and-usage]]). Anthropic's Claude Code guidance:

- **Opus 5.5 is the daily driver** for work you supervise: features across a few files, debugging, code review with follow-up edits.
- **Raise effort before changing models.** Start well-scoped work at `medium`; when a fix stops at one layer (the handler changes but a second caller doesn't), try `high`. First make sure Claude can run a test or build: a check costs one turn, more effort adds thinking to every turn.
- **Move up to Fable 5.1** when the result matters more than the token price: long unsupervised runs, problems with no existing pattern, large multi-subagent changes. If raised effort hits the same problem twice, switch; switch back once it's solved.
- **Move down to Sonnet or Haiku for lookups**, not for writing code: search-and-summarize subagents, reading logs and test output. For a mechanical edit across many files, keep Opus 5.5 at `low`.
- **Switch at a natural break.** The new model starts with an empty cache ([[context-window]]), so run `/compact` first or start fresh with a short written plan. `/model` also saves the choice as your default, so switch back when the hard part is done.

## Effort levels

Effort controls how much the model thinks, writes and calls tools per turn.

| Model | Levels |
|:--|:--|
| Opus 5.5, Fable 5.1, Fable 5, Opus 5, Sonnet 5, Opus 4.8, Opus 4.7 | `low`, `medium`, `high`, `xhigh`, `max` |
| Opus 4.6, Sonnet 4.6 | `low`, `medium`, `high`, `max` |

| Level | When to use it |
|:--|:--|
| `low` | Mechanical, scoped, latency-sensitive work |
| `medium` | Well-scoped everyday work; the default on Opus 5.5 |
| `high` | When medium stalls; the default on other models except Opus 4.7 |
| `xhigh` | Hard problems at higher token spend; the default on Opus 4.7 |
| `max` | Demanding tasks; can overthink, so test first. Session-only unless set via the env var |

An unsupported level falls back to the next one below (`xhigh` runs as `high` on Opus 4.6). The scale is calibrated per model.

**How to set it:**

- `/effort` opens a slider; `/effort high` sets it directly; `/effort auto` clears your saved level; `/effort status` prints the current level. `Enter` saves, `s` applies to this session only. A mid-task change applies from the next request.
- The left and right arrows in `/model`, `claude --effort <level>`, or `CLAUDE_CODE_EFFORT_LEVEL`.
- Settings: `effortLevel` (`low` to `xhigh`) or per-model levels under `modelSettings`. A top-level `effortLevel` in user settings doesn't apply to Opus 5.5.
- The `effort` field in skill or subagent frontmatter overrides the session level while that skill or subagent runs.

**Resolution order:** an explicit choice (env var, `--effort`, or `/effort`), then your settings, then the model default. A level saved before `/effort` became per-model doesn't apply to newly released models such as Opus 5.5; they start at their default until you pick a level. `maxEffortLevel` or an organization cap limits every source.

**Ultracode.** `ultracode` in `/effort` (or `claude --effort ultracode`, or the `ultracode` setting) is its own toggle in `/effort` (press `Tab`, or `/effort ultracode [on|off]`), stays on at any effort level, and has Claude orchestrate dynamic workflows for substantive tasks ([[workflows]]). It needs workflows on and a model with `xhigh`.

**ultrathink.** Put `ultrathink` anywhere in a prompt to request deeper reasoning for that turn only. The effort sent to the API doesn't change. Other phrases such as "think hard" are ordinary text, and on Opus 5.5 they are unnecessary ([[prompting-and-workflows]]).

## Extended thinking

- **Toggle for the session:** `Option+T` on macOS or `Alt+T` elsewhere.
- **Global default:** `/config` saves `alwaysThinkingEnabled`.
- **Turn off via environment:** `MAX_THINKING_TOKENS=0` disables thinking on the Anthropic API. Fable models and Opus 5.5 always think; on them the toggle and `/config` show a one-line reason instead of a switch.
- **Viewing:** thinking is collapsed (`Ctrl+O` shows it); `showThinkingSummaries: true` returns full summaries. You pay for all thinking tokens, as output.
- **Older models:** Fable, Sonnet 5, and Opus 4.7 and later always use adaptive reasoning. On Opus 4.6 and Sonnet 4.6, `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` reverts to a fixed budget set by `MAX_THINKING_TOKENS`.

## Extended context

On the Anthropic API, Fable 5.1, Fable 5, Sonnet 5, and Opus 4.7 and later run with a 1M-token window on every plan, including Pro, with no `[1m]` variant or usage credits needed. Opus 4.6 and Sonnet 4.6 reach 1M only through `[1m]`: Opus 4.6 1M is included on Max, Team, and Enterprise, and Sonnet 4.6 1M needs usage credits on every subscription plan. `opusplan` runs both phases at 1M when both models do. The 1M window uses standard pricing with no long-context premium. Append `[1m]` to an alias or ID (`/model opus[1m]`) to select it, or set `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` to hold sessions to 200K. On Bedrock, Vertex, Foundry and the Claude apps gateway, Opus 4.7 and later and Fable use 1M by default with no `[1m]` suffix, and behind a custom `ANTHROPIC_BASE_URL` any model with a 1M window uses it; run `/autocompact 200k` if your gateway stops at 200K. Compaction thresholds are covered in [[context-window]].

## Fast mode

Fast mode runs Opus up to 2.5x faster at a higher per-token price. It is the same model with a different API configuration, on Opus 5.5, Opus 5 and Opus 4.8 (research preview). Use it for back-and-forth work.

- **Toggle:** `/fast` (Space toggles, Enter confirms), `Option+O`/`Alt+O`, or `"fastMode": true` in user settings. A `↯` icon shows while it's on. Turning it on while on an unsupported model switches you to Opus.
- **Price:** $8 input / $40 output per MTok on Opus 5.5; $10 / $50 on Opus 5 and Opus 4.8; flat across the 1M window. The first time you enable it in a conversation, you pay the fast uncached input price for the whole existing context, so turn it on at the start.
- **Availability:** Anthropic Console API and subscription plans (including a Fast mode switch in the model menu of cloud sessions on the web), not Bedrock, Agent Platform, Foundry, or Claude Platform on AWS. On Pro, Max, Team, and Enterprise it bills only to usage credits, which must be on. Team and Enterprise Owners must enable it first.
- **Controls:** `fastModePerSessionOptIn: true` makes each session start with it off; set in managed settings, `/fast on` then works only in an interactive terminal. Managed `fastMode: false` blocks it. `CLAUDE_CODE_DISABLE_FAST_MODE=1` disables it.
- **Limits:** it has its own rate-limit pool; hitting it falls back to standard speed until the cooldown ends.

## The advisor tool

The advisor is an experimental server-side tool (Anthropic API only) that lets Claude consult a stronger model at decision points, such as before committing to an approach. Claude decides when; the advisor reads the full conversation.

`/advisor opus` sets and saves it (`advisorModel`), `claude --advisor opus` applies to one session, and `/advisor off` turns it off.

- **Pairing rule:** the advisor must be at least as capable as the main model: Opus 5.5 and Opus 5 accept Fable or Opus 5 and later, Fable 5.1 only Fable 5.1, and Haiku can't be an advisor. If the API refuses a saved advisor, Claude Code silently resends without it for the rest of the conversation; a new choice applies after `/clear` or `/compact`.
- **Cost:** each call bills at the advisor model's rates (on subscriptions, it counts toward plan limits). Toggling the advisor doesn't invalidate the main prompt cache.
- **Subagents** inherit the advisor.
- **Disable entirely:** `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1`.

## Fallback models

**Availability fallback.** When the primary model is overloaded or unavailable, Claude Code tries a fallback chain for that turn only. Auth, billing, rate-limit, and request-size errors never switch.

Set it with `claude --fallback-model sonnet,haiku` or the `fallbackModel` setting (an array); chains are capped at three models, and the flag beats the setting. The chain also applies to subagents and to compaction, but never falls back to a model with a smaller window during compaction.

**Content fallback.** Fable, Opus 5.5 and Opus 5 run safety classifiers, most often triggered by cybersecurity or biology content. On Fable 5.1, Fable 5 and Opus 5.5, biology-flagged requests re-run on Opus 5 and cybersecurity-flagged ones on Opus 4.8. On Opus 5, cybersecurity re-runs on Opus 4.8 and biology ends in a refusal. Finding and fixing vulnerabilities in your own code is allowed on Opus 5.5. The check covers the whole conversation, so earlier content can trigger it; requests to reproduce the model's internal reasoning in the reply are a flag category too.

A notice names the fallback model and the session stays on it: `/model` switches back, `Esc` `Esc` edits and retries, `/feedback` reports a wrong flag. Set `switchModelsOnFlag: false` (in `/config`, "Switch models when a message is flagged") to be asked each time. Run `claude --safe-mode` to check whether CLAUDE.md, skills, or MCP content triggered it.

## Subagent models

A subagent's model resolves in this order ([[subagents]]):

1. The per-invocation `model` parameter
2. The definition's `model` frontmatter (`inherit` means the main model)
3. `CLAUDE_CODE_SUBAGENT_MODEL`
4. The main conversation's model

An alias in frontmatter or the parameter that names the main model's family (such as `opus` while on Opus 5.5 `[1m]`) resolves to the main model exactly, window included; an alias in `CLAUDE_CODE_SUBAGENT_MODEL` doesn't. Inheriting subagents follow a `/model` switch. The built-in Explore agent inherits the main model, capped at Opus on the Claude API. To force one model onto every subagent, teammate, and workflow agent, set `CLAUDE_CODE_SUBAGENT_MODEL` and `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`. Put `model: haiku` or `model: sonnet` on search and log-reading subagents.
