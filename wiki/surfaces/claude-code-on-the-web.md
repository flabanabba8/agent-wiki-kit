---
title: Claude Code on the Web, Remote Control and Mobile
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
related: ["[[desktop-app]]", "[[ci-cd-and-code-review]]", "[[slack-and-claude-tag]]", "[[routines-and-scheduling]]", "[[hooks]]", "[[channels]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
valid_until: 2027-03-15
aliases: [cloud-sessions, claude-teleport, remote-control, claude-code-mobile, cloud-environments]
---

# Claude Code on the Web, Remote Control and Mobile

Two ways to use Claude Code away from your terminal, differing in where the code runs.

| | Cloud sessions (Claude Code on the web) | Remote Control |
|---|---|---|
| Code runs on | Cloud VM, Anthropic-managed by default | Your machine |
| You chat from | claude.ai/code, Claude mobile app, Desktop | claude.ai/code, Claude mobile app |
| Uses your local config | No, only what's in the repo | Yes |
| Requires GitHub | Yes, or a local repo bundled with `--cloud` | No |
| Keeps running if you disconnect | Yes | Only while the local process runs |
| Permission modes | Accept edits, Plan, Auto | Manual, Accept edits, Plan |
| Network | Configurable per environment | Your machine's network |

Cloud sessions suit parallel tasks, repos you haven't cloned, and work that continues with your laptop closed; Remote Control suits local work needing your filesystem, tools or MCP servers. Both require a claude.ai account; neither works with a Console API key or through Bedrock, Agent Platform or Foundry. Chat events into a local session: [[channels]]. Scheduled cloud runs: [[routines-and-scheduling]].

## Cloud sessions

In research preview for Pro, Max and Team, and Enterprise users with premium or Chat + Claude Code seats; Zero Data Retention organizations can't use it. Sessions share your plan's rate limits, with no separate compute charge.

### Connect GitHub

- **Claude GitHub App**, via browser onboarding at claude.ai/code: all public repos, plus private repos where the App is installed. Also enables PR auto-fix.
- **`/web-setup`** in the CLI: every repo your `gh auth token` can access; sends that token to your Claude account. On Team/Enterprise, an Owner must turn on **Quick web setup** first.

On Team and Enterprise, an Owner must also enable the GitHub connector under Admin settings > Connectors. Onboarding creates a **Default** environment with Trusted network access.

### How a session runs

1. The repo is cloned into a fresh Ubuntu 24.04 x86_64 VM; the environment's setup script runs.
2. Network access follows the environment's access level.
3. Claude works; watch and steer, or leave it.
4. Claude pushes a branch. Review the diff (**Compare against** diffs its changes against any branch, not only the base), leave inline comments (sent with your next message), then **Create PR** for a full PR, a draft, or GitHub's compose page. It stays live afterwards; for CI and review-comment watching, use auto-fix ([[ci-cd-and-code-review]]).

Pre-fill a new session with URL parameters on claude.ai/code: `prompt` (alias `q`), `prompt_url`, `repositories` (alias `repo`, comma-separated `owner/repo`) and `environment`.

### From terminal to cloud: `--cloud`

```bash
claude --cloud "Fix the authentication bug in src/auth/login.ts"
claude -p "your message" --cloud <session-id>   # queue a follow-up, then exit
```

- `--cloud` clones your GitHub remote at the current branch, not your local checkout, so push first. Each call creates a separate session; several run in parallel.
- Claude Code bundles your local repo instead when it has no git remote, or the Claude GitHub App isn't installed on its github.com repo. The bundle holds full history plus uncommitted changes to tracked files — not untracked files, nor uncommitted credential-like files (`.env`, `*.tfvars`, `id_rsa`, `*.pem`) — and must be under 100 MB. `CCR_FORCE_BUNDLE=1` always bundles, which also runs GitLab or Bitbucket repos in the cloud, though results can't be pushed back.
- Follow-ups accept a bare `session_...`/`cse_...` ID or a claude.ai/code URL. `--output-format json` returns `{ok, session_id, url}`. The org's `allow_remote_sessions` policy must be on.

### From cloud to terminal: teleport

Pull a cloud session into your terminal with `claude --teleport` (a picker) or `claude --teleport <session-id>`, `/teleport` (or `/tp`) inside a running session, or `t` on a session in `/tasks`. It first requires a clean git state (prompting a stash), the same repository rather than a fork, the branch pushed (fetched and checked out automatically), and the same claude.ai account — API-key auth fails with `Unable to get organization UUID`, so run `/login`.

The terminal gets its own copy; local work doesn't sync back. `--resume` lists only local history, `--teleport` pulls a cloud session and its branch. Send a local session to the cloud from Desktop's **Continue in** menu ([[desktop-app]]).

### Inside a cloud session

- **Commands**: text-output ones such as `/compact` and `/context` work; `/clear` doesn't, so start a new session. Picker commands take an argument, e.g. `/model sonnet` or `/effort high`; `/config` opens your web settings.
- **Subagents and teams**: subagents in `.claude/agents/` work; agent teams need `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set in the environment.
- **Compaction**: the platform sets `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` itself, so auto-compaction triggers partway through the window; `CLAUDE_CODE_AUTO_COMPACT_WINDOW` changes the window size.
- **Session links**: commits get a `Claude-Session: <url>` trailer and PR bodies include the session URL, unless `attribution.sessionUrl` is `false`. The session ID is in `CLAUDE_CODE_REMOTE_SESSION_ID`.
- **Sharing**: visibility is Private or Team on Team and Enterprise, Private or Public on Pro and Max — check for secrets before sharing. Archiving hides a session; deleting is permanent.
- **Expiry**: idle sessions stop and their VM is reclaimed. Reopening restores the conversation on a fresh VM, but subagents or shell jobs still running are lost.

## Cloud environments

An environment is a saved configuration used wherever a cloud session starts: the web, `claude --cloud`, Desktop, mobile, routines and Claude Tag. Edit one with the cloud icon above the message box at claude.ai/code; environments archive but don't delete. `/remote-env` sets the CLI default, saved as `remote.defaultEnvironmentId`.

Access levels set outbound connections: **None** allows no outbound traffic through the session's network; **Trusted** (the default) allows allowlisted package registries, GitHub and cloud SDKs; **Full** allows any domain; **Custom** takes your own domain list (a leading `*.` matches subdomains), optionally plus the defaults.

At every level, sessions still reach GitHub through a proxy, enabled MCP connectors through Anthropic, the hosts of any API credentials, and the Anthropic API. Other settings:

- **Environment variables**: `.env` format, copied in at session start. Anyone using the environment can read them, so no secrets.
- **API credentials** (Pro and Max, admin required): the agent proxy adds the key to requests for the hosts you list, after they leave the VM, so Claude never sees it; never attached to GitHub, the Anthropic API, public package registries or setup-script requests.
- **GitHub proxy**: real credentials stay outside the VM, `git push` works only to the session's own branch, only a pinned set of GraphQL operations is allowed, and `gh` works without setup since `GH_TOKEN` and `GITHUB_TOKEN` read as `proxy-injected` unless you set your own.
- **Pre-installed tools**: Python, Node.js 20/21/22, Ruby, PHP 8.3, OpenJDK 21, Go, Rust, GCC/Clang, Docker, PostgreSQL 16 and Redis 7.0 (installed but not running), `gh`, `jq` and ripgrep; ask Claude to run `check-tools` for versions.
- **Resources**: about 4 vCPUs, 16 GB RAM and 30 GB disk; for heavier jobs use Remote Control or a self-hosted environment.
- **Shared environments**: on Team and Enterprise, Owners create them on the **Cloud environments** admin page; Claude Tag channels can use only shared or self-hosted environments ([[slack-and-claude-tag]]).

### Setup scripts vs SessionStart hooks

A setup script runs as root, in Bash, before Claude Code launches. It must exit 0 and should finish in about five minutes. The resulting filesystem is snapshotted and reused, skipping the script, until the script or allowed hosts change or the cache expires after about seven days; running processes aren't kept.

A setup script is configured in the environment dialog, runs before launch (skipped when cached) and is cloud-only; a SessionStart hook lives in the repo's `.claude/settings.json`, runs after launch on every start and resume, and works locally and in the cloud.

Use setup scripts for toolchains, hooks for project setup ([[hooks]]); to run a hook only in the cloud, exit early unless `CLAUDE_CODE_REMOTE` is `true`.

### What carries over

The fresh clone carries the repo's `CLAUDE.md` and `.claude/rules/`, hooks in `.claude/settings.json`, `.mcp.json`, `.claude/skills/`, `.claude/agents/` and `.claude/commands/`, plugins declared in repo settings, and your organization's server-managed settings. Skills enabled on your claude.ai account load too.

Not carried over: `~/.claude/CLAUDE.md`, user-level skills and agents, plugins enabled only in user settings, MCP servers added at local or user scope (use `claude mcp add --scope project`), device MDM policy, and interactive logins such as AWS SSO.

## Remote Control

Remote Control connects claude.ai/code or the Claude app to a Claude Code session on your machine. Code and files stay local; the conversation syncs through Anthropic over outbound HTTPS only, no inbound ports.

**Requirements**:

- Any plan; on Team and Enterprise, an Owner must enable the Remote Control toggle.
- A claude.ai login: API keys and `claude setup-token` tokens don't work.
- A direct connection to `api.anthropic.com`: Bedrock, Agent Platform, Foundry, a custom `ANTHROPIC_BASE_URL` and the Claude apps gateway all block it.
- None of `DISABLE_TELEMETRY`, `DO_NOT_TRACK`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` or `DISABLE_GROWTHBOOK` set.
- Workspace trust accepted in the project directory.

Server mode, for many sessions: `claude remote-control` (press space to show a QR code). Interactive session: `claude --remote-control "My Project"` or `--rc`. From an existing session, or VS Code's prompt box: `/remote-control` or `/rc`.

Server-mode flags: `--name`, `--spawn same-dir|worktree|session`, `--capacity <N>` (default 32), `--permission-mode`, `--sandbox`, `--verbose`, and `--continue` with `--session-id <id>`, which restore sessions for about four hours after the server stops.

- **Auto-connect**: **Enable Remote Control for all sessions** in `/config`, or `remoteControlAtStartup: true` in user or managed settings; project settings can only turn it off.
- **Connecting**: open the session URL, scan the QR code, or pick it in the app's Code tab (a computer icon, green dot when online). Photos and files you attach reach the local session.
- **Forking**: the Claude app can fork a session started with `claude --remote-control` or `/remote-control`; the fork runs as a background session on your computer ([[worktrees-and-background-work]]).
- **Push notifications**: in `/config`, enable **Push when Claude decides**, **Push when actions required**, or both. `CLAUDE_CLIENT_PRESENCE_FILE` names a marker file; pushes are skipped while it exists.
- **Limits**: one remote session per interactive process (server mode for more); the local process must keep running, so use `tmux` on remote hosts; terminal-only commands like `/plugin` and `/resume` don't work remotely.
- **Admin controls**: `disableRemoteControl` turns it off, ZDR organizations can't enable it, and **Trusted Devices** (Team/Enterprise, beta) needs an enrolled device and a sign-in under 18 hours old, refreshed with a biometric or passkey check.

**Common errors**:

- `Remote Control requires a claude.ai subscription`: run `claude auth login`, and remove `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` or `apiKeyHelper` if one is in use.
- `requires a full-scope login token`: you're using a `CLAUDE_CODE_OAUTH_TOKEN` token; run `claude auth login` instead.
- `only available when using Claude via api.anthropic.com`: unset the provider or base-URL variable the message names.
- `disabled by your organization's policy`: check the Organization policy line in `claude doctor`, or ask an Owner to enable it.

## Mobile

The Claude app for iOS and Android is a client; code doesn't run on the phone. Its **Code** tab reaches cloud and Remote Control sessions, and messages Dispatch tasks to the Desktop app ([[desktop-app]]).

- Run `/mobile` to show a QR code that opens the app store.
- Sign in with the same claude.ai account and organization as Claude Code.
- Bypass permissions can't be selected from the app, and Auto isn't offered for Remote Control sessions.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Session creation failed` | Check status.claude.com, retry after a minute, confirm GitHub can reach the repo |
| Private repo missing | Install the Claude GitHub App on the account that owns it, or rerun `/web-setup` |
| Setup script fails or hangs | Add `set -x`, append `\|\| true` to non-critical steps, run installs in parallel, move large downloads into a SessionStart hook |
| Every cloud session fails authentication | Your org's IP allowlist blocks Anthropic-hosted sessions; ask Anthropic support for an exemption |
| `Remote Control session expired` on teleport | Run `/login` and confirm you're signed in to the session's owning account |
