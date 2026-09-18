---
name: wiki-query
description: Answer a question about Claude Code or agentic systems from this repo's wiki, with [[slug]] citations. Use when the user asks how Claude Code works, how to configure or extend it, or about agent research covered in raw/.
user-invocable: true
argument-hint: "[question]"
---

# Query the wiki

1. **Read `wiki/hot.md`** for recent context.
2. **Semantic recall:** `./.venv/bin/python scripts/mem0/query_wiki.py "<question>"`. If it errors, run `./scripts/doctor.sh` and fall back to `wiki/index.md`.
3. **Read the top pages.** Each fact has one home page, so the first good match usually holds the answer; follow its links for adjacent topics.
4. **Answer** concisely with `[[slug]]` citations. Warn if a cited page's `valid_until` has passed.
5. **If the wiki doesn't cover it:** grep `raw/docs/official/llms.txt` and read the official page; then use WebFetch. A hook re-renders JavaScript-shell or bot-walled pages in Camoufox and gives you a file path to read. From Bash, use `./.venv/bin/python scripts/camoufox/fetch.py <url>` rather than `curl`.
6. **Anti-evaporation:** put any durable new finding on the page that owns the topic (never a duplicate page), append `wiki/log.md`, and reindex.
7. **Feed the eval:** if recall missed the page you cited, run `./scripts/eval-harvest.py --add "<question>" <slug> [<slug> ...]`.
