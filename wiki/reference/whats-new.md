---
title: What's New in 2026
type: reference
tldr: "2026 timeline of current features"
sources:
  - raw/docs/official/whats-new__index.md
  - raw/docs/official/whats-new__2026-w37.md
  - raw/docs/changelog-2.1.271-to-2.1.272.md
  - raw/docs/changelog-2.1.273-to-2.1.274.md
  - raw/docs/changelog-2.1.275-to-2.1.278.md
  - raw/docs/official/claude-projects.md
  - raw/docs/official/commands.md
  - raw/docs/official/model-config.md
  - raw/docs/official/fast-mode.md
  - raw/docs/official/output-styles.md
  - raw/docs/official/keybindings.md
  - raw/docs/official/settings-reference.md
related: ["[[overview]]", "[[glossary]]", "[[models-and-effort]]", "[[cli-reference]]", "[[troubleshooting]]"]
created: 2026-09-15
updated: 2026-09-19
confidence: high
last_verified: 2026-09-19
aliases: [claude-code-release-timeline, new-features-2026, weekly-digest, feature-history]
valid_until: 2027-03-15
---

# What's New in 2026

Features that exist today, grouped by the month they landed, newest first. Each line points at the page that owns the detail; for flag and command spellings see [[cli-reference]] and [[slash-commands]].

## September 2026

- Projects coordinate parallel cloud sessions from one conversation; every thread starts with the project's repositories, instructions and memory — [[claude-projects]]
- A project with no CLAUDE.md takes its instructions from AGENTS.md; **Project instructions** in `/config` picks the file — [[claude-md-and-memory]]
- Auto mode defaults to the server-side classifier, which bills no overhead, for Claude API and Enterprise users and on Bedrock, Agent Platform, Foundry and gateways, where `CLAUDE_CODE_AUTO_MODE_SERVER=0` opts out; `/status` has an `Auto mode server` row — [[permissions-and-modes]]
- `CLAUDE_CODE_MCP_STARTUP_WAIT_MS` bounds how long a non-interactive first turn waits for connecting MCP servers; Bedrock, Agent Platform, Foundry and telemetry-disabled installs use the v2 MCP client with 2026-07-28 negotiation and skip `"type": "sdk"` entries with a warning — [[mcp]]
- `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1` sends request-class, agent-type, tool-duration and compaction hint headers to an LLM gateway, and `CLAUDE_GATEWAY_PROXY_IS_EGRESS_BOUNDARY=1` hands hostnames to a gateway's forward proxy instead of resolving them — [[llm-gateways]]
- The Claude apps gateway takes `store.connect_timeout_seconds`, a `headers:` map of static headers per upstream, and drains in-flight requests for 25 seconds on SIGTERM (`CLAUDE_GATEWAY_DRAIN_TIMEOUT_MS`); its `pricing` block and the `modelPricing` managed setting accept a multiplier above 1, up to 10, for internal chargeback — [[llm-gateways]]
- The `claude_code.managed_settings_resolved` OTel event reports managed-settings sources, redacted values under `OTEL_LOG_MANAGED_SETTINGS=1`; the `claude_code.llm_request` span carries `effort`, and `OTEL_LOG_TOOL_DETAILS=1` names agents, skills, plugins and MCP servers on cost metrics — [[enterprise-admin]]
- Remote Control forks a session from the Claude app into a background session on your computer; a cloud session's diff view compares its changes against any branch with **Compare against**, and `claude self-hosted-runner --drain-marker-file` reports a SIGTERM exit as a host drain — [[claude-code-on-the-web]]
- VS Code carries on the step a window reload interrupted, adds Memory and Instructions to Customize, takes `claudeCode.lockEditorGroups`, opens an agent map from the agent count, and edits hooks and permission rules there — [[ide-integrations]]
- A **Guests** setting in Claude Tag's Add channel and Add workspace forms sets guest access up front — [[slack-and-claude-tag]]
- `claude plugin eval` scores a plugin against a suite of test cases and reruns each without the plugin; `claude plugin eval init` drafts the cases and graders — [[plugins]]
- `--json` on `claude plugin install`, `uninstall`, `update`, `enable` and `disable` prints one JSON object on the last line of stdout; `--accept-command` accepts exactly the command a previous `--json` run showed; `--plugin-dir` pointed at a folder loads every immediate subfolder with a manifest, and `/plugin install <plugin> --marketplace <source>` offers to add the marketplace first — [[plugins]]
- Terminal sessions signed in to claude.ai sync the skills and plugins enabled there, unless `syncClaudeAiSkills` or `syncClaudeAiPlugins` is `false` — [[skills]] and [[plugins]]
- `maxEffortLevel`, at the top level or per model under `modelSettings`, caps the effort level on every provider; fast mode works in Claude Code Remote sessions your organization allows, and Fable always appears in `/model` on the Anthropic API, greyed out only where organization settings disable it — [[models-and-effort]]
- WebFetch fails with a deadline error if a page hasn't downloaded in five minutes (`CLAUDE_CODE_WEBFETCH_DEADLINE_MS` changes or removes it); Monitor watches always carry a deadline (30 minutes, 10 in `-p` runs) and notify Claude to re-arm; Claude reads a background task's output file with Read — [[tools-reference]]
- Desktop panes pop out into their own windows and dock back — [[desktop-app]]
- Typing `/` mid-prompt lists matching commands, and a plugin skill matches without its prefix; the `/config` panel takes mouse input in fullscreen rendering; a send-now key (`Ctrl+Enter`, or `Ctrl+X Ctrl+S`) interrupts the turn and sends every queued message at once — [[interface]]
- Claude picks a browser-tab icon for each artifact it publishes, and scheduled or Run now routine runs republish an artifact you can edit without asking; public artifacts, first publishes and deletes still ask — [[artifacts]]
- Per-command `allowed_domains` in auto mode with sandboxing opens only the hosts a command needs, for that command alone — [[sandboxing-and-security]]
- `omitClaudeMd` in agent frontmatter and `--agents` JSON runs a subagent without user, project and local CLAUDE.md, and a subagent's result arrives indented under a subagent-output header, so its text can't pass as session instructions — [[subagents]]

