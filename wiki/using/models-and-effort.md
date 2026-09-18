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
related: ["[[claude-models]]", "[[costs-and-usage]]", "[[subagents]]", "[[context-window]]", "[[cloud-providers]]", "[[workflows]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [model-selection, effort-level, fast-mode, advisor-tool, opusplan]
valid_until: 2027-03-15
---

# Models and Effort

This page covers how to choose which Claude model a Claude Code session runs, how hard it reasons (effort and thinking), and three ways to trade cost for speed or quality: fast mode, the advisor tool, and fallback models. For the lineup itself (context limits, API pricing, deprecations) see [[claude-models]].

## Aliases and model IDs

Current Claude API IDs: `claude-fable-5-1`, `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5-20251001`. Aliases save you from tracking versions:

| Alias | Selects |
|:--|:--|
| `default` | Clears any override and uses your account's default (below) |
| `best` | What `fable` resolves to where Fable is available, otherwise `opus` |
| `fable` | Fable 5.1 (Fable 5 in Claude apps gateway sessions) |
| `opus` / `sonnet` / `haiku` | Latest Opus / Sonnet / Haiku for your provider |
| `sonnet[1m]`, `opus[1m]` | The 1M-token context variant |
| `opusplan` | `opus` in plan mode, `sonnet` for execution |

| Provider | `opus` | `sonnet` |
|:--|:--|:--|
| Anthropic API | Opus 5 | Sonnet 5 |
| Claude Platform on AWS | Opus 5 | Sonnet 4.6 |
| Amazon Bedrock, Google Cloud's Agent Platform | Opus 5 | Sonnet 4.5 |
| Microsoft Foundry | Opus 4.6 | Sonnet 4.5 |

The **account default** is Opus 5 on Max, Team Premium, Enterprise, the Anthropic API, Claude Platform on AWS, Bedrock, and Agent Platform. It is Sonnet 5 on Pro and Team Standard, and Sonnet 4.5 on Foundry. An admin-set organization default model replaces it. Fable is never a default: choose it with `/model fable` or `claude --model fable`, and Fable 5 by ID (`/model claude-fable-5`). On some plans Fable bills to usage credits, and the picker then marks it "Requires usage credits" and asks for consent once. To pin exact versions on cloud providers, use `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, and `ANTHROPIC_DEFAULT_FABLE_MODEL` (see [[cloud-providers]]). Allowlists (`availableModels`) are an admin topic in [[enterprise-admin]].

## Setting the model

Highest priority first:

1. `/model <alias|name>` in the session, or `/model` for the picker
2. `claude --model <alias|name>`
3. `ANTHROPIC_MODEL`
4. The `model` key in settings
5. `ANTHROPIC_DEFAULT_MODEL`, the default for new sessions when nothing above sets one

In the picker, `Enter` switches and saves the choice as your default in `~/.claude/settings.json`, while `s` switches for this session only. Typing `/model sonnet` behaves like `Enter`. `--model` and `ANTHROPIC_MODEL` apply only to the launched session, so use them to run different models in parallel terminals. Resumed sessions keep their original model unless a launch flag or variable overrides it. If a new session starts on an unexpected model, look for a project or managed `model` value (the startup header names the file), an `ANTHROPIC_MODEL` export, or an unwritable settings file. `/status` and the status line show the active model.

## Effort levels

Effort controls adaptive reasoning, meaning how much the model thinks per step. Lower effort is faster and cheaper; higher effort reasons more deeply.

| Model | Levels |
|:--|:--|
| Fable 5.1, Fable 5, Opus 5, Sonnet 5, Opus 4.8, Opus 4.7 | `low`, `medium`, `high`, `xhigh`, `max` |
| Opus 4.6, Sonnet 4.6 | `low`, `medium`, `high`, `max` |

| Level | When to use it |
|:--|:--|
| `low` | Short, scoped, latency-sensitive tasks that don't need much intelligence |
| `medium` | Cost-sensitive work that can give up some intelligence |
| `high` | Balanced; the default on every model except Opus 4.7 |
| `xhigh` | Deeper reasoning at higher token spend; the default on Opus 4.7 |
| `max` | Demanding tasks; can overthink, so test first. Session-only unless set via the env var |

An unsupported level falls back to the highest supported level below it; for example, `xhigh` runs as `high` on Opus 4.6. The scale is calibrated per model, so the same name doesn't mean the same underlying value across models.

**How to set it:**

- `/effort` opens a slider; `/effort high` sets it directly; `/effort auto` clears your saved level. `Enter` saves, `s` applies to this session only.
- Use the left and right arrows in `/model`.
- Launch flag: `claude --effort <level>`.
- Environment: `CLAUDE_CODE_EFFORT_LEVEL`.
- Settings: `effortLevel` (`low` to `xhigh`) or per-model levels under `modelSettings`.
- The `effort` field in skill or subagent frontmatter overrides the session level while that skill or subagent runs.

**Resolution order:**

1. An explicit choice (env var, `--effort`, or `/effort`).
2. On Fable 5, Opus 4.8, and Opus 4.7, a hold on the model's default effort once you've used that model.
3. Your settings.
4. The model default.

`maxEffortLevel` or an organization cap limits every source.

**Ultracode.** `ultracode` in `/effort` (or `claude --effort ultracode`, or the `ultracode` setting) sends `xhigh` and has Claude orchestrate dynamic workflows for substantive tasks. See [[workflows]]. It is unavailable when workflows are off, when the model lacks `xhigh`, or when a cap below `xhigh` applies.

**ultrathink.** Put `ultrathink` anywhere in a prompt to request deeper reasoning for that turn only. The effort sent to the API doesn't change. Other phrases such as "think hard" are passed through as ordinary text.

## Extended thinking

- **Toggle for the session:** `Option+T` on macOS or `Alt+T` elsewhere.
- **Global default:** `/config` saves `alwaysThinkingEnabled`.
- **Turn off via environment:** `MAX_THINKING_TOKENS=0` disables thinking on the Anthropic API. Fable models can't turn thinking off.
- **Viewing:** thinking is collapsed; `Ctrl+O` shows it. Set `showThinkingSummaries: true` to receive full summaries instead of redacted blocks.
- **Billing:** you pay for all thinking tokens, including collapsed ones.
- **Older models:** Fable, Sonnet 5, and Opus 4.7 and later always use adaptive reasoning. On Opus 4.6 and Sonnet 4.6, `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` reverts to a fixed budget set by `MAX_THINKING_TOKENS`.

## Extended context

On the Anthropic API, Fable 5.1, Fable 5, Sonnet 5, and Opus 4.7 and later run with a 1M-token window by default. On Max, Team, and Enterprise, Opus is upgraded to 1M automatically. Sonnet 4.6 at 1M needs usage credits on every subscription plan. The 1M window uses standard pricing with no long-context premium. Append `[1m]` to an alias or ID (`/model opus[1m]`) to select it, or set `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` to hold sessions to 200K. Compaction thresholds are covered in [[context-window]].

## Fast mode

Fast mode runs Opus up to 2.5x faster at a higher per-token price. It is the same model with a different API configuration, supported on Opus 5 and Opus 4.8 only, and in research preview.

- **Toggle:** `/fast` (then Tab), `Option+O`/`Alt+O`, or `"fastMode": true` in user settings. A `↯` icon shows while it's on. Turning it on while on an unsupported model switches you to Opus.
- **Price:** $10 input / $50 output per MTok on Opus 5 and Opus 4.8, flat across the 1M window. The first time you enable it in a conversation, you pay the fast uncached input price for the whole existing context, so turn it on at the start.
- **Availability:** Anthropic Console API and subscription plans, not Bedrock, Agent Platform, Foundry, or Claude Platform on AWS. On Pro, Max, Team, and Enterprise it bills only to usage credits, which must be on. Team and Enterprise Owners must enable it first.
- **Controls:** `fastModePerSessionOptIn: true` makes each session start with it off. `CLAUDE_CODE_DISABLE_FAST_MODE=1` disables it.
- **Limits:** it has its own rate-limit pool. Hitting the limit falls back to standard speed, the icon grays out, and fast mode returns after the cooldown.

Fast mode keeps quality and cuts latency at higher cost. Lowering effort cuts thinking time and may reduce quality. They combine.

## The advisor tool

The advisor is an experimental server-side tool (Anthropic API only) that lets Claude consult a second, typically stronger model at decision points: before committing to an approach, when an error keeps recurring, or before declaring a task done. Claude decides when to call it, and the advisor reads the full conversation.

```bash
/advisor opus          # set and save as default (advisorModel)
claude --advisor opus  # this session only
/advisor off
```

- **Pairing rule:** the advisor must be at least as capable as the main model. Haiku 4.5 or Sonnet 4.6 accept Fable, Opus, or Sonnet advisors. Opus 5 accepts Fable or Opus 5. Fable 5.1 accepts only Fable 5.1. Haiku can't be an advisor.
- **Common pairing:** Sonnet main with an Opus advisor handles routine work cheaply and escalates planning and completion checks.
- **Cost:** each call bills at the advisor model's rates (on subscriptions, it counts toward plan limits). Toggling the advisor doesn't invalidate the main prompt cache.
- **Subagents** inherit the advisor.
- **Disable entirely:** `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1`.

| Approach | Stronger model runs |
|:--|:--|
| Advisor | At decision points, when Claude chooses |
| `opusplan` | During plan mode, then Sonnet executes |
| Subagent with `model` set | For the whole delegated subtask |
| `/model` | From the next request on |

## Fallback models

**Availability fallback.** When the primary model is overloaded or unavailable, Claude Code tries a fallback chain for that turn only. Auth, billing, rate-limit, and request-size errors never switch.

```bash
claude --fallback-model sonnet,haiku
```

```json
{ "fallbackModel": ["claude-sonnet-5", "claude-haiku-4-5"] }
```

Chains are capped at three models, and `--fallback-model` beats the setting. The chain also applies to subagents and to compaction, but never falls back to a model with a smaller window during compaction.

**Content fallback.** Fable and Opus 5 run safety classifiers, most often triggered by cybersecurity or biology content. On Fable 5.1 and Fable 5, biology-flagged requests re-run on Opus 5 and cybersecurity-flagged ones on Opus 4.8. On Opus 5, cybersecurity re-runs on Opus 4.8 and biology ends in a refusal. The session then stays on the fallback model; use `/model` to switch back. Set `switchModelsOnFlag: false` to be asked each time. Run `claude --safe-mode` to check whether CLAUDE.md, skills, or MCP content triggered it.

## Subagent models

A subagent's model resolves in this order ([[subagents]]):

1. The per-invocation `model` parameter
2. The definition's `model` frontmatter (`inherit` means the main model)
3. `CLAUDE_CODE_SUBAGENT_MODEL`
4. The main conversation's model

The built-in Explore agent inherits the main model, capped at Opus on the Claude API. To force one model onto every subagent, teammate, and workflow agent, set `CLAUDE_CODE_SUBAGENT_MODEL` and `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`. For cheap delegated work, `model: haiku` in a subagent definition is the usual choice. See [[costs-and-usage]].
