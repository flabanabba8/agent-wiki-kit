# mem0 wiki integration

Local-first [mem0](https://mem0.ai/) layer that augments the LLM-wiki with the three
improvements described on the wiki's `agent-memory` and `mem0` pages. **No API keys are
required** to build or query the index — embeddings run locally via sentence-transformers,
the vector store is embedded Qdrant, and history is SQLite. (Set `ANTHROPIC_API_KEY`
only to enable fact-extraction on the hot-recall layer.)

## The three reasons

| # | Improvement | Where | Needs |
|---|---|---|---|
| 1 | **Semantic search over `wiki/`** — scales past the ~200-page `index.md` cliff | `index_wiki.py`, `query_wiki.py` | nothing (local) |
| 2 | **Hot-recall layer** — ephemeral cross-session scratch memory, MCP tools `remember`/`recall` | `mcp_server.py` (wired in the project `.mcp.json`) | optional key for inference |
| 3 | **Temporal validity** — `supersedes:`/`valid_until:` frontmatter + checker | `../wiki-temporal.sh`, `CLAUDE.md` | nothing |

## Setup

```bash
scripts/mem0/setup.sh                              # venv + deps (one-time, downloads ~80MB model on first index)
./.venv/bin/python scripts/mem0/index_wiki.py      # build the semantic index
./.venv/bin/python scripts/mem0/query_wiki.py 'how do hooks work'
```

`index_wiki.py` is **incremental** — a content-hash manifest (`.mem0-data/wiki-manifest.json`)
means re-runs only re-embed changed pages and prune deleted ones. Run it after any wiki edit
(the Ingest/Query workflows in `CLAUDE.md` say so). `--rebuild` wipes and reindexes.

## Architecture

- **Two isolated stores** (separate Qdrant paths — embedded Qdrant is single-writer per path):
  `wiki` (the page index) and `hot` (scratch memory). The MCP server only touches `hot`, so it
  never locks the index used by the CLI.
- **`infer=False` for the wiki index** — pages are stored as raw ~220-word chunks with metadata
  (`path`, `title`, `tldr`, `chunk`). This is a document index, not conversational memory, so no
  LLM is called → no key, no cost, deterministic.
- **All data under `.mem0-data/`** (gitignored). It is a derived cache; `wiki/` is the source of
  truth and the store rebuilds from it.

## Config

`config.py` reads env overrides: `WIKI_MEM0_DATA` (store dir), `WIKI_MEM0_EMBED_MODEL` /
`WIKI_MEM0_EMBED_DIMS` (swap embedder — keep dims in sync), `WIKI_MEM0_LLM_MODEL`,
`ANTHROPIC_API_KEY` (enables hot-recall inference).

## Reverting

The pre-mem0 project is on the `pre-mem0` branch. To regress: `git checkout pre-mem0`
(or `git reset --hard pre-mem0`), then delete `.mem0-data/`.
