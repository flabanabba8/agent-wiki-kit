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
  - raw/docs/changelog-2.1.275-to-2.1.282.md
related: ["[[install-and-setup]]", "[[permissions-and-modes]]", "[[mcp]]", "[[plugins]]", "[[chrome-and-computer-use]]", "[[desktop-app]]"]
created: 2026-09-15
updated: 2026-09-25
confidence: high
last_verified: 2026-09-25
aliases: [vs-code-extension, jetbrains-plugin, cursor-extension, ide-mcp-server, claude-code-in-intellij]
---

# IDE Integrations (VS Code and JetBrains)

The **VS Code extension** is a graphical chat panel that also installs in Cursor and other forks. The **JetBrains plugin** runs the `claude` CLI in the IDE's terminal. Both run a hidden local MCP server named `ide` for native diffs, selection context and diagnostics.

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
- Install "Claude Code" from the Extensions view or the Open VSX registry; it works in Cursor and forks such as Kiro.
- Open Claude from the Spark icon in the Editor Toolbar (shown only when a file is open), the Activity Bar sessions list, or the Command Palette.
- If `ANTHROPIC_API_KEY` is set but you get the sign-in screen, launch VS Code with `code .` so it inherits your environment.
- Typing `claude` in the integrated terminal requires the standalone CLI install, because the bundled copy is private.

### Prompt box

- **Permission modes**: click the mode indicator to switch between Auto, Manual, Plan and Edit automatically. Plan opens the plan as a Markdown document that you can comment on inline. What each mode does is in [[permissions-and-modes]].
- **Model and effort**: click the model name or choose **Switch model…** from the `/` menu. An **Effort** row appears for models that support effort levels; a level other than `max` is saved as that model's default under `modelSettings` in user settings, while `max` lasts one session.
- **Command menu** (`/`):
  - attach files and toggle extended thinking
  - a Customize section for MCP servers, commands, output styles, hooks, permissions and plugins, plus **Memory** (auto-memory toggles, memory folders, and viewing, editing or deleting a saved memory) and **Instructions** (editing the CLAUDE.md files)
  - hooks and permission rules that come from managed settings or plugins are read-only there
- **Context**:
  - Selected text is sent automatically, except from files matching `files.exclude`, `search.exclude` or (with `respectGitIgnore` on) `.gitignore`, where Claude gets at most the path. The open file's name is sent too, unless you turn off `attachOpenFile`.
  - Type `@` for fuzzy file or folder mentions, and `@terminal:name` to include a terminal's output.
  - Type `@browser` for Chrome tasks ([[chrome-and-computer-use]]).
  - Paste images, or hold `Shift` while dragging files in. An image can be sent without text. A paste over 800 characters or 2 line breaks is marked so Claude can tell it from typing, and invisible Unicode formatting characters are stripped.
- **Indicators**:
  - a context-window meter
  - a prompt-cache clock that counts down the cache lifetime and turns red once the cache has likely expired
  - an agent count such as **2 agents**, which opens a map of subagents, background shells and other running tasks, each with a Stop; typed `/tasks` opens the same map
