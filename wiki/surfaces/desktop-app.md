---
title: Claude Desktop App for Code
type: reference
tldr: "Desktop Code tab: sessions, panes, SSH, WSL"
sources:
  - raw/docs/official/desktop.md
  - raw/docs/official/desktop-quickstart.md
  - raw/docs/official/desktop-linux.md
  - raw/docs/official/desktop-wsl.md
  - raw/docs/official/commands.md
related: ["[[claude-code-on-the-web]]", "[[chrome-and-computer-use]]", "[[worktrees-and-background-work]]", "[[permissions-and-modes]]", "[[enterprise-admin]]", "[[routines-and-scheduling]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [claude-desktop, desktop-code-tab, claude-desktop-linux, desktop-ssh-sessions, desktop-wsl-sessions]
---

# Claude Desktop App for Code

Three tabs: **Chat** for conversation, **Cowork** for Dispatch and longer agentic tasks in a sandboxed VM, and **Code**, which is Claude Code with a graphical interface.

The Code tab runs the CLI's engine and reads the same `CLAUDE.md`, settings, hooks, skills and MCP files. It bundles Claude Code — no Node.js or separate CLI install — and needs a Pro, Max, Team or Enterprise subscription. Use it for parallel sessions in one window, side-by-side panes and visual diff review; use the CLI for scripting ([[headless-mode]]), since Desktop has no `--print` or `--output-format` equivalent.

## Install

- **macOS**: universal build for Intel and Apple Silicon. **Windows**: x64 or ARM64 installer. Both auto-update on launch.
- **Linux (beta)**: see [Linux beta](#linux-beta).

Then sign in and click **Code**.

## Start a session

Set four things before your first message:

- **Environment**: **Local** (your machine), **Cloud** (Anthropic-managed, keeps running after you close the app — [[claude-code-on-the-web]]), **SSH** (a remote machine), **WSL** (a WSL distribution, Windows only).
- **Project folder**; cloud sessions add more repositories with **+**, each with its own branch selector.
- **Model**, from the dropdown next to the send button.
- **Permission mode**, from the mode selector:

| Desktop label | Settings value | Notes |
|---|---|---|
| Manual | `default` | Asks before edits and commands |
| Accept edits | `acceptEdits` | Auto-accepts file edits and common filesystem commands |
| Plan | `plan` | Explores and proposes; applies to the current session only |
| Auto | `auto` | Background safety checks instead of prompts, where auto mode is available |
| Bypass permissions | `bypassPermissions` | Pro/Max: enable in Settings → Claude Code. Team/Enterprise: organization policy only |

A mode you pick is remembered per folder and overrides `permissions.defaultMode`. `dontAsk` is CLI-only; cloud sessions offer Accept edits, Plan and Auto. The modes: [[permissions-and-modes]].

## Review and ship

- **Diff view**: click the `+12 -1` indicator, click any line to comment, then submit all with `Cmd+Enter` / `Ctrl+Enter`; Claude revises the code and shows a new diff.
- **Review code**: a toolbar button reviewing the current diff for high-signal issues — compile errors, logic errors, security vulnerabilities, obvious bugs — not style, formatting or anything a linter catches.
- **PR monitoring**: after you open a PR, a CI status bar polls check results through the GitHub CLI, requiring `gh` installed and authenticated. **Auto-fix** reads failing checks and iterates; **Auto-merge** squash-merges once all checks pass, and must also be enabled in the GitHub repository settings.

Other PR automation: [[ci-cd-and-code-review]].

## Arrange your workspace

Panes: chat, diff, browser, terminal, file, plan, tasks and subagent, plus the iOS Simulator on macOS. Drag a pane header to move it or an edge to resize, pop one out into its own window, close the focused pane with `Cmd+\` / `Ctrl+\`, or open more from the **Views** menu.

- **Terminal** (local sessions only): `` Ctrl+` `` opens in the session's working directory, with the same environment Claude uses.
- **File pane** (local and SSH sessions): click a path to open it, edit, then **Save**. Right-click a path for **Open in** (VS Code, Cursor, Zed), **Attach as context** or **Copy path**.
- **Transcript view**: Normal, Verbose (every tool call) or Summary (final responses and changes); cycle with `Ctrl+O`.
- **Usage ring**, next to the model picker: context usage for this session and plan usage shared across surfaces.

| Shortcut (macOS; use Ctrl on Windows) | Action |
|---|---|
| `Cmd+N` / `Cmd+W` | New / close session |
| `Ctrl+Tab` / `Ctrl+Shift+Tab` | Next / previous session |
| `Cmd+Shift+D` / `Cmd+Shift+B` | Toggle diff / Browser pane |
| `Cmd+;` | Open side chat |
| `Cmd+Shift+M` / `Cmd+Shift+I` / `Cmd+Shift+E` | Permission mode / model / effort menu |
| `Cmd+/` | Show all shortcuts |

Terminal shortcuts such as `Shift+Tab` don't apply in Desktop.

## Preview your app

Claude can start a dev server and open it in the **Browser pane**, taking screenshots, inspecting the DOM, clicking elements and filling forms to check its changes; auto-verify is on by default, so this happens after every edit.

Server configuration lives in `.claude/launch.json` at the root of the selected folder, JSON with comments:

```json
{
  "version": "0.0.1",
  "autoVerify": true,
  "configurations": [
    { "name": "web", "runtimeExecutable": "npm", "runtimeArgs": ["run", "dev"], "port": 3000, "autoPort": true }
  ]
}
```

Other fields: `cwd` (working directory); `env` (environment variables — the file is committed, so no secrets); `program` and `args` (run a script with `node`); `url` (a custom origin, or a server you already run).

`autoPort` controls port conflicts: `true` picks a free port and passes it as `PORT`, `false` fails with an error, unset asks once and saves your answer.

The Browser pane is also a tabbed browser for external sites, on a clean profile with no saved logins. The first time Claude acts on an external site you choose **Allow once**, **Always allow** or **Deny**; safety classifiers review Claude's write actions on external pages in every permission mode. For work inside your own logged-in browser, use Claude in Chrome ([[chrome-and-computer-use]]).

## Manage sessions

- **Parallel sessions**: click **+ New session** (`Cmd+N`). The **worktree** option next to the branch isolates a session in a Git worktree ([[worktrees-and-background-work]]), defaulting to `<project-root>/.claude/worktrees/`; location and branch prefix are configurable in Settings, and `.worktreeinclude` copies gitignored files such as `.env` into new worktrees.
- **Split view**: `Cmd`-click / `Ctrl`-click a session in the sidebar.
- **Archive**: hover a session and click the archive icon. **Auto-archive after PR merge or close** in Settings → Claude Code archives finished local sessions.
- **Side chat**: `Cmd+;` or `/btw` asks a question with the session's context without adding anything back; not saved to disk.
- **Tasks pane**: subagents, background shell commands and dynamic workflows running in the current session.
- **Work across sessions**: ask which session touched something, or have Claude message, rename or archive another. Claude sees the 20 most recently active local, SSH and WSL Code-tab sessions — not cloud, terminal CLI or VS Code sessions — and always asks before archiving, in every permission mode.
- **Continue in** (the VS Code icon in the session toolbar): **Claude Code on the Web** pushes your branch and continues in the cloud, needing a clean working tree, unavailable for SSH sessions; **Your IDE** opens the project in a supported IDE.
- **From the CLI**: `/desktop` moves the current terminal session into Desktop, on macOS and x64 Windows when signed in with a subscription. Inside Desktop, `/resume` lists sessions started from the CLI.
- **Dispatch** (Pro and Max): message a task from your phone. Development tasks spawn a Code session with a **Dispatch** badge, with a push notification when it finishes or needs approval.
- **Scheduled tasks**: [[routines-and-scheduling]].

## Environments

### Local

The app doesn't always inherit your shell environment: on **macOS**, launched from the Dock or Finder, it reads only `PATH` and a fixed set of Claude Code variables from your shell profile; on **Windows** it inherits user and system variables but doesn't read PowerShell profiles.

For variables reaching both local sessions and dev servers, open the environment dropdown, hover **Local** and click the gear for the local environment editor; values saved there are encrypted. The `env` key in `~/.claude/settings.json` reaches Claude sessions only, not dev servers.

### SSH

**+ Add SSH connection** takes **Name**, **SSH Host** (`user@hostname` or a host from `~/.ssh/config`), **SSH Port** and **Identity File**. The remote host must run Linux or macOS; Desktop installs Claude Code there on first connect.

- SSH sessions support permission modes, connectors, plugins and MCP servers.
- They read `~/.claude/skills/` and the managed settings file from the remote host, not your machine.

### WSL

**Requirements**: Windows 10 or 11 with WSL 2 (WSL 1 isn't supported), at least one installed distribution, and `git` inside that distribution.

Pick the distribution from the **WSL** section of the environment picker, then choose a folder using Linux paths; workspace trust is granted per distribution and folder. Use WSL when the repository lives on the distribution's filesystem: reaching those files from Windows goes over a network filesystem, slow and breaking file watching.

- **Works**: parallel sessions, side chats, diff review, PR status and worktrees.
- **Not available yet**: integrated terminal, connectors, plugins, session forking, the file pane and `@` file suggestions.

## Extensions

- **Connectors** (local and SSH sessions): **+** → **Connectors** adds Google Calendar, Slack, GitHub, Linear, Notion and more — MCP servers with a graphical setup flow ([[mcp]]).
- **Skills**: type `/`, or **+** → **Slash commands**.
- **Plugins** (local and SSH sessions): **+** → **Plugins** → **Add plugin**. Not available in cloud or WSL sessions; for cloud sessions, declare it under `enabledPlugins` in the repo's `.claude/settings.json`, or enable it for your claude.ai account ([[plugins]]).
- **MCP**: local Code sessions also load servers from `claude_desktop_config.json`, and on a name clash that definition wins. The standalone CLI doesn't read it; run `claude mcp add-from-claude-desktop` to import those servers.

## Linux beta

Requires Ubuntu 22.04+ or Debian 12+ on x86_64 or arm64. Install from Anthropic's apt repository so updates arrive with your normal package upgrades:

```bash
sudo curl -fsSLo /usr/share/keyrings/claude-desktop-archive-keyring.asc https://downloads.claude.ai/claude-desktop/key.asc
gpg --show-keys /usr/share/keyrings/claude-desktop-archive-keyring.asc   # expect 31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE
echo "deb [arch=amd64,arm64 signed-by=/usr/share/keyrings/claude-desktop-archive-keyring.asc] https://downloads.claude.ai/claude-desktop/apt/stable stable main" | sudo tee /etc/apt/sources.list.d/claude-desktop.list
sudo apt update && sudo apt install claude-desktop
```

- **Launch**: open **Claude** from the application launcher, or run `claude-desktop`. Don't launch it as root.
- **Sign in**: with a claude.ai subscription or SSO. Console API keys aren't accepted.
- **Updates**: it doesn't update itself; run `sudo apt update && sudo apt upgrade`.
- **Not yet available on Linux**: computer use, dictation, and Fedora or RHEL.
- **Cowork on Linux** needs hardware virtualization on in firmware, the QEMU and UEFI packages apt installs as recommended packages, and membership in the `kvm` group: `sudo usermod -aG kvm $USER`, then log out and back in.

## Enterprise controls

The admin console at claude.ai/admin-settings/claude-code toggles Code in the desktop, Code in the web, Remote Control and Bypass permissions mode. Desktop reads these managed settings keys:

| Key | Effect |
|---|---|
| `sshConfigs` | Pre-configured SSH connections users can't edit (each needs `id`, `name`, `sshHost`) |
| `sshHostAllowlist` | Host patterns such as `*.devboxes.example.com`. An empty array disables SSH. Managed settings only, Desktop only |
| `disableDesktopLocalSessions` | `true` turns off Code sessions that run on the device |
| `browserExternalPageTools` | `"disabled"` stops Claude's tools from reading or acting on external Browser pages |
| `disableBrowserExternalNavigation` | `true` blocks all external navigation in the Browser pane |
| `disableMobileSimulatorTools` | `true` removes Claude's control of the iOS Simulator pane |

Policy delivery depends on session type: **cloud sessions** receive server-managed settings, not files on the device; **SSH sessions** read the managed settings file on the remote host.

MDM configuration uses the `com.anthropic.claudefordesktop` preference domain on macOS and the registry path `SOFTWARE\Policies\Claude` on Windows. General policy delivery: [[enterprise-admin]].

## Not available in Desktop

- Agent teams (use dynamic workflows, or have Claude message your other sessions)
- Inline code suggestions
- `--print` scripting and the `dontAsk` mode

Commands that open a terminal dialog behave differently: those with no argument form, such as `/permissions`, reply `isn't available in this environment`; `/config` opens Settings instead.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Error 403: Forbidden` in the Code tab | Sign out and back in; confirm a paid plan; quit the app completely and reopen |
| Tools like `npm` not found | Fix `PATH` in your shell profile and restart the app, or set it in the local environment editor |
| "Git LFS is required by this repository" | Install Git LFS, run `git lfs install`, restart the app |
| "Branch doesn't exist yet" for a cloud branch | `git fetch origin <branch-name>`, then `git checkout <branch-name>` |
| Blank screen on a managed network | Allow the Anthropic, claude.ai and claude.com CDN hosts through the firewall |
