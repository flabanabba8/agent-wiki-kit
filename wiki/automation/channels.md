---
title: Channels
type: how-to
tldr: "Push chat and webhook events into a session"
sources:
  - raw/docs/official/channels.md
  - raw/docs/official/channels-reference.md
related: ["[[mcp]]", "[[plugins]]", "[[enterprise-admin]]", "[[permissions-and-modes]]", "[[routines-and-scheduling]]", "[[claude-code-on-the-web]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [claude-channels, telegram-channel, discord-channel, webhook-channel, permission-relay]
valid_until: 2027-03-15
---

# Channels

A **channel** is an [[mcp]] server that pushes events into a Claude Code session that is already running, so Claude can react to a chat message, CI failure or alert while you are away. A two-way channel also exposes a reply tool, which makes it a chat bridge. Events arrive only while the session is open, so for always-on use, run Claude in a persistent terminal or background process.

Channels are a **research preview**. They need Anthropic authentication (claude.ai or a Console API key) and are not available on Bedrock, Google Cloud's Agent Platform or Microsoft Foundry. Team and Enterprise organizations must enable them explicitly.

## How channels compare

| Feature | What it does |
|---|---|
| Channels | Push events from outside sources into your running **local** session |
| Standard MCP server | Claude queries it on demand. Nothing is pushed |
| [[claude-code-on-the-web]] | Runs a fresh cloud sandbox for async work |
| Remote Control | You drive your local session from claude.ai or mobile |
| [[routines-and-scheduling]] / `/loop` | Run on a timer instead of on events |

When Claude replies through a channel, your terminal shows the inbound message and a tool confirmation such as "sent". The reply text itself appears only on the other platform.

## Use a supported channel

The included channels are Telegram, Discord, iMessage and the **fakechat** demo. Each is a plugin that needs [Bun](https://bun.sh).

### Fakechat quickstart

```text
/plugin install fakechat@claude-plugins-official
```
```bash
claude --channels plugin:fakechat@claude-plugins-official
```

Open http://localhost:8787 and type a message. In the terminal it shows as `← fakechat · web: …`, and Claude receives it as a `<channel source="plugin:fakechat:fakechat">` event and answers through fakechat's `reply` tool. You can pass several plugins to `--channels`, separated by spaces.

If the marketplace is missing, run `/plugin marketplace add anthropics/claude-plugins-official`. Choose user scope when installing, and ignore a `Run /reload-plugins to activate.` note when you are about to restart with `--channels` anyway (see [[plugins]]).

### Telegram and Discord

1. Create a bot. For Telegram, send `/newbot` to BotFather. For Discord, create an application in the Developer Portal, enable **Message Content Intent**, and invite the bot with View Channels, Send Messages, Send Messages in Threads, Read Message History, Attach Files and Add Reactions.
2. `/plugin install telegram@claude-plugins-official` (or `discord@…`).
3. `/telegram:configure <token>` saves the token to `~/.claude/channels/telegram/.env`. You can set `TELEGRAM_BOT_TOKEN` or `DISCORD_BOT_TOKEN` instead.
4. Restart with `claude --channels plugin:telegram@claude-plugins-official`.
5. Message the bot to get a pairing code, then run `/telegram:access pair <code>` and lock the bot down with `/telegram:access policy allowlist`.

### iMessage

This one is macOS only and needs no bot token. It reads `~/Library/Messages/chat.db`, so grant your terminal **Full Disk Access**, or the server exits with `authorization denied`. Install `imessage@claude-plugins-official` and start with `--channels`. Texting yourself goes straight through. Allow other senders with `/imessage:access allow +15551234567` or an Apple ID email.

## Security model

- Each approved channel plugin keeps a **sender allowlist**, and messages from anyone else are silently dropped. Telegram and Discord build the list by pairing.
- A server must be named in `--channels` for the session. Being listed in `.mcp.json` is not enough.
- If the channel supports permission relay, anyone on its allowlist can approve or deny tool use in your session. Allowlist only people you trust with that.
- If Claude hits a permission prompt while you are away, the session pauses unless a relay answers it. `--dangerously-skip-permissions` avoids most prompts, but use it only in trusted environments (see [[permissions-and-modes]]).
- In `-p` mode, tools that need terminal input (multiple-choice questions, plan approval) are disabled so the session never stalls.

## Enterprise controls

Two managed settings control channels, and users can't override them (see [[enterprise-admin]]):

| Setting | Purpose | When unset |
|---|---|---|
| `channelsEnabled` | Master switch. It must be `true` for any channel to deliver, and turning it off also blocks the development flag | claude.ai Team/Enterprise: blocked. Console: allowed unless the organization deploys managed settings |
| `allowedChannelPlugins` | Replaces the Anthropic-maintained plugin allowlist | The Anthropic default list (the channel plugins in `claude-plugins-official`) |

```json
{
  "channelsEnabled": true,
  "allowedChannelPlugins": [
    { "marketplace": "claude-plugins-official", "plugin": "telegram" },
    { "marketplace": "acme-corp-plugins", "plugin": "internal-alerts" }
  ]
}
```

Owners can also enable channels at claude.ai → Admin settings → Claude Code → Channels. Pro and Max users outside an organization skip these checks. If a plugin is not on the allowlist, Claude Code starts normally but the channel doesn't register, and the startup notice says why.

`--channels` and `--dangerously-load-development-channels` work but don't appear in `claude --help` during the preview.

## Build a channel

**Requirements:** `@modelcontextprotocol/sdk`, a Node-compatible runtime (Bun, Node or Deno), and stdio transport. Claude Code spawns the server as a subprocess. Chat bridges poll their platform's API, and webhook receivers listen on a local HTTP port.

### Server contract

| Field | Meaning |
|---|---|
| `capabilities.experimental['claude/channel']` | Required, always `{}`. It registers the notification listener |
| `capabilities.experimental['claude/channel/permission']` | Optional `{}` that opts in to permission relay. Omit it or set `false` to opt out |
| `capabilities.tools` | `{}` for two-way channels. Omit it for one-way |
| `instructions` | Recommended. Delivered to Claude on connect: which events to expect, whether to reply, and which attribute (such as `chat_id`) to pass back |

Push an event:

```ts
await mcp.notification({
  method: 'notifications/claude/channel',
  params: {
    content: 'build failed on main: https://ci.example.com/run/1234',
    meta: { severity: 'high', run_id: '1234' },
  },
})
```

Claude sees `<channel source="your-channel" severity="high" run_id="1234">…</channel>`. `meta` keys may use only letters, digits and underscores, and other keys are silently dropped. Notifications get no acknowledgement. If the session hasn't loaded the server as a channel or policy blocks it, events are dropped with no error. Events queue, and several events that arrive during one turn are delivered together.

A **reply tool** is an ordinary MCP tool (for example `reply` with `chat_id` and `text`) plus an `instructions` string telling Claude to use it.

### Gate inbound messages

An ungated channel is a prompt-injection vector. Check the **sender** (`message.from.id`), not the room (`message.chat.id`), against an allowlist before emitting anything. Otherwise anyone in an allowlisted group chat could inject messages.

### Test locally

Register the server in `.mcp.json` (for example `"webhook": { "command": "bun", "args": ["./webhook.ts"] }`), then run:

```bash
claude --dangerously-load-development-channels server:webhook
claude --dangerously-load-development-channels plugin:yourplugin@yourmarketplace
curl -X POST localhost:8788 -d "build failed on main"
```

The flag bypasses the allowlist only for the entries you name, after a confirmation dialog. `channelsEnabled` still applies. If nothing arrives, check `/mcp` for a `failed` status, restart with `claude --debug …`, and read `~/.claude/debug/<session-id>.txt`.

## Permission relay

When a tool approval dialog opens (for `Bash`, `Write`, `Edit` and so on), a channel that declares the permission capability receives the same prompt in parallel. Whichever answer arrives first, terminal or remote, wins. Project trust and MCP consent dialogs are never relayed. Relay goes only to servers opted in with `--channels` or the development flag.

**Request** `notifications/claude/channel/permission_request`, with these `params`:

| Field | Content |
|---|---|
| `request_id` | Five lowercase letters from `a`-`z` without `l`. It isn't shown in the terminal, so include it in your outgoing prompt |
| `tool_name` | For example `Bash` |
| `description` | Claude's summary of the call. It can be just `Run shell command`, so treat it as untrusted |
| `input_preview` | The tool's arguments as JSON-shaped text. Long values are elided in the middle, and recognizable credentials are replaced with `[REDACTED]` |

**Verdict** `notifications/claude/channel/permission`, with `{ request_id, behavior: 'allow' | 'deny' }`. A verdict applies to that one call only. A verdict with an unknown ID is dropped silently. In your inbound handler, gate on the sender first, then match replies such as `/^\s*(y|yes|n|no)\s+([a-km-z]{5})\s*$/i`, lowercase the ID, and emit the verdict instead of forwarding the text as chat. Declare the capability only if the channel authenticates senders.

## Package and distribute

Wrap the server in a plugin and publish it to a marketplace. Users install it with `/plugin install` and enable it with `--channels plugin:<name>@<marketplace>`. A channel outside the Anthropic allowlist still needs the development flag, unless an admin adds it to `allowedChannelPlugins`. Submitting to the community marketplace does not add a plugin to the channel allowlist.
