---
title: Glossary
type: reference
tldr: "Claude Code terms, one line each"
sources:
  - raw/docs/official/glossary.md
  - raw/docs/official/agents.md
  - raw/docs/official/artifacts.md
  - raw/docs/official/commands.md
  - raw/docs/official/agent-view.md
  - raw/docs/official/routines.md
  - raw/docs/official/workflows.md
  - raw/docs/official/fast-mode.md
  - raw/docs/official/plugin-marketplaces.md
  - raw/docs/official/advisor.md
  - raw/docs/official/goal.md
  - raw/docs/official/self-hosted-environments.md
  - raw/docs/official/claude-tag.md
  - raw/docs/official/chrome.md
related: ["[[overview]]", "[[how-claude-code-works]]", "[[slash-commands]]", "[[whats-new]]", "[[troubleshooting]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [claude-code-terminology, what-is-a-subagent, define-claude-code-terms, jargon]
---

# Glossary

Definitions only. Each term names the page that owns the detail — configuration, syntax and limits live there, not here.

## A

**Advisor tool** — A stronger second model Claude consults mid-task; it receives the whole conversation and returns guidance. See [[models-and-effort]].

**Agent teams** — Several independent sessions coordinated by a team lead, with a shared task list and peer-to-peer messaging; each teammate has its own context window and you can talk to any of them. See [[agent-teams]].

**Agent view** — One screen for every background session, opened with `claude agents`: what is running, what is blocked on you, what is done. See [[worktrees-and-background-work]].

**Agentic coding** — A workflow where the model reads files, runs commands and makes changes itself while you watch or step away. See [[overview]].

**Agentic harness** — The tools, context management and execution environment that turn a model into a coding agent; Claude Code is the harness, Claude is the model inside it. See [[how-claude-code-works]].

**Agentic loop** — The cycle Claude repeats per task: gather context, act, verify, repeat. Hooks, skills and MCP plug into its phases. See [[how-claude-code-works]].

**Artifact** — A live interactive web page a session publishes to a private URL on claude.ai, updated in place on republish. See [[artifacts]].

**Auto memory** — Notes Claude writes for itself from your corrections, stored per repository under `~/.claude/projects/`. See [[claude-md-and-memory]].

**Auto mode** — A permission mode where a classifier model reviews actions instead of you, blocking scope escalation, untrusted infrastructure and prompt injection. See [[permissions-and-modes]].

## B

**Background session** — A full conversation that keeps running with no terminal attached; you attach, reply and leave whenever you want. See [[worktrees-and-background-work]].

**Bare mode** — `claude --bare` starts a session with no hooks, skills, commands, subagents, plugins, MCP servers, auto memory or CLAUDE.md. See [[headless-mode]].

**Bundled skill** — A prompt-based playbook shipped with Claude Code, such as `/code-review` or `/loop`, that Claude orchestrates rather than fixed logic. See [[skills]].

## C

**Channel** — An MCP server that pushes events into a running session so Claude can react while you are away; it can reply back the same way. See [[channels]].

**Checkpoint** — A restore point taken at each prompt that starts a turn; `/rewind` puts code, conversation or both back. Separate from git, and blind to Bash-tool changes. See [[sessions-and-checkpoints]].

**`.claude` directory** — Where project-scoped configuration lives (settings, hooks, skills, subagents, rules); `~/.claude/` holds your user-level defaults. See [[settings]].

**CLAUDE.md** — Instructions you write, loaded at session start as a user message after the system prompt; all discovered files are concatenated broadest scope first. See [[claude-md-and-memory]].

**Claude Tag** — A Slack integration that runs `@Claude` in your team's channels under your organization's shared identity. See [[slack-and-claude-tag]].

**Cloud session** — A session that runs somewhere other than your machine, started from claude.ai, the apps, `claude --cloud` or a routine. See [[claude-code-on-the-web]].

**Command** — A reusable instruction you invoke by typing `/name`. Unrelated senses: `claude` CLI subcommands, and the `command` field of a stdio MCP server entry. See [[slash-commands]].

**Compaction** — Automatic summarization as the context window fills: old tool outputs clear first, then the conversation is summarized. See [[context-window]].

**Connector** — An MCP server added to your claude.ai account instead of configured locally; it appears in `/mcp` when you sign in with that account. See [[mcp]].

**Context window** — A session's working memory: conversation, file contents, command output, memory files, skills and system instructions. See [[context-window]].

**Cross-session messaging** — Lets Claude list and message your other sessions, on this machine, another machine or the web, to pass findings between them. See [[worktrees-and-background-work]].

## D

**Design canvas** — Artboards Claude drafts from a `/design` brief, published as an artifact that runs Claude Design's editor for hand edits and PNG or PDF export. See [[artifacts]].

**Dispatch** — A phone-initiated task router that spawns a session in the Desktop app when you send a coding task from the Claude mobile app. See [[desktop-app]].

**Dynamic workflow** — A JavaScript script Claude writes that orchestrates many subagents in the background and that you can read and rerun. See [[workflows]].

## E

**Effort level** — The setting that controls adaptive reasoning: higher means more thinking tokens and deeper reasoning, lower is faster and cheaper. See [[models-and-effort]].

**Extended thinking** — Visible step-by-step reasoning before the answer, shown in gray italics; capped by effort level or `MAX_THINKING_TOKENS` on fixed-budget models. See [[models-and-effort]].

## F

**Fast mode** — A high-speed Claude Opus configuration, up to 2.5x faster at a higher price per token, toggled with `/fast`. Same model, same quality. See [[models-and-effort]].

**Forked subagent** — A subagent that inherits the full conversation instead of starting fresh, started with `/subtask`. See [[subagents]].

## G

**Goal** — A completion condition set with `/goal`; after each turn a small fast model checks it and Claude keeps working until it holds or the model judges it impossible. See [[prompting-and-workflows]].

## H

**Hook** — A handler that runs automatically at a fixed lifecycle point. Three levels: the hook event, a matcher that filters it, and the handler (shell command, HTTP endpoint, MCP tool, prompt or subagent). See [[hooks]].

## M

**Managed settings** — Settings your organization enforces, delivered from Anthropic's servers or deployed to devices outside `~/.claude`; user and project settings cannot override them. See [[enterprise-admin]].

**Marketplace** — A catalog that distributes plugins, with discovery, version tracking and automatic updates, from a git repository or a local path. See [[plugins]].

**MCP (Model Context Protocol)** — An open standard for connecting AI tools to external data sources and services. See [[mcp]].

**MCP server** — A program that gives Claude tools, prompts or resources over MCP, added with `claude mcp add`, in `.mcp.json`, through a plugin, or as a connector. See [[mcp]].

**MCP Tool Search** — Defers MCP tool schemas until needed: only names and server instructions load at startup, so idle servers cost little context. See [[mcp]].

## N

**Non-interactive mode** — One prompt, printed result, exit, via `claude -p`. Still saved as a resumable session; the Agent SDK is its Python and TypeScript equivalent. See [[headless-mode]].

## O

**Output style** — Configuration that changes the instructions Claude Code gives Claude; a custom style can replace the default software-engineering instructions. See [[interface]].

## P

**Permission mode** — The session's baseline approval behavior, cycled with `Shift+Tab`: `default` (labeled Manual), `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`. See [[permissions-and-modes]].

**Permission rule** — A settings entry that allows, asks about or denies a tool call by tool name and argument pattern, evaluated deny→ask→allow, first match wins. See [[permissions-and-modes]].

**Plan mode** — A permission mode where Claude researches and proposes changes without editing source files, then presents a plan for approval. See [[permissions-and-modes]].

**Plugin** — An installable bundle of skills, hooks, subagents and MCP servers; plugin skills are namespaced `plugin-name:skill-name`. See [[plugins]].

**Powerup** — Quick interactive lessons with animated demos that teach Claude Code features in the terminal, opened with `/powerup`. See [[interface]].

**Project trust** — The dialog that accepts a directory before Claude Code loads its configuration; until you accept, some repository-supplied content is held back. See [[permissions-and-modes]].

**Prompt injection** — Hostile instructions hidden in a file, page or tool result that try to redirect Claude. See [[sandboxing-and-security]].

## R

**Remote Control** — Continuing a session that runs on your machine from your phone or a browser; execution and files stay local, only the interface is remote. See [[claude-code-on-the-web]].

**Routine** — A saved configuration — prompt, repositories, connectors — that runs on cloud infrastructure from a schedule, an API call or a GitHub event. See [[routines-and-scheduling]].

**Rules** — Modular instruction files in `.claude/rules/` that load alongside CLAUDE.md, optionally path-scoped so they load only when relevant. See [[claude-md-and-memory]].

## S

**Sandboxing** — OS-level filesystem and network isolation for the Bash tool, a separate layer from permission rules. See [[sandboxing-and-security]].

**Self-hosted environment** — Infrastructure your organization operates that executes cloud sessions inside your network. See [[claude-code-on-the-web]].

**Session** — A conversation tied to your working directory with its own context window; resume with `claude -c`, fork with `--fork-session`, or run several in parallel. See [[sessions-and-checkpoints]].

**Settings layers** — The precedence order Claude Code reads configuration in: managed policy, command-line arguments, local, project, then user settings. See [[settings]].

**Skill** — A `SKILL.md` file of instructions, knowledge or a workflow that Claude loads when relevant or that you invoke as `/skill-name`, following the Agent Skills open standard. See [[skills]].

**Subagent** — A specialized assistant with its own context window, system prompt, tool access and permissions that does a delegated task and returns a summary. Built-ins: Explore, Plan, general-purpose. See [[subagents]].

**Surface** — Any place you reach Claude Code — CLI, VS Code, JetBrains, Desktop, claude.ai — all sharing one engine. See [[overview]].

## T

**Teleport** — `/teleport` pulls a cloud session into your local terminal, branch and history included; `claude --cloud` sends work the other way. See [[claude-code-on-the-web]].

**Tool** — An action Claude can take: read a file, edit code, run a command, search the web, spawn a subagent. See [[tools-reference]].

**Turn** — One complete response, from your message to Claude finishing, with any number of tool calls in between. Stop hooks fire at its end. See [[how-claude-code-works]].

## V

**Verification loop** — A check Claude can run itself, such as a test suite or a build, that it iterates against instead of stopping at the first attempt. See [[prompting-and-workflows]].

## W

**Worktree isolation** — Running a session or subagent in a separate git worktree under `.claude/worktrees/`, so parallel agents never share files. See [[worktrees-and-background-work]].
