---
title: Wiki Index
updated: 2026-09-18
---

# Wiki Index

Every page in this wiki, by folder. Each topic has exactly one page that owns it; other pages link there rather than restating facts. Search first with `./.venv/bin/python scripts/mem0/query_wiki.py "<question>"`.

## Start here

Install Claude Code and learn how it works.

- [[how-claude-code-works]] — Agentic loop, tools, access, sessions
- [[install-and-setup]] — Install, log in, update, uninstall
- [[overview]] — What Claude Code is and where it runs

## Using Claude Code

Day-to-day work: prompting, memory, context, permissions, models, cost.

- [[claude-md-and-memory]] — CLAUDE.md, rules, imports, auto memory
- [[context-window]] — What fills context, compaction, caching
- [[costs-and-usage]] — Track spend, limits, and cut token use
- [[interface]] — Shortcuts, styles, status line, voice, a11y
- [[models-and-effort]] — Pick model, effort, fast mode, advisor
- [[permissions-and-modes]] — Permission modes, rules, auto mode, trust
- [[prompting-and-workflows]] — Verify, plan first, prompt precisely
- [[sandboxing-and-security]] — Bash sandbox, isolation choices, security model
- [[sessions-and-checkpoints]] — Resume, name, branch, rewind, transcripts

## Extending

Skills, subagents, agent teams, hooks, MCP servers and plugins.

- [[agent-teams]] — Coordinated Claude sessions led by one lead
- [[hooks]] — Hook events, exit codes, blocking a command
- [[mcp]] — Connect external tools through MCP servers
- [[plugins]] — Build, install, test and distribute plugins
- [[skills]] — SKILL.md format, frontmatter, scopes, invocation
- [[subagents]] — Built-in and custom subagents, frontmatter

## Automation

Background work, workflows, schedules, channels, artifacts and headless runs.

- [[artifacts]] — Publish live, shareable pages from a session
- [[channels]] — Push chat and webhook events into a session
- [[headless-mode]] — Run Claude Code non-interactively in scripts
- [[routines-and-scheduling]] — Routines, /schedule, /loop, cron tools
- [[workflows]] — Script-orchestrated subagents at scale
- [[worktrees-and-background-work]] — Parallel sessions: worktrees, agent view, --bg

## Surfaces

Where Claude Code runs besides the terminal.

- [[chrome-and-computer-use]] — Browser automation and screen control
- [[ci-cd-and-code-review]] — Claude in CI, and automated PR review
- [[claude-code-on-the-web]] — Cloud sessions, teleport, Remote Control, mobile
- [[desktop-app]] — Desktop Code tab: sessions, panes, SSH, WSL
- [[ide-integrations]] — VS Code extension and JetBrains plugin setup
- [[slack-and-claude-tag]] — @Claude in Slack channels, two ways

## Deployment

Providers, gateways, settings, org administration, networks and privacy.

- [[cloud-providers]] — Run Claude Code on AWS, GCP or Azure
- [[data-and-privacy]] — Training, retention, ZDR, telemetry opt-outs
- [[enterprise-admin]] — Managed settings, policy, OTel, analytics
- [[llm-gateways]] — Route Claude Code through a gateway
- [[network-config]] — Proxies, custom CAs, mTLS and allowlists
- [[settings]] — Settings files, scopes, precedence, keys

## Reference

Complete lists of commands, flags, variables and tools.

- [[cli-reference]] — Every claude subcommand and launch flag
- [[environment-variables]] — Claude Code env vars grouped by purpose
- [[glossary]] — Claude Code terms, one line each
- [[slash-commands]] — Every built-in / command, grouped by task
- [[tools-reference]] — Built-in tools, prompts, and key behaviors
- [[troubleshooting]] — Symptoms, causes and fixes with commands
- [[whats-new]] — 2026 timeline of current features

## SDK and API

Building on the Agent SDK, Managed Agents and the Claude API.

- [[advanced-tool-use]] — Tool search, programmatic calls, tool examples
- [[agent-sdk-control]] — SDK sessions, permissions, hooks, MCP, subagents
- [[agent-sdk-deployment]] — Host, secure, monitor and meter SDK agents
- [[agent-sdk]] — Claude Code's agent loop as a Python/TS library
- [[claude-models]] — Claude 5 lineup: IDs, limits, prices, lifecycle
- [[context-editing-and-memory-tool]] — API context clearing, compaction, memory tool
- [[managed-agents]] — Hosted agents: session log, harness, sandbox

## Research

Findings on agentic systems, mostly from Anthropic.

- [[agent-evals]] — Graders, pass@k vs pass^k, infra noise
- [[agent-memory]] — Temporal graph, structured and trigger memory
- [[agent-standards]] — Agent Skills spec and MCP under the AAIF
- [[agentic-patterns]] — Workflows vs agents and the five patterns
- [[claude-code-in-practice]] — Domain expertise matters more than coding
- [[coding-principles]] — Karpathy's four rules for LLM coding
- [[context-engineering]] — Context rot, just-in-time retrieval, compaction
- [[long-running-agents]] — Harnesses for multi-hour and multi-day runs
- [[multi-agent-systems]] — When multi-agent helps and how it fails
- [[self-improving-agents]] — Five training-free agent self-improvement loops
- [[skill-evolution]] — Research on evolving agent skills from traces
- [[tool-design]] — Writing, testing and trimming agent tools
- [[trustworthy-agents]] — Anthropic's agent safety principles and data
- [[why-over-what]] — Teaching principles beats demonstrations

## Ecosystem

Other agents and tools this project uses or compares against.

- [[camoufox]] — Stealth Firefox; repo's WebFetch fallback
- [[computer-use-linux]] — MCP server that drives a real Linux desktop
- [[context-compression-tools]] — Headroom and Toolaria shrink tool output
- [[hermes-agent]] — Nous Research's agent vs Claude Code
- [[mem0]] — mem0 API; repo's wiki index and mem0-hot
- [[open-models]] — OpenRouter, NIM and bridges for open models
- [[openai-codex]] — Codex CLI compared with Claude Code
- [[opencode]] — Terminal agent compared with Claude Code

## This project

How the harness works and how it runs from four agents.

- [[cross-agent-setup]] — One harness, four agents: what is shared and how
- [[harness]] — How this wiki repo checks and maintains itself

## Session files

- `hot.md` — recent decisions, fixes and gotchas, newest first.
- `log.md` — append-only record of changes to this wiki.

74 pages.
