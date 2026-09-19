---
title: Troubleshooting
type: how-to
tldr: "Symptoms, causes and fixes with commands"
sources:
  - raw/docs/official/troubleshooting.md
  - raw/docs/official/troubleshoot-install.md
  - raw/docs/official/errors.md
  - raw/docs/official/debug-your-config.md
  - raw/docs/official/network-config.md
  - raw/docs/official/mcp.md
  - raw/docs/official/vs-code.md
  - raw/docs/official/jetbrains.md
related: ["[[install-and-setup]]", "[[settings]]", "[[network-config]]", "[[context-window]]", "[[mcp]]", "[[slash-commands]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [claude-code-not-working, fix-claude-code, claude-doctor, common-error-messages]
---

# Troubleshooting

Find the symptom, apply the fix. Configuration lives on the owning pages: [[settings]], [[permissions-and-modes]], [[mcp]], [[network-config]].

## Diagnostics first

| Tool | What it gives you |
| :--- | :--- |
| `claude doctor`, `claude --safe-mode`, `claude --debug` | Install and settings diagnostics when `claude` won't start; a session with every customization off, to test whether your config is the cause; a log at `~/.claude/debug/<session-id>.txt` or `--debug-file <path>`, narrowed by `claude --debug=mcp` |
| `/doctor`, `/debug [issue]` | In-session checkup of install health, invalid settings, unused extensions and duplicate subagent names, with fixes you confirm (alias `/checkup`); debug logging plus Claude reading the log |
| `/status`, `/context`; `/mcp`, `/hooks`, `/permissions`, `/skills`, `/memory` | Active settings sources, authentication method, proxy and mTLS rows; what occupies the context window; what actually loaded for one surface |

## Install and updates

- **`command not found: claude`, `'claude' is not recognized`.** The install directory isn't on `PATH`; the binary is `~/.local/bin/claude` (`%USERPROFILE%\.local\bin\claude.exe` on Windows). Check with `echo $PATH | tr ':' '\n' | grep -Fx "$HOME/.local/bin"` and add it to your shell config. The VS Code extension bundles a private copy, adding nothing to `PATH`.
- **`syntax error near unexpected token '<'`, PowerShell parse errors, a bare 403.** The install URL returned an HTML page or an error status. Test with `curl -sI https://downloads.claude.ai/claude-code-releases/latest` (expect `200`), then `brew install --cask claude-code` or `winget install Anthropic.ClaudeCode`. `The connection dropped while downloading the update` or `Download timed out` is a proxy cutting a long transfer: rerun `claude update`, set `HTTPS_PROXY`, and have your network team allow the full download from `downloads.claude.ai`.
- **`curl: (35) TLS connect error`, `unable to get local issuer certificate`, `SELF_SIGNED_CERT_IN_CHAIN`.** Missing CA certificates or a TLS-inspecting proxy: run `sudo apt-get update && sudo apt-get install ca-certificates`; behind a corporate CA, `curl --cacert /path/to/corporate-ca.pem -fsSL https://claude.ai/install.sh | bash`, then set `NODE_EXTRA_CA_CERTS` for Claude Code itself. `CRYPT_E_NO_REVOCATION_CHECK` or `CRYPT_E_REVOCATION_OFFLINE` on Windows is a blocked revocation lookup: rerun with `curl --ssl-revoke-best-effort`, or use the PowerShell or WinGet installer. On Windows with neither Git Bash nor PowerShell found, add `C:\Windows\System32\WindowsPowerShell\v1.0\` to `PATH`, or point `CLAUDE_CODE_GIT_BASH_PATH` at a file named `bash.exe` or `sh.exe` — any other name is ignored.

## Authentication

- **Login fails for no obvious reason.** `/logout`, close Claude Code, relaunch `claude`, sign in again. `Claude login not accepted` when creating a cloud session means the server refused this machine's claude.ai login.
- **`OAuth error: Invalid code`, or no browser and the pasted code does nothing (WSL2, SSH, containers).** The code expired or truncated, or the redirect can't reach the local callback listener: press `c` at the login prompt to copy the URL and finish quickly, set `BROWSER` to your Windows browser path in WSL2, or run `claude auth login`, which reads the code from stdin.
- **`API Error: 403 ... forbidden` after login.** Inactive subscription, a Console account without the Claude Code or Developer role, or a proxy altering requests ([[network-config]]).
- **`API Error: 400 ... "This organization has been disabled"` on an active subscription, or `Credit balance is too low` on a paid plan.** Requests go through a Console key: `ANTHROPIC_API_KEY` overrides a subscription and is always used in `-p`. Check the `API key` row in `/status`, `unset ANTHROPIC_API_KEY`, remove it from your shell profile, relaunch, `/login`.
- **Repeated re-login prompts.** An expired token or wrong system clock; run `/login`. On macOS, `claude doctor` reports `macOS Keychain is not writable`: run `security unlock-keychain ~/Library/Keychains/login.keychain-db`, then `/logout` and `/login` to move credentials back into the Keychain.
- **`Could not load credentials from any providers`, `Could not load the default credentials`, `ChainedTokenCredential authentication failed`.** The provider CLI isn't authenticated in this shell: `aws sts get-caller-identity`, `gcloud auth application-default login` or `az login`. In an IDE, set the provider variables in the IDE's own settings ([[cloud-providers]]).
- **`AWS credentials expired or invalid`, `Google Cloud authentication failed`, `Microsoft Foundry authentication failed` and their siblings.** A 401 means the credential expired, a 403 that the identity lacks access or the model isn't enabled. Refresh what the hint names (`awsAuthRefresh`, `gcpAuthRefresh`, `az login`, `ANTHROPIC_FOUNDRY_API_KEY`, a proxy token); *managed by this environment* means the launching app owns it, so retry or ask your administrator, as for `Gateway refused the request` ([[llm-gateways]]).

## Permissions, settings and hooks

- **A settings value seems ignored.** A closer scope wins — local, project, user — with managed settings above all, plus flags and environment variables. `claude doctor` finds invalid files; `/status` shows active sources. Permissions, hooks or `env` that do nothing globally sit in `~/.claude.json`, app state: move them to `~/.claude/settings.json`.
- **A hook never fires.** `matcher` is an array, lowercase or misspelled, or the hooks aren't in a settings file. Use one string with `|` (`"Edit|Write"`) and capitalized tool names under the `"hooks"` key in `settings.json`; only plugins use a separate `hooks/hooks.json`. Watch evaluation with `claude --debug` ([[hooks]]).
- **A skill never appears in `/skills`.** The file is `.claude/skills/name.md` instead of `.claude/skills/name/SKILL.md`; if it appears but never triggers, check for the user-only badge ([[skills]]). A subdirectory CLAUDE.md loads only when Claude reads a file there, so put must-always rules in the project-root file ([[claude-md-and-memory]]).
- **`Bash(rm *)` doesn't block `/bin/rm` or `find -delete`.** Bash rules match the literal command string; use a `PreToolUse` hook or the sandbox for a guarantee ([[sandboxing-and-security]]). If your own setup is the suspect, try `claude --safe-mode`, then `cd /tmp && CLAUDE_CONFIG_DIR=/tmp/claude-clean claude`; managed settings still apply in both.

## MCP servers

- **Server missing, failed, or connected with zero tools in `/mcp`.** A project server from `.mcp.json` needs its one-time approval; a relative `command` or `args` path resolves against your launch directory, so use absolute paths. At zero tools, choose **Reconnect**; if it stays there, `claude --debug=mcp` puts the server's stderr in the debug log.
- **`.mcp.json` never loads.** It belongs at the repository root with servers under `mcpServers`, not inside `.claude/` and not in `settings.json`; per-server variables go in `env` inside its entry.
- **Output warnings or truncation.** Output is warned about above 10,000 tokens and capped at 25,000; raise `MAX_MCP_OUTPUT_TOKENS`. For `MCP tool ... (passed via --permission-prompt-tool) not found`, confirm with `claude mcp list` that the server connects and the name matches `mcp__<server>__<tool>`; raise `MCP_TIMEOUT` if it needs over 30 seconds to start.
- **A tool call fails with `needs you to sign in again`, `rejected the credential from its headersHelper`, `rejected the Authorization header in its config` or `needs additional permissions (scope: ...)`.** The server refused the credential mid-call: re-authenticate from `/mcp`, fix the helper or static header where it is configured, adding the named scope to a pinned `oauth.scopes` list first.
- **`OAuth callback port ... is already in use`.** Find the holder with `lsof -ti:<port> -sTCP:LISTEN`, or change `MCP_OAUTH_CALLBACK_PORT`. `No available ports for OAuth redirect` instead means no local listener can bind: allow Claude Code to listen on `127.0.0.1`.

## Network and proxies

- **`Unable to connect to API`, `Connection refused`, `ENOTFOUND`, `Couldn't connect through your proxy`.** Test with `curl -I https://api.anthropic.com` from the same shell, set `HTTPS_PROXY`, or `ANTHROPIC_BASE_URL` for a gateway; SOCKS proxies aren't supported. When `curl` works but Claude Code doesn't, check `/etc/resolv.conf` on Linux and WSL, stale `utun` interfaces on macOS, and quit Docker Desktop to rule out interception.
- **`SSL certificate verification failed`, `Self-signed certificate detected`.** A TLS-inspecting proxy Claude Code doesn't trust; these aren't retried. Set `NODE_EXTRA_CA_CERTS=/path/to/ca-bundle.pem`, never `NODE_TLS_REJECT_UNAUTHORIZED=0`; `CLAUDE_CODE_CERT_STORE` selects `bundled`, `system` or both. `claude --debug` logs `CA certs:` and `mTLS:` lines, and `/status` shows Proxy and mTLS rows.
- **`Repeated 529 Overloaded errors`, `Request rejected (429)`.** Capacity is tracked per model, so `/model` keeps you working; for a rate limit, check the credential in `/status` and lower `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY`. Scripted runs that fail too early want `CLAUDE_CODE_MAX_RETRIES` (10), `CLAUDE_CODE_RETRY_WATCHDOG=1`, `API_TIMEOUT_MS` (600000) and `CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS`.

## Performance and context

- **High CPU or memory, hangs or freezes.** Run `/compact`, restart between major tasks, add build directories to `.gitignore`; after a freeze, `Ctrl+C`, restart the terminal, then `claude --resume` in the same directory. If it stays high, `/heapdump` writes `<session-id>.heapsnapshot` and `<session-id>-diagnostics.json` to `~/Desktop`; that snapshot holds your conversation and credentials, so share only the `-diagnostics.json`.
- **`Autocompact is thrashing: the context refilled to the limit...`.** Something refills the window after each compaction: read files in ranges, run `/compact keep only the plan and the diff`, move the work to a subagent, or `/clear`.
- **`Prompt is too long`, shown interactively as `Context limit reached`.** Run `/compact`, or `/clear` to start fresh. When `/compact` answers `Not enough messages to compact.`, the conversation is a single exchange, so resend with less pasted text or smaller attachments ([[context-window]]).
- **`Error during compaction: Conversation too long`.** Press `Esc` twice, step back several turns, then `/compact`; otherwise `/clear` and reopen the old session from `/resume`. `Request too large (max 32MB)` means accumulated images and attachments passed the raw request limit: `/compact`, or step back and remove them.
- **Search, `@file` mentions or custom agents find nothing.** The bundled `ripgrep` can't run: install it (`brew install ripgrep`, `sudo apt install ripgrep`), set `USE_BUILTIN_RIPGREP=0`, and confirm with `claude doctor` that the Search line shows your system path. On WSL, cross-filesystem reads return fewer matches even when Search looks OK, so keep projects under `/home/`.
- **Usage limits.** `/usage` shows each window and its reset; Opus and Sonnet limits are per family, and `/usage-credits` buys or requests more ([[costs-and-usage]]).

## Sessions

- **`Failed to resume the conversation`.** Retry with `claude --resume <session-id>` from the message, or start fresh with `claude`.
- **`No conversation found with session ID`.** Open `claude --resume`; `Ctrl+A` widens the picker to every project. Transcripts are local and swept after the retention period, 30 days by default; a `-p` run's ID is the `session_id` in its `--output-format json` output, and those sessions aren't in the picker. `This session has no saved transcript` means a background session stopped before its first response: the conversation you backgrounded from is intact, and `claude respawn <id>` starts this one fresh ([[sessions-and-checkpoints]]).

## IDE and terminal

- **Garbled text in an integrated terminal.** The terminal's GPU renderer: run `/terminal-setup` to set `terminal.integrated.gpuAcceleration` to `"off"`, then reload the window.
- **Mouse wheel scrolls one line in fullscreen.** `/scroll-speed` or `CLAUDE_CODE_SCROLL_SPEED`, neither applying in the JetBrains terminal; `PgUp`/`PgDn` move half a screen, and `/tui default` restores native scrollback.
- **Clipboard commands such as `pbcopy` fail under sandboxing.** Have Claude print the content and use `/copy`, which also saves a file and prints its path, or add `pbcopy *`, `wl-copy *`, `xclip *` to `excludedCommands`. Over SSH, Claude Code sends OSC 52 and your terminal decides: hold the native-selection key (`Fn` in Terminal.app, `Option` in iTerm2) or set `CLAUDE_CODE_DISABLE_MOUSE=1` remotely.
- **A large table is cut off.** Tables over 200 rows display the first 200; the full table stays in the conversation, so `/copy` takes every row or have Claude write it to a file.
- **VS Code.** For `Claude Code process exited with code N`, follow **View output logs**, reproduce with `claude` in the same project, run `claude doctor`. `The connection to Claude Code ended before this message completed` means the extension can't tell whether the message was processed: send it again. For `Could not locate the Claude CLI on PATH` in Windows PowerShell, run `where.exe claude` outside VS Code and set the install directory as a user or system variable rather than your PowerShell profile, then restart VS Code, which reads `PATH` only at startup. The extension needs VS Code 1.94.0 or later; the Spark icon needs an open file and a trusted workspace; on macOS Tahoe the Game Overlay takes `Cmd+Esc`, so clear that checkbox or rebind **Claude Code: Focus input**.
- **JetBrains: `/ide` reports no available IDEs.** Confirm the plugin is enabled, restart the IDE fully, launch `claude` from its integrated terminal; for remote development install the plugin on the remote host ([[ide-integrations]]).

## Still stuck

Run `/doctor` and `/mcp`, report it with `/feedback`, and check the GitHub repository for known issues; contact Anthropic support from claude.ai for account or billing problems.