- **Side questions**: `/btw <question>` answers in a side panel without adding to the conversation.
- **Focus view**: `Ctrl+Option+F` / `Ctrl+Alt+F` hides tool calls and thinking behind expandable rows.
- **Typed commands open dialogs**:
  - `/usage` opens Account & usage; on Vertex, Bedrock, Foundry and API keys it shows session cost and tokens instead of plan limits.
  - `/plugins` opens the plugin manager with user, project or local scopes ([[plugins]]); `/mcp` adds, removes, enables and authenticates servers ([[mcp]]).
  - `/status`, `/sandbox`, `/chrome`, `/export`, `/skills` (each skill's visibility, such as **On** or **Name only**, changeable except on **locked** rows), `/tasks`, `/copy`, `/logout`, `/hooks`, `/memory` (view, edit and delete saved memories) and `/rewind` open their dialogs; `/plan` enters plan mode (with a task, starts planning it) or shows the plan; `/plan open` opens the plan file.
- **Billed classifier fallback**: when auto mode falls back to billed classifier requests, the VS Code and JetBrains panels ask Continue or Stop.

### Sessions, tabs and checkpoints

- **Session history** has **Local** and **Web** tabs. The Web tab lists cloud sessions started with a GitHub repository ([[claude-code-on-the-web]]). It needs a Claude.ai subscription sign-in, and local changes are not synced back.
- **Auto-archive**: sessions inactive for 14 days move to **Archived sessions** unless they are open, unread or grouped; the **Archived sessions** header can unarchive all at once. Change this with `archiveInactiveSessions` (`1`, `2`, `7`, `14`, or `0` to turn it off).
- **Parallel conversations**: use **Open in New Tab** (`Cmd+Shift+Esc` / `Ctrl+Shift+Esc`), which opens beside your current editor group, or **Open in New Window**. A blue tab dot means a pending permission request; orange means Claude finished while hidden.
- **Shared history**: the extension and CLI share conversation history, so `claude --resume` in a terminal can pick up an extension conversation.
- **Reviewing edits**: the proposed-change diff has **Accept this change** / **Reject this change** buttons under each change (also **Accept/Reject Change at Cursor** in the Command Palette); diffs over 100 changes are reviewed as a whole file.
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
| `lockEditorGroups` | `true` | Lock the editor groups Claude opens tabs in, so your files open elsewhere |
| `scrollToBottomOnSend` | `true` | Scroll to the bottom when you send |
| `continueAfterReload` | `true` | Continue the step a window reload interrupted (under an hour old, not open elsewhere) |

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

For CLI-only features, run `claude` in the integrated terminal. If you run `claude` in an external terminal, use `/ide` to connect it to VS Code.

### Third-party providers

Turn on **Disable Login Prompt**, then configure Bedrock, Agent Platform or Foundry in `~/.claude/settings.json` ([[cloud-providers]]). Features that need a claude.ai account are unavailable: plan usage bars, voice dictation and the Web tab.

### Uninstall

Uninstall from the Extensions view. Running `claude` in a VS Code terminal reinstalls the extension automatically. To prevent that:

- turn off **Auto-install IDE extension** in `/config`
- set `autoInstallIdeExtension` to `false`
- set `CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL=1`

## JetBrains plugin

The plugin works with IntelliJ IDEA, PyCharm, WebStorm, GoLand and most other JetBrains IDEs.

1. Install the CLI. Without `claude` on PATH, the plugin shows "Cannot launch Claude Code".
2. Install the Claude Code plugin from the JetBrains Marketplace and restart the IDE.
3. Run `claude` in the IDE's integrated terminal, or `/ide` from an external terminal, which confirms with `Connected to IntelliJ IDEA.` and installs the plugin if the IDE lacks it. `claude --ide` connects at startup when exactly one valid IDE is available.

**Configuration**

- **Diff tool**: in `/config`, set **Diff tool** to `auto` for the IDE diff viewer or `terminal` to keep diffs in the terminal (setting `diffTool`). The entry appears only while Claude Code is connected to the IDE.
- **Plugin settings**: under **Settings → Tools → Claude Code [Beta]**, the **Claude command** field accepts a custom command such as `/usr/local/bin/claude` or `npx @anthropic-ai/claude-code`. On WSL, use `wsl -d Ubuntu -- bash -lic "claude"`.
- **Esc key**: if it doesn't interrupt Claude, uncheck "Move focus to the editor with Escape" in terminal settings.
- **Remote Development**: install the plugin on the remote host, not the local client.
- **Diagnostics**: Claude calls `getDiagnostics` itself; nothing is requested automatically after edits.

**WSL2 "No available IDEs detected"**: NAT networking or Windows Firewall blocks the connection. Fixes:

- A firewall rule for your WSL subnet from an elevated PowerShell: `New-NetFirewallRule -DisplayName "Allow WSL2 Internal Traffic" -Direction Inbound -Protocol TCP -Action Allow -RemoteAddress 172.21.0.0/16 -LocalAddress 172.21.0.0/16`.
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

In auto-edit modes, Claude can modify IDE configuration files the IDE may execute, such as `settings.json` or `tasks.json`. With untrusted code, use Manual mode, and in VS Code enable Restricted Mode.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Spark icon missing | Open a file (a folder alone isn't enough), run "Developer: Reload Window", disable conflicting AI extensions, and check workspace trust (no Restricted Mode) |
| `Cmd+Esc` does nothing on macOS Tahoe | Clear the Game Overlay shortcut under Keyboard Shortcuts → Game Controllers, or rebind `Claude Code: Focus input` |
| `Not logged in · Please run /login` with no sign-in screen | Run "Developer: Reload Window" |
| JetBrains "command not found" | Check `claude --version` and set the Claude command path in plugin settings |
