---
title: OpenCode
type: entity
tldr: "Terminal agent compared with Claude Code"
sources:
  - raw/docs/opencode/docs-rules.md
  - raw/docs/opencode/docs-config.md
  - raw/docs/opencode/docs-skills.md
  - raw/docs/opencode/docs-permissions.md
  - raw/docs/opencode/docs-mcp-servers.md
  - raw/docs/opencode/docs-agents.md
  - raw/docs/opencode/docs-plugins.md
  - raw/docs/opencode/docs-tools.md
  - raw/docs/opencode/docs-custom-tools.md
  - raw/docs/opencode/config-json-schema.md
  - raw/docs/opencode/src-session-instruction-ts.md
  - raw/docs/opencode/src-config-paths-ts.md
  - raw/docs/opencode/src-config-agent-ts.md
  - raw/docs/opencode/src-config-plugin-ts.md
  - raw/docs/opencode/src-skill-index-ts.md
  - raw/docs/opencode/src-tool-skill-ts.md
  - raw/docs/opencode/src-permission-index-ts.md
  - raw/docs/opencode/src-core-util-wildcard-ts.md
  - raw/docs/opencode/src-mcp-index-ts.md
  - raw/docs/opencode/src-plugin-hooks-index-ts.md
  - raw/docs/opencode/src-tool-edit-ts.md
  - raw/docs/opencode/src-tool-write-ts.md
  - raw/docs/opencode/src-tool-apply-patch-ts.md
  - raw/docs/opencode/src-tool-webfetch-ts.md
  - raw/docs/official/memory.md
  - raw/docs/official/settings.md
  - raw/docs/official/permission-modes.md
  - raw/docs/official/mcp.md
  - raw/docs/official/skills.md
  - raw/docs/official/sub-agents.md
  - raw/docs/official/hooks.md
  - raw/docs/official/headless.md
related: ["[[openai-codex]]", "[[skills]]", "[[mcp]]", "[[permissions-and-modes]]", "[[hooks]]", "[[agent-standards]]"]
created: 2026-09-17
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [opencode, opencode-vs-claude-code, opencode-config, opencode-plugin-hooks, opencode-skills]
valid_until: 2027-03-15
---

# OpenCode

OpenCode is an open-source coding agent that runs in your terminal as a TUI, non-interactively through `opencode run`, and as an HTTP server behind `opencode serve` and `opencode web`; the same configuration also drives its desktop app and GitHub Action. It is provider-agnostic: models are named `provider/model-id`, and providers can be restricted with `enabled_providers` and `disabled_providers`. Read this page if you know Claude Code and want to run OpenCode over the same repo, because OpenCode reads several Claude Code conventions on purpose. For the other side-by-side, see [[openai-codex]].

## Project instructions

OpenCode reads `AGENTS.md` from the project root for shared rules and `~/.config/opencode/AGENTS.md` for personal ones. `/init` creates or improves the project file in place. For Claude Code users, `CLAUDE.md` in the project and `~/.claude/CLAUDE.md` globally are fallbacks.

Resolution walks up from the working directory to the git worktree looking for `AGENTS.md`, then `CLAUDE.md`, then the deprecated `CONTEXT.md`, and **the first name that matches anywhere wins for the whole project layer** — so if a repo has both files, only `AGENTS.md` is loaded, and `CLAUDE.md` is ignored entirely rather than appended. The same rule applies globally: `~/.config/opencode/AGENTS.md` shuts out `~/.claude/CLAUDE.md`. Instruction files in subdirectories are attached lazily as the agent reads files beneath them.

Three environment variables turn the compatibility off: `OPENCODE_DISABLE_CLAUDE_CODE` disables all `.claude` support, `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT` disables only the `CLAUDE.md` fallbacks, and `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS` disables only `.claude/skills`.

