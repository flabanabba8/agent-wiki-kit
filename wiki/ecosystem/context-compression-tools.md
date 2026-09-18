---
title: Context Compression Tools (Headroom, Toolaria)
type: comparison
tldr: "Headroom and Toolaria shrink tool output"
sources:
  - raw/docs/headroom/headroom-docs-full.md
  - raw/docs/toolaria/README.md
  - raw/docs/toolaria/DESIGN.md
  - raw/docs/toolaria/ARCHITECTURE.md
related: ["[[context-window]]", "[[context-engineering]]", "[[mcp]]", "[[llm-gateways]]", "[[costs-and-usage]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: medium
last_verified: 2026-09-15
aliases: [headroom, toolaria, tool-output-compression, spill-to-disk, context-offloading]
---

# Context Compression Tools (Headroom, Toolaria)

Both tools attack the same waste: large tool outputs that fill the context window, such as JSON arrays, logs and web pages. They take opposite approaches.

- **Headroom** compresses content before it reaches the model. It runs as a proxy, a library or an MCP server, and lets the model retrieve the original afterwards.
- **Toolaria** saves oversized results to disk and hands the model an excerpt plus a fetch handle.

For how Claude Code's own context fills up and gets compacted, see [[context-window]]. For the strategy behind both tools, see [[context-engineering]]. All performance figures below are the vendors' own claims.

| | Headroom | Toolaria |
|---|---|---|
| Form | Python package `headroom-ai` (3.10+), TypeScript SDK, Docker image, proxy, MCP server | Plugin for Hermes Agent only |
| Works with Claude Code | Yes: proxy via `ANTHROPIC_BASE_URL`, `headroom wrap claude`, or MCP tools | No |
| Method | Content-aware lossy compression, with originals kept in a local store | Spill-to-disk: excerpt plus handle, no rewriting |
| Getting the full data back | `headroom_retrieve` tool (the architecture doc also calls it `ccr_retrieve`) | `rescuer_fetch` with `stat`, `range`, `grep`, `full` |
| Needs an LLM | No, except optional ML compressors (Kompress, LLMLingua) | No |

## Headroom

Headroom runs a transform pipeline in three stages:

1. **Cache Aligner** moves dynamic values such as dates and UUIDs out of the system prompt so provider prompt caches keep hitting.
2. **SmartCrusher** statistically samples JSON arrays and always keeps errors, anomalies and change points.
3. **Context Manager** makes the message list fit the window. It uses Intelligent Context by default, with a rolling window as the fallback.

Originals go into the CCR (Compress-Cache-Retrieve) store, so the model can call the retrieve tool to get them back. User messages, system prompt content, model responses and source code pass through unchanged. Code passes through unless AST compression is explicitly enabled.

### Use it with Claude Code

```bash
pip install "headroom-ai[proxy]"
headroom proxy                                  # listens on 127.0.0.1:8787
ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude
# or wrap the CLI in one step
headroom wrap claude
```

MCP-only mode needs no proxy: install with `pip install "headroom-ai[mcp]"`, then run `headroom mcp install` to register it with Claude Code. That adds three tools:

- `headroom_compress` returns compressed text plus a hash.
- `headroom_retrieve` takes a `hash` and an optional `query`.
- `headroom_stats` reports savings.

Originals held by the local MCP store expire after 1 hour, and the proxy's store keeps them for 5 minutes. The proxy also serves MCP at `http://host:8787/mcp`, plus `/health`, `/stats`, `/metrics` (Prometheus) and a compression-only `POST /v1/compress`. Telemetry is on by default. Turn it off with `HEADROOM_TELEMETRY=off` or `--no-telemetry`. Other useful proxy flags are `--budget` (a daily USD limit), `--no-optimize` (passthrough) and `--llmlingua`, which adds about 2 GB of dependencies. Pointing Claude Code at any proxy is a gateway setup; see [[llm-gateways]] for the official options.

### What it compresses (vendor figures)

Benchmark run by Headroom v0.5.18 on Apple M-series CPU, measuring `compress()` on realistic tool outputs:

| Content | Tokens before → after | Saved |
|---|---|---|
| JSON array, 100 items | 3,163 → 297 | 90.6% |
| JSON array, 500 items | 9,526 → 1,614 | 83.1% |
| Shell output, 200 lines | 3,238 → 469 | 85.5% |
| Build log, 200 lines | 2,412 → 148 | 93.9% |
| grep results, 150 hits | 2,624 → 2,624 | 0.0% |
| Python source, ~480 lines | 2,958 → 2,958 | 0.0% |

Limitations the vendor states:

- Short exchanges see a median compression of 4.8%.
- Code-only sessions and RAG document contexts pass through.
- Plain text compresses 43–46% but adds latency.
- Content under 200 tokens (`min_tokens_to_crush`) and arrays under 5 items are skipped.
- Invalid input passes through unchanged. The one exception is an LLMLingua out-of-memory error, which raises `RuntimeError`.

## Toolaria

Toolaria is a zero-config plugin for **Hermes Agent**, not for Claude Code. Its README says Claude Code already persists oversized tool results to disk and shows the model a short preview, and that Toolaria copies that contract. Toolaria hooks `transform_tool_result`, which Hermes's own truncation doesn't cover for MCP and web tool results, and applies to:

- MCP tool results
- `web_extract` and `web_search`
- `browser_*` tools

Install:

```bash
git clone https://github.com/Sahil-SS9/Toolaria.git ~/.hermes/plugins/toolaria
pip install -r ~/.hermes/plugins/toolaria/requirements.txt
# enable "toolaria" under plugins.enabled in ~/.hermes/config.yaml, then:
hermes plugin reload
```

When a result exceeds `max_result_chars` (default 12000):

1. Toolaria stores it in a SHA256-addressed blob store under `~/.hermes/toolaria`.
2. It returns a head/tail excerpt of 40 + 15 lines, plus JSON structure for JSON results.
3. It adds a handle that states explicitly that the excerpt is a preview, not the full output.

The model then calls `rescuer_fetch` in one of four modes:

- `stat`: blob metadata
- `range`: lines `start` to `start+count`
- `grep`: regex matches with line numbers
- `full`: the whole result, refused above 50,000 chars by default

Blobs are removed after `ttl_hours` (72) or when the store exceeds `max_store_mb` (500). A fetch for a removed blob returns advice to re-run the source tool. `delegate_task`, `session_search`, `cronjob`, the skill tools, the kanban tools, `clarify` and `memory` are never intercepted. `/rescuer` shows store status.

Known limits:

- The model can't pass the full payload to another tool without fetching it first.
- Grep needs the `regex` package for its 500 ms timeout. Without it, grep falls back to plain substring search.
- Only one gateway process may use a given store path.
- Anyone who knows a 12-hex blob id can fetch that blob.
