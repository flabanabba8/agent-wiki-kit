---
title: Claude Models
type: reference
tldr: "Claude lineup: IDs, limits, prices, lifecycle"
sources:
  - raw/docs/models-overview-2026-09.md
  - raw/docs/whats-new-opus-5-5.md
  - raw/docs/migrating-to-opus-5-5.md
  - raw/docs/prompting-claude-opus-5-5.md
  - raw/docs/changelog-2.1.275-to-2.1.282.md
  - raw/articles/anthropic-claude-opus-5-5.md
  - raw/articles/what-a-task-costs-on-opus-5-5.md
  - raw/articles/anthropic-claude-opus-5.md
  - raw/articles/anthropic-claude-sonnet-5.md
  - raw/articles/anthropic-claude-fable-5-1.md
  - raw/articles/claude-opus-5-system-card-agentic-coding.md
  - raw/articles/claude-sonnet-5-system-card-agentic-coding.md
related: ["[[models-and-effort]]", "[[prompting-claude-models]]", "[[cloud-providers]]", "[[costs-and-usage]]", "[[trustworthy-agents]]", "[[agent-evals]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
valid_until: 2026-11-15
aliases: [claude-model-ids, claude-api-pricing, model-deprecations, claude-5-models, which-claude-model, opus-5-5-migration, opus-5-5-breaking-changes]
---

# Claude Models

This page lists the Claude models on the Claude API, with IDs, limits, prices, lifecycle dates and the API changes that come with Claude Opus 5.5. For choosing models and effort inside Claude Code, see [[models-and-effort]]. For provider setup, see [[cloud-providers]]. For prompting patterns, see [[prompting-claude-models]].

## Current lineup

| | Claude Fable 5.1 | Claude Opus 5.5 | Claude Opus 5 | Claude Sonnet 5 | Claude Haiku 4.5 |
|---|---|---|---|---|---|
| API ID | `claude-fable-5-1` | `claude-opus-5-5` | `claude-opus-5` | `claude-sonnet-5` | `claude-haiku-4-5-20251001` |
| Best for | Demanding reasoning, long-horizon agentic work | Long-running agentic coding and knowledge work | Complex agentic coding and enterprise work | Speed and intelligence | Fastest responses |
| Input / output per MTok | $10 / $50 | $4 / $20 | $5 / $25 | $2 / $10 | $1 / $5 |
| Context window | 1M | 1M | 1M | 1M | 200K |
| Max output | 128K | 128K | 128K | 128K | 64K |
| Thinking | Adaptive (always on) | Adaptive (always on) | Adaptive | Adaptive | Extended |
| Default effort | `high` | `medium` | `high` | `high` | Not supported |
| Latency | Slower | Output 30%+ faster than Opus 5 | Moderate | Fast | Fastest |
| Reliable knowledge cutoff | Jun 2026 | Not stated | May 2026 | Jan 2026 | Feb 2025 |

- **Which to pick.** Opus 5.5, the first Claude 5.5 model, performs at Fable 5.1's level on most work and costs about 40% less than Opus 5 on typical workloads. Anthropic suggests a small model for lookups, Opus 5.5 for supervised work, and Fable 5.1 for the hardest tasks.
- **Coming models.** Anthropic says Claude Sonnet 5.5 and Claude Haiku 5.5 will follow in the coming weeks.
- **Capabilities.** All models accept text and image input and support tool use. The Models API returns `max_input_tokens`, `max_tokens` and a `capabilities` object for each model.
- **Mythos.** Claude Mythos 5.1 is the same model as Fable 5.1 with different safeguards, at the same specs and prices, available only through Project Glasswing and Anthropic's trusted-access programs. `claude-mythos-preview` is deprecated, replaced by `claude-mythos-5`.

## Model IDs

- **4.6 generation and later.** IDs have no date: `claude-{name}-{major}[-{minor}]`, as in `claude-opus-5-5`. Each ID is a pinned snapshot, and updated versions ship under new IDs.
- **Earlier models.** IDs carry a snapshot date (`claude-sonnet-4-5-20250929`). On the Claude API they also have aliases such as `claude-sonnet-4-5`, pointing to the latest snapshot.
- **Amazon Bedrock.** IDs add an `anthropic.` prefix (`anthropic.claude-opus-5-5`). Older dated Bedrock IDs end in `-v1:0`; `anthropic.claude-opus-4-6-v1` is the last with a `-v1` suffix.
- **Other platforms.** Claude Platform on AWS, Google Cloud and Microsoft Foundry serve Opus 5.5 as `claude-opus-5-5`. On Google Cloud, older models put `@` before the date (`claude-haiku-4-5@20251001`).
- **Behavior drift.** An ID's weights never change; its serving infrastructure (router, classifiers, sampling) can.

## Pricing

Claude API prices in USD per million tokens:

| Model | Input | 5m cache write | 1h cache write | Cache read | Output | Batch input / output |
|---|---|---|---|---|---|---|
| Fable 5.1, Mythos 5.1 | $10 | $12.50 | $20 | $0.25 | $50 | $5 / $25 |
| Fable 5, Mythos 5 | $10 | $12.50 | $20 | $1 | $50 | $5 / $25 |
| Opus 5.5 | $4 | $5 | $8 | $0.20 | $20 | $2 / $10 |
| Opus 5, 4.8, 4.7, 4.6, 4.5 | $5 | $6.25 | $10 | $0.50 | $25 | $2.50 / $12.50 |
| Sonnet 5 | $2 | $2.50 | $4 | $0.20 | $10 | $1 / $5 |
| Sonnet 4.6, 4.5 | $3 | $3.75 | $6 | $0.30 | $15 | $1.50 / $7.50 |
| Haiku 4.5 | $1 | $1.25 | $2 | $0.10 | $5 | $0.50 / $2.50 |

- **Cache multipliers.** Relative to base input price: a 5-minute write costs 1.25x, a 1-hour write 2x, and a read 0.1x (0.05x on Opus 5.5, 0.025x on Fable 5.1 and Mythos 5.1). They stack with the batch and data-residency modifiers.
- **Sonnet 5.** The price is $2 / $10; launch charts showing $3 / $15 don't apply.
- **Long context.** On 4.6 and later, the full 1M window bills at standard rates.
- **US-only inference.** `inference_geo` for US-only processing multiplies every token category by 1.1 on 4.6 and later models.
- **Fast mode.** A research preview on the Claude API only (not Bedrock, Claude Platform on AWS, Google Cloud or Foundry), set with `speed: "fast"` and the `fast-mode-2026-02-01` beta header. Opus 5.5 runs up to 2.5x faster at $8 / $40; Opus 5 and Opus 4.8 cost $10 / $50.
- **Tokenizer.** Claude 4.7 and later models, Opus 5.5 included, use a tokenizer that produces roughly 1x to 1.35x the tokens of earlier models, depending on content.

Plan and subscription usage in Claude Code is covered in [[costs-and-usage]].

## Lifecycle and deprecations

A model moves from Active to Legacy (no more updates), then Deprecated (still works, with a retirement date set), then Retired (requests fail). Anthropic gives at least 60 days' notice before retiring a public model. Dates below cover the Claude API, Claude Platform on AWS and Foundry.

| Model ID | Status | Retired no sooner than |
|---|---|---|
| `claude-fable-5-1` | Active | September 1, 2027 |
| `claude-fable-5` | Active | June 9, 2027 |
| `claude-opus-5-5` | Active | Not yet published |
| `claude-opus-5` | Active | July 24, 2027 |
| `claude-opus-4-8` | Active | May 28, 2027 |
| `claude-opus-4-7` | Active | April 16, 2027 |
| `claude-opus-4-6` | Active | February 5, 2027 |
| `claude-opus-4-5-20251101` | Active | November 24, 2026 |
| `claude-sonnet-5` | Active | June 30, 2027 |
| `claude-sonnet-4-6` | Active | February 17, 2027 |
| `claude-sonnet-4-5-20250929` | Active | September 29, 2026 |
| `claude-haiku-4-5-20251001` | Active | October 15, 2026 |

- **Retired on the Claude API.** Opus 4.1 (replaced by `claude-opus-4-8`), Opus 4, Sonnet 4, Sonnet 3.7, Haiku 3.5, Haiku 3 and older. Opus 4.1, Sonnet 4 and Haiku 3.5 remain on Bedrock and Google Cloud, and Opus 4 on Google Cloud.
- **Finding old model usage.** Claude Console > Usage > Export gives a CSV by API key and model.
- **Sampling parameters.** On Claude 4.7 and later, a non-default `temperature`, `top_p` or `top_k` returns a 400, and Python SDK v1.0 and later removes them.

## Opus 5.5 API behavior

**Breaking changes from Opus 5** (each returns a 400 `invalid_request_error`; the first three also apply to Fable 5.1):

- **Thinking can't be disabled.** `thinking: {"type": "disabled"}` and manual budgets (`{"type": "enabled", "budget_tokens": N}`) are rejected. Omit `thinking` or send `{"type": "adaptive"}`; the effort parameter (`low`, `medium`, `high`, `xhigh`, `max`) is the only thinking control.
- **Forced tool use is not supported.** `tool_choice` `any` or `tool` is rejected, including on token counting. Use `auto` (default) or `none`, add `strict: true` or structured outputs for schema-valid JSON, and say in the prompt when a tool applies.
- **Thinking blocks are tied to the model and conversation.** Opus 5.5 reads thinking blocks from Opus 5 and earlier Opus, Sonnet and Haiku models, not from Fable or Mythos. On the Claude API only Fable 5.1 and Mythos 5.1 read Opus 5.5's blocks. Unreadable blocks are dropped, not billed. For accounts created on or after August 31, 2026, replaying a block after editing the `system` prompt, `tools` or an earlier message returns a 400; the `thinking-binding-controls-2026-08-01` beta header with `prefix_mismatch_behavior: "drop_block"` drops them instead. Claude Code, the Agent SDK and Managed Agents are already append-only.
- **`computer_20251124` is rejected on the Claude API and Google Cloud.** Declare the `computer_toolset_20260801` toolset (no beta header, no `name` or display size) and handle member `tool_use` blocks, batch actions and `toolset_name`. Bedrock still accepts `computer_20251124`.

**Response changes.** Responses can begin with `thinking` blocks, empty at the default `display: "omitted"`, so read blocks by `type` and pass them back unmodified in tool loops. Text between tool calls arrives as progress-update `thinking` blocks, so a UI that shows it needs `display: "updates"` (beta, `thinking-display-updates-2026-08-18` header) or `"summarized"`. The model also thinks more per turn at a given effort than Opus 5, most at `xhigh` and `max`.

**Feature support.** Per-message effort (beta), mid-conversation system messages, task budgets, prompt caching with a 512-token minimum, batch, Files API, PDF, vision, server and client tools, compact on demand (`compact-2026-09-04` beta) and inline tool definitions in messages (`inline-tools-2026-09-15` beta). The 1M window needs no beta header. Priority Tier is not supported.

**Safeguards.** Opus 5.5 is the first Opus with Fable 5.1-class safeguards for cybersecurity, biology and distillation. A decline is HTTP 200 with `stop_reason: "refusal"` and a `stop_details` category such as `cyber`, `bio` or `reasoning_extraction`. Server-side fallback (`fallbacks: "default"`, beta) retries on another model, except `reasoning_extraction` declines. Most cyber tasks reroute to Opus 4.8; in Anthropic's benchmarks, biology tasks fell back to Opus 5. Vetted organizations can apply to the Life Sciences Verification Program, and the Cyber Verification Program is expanding to Opus 5.5. Zero data retention is available, and outputs carry EU AI Act watermarking.

## Migrating to Opus 5.5

In Claude Code, `/claude-api migrate this project to claude-opus-5-5` runs the bundled Claude API skill, which applies the changes and returns a checklist; Managed Agents users only change the model name. From Opus 5, fix the four breaking changes above, then set `effort` explicitly and re-run your effort sweep, read content by `type`, set `display` if your UI shows text between tool calls, handle refusals, and re-baseline cost and latency (at `xhigh` or `max`, start `max_tokens` at 64k). From Opus 4.8 or earlier, also budget `max_tokens` for thinking on requests that ran without it, and plan around Priority Tier. From Opus 4.6 or earlier, also drop sampling parameters, budget-based thinking and prefills, and re-test token counts.

## Fable 5.1 specifics

- **Cost.** Anthropic estimates its cheaper cache read cuts typical costs by about 25% against Fable 5 (up to 45% for highly agentic work).
- **Safeguards.** Many cyber and biology queries are rerouted, not charged at Fable prices: cyber to Opus 4.8, biology to Opus 5. It may find vulnerabilities but not develop exploits.
- **Data retention.** 30-day retention by default; eligible enterprises can use zero data retention until Enterprise Frontier Safeguards arrives.
- **Effort defaults.** High in Claude Code; Medium in Claude Cowork and on claude.ai.

## Benchmark highlights

**Opus 5.5** launch results (adaptive thinking at max effort unless noted, with production safeguards on):

| Benchmark | Opus 5.5 | Fable 5.1 | Opus 5 |
|---|---|---|---|
| Terminal-Bench 4.0 (Opus 5.5 at xhigh) | 66.4% | 55.8% | 52.3% |
| FrontierCode v1.1 (Main) | 54.4% | 50.3% | 48.0% |
| CursorBench 4.0 | 57.8% | 51.8% | 46.6% |
| GDPval-AA v2.1 (Elo) | 1846 | 1735 | 1708 |
| OSWorld 2.0 (partial) | 81.8% | 80.7% | 74.0% |

Anthropic says the real-world gap to Fable 5.1 is narrower than these scores suggest. Opus 5.5 scores best of any model on Anthropic's automated behavioral audit ([[trustworthy-agents]]).

**Opus 5** (max effort): SWE-bench Verified 96.0%, SWE-bench Pro 79.2, OSWorld 2.0 70.6. It hallucinates slightly more than Opus 4.8 and delegates to subagents readily ([[agent-sdk-control]]).

**Sonnet 5** performs close to Opus 4.8 (SWE-bench Verified 85.2%, Terminal-Bench 2.1 80.4), is much weaker at cyber tasks than Opus models, and over-refuses more often.

For how to read benchmark numbers, see [[agent-evals]].
