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
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [claude-code-not-working, fix-claude-code, claude-doctor, common-error-messages]
---

# Troubleshooting

Find the symptom, apply the fix. Configuration lives on the owning pages: [[settings]], [[permissions-and-modes]], [[mcp]], [[network-config]].

## Diagnostics first

| Tool | What it gives you |
| :--- | :--- |
| `claude doctor` | Read-only install and settings diagnostics, for when `claude` won't start |
| `/doctor` | In-session checkup of install, settings and extensions, with fixes you confirm. Alias `/checkup` |
| `/status` | Active settings sources, authentication method, proxy and mTLS rows |
| `/context` | What occupies the context window, by category |
| `/mcp`, `/hooks`, `/permissions`, `/skills`, `/memory` | What actually loaded for that one surface |
| `/debug [issue]` | Debug logging on, plus Claude diagnosing from the log |
| `claude --debug` | Log at `~/.claude/debug/<session-id>.txt`, or `--debug-file <path>`; `claude --debug=mcp` narrows it |
| `claude --safe-mode` | Every customization off, to test whether your config is the cause |

## Install and updates

- **`command not found: claude`, `'claude' is not recognized`.** Add the install directory, `~/.local/bin` (`%USERPROFILE%\.local\bin` on Windows), to `PATH` in your shell config. The VS Code extension's bundled copy adds nothing to `PATH`.
- **`syntax error near unexpected token '<'`, PowerShell parse errors, a bare 403.** The install URL returned an HTML page or an error status. Check that `downloads.claude.ai` is reachable, or install with `brew install --cask claude-code` or `winget install Anthropic.ClaudeCode`.
- **`curl: (35) TLS connect error`, `unable to get local issuer certificate`, `SELF_SIGNED_CERT_IN_CHAIN`.** Missing CA certificates or a TLS-inspecting proxy. Install `ca-certificates`, or pass `curl --cacert` your corporate CA, then set `NODE_EXTRA_CA_CERTS` for Claude Code itself.
- **`CRYPT_E_NO_REVOCATION_CHECK` or `CRYPT_E_REVOCATION_OFFLINE` on Windows.** Revocation lookup blocked: use `curl --ssl-revoke-best-effort`, or the PowerShell or WinGet installer.
- **`The connection dropped while downloading the update`, `Download timed out`.** A proxy cutting a long transfer. Rerun `claude update`, set `HTTPS_PROXY` if needed, and have the network team allow `downloads.claude.ai`.
- **`Temp directory ... Refusing to use it`, `ENOSPC: no space left on device, mkdir`.** Startup can't create or trust its private `claude-<uid>` temp directory: free disk space, remove the named entry (or `chmod 0700` it), or set `CLAUDE_CODE_TMPDIR` to a directory you control.
- **Windows: neither Git Bash nor PowerShell found.** Add `C:\Windows\System32\WindowsPowerShell\v1.0\` to `PATH`, or point `CLAUDE_CODE_GIT_BASH_PATH` at a file named `bash.exe` or `sh.exe`.

Install methods, release channels and requirements: [[install-and-setup]].

## Authentication

- **Login fails for no obvious reason, or `Claude login not accepted`.** `/logout`, relaunch `claude`, sign in again.
- **`OAuth error: Invalid code`.** Expired or truncated: press `c` to copy the URL, open it, finish quickly.
- **No browser, or the pasted code does nothing (WSL2, SSH, containers).** Paste the code at the prompt, set `BROWSER` to your Windows browser in WSL2, or run `claude auth login`, which reads the code from stdin.
- **`API Error: 403 ... forbidden` after login.** Inactive subscription, a Console account without the Claude Code or Developer role, or a proxy altering requests ([[network-config]]).
- **`API Error: 400 ... "This organization has been disabled"` on an active subscription, or `Credit balance is too low` on a paid plan.** Requests go through a Console key: `ANTHROPIC_API_KEY` overrides a subscription and is always used in `-p`. Check the `API key` row in `/status`, `unset ANTHROPIC_API_KEY`, remove it from your shell profile, relaunch, `/login`.
- **Repeated re-login prompts.** An expired token or wrong system clock; run `/login`. On macOS, `claude doctor` reports `macOS Keychain is not writable`: run `security unlock-keychain ~/Library/Keychains/login.keychain-db`, then `/logout` and `/login` to move credentials back into the Keychain.
- **`Could not load credentials from any providers`, `Could not load the default credentials`, `ChainedTokenCredential authentication failed`.** The provider CLI isn't authenticated in this shell: `aws sts get-caller-identity`, `gcloud auth application-default login` or `az login`. In an IDE, set the provider variables in the IDE's own settings ([[cloud-providers]]).
- **`AWS credentials expired or invalid`, `Google Cloud authentication failed`, `Microsoft Foundry authentication failed` and their siblings.** A 401 means the credential expired, a 403 that the identity lacks access or the model isn't enabled. Refresh what the hint names (`awsAuthRefresh`, `gcpAuthRefresh`, `az login`, `ANTHROPIC_FOUNDRY_API_KEY`, a proxy token); *managed by this environment* means the launching app owns it, so retry or ask your administrator, as for `Gateway refused the request` ([[llm-gateways]]).

## Permissions, settings and hooks

- **A settings value seems ignored.** A closer scope wins (local, project, user), managed settings above all. `claude doctor` finds invalid files; `/status` shows active sources.
- **Permissions, hooks or `env` set globally do nothing.** They were put in `~/.claude.json`, which holds app state; move them to `~/.claude/settings.json`.
- **A hook never fires.** `matcher` is an array, lowercase or misspelled, or hooks sit outside `settings.json`. Use one string with `|` (`"Edit|Write"`) and capitalized tool names under `"hooks"`; only plugins use `hooks/hooks.json`. Watch with `claude --debug`. See [[hooks]].
- **A skill never appears in `/skills`.** The file is `.claude/skills/name.md` instead of `.claude/skills/name/SKILL.md`. If it appears but Claude never triggers it, check for the user-only badge ([[skills]]).
- **Subdirectory CLAUDE.md seems ignored.** Those files load when Claude reads a file in that directory, so put must-always rules in the project-root file ([[claude-md-and-memory]]).
- **`Bash(rm *)` doesn't block `/bin/rm` or `find -delete`.** Bash rules match the literal command string; use a `PreToolUse` hook or the sandbox for a guarantee ([[sandboxing-and-security]]).
- **`The server-side auto mode classifier gave no verdict`.** Auto mode denies the action; after 10 in a row it stops the turn. Send a message to retry, or leave auto mode.
- **`WebFetch cannot fetch localhost`.** WebFetch refuses dotless hostnames; Claude uses `curl` through Bash instead.
- **Your own setup is the suspect.** Try `claude --safe-mode`; if it persists, `cd /tmp && CLAUDE_CONFIG_DIR=/tmp/claude-clean claude`. Managed settings still apply in both.

## MCP servers

- **Server missing or failed in `/mcp`.** A project server from `.mcp.json` needs its one-time approval; approve it from `/mcp`. A relative `command` or `args` path resolves against your launch directory, so use absolute paths.
- **Connected but zero tools.** Choose **Reconnect** in `/mcp`; if it stays at zero, run `claude --debug=mcp` and read the server's stderr in the debug log.
- **`.mcp.json` never loads.** It belongs at the repository root with servers under `mcpServers`, not inside `.claude/` and not in `settings.json`.
- **Server starts without its variables.** Set per-server `env` inside its `.mcp.json` entry.
- **Output warnings or truncation.** Output is warned about above 10,000 tokens and capped at 25,000; raise `MAX_MCP_OUTPUT_TOKENS`.
- **`MCP tool ... (passed via --permission-prompt-tool) not found`.** Check `claude mcp list` and the `mcp__<server>__<tool>` name; raise `MCP_TIMEOUT` for servers slower than 30 seconds to start.
- **`MCP server "<name>" needs you to sign in again`, `requires re-authorization`.** A remote server rejected its credential mid-session: select it in `/mcp` and sign in again.
- **`OAuth callback port ... is already in use`.** Find the holder with `lsof -ti:<port> -sTCP:LISTEN`, or change `MCP_OAUTH_CALLBACK_PORT`.

## Network and proxies

- **`Unable to connect to API`, `Connection refused`, `ENOTFOUND`, `Couldn't connect through your proxy`.** Test with `curl -I https://api.anthropic.com` from the same shell, set `HTTPS_PROXY`, or `ANTHROPIC_BASE_URL` for a gateway; SOCKS proxies aren't supported. When `curl` works but Claude Code doesn't, check `/etc/resolv.conf` on Linux and WSL, stale `utun` interfaces on macOS, and quit Docker Desktop to rule out interception.
- **`SSL certificate verification failed`, `Self-signed certificate detected`.** A TLS-inspecting proxy Claude Code doesn't trust; these aren't retried. Set `NODE_EXTRA_CA_CERTS=/path/to/ca-bundle.pem`, never `NODE_TLS_REJECT_UNAUTHORIZED=0`; `CLAUDE_CODE_CERT_STORE` selects `bundled`, `system` or both. `claude --debug` logs `CA certs:` and `mTLS:` lines, and `/status` shows Proxy and mTLS rows.
- **`Repeated 529 Overloaded errors`, `Request rejected (429)`.** Capacity is tracked per model, so `/model` keeps you working; for a rate limit, check the credential in `/status` and lower `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY`. Scripted runs that fail too early want `CLAUDE_CODE_MAX_RETRIES` (10), `CLAUDE_CODE_RETRY_WATCHDOG=1`, `API_TIMEOUT_MS` (600000) and `CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS`.

