---
title: Claude Code in Practice
type: research
tldr: "Domain expertise matters more than coding"
sources:
  - raw/articles/anthropic-claude-code-expertise.md
  - raw/articles/measuring-agent-autonomy.md
related: ["[[permissions-and-modes]]", "[[prompting-and-workflows]]", "[[how-claude-code-works]]", "[[headless-mode]]", "[[enterprise-admin]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [claude-code-usage-study, domain-expertise-vs-coding-skill, does-domain-knowledge-matter-more-than-coding-skill, returns-to-expertise, auto-approve-rates, agent-autonomy-study]
---

# Claude Code in Practice

Two Anthropic studies measure real Claude Code usage with privacy-preserving analysis. All classifications are made by Claude reading transcripts or tool calls, so treat the numbers as model-estimated.

| Study | Published | Data | Scope |
|---|---|---|---|
| Measuring AI agent autonomy in practice | Feb 18, 2026 | Millions of interactions across interactive Claude Code sessions and the public API; late 2025 to early 2026 | Autonomy, oversight, risk |
| Agentic coding and persistent returns to expertise | Jun 16, 2026 | ~400,000 interactive sessions from ~235,000 people, October 2025 to April 2026 | Work types, division of labor, success |

The expertise study covers the CLI, Claude.ai and the Claude Code desktop app. It excludes third-party IDEs, SDKs and headless `claude -p` runs, and its classifiers use Claude Sonnet 4.6.

## What people use it for

| Work mode | Share of sessions |
|---|---|
| Writing code | 25% |
| Fixing code | 26% |
| Testing and orchestrating | 5% |
| Operating software (deploy, configure, run, monitor) | 17% |
| Planning or exploring | 14% |
| Analysis or prose | 13% |

Between October 2025 and April 2026:

- Fixing broken code fell from 33% to 19% of sessions.
- Operating software grew from 14% to 21%.
- Writing and data analysis roughly doubled, from about 10% to 20%.
- The estimated value of the average session, benchmarked against freelance job postings, rose 27% ("about 25%" in the key findings). Building, operating and fixing tasks rose about 43%, 34% and 32%. These are coarse, relative estimates.

## Division of labor

- **Decisions.** Users make about **70%** of planning decisions (what to do) but only **20%** of execution decisions (how to do it).
- **Shape of a session.** A typical session has about four turns. Each prompt triggers around 10 Claude actions on average, sometimes over 100, and about 2,400 words of output per turn.
- **Control changes activity.** When the user makes over 80% of execution decisions, Claude takes about eight actions per turn. When Claude makes over 80% of planning decisions, it takes about 16.
- **The tail is long.** About 2% of sessions average more than 100 actions per prompt, 1 in 270 more than 200, and 1 in 2,300 more than 500.

## Does domain knowledge matter more than coding skill?

Domain expertise, not coding proficiency, is what amplifies effective use of the tool: success is determined by how well a person understands the problem they are trying to solve, not whether they are trained in coding. The ability to steer Claude toward success comes more from command of a domain than from the ability to write code, and a working grasp of the domain captures most of the benefit — deep specialization adds only a little beyond it.

Expertise was rated per task on a five-point scale. The signals were how precise the user's directions were, what they asked Claude to verify, and who corrected whom. A senior engineer asking a first Rust question counts as a beginner at that task.

| Measure | Novice | Intermediate and up |
|---|---|---|
| Claude actions per prompt | ~5 | 12 (expert) |
| Words of output per prompt | ~600 | 3,200 (expert) |
| Verified success | 15% | 28-33% |
| At least partial success | 77% | 91-92% |
| Verified success, sessions that hit trouble | 4% | 15% (expert) |
| Partial success, sessions that hit trouble | 60% | 80-81% |
| Troubled sessions abandoned (failed, zero lines written) | 19% | 5-7% |

**Verified success** requires a session judged successful *and* at least one hard signal: matching commits or PRs, passing tests, or explicit user confirmation. Sessions with "no clear goal" (about 7.7%) are excluded. After controls, each expertise level adds +9% actions and +13% output. Most of the gain comes between novice and intermediate.

**Occupation matters less than expertise.**

- Software-related occupations reach verified success in about 30% of sessions, other occupations about 26%.
- In code-producing sessions, the figures are 34% and 29%. At least partial success is 89% and 88%.
- All ten largest occupations are within seven points of software/math users. Management occupations are highest on verified success.
- Expert sessions that hit trouble tend to involve harder problems, which complicates recovery comparisons.

## Autonomy and oversight

| Finding | Value |
|---|---|
| Median turn duration | ~45 seconds (between 40 and 55 seconds over the period) |
| 99.9th percentile turn duration | Under 25 minutes → over 45 minutes, October 2025 to January 2026, smooth across model releases |
| Anthropic internal: success rate on hardest tasks, August to December | Doubled |
| Anthropic internal: human interventions per session | 5.4 → 3.3 |
| Full auto-approve | ~20% of sessions for new users (<50 sessions) → over 40% by 750 sessions |
| Interrupt rate | 5% of turns at ~10 sessions → ~9% for experienced users |

Experienced users approve fewer individual actions but interrupt more. They shift from approving each step to monitoring and intervening. Claude Code's defaults require manual approval, so part of this shift is users reconfiguring the product. The authors describe a "deployment overhang": models can handle more autonomy than they get in practice. For comparison, METR estimates Claude Opus 4.5 completes tasks that would take a human nearly 5 hours with a 50% success rate. The authors stress that METR's figure measures task difficulty, not runtime, so the two aren't directly comparable.

On the most complex tasks, **Claude asks for clarification more than twice as often as on minimal-complexity tasks**, and more often than humans interrupt it.

| Why Claude stops itself | Share | Why humans interrupt | Share |
|---|---|---|---|
| Offer a choice between approaches | 35% | Provide missing technical context or corrections | 32% |
| Gather diagnostic information or test results | 21% | Claude was slow, hanging or excessive | 17% |
| Clarify vague or incomplete requests | 13% | Got enough help to proceed alone | 7% |
| Request missing credentials, tokens or access | 12% | Want to take the next step themselves | 7% |
| Get approval before acting | 11% | Change requirements mid-task | 5% |

**Public API context** (998,481 sampled tool calls):

- Software engineering is nearly 50% of tool calls.
- 80% come from agents with at least one safeguard. The authors treat this as an upper bound.
- 73% appear to have a human in the loop.
- Only 0.8% of actions appear irreversible.
- Human involvement is 87% on minimal-complexity tool calls vs 67% on high-complexity ones.

**Recommendations from the authors:**

- Invest in post-deployment monitoring.
- Train models to recognize their own uncertainty.
- Design products for monitoring and simple intervention, such as real-time steering and OpenTelemetry.
- Don't mandate approve-every-action rules, which "create friction without necessarily producing safety benefits."

## What this means for Claude Code users

- **Bring the domain knowledge.** Frame directions precisely, say what "done" means, and ask Claude to verify with tests or commits ([[prompting-and-workflows]]).
- **Match oversight to experience.** Moving from per-action approval to monitoring and interrupting is how experienced users work. The modes that support this are on [[permissions-and-modes]].
- **Expect questions on hard tasks.** Clarifying stops are part of how the agent loop works ([[how-claude-code-works]]).
- **Organization-level monitoring.** OpenTelemetry and usage analytics are covered in [[enterprise-admin]].
- **Automated runs weren't measured.** The expertise study excluded `claude -p` usage ([[headless-mode]]).
