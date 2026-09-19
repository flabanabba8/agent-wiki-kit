---
title: Hot Cache
updated: 2026-09-18
---

# Hot Cache

Recent decisions, fixes and gotchas. Read this first in a new session, then `index.md`.

## Wiki State

- **75 pages**: start (3), using (9), extending (6), automation (7), surfaces (6), deployment (6), reference (7), sdk-and-api (7), research (14), ecosystem (8), project (2)
- **~121K words**, 1,200 wikilinks (71 unique), 403 raw files
- Sources are not in the repo: run `./scripts/sources.py fetch` to rebuild `raw/` from the manifest.

## Compressed Observations (newest first)

✅ 2026-09-19 51 pages re-verified against refetched docs; manifest records the new snapshot
📝 2026-09-19 New page [[claude-projects]]: Claude coordinates parallel cloud-session threads (Pro/Max beta)
🔧 2026-09-19 Claude Code reads AGENTS.md when no CLAUDE.md exists; with both it reads CLAUDE.md only
🔧 2026-09-19 Auto mode defaults to server-side review; CLAUDE_CODE_AUTO_MODE_SERVER=0 opts out
💡 2026-09-19 The docs now say cloud sessions; [[claude-code-on-the-web]] keeps its slug as an alias target
⚠️ 2026-09-19 claude.ai skills and plugins sync into terminal sessions; syncClaudeAiSkills/Plugins opt out
⚠️ 2026-09-19 Writer agents can die on API timeouts: have them save page by page, then resume the rest
💡 2026-09-18 .claude/ is the source of truth; run scripts/agents/sync.py after changing agents or MCP
💡 2026-09-18 tldr, section heading and aliases repeat in every mem0 chunk: cheapest retrieval lever
⚠️ 2026-09-18 Skill frontmatter must be strict YAML: OpenCode silently drops a skill Claude tolerates
⚠️ 2026-09-18 Codex edits arrive as patch text in tool_input.command, with no file path field
⚠️ 2026-09-18 Hermes keeps MCP, plugins and trust per user: run scripts/agents/hermes/setup.sh
⚠️ 2026-09-18 Word counts include table pipes: a 3-column row costs 4 words before content
⚠️ 2026-09-18 Some docs sites serve a JS shell to every browser; append .md to the path for the source
⚠️ 2026-09-18 `claude -p` without `--bare` runs a repo's hooks and .mcp.json with no trust prompt