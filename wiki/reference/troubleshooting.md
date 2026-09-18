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
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [claude-code-not-working, fix-claude-code, claude-doctor, common-error-messages]
---

# Troubleshooting

Find the symptom, apply the fix. Configuration itself lives on the owning pages: [[settings]], [[permissions-and-modes]], [[mcp]], [[network-config]].

## Diagnostics first

| Tool | What it gives you |
| :--- | :--- |
| `claude doctor` | Read-only install and settings diagnostics from your shell. Use it when `claude` won't start |
| `/doctor` | Full checkup in a session: install health, invalid settings, unused extensions, duplicate subagent names, with fixes you confirm. Alias `/checkup` |
| `/status` | Active settings sources, authentication method, proxy and mTLS rows |
| `/context` | What occupies the context window, by category |
| `/mcp`, `/hooks`, `/permissions`, `/skills`, `/memory` | What actually loaded for that one surface |
| `/debug [issue]` | Debug logging on, plus Claude diagnosing from the log |
| `claude --debug` | Log at `~/.claude/debug/<session-id>.txt`, or `--debug-file <path>`; `claude --debug=mcp` narrows it |
| `claude --safe-mode` | A session with every customization off, to prove whether your config is the cause |

## Install and updates

- **`command not found: claude`, `'claude' is not recognized`.** The install directory isn't on `PATH`; the binary is `~/.local/bin/claude` (`%USERPROFILE%\.local\bin\claude.exe` on Windows). Check with `echo $PATH | tr ':' '\n' | grep -Fx "$HOME/.local/bin"` and add it to your shell config. The VS Code extension bundles a private copy and adds nothing to `PATH`.
- **`syntax error near unexpected token '<'`, PowerShell parse errors, a bare 403.** The install URL returned an HTML page or an error status. Test reachability with `curl -sI https://downloads.claude.ai/claude-code-releases/latest` (expect `200`), then install with `brew install --cask claude-code` or `winget install Anthropic.ClaudeCode`.
- **`curl: (35) TLS connect error`, `unable to get local issuer certificate`, `SELF_SIGNED_CERT_IN_CHAIN`.** Missing CA certificates or a TLS-inspecting proxy. Run `sudo apt-get update && sudo apt-get install ca-certificates`; behind a corporate CA use `curl --cacert /path/to/corporate-ca.pem -fsSL https://claude.ai/install.sh | bash`, then set `NODE_EXTRA_CA_CERTS` for Claude Code itself.
- **`CRYPT_E_NO_REVOCATION_CHECK` or `CRYPT_E_REVOCATION_OFFLINE` on Windows.** Your network blocks the revocation lookup: rerun the download with `curl --ssl-revoke-best-effort`, or use the PowerShell or WinGet installer.
- **`The connection dropped while downloading the update`, `Download timed out`.** A proxy cutting a long transfer. Run `claude update` again, set `HTTPS_PROXY` if your network needs one, and have your network team allow the full download from `downloads.claude.ai`.
- **Windows: neither Git Bash nor PowerShell found.** Add `C:\Windows\System32\WindowsPowerShell\v1.0\` to `PATH`, or point `CLAUDE_CODE_GIT_BASH_PATH` at a file named `bash.exe` or `sh.exe` — any other name is ignored.

Install methods, release channels and requirements: [[install-and-setup]].

## Authentication

- **Login fails for no obvious reason.** `/logout`, close Claude Code, relaunch `claude`, sign in again.
- **`OAuth error: Invalid code`.** The code expired or was truncated. Press `c` at the login prompt to copy the URL, open it locally, finish quickly.
- **No browser, or the pasted code does nothing (WSL2, SSH, containers).** The redirect can't reach the local callback listener: paste the code at the prompt, set `BROWSER` to your Windows browser path in WSL2, or run `claude auth login`, which reads the code from standard input.
- **`API Error: 403 ... forbidden` after login.** Inactive subscription, a Console account without the Claude Code or Developer role, or a proxy altering requests ([[network-config]]).
- **`API Error: 400 ... "This organization has been disabled"` on an active subscription.** An `ANTHROPIC_API_KEY` in your environment overrides it, and is always used in `-p` mode. `unset ANTHROPIC_API_KEY`, remove it from your shell profile, confirm with `/status`.
- **`Credit balance is too low` on a paid plan.** Requests are going through a Console key: check the `API key` row in `/status`, unset it, relaunch, `/login`.
- **Repeated re-login prompts.** An expired token or a wrong system clock; run `/login`. On macOS, `claude doctor` reports `macOS Keychain is not writable` — run `security unlock-keychain ~/Library/Keychains/login.keychain-db`, then `/logout` and `/login` to move credentials back into the Keychain.
- **`Could not load credentials from any providers`, `Could not load the default credentials`, `ChainedTokenCredential authentication failed`.** The provider CLI isn't authenticated in this shell: `aws sts get-caller-identity`, `gcloud auth application-default login`, or `az login`. In an IDE, set the provider variables in the IDE's own settings. See [[cloud-providers]].

## Permissions, settings and hooks

- **A settings value seems ignored.** A closer scope wins — local, then project, then user — with managed settings above all, plus flags and environment variables. `claude doctor` finds invalid files; `/status` shows active sources.
- **Permissions, hooks or `env` set globally do nothing.** They were put in `~/.claude.json`, which holds app state; move them to `~/.claude/settings.json`.
- **A hook never fires.** `matcher` is an array, lowercase, or misspelled, or the hooks aren't in a settings file. Use one string with `|` (`"Edit|Write"`) and capitalized tool names under the `"hooks"` key in `settings.json`; only plugins use a separate `hooks/hooks.json`. Watch evaluation with `claude --debug`. See [[hooks]].
- **A skill never appears in `/skills`.** The file is `.claude/skills/name.md` instead of `.claude/skills/name/SKILL.md`. If it appears but Claude never triggers it, check for the user-only badge ([[skills]]).
- **Subdirectory CLAUDE.md seems ignored.** Those files load when Claude reads a file in that directory, so put must-always rules in the project-root file ([[claude-md-and-memory]]).
- **`Bash(rm *)` doesn't block `/bin/rm` or `find -delete`.** Bash rules match the literal command string; use a `PreToolUse` hook or the sandbox for a guarantee ([[sandboxing-and-security]]).
- **Your own setup is the suspect.** Try `claude --safe-mode`; if it persists, `cd /tmp && CLAUDE_CONFIG_DIR=/tmp/claude-clean claude`. Managed settings still apply in both.

## MCP servers

- **Server missing or failed in `/mcp`.** A project server from `.mcp.json` needs its one-time approval; approve it from `/mcp`. A relative `command` or `args` path resolves against your launch directory, so use absolute paths.
- **Connected but zero tools.** Choose **Reconnect** in `/mcp`; if it stays at zero, run `claude --debug=mcp` and read the server's stderr in the debug log.
- **`.mcp.json` never loads.** It belongs at the repository root with servers under `mcpServers`, not inside `.claude/` and not in `settings.json`.
- **Server starts without its variables.** Set per-server `env` inside its `.mcp.json` entry.
- **Output warnings or truncation.** Output is warned about above 10,000 tokens and capped at 25,000; raise `MAX_MCP_OUTPUT_TOKENS`.
- **`MCP tool ... (passed via --permission-prompt-tool) not found`.** Confirm with `claude mcp list` that the server connects and the name matches `mcp__<server>__<tool>`; raise `MCP_TIMEOUT` if it needs longer than 30 seconds to start.
- **`OAuth callback port ... is already in use`.** Find the holder with `lsof -ti:<port> -sTCP:LISTEN`, or change `MCP_OAUTH_CALLBACK_PORT`.

## Network and proxies

- **`Unable to connect to API`, `Connection refused`, `ENOTFOUND`, `Couldn't connect through your proxy`.** Test with `curl -I https://api.anthropic.com` from the same shell, set `HTTPS_PROXY`, or `ANTHROPIC_BASE_URL` for a gateway. SOCKS proxies aren't supported.
- **`curl` works but Claude Code doesn't.** Check `/etc/resolv.conf` on Linux and WSL, stale `utun` interfaces on macOS, and quit Docker Desktop to rule out traffic interception.
- **`SSL certificate verification failed`, `Self-signed certificate detected`.** A TLS-inspecting proxy Claude Code doesn't trust; these aren't retried. Set `NODE_EXTRA_CA_CERTS=/path/to/ca-bundle.pem`, and never `NODE_TLS_REJECT_UNAUTHORIZED=0`. `CLAUDE_CODE_CERT_STORE` selects `bundled`, `system` or both.
- **Unsure whether proxy or certificate config loaded.** `claude --debug` logs `CA certs:` and `mTLS:` lines; `/status` shows Proxy and mTLS rows.
- **`Repeated 529 Overloaded errors`, `Request rejected (429)`.** Capacity is tracked per model, so `/model` keeps you working; for a rate limit, check the credential in `/status` and lower `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY`.
- **Scripted runs fail too early.** Tune `CLAUDE_CODE_MAX_RETRIES` (10), `CLAUDE_CODE_RETRY_WATCHDOG=1` for unattended runs, `API_TIMEOUT_MS` (600000) and `CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS`.

