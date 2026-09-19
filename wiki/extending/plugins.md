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
  - raw/docs/changelog-2.1.275-to-2.1.278.md
related: ["[[skills]]", "[[subagents]]", "[[hooks]]", "[[mcp]]", "[[enterprise-admin]]", "[[settings]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [claude-plugins, plugin-marketplace, plugin-json, claude-plugin-eval, marketplace-json]
---

# Plugins and Marketplaces

A plugin is a self-contained directory packaging [[skills]], [[subagents]], [[hooks]], [[mcp]] servers, LSP servers, monitors and more, so one install brings the whole setup to another project or teammate. A marketplace is a catalog, `marketplace.json`, listing plugins and where to fetch them. Start with plain `.claude/` configuration (a skill named `/hello`) and convert it to a plugin (`/plugin-name:hello`) to share or version it.

Plugins run arbitrary code with your user privileges, so install only ones you trust.

## Install and manage

- The official marketplace `claude-plugins-official` is added automatically on first interactive launch; otherwise run `/plugin marketplace add anthropics/claude-plugins-official`. The reviewed community marketplace is `anthropics/claude-plugins-community`, installed from as `@claude-community`.
- `/plugin` opens the manager (**Discover**, **Installed**, **Marketplaces**, **Errors**, **Stats**), showing each plugin's context cost and what will install.
- `/plugin install github@claude-plugins-official` asks for a scope. From the shell, `claude plugin install formatter@my-marketplace --scope project` does the same without a prompt. To install from a marketplace you haven't added, pass the source with `--marketplace`, as in `/plugin install quality-review-plugin --marketplace your-org/plugins`: Claude Code shows the resolved source and asks before adding it, and the plugin name goes in bare.
- Closing the `/plugin` menu reloads plugins; for changes made elsewhere run `/reload-plugins`, or `/reload-plugins --force` when it warns about invalidating the prompt cache.
- From the shell: `claude plugin enable|disable|uninstall|update <plugin>@<marketplace>`, `claude plugin list --json`, and `claude plugin details <name>` for a component inventory and token cost.
- Official marketplaces and claude.ai-hosted ones auto-update by default; other third-party and local ones don't. Toggle it per marketplace in `/plugin`. `DISABLE_AUTOUPDATER` stops updates, and adding `FORCE_AUTOUPDATE_PLUGINS=1` keeps plugin updates on.
- If skills don't appear, clear `~/.claude/plugins/cache` and reinstall.

Install scopes map to settings files: `user` (the default) to `~/.claude/settings.json`, `project` to `.claude/settings.json`, `local` to `.claude/settings.local.json`, and `managed` to read-only managed settings.

To give a team the same plugins, commit `extraKnownMarketplaces` and `enabledPlugins` to `.claude/settings.json`. Teammates get the marketplace after trusting the folder, but plugins from external sources still need `claude plugin install`.

### Plugins synced from claude.ai

The plugins enabled for your claude.ai account, including ones your organization turns on, load alongside your marketplace installs, at the same trust: Claude Code downloads each into `~/.claude/plugins/synced/` and loads it as `<name>@synced`, with no marketplace and no install record.

- Cowork and cloud sessions download them at session start. A terminal session signed in with that account checks once per launch in the background, adding, updating and removing plugins and showing `Plugins changed. Run /reload-plugins to activate.`
- `claude plugin list` groups them under `Synced from claude.ai`; the `/plugin` **Installed** tab shows `synced` as their source.
- `claude plugin disable <name>@synced` writes `"<name>@synced": false` to your user `enabledPlugins`, unless your organization marks the plugin required. `install`, `update` and `uninstall` don't apply: turn it off on claude.ai and the next sync removes it.
- `syncClaudeAiPlugins: false` in user or managed settings stops syncing and moves synced plugins to `~/.claude/plugins/.trash/`; so does turning off Skills for the organization.
- An enabled plugin of the same name from any other source wins, and the synced copy reports as not loaded.

Marketplaces hosted on claude.ai, such as an organization's plugin library, appear under `From claude.ai:` in `claude plugin marketplace list` and in the `/plugin` **Marketplaces** tab. `claude plugin marketplace add --claudeai claudeai-organization-library` registers one under its `claudeai-` name; it refuses `--scope` and `--sparse` because it is hosted for your account rather than declared in settings, auto-updates, and keeps no local clone. `strictKnownMarketplaces` and `blockedMarketplaces` match it by a `hostPattern` for `claude.ai`, which doesn't admit personal uploads.

**Code intelligence plugins** (`typescript-lsp`, `pyright-lsp`, `gopls-lsp`, `rust-analyzer-lsp` and others) give Claude diagnostics after edits plus go-to-definition and references. Install the language server binary separately; `Executable not found in $PATH` in the Errors tab means it is missing.

## Create a plugin

```bash
mkdir -p my-first-plugin/.claude-plugin my-first-plugin/skills/hello
```

```json
{ "name": "my-first-plugin", "description": "A greeting plugin", "version": "1.0.0", "author": { "name": "Your Name" } }
```

Save the JSON as `my-first-plugin/.claude-plugin/plugin.json`, add `skills/hello/SKILL.md`, then run `claude --plugin-dir ./my-first-plugin` and invoke `/my-first-plugin:hello`. `--plugin-dir` also accepts a `.zip` or a folder of plugins and repeats; `--plugin-url` loads a hosted zip for one session. A local copy overrides an installed plugin of the same name.

`claude plugin init my-tool --with skills hooks` scaffolds `~/.claude/skills/my-tool/`, which loads as `my-tool@skills-dir` with no install step. A project-scope one loads only after workspace trust and runs no monitors.

| Path at plugin root | Holds |
| :-- | :-- |
| `.claude-plugin/plugin.json` | Manifest (optional; the only file that goes there) |
| `skills/<name>/SKILL.md`, or one root `SKILL.md` | Skills |
| `commands/` | Flat-file skills |
| `agents/` | Subagents; `hooks`, `mcpServers` and `permissionMode` ignored |
| `hooks/hooks.json` | Hook config, same format as settings |
| `.mcp.json`, `.lsp.json` | MCP servers; language servers (`command` and `extensionToLanguage` required) |
| `monitors/monitors.json` | Background commands whose stdout notifies Claude; interactive CLI only |
| `bin/` | Executables added to the Bash tool's `PATH` |
| `settings.json` | Defaults; only `agent` and `subagentStatusLine` |
| `output-styles/`, `themes/`, `workflows/` | Output styles, color themes, workflow scripts |

A `CLAUDE.md` at the plugin root is not loaded; ship instructions as a skill.

**Manifest.** `name` (kebab-case) is the only required field and sets the namespace. Optional fields:

- Metadata: `$schema`, `displayName`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `metadata`, and `defaultEnabled` (`false` installs disabled).
- Component paths: `skills` adds to the default scan; `commands`, `agents`, `workflows` and `outputStyles` replace their defaults; `hooks`, `mcpServers` and `lspServers` accept paths or inline config. Paths start with `./` and can't leave the plugin.
- `userConfig`: values prompted at enable time, with `type`, `title`, `description` and optionally `sensitive` (kept in the keychain). They are available as `${user_config.KEY}` in MCP, LSP and exec-form hook config, and as `CLAUDE_PLUGIN_OPTION_<KEY>` to hooks. Shell-form hooks, monitors and `headersHelper` reject them.
- `channels`, `dependencies`, and the experimental `experimental.monitors`, `experimental.themes` and `experimental.evals`.

**Paths and data.** Marketplace plugins are copied into `~/.claude/plugins/cache`, so use `${CLAUDE_PLUGIN_ROOT}` for bundled files; it changes on each update. The variables reach hook processes and MCP and LSP subprocesses but not Bash commands, so write the placeholder in plugin content instead. Keep state in `${CLAUDE_PLUGIN_DATA}` (`~/.claude/plugins/data/{id}/`), which survives updates and is deleted on the last uninstall unless you pass `--keep-data`.

Two kinds of plugin load in place rather than being copied: a `command` source in link mode, and a relative-path source in a marketplace added from a local directory. For the latter, edits to the source directory apply at the next session start or `/reload-plugins` with no version bump, `CLAUDE_PLUGIN_ROOT` points at that stable directory, and no Node.js dependencies are installed there.

A plugin shipping `package.json` with a bun or npm lockfile gets its dependencies installed with `--ignore-scripts`; a yarn or pnpm lockfile, or a `bunfig.toml` beside a bun lockfile, skips the install with a debug-log warning.

**Plugin MCP tool names** are `mcp__plugin_<plugin>_<server>__<tool>`, and the server is `plugin:<plugin>:<server>`.

## Validate and test

- `claude plugin validate ./my-plugin --strict` checks the manifest, `hooks/hooks.json` and frontmatter, failing on warnings in CI; `claude --debug` shows loading errors. Directories must sit at the plugin root, and hook scripts must be executable.
- **Evals** measure behavior. `claude plugin eval init` interviews you and writes cases under `evals/`, each a `prompt.md` plus `graders/*.md`. `claude plugin eval .` runs each case three times with the plugin and three times without it, reporting `WITH`, `W/OUT` and `Δ` along with an HTML report.

| Grader `type` | Passes when |
| :-- | :-- |
| `regex` | Pattern found in the target (`last_message`, `trace`, `files`, a file's contents, `mock_calls`) |
| `tool_used` | A tool was called between `min` and `max` times, optionally matching `input_match` |
| `tool_order` | The `before` tool ran before the `after` tool |
| `file_exists` | A file created during the run matches `path` |
| `llm` | A judge model votes PASS on the rubric in 2 of 3 votes |
| `baseline` | A judge rates the run at least as good as a reference transcript |

A `tool_used: Skill` grader is excluded from scoring in both arms, so it doesn't inflate `Δ`. Runs are isolated, with none of your settings, CLAUDE.md or MCP servers loaded, and only read-only tools unless you grant more with `--allow-tools`. The plugin's MCP servers are replaced by mocks under `evals/mocks/<server>/<tool>.md`, and every run and judge call is billed to your account. In CI:

```bash
claude plugin eval . --trust-plugin --json results.json --threshold 0.8 \
  --model claude-sonnet-5 --judge-model claude-haiku-4-5 --no-publish --max-cost-usd 20
```

Exit 0 means every case met the threshold (default 1.0), 1 a failure or load error, 2 a partial run.

## Distribute through a marketplace

`.claude-plugin/marketplace.json` at the repository root needs `name`, `owner` and `plugins`:

```json
{ "name": "company-tools", "owner": { "name": "DevTools Team" }, "plugins": [
  { "name": "code-formatter", "source": "./plugins/formatter" },
  { "name": "deployment-tools", "source": { "source": "github", "repo": "company/deploy-plugin" } }
] }
```

| `source` | Fields |
| :-- | :-- |
| Relative path | `"./plugins/x"`, resolved from the marketplace root |
| `github` | `repo`, `ref`, `sha` |
| `url` | Git `url`, `ref`, `sha` |
| `git-subdir` | `url`, `path`, `ref`, `sha` (sparse clone) |
| `npm` | `package`, `version`, `registry`; fetched and unpacked with install scripts disabled |
| `archive` | HTTPS zip `url`, `sha256` |
| `command` | Local command printing a plugin directory; users must accept it |

- Users add the marketplace with `/plugin marketplace add owner/repo`, a git URL (`#ref` to pin), a local path, or a URL to `marketplace.json`; relative plugin paths don't resolve from a URL-hosted one. From the shell, `claude plugin marketplace add|list|remove|update`. Removing a marketplace uninstalls its plugins.
- **Versions:** Claude Code uses `plugin.json` `version`, then the marketplace entry `version`, then the git commit SHA, then the archive digest, then `unknown`. With an explicit version, users get updates only when you bump it — except for a `command` source or a plugin loaded in place — so set it in one place. For release channels, publish two marketplaces pointing at different refs.
- **`strict`:** `true` (default) makes `plugin.json` authoritative, the entry adding to it; `false` makes the entry the whole definition. A top-level `renames` map (old name to new, or `null`) migrates existing installs.
- **Git LFS:** plugin and marketplace clones leave LFS files as pointers, so keep what a plugin needs out of LFS.
- **Private repositories** use your git credential helpers, except the background refresh: it checks the remote for new commits with helpers disabled, then re-clones when it finds commits or can't authenticate. Set `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` to keep the existing checkout instead of re-cloning, configure `gh auth setup-git`, or add a git URL rewrite so the check authenticates itself. `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` raises the 120-second git timeout.
- **Containers:** pre-populate plugins at build time and point `CLAUDE_CODE_PLUGIN_SEED_DIR` at them; seeds are read-only and never auto-update.
- **Dependencies:** list them as `"dependencies": ["helper-lib", { "name": "secrets-vault", "version": "~2.1.0" }]`. Ranges resolve against `{plugin-name}--v{version}` git tags that `claude plugin tag --push` creates, cross-marketplace dependencies require `allowCrossMarketplaceDependenciesOn`, and `claude plugin prune` removes orphans. A manifest holding only dependencies bundles a team's plugin set.
- **Validate** with `claude plugin validate .`. Reserved marketplace names are rejected, including `claude-plugins-official` and, in any casing, `npm`, `pip`, `uv`, `cargo`, `github`, `gh`.

Submit to the community marketplace through the claude.ai or Console forms after `claude plugin validate` passes; the official marketplace is curated by Anthropic. A CLI whose plugin is official can print `<claude-code-hint v="1" type="plugin" value="name@claude-plugins-official" />` on its own stderr line when `CLAUDECODE` is set, prompting the user to install once.

## Organization controls

Managed `strictKnownMarketplaces` allowlists marketplace sources (`[]` blocks all, and it doesn't cover synced plugins, which `syncClaudeAiPlugins: false` stops), `blockedMarketplaces` denies them, `disableCommandPluginSources` blocks command sources, and `enabledPlugins` force-enables plugins. A marketplace entry's `relevance` signals (`cwd`, `cli`, `hosts`, `filesRead`, `manifestDeps`) suggest plugins only for marketplaces in `pluginSuggestionMarketplaces`. Distributing through claude.ai organization settings rejects plugins with a top-level `bin/`. Rollout: [[enterprise-admin]]; settings keys: [[settings]].
