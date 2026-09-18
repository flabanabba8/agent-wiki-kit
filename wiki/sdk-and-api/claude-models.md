---
title: Claude Models
type: reference
tldr: "Claude 5 lineup: IDs, limits, prices, lifecycle"
sources:
  - raw/docs/models-overview-2026-09.md
  - raw/articles/anthropic-claude-opus-5.md
  - raw/articles/anthropic-claude-sonnet-5.md
  - raw/articles/anthropic-claude-fable-5-1.md
  - raw/articles/claude-opus-5-system-card-agentic-coding.md
  - raw/articles/claude-sonnet-5-system-card-agentic-coding.md
related: ["[[models-and-effort]]", "[[cloud-providers]]", "[[costs-and-usage]]", "[[trustworthy-agents]]", "[[agent-evals]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
valid_until: 2027-03-15
aliases: [claude-model-ids, claude-api-pricing, model-deprecations, claude-5-models, which-claude-model]
---

# Claude Models

This page lists the Claude models available on the Claude API as of September 2026, with IDs, limits, prices and lifecycle dates. For choosing models, aliases and effort inside Claude Code, see [[models-and-effort]]. For provider-specific IDs and setup, see [[cloud-providers]].

## Current lineup

| | Claude Fable 5.1 | Claude Opus 5 | Claude Sonnet 5 | Claude Haiku 4.5 |
|---|---|---|---|---|
| API ID | `claude-fable-5-1` | `claude-opus-5` | `claude-sonnet-5` | `claude-haiku-4-5-20251001` |
| Best for | Demanding reasoning, long-horizon agentic work | Most workloads; complex agentic coding and enterprise work | Best mix of speed and intelligence | Fastest responses |
| Input / output price per MTok | $10 / $50 | $5 / $25 | $2 / $10 | $1 / $5 |
| Context window | 1M | 1M | 1M | 200K |
| Max output | 128K | 128K | 128K | 64K |
| Thinking | Adaptive (always on) | Adaptive | Adaptive | Extended |
| Default effort | `high` | `high` | `high` | Not supported |
| Latency | Slower | Moderate | Fast | Fastest |
| Reliable knowledge cutoff | Jun 2026 | May 2026 | Jan 2026 | Feb 2025 |

Anthropic's guidance is to start with Opus 5 for most workloads, and move to Fable 5.1 when your evals on Opus 5 at higher effort still fall short. All four models accept text and image input and support tool use. The Models API returns `max_input_tokens`, `max_tokens` and a `capabilities` object for each model.

**Mythos.** Claude Mythos 5.1 is the same model as Fable 5.1 with different safeguards, at the same specs and prices. It is available only through Project Glasswing and Anthropic's trusted-access programs. `claude-mythos-preview` is deprecated, with `claude-mythos-5` as its replacement.

## Model IDs

- **4.6 generation and later.** IDs have no date: `claude-{name}-{major}[-{minor}]`, for example `claude-opus-5` or `claude-sonnet-4-6`. Each ID is a pinned snapshot, not an evergreen pointer, and updated versions ship under new IDs.
- **Earlier models.** IDs carry a snapshot date, as in `claude-sonnet-4-5-20250929`. On the Claude API these models also have aliases such as `claude-sonnet-4-5`, which point to the latest snapshot for that minor version.
- **Amazon Bedrock.** IDs add an `anthropic.` prefix (`anthropic.claude-opus-5`). Older dated Bedrock IDs end in `-v1:0`, and `anthropic.claude-opus-4-6-v1` is the last to carry a `-v1` suffix.
- **Google Cloud.** IDs use the Claude API format, except that older models put `@` before the date (`claude-haiku-4-5@20251001`).
- **Behavior drift.** An ID's weights never change, but the serving infrastructure around it (router, safety classifiers, sampling) can, which may cause small shifts in behavior.

## Pricing

Claude API prices in USD per million tokens:

| Model | Input | 5m cache write | 1h cache write | Cache read | Output | Batch input / output |
|---|---|---|---|---|---|---|
| Fable 5.1, Mythos 5.1 | $10 | $12.50 | $20 | $0.25 | $50 | $5 / $25 |
| Fable 5, Mythos 5 | $10 | $12.50 | $20 | $1 | $50 | $5 / $25 |
| Opus 5, 4.8, 4.7, 4.6, 4.5 | $5 | $6.25 | $10 | $0.50 | $25 | $2.50 / $12.50 |
| Sonnet 5 | $2 | $2.50 | $4 | $0.20 | $10 | $1 / $5 |
| Sonnet 4.6, 4.5 | $3 | $3.75 | $6 | $0.30 | $15 | $1.50 / $7.50 |
| Haiku 4.5 | $1 | $1.25 | $2 | $0.10 | $5 | $0.50 / $2.50 |

- **Cache multipliers.** Relative to base input price: a 5-minute write costs 1.25x, a 1-hour write 2x, and a read 0.1x (0.025x on Fable 5.1 and Mythos 5.1). They stack with the batch and data-residency modifiers.
- **Sonnet 5.** The standard price is $2 / $10. Some launch charts show $3 / $15, but that price doesn't apply.
- **Long context.** On 4.6 and later models, the full 1M context window is billed at standard rates, so a 900k-token request costs the same per token as a 9k one.
- **US-only inference.** Setting `inference_geo` for US-only processing multiplies every token category by 1.1 on 4.6 and later models.
- **Fast mode.** Fast mode is a research preview for Opus 5 and Opus 4.8, on the Claude API only, priced at $10 input / $50 output.
- **Tokenizer.** Claude 4.7 and later models use a newer tokenizer that produces about 30% more tokens for the same text, according to the pricing page. The Sonnet 5 announcement puts its tokenizer at roughly 1.0–1.35x, depending on content.

Plan and subscription usage in Claude Code is covered in [[costs-and-usage]].

## Lifecycle and deprecations

A model moves from Active to Legacy (no more updates), then Deprecated (still works, with a retirement date set), then Retired (requests fail). Anthropic gives at least 60 days' notice before retiring a publicly released model. The dates below apply to the Claude API, Claude Platform on AWS and Microsoft Foundry; Amazon Bedrock and Google Cloud set their own schedules.

| Model ID | Status | Retired no sooner than |
|---|---|---|
| `claude-fable-5-1` | Active | September 1, 2027 |
| `claude-fable-5` | Active | June 9, 2027 |
| `claude-opus-5` | Active | July 24, 2027 |
| `claude-opus-4-8` | Active | May 28, 2027 |
| `claude-opus-4-7` | Active | April 16, 2027 |
| `claude-opus-4-6` | Active | February 5, 2027 |
| `claude-opus-4-5-20251101` | Active | November 24, 2026 |
| `claude-sonnet-5` | Active | June 30, 2027 |
| `claude-sonnet-4-6` | Active | February 17, 2027 |
| `claude-sonnet-4-5-20250929` | Active | September 29, 2026 |
| `claude-haiku-4-5-20251001` | Active | October 15, 2026 |

- **Retired on the Claude API.** Opus 4.1 (`claude-opus-4-1-20250805`, replaced by `claude-opus-4-8`), Opus 4, Sonnet 4, Sonnet 3.7, Haiku 3.5, Haiku 3 and older models. Opus 4.1, Sonnet 4 and Haiku 3.5 remain on Bedrock and Google Cloud, and Opus 4 on Google Cloud.
- **Finding old model usage.** In the Claude Console, open Usage and click Export; the CSV breaks usage down by API key and model.
- **Deprecated parameters.** On Claude 4.7 and later, setting `temperature`, `top_p` or `top_k` to a non-default value returns a 400, and Python SDK v1.0 and later removes them. Guide behavior through prompting instead.

## Fable 5.1 specifics

- **Breaking changes for Fable 5 callers.** Forced tool use returns an error, earlier models can't read its thinking blocks, and editing earlier turns invalidates thinking blocks.
- **Additions.** Beta features: per-message effort, turn-scoped system messages, and readable progress updates between tool calls (`display: "updates"`). Also content provenance and the cheaper cache read.
- **Cost.** Anthropic estimates the cheaper cache reads cut typical workload costs by about 25% compared with Fable 5, and highly agentic workloads by up to about 45%.
- **Safeguards.** Many cybersecurity and biology queries are routed to other models, and rerouted requests aren't charged at Fable prices. In most Claude applications, cyber-flagged queries go to Opus 4.8 and biology-flagged queries to Opus 5; API customers set this up with the Fallback API. Fable 5.1 may be used to find software vulnerabilities but not to develop exploits.
- **Data retention.** Fable requires 30-day retention for safety monitoring by default. Eligible enterprise customers can use zero data retention until Enterprise Frontier Safeguards, which store data in customer-controlled cloud infrastructure, becomes available.
- **Effort defaults.** Fable 5.1 defaults to High effort in Claude Code, and to Medium in Claude Cowork and on claude.ai.

## Opus 5 and Sonnet 5 highlights

**Claude Opus 5** comes close to Fable 5's intelligence at half the price, and is the default model on Claude Max. System card results use adaptive thinking at max effort, averaged over 5 trials:

| Benchmark | Opus 5 | Opus 4.8 | Fable 5 |
|---|---|---|---|
| SWE-bench Verified | 96.0% | – | – |
| SWE-bench Pro | 79.2 | 69.2 | 80 |
| SWE-bench Multilingual | 89.5 | 84.4 | 86.6 |
| FrontierCode 1.1 (Main) | 53.4 | 46.5 | 53.5 |
| FrontierBench v0.1 | 43.3 | 21.1 | 33.8 |
| OSWorld 2.0 | 70.6 | 55.7 | 66.1 |
| BrowseComp | 90.8 | 84.3 | 87.4 |
| ARC-AGI-3 | 30.2 (high) | 1.5 | – |

- On Anthropic's automated behavioral audit, Opus 5 is its most aligned model to date, with an overall misaligned-behavior score of 2.3. Its biggest agentic-safety gains are in prompt-injection robustness.
- It is deployed under ASL-3 protections.
- It hallucinates factual claims slightly more than Opus 4.8, even though it is more accurate overall.
- It delegates to subagents readily, so cap depth and spend in SDK runs ([[agent-sdk-control]]).

**Claude Sonnet 5** performs close to Opus 4.8 and is the default model on the Free and Pro plans. System card results use adaptive thinking at max effort, averaged over 5 trials:

| Benchmark | Sonnet 5 | Sonnet 4.6 |
|---|---|---|
| SWE-bench Verified | 85.2% | – |
| SWE-bench Pro | 63.2 | 58.1 |
| Terminal-Bench 2.1 | 80.4 | 67.0 |
| OSWorld-Verified | 81.2 | 78.5 |
| BrowseComp | 84.7 (single agent), 86.6 (multi agent) | 76.2 |
| CursorBench (measured by Cursor) | 61.2% | 49% |

- Sonnet 5 shows less misaligned behavior than Sonnet 4.6, but more than Opus 4.8.
- It is much weaker at cyber tasks than Opus models, and ships with cyber safeguards on by default.
- It refuses malicious Claude Code cyber requests more reliably, but over-refuses more often.
- Its verbalized evaluation awareness is significantly higher than in earlier models.

Full safety and prompt-injection results are in [[trustworthy-agents]]. For how to read benchmark numbers, see [[agent-evals]].
