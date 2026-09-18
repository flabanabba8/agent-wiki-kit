---
title: Settings Files and Precedence
type: reference
tldr: "Settings files, scopes, precedence, keys"
sources:
  - raw/docs/official/settings.md
  - raw/docs/official/settings-reference.md
  - raw/docs/official/managed-settings.md
  - raw/docs/official/debug-your-config.md
  - raw/docs/official/llm-gateway-connect.md
related: ["[[enterprise-admin]]", "[[permissions-and-modes]]", "[[environment-variables]]", "[[hooks]]", "[[troubleshooting]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [settings-json, settings-precedence, settings-scopes, claude-config-files, settings-local-json]
---

# Settings Files and Precedence

Settings are JSON keys that control Claude Code: the starting model, what it can run without asking, which files it can't read, how the terminal looks, and what your organization enforces. The terminal, the VS Code and JetBrains extensions and the desktop app all read the same files. This page covers where settings live, which value wins, and how to check what loaded. The permission rule syntax is on [[permissions-and-modes]], and org-wide delivery is on [[enterprise-admin]].

## The files

| Scope | File | Applies to | Use for |
|---|---|---|---|
| User | `~/.claude/settings.json` | You, every project on this machine | Theme, editor mode, default model, personal permission rules |
| Shared project | `.claude/settings.json` | Everyone using the folder; commit it | Team permissions, hooks, plugins, project env vars |
| Project local | `.claude/settings.local.json` | You, this project only | Personal overrides, testing before sharing |
| Managed | `managed-settings.json`, MDM/registry policy, or server-managed settings | Everyone your org deploys to | Security policy and compliance |

On Windows, `~/.claude` is `%USERPROFILE%\.claude`. `CLAUDE_CONFIG_DIR` moves the home-directory files elsewhere. Installing Claude Code creates no settings file. Claude Code writes the user file the first time you change a `/config` option, and writes the local file the first time you choose "Yes, and don't ask again" on a permission prompt.

A fifth file, `~/.claude.json`, belongs to Claude Code itself. It holds your sign-in session, MCP server configs, per-project trust state and the *global config* keys (`autoConnectIde`, `autoInstallIdeExtension`, `copyOnSelect`, `diffTool`, `externalEditorContext`, `permissionExplainerEnabled`, `teammateDefaultModel`).

### The local file

- The first time Claude Code writes `.claude/settings.local.json` in a git repo, it adds `**/.claude/settings.local.json` to your global git excludes. If you create the file by hand, add it to `.gitignore` yourself.
- In a subdirectory of a repo, Claude Code reads and writes the local file at the repository root; in a worktree, at the main checkout's root. It stays next to `.claude/settings.json` outside git, on Windows, when the repo root is your home directory, or when you don't own the root.
- An untracked local file's `allow` rules apply without workspace trust. A tracked one needs trust like the shared file.
- The shared `.claude/settings.json` is read from the session's primary working directory, so start Claude Code at the repo root to pick up a root-level file.

## Changing a setting

- **`/config`**: the Config tab lists personal options only (theme, editor mode, verbose and similar). You can also set one directly: `/config verbose=true`. Most options save to the user file, a few (such as Show tips) to the local file, and global config options to `~/.claude.json`. `/config` isn't available in the VS Code chat panel or the desktop app.
- **Edit the JSON.** Files are strict JSON, with no comments and no trailing commas. Add `"$schema": "https://json.schemastore.org/claude-code-settings.json"` for editor autocomplete. The schema can lag new keys.
- **One session only:** `claude --settings '{"model": "claude-opus-4-8"}'` (inline JSON or a file path), a dedicated flag such as `--model` or `--effort`, or the key's paired environment variable such as `ANTHROPIC_MODEL`.

Claude Code watches settings files and hot-reloads most edits (including `permissions`, `hooks` and `apiKeyHelper`), firing a `ConfigChange` hook for each file change ([[hooks]]). `model`, `effortLevel` and `modelSettings` are read at session start; switch mid-session with `/model` or `/effort` instead. Managed settings from MDM or the console arrive on their own schedule.

## Precedence

From highest to lowest:

1. **Managed settings.** Nothing overrides them, not even `--settings`. A managed `model` only sets the starting model; to restrict choice, use `availableModels`.
2. **Command-line arguments**, including `--settings`, which merges key by key with the files below.
3. **Project local** (`.claude/settings.local.json`).
4. **Shared project** (`.claude/settings.json`).
5. **User** (`~/.claude/settings.json`).

Environment variables are not a level in this stack. Each variable/key pair decides on its own: `ANTHROPIC_MODEL` beats the `model` key from any file, while `ANTHROPIC_DEFAULT_MODEL` applies only when no file sets `model` ([[environment-variables]]). An `env` block inside a settings file is an ordinary key, and a settings-file `env` value beats a shell export of the same variable.

### Merge rules

- **Lists merge** across files. `permissions.allow` from every scope combines, so a lower scope can add entries but not remove them.
- `fallbackModel` is taken whole from the highest file that defines it.
- `modelPicker` is taken whole from the highest of managed, `--settings` or user settings, and is ignored in project and local files.
- A managed `availableModels` is applied as-is, ignoring user, project and local entries.
- `modelSettings` resolves per model together with `effortLevel`.

### Stricter values that beat managed settings

| Key | Honored value |
|---|---|
| `disableClaudeAiConnectors` | `true` from any scope |
| `enableArtifact` | `false` (or `disableArtifact: true`) from any scope |
| `isolatePeerMachines` | `true` from any scope |
| `remoteControlAtStartup` | `false` from project or local |
| `crossSessionInbound` | A stricter value (`accept` < `hold` < `refuse`) from project or local |
| `useAutoModeDuringPlan`, `syncClaudeAiSkills` | `false` from managed, `--settings`, user or local |
| `maxEffortLevel` | The lowest cap from any scope |

### Keys that don't apply from a repository file

- Keys whose Scope is `User or managed`, `User, local, or managed`, `Managed` or `Global config` in the settings index never apply from `.claude/settings.json`.
- `permissions.defaultMode` values `auto` and `bypassPermissions` don't take effect from project or local files.
- `permissions.allow`, `permissions.additionalDirectories`, `extraKnownMarketplaces` and most `env` values wait until each teammate trusts the folder. `deny` and `ask` rules apply immediately.
- A project `env` block applies only after first-run setup and the trust prompt, so a gateway credential placed there doesn't stop the login screen.

## Settings in cloud sessions

Cloud sessions on [[claude-code-on-the-web]] run on a fresh clone:

- They read the committed `.claude/settings.json`.
- They don't read user or local files.
- They receive only server-managed settings.
- On the web, `/config` opens claude.ai settings. To change a value, set environment variables on the cloud environment or commit the key.

## Check what loaded

- **`/status`** → the Status tab's `Setting sources` line lists each file loaded, such as `User settings` or `Project local settings`, and names the managed source in parentheses. It doesn't show which file supplied each key.
- **`claude doctor`** (from your shell) prints read-only installation and settings diagnostics, including entries Claude Code rejected, without starting a session. **`/doctor`** inside a session runs a fuller checkup that proposes fixes.
- **Broken files:** a *Settings Error* (invalid JSON or schema) opens a dialog to fix, exit or continue without the file. A *Settings Warning* skips only the bad entries. A broken `~/.claude.json` is copied to `~/.claude/backups/.claude.json.corrupted.<timestamp>`, and the five most recent `.claude.json.backup.<timestamp>` files let you restore it. `-p` runs show no dialog; run `claude doctor` afterwards.
- If a change made inside Claude Code doesn't persist, your user settings file is probably read-only or generated by another tool.

More symptom-driven checks are on [[troubleshooting]].

## Key catalogue

`settings-reference.md` documents every key with its scope, type, default and an example, grouped as follows (representative keys shown):

| Group | Examples |
|---|---|
| Model and responses | `model`, `availableModels`, `enforceAvailableModels`, `fallbackModel`, `modelOverrides`, `modelPicker`, `effortLevel`, `maxEffortLevel`, `fastMode`, `advisorModel`, `outputStyle`, `promptCacheTtl` |
| Permissions | `permissions.allow`/`ask`/`deny`, `permissions.defaultMode`, `permissions.additionalDirectories`, `permissions.disableBypassPermissionsMode`, `autoMode`, `disableAutoMode`, `allowManagedPermissionRulesOnly` |
| Sandbox | `sandbox.enabled`, `sandbox.filesystem.*`, `sandbox.network.allowedDomains`, `sandbox.credentials` |
| Memory and context | `autoCompactEnabled`, `autoCompactWindow`, `autoMemoryEnabled`, `claudeMd`, `claudeMdExcludes`, `env`, `fileCheckpointingEnabled` |
| Interface and terminal | `theme`, `editorMode`, `statusLine`, `spinnerTipsEnabled`, `companyAnnouncements`, `voiceEnabled`, `verbose` |
| Git and attribution | `attribution.commit`, `attribution.pr`, `includeGitInstructions`, `prUrlTemplate` |
| Hooks and automation | `hooks`, `disableAllHooks`, `allowManagedHooksOnly`, `allowedHttpHookUrls`, `enableWorkflows` |
| Plugins, skills, MCP | `enabledPlugins`, `extraKnownMarketplaces`, `strictKnownMarketplaces`, `allowedMcpServers`, `deniedMcpServers`, `managedMcpServers` |
| Authentication and providers | `apiKeyHelper`, `awsAuthRefresh`, `awsCredentialExport`, `gcpAuthRefresh`, `forceLoginMethod`, `forceLoginOrgUUID`, `otelHeadersHelper` |
| Updates and versioning | `autoUpdatesChannel`, `minimumVersion`, `requiredMinimumVersion`, `requiredMaximumVersion` |
| Privacy and telemetry | `cleanupPeriodDays`, `desktopSessionCleanupPeriodDays`, `feedbackSurveyRate`, `skipWebFetchPreflight` |
| Enterprise and managed | `managedSourcesBehavior`, `parentSettingsBehavior`, `policyHelper`, `forceRemoteSettingsRefresh`, `disableSideloadFlags`, `wslInheritsWindowsSettings` |

Managed-only keys and delivery are described on [[enterprise-admin]]. Environment variables have their own list on [[environment-variables]].
