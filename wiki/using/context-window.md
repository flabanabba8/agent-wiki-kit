---
title: The Context Window
type: reference
tldr: "What fills context, compaction, caching"
sources:
  - raw/docs/official/context-window.md
  - raw/docs/official/how-claude-code-works.md
  - raw/docs/official/prompt-caching.md
  - raw/docs/official/model-config.md
  - raw/docs/official/features-overview.md
  - raw/docs/official/best-practices.md
  - raw/docs/official/commands.md
  - raw/docs/official/interactive-mode.md
  - raw/docs/official/troubleshooting.md
related: ["[[claude-md-and-memory]]", "[[costs-and-usage]]", "[[subagents]]", "[[models-and-effort]]", "[[context-engineering]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [compaction, auto-compact, prompt-caching, context-management, slash-context]
valid_until: 2027-03-15
---

# The Context Window

The context window is everything Claude knows about the session: the system prompt, your instructions, every file it reads, command output, its own replies, and content that never appears in your terminal. It is **the most important resource to manage**. As it fills, performance degrades and Claude may lose track of earlier instructions. For how to work within this limit day to day, see [[prompting-and-workflows]]. For the research background, see [[context-engineering]].

## What fills it

**Before you type anything:**

- The system prompt, with core instructions and tool definitions
- Environment info: working directory, platform, shell, OS version, and git repo status. Branch, status, and recent commits load as a block at the end of the system prompt
- Auto memory (the first 200 lines or 25KB of `MEMORY.md`), `~/.claude/CLAUDE.md`, the project CLAUDE.md, and unscoped rules ([[claude-md-and-memory]])
- MCP tool **names** only. Full schemas stay deferred and load on demand through tool search ([[mcp]])
- Skill descriptions. Skills with `disable-model-invocation: true` aren't listed until you invoke them ([[skills]])
- Anything your setup adds, such as an output style or `--append-system-prompt` text

**As Claude works:** every file read and command output. Path-scoped rules and nested CLAUDE.md files load when a matching file is read. Hook output is added when a hook returns context.

| Feature | When it loads | Context cost |
|---|---|---|
| CLAUDE.md | Session start | Full content, every request |
| Skills | Descriptions at start, body when used | Low until used. Zero for user-only skills |
| MCP servers | Names at start, schemas when used | Low until a tool is used |
| Code intelligence | After edits and on lookup | Low, and often replaces broad file reads |
| Subagents | When spawned | Isolated. Only a summary returns |
| Hooks | On trigger | Zero unless they return context |

## See what's using it

- `/context` shows a colored grid of current usage by category, with suggestions about context-heavy tools and memory bloat. It lists which CLAUDE.md and memory files loaded. `/context all` expands the per-item breakdown, including tokens per MCP tool.
- A custom status line can track usage continuously ([[interface]]).
- `/doctor` flags unused skills, MCP servers, and plugins against their context cost.

## Keep it lean

| Technique | How |
|---|---|
| Clear between tasks | `/clear` starts a new conversation with empty context. The old one stays reachable through `/resume` |
| Delegate big reads | "use a subagent to investigate X". The subagent's tool calls stay in its own window and only a summary comes back ([[subagents]]) |
| Side questions | `/btw what was the name of that config file again?` The answer never enters history |
| Scope investigations | An unscoped "investigate" can read hundreds of files |
| Hide manual skills | `disable-model-invocation: true`, or `skillOverrides` for skills you didn't write |
| Durable rules in CLAUDE.md | Instructions given only in chat can be lost to compaction |

Token-cost tactics such as model choice and preprocessing hooks are covered in [[costs-and-usage]].

## Compaction

As the window nears its limit, Claude Code **first clears older tool outputs, then summarizes the conversation**. A full window doesn't end the session. Your requests and key code snippets are kept, but detailed instructions from early on can be lost.

### When auto-compaction runs

By default, compaction runs when the conversation reaches the model's context limit, with these exceptions:

- Models running with a native 1M window (Sonnet 5, the Fable models, and Opus 4.7 and later on the Anthropic API) compact early, at about 967K tokens.
- Sonnet 4.6 and Opus 4.6 without extended context, and Opus 4.8 and Opus 5 on a 200K window (for example on Bedrock, Agent Platform, or Foundry), compact at the 200K boundary. So do native-1M models when `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` is set.
- Cloud sessions compact as the conversation approaches the limit.
- An unrecognized model ID, such as a gateway alias, compacts at whatever window Claude Code assumes for it.

Extended-context availability and `[1m]` variants are in [[models-and-effort]].

**Set the window yourself** anywhere from 100K to 1M tokens (capped at the model's window):

| Where | How | Notes |
|---|---|---|
| Saved setting | `/autocompact 500k` (or `200000`, `1M`, `200`). `/autocompact auto` resets | Writes `autoCompactWindow` to user settings. A managed setting can override it |
| One launch | `claude --autocompact 500k` | Not preempted by managed settings |
| Scripts and cloud | `CLAUDE_CODE_AUTO_COMPACT_WINDOW=500000` | Plain token count only. Beats everything else |

### Compact on your terms

- `/compact focus on the auth bug fix` sets what the summary keeps. Run it at natural breaks before a long new task, not mid-task.
- A "Compact Instructions" section in CLAUDE.md steers every compaction.
- `/rewind` → select a message → **Summarize from here** (condense later messages, keep earlier ones) or **Summarize up to here** (condense earlier messages, keep recent ones) ([[sessions-and-checkpoints]]).
- To abandon a dead end entirely, `/rewind` instead of compacting. Rewinding truncates back to a prefix that's already cached.

### What survives compaction

| Content | After compaction |
|---|---|
| System prompt, output style | Still apply |
| Project-root CLAUDE.md, unscoped rules, auto memory | Re-injected from disk |
| The plan written in plan mode | Re-injected from disk |
| Path-scoped rules, nested CLAUDE.md | Reload when Claude next reads a matching file |
| Files read or edited | Up to five re-read, most recently modified first. Files over 5,000 tokens come back as a path reference only |
| Invoked skill bodies | Re-injected, capped at 5,000 tokens per skill and 25,000 total, oldest dropped first. Truncation keeps the top of `SKILL.md` |
| Skill description listing | Not re-injected. Only invoked skills are kept |
| Background commands and subagents | Keep running. Claude is reminded they exist |
| Context added by earlier hooks | Summarized with the conversation |
| SessionStart hooks matching `compact` | Run again, and their output is added ([[hooks]]) |

### Thrashing

If one file or tool output refills the window right after every summary, Claude Code stops after a few attempts with `Autocompact is thrashing: the context refilled to the limit...`. To recover, read the file in chunks or line ranges, run `/compact keep only the plan and the diff`, move the work into a subagent, or `/clear`.

## Prompt caching

Every turn re-sends the full context. Prompt caching keeps that affordable: the API matches the **prefix** of each request against recently processed content and bills re-read tokens at the cached rate, roughly 10% of the standard input rate. The match is exact, so a change anywhere in the prefix recomputes everything after it. Claude Code manages caching automatically and orders requests so stable content comes first:

| Layer | Content | Changes when |
|---|---|---|
| System prompt | Core instructions, tool definitions | The loaded tool definitions change |
| Project context | CLAUDE.md, auto memory, unscoped rules | Session start, `/clear`, `/compact` |
| Conversation | Messages, responses, tool results | Every turn |

**Invalidates the cache** (one slower, more expensive turn):

- Switching models with `/model`. Each model has its own cache, and the `opusplan` plan-mode toggle and automatic model fallback count as switches
- Changing effort level on most models
- Turning on fast mode for the first time in a conversation
- MCP server or plugin changes when tools load into the prefix rather than being deferred
- Denying a whole tool when tool search is off
- Compacting, which rebuilds the conversation layer
- Accumulating enough images that the oldest get dropped
- The first session after a Claude Code upgrade

**Keeps the cache:** editing repo files (Claude gets a change notice), editing CLAUDE.md mid-session (the edit doesn't apply until `/clear`, `/compact`, or restart), changing permission mode, changing output style, invoking skills and commands, `/recap`, `/rewind`, and spawning subagents. A fork reads the parent's cache.

**Tip:** choose the model and effort at the start of a session, and save `/compact` for breaks between tasks.

### Cache lifetime

The cache expires after inactivity, so the first turn after a break is slower.

| Request bucket | Subscription, within plan usage | Usage credits, API key, or cloud provider |
|---|---|---|
| Main conversation | 1 hour | 5 minutes |
| Subagents, workflows, compaction, titles | 5 minutes (a few server-controlled helpers get 1 hour) | 5 minutes |

- Override the main conversation with `promptCacheTtl` or `CLAUDE_CODE_PROMPT_CACHE_TTL`, and everything else with `subagentPromptCacheTtl` or `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL`. Each accepts `5m` or `1h`. 1-hour cache writes bill at a higher rate.
- `FORCE_PROMPT_CACHING_5M=1` forces 5 minutes everywhere. `ENABLE_PROMPT_CACHING_1H=1` requests 1 hour for both buckets.
- The cache is effectively scoped to one machine and directory, so separate worktrees don't share it.

### Check and disable

- `/usage` shows a `Prompt cache (main)` line with hit ratio, misses, warm or cold state, and often the likely cause of the last miss. A status line can read the `prompt_cache` object. If `cache_creation_input_tokens` stays high turn after turn, something in the prefix keeps changing.
- To disable caching for debugging, set `DISABLE_PROMPT_CACHING=1`, or `DISABLE_PROMPT_CACHING_HAIKU`, `_SONNET`, `_OPUS`, or `_FABLE` for one model family.
