---
title: Tool Design for Agents
type: research
tldr: "Writing, testing and trimming agent tools"
sources:
  - raw/articles/writing-tools-for-agents.md
  - raw/articles/code-execution-with-mcp.md
  - raw/articles/building-effective-agents.md
related: ["[[mcp]]", "[[advanced-tool-use]]", "[[agent-evals]]", "[[context-engineering]]", "[[agentic-patterns]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [writing-tools-for-agents, agent-computer-interface, code-execution-with-mcp, tool-descriptions, code-mode]
---

# Tool Design for Agents

A tool is a contract between a deterministic system and a non-deterministic agent. The agent may call it, answer from its own knowledge, ask a clarifying question, or misuse it. This page brings together three Anthropic posts: "Writing effective tools for AI agents" (Sep 2025), "Code execution with MCP" (Nov 2025) and the tool appendix of "Building Effective Agents" (Dec 2024). Use it when you build an MCP server or any tool set for Claude.

## The build-evaluate-improve loop

1. **Prototype.** Give Claude the docs for the libraries and APIs your tools depend on. Flat `llms.txt` files are a good format. Wrap the tools in a local MCP server, connect it with `claude mcp add <name> <command> [args...]`, and try the tools yourself.
2. **Generate evaluation tasks** grounded in real use. Strong tasks need multiple tool calls, sometimes dozens.

   | Strong task | Weak task |
   |---|---|
   | "Customer ID 9182 reported that they were charged three times for a single purchase attempt. Find all relevant log entries and determine if any other customers were affected by the same issue." | "Search the payment logs for purchase_complete and customer_id=9182." |
   | "Schedule a meeting with Jane next week to discuss our latest Acme Corp project. Attach the notes from our last project planning meeting and reserve a conference room." | "Schedule a meeting with jane@acme.corp next week." |

3. **Pair each prompt with a verifier.** A verifier can be an exact string match or Claude acting as judge. Avoid verifiers so strict that they reject correct answers over formatting. You can list the tools you expect to be called, but don't overfit to one strategy.
4. **Run the eval programmatically** with simple while-loops that alternate LLM API calls and tool calls, one loop per task. Ask the agents for reasoning and feedback blocks before their tool calls, or turn on interleaved thinking. Beyond accuracy, collect runtime per tool call and per task, number of tool calls, token consumption and tool errors.
5. **Analyze the transcripts**, both the reasoning and the raw tool calls. What agents leave out of their feedback often matters more than what they include.
   - Many redundant calls suggest adjusting pagination or token-limit parameters.
   - Many invalid-parameter errors suggest the descriptions need to be clearer.
   - When Claude's web search tool launched, Claude needlessly appended "2025" to queries. A better tool description fixed it.
6. **Let Claude Code refactor the tools.** Paste the concatenated transcripts and ask for self-consistent fixes. Check against held-out test sets so you don't overfit.

See [[agent-evals]] for grader design in general.

## Principles

| Principle | Practice |
|---|---|
| Build the right tools, not every endpoint | Don't simply wrap API endpoints. Build `search_contacts` instead of `list_contacts`, `schedule_event` instead of `list_users` + `list_events` + `create_event`, `search_logs` instead of `read_logs`, and `get_customer_context` instead of three lookup tools. Too many or overlapping tools distract agents. |
| Namespace | Group tools by service (`asana_search`, `jira_search`) and by resource (`asana_projects_search`, `asana_users_search`). Prefix vs suffix naming had "non-trivial effects" on evals and varies by LLM, so test your scheme. |
| Return meaningful context | Prefer `name`, `image_url` and `file_type` over `uuid`, `256px_image_url` and `mime_type`. Resolving UUIDs to meaningful language, or even a 0-indexed ID scheme, significantly improved Claude's retrieval precision by reducing hallucinations. |
| Let the agent choose verbosity | Expose a `response_format` enum with values such as `"concise"` and `"detailed"`. In the Slack example, a detailed response was 206 tokens and a concise one 72 tokens, about ⅓. |
| Be token-efficient | Use pagination, range selection, filtering and truncation with sensible defaults. The article says Claude Code restricts tool responses to 25,000 tokens by default. When you truncate, tell the agent how to narrow its request. Make errors specific and actionable, not opaque codes or tracebacks. |
| Prompt-engineer descriptions | Describe the tool as you would to a new hire, and spell out niche terms and relationships between resources. Name parameters unambiguously (`user_id`, not `user`). Precise refinements to tool descriptions helped Claude Sonnet 3.5 reach state-of-the-art on SWE-bench Verified. |
| Pick the response structure by eval | XML, JSON and Markdown each affect performance, and no single format wins. |
| Annotate MCP tools | Tool annotations disclose which tools need open-world access or make destructive changes. |

### Format and error-proofing ("Building Effective Agents", Appendix 2)

- Give the model enough tokens to "think" before it writes itself into a corner.
- Keep formats close to text the model has seen on the internet. Avoid overhead such as counting changed lines for a diff header or escaping code inside JSON.
- **Poka-yoke** (mistake-proof) your arguments. On the SWE-bench agent, the model made mistakes with relative filepaths after leaving the root directory. Once the tool required absolute paths, the model used it "flawlessly". The team spent more time optimizing tools than the overall prompt.

## Code execution with MCP

Loading many MCP tools directly causes two problems:

1. **Tool definitions overload context.** With thousands of tools connected, the agent processes hundreds of thousands of tokens before it reads the request.
2. **Intermediate results pass through the model.** Copying a document from one tool to another sends it through context twice. For a 2-hour sales meeting transcript, that could be an additional 50,000 tokens.

The fix is to present MCP servers as code APIs on a filesystem and let the agent write code against them.

```text
servers
├── google-drive
│   ├── getDocument.ts
│   └── index.ts
└── salesforce
    ├── updateRecord.ts
    └── index.ts
```

```typescript
import * as gdrive from './servers/google-drive';
import * as salesforce from './servers/salesforce';

const transcript = (await gdrive.getDocument({ documentId: 'abc123' })).content;
await salesforce.updateRecord({
  objectType: 'SalesMeeting',
  recordId: '00Q5f000001abcXYZ',
  data: { Notes: transcript }
});
```

The agent lists `./servers/` and reads only the tool files it needs. In the post's Google Drive-to-Salesforce example, this cut token usage **from 150,000 tokens to 2,000 tokens**, "a time and cost saving of 98.7%." Cloudflare published similar findings under the name "Code Mode".

| Benefit | How |
|---|---|
| Progressive disclosure | Read tool definitions on demand, or add a `search_tools` tool with a detail-level parameter (name only, name and description, or full schema) |
| Context-efficient results | Filter in code. A 10,000-row sheet becomes 5 logged rows. |
| Control flow | Loops, conditionals and polling run in code, not through repeated agent turns. This also saves time-to-first-token latency. |
| Privacy | Intermediate results stay in the execution environment. The harness can tokenize PII (`[EMAIL_1]`) and untokenize it only in the outgoing tool call. |
| State and skills | Write progress to `./workspace/`, and save working functions to `./skills/` with a `SKILL.md` file so they become reusable skills |

The cost is that agent-generated code needs a secure execution environment with sandboxing, resource limits and monitoring. Weigh that operational overhead against the token savings.

## What this means for Claude Code users

- When you build an MCP server for Claude Code, apply the principles above. Connecting servers, output limits and tool search are covered in [[mcp]].
- On the API, tool search and programmatic tool calling are first-party versions of progressive disclosure and code execution. See [[advanced-tool-use]].
- Code saved with a `SKILL.md` is the same idea as Claude Code [[skills]].
- Every tool response costs context; see [[context-engineering]] and [[context-window]].
