---
title: Deploying Agent SDK Agents
type: how-to
tldr: "Host, secure, monitor and meter SDK agents"
sources:
  - raw/docs/official/agent-sdk__hosting.md
  - raw/docs/official/agent-sdk__configuration.md
  - raw/docs/official/agent-sdk__agent-loop.md
  - raw/docs/official/agent-sdk__secure-deployment.md
  - raw/docs/official/agent-sdk__observability.md
  - raw/docs/official/agent-sdk__cost-tracking.md
  - raw/docs/official/agent-sdk__session-storage.md
  - raw/docs/official/agent-sdk__claude-code-features.md
  - raw/docs/official/agent-sdk__subagents.md
related: ["[[agent-sdk]]", "[[sandboxing-and-security]]", "[[enterprise-admin]]", "[[costs-and-usage]]", "[[managed-agents]]", "[[network-config]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [agent-sdk-hosting, secure-agent-deployment, agent-sdk-observability, agent-sdk-cost-tracking, session-store, max-budget-usd]
---

# Deploying Agent SDK Agents

Self-hosting an [[agent-sdk]] agent means four jobs: running a long-lived `claude` subprocess for each session, keeping its state durable, limiting what it can reach, and measuring what it spends. If you don't need your own infrastructure or data plane, [[managed-agents]] runs the agent and the sandbox for you.

## The subprocess model

`query()` spawns a `claude` CLI process and talks to it over stdio. Each session gets its own subprocess, which owns a shell, a working directory and JSONL transcripts, so N concurrent sessions mean N subprocesses. Give each session a distinct `cwd` when they need separate filesystems.

This state sits on local disk and is lost when the container restarts, scales down or moves to another node:

| State | Default location |
|---|---|
| Session transcripts | `~/.claude/projects/`, or `projects/` under `CLAUDE_CONFIG_DIR` |
| CLAUDE.md memory | `~/.claude/CLAUDE.md` and the working directory |
| Files the agent produces | The session's working directory |

## Choose a session pattern

| Pattern | Shape | Example workloads |
|---|---|---|
| Ephemeral | One container per task, destroyed when the task completes | Bug fix, invoice extraction, document translation |
| Long-running | Persistent containers holding many sessions behind an HTTP or WebSocket endpoint | Email triage agent, Slack bot, per-user site builder |
| Hybrid | Ephemeral containers that load from a `SessionStore` on start and shut down when idle | Research that pauses for hours, support agent with ticket history |
| Multi-agent container | Several SDK subprocesses in one container | Simulations where agents interact |

For long-running sessions in TypeScript, `streamInput()` adds turns to a live session and `startup()` pre-warms subprocesses; in Python, `ClaudeSDKClient` holds a session open. Behind a load balancer, pin each session to one container with consistent hashing on the session ID.

## Provision

- **Runtime.** Python 3.10+ or Node.js 18+. The bundled CLI is pinned to the SDK package version, so upgrading the SDK upgrades the CLI. Take patch releases as they come, and read the changelog before taking a minor release.
- **Resources.** Start with 1 GiB RAM, 5 GiB disk and 1 CPU per agent. Treat that as a floor: memory grows with session length, so measure peak RSS on a representative session.
- **Network.** Allow outbound HTTPS to `api.anthropic.com` (or your cloud provider's endpoint) and to any MCP endpoints. The subprocess itself doesn't listen on the network. Proxy and CA setup are in [[network-config]].
- **Cost.** Token spend usually outweighs container cost by an order of magnitude or more. A minimal container runs roughly $0.05 per hour, while one long session can spend dollars in tokens.

## Persist sessions with a SessionStore

A `SessionStore` mirrors transcripts to your own backend, so any host can resume a session. Implement `append` and `load`; the optional methods are `listSessions`, `listSessionSummaries`, `delete` and `listSubkeys`. `load` must return entries deep-equal to what was appended and in the same order, so a backend that reorders object keys is fine. The SDK ships `InMemorySessionStore` for development and testing. Both repositories carry one runnable reference adapter per storage type under `examples/session-stores/` (TypeScript) and `examples/session_stores/` (Python) — an object store (S3), a key-value store (Redis) and a relational or document database (Postgres) — plus a conformance suite for your own (`run_session_store_conformance` in Python).

```python
store = MyRedisStore(client)  # your adapter
async for message in query(
    prompt="Continue the analysis",
    options=ClaudeAgentOptions(session_store=store, resume=session_id),
):
    ...
```

What to design around:

- **It's a mirror, not a replacement.** The subprocess always writes locally first. A fresh session's local transcript outlives the run. A run resumed from the store deletes its local copy at the end, so the store then holds the only durable copy.
- **Writes are best-effort.** A failed `append` batch gets up to three attempts in total, then is dropped with a `mirror_error` system message. Deduplicate on `entry.uuid` and alert on `mirror_error`.
- **Resume from a matching working directory.** The store key encodes the original `cwd`.
- **Some options conflict.** A store can't be combined with `persistSession: false` or with file checkpointing.
- **It stores transcripts only.** CLAUDE.md and working-directory files need their own volume or sync. The SDK never deletes anything from your store, so retention is your job.
- **Python auth on resume.** When resuming from a store, Python copies only credentials and `.claude.json` into the temporary config directory. An `apiKeyHelper` in user settings then fails with `Not logged in`, so set `ANTHROPIC_API_KEY` in `env` instead.

## Isolate tenants

By default, `query()` reads host settings and per-directory memory. In a container shared by several tenants:

1. Pass `setting_sources=[]` / `settingSources: []`.
2. Set `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` in `env`, because auto memory loads whatever the setting sources are.
3. Give each tenant its own `CLAUDE_CONFIG_DIR`, which separates `~/.claude.json`, and optionally set `CLAUDE_CODE_PROJECT_DIR_NAME`.
4. Pass an explicit per-tenant `cwd` on every call.
5. Apply per-tenant egress rules at your proxy.

Server-managed settings are still fetched when the process authenticates with an organization credential, and filesystem isolation doesn't remove them ([[enterprise-admin]]).

## Secure the boundary

Agents act on the content they read, so plan for prompt injection. Claude Code's built-in controls (permission rules, AST-parsed Bash matching, the command sandbox) are covered in [[sandboxing-and-security]], and the reasoning behind this design in [[trustworthy-agents]]. For hardened deployments, run Claude Code inside an isolation boundary and keep credentials outside it.

| Technology | Isolation strength | Performance overhead | Complexity |
|---|---|---|---|
| sandbox-runtime (bubblewrap or sandbox-exec plus a built-in proxy) | Good | Very low | Low |
| Containers (Docker) | Depends on setup | Low | Medium |
| gVisor | Excellent with correct setup | Medium/High | Medium |
| VMs (Firecracker, QEMU) | Excellent with correct setup | High | Medium/High |

A hardened container uses `--cap-drop ALL`, `--security-opt no-new-privileges`, a seccomp profile, `--read-only` with a `tmpfs` for `/tmp`, `--network none`, `--memory 2g`, `--pids-limit 100` and `--user 1000:1000`. Mount code read-only (`:ro`), and mount a Unix socket to a host-side proxy as the container's only route out.

**Credential proxy pattern.** Run a proxy outside the boundary that enforces a domain allowlist, injects credentials and logs every request. There are two ways to route traffic to it:

- **`ANTHROPIC_BASE_URL`** sends model requests to the proxy in plaintext, where they can be inspected and modified.
- **`HTTP_PROXY` / `HTTPS_PROXY`** routes all traffic, but the proxy sees only opaque CONNECT tunnels unless it terminates TLS and the agent trusts its CA.

For other services, prefer a custom tool or MCP server whose backend adds credentials outside the sandbox. Proxy options include Envoy (with its `credential_injector` filter), mitmproxy, Squid and LiteLLM.

Never mount `~/.ssh`, `~/.aws` or `~/.config`. Strip `.env`, `~/.git-credentials`, `~/.kube/config`, `.npmrc`, `*.pem` and similar files from any mounted code. Authenticate inbound requests at a gateway in front of the agent, not in the agent itself.

## Observe with OpenTelemetry

The SDK produces no telemetry of its own. It passes environment variables to the CLI, and the CLI exports straight to your collector. Telemetry stays off until you set `CLAUDE_CODE_ENABLE_TELEMETRY=1` and at least one exporter:

```bash
CLAUDE_CODE_ENABLE_TELEMETRY=1
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_TRACES_EXPORTER=otlp
CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1          # needed for traces only
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT=http://collector.example.com:4318
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer your-token"
```

- **Spans.** `claude_code.interaction` wraps `claude_code.llm_request` and `claude_code.tool`, which in turn has `claude_code.tool.blocked_on_user` and `claude_code.tool.execution` children. Subagent spans nest under the parent's tool span. Filter on `session.id` to see several `query()` calls as one timeline.
- **Trace linking.** When your app has an active span, the SDK injects `TRACEPARENT` automatically, so the agent run appears inside your trace.
- **Pitfalls.** Never use the `console` exporter, because stdout is the SDK's message channel. Export errors are silent by default; set `CLAUDE_CODE_OTEL_DIAG_STDERR=1` and read them through the `stderr` callback.
- **Per-user audit.** Put end-user and tenant IDs, percent-encoded, in `OTEL_RESOURCE_ATTRIBUTES` for each call.
- **Content is excluded by default.** Opt in only if your pipeline is approved to store it: `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_TOOL_CONTENT`, `OTEL_LOG_RAW_API_BODIES`.
- **Short runs.** By default, metrics export every 60 s and traces and logs every 5 s. Lower `OTEL_METRIC_EXPORT_INTERVAL`, `OTEL_LOGS_EXPORT_INTERVAL` and `OTEL_TRACES_EXPORT_INTERVAL` so data leaves before the process exits.

Organization-wide monitoring setup is in [[enterprise-admin]].

## Track cost

`total_cost_usd` and per-model `costUSD` are estimates the client computes from a price table bundled with the SDK. Use them for budgeting and development insight, not for billing; the Usage and Cost API and the Claude Console are authoritative.

| Result field | Includes subagents? |
|---|---|
| `usage` | No, only the top-level loop |
| `total_cost_usd` | Yes |
| `modelUsage` / `model_usage` | Yes, broken down per model |

- **Per call.** Each `query()` reports only its own totals, so sum across calls yourself. In streaming input mode, each turn's result carries a running total, which starts over after `/clear`.
- **Per step.** Assistant messages carry usage. Deduplicate by message ID, because parallel tool calls share one. Their `output_tokens` is a placeholder, so read output tokens from the result.
- **Crashes.** After a crash, the `error_during_execution` result may carry zeroed cost fields. Recover totals from the previous turn's result.
- **Caching.** Prompt caching is automatic; watch `cache_creation_input_tokens` and `cache_read_input_tokens`. With API-key and cloud-provider auth, your turns use a 5-minute TTL. `ENABLE_PROMPT_CACHING_1H` requests 1 hour, or set `CLAUDE_CODE_PROMPT_CACHE_TTL` and `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` separately.

### Cap turns and spend

Both caps are off unless you set them. `max_turns` / `maxTurns` counts tool-use round trips; `max_budget_usd` / `maxBudgetUsd` is compared against the same client-side estimate as `total_cost_usd`. Hitting either ends the run with the matching result subtype ([[agent-sdk]]). Zero means different things: `max_turns=0` runs without a turn limit, exactly like leaving it unset, while the CLI rejects `max_budget_usd=0` as an invalid amount at startup and the session never runs.

With streaming input the session survives a cap result. The turn count starts over for each queued message, but the budget total accumulates, so once spend reaches the cap every later message in the conversation ends with `error_max_budget_usd` until a `/clear` starts the budget over. At the budget cap Claude Code also refuses to spawn subagents, answering `Budget limit reached`, and stops background subagents that are still running; subagent requests count toward the total. Per-subagent turn caps are in [[agent-sdk-control]], and plan usage limits in [[costs-and-usage]].

## Known limitations

| Limitation | What to do |
|---|---|
| Sessions have no timeout of their own | Bound runs with `max_turns` |
| Memory grows over long sessions | Cap session length or recycle subprocesses |
| Wide parallel subagent fan-outs can hit rate limits | Break the work into smaller batches |
| Subagents have no wall-clock deadline | Set `maxTurns` in each `AgentDefinition`. `CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS` only catches stalls |
