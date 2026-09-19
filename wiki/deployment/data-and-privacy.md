---
title: Data Usage, Retention and Privacy
type: reference
tldr: "Training, retention, ZDR, telemetry opt-outs"
sources:
  - raw/docs/official/data-usage.md
  - raw/docs/official/zero-data-retention.md
  - raw/docs/official/legal-and-compliance.md
  - raw/docs/official/managed-settings.md
  - raw/docs/official/third-party-integrations.md
  - raw/docs/official/admin-setup.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
related: ["[[enterprise-admin]]", "[[sandboxing-and-security]]", "[[cloud-providers]]", "[[llm-gateways]]", "[[sessions-and-checkpoints]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [zero-data-retention, zdr, data-retention, disable-telemetry, claude-code-privacy]
---

# Data Usage, Retention and Privacy

This page covers what Anthropic does with Claude Code data: training, how long data is kept, Zero Data Retention (ZDR), and the telemetry Claude Code sends plus how to turn it off. For the security model and sandboxing, see [[sandboxing-and-security]]. For the OpenTelemetry data you export to *your own* collector, see [[enterprise-admin]].

## Training

| Account | Policy |
|---|---|
| Consumer (Free, Pro, Max) | Your choice. When the model-improvement setting is on, data is used to train new models, including Claude Code usage |
| Commercial (Team, Enterprise, API, 3rd-party platforms, Claude Gov) | Anthropic does not train generative models on code or prompts sent to Claude Code, unless the customer opts in, for example through the Development Partner Program (first-party API only, not Bedrock or Agent Platform) |

Session quality survey responses, including any transcript you choose to share, don't affect training preferences and can't be used for training.

## Retention

| Data | Retention |
|---|---|
| Consumer, model improvement allowed | 5 years |
| Consumer, model improvement not allowed | 30 days (change at claude.ai/settings/data-privacy-controls) |
| Commercial standard | 30 days |
| Commercial with ZDR | Not stored after the response returns (see below) |
| `/feedback`, `/bug` and `/share` transcripts | 5 years |
| Transcript shared from the session survey follow-up | Up to 6 months |
| ZDR sessions flagged for a policy violation | Inputs and outputs up to 2 years |
| Local transcripts in `~/.claude/projects/` (plaintext) | 30 days by default; set `cleanupPeriodDays`. Desktop and Cowork transcripts are exempt by default; `desktopSessionCleanupPeriodDays` sets their limit |

You can delete an individual cloud session, which permanently removes its event data ([[claude-code-on-the-web]]). Local session storage is described on [[sessions-and-checkpoints]].

## Data flow and encryption

Claude Code runs locally and sends prompts and model outputs over TLS 1.2+. Encryption at rest depends on the provider:

| Provider | At rest |
|---|---|
| Anthropic API | AES-256 disk encryption; ZDR for no server-side persistence |
| Amazon Bedrock | AES-256 with AWS-managed keys; customer-managed keys via AWS KMS |
| Google Cloud's Agent Platform | Google-managed keys; CMEK available |
| Microsoft Foundry | Hosted on Azure: prompts and completions stay in Azure, and only usage metadata and safety-flagged content leave for Anthropic. Hosted on Anthropic: AES-256 on Anthropic infrastructure |

In Anthropic-hosted cloud sessions:

- The repository is cloned into an isolated VM.
- GitHub credentials stay behind a secure proxy and never enter the sandbox.
- All outbound traffic goes through an audit-logging security proxy.
- Session data follows your account's retention policy.

With Remote Control, execution stays local, but the transcript is stored on Anthropic servers while you're connected. When CMEK is in use and traffic routes through an LLM gateway or custom `ANTHROPIC_BASE_URL`, CMEK doesn't cover Claude Code's operational telemetry. Deliver `DISABLE_TELEMETRY` through managed settings to turn that telemetry off ([[llm-gateways]]).

## Telemetry and opt-outs

| Stream | What it contains | Opt out |
|---|---|---|
| Metrics | Latency, reliability, usage patterns; never code, prompts or file paths. Goes to Anthropic and third-party logging | `DISABLE_TELEMETRY=1` |
| Error reports | Internal errors and stack traces, with secrets, paths and emails redacted, sent to a third-party tracker. On only for Pro/Max sign-ins connecting directly to the Claude API without a ZDR or HIPAA agreement | `DISABLE_ERROR_REPORTING=1` |
| `/feedback` reports | A copy of conversation history including code, stored in Google Cloud Storage; optionally a public GitHub issue | `DISABLE_FEEDBACK_COMMAND=1` |
| Session quality surveys | The rating only. Transcripts upload only if you answer **Yes** to the follow-up | `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1`, or `feedbackSurveyRate` (0–1) |
| WebFetch domain check | The hostname only (not path or content), sent to `api.anthropic.com`; cached 5 minutes | `skipWebFetchPreflight: true` in settings |
| Official marketplace auto-install | — | `CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL` |

`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` turns off metrics, error reports, `/feedback` and surveys in one step. It does not cover the WebFetch check or marketplace auto-install. `DISABLE_TELEMETRY`, `DO_NOT_TRACK` and `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` each also disable the survey. `DISABLE_TELEMETRY` and `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` also stop feature-flag fetching, which makes Remote Control, default auto mode and other flag-gated features unavailable; `DISABLE_ERROR_REPORTING` doesn't. If you collect survey ratings through your own OTel collector, `CLAUDE_CODE_ENABLE_FEEDBACK_SURVEY_FOR_OTEL=1` re-enables the survey and sends ratings only there.

`/bug` and `/feedback` reports carry only the model-behavior parameters of the last API request — model, system prompt and tools — and omit request metadata and `CLAUDE_CODE_EXTRA_BODY` fields.

### Defaults by provider

| Service | Claude API | Agent Platform / Bedrock / Foundry / Claude Platform on AWS |
|---|---|---|
| Metrics | On | Off |
| Error reports | On for Pro/Max sign-ins, otherwise off | Off |
| `/feedback` reports | On | Off; written to `~/.claude/feedback-bundles/` instead |
| Session quality surveys | On | On |
| WebFetch domain check | On | On |

- **Claude apps gateway:** a signed-in session disables usage analytics, error reporting and survey ratings to Anthropic, with no setting to re-enable them. The survey's Yes answer writes a local bundle instead of uploading.
- **Host-managed providers:** when a host platform sets `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST`, metrics default to on for the cloud providers.

### Turn telemetry off for everyone

Deliver the variable through managed settings rather than relying on shells ([[enterprise-admin]]):

```json
{ "env": { "DISABLE_TELEMETRY": "1" } }
```

A value of `1` applies without an approval dialog. It also stops the usage data that feeds your organization's analytics dashboard, and disables feature-flag fetching for those developers.

## Zero Data Retention

With ZDR enabled, Anthropic processes Claude Code prompts and responses in real time and does not store them after the response returns, except where law or misuse prevention requires it.

- **Availability:** qualified Claude for Enterprise accounts only. ZDR isn't part of the standard plan and can't be turned on in admin settings; request it through sales or your account team. It is enabled **per organization**, so new organizations need their own enablement, and every enablement is audit-logged. Pay-as-you-go API ZDR customers can move to Enterprise and keep ZDR.
- **Cloud providers:** ZDR on Enterprise covers only Anthropic's direct platform. On Bedrock, Agent Platform and Foundry, the provider's own agreement governs retention ([[cloud-providers]]).
- **Coverage:** Claude Code inference for requests that authenticate into the ZDR organization. Personal accounts and keys from other organizations aren't covered; deploy `forceLoginMethod` and `forceLoginOrgUUID` to pin logins to the ZDR organization.
- **Not covered:** claude.ai chat, Cowork, Claude Code Analytics metadata (emails, usage stats), user and seat management data, and third-party tools or MCP servers.
- **Disabled under ZDR** (blocked in the backend): cloud sessions, including those started from the desktop app, because they need server-side storage of prompts and completions; Claude Tag; Artifacts; feedback submission (`/feedback`, `/bug`, `/share`); and Remote Control. Contribution metrics are also unavailable, so the analytics dashboard shows usage only.
- **Models:** Claude Fable 5.1 and Fable 5 are Covered Models that require data retention by default. Where a ZDR organization can't use them, they are hidden or disabled in `/model`, and the `best` alias resolves to Opus.

### ZDR admin features on Enterprise

- Per-user cost controls
- The analytics dashboard
- Server-managed settings
- Audit logs

## Compliance

- **BAA:** a Business Associate Agreement extends to a customer's API traffic through Claude Code only when ZDR is enabled for that organization.
- **Terms:** Commercial Terms govern Team, Enterprise and API users; Consumer Terms govern Free, Pro and Max users. Existing commercial agreements apply whether you use the Claude API directly or through Bedrock or Agent Platform.
- **Certifications and API logging controls:** see the Anthropic Trust Center.
