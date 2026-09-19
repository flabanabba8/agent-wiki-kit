---
title: Install and Set Up Claude Code
type: how-to
tldr: "Install, log in, update, uninstall"
sources:
  - raw/docs/official/setup.md
  - raw/docs/official/authentication.md
  - raw/docs/official/quickstart.md
  - raw/docs/official/overview.md
  - raw/docs/official/env-vars.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
related: ["[[overview]]", "[[settings]]", "[[troubleshooting]]", "[[cloud-providers]]", "[[environment-variables]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [install-claude-code, claude-code-login, update-claude-code, release-channel, uninstall-claude-code]
valid_until: 2027-03-15
---

# Install and Set Up Claude Code

This page covers installing the CLI, logging in, running a first session, keeping Claude Code updated, and removing it. The desktop app and IDE extensions have their own pages: [[desktop-app]] and [[ide-integrations]]. If something fails, see [[troubleshooting]].

## System requirements

| Requirement | Supported |
|---|---|
| OS | macOS 13.0+, Windows 10 1809+ or Windows Server 2019+, Ubuntu 20.04+, Debian 10+, Alpine Linux 3.19+ |
| Hardware | 4 GB+ RAM, x64 or ARM64 |
| Shell | Bash, Zsh, PowerShell, or CMD |
| Network | Internet connection required |
| Location | An Anthropic supported country |
| Account | Pro, Max, Team, Enterprise, or Console. The free claude.ai plan has no Claude Code access |

ripgrep usually ships with Claude Code.

## Install

**Native installer (recommended).** It auto-updates in the background.

```bash
# macOS, Linux, WSL
curl -fsSL https://claude.ai/install.sh | bash
```
```powershell
# Windows PowerShell
irm https://claude.ai/install.ps1 | iex
```
```batch
:: Windows CMD
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

If you see `The token '&&' is not a valid statement separator`, you're in PowerShell, not CMD. If you see `'irm' is not recognized`, you're in CMD, not PowerShell.

**Other methods:**

| Method | Command | Auto-updates? |
|---|---|---|
| Homebrew (stable channel) | `brew install --cask claude-code` | No. Run `brew upgrade claude-code` |
| Homebrew (latest channel) | `brew install --cask claude-code@latest` | No. Run `brew upgrade claude-code@latest` |
| WinGet | `winget install Anthropic.ClaudeCode` | No. Run `winget upgrade Anthropic.ClaudeCode` |
| apt / dnf / apk | Signed repos at `downloads.claude.ai`, each with `stable` and `latest` channels | No. Updates come through your system upgrade |
| npm | `npm install -g @anthropic-ai/claude-code` (needs Node.js 22+) | Upgrade with `npm install -g @anthropic-ai/claude-code@latest`, not `npm update -g` |

npm notes: the package installs the same native binary through a per-platform optional dependency, so your package manager must allow optional dependencies. Don't use `sudo npm install -g`.

**Pin a channel or version at install time** by passing it to the installer. The channel you choose becomes your auto-update default:

```bash
curl -fsSL https://claude.ai/install.sh | bash -s stable
curl -fsSL https://claude.ai/install.sh | bash -s 2.1.89
```

### Windows: native or WSL

| Option | Sandboxing | When to use |
|---|---|---|
| Native Windows | Not supported | Windows-native projects and tools |
| WSL 2 | Supported | Linux toolchains or sandboxed command execution |
| WSL 1 | Not supported | When WSL 2 is unavailable |

On native Windows you don't need Administrator. With Git for Windows installed, Claude Code uses Git Bash for the Bash tool. Without it, Claude Code runs shell commands through the PowerShell tool. If Git Bash isn't found, set its path in settings:

```json
{ "env": { "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe" } }
```

For WSL, run the Linux installer inside the WSL terminal and launch `claude` there.

### Alpine and other musl distributions

Install the dependencies, then tell Claude Code to use the system ripgrep:

```bash
apk add bash curl libgcc libstdc++ ripgrep
```
```json
{ "env": { "USE_BUILTIN_RIPGREP": "0" } }
```

## Verify

```bash
claude --version     # prints e.g. "2.1.211 (Claude Code)"
claude doctor        # read-only install and settings diagnostics, no session started
```

Inside a session, `/doctor` runs a fuller setup checkup that can also fix problems.

## Log in

Run `claude` in a project directory. On first launch a browser window opens for login.

- If the browser doesn't open, press `c` to copy the login URL.
- If the browser shows a code instead of redirecting (common in WSL2, SSH, and containers), paste it at the `Paste code here if prompted` prompt.
- If `ANTHROPIC_API_KEY` is set, Claude Code skips the browser and asks you once to approve the key.
- Signing in with a Claude account also requests access to your claude.ai plugins.
- Use `/login` to switch accounts and `/logout` to sign out. Logging out also resets first-launch setup.

| Account type | How to sign in |
|---|---|
| Claude Pro or Max | Your claude.ai account |
| Claude for Teams or Enterprise | The claude.ai account your admin invited. Enterprise adds SSO, domain capture, and managed policy |
| Claude Console | Console credentials after an admin invites you. A "Claude Code" workspace is created for cost tracking. You can sign in with or without creating an API key |
| Amazon Bedrock, Google Cloud's Agent Platform, Microsoft Foundry | Set the provider's environment variables before running `claude`, or pick **3rd-party platform** at the login prompt. No browser login. See [[cloud-providers]] |
| Claude apps gateway | Corporate SSO through `/login`. See [[llm-gateways]] |

### Which credential wins

When several are present, Claude Code uses the first match:

1. Cloud provider credentials (`CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, or `CLAUDE_CODE_USE_FOUNDRY` set)
2. `ANTHROPIC_AUTH_TOKEN` (sent as a Bearer header, for gateways)
3. `ANTHROPIC_API_KEY` (always used in `-p` mode, needs one-time approval in interactive mode)
4. `apiKeyHelper` script output
5. `CLAUDE_CODE_OAUTH_TOKEN`
6. Anthropic profile and federation credentials
7. Subscription OAuth from `/login`

