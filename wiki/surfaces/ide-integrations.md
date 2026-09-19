---
title: IDE Integrations (VS Code and JetBrains)
type: reference
tldr: "VS Code extension and JetBrains plugin setup"
sources:
  - raw/docs/official/vs-code.md
  - raw/docs/official/jetbrains.md
  - raw/docs/official/cli-reference.md
  - raw/docs/official/commands.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
  - raw/docs/changelog-2.1.275-to-2.1.278.md
related: ["[[install-and-setup]]", "[[permissions-and-modes]]", "[[mcp]]", "[[plugins]]", "[[chrome-and-computer-use]]", "[[desktop-app]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [vs-code-extension, jetbrains-plugin, cursor-extension, ide-mcp-server, claude-code-in-intellij]
---

# IDE Integrations (VS Code and JetBrains)

Claude Code plugs into two IDE families. The **VS Code extension** is a graphical chat panel that also installs in Cursor and other VS Code forks. The **JetBrains plugin** runs the `claude` CLI in the IDE's integrated terminal and wires it to the editor. Both run a hidden local MCP server named `ide`, which the CLI uses for native diffs, selection context and diagnostics.

| | VS Code extension | JetBrains plugin |
|---|---|---|
| Interface | Graphical panel (terminal mode optional) | CLI in the integrated terminal |
| Bundles the CLI | Yes, a private copy that is not put on PATH | No, so install the CLI first |
| Focus / launch | `Cmd+Esc` / `Ctrl+Esc` toggles focus | `Cmd+Esc` / `Ctrl+Esc` opens Claude Code |
| Insert file reference | `Option+K` / `Alt+K` inserts `@app.ts#5-10` | `Cmd+Option+K` / `Alt+Ctrl+K` inserts `@src/auth.ts#L1-99` |
| Model-visible IDE tools | `mcp__ide__getDiagnostics`, `mcp__ide__executeCode` | `mcp__ide__getDiagnostics` |

Both work with any paid Claude subscription or a Claude Console account; the standalone CLI install is in [[install-and-setup]].

## VS Code extension

### Install and open

- Requires VS Code 1.94.0 or later.
- In the Extensions view (`Cmd+Shift+X` / `Ctrl+Shift+X`), search "Claude Code" and install it. The same extension works in Cursor and in forks such as Kiro, or you can install it from the Open VSX registry.
- Open Claude from any of these:
  - the Spark icon in the Editor Toolbar (shown only when a file is open)
  - the Activity Bar sessions list
  - the Command Palette ("Claude Code: Open in New Tab")
  - the Status Bar item, when Claude is docked in the sidebar
- The first open shows a sign-in screen. If `ANTHROPIC_API_KEY` is set in your shell but you still get the prompt, launch VS Code from a terminal with `code .` so it inherits your environment.
- Typing `claude` in the integrated terminal requires the standalone CLI install, because the bundled copy is private.

### Prompt box

- **Permission modes**: click the mode indicator to switch between Auto, Manual, Plan and Edit automatically. Plan opens the plan as a Markdown document that you can comment on inline. What each mode does is in [[permissions-and-modes]].
- **Model and effort**: click the model name or choose **Switch model…** from the `/` menu. An **Effort** row appears for models that support effort levels.
- **Command menu** (`/`):
  - attach files and toggle extended thinking
  - a Customize section for MCP servers, commands, output styles, hooks, permissions and plugins, plus **Memory** (auto-memory toggles, memory folders, and viewing, editing or deleting a saved memory) and **Instructions** (editing the CLAUDE.md files)
  - hooks and permission rules that come from managed settings or plugins are read-only there
- **Context**:
  - Selected text is sent automatically. The open file's name is sent too, unless you turn off `attachOpenFile`.
  - Type `@` for fuzzy file or folder mentions, and `@terminal:name` to include a terminal's output.
  - Type `@browser` for Chrome tasks ([[chrome-and-computer-use]]).
  - Paste images, or hold `Shift` while dragging files in.
- **Indicators**:
  - a context-window meter
  - a prompt-cache clock that counts down the cache lifetime and turns red once the cache has likely expired
  - an agent count such as **2 agents**, which opens a map of subagents, background shells and other running tasks, each with a Stop; typed `/tasks` opens the same map
- **Side questions**: `/btw <question>` answers in a side panel without adding to the conversation.
- **Focus view**: `Ctrl+Option+F` / `Ctrl+Alt+F` hides tool calls and thinking behind expandable rows.
- **Panel menu**: **Sign out** (also `/logout`), and **Copy response** on any reply (also `/copy`).
- **Proposed changes**: the diff tab carries accept and reject buttons under each change, so an edit can be reviewed change by change.
- **Other dialogs**:
  - `/usage` opens Account & usage (claude.ai sign-in only), which also shows the session's cost and token usage where plan limits don't apply.
  - `/plugins` opens the plugin manager, with Plugins and Marketplaces tabs and user, project or local install scopes ([[plugins]]).
  - `/mcp` adds, removes, enables and authenticates MCP servers ([[mcp]]).

### Sessions, tabs and checkpoints

- **Session history** has **Local** and **Web** tabs. The Web tab lists cloud sessions started with a GitHub repository ([[claude-code-on-the-web]]). It needs a claude.ai subscription sign-in, and local changes are not synced back.
- **Auto-archive**: sessions inactive for 14 days move to **Archived sessions** unless they are open, unread or grouped, with a one-time notice the first time and an **Unarchive all** action on the group. Change this with `archiveInactiveSessions` (`1`, `2`, `7`, `14`, or `0` to turn it off).
- **Groups**: right-click a session to put it in a named group.
- **Parallel conversations**: use **Open in New Tab** (`Cmd+Shift+Esc` / `Ctrl+Shift+Esc`) or **Open in New Window**. On a tab icon, a blue dot means a permission request is pending and an orange dot means Claude finished while the tab was hidden.
- **Shared history**: the extension and CLI share conversation history, so `claude --resume` in a terminal can pick up an extension conversation.
- **Rewind**: hover a message and choose **Fork conversation from here**, **Rewind code to here**, or **Fork conversation and rewind code** ([[sessions-and-checkpoints]]).

### Key extension settings

| Setting | Default | Purpose |
|---|---|---|
| `useTerminal` | `false` | Launch the CLI-style interface instead of the panel |
| `initialPermissionMode` | unset | `default`, `plan`, `acceptEdits`, `bypassPermissions` (`manual` is an alias for `default`). Read from user settings only |
| `preferredLocation` | `panel` | `sidebar` or `panel`; **New session** in an editor tab follows it |
| `autosave` | `true` | Save files before Claude reads or writes them |
| `useCtrlEnterToSend` | `false` | Send with Ctrl/Cmd+Enter |
| `enableNewConversationShortcut` | `false` | Cmd/Ctrl+N starts a conversation |
| `environmentVariables` | `[]` | Env vars for the Claude process |
| `disableLoginPrompt` | `false` | Skip auth prompts (third-party providers) |
| `allowDangerouslySkipPermissions` | `false` | Add Bypass permissions to the mode selector |
| `claudeProcessWrapper` | unset | Executable that launches Claude, such as a separately installed `claude` |
| `lockEditorGroups` | — | Set it to stop Claude from locking the editor groups it opens in |
| **Claude Code: Continue After Reload** | — | Carries on the step a window reload interrupted, labeled in the chat; turn it off to stop that |

Shared configuration (permissions, hooks, MCP, env) belongs in `~/.claude/settings.json`, which the extension and the CLI both read ([[settings]]).

### Launch from other tools

The extension registers `vscode://anthropic.claude-code/open`, with optional `prompt` (URL-encoded text prefilled but not sent) and `session` (a session ID to resume):

```bash
open "vscode://anthropic.claude-code/open?prompt=review%20my%20changes"   # xdg-open on Linux
```

`vscode://anthropic.claude-code/install-plugin?plugin=<name>&marketplace=<owner/repo>` opens the plugin dialog on a single plugin. Nothing installs until the user picks a scope.

### Extension vs CLI

| Feature | CLI | Extension |
|---|---|---|
| Commands and skills | All | Subset (type `/`) |
| MCP config, checkpoints | Yes | Yes |
| `!` Bash shortcut, tab completion | Yes | No |

Background-task visibility is also more limited in the extension. For CLI-only features, run `claude` in the integrated terminal. If you run `claude` in an external terminal, use `/ide` to connect it to VS Code.

### Third-party providers

Turn on **Disable Login Prompt**, then configure Bedrock, Agent Platform or Foundry in `~/.claude/settings.json` ([[cloud-providers]]). Features that need a claude.ai account are unavailable: usage tracking, voice dictation and the Web tab.

### Uninstall

Uninstall from the Extensions view. Running `claude` in a VS Code terminal reinstalls the extension automatically. To prevent that:

- turn off **Auto-install IDE extension** in `/config`
- set `autoInstallIdeExtension` to `false`
- set `CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL=1`

## JetBrains plugin

The plugin works with IntelliJ IDEA, PyCharm, Android Studio, WebStorm, PhpStorm, GoLand and most other JetBrains IDEs.

1. Install the CLI. Without `claude` on PATH, the plugin shows "Cannot launch Claude Code".
2. Install the Claude Code plugin from the JetBrains Marketplace and restart the IDE.
3. Run `claude` in the IDE's integrated terminal, or `/ide` from an external terminal, which confirms with `Connected to IntelliJ IDEA.` and installs the plugin if the IDE lacks it. `claude --ide` connects at startup when exactly one valid IDE is available.

Start Claude Code from the IDE project root so both see the same files.

**Configuration**

- **Diff tool**: in `/config`, set **Diff tool** to `auto` for the IDE diff viewer or `terminal` to keep diffs in the terminal (setting `diffTool`). The entry appears only while Claude Code is connected to the IDE.
- **Plugin settings**: under **Settings → Tools → Claude Code [Beta]**, the **Claude command** field accepts a custom command such as `/usr/local/bin/claude` or `npx @anthropic-ai/claude-code`. On WSL, use `wsl -d Ubuntu -- bash -lic "claude"`.
- **Esc key**: if Esc doesn't interrupt Claude, uncheck "Move focus to the editor with Escape" under **Settings → Tools → Terminal**.
- **Remote Development**: install the plugin on the remote host (**Settings → Plugin (Host)**), not on the local client.
- **Diagnostics**: Claude reads inspection results by calling `getDiagnostics` itself. It does not request them automatically after edits.

**WSL2 "No available IDEs detected"**: WSL2's NAT networking or Windows Firewall is blocking the connection. There are two fixes:

- Add a firewall rule for your WSL subnet from an elevated PowerShell: `New-NetFirewallRule -DisplayName "Allow WSL2 Internal Traffic" -Direction Inbound -Protocol TCP -Action Allow -RemoteAddress 172.21.0.0/16 -LocalAddress 172.21.0.0/16`.
- On Windows 11 22H2 or later, set `networkingMode=mirrored` under `[wsl2]` in `.wslconfig`, then run `wsl --shutdown`.

## The built-in `ide` MCP server

The extension or plugin runs a local MCP server named `ide` that is hidden from `/mcp`. You need to know about it if a `PreToolUse` hook allowlists MCP tools ([[hooks]]).

**Auth and transport**

- Each activation writes a random token to `~/.claude/ide/<port>.lock`, or `$CLAUDE_CONFIG_DIR/ide/` when that variable is set.
- The CLI presents the token as the `X-Claude-Code-Ide-Authorization` header over unencrypted loopback `ws://`.
- VS Code binds `127.0.0.1` on a random port between 10000 and 65535. JetBrains uses an ephemeral port.
- JetBrains's **Accept connections from all network interfaces** setting exposes the port to your LAN, with traffic and token in cleartext; for WSL use mirrored networking instead.

**Context**: while connected, the current selection and active file path are attached to each prompt. The transcript shows this as `⧉ Selected N lines from <file>`. A `Read` deny rule for a path such as `.env` blocks both.

**Model-visible tools**

- `mcp__ide__getDiagnostics` (read-only) is available in both IDEs.
- `mcp__ide__executeCode` exists only in VS Code. It runs Python in the active Jupyter kernel by inserting a cell, and always asks **Execute** or **Cancel** in a Quick Pick, even when a hook allowlists the tool.

## Security

In auto-edit modes, Claude can modify IDE configuration files that the IDE may execute, such as VS Code's `settings.json` or `tasks.json`. With untrusted code:

- use Manual mode and review each change
- in VS Code, enable Restricted Mode for untrusted workspaces
- in JetBrains, keep Claude to trusted prompts, because `acceptEdits` and auto mode approve edits inside the working directory

## Troubleshooting

| Symptom | Fix |
|---|---|
| Spark icon missing | Open a file (a folder alone isn't enough), confirm VS Code 1.94.0+, run "Developer: Reload Window", disable conflicting AI extensions, and check workspace trust (the extension doesn't work in Restricted Mode) |
| `Cmd+Esc` does nothing on macOS Tahoe | Clear the Game Overlay shortcut under Keyboard Shortcuts → Game Controllers, or rebind `Claude Code: Focus input` |
| `Not logged in · Please run /login` with no sign-in screen | Run "Developer: Reload Window" |
| JetBrains "command not found" | Check `claude --version` and set the Claude command path in plugin settings |
| JetBrains features missing | Run from the project root, confirm the plugin is enabled, fully restart the IDE |