Proxies, CA trust, mTLS and hosts to allowlist: [[network-config]].

## Performance and context

- **High CPU or memory.** Run `/compact`, restart between major tasks, add build directories to `.gitignore`, and test `claude --safe-mode`. If it stays high, `/heapdump` writes `<session-id>.heapsnapshot` and `<session-id>-diagnostics.json` to `~/Desktop`. The snapshot holds your whole conversation and credentials — share only the `-diagnostics.json`.
- **`Autocompact is thrashing: the context refilled to the limit...`.** Something refills the window after each compaction: read files in ranges, run `/compact keep only the plan and the diff`, move the work to a subagent, or `/clear`.
- **`Prompt is too long`, shown interactively as `Context limit reached`.** Run `/compact`, or `/clear` to start fresh. A single-exchange conversation has nothing to summarize, so cut attachments instead ([[context-window]]).
- **`Error during compaction: Conversation too long`.** Press `Esc` twice, step back several turns, then `/compact`; otherwise `/clear` and reopen the old session from `/resume`.
- **`Request too large (max 32MB)`.** Accumulated images and attachments passed the raw request limit; `/compact` or step back and remove them.
- **Hangs or freezes.** `Ctrl+C`, restart the terminal if needed, then `claude --resume` in the same directory.
- **Search, `@file` mentions or custom agents find nothing.** The bundled `ripgrep` can't run: install your platform's package (for example `brew install ripgrep` or `sudo apt install ripgrep`), set `USE_BUILTIN_RIPGREP=0`, and confirm with `claude doctor` that the Search line shows your system path. On WSL, cross-filesystem reads return fewer matches even when `claude doctor` says Search is OK, so keep projects under `/home/`.
- **Usage limits.** `/usage` shows each window and its reset; Opus and Sonnet limits are per family, so `/model` keeps you working, and `/usage-credits` buys or requests more ([[costs-and-usage]]).

