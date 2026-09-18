---
title: Hot Cache
updated: 2026-09-18
---

# Hot Cache

Recent decisions, fixes and gotchas. Read this first in a new session, then `index.md`.

## Wiki State

- **74 pages**: start (3), using (9), extending (6), automation (6), surfaces (6), deployment (6), reference (7), sdk-and-api (7), research (14), ecosystem (8), project (2)
- **~115K words**, 1,160 wikilinks (70 unique), 400 raw files
- Sources are not in the repo: run `./scripts/sources.py fetch` to rebuild `raw/` from the manifest.

## Compressed Observations (newest first)

💡 2026-09-18 .claude/ is the source of truth; run scripts/agents/sync.py after changing agents or MCP
💡 2026-09-18 tldr, section heading and aliases repeat in every mem0 chunk: cheapest retrieval lever
⚠️ 2026-09-18 Skill frontmatter must be strict YAML: OpenCode silently drops a skill Claude tolerates
⚠️ 2026-09-18 Codex edits arrive as patch text in tool_input.command, with no file path field
⚠️ 2026-09-18 Hermes keeps MCP, plugins and trust per user: run scripts/agents/hermes/setup.sh
⚠️ 2026-09-18 Word counts include table pipes: a 3-column row costs 4 words before content
⚠️ 2026-09-18 Some docs sites serve a JS shell to every browser; append .md to the path for the source
⚠️ 2026-09-18 `claude -p` without `--bare` runs a repo's hooks and .mcp.json with no trust prompt