Everything else is pulled in through the `instructions` config key, an array of paths, globs and `https://` URLs — `["CONTRIBUTING.md", "packages/*/AGENTS.md", ".cursor/rules/*.md"]` — appended to whatever `AGENTS.md` was found. OpenCode does not expand `@file` references inside `AGENTS.md` the way [[claude-md-and-memory]] describes for Claude Code; remote instruction URLs are fetched with a five-second timeout.

## Config files and precedence

Config is JSON or JSONC (comments and trailing commas allowed), validated against `https://opencode.ai/config.json`. Project config is `opencode.json` (or `.jsonc`) found by walking up from the current directory to the git root; the global file is `~/.config/opencode/opencode.json`. Files are **merged, not replaced**, so a global `autoupdate` and a project `model` both survive. Later sources override earlier ones:

1. Remote config from an organization's `.well-known/opencode` endpoint
2. Global config
3. `OPENCODE_CONFIG` (a custom file path)
4. Project `opencode.json`
5. `.opencode` directories — agents, commands, plugins
6. `OPENCODE_CONFIG_CONTENT` (inline JSON)
7. Managed config files (`/etc/opencode/` on Linux, `/Library/Application Support/opencode/` on macOS, `%ProgramData%\opencode` on Windows)
8. macOS managed preferences delivered as a `.mobileconfig` through MDM, which users cannot override

`.opencode/` and `~/.config/opencode/` hold the subdirectories `agents/`, `commands/`, `modes/`, `plugins/`, `skills/`, `tools/` and `themes/`; the singular spellings still load. `OPENCODE_CONFIG_DIR` adds another directory with that same layout. TUI settings live apart in `tui.json`. `opencode debug config` prints the resolved result.

## Skills

Skills are a folder per skill with a `SKILL.md` inside, loaded on demand through a native `skill` tool. OpenCode searches six roots, three of them Claude Code's and the agent standard's:

- `.opencode/skills/<name>/SKILL.md` and `~/.config/opencode/skills/<name>/SKILL.md`
- `.claude/skills/<name>/SKILL.md` and `~/.claude/skills/<name>/SKILL.md`
- `.agents/skills/<name>/SKILL.md` and `~/.agents/skills/<name>/SKILL.md`

Project-local roots are collected by walking up from the working directory to the git worktree, so every `.claude/skills` and `.agents/skills` on the way contributes. `skills.paths` and `skills.urls` in config add further folders and fetched collections.

Recognized frontmatter is `name` (required), `description` (required), and the optional `license`, `compatibility` and `metadata` (a string-to-string map). **Unknown frontmatter fields are ignored**, so Claude Code's extra keys are harmless. `name` must be 1–64 characters, lowercase alphanumeric with single hyphen separators (`^[a-z0-9]+(-[a-z0-9]+)*$`), must not start or end with `-` or contain `--`, and must match its directory name; `description` must be 1–1024 characters. Names must be unique across all locations, and the filename must be capitalized `SKILL.md`.

The agent sees an `<available_skills>` list of names and descriptions in the `skill` tool's description and loads one by calling `skill({ name: "git-release" })`; the tool returns the body plus the skill's base directory and a sampled list of its other files. Access is gated by `permission.skill`, a pattern map where `allow` loads immediately, `ask` prompts, and `deny` hides the skill from the agent entirely — `{"*": "allow", "internal-*": "deny"}`. Per-agent overrides go in agent frontmatter, and `tools: { skill: false }` removes the tool. This is the same `SKILL.md` contract described in [[skills]] and [[agent-standards]].

## MCP servers

Servers are declared under the `mcp` key and their tools are registered with the server name as a prefix. A local server takes a **single `command` array** holding the executable and its arguments together — not Claude Code's separate `command` and `args`:

```jsonc
{
  "mcp": {
    "my-local-mcp-server": {
      "type": "local",
      "command": ["npx", "-y", "my-mcp-command"],
      "cwd": "packages/api",
      "environment": { "MY_ENV_VAR": "my_env_var_value" },
      "enabled": true,
      "timeout": 5000
    }
  }
}
```

`type` and `command` are required. `cwd` sets the server's working directory and resolves relative paths from the workspace, `environment` sets variables for the process, `enabled` switches the server off without deleting it, and `timeout` is the milliseconds allowed for fetching tools.

