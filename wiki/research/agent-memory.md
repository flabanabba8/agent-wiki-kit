---
title: Agent Memory Architectures
type: research
tldr: "Temporal graph, structured and trigger memory"
sources:
  - raw/articles/zep-temporal-kg.md
  - raw/articles/hindsight-agent-memory.md
  - raw/articles/t-mem.md
  - raw/docs/mem0/api-capture-2.0.20.md
  - raw/articles/agentic-context-engineering.md
  - raw/articles/autoskill.md
  - raw/articles/how-we-contain-claude.md
related: ["[[mem0]]", "[[claude-md-and-memory]]", "[[context-editing-and-memory-tool]]", "[[self-improving-agents]]", "[[context-engineering]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: medium
last_verified: 2026-09-15
aliases: [zep-graphiti, hindsight-memory, t-mem, long-term-conversational-memory, vector-memory-vs-structured-memory]
---

# Agent Memory Architectures

Long-term memory systems store what an agent learned across sessions and retrieve it later. This page compares three 2025–2026 designs: **Zep/Graphiti** (a temporal knowledge graph), **Hindsight** (four structured networks) and **T-Mem** (write-time triggers). It then contrasts them with plain vector memory and curated text. Claude Code's own file-based memory is on [[claude-md-and-memory]]. This repo's mem0 setup is on [[mem0]].

| System | Structure | How it handles time | Retrieval | Best reported result |
|---|---|---|---|---|
| Zep / Graphiti | Episodes → entities and facts → communities | Bi-temporal; contradicted edges are invalidated, not deleted | Cosine, BM25, graph BFS, then reranking | LongMemEval_s 71.2% (gpt-4o) |
| Hindsight | World, experience, observation and opinion networks | Occurrence interval plus mention time | Vector, BM25, graph and temporal channels, RRF, cross-encoder | LongMemEval 91.4% (Gemini-3) |
| T-Mem | Topics, scenes, items, per-speaker persona | Temporal questions answered from the scene/item layers | Topic → scene → item cascade plus trigger bypass | LoCoMo-Plus 74.81% |

## Zep and Graphiti

Zep (arXiv 2501.13956) is built on **Graphiti**, a knowledge graph with three tiers:

- **Episodes:** raw messages, text or JSON, kept lossless.
- **Semantic entities and facts:** extracted from episodes and resolved against existing nodes.
- **Communities:** clusters of connected entities, summarized and extended by label propagation.

Every fact edge carries four timestamps. `t_valid` and `t_invalid` record when the fact held true. `t′created` and `t′expired` record when Zep learned and retired it. When a new edge contradicts an existing one, an LLM detects the conflict and sets the old edge's `t_invalid`. Newer information wins, and history is kept.

**Results:**

- **DMR:** 94.8% vs MemGPT's 93.4% (gpt-4-turbo). But a full-conversation baseline reaches 94.4%, and Zep itself calls DMR inadequate.
- **LongMemEval_s** (~115k-token conversations), with gpt-4o:

| | Full context | Zep |
|---|---|---|
| Accuracy | 60.2% | 71.2% |
| Latency | 28.9 s | 2.58 s |
| Context size | 115k tokens | 1.6k tokens |

Single-session-assistant questions dropped 17.7% under Zep.

## Hindsight

Hindsight (ACL 2026 demo; MIT license; `pip install hindsight-all`) splits memory into four networks:

- **World:** objective facts.
- **Experience:** the agent's own actions.
- **Observation:** entity summaries.
- **Opinion:** beliefs with 0–1 confidence scores.

It exposes three operations:

- **Retain** extracts 2–5 narrative facts per conversation and links them by time, meaning, entity and cause.
- **Recall** runs vector, BM25, graph spreading-activation and temporal channels in parallel, fuses them with RRF, reranks with a cross-encoder, and stays within a caller-set token budget.
- **Reflect** answers under a behavioral profile (skepticism, literalism and empathy, each 1–5). New evidence raises or lowers opinion confidence.

It runs on PostgreSQL with pgvector and ships an MCP server. For a 10,000-unit bank, recall takes under 200 ms, excluding the LLM call.

| System | LongMemEval | LoCoMo |
|---|---|---|
| Full context, GPT-4o | 60.2 | – |
| Full context, OSS-20B | 39.0 | – |
| Zep (GPT-4o) | 71.2 | 75.1 |
| Hindsight (OSS-20B) | 83.6 | 83.2 |
| Hindsight (OSS-120B) | 89.0 | 85.7 |
| Hindsight (Gemini-3) | 91.4 | 89.6 |

Multi-session questions rose from 21.1% to 79.7% with the 20B backbone. The system has no built-in PII detection.

## T-Mem

T-Mem (Tencent, arXiv 2606.15405) argues that similarity search covers only **descriptive** recall, where the query shares words or entities with the memory. It misses **associative** recall, where query and memory share no surface features. The paper's example: a colleague's seafood allergy mentioned a month earlier should surface when the user asks where to take the team for dinner.

At write time, T-Mem pre-computes four trigger families, split by granularity (item or scene) and orientation:

| | Descriptive | Associative |
|---|---|---|
| Item | Entity | Bridge (a situation where this fact would matter) |
| Scene | Scene (situation, object, event, emotion) | Horizon (forward-looking dimensions) |

Memories reached through a trigger bypass the topic prefilter, so associative hits aren't filtered back out.

**Results** (GPT-4.1-mini for construction):

- **LoCoMo:** 80.26% (HyperMem 77.01%).
- **LoCoMo-Plus:** 74.81% (HyperMem 48.63%, Mem0 15.80%). The LoCoMo-to-Plus gap narrows to 5.45 pp.
- **Ablation:** removing the Scene and Horizon triggers costs 22.19 pp on LoCoMo-Plus but only 0.40 on LoCoMo.
- **Construction cost:** 15.60M tokens over 10 conversations, vs Mem0's 12.20M.

> [!contradiction]
> The papers report different LoCoMo scores for the same baselines. Hindsight lists Zep at 75.1%. T-Mem, citing MemOS's official-pipeline numbers, lists Zep at 59.22% and Mem0 at 64.57%. The answer models and QA pipelines differ, so cross-paper comparisons are unreliable.

## Vector memory vs structured, curated memory

A plain **vector memory** such as mem0 stores extracted memories as embeddings and returns the nearest `top_k` results for a query. In mem0 2.0.20, `search` defaults to `top_k=20` with `threshold=0.1`, and `add` can run LLM extraction (`infer=True`). How this repo uses it is covered on [[mem0]].

The sources point to where a flat store falls short and what the structured designs add:

- **No sense of time.** Flat retrieval can't tell current facts from superseded ones. Zep's validity intervals and Hindsight's occurrence intervals exist for this, and both gain most on temporal and multi-session questions.
- **Similarity-bounded reach.** T-Mem's taxonomy puts flat RAG, Mem0-style fact layers and OS-style kernels all in the descriptive half.
- **Records vs curated knowledge.** AutoSkill moves memory "from text records to behavior units" as editable, versioned files. ACE finds itemized, incremental playbook updates avoid the **context collapse** that whole-document LLM rewrites cause ([[self-improving-agents]]).
- **Persistent memory is an attack surface.** Anthropic lists memory poisoning through product memory, CLAUDE.md files and agent state directories as an open risk ([[trustworthy-agents]]).

## What this means for Claude Code users

- CLAUDE.md and auto memory are plain curated text: inspectable, but not temporally indexed. Mark superseded facts instead of letting them conflict ([[claude-md-and-memory]]).
- For API-built agents, the memory tool and context editing are the first-party options ([[context-editing-and-memory-tool]]).
- External memory servers (Hindsight ships an MCP server) plug in through [[mcp]]. Treat what they return as untrusted content.
- For choosing what to put in context at all, see [[context-engineering]].
