---
title: mem0 (Semantic Index and Hot Recall)
type: entity
tldr: "mem0 API; repo's wiki index and mem0-hot"
sources:
  - raw/docs/mem0/api-capture-2.0.20.md
  - scripts/mem0/README.md
  - scripts/mem0/config.py
  - scripts/mem0/index_wiki.py
  - scripts/mem0/query_wiki.py
  - scripts/mem0/mcp_server.py
  - scripts/mem0/page_status.py
  - scripts/mem0/remember_cli.py
  - scripts/mem0/hot_audit.py
  - scripts/mem0/requirements.txt
  - scripts/mem0/setup.sh
  - scripts/hooks/session-end.sh
  - scripts/hooks/session-start.sh
  - .mcp.json
related: ["[[agent-memory]]", "[[harness]]", "[[mcp]]", "[[claude-md-and-memory]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [mem0ai, semantic-index, query-wiki, mem0-hot, hot-recall]
---

# mem0 (Semantic Index and Hot Recall)

mem0 (`mem0ai` on PyPI) is a memory library. Its `Memory` class stores text in a vector store, and when `infer=True` it uses an LLM to extract facts before storing them. This repo runs it fully locally for two separate jobs:

1. A **semantic index over `wiki/`**. Search finds candidate pages to read, which scales better than scanning `index.md`.
2. **`mem0-hot`**, a scratch memory that persists across sessions for short-lived notes.

The wiki pages remain the source of truth, and the index can always be rebuilt from them. For how vector memory compares with an LLM-maintained wiki, see [[agent-memory]]. For Claude Code's built-in memory, see [[claude-md-and-memory]].

## Stack

| Layer | Choice |
|---|---|
| Library | `mem0ai` 2.0.20 installed (`requirements.txt`: `mem0ai>=2.0,<3`) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2`, 384 dims, run offline on CPU `torch` |
| Vector store | Embedded Qdrant, one path per namespace under `.mem0-data/` |
| History | SQLite at `.mem0-data/history.db` |
| LLM | Anthropic `claude-haiku-4-5`, called only for `infer=True` adds |

Setup: `scripts/mem0/setup.sh` creates `.venv` (with `uv` and `--torch-backend cpu` when available), installs the requirements and caches the embedding model. You don't need an API key to index or search. `scripts/mem0/config.py` sets `MEM0_TELEMETRY=false` and `HF_HUB_OFFLINE=1`. You can override `WIKI_MEM0_DATA`, `WIKI_MEM0_EMBED_MODEL`, `WIKI_MEM0_EMBED_DIMS` (change it together with the model) and `WIKI_MEM0_LLM_MODEL`. `ANTHROPIC_API_KEY` turns on fact extraction for hot notes.

## The installed Memory API (2.0.20)

```python
Memory.from_config(config_dict)
m.add(messages, *, user_id=None, agent_id=None, run_id=None, metadata=None,
      timestamp=None, expiration_date=None, infer=True, memory_type=None, prompt=None)
m.search(query, *, top_k=20, filters=None, threshold=0.1, rerank=False,
         explain=False, reference_date=None, show_expired=False, **kwargs)
m.get(memory_id)
m.get_all(*, filters=None, top_k=20, show_expired=False, **kwargs)
m.update(memory_id, text=None, metadata=None, expiration_date=..., data=None)
m.delete(memory_id)
m.delete_all(user_id=None, agent_id=None, run_id=None)
m.history(memory_id)
m.reset()
```

Gotchas you'll hit:

- **Scoping differs between methods.** `add()` takes `user_id`, `agent_id` and `run_id` as top-level arguments. `search()` and `get_all()` raise `ValueError` for those arguments. Pass `filters={"user_id": "..."}` instead, and include at least one id.
- **The result count is `top_k`.** Both methods also accept `**kwargs`, so a stray `limit=` raises nothing and does nothing (the repo's query code notes this).
- **Filters support operators:** `eq`, `ne`, `in`, `nin`, `gt`, `gte`, `lt`, `lte`, `contains`, `icontains`, `*`, `AND`, `OR`, `NOT`.
- **`infer=False` stores text verbatim.** No LLM runs, so no key is needed.
- **Return shapes:** `add` and `search` return `{"results": [...]}`, with items carrying `id`, `memory`, `event` or `score`, and `metadata`.
- **Expiry and edits:** `expiration_date` (YYYY-MM-DD) hides a memory from search unless `show_expired=True`. In `update`, prefer `text`; `data` is a deprecated alias.
- **Platform-only arguments:** `timestamp` and `reference_date` are marked platform-only and are not supported in OSS.

## The wiki index

```bash
./.venv/bin/python scripts/mem0/index_wiki.py            # incremental sync
./.venv/bin/python scripts/mem0/index_wiki.py --rebuild  # wipe and reindex
./.venv/bin/python scripts/mem0/query_wiki.py "how do hooks work" -k 6
```

**`index_wiki.py`** works like this:

- **What it indexes:** every `wiki/**/*.md` except root-level `log*.md` files.
- **Chunking:** frontmatter is parsed, and chunks are section-aware, 150 words each so they fit MiniLM's 256-token limit. Each chunk gets a header (title, tldr, type, heading trail, aliases) and is stored with `infer=False` under `user_id="wiki"`, along with its metadata (path, type, related, confidence, section).
- **Incremental sync:** `.mem0-data/wiki-manifest.json` records each page's SHA-256 and chunk ids. Unchanged pages are skipped, edited pages are re-synced, and deleted pages are pruned.
- **Embedder guard:** `.mem0-data/index-meta.json` records the embedding model and dims. If either changes, the script forces a rebuild.
- **Rebuilds:** `--rebuild` deletes the namespace directory on disk instead of calling `delete_all`, which the script notes is paginated and capped.

**`query_wiki.py`** works like this:

- **Search:** it searches with `top_k=max(k*8, 24)` and keeps the best chunk for each page.
- **Deprecated pages:** `page_status.py` moves pages marked `status: deprecated` below current ones. It reads the status from the page file, so no reindex is needed.
- **Output:** for each result it prints path, score, title, tldr, the matched section and related pages.
- **Query log:** it appends each query to `outputs/.query-log.jsonl`, which the eval harvester reads.

Git `post-commit`/`post-merge` hooks re-run the incremental sync in the background (see [[harness]]).

## mem0-hot scratch memory

`.mcp.json` declares `mem0-hot` as `./.venv/bin/python scripts/mem0/mcp_server.py`. It uses FastMCP and needs `mcp>=1.2,<2`. The server works only in the separate `hot` Qdrant store, so it never locks the wiki index. Embedded Qdrant takes an exclusive lock on a store and fails at once if another process holds it, so every caller here takes a blocking cross-process lock, opens the store for one operation and closes it again. Several agents can therefore run this server and query the index at the same time; `WIKI_MEM0_LOCK_WAIT` sets how long a caller waits (default 120 seconds). See [[cross-agent-setup]]. For how project MCP servers load, see [[mcp]].

| Tool | Behaviour |
|---|---|
| `remember(text)` | `add(text, user_id="hot", infer=<ANTHROPIC_API_KEY set>)` |
| `recall(query, k=5)` | `search(query, filters={"user_id": "hot"}, top_k=k)`, returned as a bullet list |

Session hooks feed it automatically:

- **`scripts/hooks/session-end.sh`** writes one note per session: branch, last commit, number of uncommitted files, latest `log.md` heading and re-verify queue size. It keeps the last 20 notes in `.mem0-data/hot-recent.jsonl` and also calls `remember_cli.py` in the background to add the note to the hot store.
- **`scripts/hooks/session-start.sh`** prints the last 3 of those notes into the new session's context.

Hot memory is only for short-lived facts. `./.venv/bin/python scripts/mem0/hot_audit.py` lists hot entries oldest-first and flags anything older than 14 days (change the window with `--days N`). After you've moved the keepers into wiki pages, `--purge` deletes the flagged entries.
