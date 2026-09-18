---
title: computer-use-linux MCP Server
type: entity
tldr: "MCP server that drives a real Linux desktop"
sources:
  - raw/docs/computer-use-linux/README.md
  - raw/docs/computer-use-linux/SKILL.md
  - raw/docs/computer-use-linux/CHANGELOG.md
  - raw/docs/computer-use-linux/SECURITY.md
  - raw/docs/computer-use-linux/CONTRIBUTING.md
related: ["[[chrome-and-computer-use]]", "[[mcp]]", "[[sandboxing-and-security]]", "[[openai-codex]]"]
created: 2026-09-15
updated: 2026-09-15
confidence: high
last_verified: 2026-09-15
aliases: [linux-computer-use, desktop-control-mcp, at-spi-mcp, wayland-computer-use]
---

# computer-use-linux MCP Server

`computer-use-linux` (agent-sh, MIT, written in Rust) is an MCP server and CLI that controls the Linux desktop you're already logged into. It reads AT-SPI accessibility trees, lists and focuses windows, takes screenshots, and sends clicks, drags, scrolls and keystrokes. It targets Wayland first and supports X11 on a best-effort basis, across GNOME, KDE/KWin, Hyprland, i3 and COSMIC. Any stdio MCP host can use it, including Claude Code, Claude Desktop, Codex Desktop's Linux build (which bundles it) and Hermes Agent. For Claude Code's own computer use, see [[chrome-and-computer-use]]. Consider this server when you need Linux desktop control through MCP.

## Install

| Option | Command | What you still set up |
|---|---|---|
| npm wrapper | `npm install -g @agent-sh/computer-use-linux` | `ydotoold`, AT-SPI |
| crates.io | `cargo install computer-use-linux` | `ydotoold`, AT-SPI, portals, GNOME extension |
| From a clone | `./install.sh` | Nothing. It installs distro packages, builds both binaries into `~/.local/bin`, enables `ydotoold` as a user service, turns on GNOME AT-SPI, and installs the GNOME Shell extension on GNOME Wayland |
| Prebuilt | Release assets for x86_64 and aarch64, each with a `.sha256` | Copy both `computer-use-linux` and `computer-use-linux-cosmic` |

For the manual paths, finish system setup with:

```bash
sudo apt install ydotool at-spi2-core
systemctl --user enable --now ydotoold
computer-use-linux setup                     # enables GNOME toolkit-accessibility
computer-use-linux setup-window-targeting    # GNOME Shell extension; log out and back in
```

## Register with Claude Code

```bash
claude mcp add --scope user computer-use-linux -- computer-use-linux mcp
claude mcp list
```

`--scope project` writes the server to `.mcp.json` instead. Scopes are explained in [[mcp]]. Inside a session, `/mcp` confirms the tools loaded. If the binary isn't on `PATH`, give its absolute path. The server speaks rmcp 2024-11-05 over stdio and takes `mcp` as its only argument.

## First-run checklist

1. Run `computer-use-linux doctor | jq .readiness`. You want `can_register_mcp_tools`, `can_build_accessibility_tree`, `can_send_development_input` and `can_query_windows` all true, and `blockers: []`.
2. If `accessibility.at_spi_bus.ok = false`, run `computer-use-linux setup`, then restart the apps you want to drive.
3. If `windowing.can_list_windows = false` on GNOME Wayland, run `setup-window-targeting` and log out and back in.
4. The first screenshot triggers a screencast portal prompt. Accept it and tick "remember".
5. Check that the `ydotoold` socket exists at `/run/user/$UID/.ydotool_socket`.

## Tools and safety classes

Every tool carries MCP `ToolAnnotations`. The server's CI fails if those annotations drift from the table below.

| Class | Tools | Hints |
|---|---|---|
| Read-only observation | `doctor`, `list_apps`, `list_windows`, `focused_window`, `get_app_state` | `readOnlyHint=true` |
| Local setup mutators | `setup_accessibility`, `setup_window_targeting` | idempotent, non-destructive |
| UI state mutators | `activate_window`, `scroll`, `screenshot` | non-destructive |
| Desktop action mutators | `click`, `drag`, `press_key`, `type_text`, `perform_action`, `set_value` | `destructiveHint=true`, `openWorldHint=true` |

These annotations are hints, not authorization. The README tells hosts to still ask the user before any submit, delete, send or purchase. Use Claude Code permission rules for that (see [[sandboxing-and-security]]).

Tips from the bundled skill:

- Start every session with `doctor`.
- Prefer semantic targets from `get_app_state`, meaning element indices or `role`/`name`/`text`/`states` selectors, over pixel coordinates.
- Give `type_text` an explicit target (`window_id`, `pid`, `app_id`, `wm_class`, `title`, `tty`, `terminal_pid`, `terminal_command` or `terminal_cwd`). Otherwise input goes to whichever window has focus.
- After each mutating action, re-read state.
- Avoid concurrent calls.

Screenshots are capped by default at 1920 px and 2 MiB. You can pass `max_width`, `max_height`, `max_bytes`, `scale`, `format: "jpeg"` or `quality`.

## Backends and environment

Window targeting tries these backends in order: the GNOME Shell extension, GNOME Introspect, the COSMIC helper, KWin scripting, Hyprland `hyprctl`, then i3 IPC. Sway and generic X11 have no window backend, but AT-SPI, screenshots and global `ydotool` input still work there. Screenshots try GNOME Shell DBus, then the XDG portal, then `gnome-screenshot`.

| Variable | Effect |
|---|---|
| `COMPUTER_USE_LINUX_SCREENSHOT_BACKEND` | Force `gnome-shell`, `portal` or `gnome-screenshot`. Pin `gnome-screenshot` for systemd/background contexts |
| `COMPUTER_USE_LINUX_COSMIC_HELPER` | Path to `computer-use-linux-cosmic` |
| `CU_DISABLE_ABS_POINTER` | Click through `ydotool` instead of the uinput absolute pointer |
| `COMPUTER_USE_LINUX_FORCE_PORTAL_POINTER` / `…_KEYBOARD` | Always use the RemoteDesktop portal |
| `COMPUTER_USE_LINUX_FORCE_YDOTOOL_POINTER` / `…_KEYBOARD` | Always use `ydotool` |

## Security model

- The binary opens no network listener, makes no outbound connections and sends no telemetry.
- Any process that can connect to the `ydotoold` socket can synthesize input. Keep the socket at mode `0600` under `/run/user/$UID`, and never run `ydotoold` as a system service.
- A granted screencast portal lets the host capture the screen for the rest of the session. Decline it and call `get_app_state` with `include_screenshot: false` if you don't want that.
- AT-SPI exposes window contents to every client on the session bus.
- The project supports only its latest release. Report vulnerabilities privately through GitHub.

The sibling project `agent-workspace-linux` works the other way round: it gives the agent its own hidden Xvfb desktop instead of driving yours.
