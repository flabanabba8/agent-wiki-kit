---
title: Enterprise Administration
type: how-to
tldr: "Managed settings, policy, OTel, analytics"
sources:
  - raw/docs/official/admin-setup.md
  - raw/docs/official/managed-settings.md
  - raw/docs/official/server-managed-settings.md
  - raw/docs/official/monitoring-usage.md
  - raw/docs/official/analytics.md
  - raw/docs/official/plugin-marketplaces.md
  - raw/docs/official/third-party-integrations.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
related: ["[[settings]]", "[[cloud-providers]]", "[[llm-gateways]]", "[[data-and-privacy]]", "[[plugins]]", "[[mcp]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [managed-settings, server-managed-settings, mdm-policy, opentelemetry-monitoring, claude-code-analytics]
---

# Enterprise Administration

Organizations enforce policy through **managed settings**, which sit above every user, project and command-line value ([[settings]]). This page covers how to deliver them, what to lock down, and how to measure usage and adoption. SSO, SCIM and seat assignment are configured at the Claude account level, not in Claude Code.

| Decision | Where |
|---|---|
| API provider (Teams/Enterprise, Console, Bedrock, Agent Platform, Foundry) | [[cloud-providers]] |
| How settings reach devices | Below |
| What to enforce | Below; permission syntax on [[permissions-and-modes]] |
| Usage visibility | Below; spend on [[costs-and-usage]] |
| Data handling | [[data-and-privacy]] |
| Central credentials and audit log | [[llm-gateways]] |

## Delivery mechanisms

| Mechanism | Location | Read | Priority |
|---|---|---|---|
| Server-managed | claude.ai **Admin Settings > Claude Code > Managed settings**, or a Claude apps gateway | Startup, then hourly | Highest |
| MDM / OS policy | macOS `com.anthropic.claudecode` profile; Windows `HKLM\SOFTWARE\Policies\ClaudeCode` (`Settings` value) | Startup, then every 30 min | High |
| File-based | macOS `/Library/Application Support/ClaudeCode/managed-settings.json`; Linux/WSL `/etc/claude-code/managed-settings.json`; Windows `C:\Program Files\ClaudeCode\managed-settings.json` | Startup and on file change | Medium |
| Windows user registry | `HKCU\SOFTWARE\Policies\ClaudeCode` | Every 30 min | Lowest; user-writable, so not an enforcement channel |

Minimal file:

```json
{
  "permissions": {
    "deny": ["Read(./.env)", "Read(./secrets/**)"],
    "disableBypassPermissionsMode": "disable"
  },
  "allowManagedPermissionRulesOnly": true
}
```

- **Drop-ins:** several teams can own parts of a file-based policy in `managed-settings.d/*.json`. These files merge alphabetically after `managed-settings.json`. Single values are replaced, lists are unioned, and nested blocks such as `env` merge key by key. MDM templates for Jamf, Iru, Intune and Group Policy live in the anthropics/claude-code repo under `examples/mdm`.
- **Several sources on one machine:** by default (`managedSourcesBehavior: "first-wins"`) Claude Code uses only the highest-ranked source that carries a policy key. A few keys are read from every admin source anyway: the sandbox locks, `forceRemoteSettingsRefresh`, `maxEffortLevel`, and `env`, which merges per variable. Set `"merge"` in the top source to compose all admin sources: lists union, locks take the strictest value, and allowlists such as `availableModels` come whole from the top source.
- **WSL** reads only `/etc/claude-code` unless `wslInheritsWindowsSettings: true` is set in HKLM or the Windows file.
- **Surfaces:** managed settings reach the terminal, the IDE extensions, the desktop Code tab and Agent SDK sessions. Anthropic-hosted cloud sessions receive **only server-managed settings**, and Cowork sessions never fetch them. A developer's `--model` or `ANTHROPIC_MODEL` still picks a session model under a managed `model`, so deploy `availableModels` if you need a lock.

### Server-managed settings

- **Requirements:** Teams or Enterprise, the Owner or Primary Owner role, and clients that reach `api.anthropic.com` directly with a Team/Enterprise OAuth login, `CLAUDE_CODE_OAUTH_TOKEN`, or a directly configured API key.
- **When the fetch is skipped:** `apiKeyHelper` keys and exported `CLAUDE_CODE_USE_*` or custom `ANTHROPIC_BASE_URL` values skip it. Bedrock, Agent Platform, Foundry and Claude Platform on AWS fleets get equivalent remote delivery from a Claude apps gateway.
- **Approval dialogs:** hooks, shell-command settings (`apiKeyHelper`, `statusLine`, `otelHeadersHelper`), sensitive `env` variables and several sandbox settings require the user to approve a security dialog. Rejecting it exits Claude Code.
- **Fail-closed:** `forceRemoteSettingsRefresh: true` makes the CLI exit when a fresh fetch fails. `claude auth` subcommands are exempt.
- **Limitations:** one policy for the whole organization (no per-group targeting); no `managed-mcp.json` delivery; `policyHelper` and `wslInheritsWindowsSettings` are not honored.
- **Security model:** it is a client-side control, not a security boundary. On unmanaged devices, a user can bypass it by setting a third-party provider variable or editing the cache. MDM-protected endpoint settings are stronger.
- **Audit:** events for settings changes come through the compliance API or audit log export.

## What to enforce

| Control | Keys |
|---|---|
| Permission rules and lockdown | `permissions.allow`, `permissions.deny`, `allowManagedPermissionRulesOnly`, `permissions.disableBypassPermissionsMode` |
| Starting mode, auto mode off | `permissions.defaultMode`, `permissions.disableAutoMode` |
| OS sandbox with domain allowlist | `sandbox.enabled`, `sandbox.network.allowedDomains`, `sandbox.network.allowManagedDomainsOnly` |
| Org-wide instructions | `claudeMd`, or a managed CLAUDE.md file |
| MCP servers ([[mcp]]) | `allowedMcpServers`, `deniedMcpServers`, `allowManagedMcpServersOnly`, `managedMcpServers`, `managed-mcp.json` |
| Plugin sources ([[plugins]]) | `strictKnownMarketplaces`, `blockedMarketplaces`, `disableSideloadFlags`, `disableCommandPluginSources`, `pluginSuggestionMarketplaces` |
| Customization only via plugins or managed | `strictPluginOnlyCustomization` |
| Hooks | `allowManagedHooksOnly`, `allowedHttpHookUrls` |
| Login | `forceLoginMethod`, `forceLoginOrgUUID` (these block `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` and `apiKeyHelper` sessions) |
| Background agents | `disableAgentView`, or `processWrapper` for a corporate launcher |
| Models and effort | `availableModels`, `enforceAvailableModels`, `maxEffortLevel` |
| Versions | `minimumVersion` (blocks downgrades), `requiredMinimumVersion`/`requiredMaximumVersion` (refuses to start outside the range) |
| Telemetry to Anthropic | `env` with `DISABLE_TELEMETRY` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` ([[data-and-privacy]]) |

Permission rules and sandboxing work at different layers. Denying WebFetch doesn't stop `curl` through an allowed Bash; only the sandbox's network allowlist does ([[sandboxing-and-security]]). On Enterprise plans that sign in through claude.ai or the Anthropic API, the admin console can also disable models, set a default model and cap effort server-side. Those controls don't reach cloud-provider sessions.

## Verify enforcement

Have a developer run `/status`. `Setting sources` shows `Enterprise managed settings` with the selected source: `(remote)`, `(plist)`, `(HKLM)`, `(file)`, `(drop-ins)`, `(HKCU)`, `(parent process)`, `(helper)`, or a list ending `, merged`. A `Skipped sources` line names any source that was found but overridden. If the line is missing, no source delivered a policy key. `claude doctor` lists dropped entries, and shows `Managed settings (remote)` (the fetch outcome) and `Organization policy` lines. An unparseable managed file stops Claude Code from starting.

## Distribute plugins

- **Per repository:** declare `extraKnownMarketplaces` (for example, a GitHub repo source) and `enabledPlugins` (`"code-formatter@company-tools": true`) in `.claude/settings.json`. They apply once teammates trust the folder.
- **Organization-wide:** upload or sync plugins in claude.ai **Organization settings > Plugins**. A plugin with a top-level `bin/` directory is rejected.
- **Containers and CI:** prebuild a read-only seed and point `CLAUDE_CODE_PLUGIN_SEED_DIR` at it. Build the seed with `CLAUDE_CODE_PLUGIN_CACHE_DIR=/opt/claude-seed claude plugin install my-tool@your-plugins`.
- **Lockdown:** `strictKnownMarketplaces` unset means no restriction, `[]` blocks every marketplace (including the official one), and a list acts as an allowlist.

## Monitor with OpenTelemetry

OTel export works on every provider and is opt-in:

```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://collector.example.com:4317",
    "OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Bearer example-token"
  }
}
```

- **Locking the collector:** a managed `OTEL_EXPORTER_OTLP_ENDPOINT`, protocol or headers value strips conflicting developer-set per-signal variables. Exporter selectors are not locked unless you set them in managed settings too.
- **Metrics:** `claude_code.session.count`, `lines_of_code.count`, `pull_request.count`, `commit.count`, `cost.usage` (USD), `token.usage`, `code_edit_tool.decision` and `active_time.total`, all prefixed `claude_code.`.
- **Events and spans:** `claude_code.user_prompt`, and `claude_code.managed_settings_resolved`, which reports the managed-settings sources in effect and the policy helper's state; `OTEL_LOG_MANAGED_SETTINGS=1` adds the redacted settings and their digests. The `claude_code.llm_request` trace span carries an `effort` attribute, as the `api_request` event does.
- **Privacy defaults:** prompt text, assistant responses, tool arguments, tool content and raw API bodies are off until you set `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_ASSISTANT_RESPONSES`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_TOOL_CONTENT` or `OTEL_LOG_RAW_API_BODIES`. With OAuth, `user.email` is included, sent only to your collector. `OTEL_LOG_TOOL_DETAILS=1` also puts real agent, skill, plugin and MCP server names on cost and token metrics.
- **Cardinality:** trim attributes with `OTEL_METRICS_INCLUDE_SESSION_ID`, `OTEL_METRICS_INCLUDE_ACCOUNT_UUID` and similar flags.
- **Debugging:** if nothing arrives, run `claude --debug` and look for `[3P telemetry]` errors.