## August 2026

- Claude Fable 5.1 in Claude Code with a 1M-token context window — [[claude-models]]
- Auto mode is the default permission mode on Pro, Max and Team plans, and `--restricted` starts a session without the command-running tools or your user and project settings — [[permissions-and-modes]]
- Cross-session messaging passes findings between your sessions on macOS and Linux; `@` in the prompt mentions another session by name — [[worktrees-and-background-work]]
- Self-hosted environments run cloud sessions on your own infrastructure, in public beta on Team and Enterprise; a machine running `claude remote-control` appears as a device card in the phone app's Code tab — [[claude-code-on-the-web]]
- Fork mode is on in interactive sessions: Claude can hand a side task to a subagent that inherits the conversation — [[subagents]]
- `/design` drafts editable artboards in the CLI and Desktop and implements the one you pick, a research preview — [[artifacts]]
- The built-in Concise output style leads with the result and skips preamble; `/diff` opens a live panel beside the conversation in fullscreen rendering — [[interface]]
- `/skill-doctor` shows what each skill costs in context and how often it is used — [[skills]]
- `/resume` in the Desktop prompt box picks up a session you started in the CLI — [[desktop-app]]
- Claude drafts a feedback report you review and send from `/feedback` — [[slash-commands]]
- The `modelPicker` setting controls which models `/model` lists; `ANTHROPIC_DEFAULT_MODEL` sets the model new sessions start on — [[models-and-effort]]
- Computer use in the Desktop app runs in the background on macOS on Pro and Max — [[chrome-and-computer-use]]
- The Desktop session-limit card offers Auto-continue when limits reset — [[costs-and-usage]]
- GitLab merge request URLs work with `--worktree` and agent view; marketplaces clone bare `gitlab.com` URLs — [[ci-cd-and-code-review]]
- VS Code gets Focus view — [[ide-integrations]]

## July 2026

- Claude Opus 5 is the default Opus model, with a 1M-token context window and fast mode at $10/$50 per MTok; Claude Sonnet 5 is the default for Pro and Team Standard seats, with a native 1M-token context window and adaptive thinking on — [[claude-models]]
- Auto mode runs on Amazon Bedrock, Google Cloud's Agent Platform and Microsoft Foundry with no opt-in variable — [[cloud-providers]]
- Auto mode blocks transcript tampering and asks before `rm -rf` on unresolved variables — [[permissions-and-modes]]
- Subagents run in the background by default, and agent view rows show a state word with a classifier-written headline — [[subagents]]
- `/fork` copies the conversation into a new background session while you keep working — [[worktrees-and-background-work]]
- Artifacts reach live data through each viewer's own MCP connectors, with public sharing links and editor roles on Team and Enterprise — [[artifacts]]
- `/doctor` is a full setup checkup that proposes fixes; `/checkup` is its alias — [[troubleshooting]]
- Screen reader mode replaces the visual terminal interface with linear text — [[interface]]
- Claude in Chrome is generally available on all direct Anthropic plans — [[chrome-and-computer-use]]
- The Desktop app gets an in-app browser, an iOS Simulator pane in public beta, and a Linux beta on Ubuntu and Debian — [[desktop-app]]
- The Claude Security plugin runs a multi-agent vulnerability scan and turns findings you pick into patches — [[plugins]]
- `/code-review` runs as a background subagent — [[ci-cd-and-code-review]]
- `/radio` opens Claude FM lo-fi radio — [[slash-commands]]

