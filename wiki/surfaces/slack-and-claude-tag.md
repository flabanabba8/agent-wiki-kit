---
title: Claude in Slack and Claude Tag
type: how-to
tldr: "@Claude in Slack channels, two ways"
sources:
  - raw/docs/official/slack.md
  - raw/docs/official/platforms.md
  - raw/docs/official/commands.md
  - raw/docs/official/claude-code-on-the-web.md
  - raw/docs/official/cloud-environments.md
  - raw/docs/official/self-hosted-environments.md
  - raw/docs/official/feature-availability.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
  - raw/docs/changelog-2.1.275-to-2.1.282.md
  - raw/docs/claude-tag/overview.md
  - raw/docs/claude-tag/admins__setup-overview.md
  - raw/docs/claude-tag/admins__for-slack-admins.md
  - raw/docs/claude-tag/admins__add-connections.md
  - raw/docs/claude-tag/admins__attach-to-scope.md
  - raw/docs/claude-tag/admins__restrict-access.md
  - raw/docs/claude-tag/admins__customize.md
  - raw/docs/claude-tag/admins__set-spend-limit.md
  - raw/docs/claude-tag/admins__workspaces.md
  - raw/docs/claude-tag/admins__network-requirements.md
  - raw/docs/claude-tag/concepts__how-it-works.md
  - raw/docs/claude-tag/concepts__agent-identity.md
  - raw/docs/claude-tag/concepts__glossary.md
  - raw/docs/claude-tag/concepts__for-claude-code-users.md
  - raw/docs/claude-tag/users__getting-started.md
  - raw/docs/claude-tag/users__commands.md
  - raw/docs/claude-tag/users__when-claude-responds.md
  - raw/docs/claude-tag/users__memory.md
  - raw/docs/claude-tag/users__models.md
  - raw/docs/claude-tag/users__proactivity.md
  - raw/docs/changelog-2.1.283-to-2.1.296.md
related: ["[[claude-code-on-the-web]]", "[[claude-projects]]", "[[ci-cd-and-code-review]]", "[[channels]]", "[[enterprise-admin]]", "[[slash-commands]]"]
created: 2026-09-15
updated: 2026-10-11
confidence: high
last_verified: 2026-09-25
aliases: [claude-code-in-slack, claude-tag, slack-app-setup, at-claude-in-slack]
---

# Claude in Slack and Claude Tag

Two Slack integrations put `@Claude` in your channels. Both run the work as cloud sessions ([[claude-code-on-the-web]]); they differ in whose identity and credentials the session uses.

| | Claude Tag | Claude Code in Slack |
|---|---|---|
| Identity | Its own service accounts, provisioned by an admin | The mentioning user's own Claude account |
| Plans | Team and Enterprise, first-party service only | Pro, Max, Team or Enterprise with Claude Code access |
| Access | Set per channel by admins | Whatever that person connected |
| Billing | The organization's usage balance | The user's seat |

Both answer through the same app, and each scope chooses which generation replies: **New** (Claude Tag), **Legacy** (the per-user app, deprecated), **Off**, or **Inherit**. Claude Tag is in public beta, and is unavailable on Pro and Max and through third-party deployments.

## Set up Claude Tag

Prerequisites: a Team or Enterprise plan on Anthropic's first-party service; no Zero Data Retention or customer-managed encryption policy; Routines enabled (Admin settings → Capabilities → Remote sessions); the Owner role; a Slack workspace admin to install the app; and a funded usage balance on Team plans. If a service you connect filters by source IP, allowlist Anthropic's egress range `160.79.104.0/21` first — approvals can take days.

Setup runs at claude.ai/admin-settings/claude-tag in five saved steps:

1. **Pair the workspace.** A Slack admin installs the Claude app, runs `/invite @Claude`, then posts `@Claude connect` with no other text; Claude returns a pairing code that expires in 15 minutes for an Owner to redeem. A Grid admin gets both a `workspace_` and an `enterprise_` code — only the Grid-wide one covers DMs for users homed in other workspaces.
2. **Choose at least two tools.** Selecting them here doesn't connect them.
3. **Connect GitHub** through the Claude GitHub App, installed on a GitHub organization rather than a personal account, then grant repositories. Grants apply to every channel.
4. **Create an account per tool.** Give Claude its own mailbox, invite it to each tool with the narrowest role, and paste its API key, so its actions stay auditable and revocable.
5. **Launch.** Set the monthly spend limit — $500, $1,000, $2,500, $5,000, Unlimited, or a custom amount up to $1,000,000 — and turn Claude Tag on. Before launch, every mention gets "Claude is disabled in this channel."

