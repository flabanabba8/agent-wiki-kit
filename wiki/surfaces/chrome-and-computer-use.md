---
title: Claude in Chrome and Computer Use
type: how-to
tldr: "Browser automation and screen control"
sources:
  - raw/docs/official/chrome.md
  - raw/docs/official/computer-use.md
  - raw/docs/official/desktop.md
  - raw/docs/official/vs-code.md
  - raw/docs/official/cli-reference.md
  - raw/docs/changelog-2.1.275-to-2.1.278.md
related: ["[[desktop-app]]", "[[ide-integrations]]", "[[mcp]]", "[[sandboxing-and-security]]", "[[permissions-and-modes]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [claude-in-chrome, browser-automation, computer-use, screen-control, chrome-extension]
---

# Claude in Chrome and Computer Use

Claude Code has two ways to operate graphical interfaces:

- **Claude in Chrome** drives your real, logged-in browser through an extension.
- **Computer use** clicks, types and takes screenshots in native apps on your desktop.

Computer use is the broadest and slowest option, so Claude tries more precise tools first:

1. An MCP server or connector for the service ([[mcp]])
2. Bash, for shell tasks
3. Claude in Chrome, for browser work when it's set up
4. The iOS Simulator pane, for iOS apps in Desktop
5. Computer use, for everything else: native apps, simulators and tools with no API

| | Claude in Chrome | Desktop Browser pane | Computer use |
|---|---|---|---|
| Surfaces | CLI, VS Code | Desktop app | CLI (macOS), Desktop (macOS, Windows) |
| Identity | Your browser's logins | Clean profile, no logins | Whichever apps you approve |
| Plans | Pro, Max, Team, Enterprise | Paid plans with Desktop | Pro and Max only |
| Setup | Extension plus `claude --chrome` | Built in | `/mcp` in the CLI, or the Settings toggle in Desktop |

The Desktop Browser pane is covered in [[desktop-app]].

## Claude in Chrome

### Requirements

- **Browser**: Google Chrome or Microsoft Edge. Claude Code also detects the extension in Brave, Arc, Vivaldi and Opera. It isn't supported in WSL.
- **Extension**: Claude in Chrome version 1.0.36 or later, from the Chrome Web Store.
- **Account**: a direct Anthropic plan, signed in with `/login`.
  - API-key auth and `claude setup-token` tokens keep the integration off, even with `--chrome`.
  - It isn't available through Bedrock, Agent Platform or Foundry.

### Set up

```bash
claude --chrome
```

The first launch shows a one-time intro dialog. After that, ask for a browser task, for example: "Go to code.claude.com/docs, click the search box, type hooks, and tell me what results appear." Permission prompts start with `Claude in Chrome wants to` and let you allow all actions on that site for the session.

- **`/chrome`**:
  - Shows connection status. The integration works when it reads "Status: Enabled" and "Extension: Installed".
  - **Reconnect extension** restores a dropped connection.
  - **Select browser…** chooses among connected browsers.
  - **Enabled by default** loads browser tools in every session, which costs context. `--no-chrome` turns the integration off for one session.
- **Install prompt**: if Claude needs a browser and finds no extension, an interactive session offers **Install extension**, **Not now** or **Don't ask again**. The prompt is suppressed when `deniedMcpServers` blocks the `claude-in-chrome` server.
- **VS Code**: no flag is needed. Type `@browser` followed by the task ([[ide-integrations]]).
- **Permissions**: site permissions come from the Chrome extension's own settings. In plan mode, recording a GIF, opening a new tab or running a shortcut also prompts first ([[permissions-and-modes]]). In auto mode, calls the classifier approves skip the extension's per-site check, as they do in bypass mode.
- **Tool list**: run `/mcp`, select `claude-in-chrome`, then **View tools**.

### How it behaves

Claude opens tabs in a visible Chrome window and groups them into a tab group for the session.

- `/clear` closes the group, including open pages.
- Exiting, or switching sessions with `/resume`, closes the group only if it holds nothing but empty tabs.

When Claude hits a login page or CAPTCHA, it pauses and asks you to handle it.

Typical uses:

- **Live debugging**: "Open the dashboard page and check the console for any errors when the page loads." Name the patterns you care about, because console logs are verbose.
- **Testing local apps**: submit a form on `localhost:3000` with invalid data and check that the error messages appear.
- **Authenticated web apps**: write in Google Docs, Gmail or Notion without API connectors.
- **Form filling and extraction**: enter rows from a local CSV into a web CRM, or scrape product listings into a CSV file.
- **File uploads**:
  - Up to 10 MB of files per upload.
  - `Read` deny rules also block uploading the file.
  - Files with multiple hard links (common inside `node_modules`) are refused; upload a copy instead.
- **GIF recordings and screenshots saved to disk**. Recordings capture account details on logged-in pages, so review them before sharing.

### Troubleshooting

| Error | Fix |
|---|---|
| "Browser extension is not connected" | Restart Chrome and Claude Code, then run `/chrome`. If your organization uses IP allowlisting, route `bridge.claudeusercontent.com` through your allowlisted egress |
| Extension "Not detected" in `/chrome` | Install or enable it in `chrome://extensions` |
| "No tab available" | Ask Claude to open a new tab and retry |
| "Receiving end does not exist", or tools stop after idle time | The extension's service worker went idle: `/chrome` → "Reconnect extension" |
| Browser commands stop responding | Dismiss any JavaScript alert, confirm or prompt dialog blocking the page |

First-time setup writes a native messaging host file, which Chrome reads only at startup. If the extension isn't detected on the first try, restart Chrome. If it's still missing, check that the file `com.anthropic.claude_code_browser_extension.json` exists:

- **macOS**: `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/`
- **Linux**: `~/.config/google-chrome/NativeMessagingHosts/`
- **Windows**: the registry key `HKCU\Software\Google\Chrome\NativeMessagingHosts\`

On Windows, an `EADDRINUSE` named-pipe conflict means another process holds the pipe. Close other Claude Code sessions that might be using Chrome and restart Claude Code.

## Computer use

Computer use is a research preview for Pro and Max only; it isn't available on Team or Enterprise.

- It needs claude.ai auth and an interactive session, so it doesn't run with `-p`.
- It isn't available in the Linux desktop app.

### Enable

**CLI (macOS only)**

1. Run `/mcp`, select the built-in `computer-use` server and choose **Enable**. The setting persists per project.
2. On first use, grant two macOS permissions, then select **Try again**. You may need to restart Claude Code after granting Screen Recording.
   - **Accessibility** lets Claude click, type and scroll.
   - **Screen Recording** lets Claude see the screen.

**Desktop (macOS and Windows)**

- Go to **Settings > General** (under **Desktop app**) and turn on **Computer use**. On Windows it takes effect immediately; macOS also needs the two permissions above.
- Desktop adds a **Denied apps** list and an **Unhide apps when Claude finishes** toggle.
- On macOS, computer use can run in the background on approved apps while you keep working.
- Dispatch-spawned sessions can use computer use; their app approvals expire after 30 minutes.

### App approval and control tiers

Enabling computer use grants no app access by itself. The first time Claude needs an app in a session, you choose **Allow for this session** or **Deny**. The prompt also shows any extra permissions requested, such as clipboard access, and how many apps will be hidden.

| Tier | What Claude can do | Applies to |
|---|---|---|
| View only | See the app in screenshots | Browsers, trading platforms |
| Click only | Click and scroll, but not type or use shortcuts | Terminals, IDEs |
| Full control | Click, type, drag, use shortcuts | Everything else |

Apps with broad reach get an extra warning before you approve them:

- Terminals and IDEs: "Equivalent to shell access"
- Finder: "Can read or write any file"
- System Settings: "Can change system settings"

Approve Finder to let Claude click the desktop, the Dock or a Finder window.

### How it runs

- **One session at a time**: a session takes a lock at its first computer use action and releases it when the session exits. A second session gets "Computer use is in use by another Claude session".
- **Other apps are hidden** while Claude works and restored when the turn ends. Your terminal stays visible but is excluded from screenshots.
- **Screenshots are downscaled automatically.** A 3456×2234 Retina capture becomes roughly 1372×887. If text is too small for Claude to read, enlarge it in the app rather than changing your display resolution.
- **Stopping**: press `Esc` anywhere, or `Ctrl+C` in the terminal. Claude stops and unhides your apps, and the Esc keypress is consumed so on-screen content can't use it.

### Safety

Computer use isn't sandboxed like the Bash tool ([[sandboxing-and-security]]). It acts on your real desktop with whatever you approve. The built-in guardrails are:

- per-app approval for each session
- warnings on apps with shell, file or system-settings reach
- the terminal excluded from screenshots
- a global `Esc` to abort
- the single-session lock

Claude also flags potential prompt injection from on-screen content.

Example prompt: "Build the MenuBarStats target, launch it, open the preferences window, and verify the interval slider updates the label. Screenshot the preferences window when you're done."

**`computer-use` missing from `/mcp`?** Check that:

- you're on macOS
- you have a Pro or Max plan (confirm with `/status`)
- you're signed in through claude.ai, not a third-party provider
- the session is interactive

**macOS permission prompt keeps coming back?** Quit Claude Code completely, then confirm your terminal app is listed and enabled under Privacy & Security > Screen Recording.
