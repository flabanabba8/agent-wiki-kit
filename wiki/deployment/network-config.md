---
title: Network Configuration
type: how-to
tldr: "Proxies, custom CAs, mTLS and allowlists"
sources:
  - raw/docs/official/network-config.md
  - raw/docs/official/corporate-launcher.md
related: ["[[enterprise-admin]]", "[[settings]]", "[[llm-gateways]]", "[[worktrees-and-background-work]]", "[[environment-variables]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [corporate-proxy, custom-ca-certificates, mtls-client-certificates, network-allowlist, corporate-launcher]
---

# Network Configuration

Claude Code runs behind corporate networks through environment variables for proxies, extra CA certificates and mTLS client certificates. It also has a launcher setting for organizations that require every process to start through a wrapper. Everything here can also go in the `env` block of [[settings]]. Set variables before launch: exported shell variables are read once at startup.

## Proxy

```bash
export HTTPS_PROXY=https://proxy.example.com:8080     # recommended
export HTTP_PROXY=http://proxy.example.com:8080       # if HTTPS isn't available
export NO_PROXY="localhost,192.168.1.1,.example.com"  # space- or comma-separated; "*" bypasses everything
```

- Lowercase variants work too. The first one set wins, in the order `https_proxy`, `HTTPS_PROXY`, `http_proxy`, `HTTP_PROXY`.
- Basic auth goes in the URL (`http://username:password@proxy.example.com:8080`); don't hardcode passwords in scripts. For NTLM or Kerberos proxies, use an [[llm-gateways]] service that supports them.
- SOCKS proxies are not supported. WebSocket connections to `localhost`, `::1` and `127.0.0.0/8` never go through the proxy.
- In Claude Desktop sessions where the app manages the provider connection, proxy and certificate variables are read only from managed settings and `~/.claude/settings.json`.

## Certificate trust

By default Claude Code trusts its bundled Mozilla CA set **and** the operating system's certificate store, so most TLS-inspection proxies work without extra setup. Reading the OS store needs a runtime with `tls.getCACertificates`: the native installer always has it, and npm installs need Node 22.15 or later.

| Goal | Setting |
|---|---|
| Trust one extra corporate CA | `NODE_EXTRA_CA_CERTS=/path/to/ca-cert.pem` |
| Trust only the bundled set, or only the OS store | `CLAUDE_CODE_CERT_STORE=bundled` or `CLAUDE_CODE_CERT_STORE=system` (default `bundled,system`) |

`CLAUDE_CODE_CERT_STORE` has no dedicated settings key; set it in the `env` block of `~/.claude/settings.json` or in the process environment.

## mTLS client certificates

```bash
export CLAUDE_CODE_CLIENT_CERT=/path/to/client-cert.pem
export CLAUDE_CODE_CLIENT_KEY=/path/to/client-key.pem
export CLAUDE_CODE_CLIENT_KEY_PASSPHRASE="your-passphrase"   # only for an encrypted key
```

**Rotation without restart.** Replace the files at the same paths before the old pair expires. Claude Code re-reads them when it next applies settings, or when a request fails with a connection-level error such as a reset or a TLS handshake failure. It then retries with the new pair. It does not watch the files, and it doesn't re-read after a completed handshake that returns an HTTP error. If it reads a half-written pair that doesn't match, it keeps the previous pair. OTLP telemetry exporters keep their first certificate until restart. `CLAUDE_CODE_DISABLE_MTLS_RELOAD_ON_STALE_CONNECTION=1` turns the connection-error re-read off.

**Cloud sessions** ignore `CLAUDE_CODE_CLIENT_CERT`, `CLAUDE_CODE_CLIENT_KEY`, `CLAUDE_CODE_CLIENT_KEY_PASSPHRASE`, `NODE_EXTRA_CA_CERTS`, `NODE_TLS_REJECT_UNAUTHORIZED` and `CLAUDE_CODE_OAUTH_SCOPES` from a settings `env` block, because the hosting environment manages the API connection ([[claude-code-on-the-web]]).

## Verify the configuration

Most of these values aren't validated when read, so a bad path shows up later as a connection or certificate error. The exception is an unparseable proxy URL, which is caught at startup. To check before sending a request:

```bash
claude --debug        # log goes to ~/.claude/debug/, or a path given with --debug-file
```

Look for `CA certs: Appended extra certificates from NODE_EXTRA_CA_CERTS`, `mTLS: Loaded client certificate from CLAUDE_CODE_CLIENT_CERT` and `mTLS: Loaded client key from CLAUDE_CODE_CLIENT_KEY`. A `Failed to read` or `Failed to load` line gives the reason. A successful rotation after a stale connection logs `Stale connection — reloaded rotated mTLS client material`.

In a session, `/status` shows:
- the **Proxy** row, which marks an unparseable value as ignored;
- the **mTLS client cert** and **mTLS client key** rows, present only when the files loaded;
- the **Additional CA cert(s)** row, which shows the path without confirming it loaded.

## Background agents and corporate launchers

Background sessions (`claude agents`, `--bg`, `/background`) run under a per-user supervisor process that outlives your shell ([[worktrees-and-background-work]]). That supervisor inherits the environment of whichever shell started it, and an OS-installed supervisor gets no shell environment at all. **Put network variables in the `env` block of `~/.claude/settings.json` or managed settings, not in shell exports**; settings are the only configuration that reaches every background session.

Some organizations require every process to start through a launcher that applies sandboxing, network controls or credential injection. The supervisor and its workers start Claude Code from the binary's direct path, so a wrapper placed earlier on `PATH` never sees them. Set the launcher instead:

```json
{ "env": { "CLAUDE_CODE_PROCESS_WRAPPER": "/opt/corp/launcher" } }
```

- **Setting form:** the named `processWrapper` setting carries the same value; `CLAUDE_CODE_PROCESS_WRAPPER` wins when both are set.
- **Allowed sources:** only user, `--settings` and managed settings are honored. Project and local settings are ignored, so a committed repository can't put a binary in front of every process.
- **Coverage:** the launcher wraps the background service, every agent view session including warm spares, respawns after updates or crashes, update relaunches, Remote Control session processes, and split-pane agent-team teammates.
- **Not covered:** an installed service whose unit predates the setting, sessions you start yourself in a terminal (use a `claude` script earlier on `PATH` for those), the first process of a `claude-cli://` deep link, `--worktree` with `--tmux` relaunches, and the Chrome native-messaging host. On Windows the variable is ignored.
- **Value format:** an argument list, not a shell command. Whitespace separates tokens, double quotes group, a value starting with `[` is read as a JSON array, and shell operators such as `;` or `$(` are rejected.
- **After deploying:** run `claude daemon stop --any`, or `claude daemon stop` for an installed service, so the next background command starts a wrapped supervisor. Confirm with the Self-exec entry in `/status` or with `claude daemon status`.

**Launcher contract.** The script must end with `exec "$@"`, must not reorder or drop arguments, and must pass every inherited environment variable through; adding variables is fine. It must reach `exec` within about three seconds, tolerate being invoked from inside itself, and print nothing before Claude Code starts. A minimal launcher:

```bash
#!/bin/sh
# organization setup: enter the sandbox, apply network controls, inject credentials
exec "$@"
```

`CLAUDE_CODE_SHELL_PREFIX` is different. It wraps the shell commands Claude runs, such as Bash tool calls, hooks and stdio MCP server starts, not Claude Code's own processes.

## Streaming watchdogs

Four timers abort a streaming response that goes quiet, so a dead connection retries instead of hanging. They are the first-byte deadline, the event-level watchdog, the byte-level watchdog and a 5-minute body idle timeout for non-Anthropic providers.

| Variable | Effect |
|---|---|
| `CLAUDE_ENABLE_STREAM_WATCHDOG`, `CLAUDE_ENABLE_BYTE_WATCHDOG` | Force a watchdog on (`1`) or off (`0`) on the connections it covers; byte watchdog `0` also disables the first-byte deadline |
| `CLAUDE_STREAM_IDLE_TIMEOUT_MS` | Timeout for both watchdogs (minimum 5 minutes; byte watchdog capped at 30 minutes) |
| `CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS` | Byte watchdog only, clamped to 10 seconds–30 minutes |
| `CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS` | First-byte deadline; defaults to the byte watchdog's timeout |
| `API_FORCE_IDLE_TIMEOUT` | `0` disables the body idle timeout, `1` applies it to every provider |

## Hosts to allowlist

| Host | Needed for |
|---|---|
| `api.anthropic.com` | API requests, the WebFetch domain safety check, feature flags, telemetry events |
| `claude.ai`, `claude.com`, `platform.claude.com` | claude.ai and Console sign-in, OAuth token exchange and refresh |
| `mcp-proxy.anthropic.com` | MCP connectors from claude.ai (turn off with `ENABLE_CLAUDEAI_MCP_SERVERS=false`) |
| `downloads.claude.ai` | Native installer, auto-updater, plugin executables |
| `storage.googleapis.com` | Plugin install counts and metadata in `/plugin` |
| `registry.npmjs.org` | npm-source plugins, `npx` MCP servers, npm/bun installs of Claude Code |
| `bridge.claudeusercontent.com` | Claude in Chrome bridge; with an organization IP allowlist, route it through the same egress as `claude.ai` |
| `*.frame.claudeusercontent.com` | Artifact content reads (drop by setting `"enableArtifact": false`) |
| `raw.githubusercontent.com` | `/release-notes` changelog feed |
| `code.claude.com` | Documentation lookups by the built-in guide agent and pre-approved WebFetch |
| `formulae.brew.sh` | Update checks on Homebrew installs only |
| `http-intake.logs.us5.datadoghq.com`, `browser-intake-us5-datadoghq.com` | Optional operational telemetry and error reports on the direct Anthropic API; `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` disables both |

On Bedrock, Agent Platform, Foundry or a signed-in Claude apps gateway session, model traffic and authentication go to the provider or gateway instead ([[cloud-providers]]). Behind an `ANTHROPIC_BASE_URL` gateway, the fast-mode availability check still calls `api.anthropic.com`, honoring the configured proxy ([[models-and-effort]]). For telemetry opt-outs see [[data-and-privacy]].
