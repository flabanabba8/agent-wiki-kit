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
  - raw/docs/official/plugins__org.md
  - raw/docs/official/third-party-integrations.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
  - raw/docs/changelog-2.1.275-to-2.1.282.md
  - raw/docs/changelog-2.1.283-to-2.1.296.md
related: ["[[settings]]", "[[cloud-providers]]", "[[llm-gateways]]", "[[data-and-privacy]]", "[[plugins]]", "[[mcp]]"]
created: 2026-09-15
updated: 2026-10-11
confidence: high
last_verified: 2026-09-25
aliases: [managed-settings, server-managed-settings, mdm-policy, opentelemetry-monitoring, claude-code-analytics]
---

# Enterprise Administration

Organizations enforce policy through **managed settings**, which sit above every user, project and command-line value ([[settings]]). SSO, SCIM and seat assignment are configured at the Claude account level, not in Claude Code.

| Decision | Where |
|---|---|
| API provider (Teams/Enterprise, Console, Bedrock, Agent Platform, Foundry) | [[cloud-providers]] |
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
- **Several sources on one machine:** by default (`managedSourcesBehavior: "first-wins"`) Claude Code uses only the highest-ranked source that carries a policy key. A few keys are read from every admin source anyway, excluding HKCU: the sandbox locks, `allowManagedMcpServersOnly`, `deniedMcpServers`, `disableClaudeAiConnectors`, `false` values of `syncClaudeAiSkills` and `syncClaudeAiPlugins`, `forceRemoteSettingsRefresh`, the lowest `maxEffortLevel`, and `env`, which merges per variable. Set `"merge"` in the top source to compose all admin sources: lists union, locks take the strictest value, and allowlists such as `availableModels` come whole from the top source.
- **WSL** reads only `/etc/claude-code` unless `wslInheritsWindowsSettings: true` is set in HKLM or the Windows file. On Windows and WSL, an admin policy (HKLM or `managed-settings.json`) that is present but invalid or unreadable still keeps user-writable HKCU and WSL `/etc/claude-code` from applying.
- **Invalid values:** a mistyped value on a boolean lock key such as `disableClaudeAiConnectors` or `allowManagedPermissionRulesOnly` still applies the lock, and startup names the key. One invalid nested value in managed `permissions`, `autoMode`, `worktree` or `attribution` drops only that value; the rest of the block applies. An invalid `strictKnownMarketplaces` is enforced as an empty allowlist, `disableSideloadFlags` is treated as `true`, `syncClaudeAiPlugins` as `false`, and invalid individual entries in either marketplace list are stripped (v2.1.277+).
- **Surfaces:** managed settings reach the terminal, the IDE extensions, the desktop Code tab and Agent SDK sessions. Anthropic-hosted cloud sessions receive **only server-managed settings**, and Cowork sessions never fetch them; claude.ai itself checks the console's marketplace allowlist and blocklist when anyone adds a git marketplace on claude.ai or in Cowork. A developer's `--model` or `ANTHROPIC_MODEL` still picks a session model under a managed `model`, so deploy `availableModels` if you need a lock.

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
| MCP servers ([[mcp]]) | `allowedMcpServers`, `deniedMcpServers`, `allowManagedMcpServersOnly`, `managedMcpServers`, `managed-mcp.json`; `allowClaudeInChromeWithManagedMcp` lets `claude --chrome` run beside an exclusive `managed-mcp.json` |
| Plugin sources ([[plugins]]) | `strictKnownMarketplaces`, `blockedMarketplaces`, `disableSideloadFlags`, `disableCommandPluginSources`, `pluginSuggestionMarketplaces`, `pluginTrustMessage` |
| Customization only via plugins or managed | `strictPluginOnlyCustomization` (locking skills also stops claude.ai-synced skills) |
| claude.ai sync | `syncClaudeAiSkills`, `syncClaudeAiPlugins` set to `false` (a `[]` marketplace allowlist doesn't stop synced plugins) |
| Hooks | `allowManagedHooksOnly`, `allowedHttpHookUrls` |
| claude.ai skill and plugin sync | `syncClaudeAiSkills`, `syncClaudeAiPlugins` (each honors only `false`) |
| Login | `forceLoginMethod`, `forceLoginOrgUUID` (these block `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` and `apiKeyHelper` sessions) |
| Background agents | `disableAgentView`, or `processWrapper` for a corporate launcher |
| Models and effort | `availableModels`, `availableModelsMatch` (`"exact"` allows only the version an entry names), `deniedModels`, `enforceAvailableModels`, `maxEffortLevel`, `allowedProviders` (limits which API providers a machine may use) |
| Versions | `minimumVersion` (blocks downgrades), `requiredMinimumVersion`/`requiredMaximumVersion` (refuses to start outside the range) |
| Telemetry to Anthropic | `env` with `DISABLE_TELEMETRY` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` ([[data-and-privacy]]) |

Permission rules and sandboxing work at different layers. Denying WebFetch doesn't stop `curl` through an allowed Bash; only the sandbox's network allowlist does ([[sandboxing-and-security]]). On Enterprise plans that sign in through claude.ai or the Anthropic API, the admin console can also disable models, set a default model and cap effort server-side. Those controls don't reach cloud-provider sessions.

## Verify enforcement

Have a developer run `/status`. `Setting sources` shows `Enterprise managed settings` with the selected source: `(remote)`, `(plist)`, `(HKLM)`, `(file)`, `(drop-ins)`, `(HKCU)`, `(parent process)`, `(helper)`, or a list ending `, merged`. A `Skipped sources` line names any source that was found but overridden. If the line is missing, no source delivered a policy key. `claude doctor` lists dropped entries, and shows `Managed settings (remote)` (the fetch outcome) and `Organization policy` lines. Both `/status` and `claude doctor` name the source and key when an admin source sets `allowManagedMcpServersOnly` or `allowedMcpServers` and that value isn't the one in force. An unparseable managed file stops Claude Code from starting.

## Distribute and restrict plugins

Under `first-wins`, if server-managed settings deliver any policy key, plugin keys in MDM or a file on that machine are ignored. Marketplace authoring is on [[plugin-marketplaces]].

- **Require plugins:** managed `extraKnownMarketplaces` plus `enabledPlugins` (`"code-formatter@your-marketplace": true`) install them at the next session start; users can't disable them. `false` in managed `enabledPlugins` blocks a plugin at every scope and hides it. `claude-plugins-official` needs no marketplace entry when one of its plugins is enabled. `CLAUDE_CODE_SYNC_PLUGIN_INSTALL=1` makes `-p` runs wait for installs.
- **Per repository:** the same two keys in `.claude/settings.json`. Marketplaces register only after the contributor trusts the folder; plugins with external sources still need `claude plugin install <name>@<marketplace> --scope project`.
- **claude.ai:** **Organization settings > Plugins & skills** turns plugins on for members' accounts; they reach Claude Code as synced plugins and don't set any of these keys.
- **Containers and CI:** run `claude plugin marketplace add` and `claude plugin install` with `CLAUDE_CODE_PLUGIN_CACHE_DIR=/opt/claude-seed` at build time, then set `CLAUDE_CODE_PLUGIN_SEED_DIR=/opt/claude-seed` at runtime. Seeds are read-only and still need `enabledPlugins`.
- **Allowlist:** `strictKnownMarketplaces` (alias `allowedMarketplaces`) unset means no restriction, `[]` blocks every source including the official one, and a list admits only matching sources. Entries are `github` (with `owner/*` wildcards), `git`, `url`, `file`, `directory`, `hostPattern` and `pathPattern` regexes, and `{ "source": "skills-dir" }`, without which skills-directory plugins stop loading. The allowlist registers nothing and doesn't cover `--plugin-dir`.
- **Blocklist:** `blockedMarketplaces` is checked first and matches more loosely (canonicalized git URLs, `github` and `git` forms equivalent, no `ref` means all refs).
- **Enforcement:** both lists apply before any download and again at session start, so an installed plugin from a no-longer-allowed source stops loading. While either is active, a plugin whose marketplace can't be found doesn't load.
- **Other keys:** `disableSideloadFlags` rejects `--plugin-dir`, `--plugin-url`, `--agents`, the SDK `plugins` option, non-SDK `--mcp-config` and `CLAUDE_CODE_PLUGIN_DIRS`. `disableCommandPluginSources` blocks `command` sources and marketplace `headersHelper` commands (defaults to `allowManagedHooksOnly`). `pluginTrustMessage` appends text to the install trust warning. `CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL` in managed `env` stops auto-registering the official marketplace.
- **Updates:** a managed `autoUpdate` value on an `extraKnownMarketplaces` entry overrides the user's toggle. `DISABLE_AUTOUPDATER` in managed `env` stops plugin and Claude Code updates; add `FORCE_AUTOUPDATE_PLUGINS` to keep plugin updates.
- **Audit:** OTel `claude_code.plugin_installed` and `claude_code.plugin_loaded` events (third-party names redacted unless `OTEL_LOG_TOOL_DETAILS=1`), and on Enterprise the Analytics API's `GET /v1/organizations/analytics/plugins` for per-plugin install and invocation counts.

A common lockdown allowlists `anthropics/claude-plugins-official`, `your-org/*` and `skills-dir`, registers both in `extraKnownMarketplaces` (the official one self-registers only in interactive sessions, and never again on a machine that once blocked it), and sets `disableSideloadFlags: true`.

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

- **Where to set it:** project and local settings can't turn export on, set its endpoint or capture content, so put these variables in managed or user settings ([[environment-variables]]). A repository can still set an exporter to `none`. While `otelHeadersHelper` fails, nothing is exported and interactive sessions warn once.
- **Locking the collector:** a managed `OTEL_EXPORTER_OTLP_ENDPOINT`, protocol or headers value strips conflicting developer-set per-signal variables. Exporter selectors are not locked unless you set them in managed settings too.
- **Metrics:** `claude_code.session.count`, `lines_of_code.count`, `pull_request.count`, `commit.count`, `cost.usage` (USD), `token.usage`, `code_edit_tool.decision` and `active_time.total`, all prefixed `claude_code.`.
- **Events and spans:** `claude_code.user_prompt`, and `claude_code.managed_settings_resolved`, which reports the managed-settings sources in effect and the policy helper's state; `OTEL_LOG_MANAGED_SETTINGS=1` adds the redacted settings and their digests. Request events and spans carry an `effort` attribute. `hook_execution_complete` reports hook output sizes and how many oversized outputs were saved to a file.
- **Privacy defaults:** prompt text, assistant responses, tool arguments, tool content and raw API bodies are off until you set `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_ASSISTANT_RESPONSES`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_TOOL_CONTENT` or `OTEL_LOG_RAW_API_BODIES`. With OAuth, `user.email` is included, sent only to your collector. `OTEL_LOG_TOOL_DETAILS=1` also puts real agent, skill, plugin and MCP server names on cost and token metrics.
- **Tool content:** `OTEL_LOG_TOOL_CONTENT=1` adds a `tool.output` span event on `claude_code.tool` for successful Read and Bash calls, carrying file text or command output; Edit and Write record one only with `OTEL_LOG_TOOL_DETAILS=1` as well, and no other tool records one. Each attribute is cut at the 60 KB content limit. Under detailed beta tracing, `OTEL_LOG_USER_PROMPTS=1` also gates `new_context`, which carries tool results on the `claude_code.llm_request` span.
- **Raw bodies:** `OTEL_LOG_RAW_API_BODIES=file:<dir>` writes untruncated bodies to that directory and appends one content-free line per successful response to `<dir>/index.jsonl`, linking each response file to its request file and to the transcript message it became. Pair the two events by `request_body_id`.
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

Invest in CLAUDE.md files, offer a one-click install, start people on codebase Q&A and small planned fixes, pin model versions on cloud providers, and check a central `.mcp.json` into repositories. For onboarding problems: `/logout` then `/login` switches accounts; a missing enterprise auth option needs `claude update` and a terminal restart; "You haven't been added to your organization yet" means the seat lacks Claude Code access.
