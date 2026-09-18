#!/usr/bin/env python
"""Semantic search over the wiki index (reason 1). Prints candidate pages to Read next.

Usage: scripts/mem0/query_wiki.py "how does context compaction work" [-k 6]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import open_memory  # noqa: E402
from page_status import demote_deprecated, is_deprecated  # noqa: E402

USER_ID = "wiki"


def _log_query(query, ranked):
    """Append every query and its top pages to outputs/.query-log.jsonl (gitignored).
    scripts/eval-harvest.py turns real queries into eval questions."""
    import datetime, json
    try:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(root, "outputs", ".query-log.jsonl")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "query": query,
                                "top": [os.path.splitext(os.path.basename(p))[0] for p in ranked]}) + "\n")
    except OSError:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("-k", type=int, default=6)
    args = ap.parse_args()

    # mem0 2.0+: scope is passed via filters=, not a top-level user_id kwarg, and the
    # result-count arg is top_k (NOT limit — 2.x renamed it; limit silently no-ops).
    # Pages are chunked, so over-fetch chunks then dedup to the top-k distinct pages.
    with open_memory(USER_ID) as mem:  # released straight after the search so other agents can query
        res = mem.search(args.query, filters={"user_id": USER_ID}, top_k=max(args.k * 8, 24))
    results = res.get("results") if isinstance(res, dict) else res
    if not results:
        print("No matches. Build the index first: scripts/mem0/index_wiki.py")
        return

    print(f"Top {args.k} pages for: {args.query!r}\n")
    best = {}  # path -> best-scoring chunk (results arrive in score order)
    for r in results:
        path = (r.get("metadata") or {}).get("path", "?")
        best.setdefault(path, r)
    ranked = demote_deprecated(list(best))[: args.k]
    _log_query(args.query, ranked)
    seen = set()
    for path in ranked:
        r = best[path]
        meta = r.get("metadata") or {}
        seen.add(path)
        score = r.get("score")
        score_s = f"{score:.3f}" if isinstance(score, (int, float)) else "n/a"
        typ = meta.get("type", "")
        tag = (f"[{typ}] " if typ else "") + ("[deprecated] " if is_deprecated(path) else "")
        print(f"{len(seen)}. {tag}{path}  (score {score_s})")
        print(f"   {meta.get('title', '')} — {meta.get('tldr', '')}")
        section = meta.get("section")
        if section:
            print(f"   § matched in: {section}")
        related = meta.get("related") or []
        if related:
            shown = ", ".join(related[:5]) + (" …" if len(related) > 5 else "")
            print(f"   → related: {shown}")


if __name__ == "__main__":
    main()