Verify with `@Claude what can you access from this channel?` and one read-only request per tool.

## Scopes, bundles and per-channel configuration

An **Access bundle** is a named set of credentials, domain entries, repository grants, plugins and instructions. A **scope** is where one applies: **Default Slack access** (organization-wide), a workspace, or one channel. Bundles stack downward, so a channel resolves to the union of the default, its workspace and its own. Where two carry a credential for the same host the narrowest wins, with no fallback if it returns `401` or `403`; custom instructions concatenate instead, default first. A bundle on a public channel grants its access to anyone who can join, so keep elevated credentials in private-channel scopes. A bundle applies only in member-only channels unless an Owner's attach conditions extend it to channels with guests or Slack Connect channels.

Credentials never enter the sandbox: **Agent Proxy** injects one at the network boundary when a request matches that connection's allowed websites. Other hosts are reachable only through the bundle's **Domains** list or the environment's network level; Claude names a blocked host in the thread. The proxy carries HTTP and HTTPS only, so SSH and native database protocols cannot cross it. Web search is exempt, running on Anthropic's servers rather than in the sandbox.

Each scope's **Advanced** section holds the default model, the cloud environment, auto mode allow rules, the guest setting and the Claude Tag version. Sessions run in auto mode, where a permission checker reviews every action; an allow rule is one plain sentence pre-approving an action there, up to 50 rules of 1,024 characters. Credentials belong in connections, never in environment variables, since every session reads them. Sessions resolve an environment from channel, then workspace, then Default Slack access, then the organization default. Claude Tag sessions can run in self-hosted environments, where Access bundles don't apply and one runner serves sessions different people started.

**Allow Claude to work in channels with guests** takes **Restrict** (default), **Channel only** or **Allow**, or inherits. Under **Channel only** — also how Slack Connect channels run — Claude has no bundles, repositories, memory, skills or wider instructions, and only the channel's own apply, so treat those as visible to everyone there. A bundle's **attach conditions** let an Owner extend it to channels with guests and to Slack Connect channels rather than member-only ones. In a channel with guests Claude won't search the workspace or read other channels, and guests can't approve a permission request. **Blocked** and **auto-join channel patterns** steer it by name, 50 patterns each with `*` and `?` wildcards; blocked wins.

On Enterprise, an Owner names **channel managers** per channel, who set its default model, repositories, and the credentials and plugins in its own bundle without holding Owner. Members keep memory and, unless **Channel member edits** is **Block**, channel instructions from the **Configure** link in any reply footer.

## Use Claude Tag in Slack

Claude works only in channels it was added to, so `/invite @Claude` is a user's whole setup. A mention guarantees a reply; Claude also answers untagged messages it judges warrant one, and follows every reply in a thread it joined. Each thread binds to its own persistent session in an ephemeral sandbox that anyone in the channel can steer by replying, and a channel carries one more session for its top level. Threads show Slack's native Working indicator and Stop button. Results come back as a reply, a file or chart, a page kept current, or a hosted page; code work lands as a draft pull request from the Claude GitHub App linked to the thread.

Exact bang words after the mention run fixed actions instead of a turn: `!help`, `!configure`, `!restart`, `!status`, `!mute` and `!unmute` must stand alone, while `!fast` (with `!fast off` to switch back; it moves the thread to Opus if needed), `!feedback`, `!routines` and `!fork` accept text. A 👎 reaction mutes that thread, and per channel **Respond automatically** switches unprompted replies off.

**Routines** are standing work anyone sets up in plain language — a schedule, a channel watch, or a subscription to one pull request. They run with the channel's connections rather than the creator's, schedule in UTC, and outlast their creator leaving; asked in a thread, Claude lists that thread's own scheduled tasks. **Memory** belongs to the channel: public channels share workspace memory, private channels read it but write only their own store, and anyone can correct it. Models are chosen in words, per thread or as the channel default, from the list the organization allows; each reply's footer names the model used, and a newly connected workspace follows the current default model.

