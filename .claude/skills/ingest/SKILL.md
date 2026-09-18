---
name: ingest
description: Ingest a new source into the wiki. Use when the user adds or points at a document, URL, paper or release notes and wants the knowledge added to the wiki.
user-invocable: true
argument-hint: "[path-or-url]"
---

# Ingest a source

1. **Save the source to `raw/`** as a new file with a SOURCE header (url, publisher, publication date, fetch date). Official Claude Code docs: `./scripts/refetch-docs.sh`. New Claude Code releases: `./scripts/changelog-delta.sh`. Never edit an existing raw file.
2. **Read it** and list the 3–5 facts that matter to a Claude Code user.
3. **Find the owning page** for each fact: `./.venv/bin/python scripts/mem0/query_wiki.py "<topic>"` and `wiki/index.md`. Each topic has exactly one home page.
4. **Update the owning page**: replace outdated statements (no "changed since" notes), add the raw file to `sources:`, set `updated` and `last_verified`. Create a new page only when no page owns the topic; there are no source-summary pages.
5. **Check identifiers:** `python3 scripts/lint_identifiers.py` must report nothing for pages you touched.
6. **Wire it up:** new pages go in `wiki/index.md`; append a dated entry to `wiki/log.md`; add a `wiki/hot.md` line; run `./scripts/hot-compact.py`.
7. **Verify:** `./.venv/bin/python scripts/mem0/index_wiki.py`, `./scripts/wiki-lint.sh`.
8. **Record the source:** `./scripts/sources.py manifest --accept <the new raw files>`. `raw/` is gitignored because sources are other people's text; the manifest and the identifier index are what get committed. If `raw/` is empty, run `./scripts/sources.py fetch` first.