## Performance and context

- **High CPU or memory.** Past 2.5GB of heap a critical memory warning appears: restart and `claude --continue`, or `/compact` outside fullscreen rendering. Add build directories to `.gitignore` and test `claude --safe-mode`. Otherwise `/heapdump` writes a heap snapshot and a `-diagnostics.json` to `~/Desktop`; share only the diagnostics file, since the snapshot holds your conversation and credentials.
- **`Autocompact is thrashing: the context refilled to the limit...`.** Something refills the window after each compaction: read files in ranges, `/compact` with narrow instructions, use a subagent, or `/clear`.
- **`Prompt is too long`, shown interactively as `Context limit reached`.** `/compact` or `/clear`; a single exchange can't be compacted, so cut attachments ([[context-window]]).
- **`Error during compaction: Conversation too long`.** `Esc` twice, step back several turns, then `/compact`; or `/clear`.
- **`Request too large (max 32MB)`.** Too many images and attachments; `/compact` or step back past them.
- **Hangs or freezes.** `Ctrl+C`, restart the terminal if needed, then `claude --resume` in the same directory.
- **Search, `@file` mentions or custom agents find nothing.** The bundled `ripgrep` can't run: install your system `ripgrep`, set `USE_BUILTIN_RIPGREP=0`, and check the Search line in `claude doctor`. On WSL, keep projects under `/home/`; cross-filesystem search misses matches.
- **Usage limits.** `/usage` shows each window and its reset; Opus and Sonnet limits are per family, so `/model` keeps you working, and `/usage-credits` buys or requests more ([[costs-and-usage]]).

