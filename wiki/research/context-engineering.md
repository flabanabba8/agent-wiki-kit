---
title: Context Engineering
type: research
tldr: "Context rot, just-in-time retrieval, compaction"
sources:
  - raw/articles/context-engineering.md
  - raw/articles/harness-design-long-running-apps.md
related: ["[[context-window]]", "[[claude-md-and-memory]]", "[[context-editing-and-memory-tool]]", "[[long-running-agents]]", "[[subagents]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [context-rot, attention-budget, just-in-time-context, compaction-strategy, structured-note-taking]
---

# Context Engineering

**Context engineering** is the set of strategies for curating and maintaining the optimal set of tokens during LLM inference. That includes everything that lands in the window, not only the prompt: system instructions, tools, MCP, external data and message history. Writing a prompt is a one-off task. Context engineering is iterative, because the curation happens every time you decide what to pass to the model. The source is Anthropic's "Effective context engineering for AI agents" (Sep 2025).

The guiding principle is to find "the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome."

## Why context is finite: context rot and the attention budget

- **Context rot:** as the number of tokens in the window grows, the model's ability to recall information from it goes down. Needle-in-a-haystack studies show this for every model, though some degrade more gently.
- **Attention budget:** every token attends to every other token, which gives n² pairwise relationships for n tokens. Each new token uses up some of that attention. Models also see fewer long sequences in training, so they have less experience with dependencies that span the whole context.
- **A gradient, not a cliff:** models stay highly capable at long lengths but retrieve information and reason over long ranges less precisely.

Treat context as a finite resource with diminishing marginal returns.

## Anatomy of effective context

| Component | Guidance |
|---|---|
| System prompt | Pitch it at the **right altitude**. One failure mode is brittle, hardcoded if-else logic. The other is vague guidance that assumes shared context. Organize the prompt into sections (`<background_information>`, `<instructions>`, `## Tool guidance`, `## Output description`) using XML tags or Markdown headers, though exact formatting matters less as models improve. Aim for the minimal information that fully describes the expected behavior; minimal doesn't mean short. Start with a minimal prompt on the best model, then add instructions and examples to fix the failures you observe. |
| Tools | Make them self-contained, robust to error and unambiguous, with minimal overlap. Bloated tool sets are one of the most common failures: "If a human engineer can't definitively say which tool should be used in a given situation, an AI agent can't be expected to do better." See [[tool-design]]. |
| Examples | Curate a few diverse, canonical examples. Don't stuff in a laundry list of edge cases. |
| Message history | Keep it "informative, yet tight." |

## Just-in-time retrieval

The post defines agents simply as "LLMs autonomously using tools in a loop." Many applications retrieve context before inference using embeddings. The **just-in-time** alternative keeps lightweight identifiers (file paths, stored queries, web links) and loads the data at runtime with tools.

- Claude Code analyzes large databases this way: it writes targeted queries, stores the results, and uses `head` and `tail` instead of loading whole data objects.
- Metadata carries signal. A `test_utils.py` in a `tests` folder implies a different purpose than the same file in `src/core_logic/`. Folder hierarchy, naming conventions and timestamps all help the agent decide what matters.
- This enables **progressive disclosure**: the agent discovers context layer by layer and keeps only what it needs in working memory.
- The trade-off is that runtime exploration is slower than pre-computed retrieval. Without good tools and heuristics, the agent wastes context on dead ends.

**Hybrid strategy.** Claude Code drops CLAUDE.md files into context up front, and uses primitives like glob and grep to retrieve files just in time. This avoids stale indexes and complex syntax trees. The post suggests hybrids suit less dynamic content such as legal or finance work. Its standing advice is "do the simplest thing that works."

## Long-horizon techniques

Tasks lasting tens of minutes to hours outgrow any context window. Larger windows won't remove context pollution either. The post describes three techniques:

| Technique | What it does | Best for |
|---|---|---|
| **Compaction** | When a conversation nears the limit, summarize it and start a new window with the summary | Tasks that need extensive back-and-forth |
| **Structured note-taking** (agentic memory) | The agent writes notes outside the window (a to-do list, a `NOTES.md`) and reads them back later | Iterative development with clear milestones |
| **Sub-agent architectures** | Subagents explore with clean windows, using tens of thousands of tokens or more, and return a condensed summary, often 1,000-2,000 tokens | Complex research and analysis where parallel exploration pays off |

### Compaction in practice

In Claude Code, compaction passes the message history to the model to summarize. The summary keeps architectural decisions, unresolved bugs and implementation details, and drops redundant tool outputs. The agent then continues with that summary plus **the five most recently accessed files**.

When tuning your own compaction prompt, first maximize recall so nothing relevant is lost, then improve precision. Over-aggressive compaction can drop context whose importance only shows up later. The lightest-touch form of compaction is **tool result clearing**: once a tool result is deep in the history, the raw output rarely needs to be seen again.

### Note-taking in practice

Claude playing Pokémon kept tallies across thousands of game steps, for example "for the last 1,234 steps I've been training my Pokémon in Route 1, Pikachu has gained 8 levels toward the target of 10." Without being prompted about memory structure, it built maps and strategy notes, then read them after context resets to continue. On the Claude Developer Platform, the memory tool offers a file-based store for the same purpose.

### Compaction vs context reset

A **context reset** clears the window and starts a fresh agent with a structured handoff. Compaction keeps continuity but doesn't give a clean slate. The harness-design post found Claude Sonnet 4.5 showed "context anxiety", wrapping up work early as it believed it was near its limit, strongly enough that resets were essential. Opus 4.5 largely removed that behavior, and automatic compaction was enough. See [[long-running-agents]].

## What this means for Claude Code users

- CLAUDE.md is the up-front half of Claude Code's hybrid strategy, so keep it high-signal ([[claude-md-and-memory]]).
- Compaction, what fills the window, and how to inspect it are covered in [[context-window]].
- Delegate broad exploration to [[subagents]] so only a summary returns to the main context.
- If you build on the API, context editing (tool result clearing) and the memory tool are covered in [[context-editing-and-memory-tool]].
