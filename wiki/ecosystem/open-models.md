---
title: Open Models for Claude Code and Codex
type: how-to
tldr: "OpenRouter, NIM and bridges for open models"
sources:
  - raw/docs/openrouter/claude-code-integration.md
  - raw/docs/openrouter/codex-cli.md
  - raw/docs/openrouter/free-models-router.md
  - raw/docs/openrouter/limits-2026-09-17.md
  - raw/docs/openrouter/anthropic-agent-sdk.md
  - raw/docs/openrouter/authentication.md
  - raw/docs/openrouter/quickstart.md
  - raw/docs/openrouter/models-api-2026-09-14.json
  - raw/docs/nvidia-nim/introduction.md
  - raw/docs/nvidia-nim/faq.md
  - raw/docs/nvidia-nim/llm-apis.md
  - raw/docs/nvidia-nim/qwen3-next-80b-a3b-instruct-infer.md
  - raw/docs/nvidia-nim/models-api-2026-09-14.json
  - raw/docs/claude-code-bridges/claude-code-router-readme.md
  - raw/docs/claude-code-bridges/litellm-claude-code-tutorial.md
  - raw/docs/claude-code-bridges/litellm-anthropic-unified.md
  - raw/docs/claude-code-bridges/cc-mirror-readme.md
  - raw/docs/openai-codex/config-advanced.md
