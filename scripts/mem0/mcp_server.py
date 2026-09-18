#!/usr/bin/env python
"""mem0 hot-recall MCP server (reason 2): ephemeral cross-session scratch memory.

Distinct from the wiki. This holds transient session facts ("mid-refactor on X",
"user prefers Y") that don't deserve a curated wiki page. Durable, citable knowledge
still belongs in wiki/. Exposes two tools over stdio: remember, recall.

Fact-extraction (infer=True) runs only when ANTHROPIC_API_KEY is set; otherwise notes
are stored verbatim. Uses the isolated "hot" store so it never locks the wiki index, and opens
that store per call so Claude Code, Codex, OpenCode and Hermes can all run this server at once.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Store, StoreBusy  # noqa: E402

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    sys.exit("mcp package not installed. Run scripts/mem0/setup.sh")

USER_ID = "hot"
INFER = bool(os.environ.get("ANTHROPIC_API_KEY"))

mcp = FastMCP("mem0-hot")
# Opened per call and released again, so several agents can run this server at the same time.
_store = Store(USER_ID)
BUSY = "Scratch memory is busy (another agent is using it). Try again in a moment."


@mcp.tool()
def remember(text: str) -> str:
    """Store an ephemeral fact/note for recall in later sessions (scratch memory, not the wiki)."""
    try:
        with _store.session(wait=30) as m:
            res = m.add(text, user_id=USER_ID, infer=INFER)
    except StoreBusy:
        return BUSY
    n = len(res.get("results") or []) if isinstance(res, dict) else 0
    return f"Stored ({n} memory item(s))."


@mcp.tool()
def recall(query: str, k: int = 5) -> str:
    """Search ephemeral scratch memory for facts relevant to the query."""
    try:
        with _store.session(wait=30) as m:
            res = m.search(query, filters={"user_id": USER_ID}, top_k=k)  # 2.x: top_k, not limit
    except StoreBusy:
        return BUSY
    items = (res.get("results") if isinstance(res, dict) else res) or []
    if not items:
        return "No relevant memories."
    return "\n".join(f"- {i.get('memory', '')}" for i in items)


if __name__ == "__main__":
    mcp.run()
