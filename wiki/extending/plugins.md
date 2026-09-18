---
title: Plugins and Marketplaces
type: reference
tldr: "Build, install, test and distribute plugins"
sources:
  - raw/docs/official/plugins.md
  - raw/docs/official/plugins-reference.md
  - raw/docs/official/discover-plugins.md
  - raw/docs/official/plugin-marketplaces.md
  - raw/docs/official/plugin-evals.md
  - raw/docs/official/plugin-dependencies.md
  - raw/docs/official/plugin-hints.md
  - raw/docs/official/plugin-relevance.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
related: ["[[skills]]", "[[subagents]]", "[[hooks]]", "[[mcp]]", "[[enterprise-admin]]", "[[settings]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [claude-plugins, plugin-marketplace, plugin-json, claude-plugin-eval, marketplace-json]
---

# Plugins and Marketplaces

A plugin is a self-contained directory that packages [[skills]], [[subagents]], [[hooks]], [[mcp]] servers, LSP servers, monitors and more, so one install brings the whole setup to another project or teammate. A marketplace is a catalog, `marketplace.json`, that lists plugins and where to fetch them. Start with standalone configuration in `.claude/` (skills named `/hello`), and convert it to a plugin (`/plugin-name:hello`) when you want to share or version it.

Plugins run arbitrary code with your user privileges. Install only plugins and marketplaces you trust.

## Install and manage

- The official marketplace `claude-plugins-official` is added automatically on first interactive launch; otherwise run `/plugin marketplace add anthropics/claude-plugins-official`. The reviewed community marketplace is added with `/plugin marketplace add anthropics/claude-plugins-community` and installed from as `@claude-community`.
- `/plugin` opens the manager with **Discover**, **Installed**, **Marketplaces**, **Errors** and **Stats** tabs. Plugin details show context cost and what will install.
- `/plugin install github@claude-plugins-official` asks for a scope. From the shell, `claude plugin install formatter@my-marketplace --scope project` does the same without a prompt.
- Closing the `/plugin` menu reloads plugins. For changes made elsewhere, run `/reload-plugins`, or `/reload-plugins --force` when it warns about invalidating the prompt cache.
- `claude plugin enable|disable|uninstall|update <plugin>@<marketplace>`, `claude plugin list --json` and `claude plugin details <name>` (component inventory and token cost) manage installs from the shell. `--json` prints one result object per run.
- Official marketplaces auto-update by default; third-party ones don't. Toggle auto-update per marketplace in `/plugin`. `DISABLE_AUTOUPDATER` stops updates, and adding `FORCE_AUTOUPDATE_PLUGINS=1` keeps plugin updates on.
- If skills don't appear, clear `~/.claude/plugins/cache`, restart and reinstall.

| Scope | Settings file |
| :-- | :-- |
| `user` (default) | `~/.claude/settings.json` |
| `project` | `.claude/settings.json` |
| `local` | `.claude/settings.local.json` |
| `managed` | Managed settings (read-only) |

To give a team the same plugins, commit `extraKnownMarketplaces` and `enabledPlugins` to `.claude/settings.json`. Teammates get the marketplace after trusting the folder, but plugins from external sources still need `claude plugin install`.

**Code intelligence plugins** (`typescript-lsp`, `pyright-lsp`, `gopls-lsp`, `rust-analyzer-lsp` and others) give Claude diagnostics after edits plus go-to-definition and references. The language server binary must be installed separately; `Executable not found in $PATH` in the Errors tab means it isn't.

## Create a plugin

```bash
mkdir -p my-first-plugin/.claude-plugin my-first-plugin/skills/hello
```

```json
{ "name": "my-first-plugin", "description": "A greeting plugin", "version": "1.0.0", "author": { "name": "Your Name" } }
```

Save the JSON as `my-first-plugin/.claude-plugin/plugin.json`, add `skills/hello/SKILL.md`, then run `claude --plugin-dir ./my-first-plugin` and invoke `/my-first-plugin:hello`. `--plugin-dir` also accepts a `.zip` or a folder of plugins, and repeats for several plugins. `--plugin-url` loads a hosted zip for one session. A local copy overrides an installed plugin of the same name.

`claude plugin init my-tool --with skills hooks` scaffolds `~/.claude/skills/my-tool/`, which loads automatically as `my-tool@skills-dir` with no install step. A project-scope skills-directory plugin loads only after workspace trust and doesn't run monitors.

| Path at plugin root | Holds |
| :-- | :-- |
| `.claude-plugin/plugin.json` | Manifest (optional; only this file goes in `.claude-plugin/`) |
| `skills/<name>/SKILL.md`, or one root `SKILL.md` | Skills |
| `commands/` | Flat-file skills |
| `agents/` | Subagents; `hooks`, `mcpServers` and `permissionMode` are ignored |
| `hooks/hooks.json` | Hook config, same format as settings |
| `.mcp.json` | MCP servers |
| `.lsp.json` | Language servers: `command` and `extensionToLanguage` required |
| `monitors/monitors.json` | Background commands whose stdout lines notify Claude; interactive CLI only |
| `bin/` | Executables added to the Bash tool's `PATH` |
| `settings.json` | Defaults; only `agent` and `subagentStatusLine` |
| `output-styles/`, `themes/`, `workflows/` | Output styles, color themes, workflow scripts |

A `CLAUDE.md` at the plugin root is not loaded; ship instructions as a skill.

**Manifest.** `name` (kebab-case) is the only required field and sets the namespace. Optional fields:

- Metadata: `displayName`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `metadata`, and `defaultEnabled` (`false` installs disabled).
- Component paths: `skills` adds to the default scan; `commands`, `agents`, `workflows` and `outputStyles` replace their defaults; `hooks`, `mcpServers` and `lspServers` accept paths or inline config. Paths start with `./` and can't leave the plugin.
- `userConfig`: values prompted at enable time, with `type`, `title`, `description` and optionally `sensitive` (kept in the keychain). They are available as `${user_config.KEY}` in MCP, LSP and exec-form hook config, and as `CLAUDE_PLUGIN_OPTION_<KEY>` to hooks. Shell-form hooks, monitors and `headersHelper` reject `${user_config.*}`.
- `channels`, `dependencies`, and the experimental `experimental.monitors`, `experimental.themes` and `experimental.evals`.

**Paths and data.** Marketplace plugins are copied into `~/.claude/plugins/cache`, so use `${CLAUDE_PLUGIN_ROOT}` for bundled files. Keep state in `${CLAUDE_PLUGIN_DATA}` (`~/.claude/plugins/data/{id}/`), which survives updates and is deleted on the last uninstall unless you pass `--keep-data`. When a plugin ships `package.json` with a bun or npm lockfile, dependencies install automatically with `--ignore-scripts`.

**Plugin MCP tool names** are `mcp__plugin_<plugin-name>_<server-name>__<tool>`, and the server is `plugin:<plugin-name>:<server-name>`.

## Validate and test

- `claude plugin validate ./my-plugin --strict` checks the manifest, `hooks/hooks.json` and frontmatter, and fails on warnings in CI. `claude --debug` shows loading errors. Directories must sit at the plugin root, and hook scripts must be executable.
- **Evals** measure behavior. `claude plugin eval init` interviews you and writes cases under `evals/`, each a `prompt.md` plus `graders/*.md`. `claude plugin eval .` runs each case three times with the plugin and three times without it, reporting `WITH`, `W/OUT` and `Δ` along with an HTML report.

| Grader `type` | Passes when |
| :-- | :-- |
| `regex` | Pattern found in the target (`last_message`, `trace`, `files`, a file's contents, `mock_calls`) |
| `tool_used` | A tool was called between `min` and `max` times, optionally matching `input_match` |
| `tool_order` | The `before` tool ran before the `after` tool |
| `file_exists` | A file created during the run matches `path` |
| `llm` | A judge model votes PASS on the rubric in 2 of 3 votes |
| `baseline` | A judge rates the run at least as good as a reference transcript |

A `tool_used: Skill` grader is excluded from scoring in both arms, so it doesn't inflate `Δ`. Runs are isolated, with none of your settings, CLAUDE.md or MCP servers loaded, and only read-only tools unless you grant more with `--allow-tools Write Edit "Bash(npm test *)"`. The plugin's MCP servers are replaced by mock files under `evals/mocks/<server>/<tool>.md`. Each run and judge call is billed to your account. In CI:

```bash
claude plugin eval . --trust-plugin --json results.json --threshold 0.8 \
  --model claude-sonnet-5 --judge-model claude-haiku-4-5 --no-publish --max-cost-usd 20
```

Exit 0 means every case met the threshold (default 1.0), 1 means a failure or load error, and 2 means a partial run.

## Distribute through a marketplace

`.claude-plugin/marketplace.json` at the repository root needs `name`, `owner` and `plugins`:

```json
{
  "name": "company-tools",
  "owner": { "name": "DevTools Team" },
  "plugins": [
    { "name": "code-formatter", "source": "./plugins/formatter" },
    { "name": "deployment-tools", "source": { "source": "github", "repo": "company/deploy-plugin" } }
  ]
}
```

| `source` | Fields |
| :-- | :-- |
| Relative path | `"./plugins/x"`, resolved from the marketplace root |
| `github` | `repo`, `ref`, `sha` |
| `url` | Git `url`, `ref`, `sha` |
| `git-subdir` | `url`, `path`, `ref`, `sha` (sparse clone) |
| `npm` | `package`, `version`, `registry` |
| `archive` | HTTPS zip `url`, `sha256` |
| `command` | Local command printing a plugin directory; users must accept it |

- Users add the marketplace with `/plugin marketplace add owner/repo`, a git URL (`#ref` to pin), a local path, or a URL to `marketplace.json`. Relative plugin paths don't resolve from URL-hosted marketplaces. From the shell, use `claude plugin marketplace add|list|remove|update`. Removing a marketplace uninstalls its plugins.
- **Versions:** Claude Code uses `plugin.json` `version`, then the marketplace entry `version`, then the git commit SHA, then the archive digest. With an explicit version, users get updates only when you bump it, so set it in one place only. For release channels, publish two marketplaces pointing at different refs.
- **`strict`:** `true` (default) makes `plugin.json` authoritative, with the entry adding to it. With `false`, the entry is the whole definition.
- **Former names:** a top-level `renames` map (old name to new name, or `null`) migrates existing installs.
- **Git LFS:** plugin and marketplace clones leave Git LFS files as pointers; `git lfs pull` in the checkout fetches them.
- **Private repositories** use your git credential helpers. For background updates, set `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` or configure `gh auth setup-git`. `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` raises the 120-second git timeout.
- **Containers:** pre-populate plugins at build time and point `CLAUDE_CODE_PLUGIN_SEED_DIR` at them; seeds are read-only.
- **Dependencies:** list them as `"dependencies": ["helper-lib", { "name": "secrets-vault", "version": "~2.1.0" }]`. Ranges resolve against `{plugin-name}--v{version}` git tags, which `claude plugin tag --push` creates. Cross-marketplace dependencies require `allowCrossMarketplaceDependenciesOn`. `claude plugin prune` removes orphaned dependencies. A manifest holding only dependencies bundles a team's plugin set.
- **Validate** with `claude plugin validate .`. Reserved names such as `claude-plugins-official` are rejected.

Submit to the community marketplace through the claude.ai or Console forms after `claude plugin validate` passes; the official marketplace is curated by Anthropic. A CLI whose plugin is in the official marketplace can print `<claude-code-hint v="1" type="plugin" value="name@claude-plugins-official" />` on its own stderr line when `CLAUDECODE` is set, which prompts the user to install once.

## Organization controls

Managed `strictKnownMarketplaces` allowlists marketplace sources (`[]` blocks all), `blockedMarketplaces` denies them, `disableCommandPluginSources` blocks command sources, and `enabledPlugins` in managed settings force-enables plugins. A marketplace entry's `relevance` signals (`cwd`, `cli`, `hosts`, `filesRead`, `manifestDeps`) suggest plugins only for marketplaces listed in `pluginSuggestionMarketplaces`. Distributing through claude.ai organization settings rejects plugins with a top-level `bin/`. Rollout is covered on [[enterprise-admin]] and settings keys on [[settings]].