related: ["[[llm-gateways]]", "[[openai-codex]]", "[[models-and-effort]]", "[[environment-variables]]", "[[agent-sdk]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: medium
last_verified: 2026-09-17
aliases: [openrouter, nvidia-nim, claude-code-router, litellm, cc-mirror]
valid_until: 2027-03-15
---

# Open Models for Claude Code and Codex

Claude Code speaks the Anthropic Messages API. Point `ANTHROPIC_BASE_URL` at any endpoint that serves that format and Claude Code will use whatever models that endpoint routes to. Endpoints that only speak OpenAI Chat Completions, such as NVIDIA NIM, need a translating bridge in between. Codex reaches other models through `model_providers` in `config.toml` (see [[openai-codex]]). Anthropic's own gateway configuration is covered in [[llm-gateways]]. This page covers the third-party options.

> [!warning]
> OpenRouter's own guide says "Claude Code is optimized for Anthropic models and may not work correctly with other providers," and that Claude Code through OpenRouter is "only guaranteed to work with the Anthropic first-party provider." Expect tool-use and feature gaps with open models.

## OpenRouter with Claude Code

OpenRouter's "Anthropic Skin" at `https://openrouter.ai/api` accepts Claude Code's native protocol directly, with no local proxy. Put these in your shell profile or in the `env` block of `.claude/settings.local.json`. A project `.env` file doesn't work, because the native installer doesn't read it.

```bash
export OPENROUTER_API_KEY="<key>"
export ANTHROPIC_BASE_URL="https://openrouter.ai/api"
export ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"   # sent as Authorization: Bearer
export ANTHROPIC_API_KEY=""                         # must be explicitly empty
export CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1 # optional model picker
```

1. If you were logged in with an Anthropic account, run `/logout` once and relaunch. A cached login conflicting with the gateway credential causes model-not-found errors.
2. Check `/status`. It should show `Auth token: ANTHROPIC_AUTH_TOKEN` and the OpenRouter base URL.
3. Route each model class with `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, `ANTHROPIC_DEFAULT_FABLE_MODEL` and `CLAUDE_CODE_SUBAGENT_MODEL`, set to any OpenRouter slug. Fable doesn't appear in `/model` unless you set its variable.
4. Claude Code assumes a 200k window unless the model name ends in `[1m]`. OpenRouter strips that suffix before routing.
5. `/fast` needs `CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK=1` and a specific Opus ID. With a `~anthropic/claude-opus-latest` alias it reports fast mode on but sends requests at standard speed.

The Agent SDK uses the same three `ANTHROPIC_*` variables (see [[agent-sdk]]).

## OpenRouter with Codex

```toml
# ~/.codex/config.toml
model_provider = "openrouter"
model = "~openai/gpt-sol-latest"   # or any OpenRouter slug

[model_providers.openrouter]
name = "openrouter"
base_url = "https://openrouter.ai/api/v1"

[model_providers.openrouter.auth]
command = "sh"
args = ["-c", "echo $OPENROUTER_API_KEY"]
```

Use command-based `auth` rather than `env_key`, because only command auth makes Codex fetch the OpenRouter model catalog. With `env_key`, non-OpenAI models show an "Unknown model" warning. For fully local models, Codex also has `--oss` mode with `oss_provider = "ollama"` or `"lmstudio"`.

## Free models

`openrouter/free` picks a random free model that supports the features your request needs, such as tools, vision or structured output. Add the `:free` suffix to a model id to pin a specific free model. The 2026-09-14 snapshot lists 19 `:free` ids, including `google/gemma-4-31b-it:free`, `nvidia/nemotron-3-super-120b-a12b:free` and `nvidia/nemotron-3-ultra-550b-a55b:free`. Free variants share one platform cap: 20 requests per minute, and 50 requests per UTC day until the account has purchased at least 10 credits, which raises the daily cap to 1,000. Paid variants of the same model have no platform-level request cap. `GET https://openrouter.ai/api/v1/key` reports the day's free-model usage, limit and remainder. A negative credit balance returns HTTP 402 even on free models.

## Prices (OpenRouter snapshot 2026-09-14)

USD per million tokens, from `GET /api/v1/models` (447 models). Every row supports `tools`.

| Model id | Input | Output | Context |
|---|---|---|---|
| `deepseek/deepseek-v4-pro` | 1.6 | 3.2 | 1,048,576 |
| `deepseek/deepseek-v4-flash` | 0.084 | 0.168 | 1,048,576 |
| `moonshotai/kimi-k3` | 2.648138063 | 13.28272425 | 1,048,576 |
| `moonshotai/kimi-k2.7-code` | 0.71 | 3.5 | 262,144 |
| `qwen/qwen3-coder-plus` | 0.65 | 3.25 | 1,000,000 |
| `qwen/qwen3-coder-next` | 0.12 | 0.8 | 262,144 |
| `z-ai/glm-5.3` | 1.4 | 4.4 | 1,310,720 |
| `z-ai/glm-5.3-flash` | 0.15 | 0.5 | 1,310,720 |
| `minimax/minimax-m3` | 0.3 | 1.2 | 1,048,576 |
| `mistralai/devstral-2512` | 0.4 | 2 | 262,144 |
| `openai/gpt-oss-120b` | 0.037 | 0.17 | 131,072 |
| `nvidia/nemotron-3-super-120b-a12b` | 0.08 | 0.45 | 262,144 |

Router ids such as `openrouter/auto` and `openrouter/pareto-code` have variable pricing.

## NVIDIA NIM

NIM offers two things. The first is hosted endpoints at `https://integrate.api.nvidia.com`, an OpenAI-compatible `POST /v1/chat/completions` API with trial credits from build.nvidia.com; browser use there doesn't spend credits. The second is self-hosted Docker containers that need NVIDIA-certified GPUs and an NVIDIA AI Enterprise license, priced at "$4500 per GPU per year or $1 per GPU per hour in the cloud". The 2026-09-14 model list has 81 ids. Coding-relevant ones include:

- `moonshotai/kimi-k3`
- `moonshotai/kimi-k2.6`
- `deepseek-ai/deepseek-v4-flash-0731`
- `z-ai/glm-5.3-flash`
- `openai/gpt-oss-20b`
- `mistralai/codestral-22b-instruct-v0.1`
- `nvidia/nemotron-3-ultra-550b-a55b`

NIM speaks OpenAI format, so Claude Code needs one of the bridges below to use it.

## Bridges

| Bridge | What it is | Start |
|---|---|---|
| **claude-code-router (CCR)** | Local gateway plus control plane for Claude Code, Codex and other agents. Handles OpenAI Chat/Responses, Anthropic Messages, Gemini, OpenRouter, DeepSeek, Moonshot, Mistral, Z.AI and custom providers, with routing rules, retries, fallbacks and request logs | Desktop app, or `npm install -g @musistudio/claude-code-router` (Node 22+) then `ccr ui`. UI at `http://127.0.0.1:3458`, gateway at `127.0.0.1:3456`. In the UI: Providers → Server → Agent Config |
| **LiteLLM proxy** | Self-hosted proxy whose `/v1/messages` endpoint accepts any LiteLLM provider (`openai/`, `gemini/`, `vertex_ai/`, `bedrock/`…) in Anthropic format | `uv tool install 'litellm[proxy]'`, `litellm --config config.yaml` (port 4000) |
| **cc-mirror** | Builds isolated Claude Code variants, each with its own config, sessions, MCP servers and credentials under `~/.cc-mirror/<variant>/`, plus a wrapper command | `npx cc-mirror quick --provider zai --api-key "$Z_AI_API_KEY"` |

LiteLLM with Claude Code:

```bash
export ANTHROPIC_BASE_URL="http://0.0.0.0:4000"
export ANTHROPIC_AUTH_TOKEN="$LITELLM_KEY"   # master or virtual key
claude --model <model_name from config.yaml>
```

- A non-Anthropic `ANTHROPIC_BASE_URL` turns off Claude Code's tool search. Set `ENABLE_TOOL_SEARCH=true` to keep MCP tool schemas out of context.
- On Bedrock-backed routes, set `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` to avoid `invalid beta flag` errors.
- For rotating keys, use an `apiKeyHelper` script together with `CLAUDE_CODE_API_KEY_HELPER_TTL_MS`.

cc-mirror providers are `kimi`, `minimax`, `zai`, `openrouter`, `vercel`, `ollama`, `nanogpt`, `ccrouter`, `gatewayz`, `mirror` and `custom`. Map model slots with `--model-sonnet`, `--model-opus` and `--model-haiku`. Pin the runtime with `npx cc-mirror update <name> --claude-version <version>`, and check all variants with `npx cc-mirror doctor`.
