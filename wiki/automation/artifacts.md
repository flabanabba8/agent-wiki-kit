---
title: Artifacts in Claude Code
type: how-to
tldr: "Publish live, shareable pages from a session"
sources:
  - raw/docs/official/artifacts.md
  - raw/docs/official/commands.md
  - raw/docs/official/whats-new__2026-w34.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
related: ["[[mcp]]", "[[permissions-and-modes]]", "[[enterprise-admin]]", "[[data-and-privacy]]", "[[settings]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [claude-artifacts, publish-artifact, share-session-output, artifact-connectors, design-canvas]
valid_until: 2027-03-15
---

# Artifacts in Claude Code

An **artifact** is a live, interactive web page that Claude Code publishes from your session to a private URL on claude.ai. It updates in place as the session goes on, and you can share it from the page header.

Use one when terminal text is the wrong medium: an annotated PR walkthrough, a dashboard built from data the session pulled, design options side by side, an investigation timeline, a checklist that tracks a migration, or a status board fed by connectors. An artifact is **one self-contained page with no backend**. For a real internal tool, deploy on your own infrastructure.

## Create and update

Ask in plain language, or let Claude publish on its own when the output suits a page:

```text
Make an artifact that walks through this PR with the diff annotated inline.
Build a dashboard artifact of last week's deploy failures by service and keep it updated as you investigate.
```

Claude writes an HTML or Markdown file (in a temporary directory unless you name a location) and publishes it. The first publish goes through your permission mode (see [[permissions-and-modes]]):
- **Auto mode:** the classifier reviews it and there is no prompt.
- **Manual / Accept edits:** Claude Code asks you to approve the upload to claude.ai.

Republishing an approved artifact doesn't ask again, except when Claude declares a new runtime capability (connectors or downloads), when the artifact is shared publicly, or when it is shared with people and set to always show the latest version.

After publishing:
- Your browser opens to the page. Set `CLAUDE_CODE_ARTIFACT_AUTO_OPEN=0` to stop that, and press `Ctrl+]` to reopen the most recent artifact.
- Each publish becomes a **version**. Viewers with the page open see updates live, and **Share** lets you pick which version they see.
- In a local session, a version published elsewhere doesn't start a turn; Claude learns of it from a later Artifact tool result.
- To update from a different session, give Claude the artifact URL or attach the artifact with `/artifacts`. Without one of those, a new session creates a new artifact.

`/artifacts` lists artifacts you own and ones shared with you. Press `o` to open, `c` to copy the link, or `Enter` to attach to the current session.

## Sharing

A new artifact is private. The gallery is at claude.ai/code/artifacts.

| Plan | Sharing options |
|---|---|
| Pro, Max | A public link only |
| Team, Enterprise | Specific people or the whole organization (viewers sign in). Public links only after an Owner turns on **External sharing** |

- On Team and Enterprise, you can change someone from **viewer** to **editor**. Editors publish new versions by giving Claude the URL.
- Public viewers who are not signed in, or are outside your organization, see `Content is user-generated and unverified.` instead of your name.
- When Claude reads someone else's artifact, it works like WebFetch: Claude gets a summary and is warned about instructions in the page, and the full source is saved locally.

### Comments

Artifacts shared within an organization (Team/Enterprise) accept comments. Public artifacts don't. Claude reads comments when you give it the URL, or automatically when an editor uses **Send to Claude** or mentions `@claude` in a thread, which activates that thread. Claude can reply to or resolve only activated threads.

After publishing, your session watches the artifact for sent comments. Whether Claude auto-replies depends on your permission mode: it replies on its own if posting needs no approval, waits for approval otherwise, and pauses in plan mode. Auto-replies also pause after 60 sent comments per hour on one artifact. To stop them:
- Press `Ctrl+C` once at an idle prompt to pause all of them until your next message.
- Stop the live-updates task in `/tasks` to stop them for that artifact.
- Press `Ctrl+X Ctrl+K` twice within 3 seconds to stop them for the rest of the session.

## Runtime capabilities

### Live data through MCP connectors

```text
Build a dashboard artifact of our open pull requests that pulls the live list through my GitHub connector when the page loads.
```

- Claude declares which claude.ai connectors the page may call. Local MCP servers configured in Claude Code don't qualify (see [[mcp]]).
- Each call runs through the **viewer's** own connector account: viewers approve access first, may see different data, and any actions they take use their own account.
- Pages fetch on load, can refresh on an interval, and cache responses in the browser.
- A connector-backed artifact **can't be shared publicly** on any plan. On Pro and Max it therefore stays private.
- Ask Claude to add a fallback message naming the required connector in each live section.
- If a live section stays empty, the viewer may not have connected the connector (Settings > Connectors), may have declined the prompt (reload to be asked again), the organization may have **Enable artifact connectors** turned off, or the page may call tool names the connector doesn't expose.

### File downloads

The viewer blocks downloads the page starts itself, including `data:`/`blob:` links. Ask for a control such as "Add a button that downloads this table as a CSV file" and Claude declares the downloads capability. Your account must have that capability.

## Design

- Claude applies a built-in design skill and looks for your project's design system first. Record design tokens (colors, typography, spacing) where Claude can find them, such as the project's CLAUDE.md or a theme file. Your design system takes precedence over Claude's defaults, and your prompt takes precedence over both.
- Typefaces load from Google Fonts. Anything else is inlined as a `@font-face` data URI with fallback stacks.

### Draft a design canvas with `/design`

Use `/design` to **mock up** a UI, a screen flow, a landing page or a poster instead of building a working page. Claude drafts the design as artboards laid out on one canvas and publishes that canvas as an artifact running a research preview of Claude Design's editor. The brief is the argument:

```text
/design a settings screen for a mobile banking app
```

Open the published artifact to review the artboards. Where saving is enabled for your account, select an element on an artboard, change it, and save to publish a new version; otherwise you view the draft and export it as PNG or PDF. Then ask Claude to implement the artboard you picked.

`/design` needs a session where artifacts are available (see Availability below), so it runs on the Anthropic API only and does not appear on Amazon Bedrock, Google Cloud's Agent Platform, Microsoft Foundry or Claude Platform on AWS.

To make drafts use your real components, `/design-sync` converts your repo's React design system and uploads it to Claude Design, optionally named (`/design-sync Acme DS`); a first-time sync verifies every component and can take a few hours on a large repo. `/design-login` authorizes that access with your claude.ai account. Both need claude.ai, so neither is available on those four providers.

## Page constraints

| Constraint | Effect |
|---|---|
| External requests | Scripts only from cdnjs, the Tailwind CDN, the jQuery CDN and some jsDelivr paths such as `/npm/`. Fonts only from Google Fonts. Fetch, XHR and WebSocket reach only the page's origin and the Google Fonts hosts. External images are blocked |
| No backend | The page is static and can't authenticate viewers |
| Single page | Relative links don't resolve. Use in-page anchors |
| File types | `.html`, `.htm` or `.md`, encoded as UTF-8 or UTF-16LE with a BOM. Markdown renders as a styled document |
| Size | The rendered page must be 16 MiB or smaller. Large embedded images are the usual cause of failures |

Styled pages cost more output tokens than plain text. To keep costs down, prefer SVG or HTML/CSS diagrams to raster images, skip interactivity you don't need, and summarize large datasets.

## Availability

Every condition must hold, or Claude writes a local file or says it can't publish:
- **Plan:** Pro, Max, Team (on by default) or Enterprise (an Owner enables it).
- **Authentication:** a claude.ai login via `/login`. API key, gateway token and cloud-provider sessions can't publish.
- **Provider:** the Anthropic API. Not Bedrock, Google Cloud's Agent Platform or Foundry.
- **Organization:** no CMEK, HIPAA or Zero Data Retention (see [[data-and-privacy]]).
- **Surface:** the Claude Code CLI, the desktop app, or Claude Tag. Off by default in the Agent SDK, GitHub Action and MCP-server contexts, and when `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` is set.

## Disable

| Where | How |
|---|---|
| `/config` | Turn the **Artifacts** row off (writes `"enableArtifact": false`) |
| A settings file | `"enableArtifact": false` (see [[settings]]). `true` in project or local settings doesn't turn artifacts back on |
| Environment | `CLAUDE_CODE_DISABLE_ARTIFACT=1` |
| Permission rule | `Artifact` in `permissions.deny` |

Once artifacts are off through `--settings`, the env var or managed settings, no other settings file can turn them back on. A `WebFetch(domain:claude.ai)` deny or ask rule applies to artifact reads.

## Organization admin

Owners manage these in claude.ai admin settings (see [[enterprise-admin]]):
- **Artifacts** toggle (Settings > Claude Code > Capabilities). Enterprise RBAC can scope it by role.
- **Enable artifact connectors** (Settings > Capabilities).
- **External sharing** for public links. Turning it off blocks existing public links.
- Retention periods for private and shared artifacts (Settings > Data & privacy controls).
- Audit log events `claude_artifact_*`.
- On restricted networks, allowlist `*.claudeusercontent.com` alongside `claude.ai`. Optionally allow `fonts.googleapis.com`/`fonts.gstatic.com` and the four CDN hosts. If you block them, use a fast rejection rather than a silent drop.
- Compliance API: `GET /v1/compliance/code/artifacts`, `GET /v1/compliance/code/artifacts/{artifact_id}/versions/{version_id}`, `DELETE /v1/compliance/code/artifacts/{artifact_id}`.
