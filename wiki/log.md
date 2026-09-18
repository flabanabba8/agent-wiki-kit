---
title: Change Log
updated: 2026-09-18
---

# Change Log

Append-only. Newest entry first. Older months move to `log-YYYY-MM.md`. Record what changed and why;
corrections belong here, never on the pages.

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
