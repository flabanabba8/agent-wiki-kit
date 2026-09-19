---
title: LLM Gateways
type: how-to
tldr: "Route Claude Code through a gateway"
sources:
  - raw/docs/official/gateways.md
  - raw/docs/official/llm-gateway.md
  - raw/docs/official/llm-gateway-connect.md
  - raw/docs/official/llm-gateway-rollout.md
  - raw/docs/official/llm-gateway-protocol.md
  - raw/docs/official/claude-apps-gateway.md
  - raw/docs/official/claude-apps-gateway-deploy.md
  - raw/docs/official/claude-apps-gateway-config.md
  - raw/docs/official/third-party-integrations.md
  - raw/docs/official/amazon-bedrock.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
  - raw/docs/changelog-2.1.275-to-2.1.278.md
related: ["[[cloud-providers]]", "[[enterprise-admin]]", "[[settings]]", "[[data-and-privacy]]", "[[open-models]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [llm-gateway, anthropic-base-url, claude-apps-gateway, gateway-setup, api-key-helper]
valid_until: 2027-03-15
---

# LLM Gateways

A gateway is a proxy your organization runs between Claude Code and a model provider. Developers authenticate to it with a gateway-issued credential; it forwards their requests under one organization-held credential for the Anthropic API or a cloud provider ([[cloud-providers]]). That gives one place for credentials, per-developer usage tracking, budgets and rate limits, audit logging and provider switching. Anthropic doesn't endorse third-party gateway products and doesn't support routing Claude Code to non-Claude models; see [[open-models]].

A gateway is not a corporate proxy: `HTTPS_PROXY`/`HTTP_PROXY` front *all* traffic, gateway variables only model API requests. Use both at once if you need to.

## Two options

| | Claude apps gateway | Other LLM gateway |
|---|---|---|
| What it is | Anthropic's self-hosted gateway, built into the `claude` binary | A product your organization runs |
| Developer sign-in | Corporate IdP (OIDC) through `/login`; a browser device flow, so no unattended CI | Static key, bearer token or `apiKeyHelper`, so CI works |
| Compatibility | Ships with each Claude Code release | You keep header and body forwarding current |

## Billing

A gateway credential (`ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY`, an `apiKeyHelper` or a Claude apps gateway sign-in) sets the developer's claude.ai subscription aside: requests bill per token at API rates to the account behind the gateway's provider credential — your Console organization, or your Bedrock, Agent Platform or Foundry account.

With **only** `ANTHROPIC_BASE_URL` and no gateway credential, a saved claude.ai login stays active: requests route through the gateway under subscription limits and billing, and the gateway must forward the OAuth capability in `anthropic-beta` or they fail with `401`.

## Connect a developer machine

If an administrator already distributed the configuration, `claude` opens with no login screen and `/status` shows an `Anthropic base URL` line plus an `Auth token` or `API key` line. Otherwise pick the credential variable matching how the gateway reads keys:

| Variable | Sent as | Use when |
|---|---|---|
| `ANTHROPIC_AUTH_TOKEN` | `Authorization: Bearer` | "Bearer token", or you weren't told |
| `ANTHROPIC_API_KEY` | `x-api-key` | "API key" or "x-api-key"; needs a one-time approval in interactive mode |
| `apiKeyHelper` setting | Both headers | Key rotates or comes from a vault |

```bash
export ANTHROPIC_BASE_URL=https://llm-gateway.example.com
export ANTHROPIC_AUTH_TOKEN=sk-gateway-key

curl -X POST "$ANTHROPIC_BASE_URL/v1/messages" \
  -H "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN" \
  -H "anthropic-version: 2023-06-01" -H "content-type: application/json" \
  -d '{"model": "claude-sonnet-4-6", "max_tokens": 1, "messages": [{"role": "user", "content": "."}]}'
```

A response starting `{"id":"msg_` works; an unknown-model error still proves the URL and credential good, and a `401` means trying the other variable.

Persist the values, including for background agents, in the `env` block of `~/.claude/settings.json` or `.claude/settings.local.json`, never a committed `.claude/settings.json`; a settings-file `env` value beats a shell export of the same variable ([[settings]]).

**apiKeyHelper:** a command printing only the credential to stdout (`"apiKeyHelper": "~/bin/get-gateway-key.sh"`), cached five minutes; change that with `CLAUDE_CODE_API_KEY_HELPER_TTL_MS`.

**Optional:**

- `ANTHROPIC_CUSTOM_HEADERS`: extra `Name: Value` headers, one per line (`\n` in JSON).
- `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`: queries the gateway's `GET /v1/models?limit=1000` at startup and adds those names to `/model`. Raise the 3-second timeout with `CLAUDE_CODE_GATEWAY_MODEL_DISCOVERY_TIMEOUT_MS`; any redirect counts as failure, so serve the endpoint at the base URL itself.
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`: for networks that allow egress only to the gateway; it also disables auto-updates and the fast mode availability check, but not the WebFetch domain check ([[data-and-privacy]]).
- `CLAUDE_CODE_SKIP_FAST_MODE_NETWORK_ERRORS` or `CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK`: restore fast mode, whose check calls `api.anthropic.com`.

### Route to a cloud provider through the gateway

Use these only if your gateway team names a provider route. Foundry and Claude Platform on AWS routes use the Anthropic Messages format. A Bedrock or Agent Platform route sends that provider's native format: its model IDs, the `anthropic-beta` subset those providers accept, and fixed thinking budgets instead of adaptive reasoning, effort and context-management fields. `ANTHROPIC_BASE_URL` sends Anthropic IDs and everything the Claude API accepts; a Claude apps gateway sign-in sends Anthropic IDs with the narrower subset. For a model ID Claude Code doesn't recognize, such as a gateway alias, it assumes a 200K context window (1M when the ID carries `[1m]`); a `modelOverrides` entry mapping the real Anthropic ID to the alias supplies that model's capabilities.

| Provider | Base URL variable | Skip client auth | Gateway token |
|---|---|---|---|
| Bedrock | `ANTHROPIC_BEDROCK_BASE_URL` + `CLAUDE_CODE_USE_BEDROCK=1` | `CLAUDE_CODE_SKIP_BEDROCK_AUTH=1` (leave `AWS_BEARER_TOKEN_BEDROCK` unset) | `ANTHROPIC_AUTH_TOKEN` |
| Bedrock Mantle | `ANTHROPIC_BEDROCK_MANTLE_BASE_URL` + `CLAUDE_CODE_USE_MANTLE=1` | `CLAUDE_CODE_SKIP_MANTLE_AUTH=1` | — |
| Agent Platform | `ANTHROPIC_VERTEX_BASE_URL` + `CLAUDE_CODE_USE_VERTEX=1` (+ `ANTHROPIC_VERTEX_PROJECT_ID`, `CLOUD_ML_REGION`) | `CLAUDE_CODE_SKIP_VERTEX_AUTH=1` | `ANTHROPIC_AUTH_TOKEN` |
| Foundry | `ANTHROPIC_FOUNDRY_BASE_URL` + `CLAUDE_CODE_USE_FOUNDRY=1` | `CLAUDE_CODE_SKIP_FOUNDRY_AUTH=1` (only if the gateway injects `Authorization`) | `ANTHROPIC_FOUNDRY_API_KEY` or `ANTHROPIC_FOUNDRY_AUTH_TOKEN` |
| Claude Platform on AWS | `ANTHROPIC_AWS_BASE_URL` + `CLAUDE_CODE_USE_ANTHROPIC_AWS=1` (+ `ANTHROPIC_AWS_WORKSPACE_ID`) | `CLAUDE_CODE_SKIP_ANTHROPIC_AWS_AUTH=1` | `ANTHROPIC_AUTH_TOKEN` |

`/status` then shows rows such as `Bedrock base URL` and `AWS auth skipped`.

### Other surfaces

- **VS Code:** put the variables in `claudeCode.environmentVariables`; the extension's login check doesn't read `~/.claude/settings.json`.
- **Desktop app:** reads its own third-party inference configuration (Developer → Configure Third-Party Inference, or from an admin) and runs only local sessions on a gateway.
- **GitHub Actions:** set `ANTHROPIC_BASE_URL` in `env` and pass the key as `anthropic_api_key`, plus `ANTHROPIC_AUTH_TOKEN` in `env` for bearer gateways.
- **Agent SDK:** in TypeScript, `options.env` replaces the environment, so spread `process.env`; in Python, `env` merges ([[agent-sdk]]).
- Slack and cloud sessions always use Anthropic's API, and gateway variables set on a cloud environment are ignored. A gateway credential also disables voice dictation and Remote Control; Remote Control stops for any non-Anthropic `ANTHROPIC_BASE_URL` host.

## Roll out a gateway (admins)

The gateway must:

- Accept a supported API format, normally `POST /v1/messages`.
- **Stream** server-sent events as they arrive, including keep-alive pings; Claude Code aborts a stream silent for 300 seconds.
- Route Claude model names such as `claude-sonnet-4-6` upstream.
- Forward `anthropic-beta`, `anthropic-version` and request bodies unchanged, as open lists rather than allowlists.
- Return upstream errors unmodified: Claude Code's automatic recovery matches on error wording.
- Be exempt from request-body WAF inspection, whose XSS rules return `403` on prompts containing source code.

Distribute the base URL and credential through a managed settings file ([[enterprise-admin]]):

```json
{
  "env": { "ANTHROPIC_BASE_URL": "https://llm-gateway.example.com" },
  "apiKeyHelper": "/usr/local/bin/get-gateway-key"
}
```

- A managed `ANTHROPIC_BASE_URL` is enforced over shell exports.
- Don't add `forceLoginMethod` or `forceLoginOrgUUID` alongside a gateway credential: either key blocks `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` and `apiKeyHelper` at startup.
- Server-managed settings need a direct connection to `api.anthropic.com`, so gateway sessions rely on file or MDM delivery.
- Size per-key rate limits for client retries: up to 10 attempts with backoff, honoring `Retry-After`.
- Pin developers to a tested release with `requiredMaximumVersion` or `DISABLE_UPDATES`: feature-flag defaults, the starting model, alias resolution and model-capability assumptions are built into each build, so an upgrade can change behavior silently. `ANTHROPIC_DEFAULT_MODEL` and the `ANTHROPIC_DEFAULT_*_MODEL` variables hold the model choice constant.

Verify from a developer machine with a streaming request (`"stream": true`): `data:` lines should arrive incrementally, and `/status` should list managed settings under `Setting sources`.

### What Claude Code sends

| Header | Use |
|---|---|
| `anthropic-version`, `anthropic-beta` | Forward verbatim |
| `anthropic-workspace-id` | Forward when the upstream is Claude Platform on AWS |
| `x-claude-code-session-id` | Group requests by session |
| `x-claude-code-agent-id`, `x-claude-code-parent-agent-id` | Attribute cost to subagents (identifies an agent, not a person) |
| `x-claude-code-request-class`, `x-claude-code-agent-type`, `x-claude-code-prev-tool-durations`, `x-claude-code-compaction`, `x-claude-code-context-compacted` | Routing and scheduling hints, sent only with `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1` |

Token-counting endpoints are optional; without them `/context` shows estimates. Forward `cache_control` unchanged, or every turn bills as uncached input. If the upstream rejects beta fields with `400 Extra inputs are not permitted` — common when Anthropic-format requests reach Bedrock — set `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` or use the matching provider route.

Going back: return `content-type: text/event-stream` on streamed Anthropic-format responses and relay `application/vnd.amazon.eventstream` untouched on Bedrock-format ones; write `retry-after` as integer seconds, not an HTTP date, since above 60 it stops the retries and surfaces the error at once; pass `x-should-retry` through so retry decisions match the upstream's, and `anthropic-ratelimit-unified-*` so plan limits and spend caps display. A `400` naming a thinking block `bound to a different conversation` is the API's preserved-thinking check, which a gateway that rewrites `system`, `tools` or earlier message content trips itself.

## Claude apps gateway

Run it with `claude gateway --config gateway.yaml`. It needs an OIDC IdP (Okta, Entra ID, Google Workspace, Keycloak, Dex; no SAML or LDAP), PostgreSQL 14 or later, HTTPS on a hostname that resolves only to private addresses, and a native Linux host. Upstreams can be Bedrock (not Mantle), Claude Platform on AWS, Agent Platform, Foundry or the Anthropic API. Failover runs in order and keeps no state, so a down upstream is tried again on every request that reaches it.

Connect developers with these keys in the device's managed settings file:

```json
{
  "forceLoginMethod": "gateway",
  "forceLoginGatewayUrl": "https://claude-gateway.internal.example.com",
  "parentSettingsBehavior": "merge"
}
```

Developers press Enter at `/login`, accept the pinned TLS fingerprint and confirm the account the gateway names before the credential is saved. Sessions expire within `ttl_hours` (one hour by default) after IdP deprovisioning.

For an internal network numbered from public IPv4 space your organization owns, list up to four non-overlapping blocks in the managed `gatewayInternalNetworks` key, read only from a source on the machine (file, plist, HKLM or a policy helper). Every address the gateway name resolves to, and the developer's own, must sit in one listed block over a direct connection. An invalid entry makes `/login` refuse every new gateway sign-in on that machine.

The gateway enforces model access server-side, delivers per-group managed settings hourly, relays OTLP/HTTP telemetry and supports per-user spend limits. It logs no prompt or completion content.

Operating it:

- `store.postgres_url` holds the database URL, `store.connect_timeout_seconds` the Postgres connect timeout (5 seconds by default) and `store.max_connections` the per-replica pool size (5 by default).
- A replica sends at most 256 requests upstream at once, counting a stream until it ends; it logs the limit at startup, warns when more are open, and queues the rest in memory. Add replicas, or raise `BUN_CONFIG_MAX_HTTP_REQUESTS` and size the container's memory for peak open requests.
- On `SIGTERM`, in-flight requests get up to 25 seconds; `CLAUDE_GATEWAY_DRAIN_TIMEOUT_MS` changes the window. Keep the orchestrator's grace period at least five seconds longer.
- Sign-in is rate limited per client IP (30 starts and 10 code submissions per 10 minutes). Set `listen.trusted_proxies` so the gateway sees the developer's address, not the load balancer's, and raise `rate_limits` when many developers share a NAT egress address.
- `access_control.allow_cidrs` restricts which client addresses the gateway serves; an empty list serves everyone and logs a warning.
- `CLAUDE_GATEWAY_PROXY_IS_EGRESS_BOUNDARY=1` suits a gateway whose only egress is the forward proxy in `HTTPS_PROXY`: outbound requests hand the proxy a hostname instead of a locally resolved IP, moving the SSRF check onto the proxy's allowlist. It stays off unless `NO_PROXY` and `no_proxy` are empty and `CLAUDE_GATEWAY_ALLOW_LOOPBACK` is unset.
- A `headers:` map on an upstream sends fixed headers to a proxy in front of a provider, with `${VAR}` or `${file:/path}` expansion. `authorization`, `x-api-key`, `host`, `content-type`, `user-agent` and any `anthropic-`, `x-goog-`, `x-amz-` or `x-amzn-` name are reserved.
- Relayed Claude Desktop and Cowork telemetry carries `enduser.sub`, the IdP subject.

Gateway sessions have no server-side web search, no `/design-sync` or `/import`, no 1-hour cache TTL and no first-party-only optimizations.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Startup warning naming two credential sources | Unset the variable, or `/logout` to keep only the gateway credential |
| `401` | Wrong header or variable; see the credential table |
| `API returned an empty or malformed response (HTTP 200)` | The gateway returned HTML or a login page; test with curl |
| `400` naming `thinking`/`adaptive` | Upgrade the upstream model build; on Opus/Sonnet 4.6, `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` |
| Gateway-worded context-limit `400` | `/compact`, then set `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (minimum 100,000) and `CLAUDE_CODE_MAX_OUTPUT_TOKENS` |
| Login prompt even though curl works | Set `ANTHROPIC_AUTH_TOKEN` in the shell, user settings `env` or managed settings; a project `env` waits for trust |
| `ANTHROPIC_API_KEY` silently ignored | Approve it under `/config` → `Use custom API key` |
