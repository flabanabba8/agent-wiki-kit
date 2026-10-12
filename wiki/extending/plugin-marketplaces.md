---
title: Plugin Marketplaces
type: how-to
tldr: "Create, host and publish a plugin catalog"
sources:
  - raw/docs/official/plugins__create-marketplace.md
  - raw/docs/official/plugins__host-marketplace.md
  - raw/docs/official/plugins__marketplace-reference.md
  - raw/docs/official/plugins__publish.md
  - raw/docs/official/plugins__dependencies.md
  - raw/docs/official/plugins__relevance.md
  - raw/docs/official/plugins__cli-hints.md
  - raw/docs/official/plugins__anthropic-marketplaces.md
  - raw/docs/official/plugins__security.md
  - raw/docs/official/plugins__loading.md
  - raw/docs/official/plugins__install.md
related: ["[[plugins]]", "[[enterprise-admin]]", "[[settings]]", "[[skills]]", "[[mcp]]"]
created: 2026-09-25
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [plugin-marketplace, marketplace-json, host-a-marketplace, publish-a-plugin, private-marketplace, plugin-release-channels, claude-code-hint]
---

# Plugin Marketplaces

A marketplace is a repository or directory with a `.claude-plugin/marketplace.json` catalog that lists plugins and where to fetch each one. It is a catalog, not a hosted store. This page is for people who publish and run one; installing, building and loading plugins are on [[plugins]], and org-wide allowlists and forced installs are on [[enterprise-admin]].

## Anthropic's marketplaces

| | Official | Community | Demo |
| :-- | :-- | :-- | :-- |
| Repository | `anthropics/claude-plugins-official` | `anthropics/claude-plugins-community` | `anthropics/claude-code` |
| Name after `@` | `claude-plugins-official` | `claude-community` | `claude-code-plugins` |
| How you get it | Added on the first interactive terminal session | `/plugin marketplace add anthropics/claude-plugins-community` | `/plugin marketplace add anthropics/claude-code` |

Official and community names are accepted only for marketplaces sourced from `github.com/anthropics/`; a marketplace using one of those names from anywhere else stops loading, along with its plugins. Every other marketplace is third-party and unreviewed. The community catalog pins nearly every entry to a commit SHA, and Claude Code refuses a different commit.

## Write the catalog

`name`, `owner` and `plugins` are required. Each entry needs `name` and `source`:

```json
{
  "name": "company-tools",
  "owner": { "name": "DevTools Team" },
  "plugins": [
    { "name": "code-formatter", "source": "./plugins/formatter" },
    { "name": "deploy-tools", "source": { "source": "github", "repo": "company/deploy-plugin" } }
  ]
}
```

| `source` | Fields | Notes |
| :-- | :-- | :-- |
| Relative path | the string | Inside the marketplace, starting `./`; bare names resolve under `metadata.pluginRoot` |
| `github` | `repo`, `ref`, `sha` | `sha` is a full 40-character commit and wins over `ref` |
| `url` | `url`, `ref`, `sha` | Any git repository |
| `git-subdir` | `url`, `path`, `ref`, `sha` | Sparse partial clone of one subdirectory |
| `npm` | `package`, `version`, `registry` | Fetched with your npm client; install scripts never run |
| `archive` | `url`, `sha256` | HTTPS zip; a `sha256` pin refuses a changed download |
| `command` | `command`, `timeout`, `mode` | A local command prints the plugin directory; users accept it first. `mode` is `copy` (default) or `link` |

- **Entry name vs manifest name:** the entry `name` is the install ID (`<entry>@<marketplace>`) and the `enabledPlugins` key; the `plugin.json` name is the skill prefix. Keep them the same.
- **`strict`:** `true` (default) keeps `plugin.json` authoritative and appends the entry's `commands`, `agents`, `skills`, `outputStyles` and `themes` (entry `hooks` replace the manifest's matchers per event). With `false`, an entry that declares any of those alongside a `plugin.json` is a conflict and the plugin fails to load. Without a `plugin.json`, the entry is the manifest.
- **Other entry fields:** `description`, `version`, `category`, `tags`, `displayName`, `defaultEnabled` (overrides the manifest), `dependencies`, `relevance`, `metadata`, `headers`, `headersHelper`.
- **Top-level extras:** `description`, `metadata.pluginRoot`, `renames`, `forceRemoveDeletedPlugins`, `allowCrossMarketplaceDependenciesOn`.
- **Reserved names:** the official and community names, impersonations of them (and any non-ASCII name), `inline`, `builtin`, `skills-dir`, `synced`, `npm`, `pip`, `uv`, `cargo`, `github`, `gh`, and names starting `claudeai-`.

Test locally with `claude plugin validate .` and `claude plugin marketplace add ./path`, then install from it.

## Host it

| Host | Users run | They need |
| :-- | :-- | :-- |
| GitHub | `/plugin marketplace add your-org/your-marketplace` | `git`, plus access for a private repo |
| Other git host | `/plugin marketplace add https://gitlab.example.com/team/plugins.git` | The full URL; `owner/repo` always means github.com |
| Hosted JSON | `/plugin marketplace add https://plugins.example.com/marketplace.json` | HTTPS only; relative-path entries fail, so use fetchable sources |
| Shared directory | `/plugin marketplace add /Volumes/shared/claude-plugins` | Read access; relative-path plugins load in place, so edits apply on the next session or `/reload-plugins` |

