---
title: Karpathy Coding Principles
type: research
tldr: "Karpathy's four rules for LLM coding"
sources:
  - raw/articles/karpathy-coding-pitfalls.md
related: ["[[claude-md-and-memory]]", "[[prompting-and-workflows]]", "[[plugins]]", "[[skills]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: medium
last_verified: 2026-09-15
aliases: [karpathy-guidelines, andrej-karpathy-skills, llm-coding-pitfalls, surgical-changes]
---

# Karpathy Coding Principles

`andrej-karpathy-skills` is a third-party, MIT-licensed guideline set by forrestchang (the fetched repo URL is under multica-ai). It turns Andrej Karpathy's observations about LLM coding pitfalls into four principles, shipped as one `CLAUDE.md` file or as a Claude Code plugin. The principles are community guidance, not Anthropic documentation.

## The problems it targets

Karpathy's post, as quoted in the repo:

> "The models make wrong assumptions on your behalf and just run along with them without checking. They don't manage their confusion, don't seek clarifications, don't surface inconsistencies, don't present tradeoffs, don't push back when they should."

> "They really like to overcomplicate code and APIs, bloat abstractions, don't clean up dead code... implement a bloated construction over 1000 lines when 100 would do."

> "They still sometimes change/remove comments and code they don't sufficiently understand as side effects, even if orthogonal to the task."

## The four principles

| Principle | Rule | Addresses |
|---|---|---|
| Think Before Coding | Don't assume. Don't hide confusion. Surface tradeoffs. | Wrong assumptions, hidden confusion, missing tradeoffs |
| Simplicity First | Minimum code that solves the problem. Nothing speculative. | Overcomplication, bloated abstractions |
| Surgical Changes | Touch only what you must. Clean up only your own mess. | Orthogonal edits, touching code you shouldn't |
| Goal-Driven Execution | Define success criteria. Loop until verified. | Weak or missing verification |

### 1. Think Before Coding

- State assumptions explicitly. If uncertain, ask instead of guessing.
- When a request is ambiguous, present the possible interpretations instead of silently picking one.
- Push back when a simpler approach exists.
- When confused, stop, name what's unclear, and ask.

The repo's example: for "make the search faster," lay out the three meanings (response time, throughput, perceived speed) with effort estimates, then ask which one matters.

### 2. Simplicity First

- No features beyond what was asked.
- No abstractions for single-use code.
- No unrequested "flexibility" or configurability.
- No error handling for impossible scenarios.
- If 200 lines could be 50, rewrite it.

**The test:** would a senior engineer call this overcomplicated? The repo's example replaces a strategy-pattern class hierarchy for a single discount calculation with one function.

### 3. Surgical Changes

- Don't "improve" adjacent code, comments or formatting.
- Don't refactor things that aren't broken.
- Match the existing style, even if you'd do it differently.
- Mention unrelated dead code instead of deleting it.
- Remove imports, variables and functions that *your* change made unused. Leave pre-existing dead code unless asked.

**The test:** every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

Turn imperative tasks into verifiable goals:

| Instead of... | Transform to... |
|---|---|
| "Add validation" | "Write tests for invalid inputs, then make them pass" |
| "Fix the bug" | "Write a test that reproduces it, then make it pass" |
| "Refactor X" | "Ensure tests pass before and after" |

For multi-step work, state a short plan where each step has a check:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Karpathy's key insight, as quoted: "LLMs are exceptionally good at looping until they meet specific goals... Don't tell it what to do, give it success criteria and watch it go."

## Install

As a Claude Code plugin (the repo's recommended option), from inside Claude Code:

```
/plugin marketplace add forrestchang/andrej-karpathy-skills
/plugin install andrej-karpathy-skills@karpathy-skills
```

Or as a per-project `CLAUDE.md`:

```bash
# new project
curl -o CLAUDE.md https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md
# existing project (append)
echo "" >> CLAUDE.md
curl https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md >> CLAUDE.md
```

The guidelines are meant to be merged with project-specific rules. The repo also ships a Cursor rule file.

## How to tell it's working

- Diffs contain only the requested changes.
- Fewer rewrites caused by overcomplication.
- Clarifying questions come *before* implementation, not after mistakes.
- Clean, minimal PRs with no drive-by refactoring.

## Tradeoff

The guidelines favor caution over speed. For trivial tasks such as typo fixes or obvious one-liners, the author says to use judgment. The repo's framing of the failure mode: the overcomplicated examples "aren't obviously wrong"; the problem is *timing*, "adding complexity before it's needed."

## What this means for Claude Code users

- These rules fit best in CLAUDE.md as short, standing instructions ([[claude-md-and-memory]]), or installed as a plugin ([[plugins]]).
- Goal-Driven Execution is the same idea as giving Claude a way to verify its work. See the verification guidance in [[prompting-and-workflows]].
- The source is a community repo, not a measured study. No benchmark numbers back these principles.
