---
title: Environment Variables
type: reference
tldr: "Claude Code env vars grouped by purpose"
sources:
  - raw/docs/official/env-vars.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
  - raw/docs/changelog-2.1.275-to-2.1.278.md
related: ["[[settings]]", "[[cloud-providers]]", "[[llm-gateways]]", "[[enterprise-admin]]", "[[cli-reference]]", "[[troubleshooting]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [env-vars, claude-code-env, environment-variable-list, anthropic-env-vars]
---

# Environment Variables

Variables control model selection, authentication, routing, limits and feature toggles; most also have a settings key ([[settings]]), a CLI flag ([[cli-reference]]) or an in-session command. Rare display-name, region and cache-tuning variants are summarized by pattern.

## Setting and precedence

- **Shell:** `export API_TIMEOUT_MS="1200000"` before `claude`; read at startup.
- **Settings file:** under `"env"` in `~/.claude/settings.json` (user), `.claude/settings.json` (project, checked in), `.claude/settings.local.json` (user, this project) or managed settings (organization). A running session applies saved changes except startup-only features such as OpenTelemetry; removals take effect next launch.
- A settings `env` value beats the shell; between files normal precedence applies, so managed settings win.
- Settings can't unset a variable, but an empty string counts as unset for provider selection: `"CLAUDE_CODE_USE_VERTEX": ""`.
- Flags and commands vary per feature: `--model` and `/model` override `ANTHROPIC_MODEL`, while `CLAUDE_CODE_EFFORT_LEVEL` overrides `--effort` and `/effort`.
- `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_TMPDIR`, `OTEL_LOG_RAW_API_BODIES`, `BETA_TRACING_ENDPOINT` and `ENABLE_BETA_TRACING_DETAILED` are ignored in project and local settings. `CLAUDE_CODE_PROJECT_DIR_NAME` is read only from the launch environment, and `CLAUDE_CODE_RESTRICTED` is ignored in any `env` block.
- **Values:** numeric variables accept `2e3` and `64_000` unless marked plain-digits only; on/off variables take `1`/`true` and `0`/`false`. These turn on when set to *anything*, including `0`, so unset them instead: `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `DISABLE_TELEMETRY`, `DISABLE_ERROR_REPORTING`, `CLAUDE_CODE_TMUX_TRUECOLOR`, `FALLBACK_FOR_ALL_PRIMARY_MODELS`, `IS_DEMO`. `FORCE_HYPERLINK` is numeric: only `0` disables it.

## Authentication

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | API key (`X-Api-Key`). Overrides a subscription login; always used in `-p`, approved once interactively. `unset ANTHROPIC_API_KEY` to use the subscription |
| `ANTHROPIC_AUTH_TOKEN` | Custom `Authorization: Bearer` value |
| `CLAUDE_CODE_OAUTH_TOKEN` | claude.ai access token for SDK and automation; from `claude setup-token` |
| `CLAUDE_CODE_OAUTH_REFRESH_TOKEN`, `CLAUDE_CODE_OAUTH_SCOPES` | Let `claude auth login` exchange a refresh token without a browser |
| `ANTHROPIC_PROFILE`; `ANTHROPIC_FEDERATION_RULE_ID`, `ANTHROPIC_ORGANIZATION_ID`, `ANTHROPIC_WORKSPACE_ID` | Profile to authenticate with; Workload Identity Federation |
| `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` | Refresh interval for `apiKeyHelper` credentials |

## Providers, endpoints, gateways

| Variable | Purpose |
|---|---|
| `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, `CLAUDE_CODE_USE_FOUNDRY`, `CLAUDE_CODE_USE_ANTHROPIC_AWS`, `CLAUDE_CODE_USE_MANTLE` | Select Amazon Bedrock, Google Cloud's Agent Platform, Microsoft Foundry, Claude Platform on AWS or the Bedrock Mantle endpoint |
| `ANTHROPIC_BASE_URL` | Route through a proxy or gateway; a non-first-party host disables MCP tool search by default and disables Remote Control |
| `ANTHROPIC_BEDROCK_BASE_URL`, `ANTHROPIC_BEDROCK_MANTLE_BASE_URL`, `ANTHROPIC_VERTEX_BASE_URL`, `ANTHROPIC_FOUNDRY_BASE_URL`, `ANTHROPIC_AWS_BASE_URL` | Per-provider endpoint overrides |
| `AWS_BEARER_TOKEN_BEDROCK`, `ANTHROPIC_FOUNDRY_API_KEY`, `ANTHROPIC_FOUNDRY_AUTH_TOKEN`, `ANTHROPIC_FOUNDRY_RESOURCE`, `ANTHROPIC_VERTEX_PROJECT_ID`, `ANTHROPIC_AWS_API_KEY`, `ANTHROPIC_AWS_WORKSPACE_ID` | Provider credentials and identifiers |
| `ANTHROPIC_BEDROCK_REGION_PREFIX`, `ANTHROPIC_BEDROCK_SERVICE_TIER` | Bedrock inference-profile prefix; service tier (`default`, `flex`, `priority`) |
| `VERTEX_REGION_CLAUDE_5_OPUS` and other `VERTEX_REGION_*` | Per-model region overrides on Agent Platform |
| `CLAUDE_CODE_SKIP_BEDROCK_AUTH`, `CLAUDE_CODE_SKIP_VERTEX_AUTH`, `CLAUDE_CODE_SKIP_FOUNDRY_AUTH`, `CLAUDE_CODE_SKIP_MANTLE_AUTH`, `CLAUDE_CODE_SKIP_ANTHROPIC_AWS_AUTH` | Skip client-side provider auth when a gateway signs requests |
| `ANTHROPIC_BETAS`, `ANTHROPIC_CUSTOM_HEADERS`, `CLAUDE_CODE_EXTRA_BODY` | Extra beta headers, `Name: Value` headers, JSON merged into request bodies |
| `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` | Strip beta headers and beta schema fields when a gateway rejects them (turns MCP tool search off) |
| `DISABLE_INTERLEAVED_THINKING`, `CLAUDE_CODE_DISABLE_THINKING` | For gateways that reject interleaved thinking or the `thinking` parameter |
| `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY`, `CLAUDE_CODE_GATEWAY_MODEL_DISCOVERY_TIMEOUT_MS` | Fill `/model` from the gateway's `/v1/models`; discovery timeout (3000) |
| `CLAUDE_CODE_MAX_CONTEXT_TOKENS`, `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT`, `CLAUDE_CODE_ALWAYS_ENABLE_EFFORT` | For gateway or custom model IDs Claude Code doesn't recognize |
| `CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST` | Set by embedding hosts; settings can't override their provider routing |
| `CLAUDE_CODE_GATEWAY_HINT_HEADERS`, `CLAUDE_GATEWAY_DRAIN_TIMEOUT_MS`, `CLAUDE_GATEWAY_PROXY_IS_EGRESS_BOUNDARY` | `1` sends the gateway routing-hint request headers; Claude apps gateway drain window on `SIGTERM`; hostname-only egress through a forward proxy |

Setup: [[cloud-providers]], [[llm-gateways]].

## Network, timeouts, retries

| Variable | Purpose |
|---|---|
| `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY`, `CLAUDE_CODE_PROXY_RESOLVES_HOSTS` | Proxy settings |
| `CLAUDE_CODE_CERT_STORE`, `CLAUDE_CODE_CLIENT_CERT`, `CLAUDE_CODE_CLIENT_KEY`, `CLAUDE_CODE_CLIENT_KEY_PASSPHRASE` | CA sources, default `bundled,system`; then mTLS cert, key, passphrase |
| `API_TIMEOUT_MS`; `CLAUDE_STREAM_IDLE_TIMEOUT_MS`, `CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS`, `CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS`, `API_FORCE_IDLE_TIMEOUT` | Per-request timeout, default 600000 (10 min); streaming stall timers, where an explicit `CLAUDE_STREAM_IDLE_TIMEOUT_MS` minimum is 300000 |
| `CLAUDE_ENABLE_STREAM_WATCHDOG`, `CLAUDE_ENABLE_BYTE_WATCHDOG` | Force the stream watchdogs on (`1`) or off (`0`) |
| `CLAUDE_CODE_MAX_RETRIES`, `CLAUDE_CODE_RETRY_WATCHDOG` | Retry count, default 10; unattended runs retry `429`/`529` capacity errors indefinitely and other transient errors up to 300 times |
| `CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK` | Disable non-streaming fallback when a proxy duplicates tool execution |

## Models, effort, thinking

| Variable | Purpose |
|---|---|
| `ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_MODEL` | Model to use (read before the `model` setting); model new sessions start on |
| `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, `ANTHROPIC_DEFAULT_FABLE_MODEL` | What each alias resolves to; Haiku also runs background functionality. Each has `_NAME`, `_DESCRIPTION` and `_SUPPORTED_CAPABILITIES` variants for the picker |
| `ANTHROPIC_CUSTOM_MODEL_OPTION` | Add a custom `/model` entry (with `_NAME`, `_DESCRIPTION`, `_SUPPORTED_CAPABILITIES`) |
| `CLAUDE_CODE_SUBAGENT_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` | Default model for subagents, teammates and workflow agents; `_FORCE=1` imposes it |
| `CLAUDE_CODE_EFFORT_LEVEL` | `low` to `max` or `auto`; beats `--effort`, `/effort` and settings, subject to `maxEffortLevel` |
| `MAX_THINKING_TOKENS`, `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING` | Fixed thinking budget (`0` disables thinking on the Anthropic API except on Fable models); use that fixed budget on Opus 4.6 and Sonnet 4.6 |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS`, `CLAUDE_CODE_DISABLE_1M_CONTEXT` | Max output tokens, where raising it shrinks usable context before compaction; hold sessions to a 200K window |
| `CLAUDE_CODE_DISABLE_FAST_MODE`, `CLAUDE_CODE_SKIP_FAST_MODE_NETWORK_ERRORS`, `CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK` | Fast mode off, or availability-check workarounds behind proxies |
| `CLAUDE_CODE_DISABLE_ADVISOR_TOOL`, `FALLBACK_FOR_ALL_PRIMARY_MODELS` | Disable the advisor tool, leaving `--advisor` accepted but ignored; stop retrying repeated overloads on every model when no fallback is configured |

`ANTHROPIC_SMALL_FAST_MODEL` is deprecated; use `ANTHROPIC_DEFAULT_HAIKU_MODEL`. See [[models-and-effort]].

## Context, compaction, caching, memory

| Variable | Purpose |
|---|---|
| `DISABLE_AUTO_COMPACT`, `DISABLE_COMPACT` | Turn off auto-compaction (`/compact` still works), or all compaction |
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | Auto-compact window, plain integer 100000–1000000; beats `/autocompact` |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Compact earlier, as a percentage (can't raise the threshold) |
| `DISABLE_PROMPT_CACHING` | Disable caching for all models; per-family variants end in `_OPUS`, `_SONNET`, `_HAIKU`, `_FABLE` |
| `ENABLE_PROMPT_CACHING_1H`, `CLAUDE_CODE_PROMPT_CACHE_TTL`, `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL`, `FORCE_PROMPT_CACHING_5M` | Cache TTL choice (`5m` or `1h`); `FORCE_PROMPT_CACHING_5M` wins |
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY`, `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` | Skip CLAUDE.md files; toggle auto memory; load memory files from `--add-dir` directories |
| `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS`, `CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT` | Drop built-in git instructions; shorter system prompt |
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS`, `CLAUDE_CODE_DISABLE_ATTACHMENTS` | Larger file reads; send `@` mentions as plain text |

## Tools and shell

| Variable | Purpose |
|---|---|
| `BASH_DEFAULT_TIMEOUT_MS`, `BASH_MAX_TIMEOUT_MS`, `BASH_MAX_OUTPUT_LENGTH`, `CLAUDE_CODE_BASH_EDIT_DIFF` | Bash timeout default 120000, ceiling 600000; output read back into a result, default 30000, max 150000; diff of a command's file changes ([[hooks]]) |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR`, `CLAUDE_ENV_FILE` | Return to the project directory after each command; script sourced before each Bash command (virtualenv, conda) |
| `CLAUDE_CODE_SHELL`, `CLAUDE_CODE_SHELL_PREFIX` | Shell binary (`bash` or `zsh`); wrapper command for auditing |
| `CLAUDE_CODE_TOOL_MEMORY_LIMIT`, `CLAUDE_CODE_TOOL_MEMORY_CGROUP_EXCLUDE` | Linux/WSL memory cap for tool commands, e.g. `4G` |
| `CLAUDE_CODE_USE_POWERSHELL_TOOL`, `CLAUDE_CODE_POWERSHELL_RESPECT_EXECUTION_POLICY`, `CLAUDE_CODE_GIT_BASH_PATH`, `CLAUDE_CODE_DISABLE_WINDOWS_SHELL_LAUNCHER` | PowerShell tool and Windows shell setup |
| `CLAUDE_CODE_GLOB_HIDDEN`, `CLAUDE_CODE_GLOB_NO_IGNORE`, `CLAUDE_CODE_GLOB_TIMEOUT_SECONDS` | Glob dotfiles, `.gitignore`, timeout |
| `USE_BUILTIN_RIPGREP`, `CLAUDE_CODE_USE_NATIVE_FILE_SEARCH` | `0` uses system `rg`; Node file APIs for discovery |
| `CLAUDE_CODE_WEBFETCH_CACHE_TTL_MS`, `CLAUDE_CODE_WEBFETCH_DEADLINE_MS`, `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` | WebFetch cache (900000) and download deadline (300000); WebSearch cap, default 200 |
| `CLAUDE_CODE_ENABLE_TODO_TOOLS`, `CLAUDE_CODE_ENABLE_TASKS`, `CLAUDE_CODE_TASK_LIST_ID`, `TASK_MAX_OUTPUT_LENGTH` | Task-tracking tools on every model; `0` selects `TodoWrite`; shared task list; the last has no effect |
| `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY` | Parallel read-only tools and subagents, default 10 |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`, `CLAUDE_CODE_SCRIPT_CAPS` | Strip credentials and config-directory pointers from subprocesses; per-script call caps |
| `CLAUDE_CODE_PERFORCE_MODE`, `CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING`, `CLAUDE_CODE_TMPDIR` | Perforce write protection; no checkpoints; temp directory |

Tool behavior: [[tools-reference]].

## Subagents, background work, automation

| Variable | Purpose |
|---|---|
| `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` | Concurrency (default 20) and nesting depth (default 3) |
| `CLAUDE_CODE_FORK_SUBAGENT`; `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS`, `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS` | Fork mode: `1` also in `-p` and SDK, `0` off everywhere; remove built-in subagents |
| `CLAUDE_AUTO_BACKGROUND_TASKS`, `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`, `CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS`, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Auto-backgrounding on/off; subagent stall timeout; enable agent teams |
| `CLAUDE_CODE_DISABLE_WORKFLOWS`, `CLAUDE_CODE_DISABLE_AGENT_VIEW`, `CLAUDE_CODE_DISABLE_CRON`, `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` | Turn off workflows, agent view and background agents, scheduled tasks; agents per workflow run, 1–256 ([[workflows]]) |
| `CLAUDE_DISABLE_ADOPT`, `CLAUDE_CODE_DISABLE_BG_EXIT_HANDOFF` | Stop in-flight work instead of carrying it into background sessions |
| `CLAUDE_CODE_GOAL_CHECKIN_MINUTES`, `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` | `/goal` check-in interval (30); consecutive Stop-hook blocks (8); SessionEnd hook budget ([[hooks]]) |
| `CLAUDE_CODE_AUTO_MODE_SERVER` | `0` opts out of the server-side auto-mode classifier ([[permissions-and-modes]]) |
| `CLAUDE_CODE_MAX_TURNS`, `MAX_STRUCTURED_OUTPUT_RETRIES`, `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`, `CLAUDE_CODE_BG_TASKS_REPORT_RUNNING` | Turn cap; `--json-schema` attempts (5); `-p` wait for background tasks; running status past turn end ([[worktrees-and-background-work]]) |
| `CLAUDE_CODE_RESUME_INTERRUPTED_TURN`, `CLAUDE_CODE_RESUME_PROMPT`, `CLAUDE_CODE_EXIT_AFTER_STOP_DELAY`, `CLAUDE_CODE_STARTUP_FAILURE_RESULTS` | SDK resume and exit behavior; startup-refusal result messages ([[agent-sdk]]) |
| `CLAUDE_CODE_SKIP_PROMPT_HISTORY`, `CLAUDE_CODE_SIMPLE`, `CLAUDE_CODE_SAFE_MODE`, `CLAUDE_CODE_RESTRICTED` | No transcripts; bare, safe, restricted modes |

## MCP, plugins, skills

| Variable | Purpose |
|---|---|
| `MCP_TIMEOUT`, `MCP_TOOL_TIMEOUT`, `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT`, `MAX_MCP_OUTPUT_TOKENS` | Server startup (30000), tool execution, idle abort; tool response cap, default 25000 |
| `ENABLE_TOOL_SEARCH` | Deferral: unset defers all MCP tools; `auto`, `auto:N`, `true`, `false` |
| `MCP_CONNECTION_NONBLOCKING`, `MCP_CONNECT_TIMEOUT_MS`, `MCP_SERVER_CONNECTION_BATCH_SIZE`, `MCP_REMOTE_SERVER_CONNECTION_BATCH_SIZE`, `CLAUDE_CODE_MCP_STARTUP_WAIT_MS` | Startup connection behavior, including how long a non-interactive first turn waits for connecting servers |
| `ENABLE_CLAUDEAI_MCP_SERVERS`, `CLAUDE_CODE_MCP_ALLOWLIST_ENV`, `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS` | claude.ai connectors; minimal stdio env; background long calls |
| `MCP_CLIENT_SECRET`, `MCP_OAUTH_CALLBACK_PORT`, `MCP_DISCOVERY_CACHE` | OAuth and discovery cache |
| `MCP_SDK_GENERATION`, `MCP_PROTOCOL_NEGOTIATION` | Opt out of the v2 MCP client and current protocol negotiation ([[mcp]]) |
| `CLAUDE_CODE_PLUGIN_CACHE_DIR`, `CLAUDE_CODE_PLUGIN_SEED_DIR`, `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS`, `CLAUDE_CODE_PLUGIN_PREFER_HTTPS`, `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE` | Plugin storage, container seeding, git behavior |
| `CLAUDE_CODE_SYNC_PLUGIN_INSTALL`, `FORCE_AUTOUPDATE_PLUGINS`, `CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL` | Plugin install and update behavior |
| `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS`, `CLAUDE_CODE_DISABLE_POLICY_SKILLS`, `CLAUDE_CODE_SYNC_SKILLS`, `SLASH_COMMAND_TOOL_CHAR_BUDGET` | Bundled and managed skills; make a `-p` run wait for your claude.ai skills; skill listing budget |

## Privacy, updates, telemetry

| Variable | Purpose |
|---|---|
| `DISABLE_TELEMETRY`, `DO_NOT_TRACK`, `DISABLE_ERROR_REPORTING`, `DISABLE_GROWTHBOOK` | Opt out of telemetry, error reporting, feature-flag fetching |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Block auto-updates, telemetry, error reporting, `/feedback`, release notes, availability checks |
| `DISABLE_AUTOUPDATER`, `DISABLE_UPDATES`, `CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE` | Background updates off; all updates off; let Homebrew or WinGet upgrade |
| `DISABLE_DOCTOR_COMMAND`, `DISABLE_FEEDBACK_COMMAND`, `DISABLE_LOGIN_COMMAND`, `DISABLE_LOGOUT_COMMAND`, `DISABLE_UPGRADE_COMMAND`, `DISABLE_EXTRA_USAGE_COMMAND`, `DISABLE_INSTALL_GITHUB_APP_COMMAND` | Hide commands |
| `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY`, `CLAUDE_CODE_SEND_FEEDBACK`, `DISABLE_COST_WARNINGS`, `DISABLE_INSTALLATION_CHECKS` | Surveys, Claude-drafted feedback, warnings |
| `CLAUDE_CODE_DISABLE_ARTIFACT`, `CLAUDE_CODE_ARTIFACT_AUTO_OPEN`, `CLAUDE_CODE_ARTIFACT_COMMENTS` | Artifact tool, browser auto-open, comment replies |
| `CLAUDE_CODE_ENABLE_TELEMETRY`; `OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_ASSISTANT_RESPONSES`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_TOOL_CONTENT`, `OTEL_LOG_RAW_API_BODIES` | Turn on OpenTelemetry export; opt content into it (redacted by default) |
| `OTEL_LOG_MANAGED_SETTINGS`; `OTEL_METRICS_INCLUDE_SESSION_ID`, `OTEL_METRICS_INCLUDE_ACCOUNT_UUID`, `OTEL_METRICS_INCLUDE_VERSION`, `OTEL_METRICS_INCLUDE_REPOSITORY` | Redacted managed settings and their digests on the managed-settings OTel event; metric attributes |
| `CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH`, `CLAUDE_CODE_OTEL_SHUTDOWN_TIMEOUT_MS`, `CLAUDE_CODE_OTEL_DIAG_STDERR`, `CLAUDE_CODE_PROPAGATE_TRACEPARENT` | Exporter tuning and trace propagation |

Standard exporter variables such as `OTEL_EXPORTER_OTLP_ENDPOINT` also work. `DISABLE_GROWTHBOOK`, `DISABLE_TELEMETRY`, `DO_NOT_TRACK` and `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` each turn off feature-flag fetching, which removes Remote Control, the advisor, `/skill-doctor`, `claude import`, auto mode as the default start mode, `AGENTS.md` as project instructions, claude.ai skill and plugin sync, messaging to other machines and Claude-drafted feedback. Third-party providers and Claude apps gateway sessions skip the fetch too. See [[data-and-privacy]], [[enterprise-admin]].

## Terminal and display

| Variable | Purpose |
|---|---|
| `CLAUDE_CODE_NO_FLICKER`, `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN` | Fullscreen renderer on; classic renderer |
| `CLAUDE_CODE_DISABLE_MOUSE`, `CLAUDE_CODE_DISABLE_MOUSE_CLICKS`, `CLAUDE_CODE_SCROLL_SPEED` | Mouse handling and wheel speed in fullscreen |
| `CLAUDE_CODE_DISABLE_VIRTUAL_SCROLL`, `CLAUDE_CODE_ALT_SCREEN_FULL_REPAINT` | Fullscreen rendering fixes |
| `CLAUDE_AX_SCREEN_READER`, `CLAUDE_CODE_ACCESSIBILITY`, `CLAUDE_CODE_NATIVE_CURSOR` | Screen-reader output, magnifier-friendly cursor |
| `CLAUDE_CODE_SYNTAX_HIGHLIGHT`, `CLAUDE_CODE_TMUX_TRUECOLOR`, `FORCE_HYPERLINK`, `CLAUDE_CODE_FORCE_SYNC_OUTPUT` | Colors, hyperlinks, synchronized output |
| `CLAUDE_CODE_NONBLOCKING_STDOUT`, `CLAUDE_CODE_DISABLE_TERMINAL_TITLE`, `CLAUDE_CODE_HIDE_CWD`, `IS_DEMO` | Stalled-terminal protection, title, hide path, demo mode |
| `CLAUDE_CODE_ENABLE_PROMPT_SUGGESTION`, `CLAUDE_CODE_ENABLE_AWAY_SUMMARY`, `CLAUDE_AFK_TIMEOUT_MS` | Prompt suggestions, session recap, `AskUserQuestion` auto-continue |
| `CLAUDE_CODE_AUTO_CONNECT_IDE`, `CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL` | IDE connection and extension install |

## Debugging and config location

| Variable | Purpose |
|---|---|
| `DEBUG` | `1`, `true`, `yes` or `on` enables debug mode; log at `~/.claude/debug/<session-id>.txt` |
| `CLAUDE_CODE_DEBUG_LOGS_DIR`, `CLAUDE_CODE_DEBUG_LOG_LEVEL` | Debug log *file* path, needing debug mode enabled separately; `verbose`, `debug` (default), `info`, `warn`, `error` |
| `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_PROJECT_DIR_NAME` | Config directory, default `~/.claude`, e.g. `alias claude-work='CLAUDE_CONFIG_DIR=~/.claude-work claude'`; the `projects/` directory name under it |

## Set by Claude Code

Read these from scripts, hooks and tools; don't set them.

| Variable | Value |
|---|---|
| `CLAUDECODE`, `CLAUDE_CODE_CHILD_SESSION` | `1` in spawned subprocesses; the child marker is set only by Claude Code itself |
| `CLAUDE_CODE_SESSION_ID`, `CLAUDE_PID`, `CLAUDE_EFFORT` | Session ID, Claude Code's PID, effort level in effect |
| `CLAUDE_JOB_DIR` | Background session's `~/.claude/jobs/<id>` directory |
| `CLAUDE_CODE_REMOTE`, `CLAUDE_CODE_REMOTE_SESSION_ID`, `CLAUDE_CODE_BRIDGE_SESSION_ID` | Cloud session marker and IDs; Remote Control session ID |
| `CLAUDE_CODE_MESSAGING_SOCKET`, `CLAUDE_CODE_MESSAGING_TOKEN` | Cross-session messaging inbox and token |
