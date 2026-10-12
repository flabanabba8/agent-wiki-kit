---
title: Plugins
type: reference
tldr: "Install, build, load and test plugins"
sources:
  - raw/docs/official/plugins__overview.md
  - raw/docs/official/plugins__install.md
  - raw/docs/official/plugins__anthropic-marketplaces.md
  - raw/docs/official/plugins__create.md
  - raw/docs/official/plugins__components.md
  - raw/docs/official/plugins__manifest-reference.md
  - raw/docs/official/plugins__loading.md
  - raw/docs/official/plugins__cli-reference.md
  - raw/docs/official/plugins__code-intelligence.md
  - raw/docs/official/plugins__measure.md
  - raw/docs/official/plugins__security.md
  - raw/docs/official/plugins__troubleshooting.md
  - raw/docs/official/plugin-evals.md
  - raw/docs/changelog-2.1.275-to-2.1.282.md
related: ["[[plugin-marketplaces]]", "[[skills]]", "[[subagents]]", "[[hooks]]", "[[mcp]]", "[[enterprise-admin]]", "[[settings]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [claude-plugins, plugin-json, claude-plugin-eval, plugin-dir, install-plugin, plugin-scopes, synced-plugins]
---

# Plugins

A plugin is a directory of [[skills]], [[subagents]], [[hooks]], [[mcp]] servers, LSP servers and other components that Claude Code installs and loads as one unit, usually from a marketplace. Standalone files under `.claude/` work without a plugin; make one when you want to share a setup with teammates, reuse it across projects or publish versioned releases. Running and publishing marketplaces is on [[plugin-marketplaces]]; org policy is on [[enterprise-admin]].

A plugin runs code with your user privileges. Hooks and MCP servers run outside the sandbox; calls to its MCP tools and `bin/` executables are tool calls, so permission rules apply. An enabled plugin also costs context every turn: the names and descriptions of its model-invocable skills, agents and commands.

## Install and manage

- Claude Code adds the official marketplace, `claude-plugins-official`, on the first interactive terminal session unless policy or `CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL` blocks it. Others are added with `/plugin marketplace add <source>` (see [[plugin-marketplaces]]).
- `/plugin install commit-commands@claude-plugins-official` opens the plugin's details (**Will install**, and for official plugins a **Context cost** estimate) and asks for a scope. The summary says `Plugin is now active.` or `Run /reload-plugins to activate.`
- `/plugin install deploy-helper --marketplace your-org/plugins` adds the marketplace after confirmation and then installs.
- `/plugin` has **Discover**, **Installed**, **Marketplaces** and **Errors** tabs, plus **Stats** for the usage report. **Installed** groups plugins under **Not used recently** and shows **Last used**.
- From the shell, `claude plugin install formatter@your-org --scope project` installs without a session; `--yes` accepts a `command`-source prompt and `--config key=value` sets options. On a fresh machine, run `claude plugin marketplace add anthropics/claude-plugins-official` first.
- `claude plugin enable|disable|uninstall|update <plugin>@<marketplace>`, `claude plugin list` and `claude plugin details <name>` manage installs. `details` prints an `Always-on` token figure and a per-component breakdown. On install, enable, disable, uninstall and update, `--json` prints one result object for scripts.
- Closing `/plugin` with pending changes runs `/reload-plugins`. If a reload would invalidate the prompt cache (adding or removing MCP tools or the LSP tool), it warns instead; `/reload-plugins --force` applies it.
- **Other surfaces:** the desktop app's **+ > Plugins** and VS Code's `/plugins` read the same settings files as the terminal. `claude -p` loads installed plugins, but `/plugin` doesn't run there. Cloud sessions load neither your local plugins nor a repository's plugin settings; only server-managed settings install plugins there.

| Scope | Settings file |
| :-- | :-- |
| `user` (default) | `~/.claude/settings.json` |
| `project` | `.claude/settings.json` (committed) |
| `local` | `.claude/settings.local.json` |
| `managed` | Managed settings (read-only) |

Local overrides project, which overrides user. A project that enables a plugin from an external source still needs each collaborator to run `claude plugin install <name>@<marketplace> --scope project`. Uninstalling a project-enabled plugin asks whether to disable it for you (`y`) or remove it for everyone (`u`). Installing or enabling a plugin also installs or enables its dependencies; after an uninstall, `claude plugin prune` removes the orphaned ones.

**Updates.** Auto-update is on by default for official marketplace names (except `knowledge-work-plugins` and `first-party-plugins`) and marketplaces added from claude.ai, and off for everything else; toggle it per marketplace under **Marketplaces**. It runs after a random delay of up to ten minutes after your first message, and the running session keeps the old version until `/reload-plugins`. `DISABLE_UPDATES`, `DISABLE_AUTOUPDATER` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` turns it off unless `FORCE_AUTOUPDATE_PLUGINS=1` is also set. Removing a marketplace uninstalls its plugins.

**Plugins from claude.ai.** Plugins you or your org enable on your claude.ai account sync in the background at each terminal start (v2.1.273+) and load as `<name>@synced`. Disable one with `claude plugin disable <name>@synced`, unless your org marks it required; `syncClaudeAiPlugins: false` stops all of them. Plugins installed locally don't go to claude.ai, and the `ListPlugins` tool lists the claude.ai ones. `claude plugin marketplace add --claudeai <name>` adds a marketplace claude.ai lists, registered under a `claudeai-` name.

**Code intelligence plugins** (`typescript-lsp`, `pyright-lsp`, `gopls-lsp`, `rust-analyzer-lsp`, `clangd-lsp` and others) give Claude diagnostics after edits and symbol navigation. Install the language server binary separately; `Executable not found in $PATH` in the Errors tab names the missing one.

## Create a plugin

```bash
mkdir -p my-first-plugin/.claude-plugin my-first-plugin/skills/hello
```

```json
{ "name": "my-first-plugin", "description": "A greeting plugin", "version": "1.0.0", "author": { "name": "Your Name" } }
```

Save the JSON as `my-first-plugin/.claude-plugin/plugin.json`, add `skills/hello/SKILL.md`, run `claude plugin validate ./my-first-plugin`, then `claude --plugin-dir ./my-first-plugin` and `/my-first-plugin:hello`. To convert an existing `.claude/` setup, copy `commands/`, `agents/` and `skills/` to the plugin root and move the settings `hooks` object into `hooks/hooks.json`; delete the originals afterward, or hooks run twice.

| Path at plugin root | Holds |
| :-- | :-- |
| `.claude-plugin/plugin.json` | Manifest (optional; nothing else goes in `.claude-plugin/`) |
| `skills/<name>/SKILL.md`, or one root `SKILL.md` | Skills |
| `commands/` | Flat Markdown skills (older form) |
| `agents/` | Subagents; `permissionMode`, `hooks`, `mcpServers` and `initialPrompt` are ignored |
| `hooks/hooks.json` | Hook config, same shape as settings |
| `.mcp.json` | MCP servers |
| `.lsp.json` | Language servers; `command` and `extensionToLanguage` required |
| `monitors/monitors.json` | Background monitors; interactive sessions only |
| `bin/` | Executables on the Bash tool's `PATH`, after the user's own entries |
| `settings.json` | Only `agent` and `subagentStatusLine` apply |
| `output-styles/`, `themes/`, `workflows/` | Output styles, color themes, workflow scripts |

A root `CLAUDE.md` isn't loaded; ship instructions as a skill.

**Manifest.** `name` (kebab-case) is the only required field and namespaces every component. Other fields:

- Metadata: `displayName`, `version`, `description`, `author`, `homepage` (must parse as a URL), `repository`, `license`, `keywords`, `metadata`, and `defaultEnabled` (`false` installs it off).
- Component paths: `skills` adds to the default scan; `commands`, `agents` (`.md` files only), `outputStyles`, `workflows` and the experimental themes and monitors replace their defaults; `hooks`, `mcpServers` (also `.mcpb`/`.dxt` bundles) and `lspServers` merge with the default file. Paths start with `./` and must stay inside the plugin.
- `userConfig`: options prompted at enable time, each with `type` (`string`, `number`, `boolean`, `directory` or `file`), `title` and `description`, plus optional `required`, `default`, `options`, `multiple`, `sensitive` (kept in secure storage) and `min`/`max`. Values substitute as `${user_config.KEY}` in MCP and LSP config, exec-form hook `args`, and skill and agent content (non-sensitive only), and reach hooks as `CLAUDE_PLUGIN_OPTION_<KEY>`. Shell-form hooks, monitors and MCP `headersHelper` reject `${user_config.*}`. Options also appear in `/config`; `/plugin configure <plugin>` reopens the dialog.
- `settings`, `channels`, `dependencies` ([[plugin-marketplaces]]), and `experimental.themes`, `experimental.monitors` and `experimental.evals`.

**Paths and data.** Marketplace plugins are copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, so reference bundled files with `${CLAUDE_PLUGIN_ROOT}` (quoted in shell-form hooks) and never write state there. `${CLAUDE_PLUGIN_DATA}` (`~/.claude/plugins/data/<id>/`) survives updates and is deleted on the last uninstall unless you pass `--keep-data`. `${CLAUDE_PROJECT_DIR}` is the project root. These variables aren't in the Bash tool's environment. When the plugin root has `package.json` and a bun or npm lockfile, Claude Code installs dependencies into the cached copy with frozen resolution and `--ignore-scripts` (60-second timeout; Yarn and pnpm are skipped).

**Plugin MCP names** are `plugin:<plugin>:<server>` for the server and `mcp__plugin_<plugin>_<server>__<tool>` for tools, which is the form to use in permission rules and hook matchers.

## Load without installing

- `claude --plugin-dir <path>` loads a directory, a `.zip`, or a folder whose subfolders each have a manifest, for one session; repeat it for more. `--plugin-url <url>` fetches a zip. `CLAUDE_CODE_PLUGIN_DIRS` lists paths when you can't pass a flag. These load as `<name>@inline`.
- `claude plugin init my-tool --with skills` scaffolds `~/.claude/skills/my-tool/`, which loads every session as `my-tool@skills-dir`. A project's `.claude/skills/<name>/` with a manifest loads for everyone after workspace trust, without monitors, MCP bundles or out-of-plugin MCP files.
- **Name conflicts,** by manifest name: managed `enabledPlugins` wins, then `--plugin-dir`/`--plugin-url`/`CLAUDE_CODE_PLUGIN_DIRS`, then installed marketplace plugins, then skills-directory plugins, then synced plugins. `"<name>@inline": false` stops a session-only copy from shadowing.

## Validate and test

- `claude plugin validate <path> --strict` checks the manifest and every skill, agent and command frontmatter, and fails on warnings in CI. Then `/reload-plugins`, the **Installed** and **Errors** tabs, and `claude plugin list` show what loaded. `claude --debug` logs dependency-install failures and `--plugin-dir` overrides.
- Common errors: `<component> path not found`, `path escapes plugin directory`, `skills/` placed inside `.claude-plugin/`, or `--plugin-dir` pointed at a marketplace root. Errors are indexed on the official troubleshooting page.
- **Evals** measure behavior. `claude plugin eval init` interviews you and writes cases under `evals/`, each a `prompt.md` plus `graders/*.md`, or a `case.yaml`. `claude plugin eval .` runs each case three times with the plugin and three times without, reporting `WITH`, `W/OUT` and `Δ` and an HTML report.

| Grader `type` | Passes when |
| :-- | :-- |
| `regex` | Pattern found in the target (`last_message` default, `trace`, `files`, a file, `mock_calls`) |
| `tool_used` | A tool was called between `min` and `max` times, optionally matching `input_match` |
| `tool_order` | The first `before` call precedes the first `after` call |
| `file_exists` | A file created during the run matches `path` |
| `llm` | A judge votes PASS on the rubric in at least two of three votes |
| `baseline` | A judge rates the run at least as good as a reference transcript |

In a two-arm run, `tool_used: Skill` graders, `mock_calls` graders on the plugin's own mocked servers, and graders marked `arm: with-only` count in neither arm (`arm: both` forces scoring). Runs are isolated: none of your settings, CLAUDE.md or MCP servers, and only read-only tools unless you grant more with `--allow-tools Write Edit "Bash(npm test *)"`. MCP servers are replaced by mock files under `evals/mocks/<server>/<tool>.md`. The first run in an untrusted directory asks `Trust this plugin directory?`; without a terminal, under `--json`, or with `CI` set it exits 1 unless you pass `--trust-plugin`. Runs and judge calls are billed to your account. In CI:

```bash
claude plugin eval . --trust-plugin --json results.json --threshold 0.8 \
  --model claude-sonnet-5 --judge-model claude-haiku-4-5 --no-publish --max-cost-usd 20
```

Exit 0 means every case met the threshold (default 1.0), 1 means a failure or load error, and 2 means a partial run.
