---
title: Claude in Slack and Claude Tag
type: how-to
tldr: "@Claude in Slack channels, two ways"
sources:
  - raw/docs/official/slack.md
  - raw/docs/official/claude-tag.md
  - raw/docs/official/platforms.md
  - raw/docs/official/commands.md
  - raw/docs/official/claude-code-on-the-web.md
  - raw/docs/official/cloud-environments.md
  - raw/docs/official/self-hosted-environments.md
  - raw/docs/official/feature-availability.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
  - raw/docs/changelog-2.1.275-to-2.1.278.md
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
related: ["[[claude-code-on-the-web]]", "[[ci-cd-and-code-review]]", "[[channels]]", "[[enterprise-admin]]", "[[slash-commands]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [claude-code-in-slack, claude-tag, slack-app-setup, at-claude-in-slack]
---

# Claude in Slack and Claude Tag

Two Slack integrations put `@Claude` in your channels. Both run the work as cloud sessions in Anthropic's cloud ([[claude-code-on-the-web]]); they differ in whose identity and credentials the session uses.

| | Claude Tag | Claude Code in Slack |
|---|---|---|
| Identity | Its own service accounts, provisioned by an admin | The mentioning user's own Claude account |
| Plans | Team and Enterprise, first-party service only | Pro, Max, Team or Enterprise with Claude Code access |
| Access | Set per channel by admins | Whatever that person connected |
| Billing | The organization's usage balance | The user's seat |

Both answer through the same app, and each scope chooses which generation replies: **New** (Claude Tag), **Legacy** (the per-user app, deprecated), **Off**, or **Inherit**. Claude Tag is in public beta, and is unavailable on Pro and Max and through third-party deployments.

## Set up Claude Tag

Prerequisites: a Team or Enterprise plan on Anthropic's first-party service; no Zero Data Retention or customer-managed encryption policy; Routines enabled at claude.ai/admin-settings/claude-code; the Owner role; a Slack workspace admin to install the app; and a funded usage balance on Team plans. If a service you connect filters by source IP, allowlist Anthropic's egress range `160.79.104.0/21` first — approvals can take days.

Setup runs at claude.ai/admin-settings/claude-tag in five saved steps:

1. **Pair the workspace.** A Slack admin installs the Claude app, runs `/invite @Claude`, then posts `@Claude connect` with no other text; Claude returns a pairing code that expires in 15 minutes for an Owner to redeem. A Grid admin gets both a `workspace_` and an `enterprise_` code — only the Grid-wide one covers DMs for users homed in other workspaces.
2. **Choose at least two tools.** Selecting them here doesn't connect them.
3. **Connect GitHub** through the Claude GitHub App, installed on a GitHub organization rather than a personal account, then grant repositories. Grants apply to every channel.
4. **Create an account per tool.** Treat Claude as a new hire: give it a mailbox, invite that address to each tool with the narrowest role, sign in as it, and paste its API key — a dedicated account keeps its actions separately auditable and revocable.
5. **Launch.** Set the monthly spend limit — $500, $1,000, $2,500, $5,000, Unlimited, or a custom amount up to $1,000,000 — and turn Claude Tag on. Before launch, every mention gets "Claude is disabled in this channel."

Verify with `@Claude what can you access from this channel?` and one small read-only request per tool; the action should appear in that tool's audit log under Claude's account.

## Scopes, bundles and per-channel configuration

An **Access bundle** is a named set of credentials, domain entries, repository grants, plugins and instructions. A **scope** is where one applies: **Default Slack access** (organization-wide), a workspace, or one channel. Bundles stack downward, so a channel resolves to the union of the default, its workspace and its own. Where two carry a credential for the same host the narrowest wins, with no fallback if it returns `401` or `403`; custom instructions concatenate instead, default first. A bundle on a public channel grants its access to anyone who can join, so keep elevated credentials in private-channel scopes.

Credentials never enter the sandbox. **Agent Proxy** holds them and injects one at the network boundary when a request matches that connection's allowed websites. A connection can start from a vendor preset on the **Credentials** tab; new Datadog connections are limited to Datadog's read and query API routes. Otherwise a host is reachable only through the bundle's **Domains** list or the scope's environment network level; anything else is blocked, and Claude names the blocked host in the thread. The proxy carries HTTP and HTTPS only, so SSH and native database protocols cannot cross it. Web search is exempt, running on Anthropic's servers rather than in the sandbox.

Each scope's **Advanced** section holds the default model, the cloud environment, auto mode allow rules, the guest setting and the Claude Tag version. Sessions run in auto mode, where a permission checker reviews every action; an allow rule is one plain sentence pre-approving an action there, up to 50 rules of 1,024 characters. An environment supplies a setup script, environment variables and a network access level, defaulting to Trusted access; credentials belong in connections, never in environment variables, since every session reads them. Sessions resolve an environment from channel, then workspace, then Default Slack access, then the organization default. Claude Tag sessions can run in self-hosted environments, though Access bundles don't apply there; a channel session carries no user account, so one runner locked to the agent serves sessions different people started — size fleets accordingly.

**Allow Claude to work in channels with guests** takes **Restrict** (default), **Channel only** or **Allow**, or inherits. Under **Channel only** — also how Slack Connect channels run — Claude has no bundles, repositories, memory, skills or wider instructions, and only the channel's own apply, so treat those as visible to everyone there. A bundle's **attach conditions** let an Owner extend it to channels with guests and to Slack Connect channels rather than member-only ones. In a channel with guests Claude won't search the workspace or read other channels, and guests can't approve a permission request. **Blocked** and **auto-join channel patterns** steer it by name, 50 patterns each with `*` and `?` wildcards; blocked wins.

On Enterprise, an Owner names **channel managers** per channel, who set its default model, repositories, and the credentials and plugins in its own bundle without holding Owner. Members keep memory and, unless **Channel member edits** is **Block**, channel instructions from the **Configure** link in any reply footer.

## Use Claude Tag in Slack

Claude works only in channels it was added to, so `/invite @Claude` is a user's whole setup. A mention guarantees a reply; Claude also answers untagged messages it judges warrant one, and follows every reply in a thread it joined. Each thread binds to its own persistent session in an ephemeral sandbox that anyone in the channel can steer by replying, and a channel carries one more session for its top level. Results come back as a reply, a file or chart, a page kept current, or a hosted page; code work lands as a draft pull request from the Claude GitHub App linked to the thread.

Exact bang words after the mention run fixed actions instead of a turn: `!help`, `!configure`, `!restart`, `!status`, `!mute` and `!unmute` must stand alone, while `!feedback`, `!routines` and `!fork` accept text. A 👎 reaction mutes that thread, and per channel **Respond automatically** switches unprompted replies off.

**Routines** are standing work anyone sets up in plain language — a schedule, a channel watch, or a subscription to one pull request. They run with the channel's connections rather than the creator's, schedule in UTC, and outlast their creator leaving. **Memory** belongs to the channel: public channels share workspace memory, private channels read it but write only their own store, and anyone can correct it. Models are chosen in words, per thread or as the channel default, from the list the organization allows; each reply's footer names the model used.

Claude follows instructions other people write in the conversation, so use it only where you trust the participants — the same prompt-injection exposure as any event-driven surface ([[channels]]).

## Set up Claude Code in Slack

Prerequisites: a plan with Claude Code access, cloud sessions enabled with at least one authenticated GitHub repository ([[claude-code-on-the-web]]), and your Slack account linked to your Claude account.

1. **Install the app.** A workspace administrator adds the Claude app from the Slack App Marketplace; from a session, `/install-slack-app` opens the OAuth flow ([[slash-commands]]).
2. **Connect your Claude account.** In Claude's **App Home** tab, click **Connect** and authenticate in the browser. Every user does this individually.
3. **Connect GitHub.** Sign in at claude.ai/code with the same account and authenticate at least one repository.
4. **Choose a routing mode** in App Home: **Code only** makes every mention a Claude Code session; **Code + Chat** routes coding tasks to Claude Code and the rest to Claude Chat, with **Retry as Code** to switch a thread.
5. **Invite Claude to channels.** Installation joins none. It answers mentions only in channels it has joined, public or private, never in DMs.

Mention `@Claude` with the task; a thread mention gathers that thread, a top-level one pulls recent channel messages. Claude creates a session on claude.ai/code, posts progress, and mentions you with a summary when it finishes. Messages carry action buttons:

| Button | Effect |
|---|---|
| **View Session** | Opens the full transcript on the web, where you can continue the work |
| **Create PR** | Opens a pull request from the session's changes |
| **Retry as Code** | Re-runs a chat reply as a Claude Code session |
| **Change Repo** | Picks a different repository when Claude chose wrongly |

## Access, limits and billing

- **Claude Code in Slack, per user**: sessions run under the individual's account, count against their plan limits, reach only repositories they connected, and appear in their history at claude.ai/code. On Team and Enterprise they carry Team visibility.
- **Claude Tag, per channel**: everyone in a channel gets the same access, and actions appear under the agent's service accounts in each tool's audit log. Channel work bills to the organization's usage balance under the spend limit plus any per-channel limit; reading a channel and deciding whether to reply isn't billed. A DM runs on the sender's own account and connectors, billed to their seat. Owner toggles restrict who can invoke Claude — by role on Enterprise, to organization members on Team — and disable DMs.
- **Workspace level**: Slack admins decide whether the app is installed; removing it revokes access and deletes that workspace's Claude data. In Enterprise Grid, organization admins control which workspaces get it. A workspace pairs with one Claude organization at a time.
- **GitHub only** for repositories, and **one pull request per session** for Claude Code in Slack. Without cloud sessions enabled, it answers with ordinary chat replies instead of starting a session.

Claude Tag replaces local Claude Code configuration with admin settings: a session starts from a fresh sandbox, loads `CLAUDE.md` and `.claude/skills/` only after cloning a granted repository, ignores `.mcp.json` and repository hooks, and never reads your machine.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Claude Code is not enabled for your account" | The account has no cloud environment. Sign in at claude.ai/code and finish web onboarding; the error clears on the next mention |
| "Claude is disabled in this channel" | Claude Tag was never launched, the scope's version is **Off**, or a blocked channel pattern matches |
| Sessions don't start | Confirm the account is connected in App Home, cloud sessions are enabled, and a GitHub repository is connected |
| A Claude Tag channel's sessions fail immediately | The channel points at a personal cloud environment. Its Owner shares it with the organization from the environment selector, or recreates it on the **Cloud environments** page, then sets it as the default or on the scope ([[enterprise-admin]]) |
| Claude can't reach a host or pasted link | Add the host to the bundle's **Domains** tab, or pin an environment with a broader network level, then retry in a fresh thread |
| A new connection doesn't work in a running thread | Threads keep the skills, plugins and instructions they started with; start a new top-level thread |
| Repository missing, or the wrong one chosen | Connect it at claude.ai/code and check GitHub permissions; use **Change Repo**, or name the repository in the request |

Use Slack when the context already lives there, when work should start asynchronously, or when teammates need visibility; use claude.ai/code for file uploads, real-time interaction and longer tasks. For review automation on the pull request, see [[ci-cd-and-code-review]].
