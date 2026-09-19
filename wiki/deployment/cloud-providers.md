---
title: Cloud Providers (Bedrock, Agent Platform, Foundry, Claude Platform on AWS)
type: how-to
tldr: "Run Claude Code on AWS, GCP or Azure"
sources:
  - raw/docs/official/third-party-integrations.md
  - raw/docs/official/feature-availability.md
  - raw/docs/official/amazon-bedrock.md
  - raw/docs/official/google-vertex-ai.md
  - raw/docs/official/microsoft-foundry.md
  - raw/docs/official/claude-platform-on-aws.md
  - raw/docs/official/admin-setup.md
  - raw/docs/official/data-usage.md
related: ["[[llm-gateways]]", "[[enterprise-admin]]", "[[models-and-effort]]", "[[data-and-privacy]]", "[[settings]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [bedrock-setup, vertex-ai-setup, microsoft-foundry-setup, claude-platform-on-aws, third-party-providers]
valid_until: 2027-03-15
---

# Cloud Providers

Claude Code can run its model traffic through a cloud provider instead of a claude.ai or Console login. Pick this when you want to inherit existing AWS, GCP or Azure compliance controls, IAM and billing. For most organizations the docs still recommend Claude for Teams or Enterprise, which needs no infrastructure and covers both Claude Code and Claude on the web in one subscription ([[enterprise-admin]]). To put a proxy or gateway in front of a provider, see [[llm-gateways]].

## Choose a provider

| | Amazon Bedrock | Claude Platform on AWS | Google Cloud's Agent Platform | Microsoft Foundry |
|---|---|---|---|---|
| Enable with | `CLAUDE_CODE_USE_BEDROCK=1` (Mantle: `CLAUDE_CODE_USE_MANTLE=1`) | `CLAUDE_CODE_USE_ANTHROPIC_AWS=1` | `CLAUDE_CODE_USE_VERTEX=1` | `CLAUDE_CODE_USE_FOUNDRY=1` |
| Who runs inference | AWS | Anthropic's API, with AWS auth and AWS Marketplace billing | Google | Depends on the deployment's hosting option |
| Auth | AWS credentials or Bedrock API key | SigV4 AWS credentials or workspace API key | GCP credentials | API key, Entra ID or bearer token |
| Cost tracking | AWS Cost Explorer | AWS Cost Explorer | GCP Billing | Azure Cost Management |
| Enterprise controls | IAM policies, CloudTrail | IAM policies, CloudTrail | IAM roles, Cloud Audit Logs | RBAC policies, Azure Monitor |
| Setup wizard | Yes (`/setup-bedrock`) | No | Yes (`/setup-vertex`) | No |

Prompt caching is on by default on all four. The Agent Platform variable names keep the `VERTEX` spelling, and the login menu labels it "Google Vertex AI". If `CLAUDE_CODE_USE_BEDROCK` or `CLAUDE_CODE_USE_FOUNDRY` is set, it takes precedence over Claude Platform on AWS. On Bedrock, Agent Platform and Foundry, `/logout` is unavailable because the cloud credentials handle authentication.

> [!contradiction]
> `feature-availability.md` labels Microsoft Foundry "Anthropic-operated". `microsoft-foundry.md` and `data-usage.md` say each deployment's hosting option decides whether inference runs on Azure or on Anthropic infrastructure. For Hosted on Azure deployments, prompts and completions stay within Azure.

## Amazon Bedrock

**Wizard path:** in the Bedrock console, open the Model catalog, pick an Anthropic model and submit the use-case form (once per AWS account; AWS Organizations can submit it from the management account with `PutUseCaseForModelAccess`). Then run `claude`, choose **3rd-party platform → Amazon Bedrock**. The wizard writes the result to the `env` block of `~/.claude/settings.json`, or to `$CLAUDE_CONFIG_DIR/settings.json` if that variable is set.

**Manual path** (CI, scripted rollouts):

```bash
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION=us-east-1          # optional if your profile sets a region
# export ANTHROPIC_BEDROCK_BASE_URL=https://bedrock-runtime.us-east-1.amazonaws.com
```

- **Credentials** come from the AWS SDK default chain: `aws configure`, `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_SESSION_TOKEN`, `aws sso login` plus `AWS_PROFILE`, `aws login`, or a Bedrock API key in `AWS_BEARER_TOKEN_BEDROCK`. Resolved credentials are cached until five minutes before expiry, or for one hour if they carry no expiry. `CLAUDE_CODE_SKIP_AWS_CRED_CACHE=1` disables the cache, and `CLAUDE_CODE_AWS_CHAIN_RESOLVE_TIMEOUT_MS` raises the 60-second resolve timeout.
- **Region order:** `AWS_REGION` → `AWS_DEFAULT_REGION` → the active profile's `region` → `us-east-1`.
- **Credential refresh settings:** `awsAuthRefresh` runs only when credentials are expired, for example `aws sso login --profile myprofile`, and its output is shown. `awsCredentialExport` runs at every session start and must print JSON `Credentials` (`AccessKeyId`, `SecretAccessKey`, `SessionToken`, optional `Expiration`). If VPNs or TLS inspection make SSO browser tabs spawn in a loop, remove `awsAuthRefresh` and run `aws sso login` by hand.
- **IAM:** allow `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, `bedrock:ListInferenceProfiles` and `bedrock:GetInferenceProfile` on inference-profile, application-inference-profile and foundation-model resources, plus `aws-marketplace:ViewSubscriptions`/`Subscribe` conditioned on `aws:CalledViaLast = bedrock.amazonaws.com`.
- **Inference profile prefixes:** built-in defaults resolve to cross-region profile IDs by region: `us-gov-*`→`us-gov.`, `us-*`→`us.`, `eu-*`→`eu.`, `ap-*`→`apac.`, all others→`global.`. `ANTHROPIC_BEDROCK_REGION_PREFIX` (`us`, `eu`, `apac`, `jp`, `au`, `global`) changes the preferred prefix without pinning. GovCloud always uses `us-gov.`.
- **Several versions per family:** map Anthropic IDs to application inference profile ARNs with the `modelOverrides` setting. They then show in `/model` and apply to `--model` and `ANTHROPIC_MODEL`.
- **Service tiers:** `ANTHROPIC_BEDROCK_SERVICE_TIER` = `default`, `flex` or `priority`.
- **Guardrails:** send `X-Amzn-Bedrock-GuardrailIdentifier` and `X-Amzn-Bedrock-GuardrailVersion` through `ANTHROPIC_CUSTOM_HEADERS` in the settings `env` block.
- **Mantle endpoint** serves Claude through the Anthropic API shape. It uses IDs such as `anthropic.claude-haiku-4-5` (for example `claude --model anthropic.claude-haiku-4-5`) and has its own model lineup. With both `CLAUDE_CODE_USE_BEDROCK` and `CLAUDE_CODE_USE_MANTLE` set, Mantle-format IDs go to Mantle and all other IDs go to the Invoke API. List Mantle IDs in `availableModels` to show them in the picker. Override the URL with `ANTHROPIC_BEDROCK_MANTLE_BASE_URL`.
- Claude Code uses the Bedrock Invoke API, not Converse. WebSearch is unavailable. "on-demand throughput isn't supported" means you should use an inference profile ID.

## Claude Platform on AWS

This is Anthropic's own API, with the same models and API features as the Claude API, reached with AWS authentication and billed through AWS Marketplace. Subscribing creates a **separate Anthropic organization**, so Console keys from an existing organization don't work with it.

```bash
export CLAUDE_CODE_USE_ANTHROPIC_AWS=1
export ANTHROPIC_AWS_WORKSPACE_ID=wrkspc_01ABCDEFGHIJKLMN   # required
export AWS_REGION=us-east-1
# or: export ANTHROPIC_AWS_API_KEY=sk-ant-...   (takes precedence over SigV4)
```

The base URL is `https://aws-external-anthropic.{region}.api.aws`; override it with `ANTHROPIC_AWS_BASE_URL`. `awsAuthRefresh` works here too. `/login` → **Claude Platform on AWS · refresh credentials** re-runs it without a restart. A `403`/`AccessDenied` response points at missing `aws-external-anthropic` IAM actions or a stale API key.

## Google Cloud's Agent Platform

```bash
gcloud config set project YOUR-PROJECT-ID
gcloud services enable aiplatform.googleapis.com
# request Claude model access in Model Garden (may take 24-48 hours)

export CLAUDE_CODE_USE_VERTEX=1
export CLOUD_ML_REGION=global            # or eu / us / us-east5
export ANTHROPIC_VERTEX_PROJECT_ID=YOUR-PROJECT-ID
export VERTEX_REGION_CLAUDE_HAIKU_4_5=us-east5   # per-model override when a model lacks global
```

- Credentials use the standard Application Default Credentials chain, including X.509 Workload Identity Federation through `GOOGLE_APPLICATION_CREDENTIALS`. Requests go to the project in `ANTHROPIC_VERTEX_PROJECT_ID` even if `GCLOUD_PROJECT`, `GOOGLE_CLOUD_PROJECT` or the credential file names another project.
- The `gcpAuthRefresh` setting (for example `gcloud auth application-default login`) runs when credentials are expired and times out after three minutes.
- A malformed `VERTEX_REGION_CLAUDE_*` value falls back to `CLOUD_ML_REGION`, and a malformed `CLOUD_ML_REGION` falls back to `us-east5`.
- IAM: `roles/aiplatform.user` (it includes `aiplatform.endpoints.predict`).
- MCP tool search is on by default for Claude 4.5-generation models and later. Older models load tool definitions upfront.
- For "model not found" 404s, confirm the model is enabled in Model Garden and offered at your location. Some models exist only on `global` or multi-region endpoints. For 429s, check that both the primary and the small/fast model exist in your region, or use `global`.

## Microsoft Foundry

Create a resource in the Foundry portal and one deployment each for Opus, Sonnet and Haiku, choosing a specific model version rather than auto-update. There is no wizard; environment variables are the only configuration path.

```bash
export CLAUDE_CODE_USE_FOUNDRY=1
export ANTHROPIC_FOUNDRY_RESOURCE={resource}
# or: export ANTHROPIC_FOUNDRY_BASE_URL=https://{resource}.services.ai.azure.com/anthropic
export ANTHROPIC_FOUNDRY_API_KEY=your-azure-api-key   # option A
# option B: leave both key vars unset and use the Azure default credential chain (az login)
# option C: export ANTHROPIC_FOUNDRY_AUTH_TOKEN=...   (wins over A and B)
```

RBAC: the `Azure AI User` or `Cognitive Services User` roles, or a custom role with the `Microsoft.CognitiveServices/accounts/providers/*` data action. Repeated connection errors on the first prompt usually mean `ANTHROPIC_FOUNDRY_RESOURCE` still holds a placeholder.

## Pin model versions

Pin models before rolling out to a team using `ANTHROPIC_DEFAULT_FABLE_MODEL`, `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL` and `ANTHROPIC_DEFAULT_HAIKU_MODEL`. Without pins, aliases resolve to Claude Code's built-in default for that provider, which can lag the newest release and may not be enabled in your account.

| Provider | Unpinned `opus` | Unpinned `sonnet` | Background (small/fast) tasks |
|---|---|---|---|
| Bedrock | Opus 5 (primary model default) | Sonnet 4.5 | Default Sonnet model |
| Agent Platform | Opus 5 (`claude-opus-5` primary) | Sonnet 4.5 | Default Sonnet model |
| Foundry | Opus 4.6 | Your deployment name | Primary model |
| Claude Platform on AWS | Opus 5 | Claude API IDs | — |

```bash
# Bedrock example (cross-region inference profile IDs)
export ANTHROPIC_DEFAULT_OPUS_MODEL='us.anthropic.claude-opus-4-8'
export ANTHROPIC_DEFAULT_SONNET_MODEL='us.anthropic.claude-sonnet-4-6'
export ANTHROPIC_DEFAULT_HAIKU_MODEL='us.anthropic.claude-haiku-4-5-20251001-v1:0'
```

- The unpinned primary model on Bedrock and Agent Platform is an Opus model, billed at Opus rates. To keep Sonnet 4.5 as primary, set `ANTHROPIC_MODEL` to its full ID.
- Setting `ANTHROPIC_DEFAULT_HAIKU_MODEL` moves background tasks such as session titles onto Haiku. Choosing a primary model with `--model`, `ANTHROPIC_MODEL` or `model` moves them onto that model.
- **Startup model checks** run on Bedrock and Agent Platform. An older pin triggers a prompt to update it. A missing default falls back, for that session only, to earlier versions and then to Sonnet. Foundry has no check, so requests simply fail.
- **1M context:** Sonnet 5 always runs with 1M. For Opus 4.6+ and Sonnet 4.6, append `[1m]` to the pinned ID.

Aliases, effort and fallback behaviour are covered on [[models-and-effort]].

## Feature differences

Everything local works on every provider: the CLI, Agent SDK, IDE extensions, subagents, hooks, skills, plugins, MCP, checkpoints, sandboxing, Workflows, OpenTelemetry and managed-settings files. Features that need a claude.ai subscription do not work on any of these providers, including cloud sessions ([[claude-code-on-the-web]]), Desktop (except through Claude Desktop on 3P), routines, Code Review, Remote Control, Chrome and Artifacts.

| Feature | Bedrock | Platform on AWS | Agent Platform | Foundry |
|---|---|---|---|---|
| Web search | ✗ | ✓ | Claude 4+ models | Hosted-on-Anthropic deployments |
| Fast mode, Advisor, Channels | ✗ | ✗ | ✗ | ✗ |
| Auto mode | Sonnet 5, Opus 4.7+, Fable | ✓ | Sonnet 5, Opus 4.7+, Fable | Sonnet 5, Opus 4.7+, Fable |
| GitHub Actions | ✓ | ✗ | ✓ | ✓ |
| GitLab CI/CD | ✓ | ✓ | ✓ | ✗ |
| Analytics dashboard, server-managed settings | ✗ | ✗ | ✗ | ✗ |
| Zero Data Retention | Per AWS agreement | Qualified accounts | Per Google Cloud agreement | Per Azure agreement |

`/design-sync` and `/import` are unavailable on all four. Organization model and effort controls from the claude.ai admin console don't reach these sessions, so use managed `availableModels`, `model` and `maxEffortLevel` instead ([[enterprise-admin]]). As alternatives, use `/loop` instead of `/schedule`, and GitHub Actions or GitLab CI/CD for cloud runs ([[ci-cd-and-code-review]]). Error reporting and telemetry to Anthropic are off by default on these providers ([[data-and-privacy]]).

## Verify

Run `/status`. The `API provider` line shows `Amazon Bedrock`, `Amazon Bedrock (Mantle)`, `Claude Platform on AWS`, `Google Vertex AI` or `Microsoft Foundry`, along with the region, project, workspace or resource. If that line is missing, the variables never reached the process. Export them in the launching shell, or put them in the settings `env` block ([[settings]]).