## Sessions

- **`Failed to resume the conversation`.** Retry with `claude --resume <session-id>` from the message, or start fresh with `claude`.
- **`No conversation found with session ID`.** Open `claude --resume` and press `Ctrl+A` to widen the picker to every project. Transcripts are local and swept after the retention period, 30 days by default; a `-p` run's ID is the `session_id` in its `--output-format json` output, and those sessions aren't in the picker.
- **`This session has no saved transcript`.** The background session stopped before its first response finished; the conversation you backgrounded from is intact, and `claude respawn <id>` starts this one fresh ([[sessions-and-checkpoints]]).

## IDE and terminal

- **Garbled text in an integrated terminal.** The terminal's GPU renderer: run `/terminal-setup` to set `terminal.integrated.gpuAcceleration` to `"off"`, then reload the window.
- **Mouse wheel scrolls one line in fullscreen rendering.** `/scroll-speed` or `CLAUDE_CODE_SCROLL_SPEED`, neither of which applies in the JetBrains terminal; `PgUp`/`PgDn` move half a screen, and `/tui default` hands scrolling back to the terminal.
- **Clipboard commands such as `pbcopy` fail under sandboxing.** Have Claude print the content and use `/copy`, which also saves a file and prints its path, or add `pbcopy *`, `wl-copy *`, `xclip *` to `excludedCommands`.
- **Copied text doesn't reach a local clipboard over SSH.** Claude Code sends OSC 52 and your terminal decides: hold the native-selection key (`Fn` in Terminal.app, `Option` in iTerm2) or set `CLAUDE_CODE_DISABLE_MOUSE=1` on the remote machine.
- **A large table is cut off.** Tables over 200 rows display the first 200; the full table stays in the conversation, `/copy` takes every row, or have Claude write it to a file.
- **`Claude Code process exited with code N`.** Follow **View output logs** in VS Code, reproduce with `claude` in the same project, and run `claude doctor`.
- **`Could not locate the Claude CLI on PATH`** (VS Code, Windows PowerShell). Run `where.exe claude` outside VS Code, set the install directory as a user or system variable rather than in your PowerShell profile, then restart VS Code, which reads `PATH` only at startup.
- **VS Code extension problems.** It needs VS Code 1.94.0 or later; the Spark icon needs an open file and a trusted workspace; on macOS Tahoe the system Game Overlay takes `Cmd+Esc`, so clear that checkbox or rebind **Claude Code: Focus input**.
- **JetBrains: `/ide` reports no available IDEs.** Confirm the plugin is enabled, restart the IDE fully, launch `claude` from its integrated terminal, and install the plugin on the remote host for remote development ([[ide-integrations]]).

## Still stuck

Run `/doctor` and `/mcp`, report it with `/feedback`, and check the GitHub repository for known issues. For account or billing problems, contact Anthropic support from claude.ai.
