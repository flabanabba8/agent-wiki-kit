---
title: Claude Managed Agents
type: concept
tldr: "Hosted agents: session log, harness, sandbox"
sources:
  - raw/articles/managed-agents-brain-hands.md
  - raw/docs/official/agent-sdk__overview.md
  - raw/docs/official/agent-sdk__hosting.md
  - raw/docs/official/commands.md
  - raw/docs/changelog-2.1.148-to-2.1.270.md
  - raw/docs/changelog-2.1.271-to-2.1.272.md
related: ["[[agent-sdk]]", "[[agent-sdk-deployment]]", "[[long-running-agents]]", "[[context-engineering]]", "[[trustworthy-agents]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: medium
last_verified: 2026-09-15
aliases: [claude-managed-agents, managed-agents-api, brain-and-hands, meta-harness]
---

# Claude Managed Agents

Managed Agents is a hosted REST API on the Claude Platform for long-horizon, asynchronous agent work. Anthropic runs both the agent loop and the sandbox. Your application sends events and streams results back, so you don't operate any hosting infrastructure. It is a separate product from the [[agent-sdk]].

## When to choose it

| You need | Choose |
|---|---|
| A library that runs the loop in your own process, with your own isolation and data plane | [[agent-sdk]], self-hosted ([[agent-sdk-deployment]]) |
| Long-running or asynchronous agents without operating sandboxes or session storage | Managed Agents |
| Full control of the Messages API loop | Client SDK |

In Claude Code, the bundled `/claude-api` skill loads Managed Agents reference material for your project's language. `/claude-api managed-agents-onboard` walks you through creating a new Managed Agent.

## Architecture: session, brain, hands

Anthropic calls Managed Agents a "meta-harness". It is opinionated about the interfaces around Claude and neutral about the harness that runs behind them. Claude Code is one harness it can host, and task-specific harnesses are others. Three parts of an agent are virtualized, so each can fail or be replaced on its own:

| Component | What it is | Interface (as described by Anthropic Engineering) |
|---|---|---|
| **Session** | An append-only, durable log of everything that happened | `emitEvent(id, event)` writes; `getSession(id)` and `getEvents()` read positional slices |
| **Harness** (the "brain") | A stateless loop that calls Claude and routes its tool calls | `wake(sessionId)` starts a replacement harness from the log |
| **Sandbox and tools** (the "hands") | Execution environments where code runs and files change | `execute(name, input) → string`; `provision({resources})` creates one |

These interface names come from Anthropic's engineering write-up of the design, not from a public API reference.

### What decoupling buys

- **Containers are cattle, not pets.** When session, harness and sandbox share one container, a dead container loses the session, and debugging means opening a shell inside a box that holds user data. With the harness outside, a container failure is just a tool-call error that Claude can react to, and a fresh sandbox is provisioned from a standard recipe.
- **Harness recovery.** The log lives outside the harness, so a crashed harness is replaced with `wake(sessionId)` and picks up from the last event.
- **Latency.** A container is provisioned only when a tool call needs one, so inference can start as soon as pending events are pulled from the log. Anthropic reports that this cut p50 time-to-first-token by roughly 60% and p95 by over 90%.
- **Many brains, many hands.** Stateless harnesses scale out. One brain can reach several execution environments, because any custom tool, MCP server or Anthropic tool sits behind the same `execute` interface, and brains can pass hands to each other. Work can reach resources in a customer VPC without network peering.

## Credentials never reach the sandbox

Code that Claude generates runs where a prompt injection could read the environment. Instead of relying only on narrowly scoped tokens, the design keeps tokens out of the sandbox's reach entirely:

- **Bundled with the resource.** A repository's access token is used to clone the repo while the sandbox initializes, then wired into the git remote. `git push` and `git pull` work inside the sandbox, but the agent never handles the token.
- **Held in a vault.** MCP OAuth tokens are stored in a secure vault. Claude calls MCP tools through a proxy that takes a token tied to the session, fetches the real credential from the vault and calls the external service. The harness never sees any credentials.

This is the same credential-proxy principle recommended for self-hosted agents in [[agent-sdk-deployment]]. The broader containment reasoning is in [[trustworthy-agents]].

## The session is not the context window

Compaction, memory files and context trimming all make irreversible decisions about what Claude keeps, and it is hard to know which tokens later turns will need. Managed Agents keeps the full event log durable, outside the context window. The harness chooses which events to fetch, and can transform them before they reach Claude, for example to raise prompt-cache hit rates. Recoverable storage (the session) is deliberately kept apart from context management (the harness), so context-engineering strategies for future models can change without touching the log. See [[context-engineering]] and [[context-editing-and-memory-tool]].

## Other capabilities in the sources

The raw sources mention these only through Claude Code's bundled `claude-api` skill:

- Web search and web fetch domain settings, and memory stores on self-hosted sandboxes.
- Starting deliverable-shaped work with `user.define_outcome`.

For how long-horizon harnesses are structured, see [[long-running-agents]].

> [!note]
> The raw sources do not include the Managed Agents API reference (endpoints, event schemas, pricing, limits). Check platform.claude.com/docs/en/managed-agents/overview for those before building.