> [!contradiction]
> The MCP docs and the config schema both give `timeout`'s default as 5000 ms, while the MCP implementation falls back to a `DEFAULT_TIMEOUT` of 30,000 ms when no `timeout` is set. Set it explicitly if the value matters.

Remote servers take `type: "remote"` with `url`, optional `headers`, and OAuth that is auto-detected (or configured with `clientId`/`clientSecret`/`scope`, or disabled with `oauth: false`). `opencode mcp auth`, `list`, `logout` and `debug` manage credentials. Compare the `.mcp.json` shape in [[mcp]].

## Permissions

OpenCode allows everything by default, and the `permission` key narrows that. Each rule resolves to `allow`, `ask` or `deny`. A key can take a bare action (`"edit": "ask"`), a pattern map, or the whole key can be one string (`"permission": "allow"`). Patterns are matched against the tool input: a file path for `read` and `edit`, the parsed command for `bash`, the URL for `webfetch`, the subagent type for `task`, the skill name for `skill`.

```json
{
  "permission": {
    "bash": { "*": "ask", "git *": "allow", "rm *": "deny" },
    "edit": { "*": "deny", "packages/web/src/content/docs/*.mdx": "allow" }
  }
}
```

Four things to internalize. **The last matching rule wins**, so the catch-all `"*"` goes first and specific rules after. `edit` is one key covering all three mutating tools — `edit`, `write` and `apply_patch` — so there is no separate write permission. The pattern for those tools is the file path **relative to the git worktree**, not an absolute path. And `*` in a pattern compiles to `.*` with dot-matching-newline, so **it crosses `/` freely**: `src/*` also matches `src/a/b/c.ts`; `?` matches exactly one character, and `~` or `$HOME` at the start of a pattern expands to the home directory.

Beyond tool names there are `external_directory` (anything touching paths outside the worktree) and `doom_loop` (the same call with identical input three times), both defaulting to `ask`; `read` defaults to allow but denies `*.env`. `--auto` (also `opencode run --auto`) auto-approves anything not explicitly denied. An `ask` prompt offers once, always (for the rest of the session) or reject. Agents can override any of this, and agent rules win. Claude Code's equivalent model is in [[permissions-and-modes]].

## Agents and subagents

Built-in primary agents are **build** (everything enabled, the default) and **plan** (edits and bash set to `ask`); built-in subagents are **general**, **explore** (read-only) and **scout** (read-only dependency and docs research). Hidden system agents handle compaction, titles and summaries. Tab cycles primary agents; `@general` invokes a subagent by hand.

Custom agents are markdown files in `.opencode/agents/` or `~/.config/opencode/agents/`, where the filename becomes the agent name and the body becomes the system prompt:

```markdown
---
description: Reviews code for quality and best practices
mode: subagent
model: anthropic/claude-sonnet-4-5
temperature: 0.1
permission:
  edit: deny
  bash: { "*": ask, "git log*": allow }
---

You are in code review mode.
```

`description` is required. `mode` is `primary`, `subagent` or `all`, defaulting to `all`. `model` uses the `provider/model-id` format; unset, primary agents take the global model and subagents inherit the caller's. Other fields are `temperature`, `top_p`, `steps` (a cap on agentic iterations), `prompt` (a `{file:...}` reference), `permission`, `disable`, `hidden` (keeps a subagent out of `@` autocomplete), `color`, and any additional keys, which pass through to the provider as model options. The same objects can be written under `agent` in `opencode.json`. `default_agent` picks the starting primary agent and `subagent_depth` (default 1) caps nesting. `opencode agent create` scaffolds one. See [[subagents]] for Claude Code's version.

## Plugins are the hook system

OpenCode has no separate hooks file: a plugin is a JavaScript or TypeScript module in `.opencode/plugins/` or `~/.config/opencode/plugins/` (or an npm package listed in `plugin`), and hooks are the object it returns.

