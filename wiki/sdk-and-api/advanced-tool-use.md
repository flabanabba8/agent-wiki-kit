---
title: Advanced Tool Use (API)
type: reference
tldr: "Tool search, programmatic calls, tool examples"
sources:
  - raw/docs/tool-search-and-programmatic-calling.md
  - raw/articles/advanced-tool-use.md
related: ["[[tool-design]]", "[[mcp]]", "[[context-engineering]]", "[[claude-models]]", "[[context-editing-and-memory-tool]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [tool-search-tool, programmatic-tool-calling, tool-use-examples, defer-loading, allowed-callers]
---

# Advanced Tool Use (API)

These three Claude API features are for agents with large tool libraries or heavy tool output. Pick one based on the bottleneck:

| Bottleneck | Feature |
|---|---|
| Tool definitions bloat context, or Claude picks the wrong tool | Tool search (`defer_loading`) |
| Large intermediate results fill context, or there are many round trips | Programmatic tool calling (`allowed_callers`) |
| Parameters are malformed or inconsistent | Tool use examples (`input_examples`) |

The features work together. Tool search finds the right tool, programmatic calling runs it efficiently, and examples make the call correct. This page is for applications that call the Messages API directly; Claude Code handles MCP tool search on its own ([[mcp]]). General advice on writing tools is in [[tool-design]].

## Tool search

Instead of loading every tool definition up front, Claude searches your catalog (tool names, descriptions, argument names and argument descriptions) and loads only the matches. Anthropic's example five-server MCP setup (GitHub, Slack, Sentry, Grafana, Splunk) has 58 tools and uses about 55K tokens before any work starts. Tool search typically cuts that by over 85%, loading 3–5 tools per request. Claude's tool selection gets less accurate once 30–50 tools are loaded. In Anthropic's internal MCP evaluations with tool search enabled, Opus 4 went from 49% to 74%, and Opus 4.5 from 79.5% to 88.1%.

### Set up

```python
tools = [
    {"type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex"},
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
        "defer_loading": True,
    },
]
```

| Variant | Query form | Max length |
|---|---|---|
| `tool_search_tool_regex_20251119` | A Python `re.search()` pattern, matched case-insensitively | 200 characters |
| `tool_search_tool_bm25_20251119` | Natural language | 500 characters |

Rules:

- Send every tool definition in `tools` on every request, whether deferred or not. `defer_loading` controls what enters the context window, not what you send.
- At least one tool must be non-deferred, or the API returns a 400. That is normally the search tool, which you should never defer. Keep your 3–5 most-used tools non-deferred too.
- A deferred tool can't also carry `cache_control` (the API returns a 400); put the cache breakpoint on a non-deferred tool. Deferred tools stay out of the prompt prefix, so prompt caching still works.
- With the MCP connector, set `defer_loading` in an `mcp_toolset` entry's `default_config`, or per tool in `configs`.
- Name tools consistently by service (`github_`, `slack_`), write descriptions with the keywords users would use, and tell Claude in the system prompt which tool categories exist.

### What comes back

1. Claude calls the search as a `server_tool_use` with an ID starting `srvtoolu_`. Never answer that ID with a `tool_result`, or the request is rejected.
2. The API returns a `tool_search_tool_result` containing `tool_reference` blocks. A search returns 5 matches by default, and Claude may set `limit` anywhere from 1 to 10,000. The API expands those references into full definitions for Claude.
3. Claude makes an ordinary `tool_use` call, which you execute. On the next request, pass the assistant content back unchanged. Tools Claude has discovered stay usable in later turns without another search.

Search failures return HTTP 200 with a `tool_search_tool_result_error` whose code is one of `invalid_tool_input`, `unavailable`, `too_many_requests` or `execution_time_exceeded`. A search that matches nothing returns an empty `tool_references` array, not an error.

**Custom search**, for example with embeddings: build your own tool and return a standard `tool_result` whose content is `[{"type": "tool_reference", "tool_name": "..."}]`. Every tool you reference needs a definition in `tools`, normally with `defer_loading: true`.

### Availability and limits

- **Models.** The compatibility table lists Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5, Opus 4.8, 4.7, 4.6 and 4.5, Sonnet 4.6, Sonnet 4.5 and Haiku 4.5. Opus 4.1 and earlier are not supported.
- **Limits.** Up to 10,000 deferred tools per request. Tool search works with the Batches API and with streaming.
- **Amazon Bedrock.** Server-side tool search works only through the InvokeModel API, not Converse.
- **Billing.** Tool search is not metered separately. Definitions it loads count as input tokens.
- **When to use it.** You have 10 or more tools, definitions over 10K tokens, several MCP servers, or falling selection accuracy. Skip it with fewer than 10 tools, when every tool is used on every request, or when all definitions together are under 100 tokens.

## Programmatic tool calling

With programmatic tool calling, Claude writes Python that calls your tools as async functions inside the code execution container. When the code calls a tool, execution pauses and you receive a `tool_use`. Your result goes back to the running code, not into Claude's context, and only the script's final output reaches Claude.

### Set up

```python
tools = [
    {"type": "code_execution_20260120", "name": "code_execution"},
    {
        "name": "query_database",
        "description": "Execute a SQL query against the sales database. Returns a list of rows as JSON objects.",
        "input_schema": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]},
        "allowed_callers": ["code_execution_20260120"],
    },
]
```

`allowed_callers` can be `["direct"]` (the default), `["code_execution_20260120"]`, or both. Choose one per tool so Claude gets clear guidance. The API treats `code_execution_20260521` and `code_execution_20260120` as interchangeable in this field. `allowed_callers` steers Claude but is not a security boundary, so your client must still handle a direct `tool_use` for any tool it defines.

### The request loop

1. The response pauses with `stop_reason: "tool_use"`, a `container` ID, and `tool_use` blocks whose `caller` is `{"type": "code_execution_20260120", "tool_id": "srvtoolu_..."}`.
2. Reply with a user message that contains only `tool_result` blocks, whose content is a string or text blocks (no images). Include the `container` ID, which is required while calls are pending, and resend the same `tools` array.
3. Repeat until a `code_execution_tool_result` with `stdout` arrives and Claude continues its turn.

Timing: a pending call raises `TimeoutError` inside the code after about 4 minutes. Idle containers are reclaimed after about 5 minutes, and no container can be reused more than 30 days after it was created.

### Requirements and restrictions

- **Models.** Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5, Opus 4.8, 4.7, 4.6 and 4.5, Sonnet 5, Sonnet 4.6 and Sonnet 4.5. Haiku 4.5 accepts the code execution tool but not programmatic calling.
- **Platforms.** Claude API, Claude Platform on AWS, and Microsoft Foundry (on a Hosted on Anthropic deployment). It is not available on Amazon Bedrock or Google Cloud. It is not eligible for ZDR, and container data is kept for up to 30 days.
- **Incompatible features.** Tools with `strict: true`, forcing a tool through `tool_choice`, and `disable_parallel_tool_use: true`. Tools whose schemas contain a recursive `$ref`, MCP connector tools, and the computer and browser use toolsets can't be called from code.
- **Billing.** Results of programmatic calls don't count toward input or output tokens. Pricing follows code execution.
- **Tool design.** Document the return format in the tool description, return JSON, and validate data from outside sources, because results are strings the code may act on.

### When it pays off

Numbers Anthropic has reported:

- **Budget-compliance example:** raw data reaching Claude shrank from 200KB of expense records to 1KB of results.
- **Complex research tasks:** average usage fell from 43,588 to 27,297 tokens, a 37% reduction. Internal knowledge retrieval rose from 25.6% to 28.5%, and GIA from 46.5% to 51.2%.
- **BrowseComp and DeepSearchQA:** 11% better performance on average, with 24% fewer input tokens.
- **75-tool project-management benchmark:** roughly 38% fewer billed input tokens, with no change in accuracy.
- **τ²-bench**, where each turn makes one or two sequential calls: scores were unchanged and cost was roughly 8% higher.
- **Production traffic with 10–49 tool definitions:** typical token savings of 20%–40%.

It fits well for fan-out across many items, large results that can be filtered, and agentic search. It fits poorly for strictly sequential calls where Claude must reason between each one, for a few small calls, and for calls that need user feedback in between. Measure billed input tokens with and without `allowed_callers` before turning it on broadly.

## Tool use examples

Add `input_examples` to a tool definition to show Claude concrete calls. JSON Schema defines what is valid, but not conventions such as date formats, ID patterns, or which optional fields belong together.

```json
{
  "name": "create_ticket",
  "input_schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
  "input_examples": [
    {
      "title": "Login page returns 500 error",
      "priority": "critical",
      "labels": ["bug", "authentication", "production"],
      "reporter": {"id": "USR-12345", "name": "Jane Smith", "contact": {"email": "jane@acme.com"}},
      "due_date": "2024-11-06",
      "escalation": {"level": 2, "notify_manager": true, "sla_hours": 4}
    },
    {"title": "Add dark mode support", "labels": ["feature-request", "ui"], "reporter": {"id": "USR-67890", "name": "Alex Chen"}},
    {"title": "Update API documentation"}
  ]
}
```

(The real schema would also declare `priority`, `labels`, `reporter`, `due_date` and `escalation`.)

- In Anthropic's internal testing, examples raised accuracy on complex parameter handling from 72% to 90%.
- Use 1–5 realistic examples that show minimal, partial and full calls, and add them only where the schema leaves room for doubt. Examples cost tokens, so skip them for simple tools and standard formats such as URLs or emails.
- With tool search, a discovered tool's `input_examples` are expanded along with its definition.

Model availability for these features is listed per model above; model IDs and prices are in [[claude-models]]. For the context-budget reasoning behind them, see [[context-engineering]].