Claude follows instructions others write in the conversation, so use it only where you trust the participants ([[channels]]). For a personal stream of work that Claude coordinates across parallel cloud sessions, see [[claude-projects]].

## Set up Claude Code in Slack

Prerequisites: a plan with Claude Code access, cloud sessions ([[claude-code-on-the-web]]) enabled for your account with GitHub connected at claude.ai/code and at least one repository authenticated, and your Slack account linked to your Claude account.

1. **Install the app.** A workspace administrator adds the Claude app from the Slack App Marketplace; from a session, `/install-slack-app` opens the OAuth flow ([[slash-commands]]).
2. **Connect your Claude account.** In Claude's **App Home** tab, click **Connect** and authenticate in the browser. Every user does this individually.
3. **Configure cloud sessions.** Sign in at claude.ai/code with the same account, connect GitHub, and authenticate at least one repository.
4. **Choose a routing mode** in App Home: **Code only** makes every mention a cloud session; **Code + Chat** routes coding tasks to a cloud session and the rest to Claude Chat, with **Retry as Code** to switch a thread.
5. **Invite Claude to channels.** Installation joins none. It answers mentions only in channels it has joined, public or private, never in DMs.

Mention `@Claude` with the task; a thread mention gathers that thread, a top-level one recent channel messages. Claude creates a session on claude.ai/code and mentions you with a summary when done. Messages carry action buttons:

| Button | Effect |
|---|---|
| **View Session** | Opens the full transcript at claude.ai/code, where you can continue the work |
| **Create PR** | Opens a pull request from the session's changes |
| **Retry as Code** | Re-runs a chat reply as a Claude Code session |
| **Change Repo** | Picks a different repository when Claude chose wrongly |

## Access, limits and billing

- **Claude Code in Slack, per user**: sessions run under the individual's account, count against their plan limits, reach only repositories they connected, and appear in their history at claude.ai/code. On Team and Enterprise they carry Team visibility.
- **Claude Tag, per channel**: everyone in a channel gets the same access, and actions appear under the agent's service accounts in each tool's audit log. Channel work bills to the organization's usage balance under the spend limit plus any per-channel limit; reading a channel and deciding whether to reply isn't billed. A DM runs on the sender's own account and connectors, billed to their seat. Owner toggles restrict who can invoke Claude — by role on Enterprise, to organization members on Team — and disable DMs.
- **Workspace level**: removing the app revokes access and deletes that workspace's Claude data; in Enterprise Grid, organization admins choose workspaces. A workspace pairs with one Claude organization at a time.
- **GitHub only** for repositories, and **one pull request per session** for Claude Code in Slack. Without cloud sessions enabled, it answers with ordinary chat replies instead of starting a session.

Claude Tag replaces local Claude Code configuration with admin settings: a session starts from a fresh sandbox, loads `CLAUDE.md` and `.claude/skills/` only after cloning a granted repository, ignores `.mcp.json` and repository hooks, and never reads your machine.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Claude Code is not enabled for your account" | The account has no cloud environment. Sign in at claude.ai/code and finish web onboarding; the error clears on the next mention |
| "Claude is disabled in this channel" | Claude Tag was never launched, the scope's version is **Off**, or a blocked channel pattern matches |
| A Claude Tag channel's sessions fail immediately | The channel points at a personal cloud environment. An Owner shares their own environment from the environment selector, or recreates it as organization-shared on the **Cloud environments** admin page, then sets it as the default or on the scope ([[enterprise-admin]]) |
| Claude can't reach a host | Add it to the bundle's **Domains** tab or use a broader network level, then retry in a fresh thread |
| A new connection doesn't work in a running thread | Threads keep the skills, plugins and instructions they started with; start a new top-level thread |
| Repository missing, or the wrong one chosen | Connect it at claude.ai/code and check GitHub permissions; use **Change Repo**, or name the repository in the request |

For review automation on the pull request, see [[ci-cd-and-code-review]].
