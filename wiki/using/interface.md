---
title: Interface
type: reference
tldr: "Shortcuts, styles, status line, voice, a11y"
sources:
  - raw/docs/official/interactive-mode.md
  - raw/docs/official/keybindings.md
  - raw/docs/official/terminal-config.md
  - raw/docs/official/output-styles.md
  - raw/docs/official/statusline.md
  - raw/docs/official/voice-dictation.md
  - raw/docs/official/fullscreen.md
  - raw/docs/official/accessibility.md
  - raw/docs/official/commands.md
  - raw/docs/official/common-workflows.md
  - raw/docs/official/whats-new__2026-w14.md
related: ["[[slash-commands]]", "[[settings]]", "[[ide-integrations]]", "[[costs-and-usage]]", "[[claude-md-and-memory]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [keyboard-shortcuts, keybindings-json, output-style, status-line, screen-reader-mode]
---

# Interface

This page covers how to shape the terminal UI of the Claude Code CLI: default shortcuts, custom keybindings, terminal fixes, themes, output styles, the status line, voice dictation, fullscreen rendering, and accessibility. Every command mentioned here is also listed in [[slash-commands]]. Most options are settings keys, and their scopes are covered in [[settings]].

## Feature lessons

`/powerup` opens quick interactive lessons that teach Claude Code features through animated demos, played in the terminal. Run it with no argument:

```text
/powerup
```

Claude Code ships features often, and ones that would have changed how you work can slip by; one pass through the lessons shows what is there. Asking Claude about its own features instead gets you documentation-based answers — `/powerup` is the hands-on version.

## Everyday shortcuts

| Keys | Action |
|:--|:--|
| `Esc` | Interrupt Claude or close a dialog |
| `Esc` `Esc` | Clear the draft, or open rewind on an empty prompt |
| `Shift+Tab` | Cycle permission modes |
| `Ctrl+C` / `Ctrl+D` | Interrupt or clear input / exit |
| `Ctrl+G` | Open the prompt in your text editor |
| `Ctrl+O` | Toggle the transcript viewer (full tool output, thinking) |
| `Ctrl+R` | Reverse-search prompt history |
| `Ctrl+B` | Send running Bash commands and agents to the background |
| `Ctrl+T` | Toggle Claude's task checklist |
| `Ctrl+V` (`Alt+V` on Windows) | Paste an image from the clipboard |
| `Ctrl+S` | Stash or restore the current prompt |
| `Option+P` / `Alt+P` | Switch model |
| `Option+T` / `Alt+T` | Toggle extended thinking |
| `Option+O` / `Alt+O` | Toggle fast mode |
| `Ctrl+J`, or `\` then `Enter` | Newline without submitting |

Readline editing works too: `Ctrl+A`/`Ctrl+E` for start and end of line, `Ctrl+W`/`Ctrl+U`/`Ctrl+K` for deleting, `Ctrl+Y` to paste back, and `Alt+B`/`Alt+F` to move by word. On macOS, Option shortcuts need the terminal's "Use Option as Meta Key" setting; in iTerm2, set the Option keys to "Esc+". `/focus` shows only your last prompt, a one-line tool summary, and the final response. `/color` tints the prompt bar for the session.

## Custom keybindings

Run `/keybindings` to create or open `~/.claude/keybindings.json`. Changes apply without a restart.

```json
{
  "$schema": "https://www.schemastore.org/claude-code-keybindings.json",
  "bindings": [
    { "context": "Chat", "bindings": { "ctrl+e": "chat:externalEditor", "ctrl+u": null } }
  ]
}
```

- **Contexts** scope where a binding applies: `Global`, `Chat`, `Autocomplete`, `Confirmation`, `Transcript`, `HistorySearch`, `Task`, `ModelPicker`, `EffortSlider`, `DiffPanel`, `Scroll`, and others.
- **Actions** use `namespace:action`, such as `chat:submit`, `chat:newline`, `voice:pushToTalk`, or `modelPicker:thisSessionOnly`.
- **Keystrokes:**
  - Modifiers join with `+`: `ctrl`, `shift`, `alt`/`opt`/`meta`, and `cmd`. `cmd` only works in terminals that report Super.
  - Chords are space-separated, such as `ctrl+k ctrl+s`, and each key must follow within 3 seconds.
  - Key names are case-insensitive, so write `shift+k` for Shift and a letter.
- **Unbinding:** `null` removes a default. To reuse a chord prefix such as `ctrl+x` as a single key, unbind every chord on it.
- **Reserved:** `Ctrl+C`, `Ctrl+D`, `Ctrl+M`, `Ctrl+[`, `Ctrl+I`, `Ctrl+H`, and Caps Lock can't be rebound. `Ctrl+B` (tmux prefix), `Ctrl+A` (screen), and `Ctrl+Z` (suspend) may conflict with your terminal.
- **Errors:** invalid entries produce warnings; start with `claude --debug` to see details.

**Vim mode** is set in `/config` → Editor mode, or with `"editorMode": "vim"`. Vim keys can't be remapped in the keybindings file, but `vimInsertModeRemaps` maps sequences such as `jj` to Escape. In INSERT mode, `Enter` still submits.

## Terminal fixes

| Problem | Fix |
|:--|:--|
| Shift+Enter submits | Works natively in Ghostty, Kitty, iTerm2, WezTerm, Warp, Apple Terminal, and Windows Terminal. In VS Code, Cursor, Devin Desktop, older Alacritty, and Zed, run `/terminal-setup` once. In gnome-terminal and JetBrains terminals, use `Ctrl+J` |
| No alert when Claude finishes | Desktop notifications fire by default in Ghostty, Kitty, and iTerm2. Elsewhere set `"preferredNotifChannel": "terminal_bell"` or add a Notification hook |
| Shift+Enter or notifications break in tmux | Add `set -g allow-passthrough on`, `set -s extended-keys on`, `set -as terminal-features 'xterm*:extkeys'` to `~/.tmux.conf` |
| Backspace deletes a word on Windows | `CLAUDE_CODE_BS_AS_CTRL_BACKSPACE=0` |
| Flicker or jumping scrollback | Fullscreen rendering (below), or `CLAUDE_CODE_FORCE_SYNC_OUTPUT=1` if only the flicker bothers you |

Pastes over 800 characters or three lines collapse to a `[Pasted text #1 +120 lines]` placeholder but are sent in full. For very large inputs, write a file and ask Claude to read it.

**Themes.** `/theme` offers auto (follows the terminal background), light and dark, colorblind-friendly `dark-daltonized` and `light-daltonized`, ANSI themes, and custom themes. Choose **New custom theme…** to create one; it is saved as `~/.claude/themes/<slug>.json` and selected as `custom:<slug>`.

## Output styles

An output style replaces how Claude responds (role, tone, format) on every turn. It changes behavior, not project knowledge, which belongs in CLAUDE.md ([[claude-md-and-memory]]).

| Style | Behavior |
|:--|:--|
| Default | Standard software-engineering instructions |
| Proactive | Acts immediately and makes reasonable assumptions; your permission mode still gates actions |
| Concise | Leads with the result and skips narration |
| Explanatory | Adds educational "Insights" while working |
| Learning | Adds Insights and leaves `TODO(human)` pieces for you to write |

Pick one in `/config` → **Output style** (saved to `.claude/settings.local.json`) or set `"outputStyle": "Explanatory"`. A change takes effect on your next message.

A custom style is a Markdown file in `~/.claude/output-styles`, `.claude/output-styles`, or a plugin's `output-styles/` directory:

```markdown
---
name: Diagrams first
description: Lead every explanation with a diagram
keep-coding-instructions: true
---
When explaining code or data flow, start with a Mermaid diagram, then explain in prose.
```

- **`keep-coding-instructions`** defaults to `false`, which drops Claude Code's engineering guidance (scoping, comments, verification). Set it to `true` when Claude is still writing code.
- **Plugin styles** can set `force-for-plugin` to apply automatically.
- **Scope:** styles apply to the main conversation and forks, not to other subagents.
- **Reloading:** style files are read at startup, so restart after editing one.

## Status line

The status line is a row above the footer, filled by any shell command. Claude Code pipes session JSON to the command on stdin and displays what it prints. Run `/statusline show model name and context percentage with a progress bar` to generate one, or configure it by hand:

```json
{ "statusLine": { "type": "command", "command": "~/.claude/statusline.sh", "padding": 2 } }
```

```bash
#!/bin/bash
input=$(cat)
MODEL=$(echo "$input" | jq -r '.model.display_name')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
echo "[$MODEL] ${PCT}% context"
```

- **Useful fields:**
  - Model and workspace: `model.display_name`, `workspace.current_dir`, `workspace.repo.name`
  - Context and cost: `context_window.used_percentage`, `cost.total_cost_usd`
  - Limits: `rate_limits.five_hour.used_percentage`, `rate_limits.seven_day.used_percentage`
  - Session state: `effort.level`, `fast_mode`, `session_name`, `vim.mode`, `worktree.name`, `pr.number`, `transcript_path`
- **Updates:** the command runs at session start, after each assistant message, after `/compact`, and on permission-mode or vim changes. Runs are debounced by 300 ms. `refreshInterval` adds a timer, which helps for clocks or idle sessions.
- **Output:** multi-line output, ANSI colors, and OSC 8 links work. Read `COLUMNS` and `LINES` for width, since `tput cols` can't see the terminal.
- **Cost:** it runs locally and uses no tokens. A custom status line hides most footer hints. Remove it with `/statusline delete`.

Cost-related fields are explained in [[costs-and-usage]].

## Voice dictation

`/voice` turns on speech-to-text for the prompt. Audio streams to Anthropic for transcription.

- **Requirements:** a Claude.ai account (not API keys, Bedrock, Agent Platform, or Foundry) and a local microphone (not SSH or web sessions). Transcription doesn't count toward `/usage` limits.
- **Modes:**
  - `/voice hold` (default): hold `Space` to talk and release to stop.
  - `/voice tap`: tap `Space` to start, tap again to send; transcripts of three words or more auto-submit.
  - `/voice off` disables it.
- **Settings:** `"voice": { "enabled": true, "mode": "tap", "autoSubmit": true }`. The `language` setting picks the dictation language, falling back to English.
- **Rebinding:** bind `voice:pushToTalk` to a modifier combo such as `meta+k` to skip the hold warmup.

The VS Code extension supports dictation too ([[ide-integrations]]).

## Fullscreen rendering

Fullscreen is a flicker-free renderer on the terminal's alternate screen, with mouse support and flat memory in long conversations. It is in research preview. Switch with `/tui fullscreen` (the conversation relaunches intact and the choice is saved) and back with `/tui default`, or launch with `CLAUDE_CODE_NO_FLICKER=1 claude`.

- **Search:** use `Ctrl+O` for the transcript, then `/` to search or `[` to write it to scrollback.
- **Selection:** in-app selection copies on mouse release. Hold `Shift` (`Option` in iTerm2, `Fn` in Terminal.app) for native selection.
- **Mouse:** `CLAUDE_CODE_DISABLE_MOUSE=1` turns off mouse capture entirely. `CLAUDE_CODE_DISABLE_MOUSE_CLICKS=1` keeps wheel scrolling but ignores clicks.

## Accessibility

Screen reader mode replaces boxes, animations, and redraws with labeled linear text.

- **Turning it on:** `claude --ax-screen-reader` for one session, `CLAUDE_AX_SCREEN_READER=1` for a shell, or `"axScreenReader": true` for every session. The flag beats the variable, which beats the setting.
- **What changes:**
  - Messages start with `you:`, `claude:`, `tool:`, `error:`, or `Permission Required:`.
  - Menus become numbered lists.
  - The bell rings when Claude finishes or needs an answer.
  - Turns carry OSC 133 markers, so jump-to-prompt keys work.
- **Other options:** `CLAUDE_CODE_ACCESSIBILITY=1` keeps a visible cursor for magnifiers, `prefersReducedMotion: true` calms animations, and `/theme` offers the daltonized themes.