A signed-in Claude apps gateway session sits above the whole list. A common gotcha is a stale `ANTHROPIC_API_KEY` overriding your subscription. Run `unset ANTHROPIC_API_KEY`, then check `/status` to see which credential is active.

### Tokens for CI and scripts

```bash
claude setup-token                       # browser approval, prints a one-year OAuth token
export CLAUDE_CODE_OAUTH_TOKEN=your-token
```

The token requires a Pro, Max, Team, or Enterprise plan. It can only make model requests, so it can't start Remote Control or fetch claude.ai connectors. Bare mode (`--bare`) doesn't read it; use `ANTHROPIC_API_KEY` or `apiKeyHelper` there. See [[headless-mode]].

### Where credentials live

- **macOS:** the encrypted Keychain. If the Keychain rejects the write (for example, locked over SSH), `~/.claude/.credentials.json` with mode `0600`.
- **Linux:** `~/.claude/.credentials.json`, mode `0600`.
- **Windows:** `%USERPROFILE%\.claude\.credentials.json`.
- With `CLAUDE_CONFIG_DIR` set, the file lives under that directory.

When a `/login` credential is within three days of expiring, startup shows `Your login expires in 3 days · run /login to renew`.

Org-wide login restrictions (`forceLoginMethod`, `forceLoginOrgUUID`) are covered in [[enterprise-admin]].

## First session

```bash
cd /path/to/your/project
claude
```

The prompt shows the version, model, and working directory. Try `what does this project do?`, then a small change. Type `/help` for commands, `/resume` to reopen a conversation, and `/init` to generate a starter CLAUDE.md ([[claude-md-and-memory]]).

On Pro, Max, and Team plans, interactive terminal sessions start in auto mode. On other plans they start in Manual mode. Press `Shift+Tab` to switch modes ([[permissions-and-modes]]).

| Shell command | Does |
|---|---|
| `claude` | Start interactive mode |
| `claude "task"` | Start with an initial prompt |
| `claude -p "query"` | One-off query, then exit |
| `claude -c` | Continue the most recent conversation in this directory |
| `claude -r` | Resume a previous conversation |

## Updates and release channels

Native installs check for updates at startup and periodically, download in the background, and apply on the next launch. `claude doctor` shows the last update attempt.

| Setting | Values | Effect |
|---|---|---|
| `autoUpdatesChannel` | `"latest"` (default), `"stable"` | `stable` is typically about a week old and skips releases with major regressions. Also settable in `/config` under **Auto-update channel** |
| `minimumVersion` | e.g. `"2.1.100"` | Floor for auto-updates and `claude update`, so switching to `stable` doesn't downgrade you |
| `DISABLE_AUTOUPDATER` (in `env`) | `"1"` | Stops background checks. `claude update` and `claude install` still work |
| `DISABLE_UPDATES` (env var) | `1` | Blocks every update path, including manual ones |
| `CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE` | `1` | Claude Code runs the Homebrew or WinGet upgrade for you in the background |

```json
{ "autoUpdatesChannel": "stable", "minimumVersion": "2.1.100" }
```

Run `claude update` to update right away. Homebrew picks its channel by cask name (`claude-code` is stable, `claude-code@latest` is latest). To make Claude Code refuse to start outside a version range, admins use `requiredMinimumVersion` and `requiredMaximumVersion` in managed settings ([[enterprise-admin]]).

The native launcher on macOS and Linux is `~/.local/bin/claude`, a symlink into `~/.local/share/claude/versions/`. If you replace it with your own launcher, updates leave it alone. Remove it and run `claude update` to hand control back.

## Verify binary integrity

Each release publishes a GPG-signed `manifest.json` with SHA256 checksums. Import the key from `https://downloads.claude.ai/keys/claude-code.asc`, confirm the fingerprint `31DD DE24 DDFA B679 F42D 7BD2 BAA9 29FF 1A7E CACE`, then run `gpg --verify manifest.json.sig manifest.json` and compare the binary's checksum. macOS binaries are signed by "Anthropic PBC" and notarized, and Windows binaries are signed by "Anthropic, PBC". Linux binaries aren't individually signed, but apt, dnf, and apk verify repository signatures automatically.

## Uninstall

| Install method | Remove with |
|---|---|
| Native (macOS/Linux/WSL) | `rm -f ~/.local/bin/claude` and `rm -rf ~/.local/share/claude` |
| Homebrew | `brew uninstall --cask claude-code` (or `claude-code@latest`) |
| WinGet | `winget uninstall Anthropic.ClaudeCode` |
| apt | `sudo apt remove claude-code`, then delete `/etc/apt/sources.list.d/claude-code.list` and `/etc/apt/keyrings/claude-code.asc` |
| dnf | `sudo dnf remove claude-code`, then delete `/etc/yum.repos.d/claude-code.repo` |
| npm | `npm uninstall -g @anthropic-ai/claude-code` |

To wipe configuration and history too, delete `~/.claude` and `~/.claude.json`, and per project `.claude` and `.mcp.json`. This deletes all settings, MCP configs, and session history. The VS Code extension, JetBrains plugin, and desktop app also write to `~/.claude/` and will recreate it, so uninstall them first. If `claude` still runs afterwards, a second install or an old shell alias is left over ([[troubleshooting]]).
