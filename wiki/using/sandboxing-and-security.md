---
title: Sandboxing and Security
type: reference
tldr: "Bash sandbox, isolation choices, security model"
sources:
  - raw/docs/official/sandboxing.md
  - raw/docs/official/sandbox-environments.md
  - raw/docs/official/security.md
  - raw/docs/official/data-usage.md
  - raw/docs/official/permission-modes.md
related: ["[[permissions-and-modes]]", "[[data-and-privacy]]", "[[enterprise-admin]]", "[[trustworthy-agents]]", "[[settings]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [bash-sandbox, sandbox-settings, prompt-injection, network-isolation, dev-container-isolation]
---

# Sandboxing and Security

[[permissions-and-modes]] decide *whether* a tool call runs. The Bash sandbox decides *what a running command can reach*. The operating system enforces it on every Bash, PowerShell, and Monitor command and its child processes, so the boundary holds even when an approved command does more than its name suggests. Use both layers together. This page also covers how to choose a stronger isolation boundary for unattended runs, and Claude Code's security model.

## The built-in Bash sandbox

| Platform | Mechanism | Setup |
|:--|:--|:--|
| macOS | Seatbelt | Nothing to install |
| Linux, WSL2 | bubblewrap + socat | `sudo apt-get install bubblewrap socat` (or `dnf`) |
| Native Windows, WSL1 | Not supported | Use WSL2, a container, or a VM |

Run `/sandbox` to open the panel:

- **Mode** chooses between auto-allow and regular permissions.
- **Overrides** controls `allowUnsandboxedCommands`.
- **Config** shows the resolved settings.
- **Dependencies** appears on Linux when something is missing.

On Ubuntu 24.04 and later, if `sysctl kernel.apparmor_restrict_unprivileged_userns` returns `1`, add an AppArmor profile for `bwrap`. The optional seccomp filter (`npm install -g @anthropic-ai/sandbox-runtime`) adds Unix-socket blocking.

The panel saves to `.claude/settings.local.json`. To enable the sandbox everywhere, set `sandbox.enabled: true` in `~/.claude/settings.json`. For one session only:

```bash
claude --settings '{"sandbox": {"enabled": true, "allowUnsandboxedCommands": false}}'
```

If the sandbox can't start, Claude Code warns and runs commands unsandboxed. Set `sandbox.failIfUnavailable: true` to make that a hard failure.

### Sandbox modes

- **Auto-allow:** commands that can run sandboxed are approved without a prompt, even in Manual mode. A bare `Bash` ask rule is skipped for those commands. Deny rules, content-scoped ask rules such as `Bash(git push *)`, and critical-path `rm` still apply. Two exceptions: in plan mode auto-allow doesn't widen approvals, and in auto mode a command carrying per-command allowed domains (below) goes to the classifier instead.
- **Regular permissions:** every command goes through the normal permission flow, sandboxed or not.

Auto-allow is not the same as auto mode. Auto-allow trusts the OS boundary; auto mode trusts a classifier. They combine, with those two exceptions.

**Escape hatch.** When a command fails because of the sandbox, Claude may retry it with `dangerouslyDisableSandbox`, which goes through the normal permission flow (prompt in Manual, classifier in auto). The prompt is titled "Bash command (unsandboxed)".

- To force a prompt on every retry, add an ask rule for `Bash(dangerouslyDisableSandbox:true)`.
- To forbid retries, set `allowUnsandboxedCommands: false` (**Strict sandbox mode**). Then only commands listed in `excludedCommands` run outside the sandbox.
- Commands you type yourself at the `!` shell prompt run unsandboxed, except in background sessions.

### Default boundary

- **Writes:** allowed in the working directory, directories added with `--add-dir`/`/add-dir`/`additionalDirectories`, and the session temp directory that `$TMPDIR` points to.
- **Reads:** the whole machine except denied paths. This includes `~/.aws/credentials` and `~/.ssh/` unless you block them.
- **Network:** no domains are pre-allowed. The first connection to a host prompts; in auto mode Claude instead names the hosts on the command itself (below). **Yes, and don't ask again** saves a `WebFetch(domain:...)` allow rule, and those rules also feed the sandbox allowlist.
- **Always denied inside writable areas:** `.claude` settings files and the `.claude/skills`, `agents`, `commands`, and `hooks` directories; `.mcp.json`; shell startup files; `.gitconfig`; `.git/hooks` and `.git/config`; and most of `~/.claude` plus `~/.claude.json`. No `allowWrite` entry lifts this. A top-level `HEAD`, `objects`, or `refs` is denied because it would make the directory a bare git repository, as are top-level `config` and `hooks` when a `HEAD` sits beside them; a file named `config` is denied with or without one.

### Configure paths and domains

```json
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowWrite": ["~/.kube", "/tmp/build"],
      "denyRead": ["~/"],
      "allowRead": ["."]
    },
    "network": { "allowedDomains": ["github.com", "*.npmjs.org"] }
  }
}
```

- **Path prefixes:** `/tmp/build` is absolute, `~/` is home, and `./` or a bare path is relative to the project root in project settings or to `~/.claude` in user settings. Permission rules differ: there, `//path` is absolute and `/path` is relative to the settings source.
- **Merging and overlap:** filesystem arrays merge across scopes, and when read rules overlap the rule with the narrower path applies.
- **Other network keys:** `deniedDomains` blocks hosts inside a wider allow. `strictAllowlist: true` (user, managed, or `--settings` only) denies unlisted hosts instead of prompting, and `allowManagedDomainsOnly` narrows the allowlist to the managed entries.
- **Filesystem layer off:** `sandbox.filesystem.disabled: true` keeps network isolation but removes filesystem isolation. A sandboxed command could then write shell startup files or settings that widen its own access, and project settings can't set this key.

### Per-command allowed domains in auto mode

In auto mode with sandboxing on, Claude names the hosts a command needs on the command itself instead of triggering a network approval per connection. Each sandboxed Bash, PowerShell, or Monitor command can carry hosts beyond the sandbox allowlist — a domain such as `registry.npmjs.org`, a wildcard such as `*.pythonhosted.org`, or an IP address, each with an optional `:port` — and the classifier reviews them together with the command.

- An approved list opens those hosts for that one command, for as long as it runs. Nothing is added to the session's allowed hosts or your settings; the next command names its own.
- A command carrying hosts goes to the classifier rather than being approved by a permission rule or auto-allow. If an ask rule forces a prompt, the dialog lists the hosts beside the command and approving covers both.
- A per-command list only widens what the sandbox denies by default: `deniedDomains` still blocks, and Claude Code refuses per-command lists while `strictAllowlist` or `allowManagedDomainsOnly` locks the allowlist.
- While per-command lists apply, a connection to a host no approved command listed is refused outright, with no prompt or classifier check. The refusal names the host in the command's result, and Claude re-runs the command with it added.

### Protect credentials

`sandbox.credentials` removes or masks secrets for sandboxed commands:

```json
{
  "sandbox": {
    "enabled": true,
    "credentials": {
      "files": [{ "path": "~/.aws/credentials", "mode": "deny" }, { "path": "~/.ssh", "mode": "deny" }],
      "envVars": [{ "name": "GITHUB_TOKEN", "mode": "deny" }]
    }
  }
}
```

- **`deny`** blocks the file or unsets the variable. It works from any scope, and no scope can remove another scope's entry.
- **`mask`** gives the command a sentinel value, and the sandbox proxy swaps in the real credential only on requests to `injectHosts`. Masking requires `network.tlsTerminate` and is honored only from user settings, managed settings, or `--settings`. On macOS, masked files are simply blocked.
- **All subprocesses:** `sandbox.credentials` covers sandboxed Bash only. To strip credentials from every subprocess, set `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`.

### Common fixes

| Symptom | Fix |
|:--|:--|
| `jest` hangs | `jest --no-watchman` |
| `docker` fails | Add `docker *` to `excludedCommands` |
| `gh`, `gcloud`, `terraform` fail TLS on macOS | Add them to `excludedCommands` |
| `bwrap` can't mount `/proc` in a container | `enableWeakerNestedSandbox: true`, only when the container is the real boundary |
| `open`/`osascript` error `-600` on macOS | `allowAppleEvents: true`, which removes code-execution isolation |
| `git checkout` fails with `unable to unlink old` | Approve the unsandboxed retry or run it yourself |

### Organization enforcement

Deliver these keys through managed settings — an MDM-managed file or server-managed settings on claude.ai ([[enterprise-admin]]):

```json
{ "sandbox": { "enabled": true, "failIfUnavailable": true, "allowUnsandboxedCommands": false } }
```

Boolean keys use the managed value. Array keys merge, so developers can append entries. `allowManagedReadPathsOnly` and `allowManagedDomainsOnly` lock read paths and domains to the managed lists. `excludedCommands` can't be locked, so keep the managed list short.

### Limits of the sandbox

- **No content inspection:** the proxy filters by hostname without inspecting TLS, so broad domains such as `github.com` allow exfiltration and domain fronting. For inspection, use a custom proxy via `httpProxyPort`/`socksProxyPort`.
- **Unix sockets:** `allowUnixSockets` can expose host services; `/var/run/docker.sock` effectively gives host access.
- **Shell commands only:** Read, Edit, and Write use permission rules instead. MCP servers and command hooks run unconstrained on the host. Computer use acts on your real desktop.
- **Both layers matter:** without network isolation, readable secrets can leak; without filesystem isolation, a compromised command can backdoor the system.

## Choosing an isolation boundary

| Approach | Isolates | Docker | Use when |
|:--|:--|:--|:--|
| Sandboxed Bash tool | Bash, PowerShell and Monitor commands and their children | No | Fewer prompts on your own machine |
| Sandbox runtime (`npx @anthropic-ai/sandbox-runtime claude`) | Whole Claude Code process, including file tools, MCP servers, and hooks | No | Isolating MCP and hooks without Docker (beta) |
| Dev container | Full dev environment | Yes | Team standard; default-deny firewall supports unattended runs |
| Custom container | Full dev environment | Yes | Existing container or CI infrastructure |
| Virtual machine | Full OS | No | Untrusted repositories, kernel-level separation |
| Cloud session | Anthropic-managed VM | No | Full isolation without provisioning ([[claude-code-on-the-web]]) |

A cloud session needs a Claude subscription, plus a connected GitHub account unless you launch it with `claude --cloud`, which can upload your local repository instead. Always run `--dangerously-skip-permissions` inside a container, VM, or the sandbox runtime, as a non-root user. For auto mode, isolation adds defense in depth but isn't required. The Bash sandbox alone constrains only shell commands, so it is not enough for fully unattended runs. The sandbox runtime reads `~/.srt-settings.json` and, with no valid settings, starts with network blocked, so a clean start doesn't prove your settings loaded.

## Security model and prompt injection

- **Permission-based:** Manual mode starts read-only, asks before edits and non-read-only commands, and writes only inside the launch directory. Sandboxing restricts shell commands' filesystem and network access; permission rules cover every tool ([[permissions-and-modes]]).
- **Injection defenses:**
  - Web fetches run in a separate context window.
  - `curl` and `wget` aren't auto-approved.
  - Suspicious commands need approval even if allowlisted, and unmatched commands require approval (fail-closed).
  - First-time codebases and new MCP servers require trust verification, which `-p` skips.
  - In auto mode, the classifier never sees tool results, and a server-side probe flags suspicious tool output.
- **Credentials** are stored in the macOS Keychain when available, and protected by file permissions on Linux and Windows.
- **MCP:** Anthropic doesn't security-audit MCP servers; use your own or trusted providers.
- **Windows:** avoid enabling WebDAV or allowing paths such as `\\*`, which can trigger network requests that bypass permissions.
- **Cloud sessions** run in isolated VMs with limited network access, a scoped-credential GitHub proxy, pushes restricted to the working branch, and audit logging.

Practices for untrusted content:

- Review commands before approving them.
- Don't pipe untrusted content straight to Claude.
- Verify changes to critical files.
- Use VMs when interacting with external services.
- Audit rules with `/permissions`.
- Report odd behavior with `/feedback`.
- Report vulnerabilities through Anthropic's HackerOne program, not publicly.

Isolation doesn't change what reaches the model: prompts and files Claude reads go to the API or your provider either way. Consumer accounts (Free, Pro, Max) choose whether data trains models and have 30-day or 5-year retention. Commercial accounts aren't trained on by default and have 30-day retention, with zero data retention available to qualified Enterprise orgs. Local transcripts sit in plaintext under `~/.claude/projects/` for 30 days. Full details are in [[data-and-privacy]]. For the research framing of containment tiers and injection defenses, see [[trustworthy-agents]].
