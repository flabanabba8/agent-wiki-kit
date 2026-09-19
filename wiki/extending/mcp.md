---
title: MCP in Claude Code
type: reference
tldr: "Connect external tools through MCP servers"
sources:
  - raw/docs/official/mcp.md
  - raw/docs/official/mcp-quickstart.md
  - raw/docs/official/managed-mcp.md
  - raw/docs/official/features-overview.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
related: ["[[plugins]]", "[[enterprise-admin]]", "[[channels]]", "[[advanced-tool-use]]", "[[hooks]]", "[[agent-standards]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [mcp-servers, mcp-json, claude-mcp-add, managed-mcp, mcp-tool-search]
---

# MCP in Claude Code

The Model Context Protocol (MCP) is an open standard for connecting AI tools to external systems ([[agent-standards]]). An MCP server gives Claude Code tools, resources and prompts for an issue tracker, database, browser or API. Connect a server when you keep copying data into chat from another tool. MCP provides the connection; a skill can teach Claude how to use it well. Connect only servers you trust; servers that fetch external content expose you to prompt injection.

## Transports and adding servers

Run these in your shell, not inside a session.

```bash
# Remote HTTP (recommended); SSE-only servers are detected and connected over SSE
claude mcp add --transport http notion https://mcp.notion.com/mcp
claude mcp add --transport http secure-api https://api.example.com/mcp --header "Authorization: Bearer your-token"

# Explicit SSE (deprecated transport)
claude mcp add --transport sse asana https://mcp.asana.com/sse

# Local stdio: everything after -- is the server command
claude mcp add --env AIRTABLE_API_KEY=YOUR_KEY --transport stdio airtable -- npx -y airtable-mcp-server

# WebSocket or any JSON entry
claude mcp add-json events-server '{"type":"ws","url":"wss://mcp.example.com/socket","headers":{"Authorization":"Bearer YOUR_TOKEN"}}'
```

- `--transport` accepts `http`, `sse` and `stdio`, not `ws`. In JSON, `streamable-http` is an alias for `http`. An entry with a `url` but no `type` is read as stdio and skipped.
- Claude Code picks an MCP runtime at launch and keeps it. It uses v2 everywhere, including Amazon Bedrock, Claude Platform on AWS, Google Cloud's Agent Platform, Microsoft Foundry, gateway sign-ins and telemetry-disabled sessions. v2 asks HTTP servers whether they support MCP 2026-07-28 and uses it with those that do, plus claude.ai connector servers in sessions that fetch feature flags; `MCP_PROTOCOL_NEGOTIATION=auto` also asks stdio servers and connectors everywhere, and `legacy` stops it asking. `MCP_SDK_GENERATION` pins `v1` or `v2`.
- `"type": "sdk"` entries in `.mcp.json`, settings, plugins and agent files are skipped with a warning, because only an SDK host application can register an in-process server ([[agent-sdk-control]]).
- Short flags: `-t`, `-H`, `-e`, `-s`. Put another option between `--env` and the server name.
- Stdio servers receive `CLAUDE_PROJECT_DIR` in their environment. Servers that limit filesystem access should implement `roots/list`, which returns the launch directory plus added working directories.
- Server names may contain only letters, numbers, hyphens and underscores. Built-in names such as `workspace`, `claude-in-chrome` and `computer-use` are reserved.
- For setup instructions written for another client, turn a URL into `--transport http`, a launch command into `-- <command>`, or the object inside an `mcpServers` block into `claude mcp add-json <name> '<json>'`.
- `claude mcp add-from-claude-desktop` imports Claude Desktop servers on macOS and WSL. `claude mcp serve` runs Claude Code itself as a stdio MCP server.

## Scopes and `.mcp.json`

| Scope | Loads in | Shared | Stored in |
| :-- | :-- | :-- | :-- |
| `local` (default) | Current project | No | `~/.claude.json`, under the project path |
| `project` | Current project | Yes, via git | `.mcp.json` at the project root |
| `user` | All your projects | No | `~/.claude.json`, top-level `mcpServers` |

```json
{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": { "Authorization": "Bearer ${API_KEY}" }
    },
    "playwright": { "type": "stdio", "command": "npx", "args": ["-y", "@playwright/mcp@latest"] }
  }
}
```

- `${VAR}` and `${VAR:-default}` expand in `command`, `args`, `env`, `url` and `headers`. An unset variable with no default stays literal, with a warning. For local, project and user servers, `/mcp` details and `claude mcp list|get` print the reference by name rather than its value; a `managedMcpServers` entry shows only the URL's host.
- In a remote server's `url` and `headers`, credential variables such as `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` and `AWS_BEARER_TOKEN_BEDROCK` always read as empty. Copy the value into a variable with your own name.
- When a name is defined in several places, one whole entry wins, with no field merging. The order is local, project, user, plugin servers, then claude.ai connectors. Plugins and connectors are matched by endpoint. An organization's `managedMcpServers` entry outranks all of them.
- Claude Code reads `.mcp.json` at session start; restart after editing. It never reads paths such as `~/.claude/mcp.json`.

## Manage servers

- `claude mcp list`, `claude mcp get <name>` and `claude mcp remove <name> --scope <scope>` manage servers from the shell; `/mcp` manages them in a session. Removing a remote server deletes its stored OAuth tokens.
- Statuses: `✔ Connected`, `! Needs authentication`, `✘ Failed to connect` (with the HTTP status or error detail), `⏸ Pending approval`, `⊘ Disabled for this project`. A remote server used before can show `cached`, meaning its tool list came from the discovery cache (`MCP_DISCOVERY_CACHE`) and it connects on first use.
- Toggling a server off in `/mcp` writes `disabledMcpServers` for that project in `~/.claude.json`. Default-off built-ins such as `computer-use` are enabled through `enabledMcpServers`.
- Claude Code refreshes tools on `list_changed` notifications and reconnects dropped remote servers with exponential backoff, up to five attempts. Stdio servers are not reconnected. When reconnection gives up, an `MCP server "<name>" disconnected · open /mcp to reconnect` notification appears. The startup notice for servers needing sign-in names each server once and skips it at later launches until it has connected and needs signing in again; `/mcp` always lists them all.

## Approval and trust

Interactive sessions ask before using project-scoped servers from `.mcp.json`; reset choices with `claude mcp reset-project-choices`. `claude -p`, Agent SDK and cloud sessions load them without asking, a cloud session reading the committed `.mcp.json` when the session has one repository. To keep one out, add it to `disabledMcpjsonServers`, exclude project settings with `--setting-sources`, or pass `--strict-mcp-config` so only `--mcp-config` servers load — that flag asks to replace a managed set, so it exits at startup where a `managed-mcp.json` is deployed.

An `enableAllProjectMcpServers` or `enabledMcpjsonServers` approval committed in the repository's `.claude/settings.json` is ignored until you trust the workspace; approvals in user, managed and `--settings` settings still apply. A `headersHelper` from `.mcp.json` or local scope runs only after you trust that project folder. See [[permissions-and-modes]].

## Authentication

- **OAuth:** add the server, then authenticate from `/mcp` or with `claude mcp login <name>`. Pass `--no-browser` over SSH to paste the redirect URL, and use `claude mcp logout <name>` to clear credentials. Tokens are stored securely and refreshed; a 401 triggers one refresh and retry.
- **Pre-registered apps:** `--client-id`, `--client-secret` (masked prompt, or `MCP_CLIENT_SECRET` in CI) and `--callback-port 8080`, matching a redirect URI of `http://localhost:8080/callback`. In JSON, use the `oauth` object with `clientId`, `callbackPort`, `authServerMetadataUrl` (must be `https://`) and `scopes`, a space-separated list that pins the requested scopes. A 403 `insufficient_scope` from the server fails the call with a `needs additional permissions` message naming the scope and marks the server as needing authentication; because Claude Code only ever requests the pinned scopes, add the named one to `scopes` before authenticating again.
- **Static tokens:** `--header "Authorization: Bearer <token>"`. A rejected configured header is reported as a failed connection, not a sign-in prompt.
- **Dynamic headers:** `"headersHelper": "/opt/bin/get-mcp-auth-headers.sh"` must print a JSON object of string headers within 10 seconds. It runs on every connection and receives `CLAUDE_CODE_MCP_SERVER_NAME` and `CLAUDE_CODE_MCP_SERVER_URL`. Helpers from repositories or plugins run without credential-like environment variables.

## Tool search and context

Tool search is on by default: only tool names and server instructions load at start, and Claude discovers full schemas on demand, so adding servers barely affects context. Tool descriptions and server instructions are truncated at 2KB each. Tool search is off when `ANTHROPIC_BASE_URL` points at a non-first-party host, and it requires Claude Sonnet 4.5, Haiku 4.5, Opus 4.5 or later. It is unavailable on Microsoft Foundry deployments hosted on Azure.

| `ENABLE_TOOL_SEARCH` | Behavior |
| :-- | :-- |
| unset | Defer all MCP tools, with the fallbacks above |
| `true` | Defer, and send the beta header through proxies |
| `auto` / `auto:N` | Load upfront until definitions reach 10% (or N%) of the context window, then defer |
| `false` | Load all tools upfront |

Set `"alwaysLoad": true` on a server, or `"anthropic/alwaysLoad": true` in a tool's `_meta`, to skip deferral for tools Claude needs every turn. Deny `ToolSearch` in permissions to disable the tool. `/context all` shows per-tool token cost ([[context-window]]). The API-level mechanics are on [[advanced-tool-use]].

## Timeouts and output limits

- `MCP_TIMEOUT` sets the server startup timeout, 30 seconds by default: `MCP_TIMEOUT=60000 claude`.
- `CLAUDE_CODE_MCP_STARTUP_WAIT_MS` bounds how long the first turn of a non-interactive session waits for servers that are still connecting (`0` doesn't wait); their tools arrive on a later turn.
- A per-server `"timeout"` in milliseconds overrides `MCP_TOOL_TIMEOUT` for tool calls. Values under 1000 are ignored.
- A call with no response or progress for the idle window aborts. The window is five minutes for remote servers and 30 minutes for stdio; set `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT` (`0` disables it).
- A main-conversation call still running after two minutes moves to a background task listed in `/tasks`. Set `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS` (`0` disables it).
- Output over 10,000 tokens shows a warning. The default maximum is 25,000 tokens (`MAX_MCP_OUTPUT_TOKENS=50000` raises it). Larger text results are saved to a file that Claude reads on demand. Server authors can set `_meta["anthropic/maxResultSizeChars"]` per tool, up to 500,000 characters.
- `_meta["anthropic/requiresUserInteraction"]: true` forces a permission prompt on every call, in every mode, and hooks can't auto-allow it.

## Plugin servers, connectors, resources and prompts

- **Plugin servers** start with the plugin. Their tools are named `mcp__plugin_<plugin-name>_<server-name>__<tool-name>`; use that full name in permission rules, `allowed-tools`, subagent `tools` and hook matchers ([[plugins]], [[hooks]]).
- **claude.ai connectors** load automatically when you are signed in with a claude.ai subscription and no API key, `apiKeyHelper` or third-party provider is active. Turn them off with `"disableClaudeAiConnectors": true` or `ENABLE_CLAUDEAI_MCP_SERVERS=false`. Organizations can set connector tools to `ask`, which prompts on every call, or `blocked`, which hides the tool.
- **Resources:** type `@` and reference `@github:issue://123`.
- **Prompts** appear in the `/` menu as `/servername:promptname (MCP)` and also run as `/mcp__github__pr_review 456`.
- **Elicitation:** servers can request form input or open a URL mid-task; the `Elicitation` hook can answer automatically.
- **Channels:** a server declaring `claude/channel` can push events into the session with `--channels` ([[channels]]).

## Managed MCP for organizations

| Pattern | Configure |
| :-- | :-- |
| Disable MCP | `managed-mcp.json` with `{"mcpServers": {}}` |
| Fixed deployment | `managed-mcp.json` listing the servers |
| Provided servers alongside users' own | `managedMcpServers` in managed settings (remote `http`/`sse` over `https://` only, no `${VAR}`) |
| Approved catalog | `allowedMcpServers` plus `allowManagedMcpServersOnly: true` |
| Plugin servers only | `strictPluginOnlyCustomization` including `mcp` |
| Denylist | `deniedMcpServers` |

- `managed-mcp.json` lives at `/Library/Application Support/ClaudeCode/managed-mcp.json` (macOS), `/etc/claude-code/managed-mcp.json` (Linux and WSL) or `C:\Program Files\ClaudeCode\managed-mcp.json` (Windows). It takes exclusive control: user, plugin and `--mcp-config` servers are blocked, and claude.ai connectors are suppressed unless `allowAllClaudeAiMcps` is set. Server-managed settings can't deliver it. Don't put credentials in it.
- List entries match by `serverUrl` (with `*` wildcards), `serverCommand` (exact argument array) or `serverName`. A name is a user-chosen label and not a security control. The denylist always wins and merges from every scope. Without `allowManagedMcpServersOnly`, users can extend the allowlist; with it, the lock applies from every admin-controlled managed source and the managed allowlist comes from the highest-ranked source that sets one.
- Blocked servers disappear silently from `/mcp`, and `claude mcp add` fails with an enterprise-policy error, so tell users what you block. Setting `OTEL_LOG_TOOL_DETAILS=1` records server and tool names in telemetry. Managed settings delivery is on [[enterprise-admin]].

## Troubleshooting

- `No MCP servers configured`: a local-scope server was added in a different project, or a file sits at a path Claude Code doesn't read.
- Failed connection: read the detail in `claude mcp get <name>`, run `curl -I <url>` (401 or 403 means authentication is needed, 404 or 405 means the host is up), or run the stdio command by hand. A missing `--` puts server flags in the wrong place.
- Connected but no tools: usually a missing environment variable; pass `--env KEY=value`.