- Append `#<ref>` to pin a branch or tag. `claude plugin marketplace add your-org/your-marketplace --scope project`, committed, registers it for every teammate who trusts the folder.
- Keep plugin files out of Git LFS; clones leave LFS files as pointers.
- Symlinks inside a plugin survive caching; links to elsewhere in the same marketplace are dereferenced; links outside the marketplace are skipped.
- **Organization sync:** Team and Enterprise orgs can distribute through claude.ai **Organization settings > Plugins & skills**, which reads the repo through the org's GitHub or GitLab connection. On github.com and gitlab.com the repo must be private or internal, sources must be `github`, `url`, `git-subdir` or `./` paths, and a plugin with a top-level `bin/` is rejected.

### Private repositories

Claude Code runs `git` with prompts disabled and has no token of its own. `owner/repo` probes SSH first and falls back to HTTPS (`CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` skips the probe). SSH keys must work without a passphrase prompt and the host must be in `known_hosts`; HTTPS needs a credential already stored by a helper, such as `gh auth login` then `gh auth setup-git`. A `GITHUB_TOKEN` alone doesn't authenticate background checks. When a background check can't authenticate, Claude Code re-clones and keeps the old checkout if that fails; `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` skips the re-clone. `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` raises the 120-second clone timeout. For users without git accounts, use `archive` entries, public HTTPS git URLs, or a shared directory.

### Authenticated archive downloads

Set `headers`, or a `headersHelper` command for short-lived tokens, on the marketplace's `url` source or on one plugin entry (which must also set `"strict": false`). The helper prints one JSON object of headers and exits 0 within 10 seconds. An entry's helper runs only when a user installs or updates that one plugin and accepts the command (`--yes` or `--accept-command <sha256>` in scripts); bulk installs, dependency installs and auto-update refuse it. Managed `disableCommandPluginSources` blocks helpers except for marketplaces that managed settings declare.

## Release updates

Users get a new copy only when the computed version changes: `plugin.json` `version`, then the entry `version`, then the commit SHA (git sources) or archive digest. Either bump `version` every release or omit it everywhere; don't set it in both places.

- **Auto-update** is off for your marketplace until each user enables it under **Marketplaces** in `/plugin`, or an admin sets `autoUpdate` on a managed `extraKnownMarketplaces` entry. Otherwise users run `claude plugin update <plugin>@<marketplace>`.
- **Hold a version** with `ref`/`sha` on the entry or `#<ref>` on the add command.
- **Release channels:** host two marketplaces with different `name` values whose entries point at different refs, such as `stable-tools` and `latest-tools`.
- **Renames and removals:** never change a published `name`; change `displayName` instead. If you must, add a `renames` map (old name to new, or to `null` for removed), treat it as append-only, and run `claude plugin validate .`. `"forceRemoveDeletedPlugins": true` uninstalls removed plugins from user, project and local scopes.
- **Changed `command` sources** need each user to accept the new command via the `claude plugin update` shown in the Errors tab.

## Dependencies

```json
{ "name": "deploy-kit", "dependencies": ["audit-logger", { "name": "secrets-vault", "version": "~2.1.0" }] }
```

Bare names resolve in the same marketplace. A `version` range installs the highest `{plugin-name}--v{version}` git tag that satisfies it, so maintainers tag releases with `claude plugin tag --push`. Pre-releases match only with a suffix such as `^2.0.0-0`. A dependency from another marketplace installs only when the root marketplace lists it in `allowCrossMarketplaceDependenciesOn`, unless the user already has it enabled at that scope. A manifest holding only `name` and `dependencies` works as a team bundle. For local testing, load both plugins with `--plugin-dir`.

## Publish and promote

| Route | Who can install | Auto-updates |
| :-- | :-- | :-- |
| Send the folder or a `.zip` | People you give it to (`--plugin-dir`, `--plugin-url`, or `~/.claude/skills/`) | No |
| Your own marketplace | Anyone who can reach the repo | Off by default |
| Community marketplace | Anyone who adds it | Off by default |

Before release: pick a permanent kebab-case name, decide on versioning, run `claude plugin validate --strict`, install from a local marketplace, and fill in `description`, `author`, `homepage` and `repository`. Submit to the community marketplace through the claude.ai form (Team or Enterprise with the Directory permission) or the Console form; the official marketplace takes no submissions through these forms.

- **Relevance suggestions:** a `relevance` block on an entry (`topic`, and `signals` of `cwd`, `cli`, `hosts`, `filesRead` or `manifestDeps`) matches locally and suggests the plugin in a spinner tip, a session-start notice (for `cwd`) and the top of **Discover**. Users see suggestions only once an admin lists the marketplace in `pluginSuggestionMarketplaces`; nothing installs without confirmation.
- **CLI hints:** a CLI whose plugin is in an official-named marketplace can print `<claude-code-hint v="1" type="plugin" value="name@claude-plugins-official" />` on its own stderr line when `CLAUDECODE` or `CLAUDE_CODE_CHILD_SESSION` is set. Claude Code strips the line and, in interactive local sessions with analytics on, prompts once per plugin (one prompt per session).
