---
title: Cloud Sessions, Remote Control and Mobile
type: reference
tldr: "Cloud sessions, teleport, Remote Control, mobile"
sources:
  - raw/docs/official/claude-code-on-the-web.md
  - raw/docs/official/web-quickstart.md
  - raw/docs/official/cloud-environments.md
  - raw/docs/official/remote-control.md
  - raw/docs/official/mobile.md
  - raw/docs/official/commands.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
  - raw/docs/changelog-2.1.275-to-2.1.282.md
related: ["[[desktop-app]]", "[[ci-cd-and-code-review]]", "[[slack-and-claude-tag]]", "[[routines-and-scheduling]]", "[[hooks]]", "[[channels]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
valid_until: 2027-03-15
aliases: [cloud-sessions, cloud-session, claude-code-on-the-web, claude-teleport, remote-control, claude-code-mobile, cloud-environments]
---

# Cloud Sessions, Remote Control and Mobile

A cloud session is a Claude Code session running on cloud infrastructure instead of your machine; Remote Control steers a local session from elsewhere.

| | Cloud session | Local session with Remote Control |
|---|---|---|
| Code runs on | Cloud VM, Anthropic-managed by default | Your machine |
| Start it from | claude.ai/code ("Claude Code on the web"), the mobile Code tab, Desktop with **Cloud** selected, `claude --cloud`, routines | Your terminal, the VS Code extension, or the Desktop app |
| You chat from | claude.ai, the mobile app, or Desktop | claude.ai or the mobile app, plus where you started it |
| Uses your local config | No, only what's in the repo | Yes |
| Requires GitHub | Yes, or a local repo bundled with `--cloud` | No |
| Keeps running if you disconnect | Yes | While the session stays open on your machine |
| Permission modes | Accept edits, Plan, Auto | Manual, Accept edits, Plan (from claude.ai and mobile) |
| Network | Configurable per environment | Your machine's network |

Both require a claude.ai account; neither works with a Console API key or through Bedrock, Agent Platform or Foundry. Chat events into a local session: [[channels]]. Scheduled cloud runs: [[routines-and-scheduling]]. For Claude to start and track many cloud sessions for one body of work, see [[claude-projects]].

## Cloud sessions

Available on Pro, Max and Team plans, and for Enterprise users with premium or Chat + Claude Code seats; Zero Data Retention organizations can't use it. Sessions share your plan's rate limits, with no separate compute charge.

### Connect GitHub

- **Claude GitHub App**, via browser onboarding at claude.ai/code: all public repos, plus private repos where the App is installed. Also enables PR auto-fix.
- **`/web-setup`** in the CLI: every repo your `gh auth token` can access; sends that token to your Claude account. On Team/Enterprise, an Owner must turn on **Quick web setup** first; where an admin disabled cloud sessions it returns `Cloud sessions are disabled by your organization's policy`.
- Project threads need the Claude GitHub App on each repository they clone, whichever method you used.

On Team and Enterprise the Owner also enables the GitHub connector under Admin settings > Connectors. Onboarding creates a **Default** environment with Trusted network access. Project threads need the Claude GitHub App on every repository they clone.

### How a session runs

1. The repo is cloned into a fresh Ubuntu 24.04 x86_64 VM; the environment's setup script runs.
2. Network access follows the environment's access level.
3. Claude works; watch and steer, or leave it.
4. Claude pushes a branch. Review the diff (against the base branch, or any branch via **Compare against**), leave inline comments, then **Create PR** (full, draft, or GitHub's compose page). For CI and review-comment watching, use auto-fix ([[ci-cd-and-code-review]]). A running session can attach another repository, even from a different GitHub owner.

Pre-fill a new session with claude.ai/code URL parameters `prompt` (`q`), `prompt_url`, `repositories` (`repo`) and `environment`.

### From terminal to cloud: `--cloud`

```bash
claude --cloud "Fix the authentication bug in src/auth/login.ts"
claude -p "your message" --cloud <session-id>   # queue a follow-up, then exit
```

- `--cloud` clones your GitHub remote at the current branch, not your local checkout, so push first. Each call creates a separate session; several run in parallel.
- With no git remote, or no Claude GitHub App on its github.com repo, Claude Code bundles the local repo: full history plus uncommitted changes to tracked files, but not untracked files or uncommitted credential-like files (`.env`, `*.tfvars`, `id_rsa`, `*.pem`), under 100 MB. `CCR_FORCE_BUNDLE=1` always bundles, which also runs GitLab or Bitbucket repos, though results can't be pushed back.
- Follow-ups accept a bare `session_...`/`cse_...` ID or a claude.ai/code URL. `--output-format json` returns `{ok, session_id, url}`. The org's `allow_remote_sessions` policy must be on.

### From cloud to terminal: teleport

`claude --teleport` (a picker), `claude --teleport <session-id>`, `/teleport` (alias `/tp`) inside a session, or `t` in `/tasks` pulls a cloud session into your terminal. It needs a clean git state (prompting a stash), the same repository rather than a fork, the branch pushed (fetched and checked out), and the same account — API-key auth fails with `Unable to get organization UUID`, so run `/login`.

The terminal gets its own copy; local work doesn't sync back, and `--resume` lists only local history. Desktop's **Continue in** menu sends a local session the other way ([[desktop-app]]).

### Inside a cloud session

- **Commands**: text-output ones such as `/compact` and `/context` work, `/clear` doesn't, and picker commands take an argument, e.g. `/model sonnet`. `/config` opens your claude.ai settings instead of setting a value: change a setting through an environment variable, or commit it to the repo's `.claude/settings.json` in a single-repository session. A message you send while Claude works queues until read; its ✕ takes it back into the message box.
- **Subagents and teams**: subagents in `.claude/agents/` work; agent teams need `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in the environment.
- **Compaction**: the session sets `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` itself, overriding the environment's value, so compaction triggers partway through the window; `CLAUDE_CODE_AUTO_COMPACT_WINDOW` changes the window size.
- **Session links**: commits get a `Claude-Session: <url>` trailer and PR bodies the session URL unless `attribution.sessionUrl` is `false`; the ID is in `CLAUDE_CODE_REMOTE_SESSION_ID`.
- **Sharing**: Private or Team on Team and Enterprise, Private or Public on Pro and Max — check for secrets first. Archiving hides a session, deleting is permanent.
- **Expiry**: idle sessions stop and their VM is reclaimed; waiting for you to approve or sign in to an MCP connector counts as idle. Reopening restores the conversation on a fresh VM, losing running subagents and shell jobs.

## Cloud environments

An environment is a saved configuration used wherever a cloud session starts: claude.ai/code, `claude --cloud`, Desktop, mobile, routines and Claude Tag. Project threads use the environment in the project's settings. Edit one with the cloud icon above the message box at claude.ai/code; environments archive but don't delete. `/remote-env` sets the CLI default, saved as `remote.defaultEnvironmentId`.

Access levels: **None** (no outbound traffic), **Trusted** (default: package registries, GitHub, cloud SDKs), **Full** (any domain), or **Custom** (your domain list, at least one, with `*.` for subdomains, optionally plus the defaults).

Every level still reaches GitHub (via proxy), MCP connectors, API-credential hosts and the Anthropic API. Other settings:

- **Environment variables**: `.env` format, copied in at session start and readable by anyone using the environment, so no secrets.
- **API credentials** (Pro and Max, admin required): the agent proxy adds the key for the hosts you list after requests leave the VM, so Claude never sees it; never attached to GitHub, the Anthropic API, public registries or setup scripts.
- **GitHub proxy**: credentials stay outside the VM, `git push` reaches only the session's own branch, only a pinned set of GraphQL operations is allowed, and `gh` needs no setup because `GH_TOKEN` and `GITHUB_TOKEN` read as `proxy-injected`.
- **Pre-installed tools**: Python, Node.js 20/21/22, Ruby, PHP 8.3, OpenJDK 21, Go, Rust, GCC/Clang, Docker, PostgreSQL 16 and Redis 7.0 (installed, not running), `gh`, `jq` and ripgrep; ask Claude to run `check-tools` for versions.
- **Resources**: about 4 vCPUs, 16 GB RAM, 30 GB disk; heavier jobs need Remote Control or a self-hosted environment.

### Shared environments

A setup script runs as root in Bash before Claude Code launches, must exit 0 and should finish in about five minutes. The resulting filesystem is snapshotted and reused until the script or allowed hosts change or about seven days pass.

A SessionStart hook lives in the repo, runs after launch on every start and resume, and works locally too. Use setup scripts for toolchains, hooks for project setup ([[hooks]]); to run a hook only in the cloud, exit early unless `CLAUDE_CODE_REMOTE` is `true`.

### What carries over

The fresh clone carries the repo's `CLAUDE.md`, `.claude/rules/`, `.claude/skills/`, `.claude/agents/` and `.claude/commands/`, and your organization's server-managed settings. Hooks and permission rules in `.claude/settings.json` and `.mcp.json` servers apply only in a session with one repository; a multi-repository session starts above the clones and reads neither. Skills enabled on your claude.ai account load too.

Not carried over: plugins a repo enables in `.claude/settings.json` (including from its `extraKnownMarketplaces`), `~/.claude/CLAUDE.md`, user-level skills and agents, plugins enabled only in user settings, MCP servers added at local or user scope (use `claude mcp add --scope project`), device MDM policy, and interactive logins such as AWS SSO.

A session with several repositories starts above the clones: from each repository's `.claude/settings.json` it takes only the plugins and marketplaces declared there, not hooks, permission rules or `env`, and reads no `.mcp.json`. A repo SessionStart hook doesn't run either; use a setup script instead.

Not carried over: `~/.claude/CLAUDE.md`, user-level skills, agents and plugins, MCP servers added at local or user scope (use `claude mcp add --scope project`), device MDM policy, and interactive logins such as AWS SSO.

## Remote Control

Remote Control connects claude.ai/code or the Claude app to a local session. Code and files stay local; the conversation syncs through Anthropic over outbound HTTPS only, no inbound ports.

**Requirements**: any plan, with an Owner enabling the toggle on Team and Enterprise; a claude.ai login, since API keys and `claude setup-token` tokens don't work; a direct connection to `api.anthropic.com`, blocked by Bedrock, Agent Platform, Foundry, a custom `ANTHROPIC_BASE_URL` or the Claude apps gateway; none of `DISABLE_TELEMETRY`, `DO_NOT_TRACK`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` or `DISABLE_GROWTHBOOK` set; and workspace trust in the project directory.

Server mode, for many sessions: `claude remote-control` (press space for a QR code). Interactive session: `claude --remote-control "My Project"` or `--rc`; from an existing session or VS Code's prompt box, `/remote-control` or `/rc`. Server-mode flags: `--name`, `--spawn same-dir|worktree|session`, `--capacity <N>` (default 32), `--permission-mode`, `--sandbox`, `--verbose`, plus `--continue` with `--session-id <id>`, which restore sessions for about four hours after the server stops.

- **Auto-connect**: **Enable Remote Control for all sessions** in `/config`, or `remoteControlAtStartup: true` in user or managed settings; project settings can only turn it off.
- **Connecting**: open the session URL, scan the QR code, or pick it in the app's Code tab.
- **Forking**: the Claude app can fork a Remote Control session into a background session on your computer ([[worktrees-and-background-work]]).
- **Push notifications**: in `/config`, enable **Push when Claude decides**, **Push when actions required**, or both. `CLAUDE_CLIENT_PRESENCE_FILE` names a marker file; pushes are skipped while it exists.
- **Limits**: one remote session per interactive process (server mode for more); keep the local process running (`tmux` on remote hosts); terminal-only commands like `/plugin` don't work remotely.
- **Diff pane**: on a branch ahead of the default branch it shows changes since the split, uncommitted edits included; otherwise only uncommitted changes.
- **Admin controls**: `disableRemoteControl` turns it off, ZDR organizations can't enable it, and **Trusted Devices** (beta, off by default) needs an enrolled device and a sign-in under 18 hours old, refreshed with a biometric or passkey check. On Team and Enterprise an Owner turns it on under Organization settings > Capabilities > Remote sessions; on Pro and Max you turn on **Require trusted devices** yourself.

**Common errors**:

- `Remote Control requires a claude.ai subscription` (or `/remote-control requires…`): run `claude auth login` and remove any API key or `apiKeyHelper`.
- `requires a full-scope login token`: you're using a `CLAUDE_CODE_OAUTH_TOKEN` token; run `claude auth login` instead.
- `only available when using Claude via api.anthropic.com`: unset the provider or base-URL variable the message names.
- `disabled by your organization's policy`: check the Organization policy line in `claude doctor`.

## Mobile

The Claude app for iOS and Android is a client. Its **Code** tab reaches cloud sessions, projects and Remote Control sessions, and messages Dispatch tasks to the Desktop app ([[desktop-app]]).

- Run `/mobile` to show a QR code that opens the app store.
- Sign in with the same claude.ai account and organization as Claude Code.
- Bypass permissions can't be selected from the app, and Auto isn't offered for Remote Control sessions.

## Troubleshooting

| Problem | Fix |
|---|---|
| Private repo missing | Install the Claude GitHub App on the account that owns it, or rerun `/web-setup` |
| Every cloud session fails authentication | Your org's IP allowlist blocks Anthropic-hosted sessions; ask Anthropic support for an exemption |
| `Remote Control session expired` on teleport | Run `/login` and confirm you're signed in to the session's owning account |
