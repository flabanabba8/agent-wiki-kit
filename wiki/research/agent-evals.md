---
title: Agent Evals
type: research
tldr: "Graders, pass@k vs pass^k, infra noise"
sources:
  - raw/articles/demystifying-evals.md
  - raw/articles/infrastructure-noise-evals.md
  - raw/articles/multi-agent-research-system.md
related: ["[[tool-design]]", "[[long-running-agents]]", "[[multi-agent-systems]]", "[[plugins]]", "[[headless-mode]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [demystifying-evals, pass-at-k, llm-as-judge, infrastructure-noise, eval-driven-development]
---

# Agent Evals

An **eval** gives an AI system an input and applies grading logic to its output. Agent evals are harder than single-turn evals because agents act over many turns, change state, and find valid paths the eval designer didn't anticipate. This page draws on "Demystifying evals for AI agents" (Jan 2026), "Quantifying infrastructure noise in agentic coding evals" (Feb 2026) and the evaluation section of the multi-agent research system post (Jun 2025).

## Vocabulary

| Term | Meaning |
|---|---|
| Task | One test with defined inputs and success criteria |
| Trial | One attempt at a task. Run several, because outputs vary. |
| Grader | Logic that scores part of the performance. A grader can hold multiple assertions (checks). |
| Transcript | The full record of a trial: outputs, tool calls, reasoning. For the API, this is the final messages array. |
| Outcome | The final state of the environment. For example, whether the reservation exists in the database, not whether the agent said "booked". |
| Evaluation harness | The infrastructure that runs tasks, records steps, grades and aggregates |
| Agent harness | The scaffold that makes a model an agent. Evaluating "an agent" means evaluating the harness and the model together. |
| Evaluation suite | A collection of tasks that share a broad goal |

## Grader types

| Type | Methods | Strengths | Weaknesses |
|---|---|---|---|
| Code-based | String match, fail-to-pass and pass-to-pass tests, static analysis, outcome verification, tool-call checks, transcript metrics | Fast, cheap, objective, reproducible, easy to debug | Brittle to valid variations, lacking nuance |
| Model-based | Rubric scoring, natural-language assertions, pairwise comparison, reference-based evaluation, multi-judge consensus | Flexible, scalable, handles open-ended output | Non-deterministic, costs more, needs human calibration |
| Human | SME (subject-matter expert) review, crowdsourcing, spot checks, A/B tests, inter-annotator agreement | Gold standard, calibrates model graders | Expensive, slow |

Scores can be **weighted** (combined scores must reach a threshold), **binary** (every grader must pass) or a hybrid. **Capability evals** should start at a low pass rate so there is a hill to climb. **Regression evals** should sit near 100%. Once capability tasks pass reliably, they can "graduate" into the regression suite.

## By agent type

| Agent | Typical grading | Benchmarks named |
|---|---|---|
| Coding | Deterministic tests, plus an LLM rubric for code quality and transcript checks | SWE-bench Verified (LLMs went from 40% to >80% in one year), Terminal-Bench |
| Conversational | Outcome state check, turn limit (e.g. <10 turns), tone rubric, and a second LLM simulating the user | τ-Bench, τ2-Bench |
| Research | Groundedness, coverage and source-quality checks. Calibrate rubrics against experts often. | BrowseComp |
| Computer use | Run in a real or sandboxed environment, then verify backend state, not just the confirmation page | WebArena, OSWorld |

## Non-determinism: pass@k vs pass^k

- **pass@k** is the probability of at least one success in k trials. It rises with k. Use it when one success is enough.
- **pass^k** is the probability that all k trials succeed. It falls with k. Use it when consistency matters, as in customer-facing agents. With a 75% per-trial success rate over 3 trials, (0.75)³ ≈ 42%.

The two are identical at k=1. By k=10, pass@k approaches 100% while pass^k falls to 0%.

## Roadmap from zero to trustworthy evals

| Step | Advice |
|---|---|
| 0. Start early | 20-50 simple tasks drawn from real failures is a great start. Early changes have large effects, so small samples suffice. The Research team began with about 20 queries, where one prompt tweak moved success from 30% to 80%. |
| 1. Use what you test manually | Turn bug-tracker and support-queue failures into tasks. |
| 2. Write unambiguous tasks | Two domain experts should independently reach the same verdict. Write a reference solution for each task. With frontier models, 0% pass@100 usually means the task is broken, not that the agent can't do it. |
| 3. Balance the problem set | Test both when a behavior should happen and when it shouldn't. Claude.ai's web-search evals covered both over-triggering and under-triggering. |
| 4. Isolate trials | Start each trial from a clean environment. In one internal eval, Claude gained an unfair advantage by reading git history from previous trials. |
| 5. Design graders | Prefer deterministic graders, use LLM graders where needed, and use humans judiciously. Grade the outcome, not the exact path. Give partial credit. Let LLM judges answer "Unknown". Make graders resistant to cheating. |
| 6. Read transcripts | Transcripts tell you whether a failure was the agent's mistake or a grader rejecting a valid solution. |
| 7. Watch for saturation | An eval at 100% gives no signal for improvement. Opus 4.5 scored 42% on CORE-Bench until grading bugs were fixed (for example, "96.12" was rejected when the expected value was "96.124991…") and a less constrained scaffold was used; then it scored 95%. |
| 8. Maintain ownership | A dedicated evals team owns the infrastructure while domain experts contribute tasks. Practice eval-driven development. |

> [!contradiction]
> On LLM judges covering several quality dimensions, the two current sources disagree. "Demystifying evals" recommends grading "each dimension with an isolated LLM-as-judge rather than using one to grade all dimensions." The multi-agent research post found that "a single LLM call with a single prompt outputting scores from 0.0-1.0 and a pass-fail grade was the most consistent and aligned with human judgements."

For agents that change persistent state, the research post recommends **end-state evaluation**, with discrete checkpoints instead of turn-by-turn checks. Human testers still catch what automated evals miss; in that post, humans noticed agents preferring SEO content farms over authoritative sources.

No single method catches everything; the post compares this to the Swiss cheese model. Combine automated evals (pre-launch and in CI), production monitoring, A/B tests, user feedback, manual transcript review, and systematic human studies for calibration.

## Infrastructure noise

Anthropic ran Terminal-Bench 2.0 on Google Kubernetes Engine under six resource configurations, from strict enforcement of per-task specs (1x) to fully uncapped. The Claude model, harness and task set stayed the same.

| Comparison | Result |
|---|---|
| Infra error rate, 1x → uncapped | 5.8% → 0.5% |
| 1x → 3x | Infra errors 5.8% → 2.1% (p < 0.001); success change within noise (p=0.40) |
| 3x → uncapped | Infra errors fall another 1.6 points; success rises almost 4 points |
| Uncapped vs 1x overall | +6 percentage points (p < 0.01) |
| SWE-bench crossover (227 problems × 10 samples, RAM up to 5x) | Scores 1.54 points higher at 5x than 1x |

Up to about 3x, extra resources fix reliability problems such as transient spikes that get containers OOM-killed. Above 3x, they change **what the eval measures**. For example, on `bn-fit-modify`, installing the full Python data-science stack only works with generous memory. The team also saw pass rates vary anecdotally with time of day.

**Recommendations:**

- Specify both a guaranteed allocation and a separate hard kill limit per task, not one pinned value.
- Calibrate the band between them so scores at the floor and ceiling fall within noise.
- Report the multiplier you used.
- Treat resource configuration as a first-class experimental variable.
- Be skeptical of leaderboard differences **below 3 percentage points** until configurations are documented and matched. Naive binomial confidence intervals already span 1-2 points, and infrastructure noise stacks on top of that.

Frameworks named in the source are Harbor, Braintrust, LangSmith, Langfuse, and Arize (Phoenix and AX). They are "only as good as the eval tasks you run through them."

## What this means for Claude Code users

- To evaluate skills and plugin behavior, see the plugin eval tooling on [[plugins]].
- To run Claude Code non-interactively inside an eval harness, see [[headless-mode]]. To run evals in CI, see [[ci-cd-and-code-review]].
- To evaluate MCP tools specifically, see [[tool-design]].
- This repo's own retrieval eval is described in [[harness]].