## Analytics dashboards

| Plan | Dashboard | Contents |
|---|---|---|
| Teams / Enterprise | claude.ai/analytics/claude-code (Admins, Owners) | Lines accepted, accept rate, DAU/sessions, contribution metrics, leaderboard, CSV export |
| Console | platform.claude.com/claude-code (UsageView permission) | Lines accepted, accept rate, activity, estimated spend, per-member table |

- **Contribution metrics** (public beta) need a GitHub admin to install github.com/apps/claude, then an Owner to enable Claude Code analytics and GitHub analytics. Data appears within about 24 hours. They support GitHub Cloud and Enterprise Server, and are unavailable with ZDR.
- **Attribution:** sessions from 21 days before to 2 days after a merge are matched, and code rewritten by more than 20% isn't counted. Attributed PRs get the `claude-code-assisted` label.
- **APIs:** the Enterprise Analytics API uses a Primary Owner key with `read:analytics`; Console organizations use the Claude Code Analytics API with an Admin key.
- **Not available:** there is no analytics dashboard on cloud providers. Per-user token and cost numbers come from OTel or the Teams/Enterprise spend report.

## Drive adoption

- Invest in CLAUDE.md files at several levels.
- Offer a one-click install.
- Start people on codebase Q&A and small fixes with plans.
- Pin model versions on cloud providers.
- Check a central `.mcp.json` into repositories.

For onboarding problems:

- To switch accounts, run `/logout` then `/login`.
- If the enterprise auth option is missing, run `claude update` and restart the terminal.
- "You haven't been added to your organization yet" means the seat lacks Claude Code access.
