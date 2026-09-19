---
title: Change Log
updated: 2026-09-19
---

# Change Log

Append-only. Newest entry first. Older months move to `log-YYYY-MM.md`. Record what changed and why;
corrections belong here, never on the pages.

## 2026-09-19 — re-verified against refetched sources; Projects added

Upstream moved: 134 of the official Claude Code docs pages changed, two new ones appeared, and
releases 2.1.275 to 2.1.278 shipped. All 51 pages that cite a changed source were re-checked against
the new text, and `sources/manifest.tsv` now records the new snapshot.

**Terminology.** The surface the docs used to call by its product name is now **cloud sessions**, and
the wiki says so throughout. [[claude-code-on-the-web]] keeps its slug, because the docs URL did not
change and other pages link to it, but is retitled and answers to `cloud-session` as an alias.

**New page.** [[claude-projects]] covers Projects: one conversation in which Claude coordinates
parallel cloud-session threads that share repositories, instructions and memory. It is a public beta
on Pro and Max, so the page carries `valid_until`. [[overview]], [[worktrees-and-background-work]],
[[routines-and-scheduling]], [[glossary]] and [[whats-new]] point at it.

**Two pages had become wrong, not just stale.** [[claude-md-and-memory]] said Claude Code reads
`CLAUDE.md` and not `AGENTS.md`. It now reads `AGENTS.md` directly as project instructions when no
`CLAUDE.md` sits at or above the working directory, and with both present it reads `CLAUDE.md` alone;
the page documents the default check, the Project instructions setting and the sessions that still
need an import. [[permissions-and-modes]] had the auto-mode classifier inverted: server-side review
is the default for Claude API and Enterprise users and on cloud providers and gateways, and the
variable opts out rather than in.

**Other substantive changes.** [[skills]] and [[plugins]] cover claude.ai skills and plugins syncing
into terminal sessions and the settings that turn that off. [[llm-gateways]] was reworked around the
rewritten Claude apps gateway docs. [[agent-sdk]], [[agent-sdk-control]] and [[agent-sdk-deployment]]
absorbed the new SDK configuration page rather than adding a page of their own.
[[sandboxing-and-security]] gained per-command allowed domains in auto mode. [[hooks]] gained the
Bash edit diff and the MCP server object on tool events. [[subagents]] gained the handback report.
[[troubleshooting]] was checked against a heavily rewritten errors page. [[interface]] restores
`/output-style` as a working command. The TaskOutput tool is gone, so the variable and setting that
sized its output no longer do anything, which [[environment-variables]] now says.

**Left out on purpose.** Version floors such as "requires 2.1.277 or later" are not on the pages, per
the current-facts rule, so a reader on an older build gets no warning from them. A few facts were cut
for the 2,000-word cap rather than for doubt, among them the claude.ai/code URL pre-fill parameters
and the full Claude Tag credential preset list.

**Checked for this project's own setup:** having both `CLAUDE.md` and an `AGENTS.md` symlink does not
load the instructions twice, recorded on [[cross-agent-setup]].

## 2026-09-18 — initial release

The wiki ships with 74 pages in eleven topic folders, each written from primary sources and verified
against them on the dates in its frontmatter. The sources themselves are not distributed:
`sources/manifest.tsv` lists where each one came from, with a hash of its content at verification
time, and `./scripts/sources.py fetch` rebuilds `raw/` locally. A source that differs after fetching
means upstream has moved since the page was checked, which is what `./scripts/freshness.py` reports.

Pages keep contradiction callouts where two current sources disagree. Examples: who operates
Microsoft Foundry inference ([[cloud-providers]]), one LLM judge versus one per dimension
([[agent-evals]]), the OpenCode local MCP timeout default ([[opencode]]) and the Hermes MCP tool-name
prefix ([[hermes-agent]]).
