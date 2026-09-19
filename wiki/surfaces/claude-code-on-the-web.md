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
related: ["[[desktop-app]]", "[[ci-cd-and-code-review]]", "[[slack-and-claude-tag]]", "[[routines-and-scheduling]]", "[[hooks]]", "[[channels]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
valid_until: 2027-03-15
aliases: [cloud-sessions, cloud-session, claude-code-on-the-web, claude-teleport, remote-control, claude-code-mobile, cloud-environments]
---

# Cloud Sessions, Remote Control and Mobile

Two ways to work away from your terminal, differing in where code runs.

| | Cloud session | Remote Control |
|---|---|---|
| Code runs on | Cloud VM, Anthropic-managed by default | Your machine |
| Start from | claude.ai/code, the Claude app, Desktop's **Cloud** option, `claude --cloud`, a routine | Terminal, VS Code extension, Desktop |
| Chat from | claude.ai/code, the Claude app, Desktop | The same, plus where it started |
| Your local config | No, only what's in the repo | Yes |
| Requires GitHub | Yes, or a local repo bundled with `--cloud` | No |
| Survives disconnect | Yes | Only while the local process runs |
| Permission modes | Accept edits, Plan, Auto | Manual, Accept edits, Plan |
| Network | Configurable per environment | Your machine's network |

Cloud sessions suit parallel tasks, repos you haven't cloned, and work continuing with your laptop closed; Remote Control suits local work needing your filesystem, tools or MCP servers. Both need a claude.ai account, and neither works with a Console API key or a third-party provider. For one body of work needing many cloud sessions, use a project ([[claude-projects]]); for chat events into a local session, [[channels]]; for scheduled runs, [[routines-and-scheduling]].

## Cloud sessions

Research preview for Pro, Max, Team, and Enterprise users with premium or Chat + Claude Code seats; not for Zero Data Retention organizations. Sessions share your plan's rate limits, with no separate compute charge.

### Connect GitHub

- **Claude GitHub App**, through browser onboarding at claude.ai/code: all public repos, plus private repos where it's installed; also enables PR auto-fix.
- **`/web-setup`** in the CLI: every repo your `gh auth token` can access, sending that token to your Claude account. On Team and Enterprise an Owner must turn on **Quick web setup** first.

On Team and Enterprise the Owner also enables the GitHub connector under Admin settings > Connectors. Onboarding creates a **Default** environment with Trusted network access. Project threads need the Claude GitHub App on every repository they clone.

### How a session runs

1. The repo is cloned into a fresh Ubuntu 24.04 x86_64 VM, the environment's setup script runs, and network access follows the environment's access level.
2. Claude works; watch and steer, or leave it.
3. Claude pushes a branch. In the diff view, **Compare against** picks any branch as the base, and inline comments go with your next message. **Create PR** opens a full PR, a draft, or GitHub's compose page, and the session stays live; for CI and review-comment watching, use auto-fix ([[ci-cd-and-code-review]]).

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

One environment applies wherever a cloud session starts, Claude Tag included. Edit one with the cloud icon above the message box at claude.ai/code; environments archive but don't delete. `/remote-env` sets the CLI default, stored as `remote.defaultEnvironmentId`.

Access levels set outbound connections: **None** allows none; **Trusted** (the default) allowlisted package registries, GitHub and cloud SDKs; **Full** any domain; **Custom** your own list, where a leading `*.` matches subdomains, optionally plus the defaults. At every level sessions still reach GitHub through a proxy, enabled MCP connectors through Anthropic, the hosts of any API credentials, and the Anthropic API.

- **Environment variables**: `.env` format, copied in at session start and readable by anyone using the environment, so no secrets.
- **API credentials** (Pro and Max, admin required): the agent proxy adds the key for the hosts you list after requests leave the VM, so Claude never sees it; never attached to GitHub, the Anthropic API, public registries or setup scripts.
- **GitHub proxy**: credentials stay outside the VM, `git push` reaches only the session's own branch, only a pinned set of GraphQL operations is allowed, and `gh` needs no setup because `GH_TOKEN` and `GITHUB_TOKEN` read as `proxy-injected`.
- **Pre-installed tools**: Python, Node.js 20/21/22, Ruby, PHP 8.3, OpenJDK 21, Go, Rust, GCC/Clang, Docker, PostgreSQL 16 and Redis 7.0 (installed, not running), `gh`, `jq` and ripgrep; ask Claude to run `check-tools` for versions.
- **Resources**: about 4 vCPUs, 16 GB RAM, 30 GB disk; heavier jobs need Remote Control or a self-hosted environment.

### Shared environments

On Team and Enterprise the selector groups your own environments under **Personal** and the organization's under **Organization**. A shared environment opens read-only for everyone, Owners included, who edit and archive it from the **Cloud environments** admin page. An Owner creates one there or shares a personal environment from its **Who can use it** row; sharing keeps the ID, so sessions and routines already using it keep working. Claude Tag channels can use only shared or self-hosted environments ([[slack-and-claude-tag]]).

### Setup scripts vs SessionStart hooks

A setup script is configured in the environment dialog and runs as root, in Bash, before Claude Code launches. It must exit 0 and should finish in about five minutes. The filesystem it produces is snapshotted and reused, skipping the script, until the script or allowed hosts change or the cache expires after about seven days; running processes aren't kept. A SessionStart hook instead lives in the repo's `.claude/settings.json` and runs after launch on every start and resume, locally and in the cloud. Use setup scripts for toolchains, hooks for project setup ([[hooks]]); for a cloud-only hook, exit early unless `CLAUDE_CODE_REMOTE` is `true`.

### What carries over

The clone carries the repo's `CLAUDE.md`, `.claude/rules/`, `.claude/settings.json` hooks, `.mcp.json`, `.claude/skills/`, `.claude/agents/`, `.claude/commands/` and declared plugins, plus your organization's server-managed settings. Skills enabled on your claude.ai account load too.

A session with several repositories starts above the clones: from each repository's `.claude/settings.json` it takes only the plugins and marketplaces declared there, not hooks, permission rules or `env`, and reads no `.mcp.json`. A repo SessionStart hook doesn't run either; use a setup script instead.

Not carried over: `~/.claude/CLAUDE.md`, user-level skills, agents and plugins, MCP servers added at local or user scope (use `claude mcp add --scope project`), device MDM policy, and interactive logins such as AWS SSO.

## Remote Control

Remote Control connects claude.ai/code or the Claude app to a local session. Code and files stay local; the conversation syncs through Anthropic over outbound HTTPS only, no inbound ports.

**Requirements**: any plan, with an Owner enabling the toggle on Team and Enterprise; a claude.ai login, since API keys and `claude setup-token` tokens don't work; a direct connection to `api.anthropic.com`, blocked by Bedrock, Agent Platform, Foundry, a custom `ANTHROPIC_BASE_URL` or the Claude apps gateway; none of `DISABLE_TELEMETRY`, `DO_NOT_TRACK`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` or `DISABLE_GROWTHBOOK` set; and workspace trust in the project directory.

Server mode, for many sessions: `claude remote-control` (press space for a QR code). Interactive session: `claude --remote-control "My Project"` or `--rc`; from an existing session or VS Code's prompt box, `/remote-control` or `/rc`. Server-mode flags: `--name`, `--spawn same-dir|worktree|session`, `--capacity <N>` (default 32), `--permission-mode`, `--sandbox`, `--verbose`, plus `--continue` with `--session-id <id>`, which restore sessions for about four hours after the server stops.

- **Auto-connect**: **Enable Remote Control for all sessions** in `/config`, or `remoteControlAtStartup: true` in user or managed settings; project settings can only turn it off.
- **Connecting**: open the session URL, scan the QR code, or pick it in the app's Code tab, where a green dot means online. Attached photos and files reach the local session.
- **Forking**: the Claude app can fork a Remote Control session; the fork runs as a background session on your computer ([[worktrees-and-background-work]]).
- **Push notifications**: `/config` offers **Push when Claude decides** and **Push when actions required**; pushes are skipped while the marker file named by `CLAUDE_CLIENT_PRESENCE_FILE` exists.
- **Limits**: one remote session per interactive process (server mode for more); the local process must keep running, so use `tmux` on remote hosts; terminal-only commands such as `/plugin` don't work remotely.
- **Admin controls**: `disableRemoteControl` turns it off and ZDR organizations can't enable it. **Trusted Devices** (Team/Enterprise, beta) needs an enrolled device and a sign-in under 18 hours old, refreshed by biometrics or a passkey.
- **Errors**: `requires a claude.ai subscription` or `requires a full-scope login token` — run `claude auth login` and remove `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN` or `apiKeyHelper`; `only available when using Claude via api.anthropic.com` — unset the variable named; a policy refusal shows on `claude doctor`'s Organization policy line.

## Mobile

The Claude app for iOS and Android is a client; code doesn't run on the phone. Its **Code** tab reaches cloud sessions, projects and Remote Control sessions, and messages Dispatch tasks to Desktop ([[desktop-app]]). `/mobile` shows a QR code to the app store; sign in with the same claude.ai account and organization. Bypass permissions can't be chosen from the app, and Auto isn't offered for Remote Control sessions.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Session creation failed` | Check status.claude.com and confirm GitHub can reach the repo |
| Private repo missing | Install the Claude GitHub App on the owning account, or rerun `/web-setup` |
| Setup script fails or hangs | Add `set -x`, append `\|\| true` to non-critical steps, parallelize installs, move large downloads into a hook |
| Every session fails auth | Your org's IP allowlist blocks Anthropic-hosted sessions; ask for an exemption |
| `Remote Control session expired` on teleport | Run `/login` as the session's owning account |
| `/web-setup` hidden, or `Cloud sessions are disabled by your organization's policy` | Cloud sessions are off for the org, ZDR is on, or Quick web setup isn't enabled |
