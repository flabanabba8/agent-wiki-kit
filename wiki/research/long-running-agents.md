---
title: Long-Running Agents
type: research
tldr: "Harnesses for multi-hour and multi-day runs"
sources:
  - raw/articles/effective-harnesses.md
  - raw/articles/harness-design-long-running-apps.md
  - raw/articles/long-running-claude.md
  - raw/articles/building-c-compiler.md
related: ["[[context-engineering]]", "[[agent-evals]]", "[[agentic-patterns]]", "[[agent-teams]]", "[[headless-mode]]", "[[agent-sdk]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [agent-harness-design, planner-generator-evaluator, ralph-loop, c-compiler-agent-team, context-resets]
---

# Long-Running Agents

A long-running agent works across many context windows, and each new session starts with no memory of the last. Anthropic has published four harness designs for this. The recurring lesson is that most of the effort goes into the environment around the model: specs, progress files, tests and verifiers.

| Post | Model | Task | Key structure |
|---|---|---|---|
| Effective harnesses (Nov 2025) | Opus 4.5 on the Claude Agent SDK | claude.ai clone web app | Initializer agent + coding agent |
| Harness design (Mar 2026) | Opus 4.5, then Opus 4.6 | Full-stack apps (game maker, DAW) | Planner / generator / evaluator |
| Long-running Claude (Mar 2026) | Claude Opus 4.6 in Claude Code | Differentiable cosmological Boltzmann solver in JAX | CLAUDE.md plan, progress file, test oracle, Ralph loop |
| C compiler (Feb 2026) | Opus 4.6 in Claude Code | Rust C compiler able to build Linux | 16 parallel agents with git task locks |

## 1. Initializer + coding agent

Compaction alone wasn't enough. Given only "build a clone of claude.ai", Opus 4.5 failed in three ways: it tried to one-shot the app and ran out of context mid-feature, later sessions saw progress and declared the job done, and it marked features complete without end-to-end testing.

The two "agents" differ only in their first user prompt. The system prompt, tools and harness are identical.

| Problem | Initializer agent | Coding agent |
|---|---|---|
| Declares victory too early | Writes a structured JSON feature list from the spec | Reads the list and picks a single feature |
| Leaves bugs or undocumented progress | Creates a git repo and a progress notes file | Reads the notes and git log, runs a basic test, and ends the session with a commit and a progress update |
| Marks features done prematurely | Sets up the feature list | Marks a feature "passing" only after careful testing |
| Wastes time figuring out how to run the app | Writes `init.sh` to start the dev server | Reads `init.sh` at the start |

Details that mattered:

- The feature list had over 200 features, all initially `"passes": false`. Agents could change only that field, and the prompt warned: "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality." JSON was chosen because the model is less likely to rewrite it inappropriately than Markdown.
- The progress file was `claude-progress.txt`. Each session started by running `pwd`, reading the progress file and `feature_list.json`, checking `git log --oneline -20`, and smoke-testing the app before starting new work.
- End-to-end testing through the Puppeteer MCP server "dramatically improved performance." A remaining gap is that Claude can't see browser-native alert modals through that server.

## 2. Planner / generator / evaluator

This design is inspired by generative adversarial networks (GANs). It targets two failures:

- **Lost coherence and "context anxiety".** Claude Sonnet 4.5 wrapped up early as it approached what it believed was its limit, so the harness needed **context resets**. Opus 4.5 largely removed that behavior, so this harness dropped resets and relied on the Agent SDK's automatic compaction.
- **Lenient self-evaluation.** Agents "confidently praise" their own mediocre work. Tuning a separate evaluator to be skeptical is "far more tractable" than making a generator critical of itself.

**Frontend design experiment.** Four criteria went to both agents: design quality, originality, craft and functionality. Design quality and originality were weighted more heavily. The evaluator was calibrated with few-shot score breakdowns and used the Playwright MCP to navigate the live page. Runs used 5 to 15 iterations and took up to four hours. The wording of the criteria steered the output; "museum quality" pushed designs toward one visual style.

**Full-stack roles:**

- **Planner:** expands a 1-4 sentence prompt into an ambitious product spec. It covers product context and high-level design, not granular implementation, because spec errors cascade downstream.
- **Generator:** builds one feature at a time on a React, Vite, FastAPI and SQLite stack, uses git, and self-checks before QA.
- **Evaluator:** clicks through the running app with the Playwright MCP and grades product depth, functionality, visual design and code quality. Each criterion has a hard threshold.
- **Sprint contracts:** before each sprint, the generator and evaluator agree on what "done" means. They communicate through files.

**Results with Opus 4.5** (prompt: a 2D retro game maker):

| Harness | Duration | Cost |
|---|---|---|
| Solo | 20 min | $9 |
| Full harness | 6 hr | $200 |

The harness cost over 20x more. The solo app's game was broken, while the harness app was playable. The planner produced a 16-feature spec across ten sprints, and Sprint 3 alone had 27 criteria. Out of the box, "Claude is a poor QA agent": it found real issues and then talked itself into approving the work. The fix was several rounds of reading evaluator logs and correcting the prompt where its judgment diverged from the author's.

**Simplifying for Opus 4.6.** "Every component in a harness encodes an assumption about what the model can't do on its own." Removing one component at a time showed the following:

- The sprint construct could go.
- The planner stayed, because without it the generator under-scoped.
- The evaluator moved to a single pass at the end. It is worth its cost only when the task sits beyond what the model does reliably solo.

The updated harness built a browser DAW (digital audio workstation):

| Phase | Duration | Cost |
|---|---|---|
| Planner | 4.7 min | $0.46 |
| Build (Round 1) | 2 hr 7 min | $71.08 |
| QA (Round 1) | 8.8 min | $3.24 |
| Build (Round 2) | 1 hr 2 min | $36.89 |
| QA (Round 2) | 6.8 min | $3.09 |
| Build (Round 3) | 10.9 min | $5.88 |
| QA (Round 3) | 9.6 min | $4.06 |
| **Total** | **3 hr 50 min** | **$124.70** |

QA still caught stubbed features, such as recording that toggled a button but never captured audio.

## 3. Multi-day scientific computing in Claude Code

The setup had four parts:

- **CLAUDE.md plan:** deliverables and an accuracy target of 0.1% against the reference CLASS implementation. Claude could edit the plan as it worked.
- **Progress file (`CHANGELOG.md`):** current status, completed tasks, accuracy tables, known limitations and **failed approaches** ("Tried using Tsit5 for the perturbation ODE, system is too stiff. Switched to Kvaerno5."). Without the failed approaches, later sessions retry the same dead ends.
- **Test oracle:** unit tests continuously run against the CLASS C source.
- **Git as coordination:** for example, "Commit and push after every meaningful unit of work. Run `pytest tests/ -x -q` before every commit."

Claude Code ran in tmux on a SLURM node (`tmux new-session -d -s claude "claude; exec bash"`). To counter "agentic laziness", the author used the **Ralph loop**, which pushes the agent back to work when it claims completion. The post says Ralph installs via `/plugin`, and that Claude Code's native `/loop` is a similar pattern.

```text
/ralph-loop:ralph-loop "Please keep working on the task until the success criterion of 0.1% accuracy across the entire parameter range is achieved." --max-iterations 20 --completion-promise "DONE"
```

Over a few days, the solver reached sub-percent agreement with CLASS. It isn't production-grade. For a while it tested only one fiducial parameter point, and it chased bugs a cosmologist would spot instantly. A tightly coupled pipeline like this suits one sequential agent that spawns subagents, not wide parallelism.

## 4. The C-compiler agent team

16 agents ran on Opus 4.6. Over nearly 2,000 Claude Code sessions across two weeks, they used 2 billion input tokens and 140 million output tokens, a total cost just under $20,000. The result is a clean-room, 100,000-line Rust compiler. It builds a bootable Linux 6.9 on x86, ARM and RISC-V, compiles QEMU, FFmpeg, SQlite, postgres and redis, and has a 99% pass rate on most compiler test suites, including the GCC torture test suite.

**Harness.** An infinite loop in a container runs `claude --dangerously-skip-permissions -p "$(cat AGENT_PROMPT.md)"`. Each agent's Docker container mounts a bare repo at `/upstream` and works in `/workspace`. Agents claim tasks by writing lock files to `current_tasks/`, and git sync forces a second claimant to pick another task. There is no orchestration agent.

**Lessons:**

- **The verifier must be nearly perfect,** "otherwise Claude will solve the wrong problem." When new features kept breaking old ones, a CI pipeline with stricter enforcement fixed it.
- **Avoid context pollution.** Print a few lines, log details to files, put `ERROR` and the reason on the same line so grep finds them, and pre-compute summary statistics.
- **Design for time blindness.** A default `--fast` test option runs a 1% or 10% random sample that is deterministic per agent but random across VMs.
- **Make parallelism possible.** Parallel work is easy with many independent failing tests. Compiling the Linux kernel is one giant task, so all 16 agents hit the same bug. Using GCC as a known-good oracle to compile a random subset of files split the work apart.
- **Give agents specialized roles:** deduplicating code, compiler performance, output-code efficiency, Rust design critique and documentation.

**Limits.** The compiler calls GCC for 16-bit x86, has a buggy assembler and linker of its own, and emits code less efficient than GCC with all optimizations disabled. Near the end, new features frequently broke existing functionality.

## What this means for Claude Code users

- `claude -p` loops and automation flags are covered in [[headless-mode]]. Scheduled and repeating runs are covered in [[routines-and-scheduling]].
- The compiler's harness was a bare-bones custom loop. Claude Code's built-in multi-instance feature is [[agent-teams]].
- Run `--dangerously-skip-permissions` only in a container or sandbox, as the compiler post insists ([[permissions-and-modes]], [[sandboxing-and-security]]).
- Put plans in CLAUDE.md, keep a progress file that records failed approaches, and give the agent an oracle. For grading the work, see [[agent-evals]]. For building custom harnesses, see [[agent-sdk]].
