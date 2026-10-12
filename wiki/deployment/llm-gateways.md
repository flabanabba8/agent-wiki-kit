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
  - raw/docs/changelog-2.1.275-to-2.1.282.md
related: ["[[cloud-providers]]", "[[enterprise-admin]]", "[[settings]]", "[[data-and-privacy]]", "[[open-models]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [llm-gateway, anthropic-base-url, claude-apps-gateway, gateway-setup, api-key-helper]
valid_until: 2027-03-15
---

# LLM Gateways

A gateway is a proxy your organization runs between Claude Code and a model provider. Developers use a gateway-issued credential; the gateway forwards requests to the Anthropic API or a cloud provider ([[cloud-providers]]) with one organization-held credential. That gives you one place for credentials, per-developer usage tracking, budgets and rate limits, audit logging and provider switching. This page covers the official configuration only. Anthropic doesn't endorse third-party gateway products and doesn't support routing Claude Code to non-Claude models; for that, see [[open-models]].

A gateway is not a corporate proxy: `HTTPS_PROXY`/`HTTP_PROXY` cover *all* traffic, gateway variables only model requests. Both can coexist.

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

If `claude` opens without a login screen, run `/status`: an `Anthropic base URL` line plus an `Auth token` or `API key` line means your admin already configured it.

Otherwise, pick the credential variable that matches how the gateway reads keys:

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
- `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`: queries the gateway's `GET /v1/models` at startup and adds those names to `/model`. The request times out after 3 seconds (`CLAUDE_CODE_GATEWAY_MODEL_DISCOVERY_TIMEOUT_MS` raises it) and treats any redirect as failure, so serve the endpoint directly at the base URL.
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`: for networks that allow egress only to the gateway. It also disables auto-updates and the fast mode availability check. The WebFetch domain check still calls `api.anthropic.com`; turn that off with `skipWebFetchPreflight: true`.
- `CLAUDE_CODE_SKIP_FAST_MODE_NETWORK_ERRORS` or `CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK`: restore fast mode, whose check calls `api.anthropic.com` directly.

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

- **VS Code:** set the variables in `claudeCode.environmentVariables` in VS Code user settings. The extension's login check doesn't read `~/.claude/settings.json`.
- **Desktop app:** reads its own third-party inference configuration, distributed by an admin or set under Developer → Configure Third-Party Inference. With a gateway, it runs only local sessions.
- **GitHub Actions:** set `ANTHROPIC_BASE_URL` in `env` and pass the key as `anthropic_api_key`. For bearer gateways, also set `ANTHROPIC_AUTH_TOKEN` in `env`.
- **Agent SDK:** in TypeScript, `options.env` replaces the environment, so spread `process.env`. In Python, `env` merges ([[agent-sdk]]).
- Slack and cloud sessions always use Anthropic's API. Remote Control and voice dictation are unavailable while a gateway credential is active, and Remote Control also while `ANTHROPIC_BASE_URL` points at a non-Anthropic host.

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

Verify with a streaming curl request (`data:` lines should arrive incrementally), then check `/status` → `Setting sources`.

### What Claude Code sends

| Header | Use |
|---|---|
| `anthropic-version`, `anthropic-beta` | Forward verbatim |
| `anthropic-workspace-id` | Forward when the upstream is Claude Platform on AWS |
| `x-claude-code-session-id` | Group requests by session |
| `x-claude-code-agent-id`, `x-claude-code-parent-agent-id` | Attribute cost to subagents (identifies an agent, not a person) |
| `x-claude-code-request-class`, `x-claude-code-agent-type`, `x-claude-code-prev-tool-durations`, `x-claude-code-compaction`, `x-claude-code-context-compacted` | Routing and scheduling hints with no prompt text. Sent by default on direct Anthropic API connections; through a custom base URL or cloud provider only with `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1` (`0` turns them off everywhere) |

Token-counting endpoints are optional; without them `/context` shows estimates. Forward `cache_control` unchanged, or every turn bills as uncached input. If the upstream rejects beta fields with `400 Extra inputs are not permitted` (common when Anthropic-format requests are forwarded to Bedrock), set `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` or use the matching provider route. A Bedrock-format gateway must relay `Content-Type: application/vnd.amazon.eventstream` untouched.

On responses, return `retry-after` as integer seconds (a value above 60 stops retries and shows the error), and pass `x-should-retry` and `anthropic-ratelimit-unified-*` through unchanged. If the gateway rejects the advisor tool entry as an unknown tool type (`Input tag 'advisor_20260301'`), Claude Code retries once without it and leaves the advisor out for that base URL until it exits.

An `ANTHROPIC_BASE_URL` gateway receives Anthropic IDs, the full beta set, and adaptive-reasoning and effort fields even for unrecognized alias IDs; provider-format routes and Claude apps gateway sign-ins send only the betas Bedrock and Agent Platform accept.

**Upgrades:** default models, aliases, feature-flag defaults and capability assumptions are built into each Claude Code version. Pin a tested version with `requiredMaximumVersion` (or `DISABLE_UPDATES` if you ship your own builds), pin models with `ANTHROPIC_DEFAULT_MODEL` and the `ANTHROPIC_DEFAULT_*_MODEL` variables, and map gateway aliases to Anthropic IDs with `modelOverrides`.

## Claude apps gateway

Going back: return `content-type: text/event-stream` on streamed Anthropic-format responses and relay `application/vnd.amazon.eventstream` untouched on Bedrock-format ones; write `retry-after` as integer seconds, not an HTTP date, since above 60 it stops the retries and surfaces the error at once; pass `x-should-retry` through so retry decisions match the upstream's, and `anthropic-ratelimit-unified-*` so plan limits and spend caps display. A `400` naming a thinking block `bound to a different conversation` is the API's preserved-thinking check, which a gateway that rewrites `system`, `tools` or earlier message content trips itself.

- An OIDC IdP (Okta, Entra ID, Google Workspace, Keycloak, Dex and others; no SAML or LDAP).
- PostgreSQL 14 or later.
- HTTPS on a hostname that resolves only to private addresses. If your internal network uses public IPv4 space you own, list up to four non-overlapping blocks (`/8` to `/32`) in the managed `gatewayInternalNetworks` setting; `/login` then accepts a gateway in a listed block only when the client connects directly from inside the same block. An invalid list refuses every new gateway sign-in on that machine. Set the gateway's `access_control.allow_cidrs` to the same blocks.
- A native Linux host.
- Claude Code v2.1.195 or later on the server and on clients.

Run it with `claude gateway --config gateway.yaml`. It needs an OIDC IdP (Okta, Entra ID, Google Workspace, Keycloak, Dex; no SAML or LDAP), PostgreSQL 14 or later, HTTPS on a hostname that resolves only to private addresses, and a native Linux host. Upstreams can be Bedrock (not Mantle), Claude Platform on AWS, Agent Platform, Foundry or the Anthropic API. Failover runs in order and keeps no state, so a down upstream is tried again on every request that reaches it.

Connect developers with these keys in the device's managed settings file:

```json
{
  "forceLoginMethod": "gateway",
  "forceLoginGatewayUrl": "https://claude-gateway.internal.example.com",
  "parentSettingsBehavior": "merge"
}
```

Developers press Enter at `/login` and accept the pinned TLS fingerprint; when the gateway names the signed-in account they confirm it too, and `/status` shows it. `/logout` also ends the session on gateways that advertise token revocation. Sessions are short-lived and expire within `ttl_hours` (one hour by default) after IdP deprovisioning.

For an internal network numbered from public IPv4 space your organization owns, list up to four non-overlapping blocks in the managed `gatewayInternalNetworks` key, read only from a source on the machine (file, plist, HKLM or a policy helper). Every address the gateway name resolves to, and the developer's own, must sit in one listed block over a direct connection. An invalid entry makes `/login` refuse every new gateway sign-in on that machine.

The gateway enforces model access server-side, delivers per-group managed settings hourly, relays OTLP/HTTP telemetry and supports per-user spend limits. It logs no prompt or completion content.

- `store.postgres_url` holds the database URL; `store.connect_timeout_seconds` (default 5) and `store.readiness_grace_seconds` tune Postgres connects and how long `/readyz` survives a failover.
- A replica sends at most 256 concurrent upstream requests. On `SIGTERM`, in-flight requests get 25 seconds (`CLAUDE_GATEWAY_DRAIN_TIMEOUT_MS`).
- Relayed Desktop and Cowork telemetry carries `enduser.sub`; `telemetry.resource_attributes` adds fixed labels.
- `CLAUDE_GATEWAY_PROXY_IS_EGRESS_BOUNDARY=1` hands hostnames to a forward proxy instead of resolving them locally.
- `desktop` policy blocks take Claude Desktop keys such as `disableBypassPermissionsMode`.

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