## June 2026

- Artifacts turn a session's output into a live shareable page on claude.ai — [[artifacts]]
- Deny and ask rules match tool parameters with `Tool(param:value)`, for example `Agent(model:opus)`; auto mode blocks destructive git commands when you didn't ask to discard local work, and prompts before writing files that can run code in `acceptEdits` — [[permissions-and-modes]]
- `/config key=value` sets any setting from the prompt, in `-p` and from Remote Control — [[settings]]
- `claude mcp login` authenticates a configured MCP server from your shell; `claude mcp logout` clears its credentials — [[mcp]]
- Subagents can spawn their own subagents, with background chains capped at five levels; background subagents surface permission prompts in the main session — [[subagents]]
- `fallbackModel` configures up to three fallback models tried in order — [[models-and-effort]]
- `/cd` moves a session to a new working directory without rebuilding the prompt cache — [[slash-commands]]
- `claude --safe-mode` starts with all customizations disabled for troubleshooting — [[troubleshooting]]
- `/plugin list` prints your installed plugins inline — [[plugins]]
- Managed deployments can require an approved Claude Code version range — [[enterprise-admin]]
- Shell mode explains command output without a second prompt (`! npm test`) — [[interface]]
- `/rewind` can resume a conversation from before `/clear` — [[sessions-and-checkpoints]]

## May 2026

- Agent view: `claude agents` opens one screen for every session, showing what is running, blocked or done; background sessions appear in `/resume` and stay alive when pinned, and `worktree.baseRef` branches new worktrees from the remote default or local `HEAD` — [[worktrees-and-background-work]]
- Dynamic workflows orchestrate dozens to hundreds of subagents from a script Claude writes — [[workflows]]
- `/goal` keeps Claude working across turns until a completion condition holds — [[prompting-and-workflows]]
- `/effort xhigh` for the hardest tasks, and fast mode at $10/$50 per MTok — [[models-and-effort]]
- `/usage` breaks plan limits down by skill, subagent, plugin and MCP server — [[costs-and-usage]]
- `/code-review` reports correctness bugs — [[ci-cd-and-code-review]]
- The Rewind menu compresses earlier context with "Summarize up to here" — [[sessions-and-checkpoints]]
- Plugins load from `.zip` archives and URLs: `--plugin-dir` takes archives and `--plugin-url` fetches one for the session; the security-guidance plugin reviews Claude's changes for vulnerabilities as it works — [[plugins]]
- Auto mode hard deny rules block actions regardless of allow exceptions — [[permissions-and-modes]]
- Hooks see the active effort level through `effort.level` and `$CLAUDE_EFFORT` — [[hooks]]
- History search spans all your projects, with `Ctrl+R` and `Ctrl+S` to cycle its scope — [[interface]]

## April 2026

- Routines fire templated cloud agents from a schedule, a GitHub event or an API call; `/loop` self-paces when you omit the interval — [[routines-and-scheduling]]
- The `xhigh` effort level with an interactive `/effort` slider — [[models-and-effort]]
- Computer use comes to the CLI as a research preview, for verification only a GUI can do — [[chrome-and-computer-use]]
- The Monitor tool streams background events into the conversation, so Claude can tail logs live — [[tools-reference]]
- `/ultrareview` runs a fleet of bug-hunting cloud agents and lands findings back in the CLI or Desktop (`claude ultrareview` does it from CI and scripts), and `/autofix-pr` turns on PR auto-fix from your terminal — [[ci-cd-and-code-review]]
- `/team-onboarding` packages your setup into a replayable guide, and `/powerup` teaches features in interactive lessons — [[slash-commands]]
- Mobile push notifications ping your phone when a long task finishes or Claude needs you — [[claude-code-on-the-web]]
- The CLI ships as native binaries; on Windows, Git for Windows is optional because Claude Code uses PowerShell as its shell tool, and sign-in works without a browser callback via `claude auth login` — [[install-and-setup]]
- `claude project purge` cleans up local state for a project — [[cli-reference]]
- Pasting a PR URL into `/resume` finds the session that created it — [[sessions-and-checkpoints]]
- Session recap shows what happened while the terminal was unfocused; custom themes ship from `/theme` or a plugin — [[interface]]
- A per-tool MCP result-size override reaches 500K, and plugin executables land on the Bash tool's `PATH` — [[mcp]]

## March 2026

- Auto mode: a classifier handles permission prompts, running safe actions and blocking risky ones — [[permissions-and-modes]]
- Computer use in the Desktop app — [[chrome-and-computer-use]]
- PR auto-fix on cloud sessions — [[ci-cd-and-code-review]]
- A native PowerShell tool for Windows — [[tools-reference]]
- Conditional `if` hooks — [[hooks]]