## Sessions

- **`Failed to resume the conversation`.** Retry with `claude --resume <session-id>` from the message, or start fresh with `claude`.
- **`No conversation found with session ID`.** In `claude --resume`, `Ctrl+A` widens the picker to every project. Transcripts are swept after 30 days by default; `-p` runs aren't in the picker, so use the `session_id` from `--output-format json`.
- **`API Error: 400 orphaned tool_result`, `duplicate tool_use ID`, `thinking blocks ... cannot be modified`.** History reached an inconsistent state after an interrupted tool call: `/rewind` or `Esc` twice to a checkpoint before it.
- **`Invalid encrypted_content in search_result block`.** Hosted web-search results from a proxy or gateway the API can't decrypt; every later turn fails the same way, so `/clear` or start a new session.
- **`This session has no saved transcript`.** The background session stopped before its first response; `claude respawn <id>` starts it fresh ([[sessions-and-checkpoints]]).

## IDE and terminal

- **Garbled text in an integrated terminal.** Run `/terminal-setup` to turn off `terminal.integrated.gpuAcceleration`, then reload the window.
- **Mouse wheel scrolls one line in fullscreen rendering.** `/scroll-speed` or `CLAUDE_CODE_SCROLL_SPEED`, neither of which applies in the JetBrains terminal; `PgUp`/`PgDn` move half a screen, and `/tui default` hands scrolling back to the terminal.
- **Clipboard commands such as `pbcopy` fail under sandboxing.** Have Claude print the content and use `/copy`, which runs outside the sandbox and also saves a file. Adding `pbcopy *` to `excludedCommands` doesn't unsandbox a piped call on its own.
- **Copied text doesn't reach a local clipboard over SSH.** Claude Code sends OSC 52 and your terminal decides: hold the native-selection key (`Fn` in Terminal.app, `Option` in iTerm2) or set `CLAUDE_CODE_DISABLE_MOUSE=1` on the remote machine.
- **A large table is cut off.** Only the first 200 rows display; `/copy` takes every row.
- **`Claude Code process exited with code N`.** Follow **View output logs** in VS Code, reproduce with `claude` in the same project, and run `claude doctor`.
- **`The connection to Claude Code ended before this message completed`** (VS Code). Send the message again; if it repeats, run `claude` in a terminal to see the real error.
- **`Could not locate the Claude CLI on PATH`** (VS Code, Windows PowerShell). Put the install directory in the user or system `PATH`, not your PowerShell profile, then restart VS Code.
- **VS Code extension problems.** It needs VS Code 1.94.0 or later; the Spark icon needs an open file and a trusted workspace; on macOS Tahoe the system Game Overlay takes `Cmd+Esc`, so clear that checkbox or rebind **Claude Code: Focus input**.
- **JetBrains: `/ide` reports no available IDEs.** Confirm the plugin is enabled, restart the IDE fully, launch `claude` from its integrated terminal, and install the plugin on the remote host for remote development ([[ide-integrations]]).

## Still stuck

Run `/doctor` and `/mcp`, report it with `/feedback`, and check the GitHub repository for known issues; contact Anthropic support from claude.ai for account or billing problems.
