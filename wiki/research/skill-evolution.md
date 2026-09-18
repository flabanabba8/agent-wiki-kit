---
title: Skill Evolution
type: research
tldr: "Research on evolving agent skills from traces"
sources:
  - raw/articles/skillopt-2026.pdf
  - raw/articles/skillsvote-2026.pdf
  - raw/articles/hasp-2026.pdf
  - raw/articles/skillclaw.md
  - raw/articles/skill-kd.md
  - raw/articles/muse-autoskill.md
  - raw/articles/after-procedural-memory.md
related: ["[[skills]]", "[[agent-standards]]", "[[self-improving-agents]]", "[[agent-evals]]", "[[plugins]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: medium
last_verified: 2026-09-15
aliases: [skillopt, skillsvote, hasp-program-functions, skill-kd, muse-autoskill]
---

# Skill Evolution

This 2026 research line treats an agent's **skills** (usually `SKILL.md` files in the [[agent-standards]] format) as trainable state for a frozen model. Each system turns execution traces into edits to the skill library and must decide which edits to trust. For how skills work in Claude Code, see [[skills]].

| System | Skill form | Update signal | Gate before an edit sticks | Headline |
|---|---|---|---|---|
| SkillOpt | One skill document | Scored rollouts, minibatch reflection | Must strictly beat a held-out validation score | Best or tied on 52/52 cells |
| SkillsVote | Open-source skill library | Subtask-level attribution | Only successful subtasks with reusable exploration | Terminal-Bench 2.0 +7.9 pp |
| HASP | Executable Program Functions | Recurring failure→repair patterns | Executable validation plus teacher review | Web search 60.3% (7B) |
| SkillClaw | Shared multi-user repository | Sessions grouped by skill | Nightly A/B run in real environments | Creative Synthesis 11.57% → 21.80% |
| SKILL-KD | Textual rule library | Teacher-vs-student trajectory contrast | Student rerun must succeed | Qwen3.5-4B avg 43.5 → 66.8 |
| MUSE-Autoskill | Skill package plus `.memory.md` | Agent's own successful trajectory | Bundled unit tests or sandbox checks | Covered tasks 85.24% vs human skills 81.17% |
| AFTER | Benchmark | — | — | Diverse traces: 73.1% cross-model |

## SkillOpt: a text-space optimizer

SkillOpt (Microsoft et al., arXiv 2605.23904) trains a skill the way you would train weights, with a separate optimizer model:

- **Forward pass.** The frozen target runs a batch of 40 rollouts with the current skill.
- **Backward pass.** Failure minibatches propose corrections; success minibatches protect behaviors that already work.
- **Bounded update.** A *textual learning rate* L_t caps the number of add/delete/replace edits per step (default 4, cosine decay to 2).
- **Validation gate.** The candidate is accepted only if it scores strictly higher on a held-out split. Ties are rejected.
- **Rejected-edit buffer and slow/meta update.** Failed edits are remembered for the rest of the epoch, and a protected region holds lessons learned across epochs.

The output, `best_skill.md`, adds zero model calls at deployment.

**Results** (held-out test splits):

- GPT–5.5 no-skill average rises **+23.5** in direct chat, **+24.8** in the Codex harness and **+19.1** in the Claude Code harness.
- SpreadsheetBench goes 41.8 → 80.7 and OfficeQA 33.1 → 72.1 (GPT–5.5, direct chat).
- Final skills are 379–1,995 tokens and came from only 1–4 accepted edits. OfficeQA's +39.0 came from a single edit.
- Removing slow/meta updates dropped SpreadsheetBench from 77.5 to 55.0.
- A SpreadsheetBench skill trained in Codex scored 22.1 → 81.8 when moved into Claude Code.

## SkillsVote: governing a skill library

SkillsVote (MemTensor, arXiv 2605.18401) manages a skill library across its whole lifecycle:

1. **Collection.** It profiles a million-scale GitHub `SKILL.md` corpus for runtime requirements, quality and verifiability.
2. **Recommendation.** Before a task, a separate agent searches the library and exposes only a few matching skills with a usage guide.
3. **Attribution.** After a task, it splits the trajectory into subtasks. Each has one objective, one evaluation signal and at most one skill.
4. **Evidence-gated update.** Only successful subtasks with reusable exploration can edit a skill or create a new one.

**Results** (Codex with GPT-5.2):

- **Terminal-Bench 2.0:** offline evolution 51.0 → 58.9 (+7.9 pp); online +2.7.
- **SWE-Bench Pro:** online 47.6 → 50.2 (+2.6).

Exposing skills is not neutral. On the Hard subset, exposing the online library without recommendation gave mean task-level gain/loss of +3.3/−6.7; with recommendation it was +6.0/−6.0.

## HASP: skills as executable guardrails

HASP (NYU and Salesforce, arXiv 2605.17734) turns skills into **Program Functions (PFs)** with two parts: `should_activate` checks the current state and proposed action, and `intervene` either rewrites the action or injects corrective context.

On Qwen2.5-7B-Instruct:

- **PF-only intervention:** web-search average 51.0%, vs 20.5% for the same skills as prompt text.
- **With a teacher selecting PFs:** 56.2%.
- **HASP-Evolve + rejection sampling:** 60.3% web search, 45.4% math, 69.9% average coding pass@1.
- **Evolution without filtering:** collapses to 36.3%.

65.1% of fired interventions changed the action itself.

## SkillClaw: collective evolution across users

SkillClaw (arXiv 2604.08377) collects sessions from many users, groups them by the skill they invoked, and gives each group to an agentic evolver. The evolver chooses to refine, create or skip, treating successful sessions as invariants to preserve. At night, candidate skills are A/B-run in idle user environments, and only improvements are deployed.

In a 6-day simulation with 8 users on WildClawBench (Qwen3-Max):

| Category | Day 1 | Day 6 |
|---|---|---|
| Social Interaction | 54.01% | 60.34% |
| Search & Retrieval | 22.73% | 34.55% |
| Creative Synthesis | 11.57% | 21.80% |
| Safety & Alignment | 24.00% | 32.00% |

Three controlled queries averaged 30.4% → 72.5%. Gains were largest where failures came from missing procedural knowledge.

## SKILL-KD: teacher-to-student distillation

SKILL-KD (arXiv 2607.28048) contrasts a weaker student's failure with a stronger teacher's trajectory on the same task and writes a skill patch. It then reruns the student and refines the patch until the student succeeds or the round budget runs out. A consolidation agent reads a trace-linked edit history and decides add, modify, delete or skip.

**Results:**

- **Qwen3.5-4B with Qwen3.7-plus as teacher:** 43.5 → 66.8 average (SkillOpt 63.5) with only 38 rules and 3,010 words. Student-only reflection produced 96 rules.
- **Qwen3.6-35B-A3B with ChatGPT-5.5:** 57.9 → 74.6.
- **Without consolidation:** LiveMath fell from 54.8 to 27.4.

The paper names three kinds of drift: case-specific, skill-bloat and destructive-update.

## MUSE-Autoskill: lifecycle-managed skills

MUSE-Autoskill (ByteDance, arXiv 2605.27366) covers creation, memory, management, evaluation and refinement in one agent:

- A `skill_create` tool builds skills inside the agent's own loop.
- A `tests/` directory blocks registration until the tests pass.
- Each skill has a `.memory.md` file for per-skill lessons.

**SkillsBench results** (75 tasks, all agents on GPT-5.5):

- **With human skills:** MUSE 59.67%; human skills lift every agent by +10.78 to +13.73 pp.
- **Self-created skills:** MUSE 53.42%, Codex 47.52%, Claude Code 44.27%.
- **On the 47 tasks where MUSE created a skill:** 85.24%, above human skills at 81.17%.
- **Transfer:** MUSE-created skills lifted Hermes to 51.90%.

Coverage is the bottleneck: 28 of 75 tasks got no usable skill. One skill regressed its task from 80% to 20%.

In this paper, the Claude Code runs used **GPT-5.5 through a compatibility bridge**, not a Claude model.

## AFTER: does procedural memory transfer?

AFTER (arXiv 2606.23127) is a benchmark of 382 enterprise tasks across 6 roles and 22 skills.

**Benefits:**

- Static skills add **+2.8** full-pass points on average.
- One refinement round adds **+3.7 to +6.7** aggregate.
- Skills evolved from diverse multi-model traces reach **73.1%** cross-model accuracy, vs 36.0–59.4% from any single model's traces. Weaker source models gave more transferable signal.

**Limits:**

- Transfer across roles breaks. A pdf skill gained +11.7 within PM and +6.2 within DS, but lost 4.8 to 7.5 points when moved to the other role.
- Large training gains can vanish on held-out tasks. EvoSkill's narrow run gained +14.9 on train and lost 2.7 on test.

## Patterns across the papers

- **Gate every edit** on held-out validation, a student rerun, tests or a real A/B run. Ungated evolution degrades (HASP 36.3%).
- **Keep edits small and traceable.** Bounded updates, edit histories and protected regions prevent drift and bloat.
- **Control exposure.** Irrelevant skills in context cause regressions.
- **Transfer is uneven.** Skills often move across models and harnesses, less reliably across roles.

## What this means for Claude Code users

- Test a skill before keeping an edit to it. Plugin evals are one way to do that ([[plugins]], [[agent-evals]]).
- Prefer a few short, procedural rules over long skill files, and keep unrelated skills out of the listing budget ([[skills]]).
- Validate skills from public marketplaces before using them. Execution requirements vary ([[agent-standards]]).
- Related non-skill loops are covered on [[self-improving-agents]].
