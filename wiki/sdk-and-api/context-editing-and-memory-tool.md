---
title: Context Editing and Memory Tool (API)
type: reference
tldr: "API context clearing, compaction, memory tool"
sources:
  - raw/docs/context-editing.md
  - raw/docs/memory-tool.md
  - raw/articles/context-management.md
related: ["[[context-engineering]]", "[[context-window]]", "[[agent-memory]]", "[[long-running-agents]]", "[[managed-agents]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [context-editing-api, memory-tool, clear-tool-uses, compaction-control, context-management-api]
---

# Context Editing and Memory Tool (API)

These Claude API features are for agents whose conversations outgrow the context window, in applications that call the Messages API directly. Claude Code's own compaction and memory are covered in [[context-window]] and [[claude-md-and-memory]]. The strategy behind all of them is in [[context-engineering]].

| Feature | Runs in | What it does |
|---|---|---|
| Server-side compaction | API | Summarizes the whole conversation as it nears the limit. Anthropic's recommended default |
| Tool result clearing (`clear_tool_uses_20250919`) | API | Replaces old tool results with placeholders once a threshold is passed |
| Thinking block clearing (`clear_thinking_20251015`) | API | Controls how many past turns keep their thinking blocks |
| SDK compaction (`compaction_control`) | Client SDK tool runner | A client-side summary that replaces the history |
| Memory tool (`memory_20250818`) | Your application | Files under `/memories` that persist across conversations |

In Anthropic's internal agentic-search evaluation, announced alongside Claude Sonnet 4.5, the memory tool plus context editing improved performance by 39% over baseline, and context editing alone by 29%. In a 100-turn web search evaluation, context editing let agents finish workflows that would otherwise fail from context exhaustion, while cutting token consumption by 84%.

## Server-side compaction

For most long-running conversations, use server-side compaction. Pass the `compact_20260112` edit in the request's `context_management` parameter; this also works with a tool runner. The full parameter reference is at platform.claude.com/docs/en/build-with-claude/compaction, which this wiki's raw sources don't include. Use the strategies below when you need finer control over what gets cleared.

## Context editing

Context editing needs the beta header `context-management-2025-06-27`. Edits go in `context_management.edits`. The API applies them server-side before the prompt reaches Claude, and your client keeps the full, unedited history with no syncing needed. It works on all supported models.

```python
response = client.beta.messages.create(
    model="claude-opus-5",
    max_tokens=16000,
    messages=messages,
    tools=tools,
    betas=["context-management-2025-06-27"],
    context_management={"edits": [
        {"type": "clear_thinking_20251015", "keep": {"type": "thinking_turns", "value": 2}},
        {"type": "clear_tool_uses_20250919",
         "trigger": {"type": "input_tokens", "value": 30000},
         "keep": {"type": "tool_uses", "value": 5}},
    ]},
)
```

When you use both strategies, `clear_thinking_20251015` must come first in `edits`.

### Tool result clearing options

| Option | Default | Meaning |
|---|---|---|
| `trigger` | 100,000 input tokens | When clearing starts, measured in `input_tokens` or `tool_uses` |
| `keep` | 3 tool uses | How many recent tool use/result pairs survive |
| `clear_at_least` | None | Minimum tokens to clear. If that much can't be cleared, the strategy isn't applied |
| `exclude_tools` | None | Tools whose uses and results are never cleared |
| `clear_tool_inputs` | `false` | Also clear the tool call parameters, not just the results |

The oldest results are cleared first and replaced with placeholder text that tells Claude they were removed. Clearing invalidates the cached prompt prefix from that point on, so use `clear_at_least` to make each cache break worth it.

### Thinking block clearing

Set `keep` to `{"type": "thinking_turns", "value": N}` (N must be greater than 0) or to `"all"`. Without it, the default depends on the model:

| Model class | Keeps all prior thinking | Keeps only the last turn's thinking |
|---|---|---|
| Opus | Opus 4.5 and later | Opus 4.1 and earlier |
| Sonnet | Sonnet 4.6 and later | Sonnet 4.5 and earlier |
| Haiku | None | Every model through Haiku 4.5 |
| Fable and Mythos | All models | None |

If your code runs across model tiers, set `keep` explicitly. Keeping thinking blocks preserves the prompt cache; clearing them invalidates it at the point where clearing happens. On Claude Fable 5.1, server-side context management never invalidates thinking blocks, but client-side edits to earlier turns can.

### Observe the effect

The response's `context_management.applied_edits` field lists what was cleared and how many tokens. When streaming, it arrives in the final `message_delta` event. The token counting endpoint also accepts `context_management`, and returns `input_tokens` after editing alongside `original_input_tokens` before it.

## SDK compaction (tool runner)

The TypeScript and Ruby SDK tool runners accept `compaction_control` (`compactionControl` in TypeScript), but the parameter is deprecated there. Python SDK v1.0 and later and the C#, Go and Java tool runners don't support it. Prefer server-side compaction.

```typescript
const runner = client.beta.messages.toolRunner({
  model: "claude-opus-5",
  max_tokens: 1024,
  tools: [readFile],
  messages: [{ role: "user", content: "What's in config.json?" }],
  compactionControl: { enabled: true, contextTokenThreshold: 100000 }
});
```

After each response, the SDK adds up `input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens`. Once that passes the threshold, it injects a summary request, and Claude's summary (inside `<summary></summary>` tags) replaces the entire history.

| Option | Default | Meaning |
|---|---|---|
| `enabled` | none (required) | Turns compaction on |
| `context_token_threshold` | 100,000 | Token count that triggers compaction |
| `model` | Same as the main model | Model that writes the summary |
| `summary_prompt` | Built-in prompt | Custom summary instructions |

Limitations:

- Server-side tools such as web search inflate `cache_read_input_tokens`, which can trigger compaction too early. Use the token counting endpoint to check the real context length.
- If compaction runs while a tool use is pending, that tool use is dropped before summarizing, and Claude re-issues it afterwards if still needed.

SDK compaction suits long file-heavy or research tasks whose output lives outside the conversation. It is a poor fit for tasks that need precise recall of early details or exact state across many variables.

## Memory tool

The memory tool gives Claude a `/memories` directory whose files persist across conversations. Claude can create, read, update and delete files there. The tool runs client-side: Claude requests an operation, your handler executes it against storage you control (per-user directories, a database, encrypted files) and returns the result in a `tool_result`. No beta header is required.

```python
tools = [{"type": "memory_20250818", "name": "memory"}]
```

When the tool is present, the API adds a system-prompt instruction. It tells Claude to view its memory directory before doing anything else, and to record progress because its context window "might be reset at any moment". So Claude checks memory at the start of a task and writes to it as it works.

| Command | Input fields |
|---|---|
| `view` | `path`, optional `view_range` `[start_line, end_line]` (`-1` reads to the end) |
| `create` | `path`, `file_text` |
| `str_replace` | `path`, `old_str`, optional `new_str` (omit it to delete `old_str`) |
| `insert` | `path`, `insert_line` (`0` inserts at the top), `insert_text` |
| `delete` | `path` |
| `rename` | `old_path`, `new_path` (never the `/memories` root itself) |

For `view`, return a directory listing with sizes, or file lines numbered with a 6-character right-aligned number and a tab. To report an error, set `is_error: true` on the tool result. SDK helpers handle the tool interface and loop: `BetaAbstractMemoryTool` in Python and C#, `betaMemoryTool` in TypeScript, and `BetaMemoryToolHandler` in Java. Python and TypeScript also ship a ready-made `BetaLocalFilesystemMemoryTool`.

**Security is your job:**

- Validate every path in every command. Resolve each path to canonical form, confirm it stays inside `/memories`, and reject `../`, `..\` and URL-encoded `%2e%2e%2f`. In Python, `pathlib.Path.resolve()` and `relative_to()` do this.
- Cap file sizes and how much `view` returns, and delete files that haven't been accessed in a long time.
- Strip sensitive data before writing, even though Claude usually declines to store it.

### Pairing memory with other features

- **With context editing.** As context approaches the clearing threshold, Claude gets an automatic warning, so it can save important tool results to memory before they are cleared and read them back later.
- **With compaction.** Compaction keeps the active context small, and memory holds whatever must survive summarization.
- **Multisession pattern.** A first session sets up the memory files: a progress log, a feature checklist and a pointer to the startup script. Every later session reads them first and updates the log before it ends. Work on one feature at a time, and mark it done only after end-to-end verification. The harness case study is in [[long-running-agents]], and memory designs are compared in [[agent-memory]]. [[managed-agents]] takes a different approach, keeping the durable log outside the context window entirely.
