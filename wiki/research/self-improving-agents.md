---
title: Self-Improving Agents
type: research
tldr: "Five training-free agent self-improvement loops"
sources:
  - raw/articles/rehearse-confidence-cliff.md
  - raw/articles/self-compacting-agents.md
  - raw/articles/agentic-context-engineering.md
  - raw/articles/autoskill.md
  - raw/articles/contextual-experience-replay.md
related: ["[[context-engineering]]", "[[context-window]]", "[[long-running-agents]]", "[[skill-evolution]]", "[[agent-memory]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: medium
last_verified: 2026-09-15
aliases: [rehearse, selfcompact, agentic-context-engineering, autoskill, contextual-experience-replay]
---

# Self-Improving Agents

These five papers make an agent better over time **without changing model weights**. Each changes what goes into the context: a memory of past outcomes, a compaction decision, an evolving playbook, extracted skills, or replayed experience. Skill-library optimizers are covered on [[skill-evolution]], and memory stores on [[agent-memory]].

| Method | What improves | Store | Learning signal | Headline result |
|---|---|---|---|---|
| Rehearse | Choosing which experiment to run | Similar past changes plus a worked/didn't-work label | Measured training outcomes | Late-loop selective accuracy 56.9% → 83.5% |
| SelfCompact | When to compact context | None (rubric plus summarize tool) | Rubric verdict on the trajectory | Up to +18.1 points on math |
| ACE | System prompt or agent memory | Itemized bullet playbook | Execution feedback, labels optional | +10.6% on agents, +8.6% on finance |
| AutoSkill | Personalization across sessions | Versioned SKILL.md files | User queries only | 1,858 skills extracted from WildChat |
| CER | Web navigation | Environment dynamics plus skills buffer | Past trajectories | WebArena 36.7% |

## Rehearse: the confidence cliff

In autoresearch loops (propose a code change, run training, keep it if the metric improves), the share of helpful changes in public AutoSOTA logs falls from **70% in iterations 1–2 to 43% by iteration 6+**. Rehearse (arXiv 2607.27687) built a 366-pair benchmark from 39 AutoSOTA tasks to test whether an LLM judge can tell, before training, which of two proposed changes will help.

- With no history, the judge reaches **79.5%** selective accuracy on the 296 pairs where one change worked and one didn't.
- As successes accumulate, a memoryless judge drops from **82.8% to 56.9%** selective accuracy while giving verdicts *more* often (76% → 85% coverage). The authors call this the **confidence cliff**.
- The fix is to show the judge only the few most similar past attempts, one line each: what changed, and whether it worked. That holds late-loop accuracy at **83.5%**. A full-history dump gets 70.8%, a Reflexion-style buffer 74.1%, and an LLM summary 80.9%.
- Adding recorded failure reasons *lowers* accuracy (83.5% → 80.6%).

The loop becomes Propose, Predict, Execute: propose 5 candidates, rank them with a two-order strict-consensus pairwise tournament, and run only the top one. Across 4,000 budgeted training runs:

- **nanochat:** vanilla 7.1%, propose-many 6.9%, select 8.4%, Rehearse 10.7% mean improvement.
- **CIFAR-10:** accuracy gain 2.85% vs 2.10%.
- **ETTh1:** MSE reduction 54.0% vs 40.1%.

Models were hy3-preview, glm-5.1 and deepseek-v4. Rehearse ships as a skill backed by plain files.

## SelfCompact: letting the model decide when to compact

Fixed token-threshold compaction can erase verified facts mid-derivation. SelfCompact (arXiv 2606.23525) gives the model two things: a summarization tool, and a rubric that says **fire** when a sub-task has resolved or the trajectory is converging, and **suppress** when the model is mid-derivation or stuck. The probe appends to the cached prefix, so it costs almost nothing.

| Model / benchmark | No compaction | Fixed interval | SelfCompact |
|---|---|---|---|
| Qwen3.5-9B, HMMT Feb 26 | 34.2 | 44.9 | 52.3 (+18.1) |
| GLM-4.7-Flash, 3-benchmark search average | 36.6 | 41.5 | 46.4 |
| MiniMax-M2.5, BrowseComp-Plus cost per question | $0.19 | $0.04 | $0.07 (−63% vs no compaction) |

Both parts are needed. With the tool but no rubric, GLM-4.7-Flash averages 41.0%, no better than fixed intervals. Fixed-interval summarization on Qwen3-4B (IMO-Answerbench) flipped 1,009 answers from correct to wrong alongside 1,486 wrong to correct. Only open-weight models were tested; the authors note frontier models may detect context rot without a rubric.

## ACE: contexts as evolving playbooks

Agentic Context Engineering (arXiv 2510.04618, ICLR 2026) splits the work into a **Generator** that produces trajectories, a **Reflector** that extracts lessons, and a **Curator** that writes small delta updates. The context is a list of bullets, each with an ID and helpful/harmful counters. Non-LLM logic merges deltas and removes near-duplicates using embeddings.

It targets two failure modes:

- **Brevity bias:** optimizers drift toward short, generic prompts.
- **Context collapse:** asking an LLM to rewrite the whole context. On AppWorld, a context of 18,282 tokens (66.7 accuracy) collapsed in one step to 122 tokens (57.1), below the 63.7 no-adaptation baseline.

Results with DeepSeek-V3.1:

- **AppWorld:** 59.4% average for ReAct + ACE, matching the top leaderboard agent IBM CUGA (60.3%, GPT-4.1). Without ground-truth labels it still gains +14.8 over ReAct.
- **Finance:** FiNER/Formula average 69.1 → 81.9 offline, with labels.
- **Cost:** adaptation latency is 82.3% lower and rollouts 75.1% fewer than GEPA on AppWorld.
- **Caching:** with GPT-5.1, 91.8% of input tokens were served from cache.

Without reliable feedback, both ACE and Dynamic Cheatsheet can degrade. Online ACE without labels scored 67.3 on FiNER vs a 70.7 base.

## AutoSkill: skills from user interaction

AutoSkill (arXiv 2603.01145) turns recurring user preferences into versioned `SKILL.md` artifacts without retraining.

1. An extractor proposes a skill candidate from **user queries only**, never model responses.
2. The candidate is compared with its most similar existing skill (dense embedding plus BM25).
3. A judge chooses add, merge (with a version bump) or discard.
4. Relevant skills are retrieved and injected into later requests.

It runs as an SDK, a web UI, or an OpenAI-compatible proxy. Applied to WildChat-1M conversations longer than 8 turns, it extracted 1,858 skills across four subsets. One skill, `professional_text_rewrite`, reached version 0.1.34 after 34 merges. The paper reports no task-accuracy benchmark.

## CER: contextual experience replay

CER (arXiv 2506.06698, ACL 2025) distills two things from past web trajectories: **environment dynamics** (page summaries with URLs) and **skills** (step-by-step workflows with abstracted variables). It retrieves up to 5 of each for a new task and replays them in context. It works offline, online, or both (hybrid).

- **WebArena, GPT-4o:** hybrid 36.7% vs a 24.3% BrowserGym baseline (51.0% relative) for 17.3% more input tokens.
- **VisualWebArena:** 31.9%, beating tree search at much lower token cost.

Filtering to successful trajectories only helped slightly (33.5 vs 31.4). Unstructured self-exploration trajectories used as offline data made hybrid worse than online-only on the Forum split (35.1 vs 37.7).

## Patterns across the papers

- **Focused beats exhaustive.** Relevant, outcome-labeled records outperform full-history dumps (Rehearse). Itemized deltas outperform full rewrites (ACE).
- **Timing is a capability.** A short rubric supplies it for compaction (SelfCompact).
- **Feedback quality limits every loop.** ACE and CER degrade on noisy or unverified signals.
- **Store explicit, inspectable artifacts.** Bullets, SKILL.md files and plain-file stores can be audited and edited by hand.

## What this means for Claude Code users

- Compact at natural boundaries (after a sub-task resolves), not mid-derivation. See [[context-window]] and [[context-engineering]].
- For long autonomous loops, keep a short worked/didn't-work log of attempts and feed back only the relevant entries ([[long-running-agents]]).
- Save lessons as small, separate edits to CLAUDE.md or skills instead of rewriting the whole file ([[claude-md-and-memory]], [[skills]]).
- Research on optimizing skill libraries is on [[skill-evolution]].
