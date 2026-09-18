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
  - raw/docs/official/third-party-integrations.md
  - raw/docs/official/amazon-bedrock.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
related: ["[[cloud-providers]]", "[[enterprise-admin]]", "[[settings]]", "[[data-and-privacy]]", "[[open-models]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [llm-gateway, anthropic-base-url, claude-apps-gateway, gateway-setup, api-key-helper]
valid_until: 2027-03-15
---

# LLM Gateways

A gateway is a proxy your organization runs between Claude Code and a model provider. Developers authenticate to the gateway with a gateway-issued credential. The gateway forwards requests to the Anthropic API or a cloud provider ([[cloud-providers]]) using one organization-held provider credential. That gives you one place for credentials, per-developer usage tracking, budgets and rate limits, audit logging and provider switching. This page covers the official configuration only. Anthropic doesn't endorse third-party gateway products and doesn't support routing Claude Code to non-Claude models; for that, see [[open-models]].

A gateway is not the same as a corporate proxy. `HTTPS_PROXY`/`HTTP_PROXY` sit in front of *all* traffic, while gateway variables route only model API requests. You can use both at once.

## Two options

| | Claude apps gateway | Other LLM gateway |
|---|---|---|
| What it is | Anthropic's self-hosted gateway, built into the `claude` binary | A product your organization already runs |
| Developer sign-in | Corporate IdP (OIDC) through `/login` | Static key, bearer token or `apiKeyHelper` |
| Keeping up with releases | Ships with each Claude Code release | You must keep header and body forwarding current |
| Policy | Model allowlists and managed settings per IdP group, OTLP telemetry, spend limits | Whatever the product offers, plus file-based managed settings |
| CI without a human | Not supported (browser device flow only) | Works with a static credential |

## Billing

When a gateway credential (`ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY`, an `apiKeyHelper`, or a Claude apps gateway sign-in) is active, the developer's claude.ai subscription is not used. Every request is billed per token, at API rates, to the account behind the gateway's provider credential: your Console organization, or your Bedrock, Agent Platform or Foundry account.

If you set **only** `ANTHROPIC_BASE_URL`, with no gateway credential, a saved claude.ai login stays active. Requests route through the gateway, but subscription limits and billing apply. The gateway must then forward the OAuth capability in `anthropic-beta`, or requests fail with `401`.

## Connect a developer machine

Check first whether your administrator already distributed the configuration. If `claude` opens a session without a login screen, run `/status`. An `Anthropic base URL` line plus an `Auth token` or `API key` line means you're done.

Otherwise, pick the credential variable that matches how the gateway reads keys:

| Variable | Sent as | Use when |
|---|---|---|
| `ANTHROPIC_AUTH_TOKEN` | `Authorization: Bearer` | "Bearer token", or you weren't told |
| `ANTHROPIC_API_KEY` | `x-api-key` | "API key" or "x-api-key"; needs a one-time approval in interactive mode |
| `apiKeyHelper` setting | Both headers | Key rotates or comes from a vault |

```bash
export ANTHROPIC_BASE_URL=https://llm-gateway.example.com
export ANTHROPIC_AUTH_TOKEN=sk-gateway-key

# verify before opening Claude Code
curl -X POST "$ANTHROPIC_BASE_URL/v1/messages" \
  -H "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN" \
  -H "anthropic-version: 2023-06-01" -H "content-type: application/json" \
  -d '{"model": "claude-sonnet-4-6", "max_tokens": 1, "messages": [{"role": "user", "content": "."}]}'
```

A response starting `{"id":"msg_` works. An unknown-model error still proves the URL and credential are good. A `401` means you should switch to the other credential variable.

To persist the values, including for background agents, put them in the `env` block of `~/.claude/settings.json` or `.claude/settings.local.json`. **Never** put them in a committed `.claude/settings.json`. A settings-file `env` value wins over a shell export of the same variable ([[settings]]).

**apiKeyHelper:** a command that prints only the credential to stdout, for example `"apiKeyHelper": "~/bin/get-gateway-key.sh"`. Output is cached for five minutes; change that with `CLAUDE_CODE_API_KEY_HELPER_TTL_MS`.

**Optional variables:**

- `ANTHROPIC_CUSTOM_HEADERS`: extra `Name: Value` headers, one per line (`\n` in JSON).
- `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`: queries the gateway's `GET /v1/models` at startup and adds those names to `/model`.
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`: for networks that allow egress only to the gateway. It also disables auto-updates and the fast mode availability check. The WebFetch domain check still calls `api.anthropic.com`; turn that off with `skipWebFetchPreflight: true`.
- `CLAUDE_CODE_SKIP_FAST_MODE_NETWORK_ERRORS` or `CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK`: restore fast mode, whose check calls `api.anthropic.com` directly.

### Route to a cloud provider through the gateway

Use these only if your gateway team names a provider route. Bedrock and Agent Platform routes send those providers' native formats, while Foundry and Claude Platform on AWS use the Anthropic Messages format.

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
- Slack and Claude Code on the web always use Anthropic's API. Remote Control and voice dictation are unavailable while a gateway credential is active, and Remote Control also while `ANTHROPIC_BASE_URL` points at a non-Anthropic host.

## Roll out a gateway (admins)

The gateway must:

- Accept a supported API format, normally `POST /v1/messages`.
- **Stream** server-sent events as they arrive, including keep-alive pings. Claude Code aborts a stream that is silent for 300 seconds.
- Route Claude model names such as `claude-sonnet-4-6` to upstream models.
- Forward `anthropic-beta`, `anthropic-version` and request bodies unchanged, treating them as open lists rather than allowlists.
- Return upstream errors unmodified, because Claude Code's automatic recovery matches on error wording.
- Exempt the path from request-body WAF inspection. Prompts containing source code trip XSS rules and return `403`.

Distribute the base URL and credential through a managed settings file ([[enterprise-admin]]):

```json
{
  "env": { "ANTHROPIC_BASE_URL": "https://llm-gateway.example.com" },
  "apiKeyHelper": "/usr/local/bin/get-gateway-key"
}
```

- A managed `ANTHROPIC_BASE_URL` is enforced over shell exports.
- Don't add `forceLoginMethod` or `forceLoginOrgUUID` alongside a gateway credential. Either key blocks `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` and `apiKeyHelper` at startup.
- Server-managed settings need a direct connection to `api.anthropic.com`, so gateway sessions rely on file or MDM delivery.
- Size per-key rate limits for client retries: up to 10 attempts with backoff, honoring `Retry-After`.

Verify from a developer machine with a streaming curl request (`"stream": true`); `data:` lines should arrive incrementally. Then check that `/status` shows managed settings under `Setting sources`.

### What Claude Code sends

| Header | Use |
|---|---|
| `anthropic-version`, `anthropic-beta` | Forward verbatim |
| `anthropic-workspace-id` | Forward when the upstream is Claude Platform on AWS |
| `x-claude-code-session-id` | Group requests by session |
| `x-claude-code-agent-id`, `x-claude-code-parent-agent-id` | Attribute cost to subagents (identifies an agent, not a person) |
| `x-claude-code-request-class`, `x-claude-code-agent-type`, `x-claude-code-prev-tool-durations`, `x-claude-code-compaction`, `x-claude-code-context-compacted` | Routing and scheduling hints, sent only with `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1` |

Token-counting endpoints are optional; without them `/context` shows estimates. Forward `cache_control` unchanged, or every turn bills as uncached input. If the upstream rejects beta fields with `400 Extra inputs are not permitted` (common when Anthropic-format requests are forwarded to Bedrock), set `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` or use the matching provider route. A Bedrock-format gateway must relay `Content-Type: application/vnd.amazon.eventstream` untouched.

## Claude apps gateway

Run it with `claude gateway --config gateway.yaml`. Prerequisites:

- An OIDC IdP (Okta, Entra ID, Google Workspace, Keycloak, Dex and others; no SAML or LDAP).
- PostgreSQL 14 or later.
- HTTPS on a hostname that resolves only to private addresses.
- A native Linux host.
- Claude Code v2.1.195 or later on the server and on clients.

Upstreams can be Bedrock (not Mantle), Claude Platform on AWS, Agent Platform, Foundry or the Anthropic API, with failover between them.

Connect developers by pushing these keys in the device's managed settings file:

```json
{
  "forceLoginMethod": "gateway",
  "forceLoginGatewayUrl": "https://claude-gateway.internal.example.com",
  "parentSettingsBehavior": "merge"
}
```

Developers press Enter at `/login` and accept the pinned TLS fingerprint. Sessions are short-lived and expire within `ttl_hours` (one hour by default) after IdP deprovisioning.

The gateway enforces model access server-side, delivers per-group managed settings with an hourly refresh, relays OTLP/HTTP telemetry, and supports per-user spend limits. It does not log prompt or completion content.

Operating it:

- `store.postgres_url` holds the database URL, and `store.connect_timeout_seconds` the Postgres connect timeout, 5 seconds by default.
- A replica sends at most 256 requests upstream at once. It logs that limit at startup and warns when more requests than that are open.
- On `SIGTERM`, in-flight requests have up to 25 seconds to finish; `CLAUDE_GATEWAY_DRAIN_TIMEOUT_MS` changes the window.
- Telemetry it relays for Claude Desktop and Cowork sessions carries `enduser.sub`, the IdP subject.

On gateway sessions these are unavailable:

- Server-side web search
- Remote Control
- `/design-sync` and `/import`
- The 1-hour cache TTL
- First-party-only optimizations

## Troubleshooting

| Symptom | Fix |
|---|---|
| Startup warning naming two credential sources | Unset the variable, or `/logout` to keep only the gateway credential |
| `401` | Wrong header or variable; see the credential table |
| `API returned an empty or malformed response (HTTP 200)` | The gateway returned an HTML or login page; test with curl |
| `400` naming `thinking`/`adaptive` | Upgrade the upstream model build; on Opus/Sonnet 4.6, `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` |
| Gateway-worded context-limit `400` | `/compact`, then set `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (minimum 100,000) and `CLAUDE_CODE_MAX_OUTPUT_TOKENS` |
| Login prompt even though curl works | Put `ANTHROPIC_AUTH_TOKEN` in the shell, the user settings `env`, or managed settings; project `env` waits for trust |
| `ANTHROPIC_API_KEY` silently ignored | Approve it under `/config` → `Use custom API key` |