```ts
export const MyPlugin = async ({ project, client, $, directory, worktree }) => ({
  "tool.execute.before": async (input, output) => {
    if (input.tool === "read" && output.args.filePath.includes(".env"))
      throw new Error("Do not read .env files")
  },
})
```

`tool.execute.before` receives `input: { tool, sessionID, callID }` and `output: { args }`. Mutating `output.args` rewrites the call; **throwing blocks it**. `tool.execute.after` receives `input: { tool, sessionID, callID, args }` and `output: { title, output, metadata }`, so **`output.output` can be rewritten after the tool has run**. The `event` hook takes `({ event })` and switches on `event.type`: session events are `session.created`, `session.compacted`, `session.deleted`, `session.diff`, `session.error`, `session.idle`, `session.status` and `session.updated`, alongside `file.edited`, `permission.asked`, `permission.replied`, `command.executed`, `todo.updated` and others. Also available: `shell.env` for injecting variables, `permission.ask`, `chat.params`, `chat.headers`, `tool.definition`, and `experimental.session.compacting`. All plugins load in sequence (global config, project config, global directory, project directory) and every hook runs.

Built-in tool names and the argument keys those hooks see: `bash` (`command`), `read` (`filePath`), `write` (`filePath`, `content`), `edit` (`filePath`, `oldString`, `newString`, `replaceAll`), `apply_patch` (`patchText` — match on `"apply_patch"`, not `"patch"`, and note paths live in marker lines such as `*** Update File: src/existing.ts` inside the patch text), `grep`, `glob`, `list`, `task`, `todowrite`, `webfetch` (`url`, `format`, `timeout`), `websearch`, `skill` (`name`), `question` and experimental `lsp`. Plugins can also register new tools through the `tool` key, and standalone custom tools live in `.opencode/tools/`, where the filename becomes the tool name.

## OpenCode compared with Claude Code

| Area | OpenCode | Claude Code |
|---|---|---|
| Instruction file | `AGENTS.md`, falling back to `CLAUDE.md`; first match wins, one layer only | `CLAUDE.md`, `CLAUDE.local.md`, `~/.claude/CLAUDE.md`, all levels concatenated, `@path` imports; `AGENTS.md` when no `CLAUDE.md` is present ([[claude-md-and-memory]]) |
| Config format | JSON/JSONC `opencode.json`, `~/.config/opencode/opencode.json`, merged; `.opencode/` dirs | JSON `.claude/settings.json`, `~/.claude/settings.json`, `.claude/settings.local.json`, managed settings |
| Extra instruction files | `instructions` array of paths, globs and URLs | `@imports` inside CLAUDE.md |
| Autonomy controls | `permission` rules (`allow`/`ask`/`deny`), last match wins, `--auto` | Permission modes `default` (Manual), `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions` plus allow/ask/deny rules ([[permissions-and-modes]]) |
| Write permission | One `edit` key covers `edit`, `write` and `apply_patch` | Per-tool rules such as `Edit`, `Write`, `Bash(git status:*)` |
| Skills | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` (project and global); `skill` tool | `.claude/skills/<name>/SKILL.md`, `~/.claude/skills/` ([[skills]]) |
| MCP config | `mcp` key in config; one `command` array; `cwd`, `environment`, `timeout` | `.mcp.json` with separate `command` and `args`; `claude mcp add` ([[mcp]]) |
| Subagents | Markdown in `.opencode/agents/`; built-ins build, plan, general, explore, scout | Markdown in `.claude/agents/`, `~/.claude/agents/` ([[subagents]]) |
| Hooks | TypeScript/JavaScript plugins returning hook functions; throw to block | Shell or HTTP handlers wired to events with matchers in settings ([[hooks]]) |
| Custom tools | `.opencode/tools/*.ts` with a Zod schema | MCP servers or skills |
| Non-interactive | `opencode run` | `claude -p` ([[headless-mode]]) |
| Model naming | `provider/model-id` across many providers | Anthropic models plus gateways ([[models-and-effort]]) |
