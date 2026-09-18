---
title: Agentic Patterns
type: research
tldr: "Workflows vs agents and the five patterns"
sources:
  - raw/articles/building-effective-agents.md
  - raw/articles/multi-agent-research-system.md
related: ["[[multi-agent-systems]]", "[[tool-design]]", "[[context-engineering]]", "[[subagents]]", "[[workflows]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [building-effective-agents, workflows-vs-agents, orchestrator-workers, evaluator-optimizer, prompt-chaining]
---

# Agentic Patterns

Anthropic's "Building Effective Agents" (Dec 2024) separates agentic systems into **workflows** and **agents**, and describes five workflow patterns that sit on one building block. "How we built our multi-agent research system" (Jun 2025) shows one of them, orchestrator-workers, running in production as Claude's Research feature. Use this page to pick the least complex design that solves your task.

## Workflows vs agents

| | Workflows | Agents |
|---|---|---|
| Definition | LLMs and tools orchestrated through predefined code paths | LLMs dynamically direct their own processes and tool usage |
| Best for | Well-defined tasks that need predictability and consistency | Open-ended problems where you can't predict the number of steps or hardcode a path |
| Trade-off | Less flexible | Higher cost and the potential for compounding errors |

The core advice is to find the simplest solution possible and add complexity only when it demonstrably improves outcomes. For many applications, a single LLM call optimized with retrieval and in-context examples is enough. Agentic systems trade latency and cost for better task performance.

Frameworks make it easy to get started, but they add abstraction layers that hide the underlying prompts and responses. The post recommends starting with LLM APIs directly. If you do use a framework, understand the code underneath: "Incorrect assumptions about what's under the hood are a common source of customer error."

## Building block: the augmented LLM

Every pattern assumes an LLM with retrieval, tools and memory, which the model uses actively by writing its own search queries, choosing tools and deciding what to retain. Tailor these capabilities to the use case and give them an easy, well-documented interface. The Model Context Protocol is one way to provide them.

## The five workflow patterns

| Pattern | How it works | Use when | Example from the source |
|---|---|---|---|
| Prompt chaining | Sequence of LLM calls, each processing the previous output, with optional programmatic "gate" checks between steps | The task decomposes cleanly into fixed subtasks and you are willing to trade latency for accuracy | Write an outline, check it against criteria, then write the document |
| Routing | Classify the input and send it to a specialized follow-up | Distinct categories are better handled separately and can be classified accurately | Send easy questions to Claude Haiku 4.5 and hard ones to Claude Sonnet 4.5 |
| Parallelization | **Sectioning:** independent subtasks run in parallel. **Voting:** the same task runs several times | Subtasks can run in parallel for speed, or multiple attempts raise confidence | One instance answers while another screens for inappropriate content; several prompts review code for vulnerabilities |
| Orchestrator-workers | A central LLM breaks the task down dynamically, delegates to worker LLMs and synthesizes the results | You can't predict the subtasks in advance | Coding changes across many files; search across multiple sources |
| Evaluator-optimizer | One call generates while another evaluates and gives feedback in a loop | Evaluation criteria are clear and iterative refinement adds measurable value | Literary translation; complex search where the evaluator decides whether more searching is needed |

Orchestrator-workers and parallelization look alike, but in orchestrator-workers the subtasks aren't predefined. The orchestrator decides them from the input. Evaluator-optimizer fits when two things hold: responses clearly improve when a human gives feedback, and an LLM can give that feedback itself.

## Agents

Agents are "typically just LLMs using tools based on environmental feedback in a loop." At each step they need ground truth from the environment, such as tool results or code execution. They can pause for human feedback at checkpoints or blockers, and they usually have stopping conditions such as a maximum number of iterations. Because autonomy raises cost and lets errors compound, the post recommends extensive testing in sandboxed environments with guardrails.

According to the post's appendix, agents add the most value where a task needs both conversation and action, has clear success criteria, allows feedback loops and includes human oversight. Customer support and coding are the two examples. Code can be verified by automated tests, but human review is still crucial for fit with broader system requirements.

The post gives three principles for building agents:

1. Keep the agent's design simple.
2. Be transparent by showing the agent's planning steps explicitly.
3. Design the agent-computer interface (ACI) carefully, with thorough tool documentation and testing (see [[tool-design]]).

## Orchestrator-workers in production: Claude Research

**Architecture.** A LeadResearcher agent analyzes the query and saves its plan to Memory, because context beyond 200,000 tokens is truncated. It then spawns subagents with specific research tasks. Each subagent runs web searches, evaluates the results with interleaved thinking and reports back. The lead synthesizes the findings and decides whether more research is needed. A final CitationAgent ties each claim to its source. Unlike static retrieval-augmented generation (RAG), which fetches the chunks most similar to the query once, the search adapts to what it finds.

**Results and cost:**

| Finding | Setting |
|---|---|
| Multi-agent outperformed single-agent by **90.2%** | Claude Opus 4 lead with Claude Sonnet 4 subagents vs single-agent Claude Opus 4, on Anthropic's internal research eval |
| Three factors explained **95%** of performance variance; token usage alone explained **80%** | BrowseComp analysis; tool-call count and model choice were the other two factors |
| Upgrading to Claude Sonnet 4 gained more than doubling the token budget on Claude Sonnet 3.7 | Same analysis |
| Agents use about **4×** more tokens than chat; multi-agent systems about **15×** | Anthropic's usage data |
| Parallel subagents and parallel tool calls cut research time by **up to 90%** for complex queries | Lead spins up 3-5 subagents at once; subagents use 3+ tools in parallel |
| A tool-testing agent's rewritten tool descriptions gave a **40%** decrease in task completion time | Future agents using the improved description |

**Prompting lessons:**

- **Think like your agents.** Simulate the system with its exact prompts and tools, then watch the agents step by step.
- **Teach the orchestrator to delegate.** Each subagent needs an objective, an output format, guidance on which tools and sources to use, and clear task boundaries. Vague briefs such as "research the semiconductor shortage" led to duplicated searches.
- **Scale effort to query complexity.** Simple fact-finding needs 1 agent with 3-10 tool calls. Direct comparisons might need 2-4 subagents with 10-15 calls each. Complex research might use more than 10 subagents with clearly divided responsibilities.
- **Start wide, then narrow down.** Begin with short, broad queries before drilling into specifics.
- **Guide the thinking.** The lead uses extended thinking to plan. Subagents use interleaved thinking after tool results.

**Production engineering.** Agents are stateful and their errors compound. The team resumes runs from the point of failure rather than restarting, tells the agent when a tool is failing, and adds retry logic and checkpoints. Full production tracing makes failures diagnosable. Rainbow deployments shift traffic gradually so running agents aren't broken by updates. Running subagents synchronously is a bottleneck, because the lead can't steer them and they can't coordinate with each other. For long tasks, agents summarize finished phases into external memory. When the context limit approaches, they spawn fresh subagents with clean contexts. Subagents write outputs to a filesystem and pass back lightweight references, which avoids a "game of telephone" through the lead.

For when a multi-agent design is the wrong choice, see [[multi-agent-systems]].

## What this means for Claude Code users

- Claude Code is itself an agent, an LLM using tools in a loop. [[how-claude-code-works]] explains that loop.
- Orchestrator-workers corresponds to [[subagents]], where the main session delegates focused tasks to clean contexts. Predefined multi-step pipelines correspond to [[workflows]].
- When you delegate, write the brief the Research team found necessary: objective, output format, tool and source guidance, and boundaries.
- For evaluator-optimizer loops in long coding runs, see the planner/generator/evaluator harness in [[long-running-agents]].
- Start with a single well-prompted session before adding structure ([[prompting-and-workflows]]).
