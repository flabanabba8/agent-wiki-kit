#!/usr/bin/env python
"""Camoufox MCP server: two tools, backed by the official camoufox Python library.

Wired in the project .mcp.json as `camoufox`. Approve it the first time you run `claude`
in this repo. Uses the same .venv as the mem0 layer (mcp<2 for FastMCP).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    sys.exit("mcp (<2) not installed in this venv. Run scripts/mem0/setup.sh")

try:
    from browse import DEFAULT_MAX_CHARS, fetch
except ImportError as e:
    sys.exit(f"camoufox not installed ({e}). Run: uv pip install --python .venv/bin/python 'camoufox[geoip]' && .venv/bin/python -m camoufox fetch")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
mcp = FastMCP("camoufox")


@mcp.tool()
async def fetch_page(url: str, wait_until: str = "domcontentloaded", max_chars: int = DEFAULT_MAX_CHARS,
                     include_links: bool = False) -> dict:
    """Load a URL in the Camoufox stealth Firefox and return its title, final URL, HTTP status and
    visible text. Use when WebFetch returns 403, an empty page, a JavaScript shell, or only a
    summary. wait_until: domcontentloaded (default), load, or networkidle for JS-heavy pages."""
    return await fetch(url, wait_until=wait_until, max_chars=max_chars, include_links=include_links)


@mcp.tool()
async def screenshot_page(url: str, full_page: bool = True, filename: str = "") -> dict:
    """Load a URL in Camoufox and save a PNG screenshot under outputs/screenshots/. Returns the
    absolute path (read it with the Read tool to see the image) plus title and status."""
    name = filename or "camoufox-" + "".join(c if c.isalnum() else "-" for c in url.split("//")[-1])[:80] + ".png"
    path = os.path.join(REPO, "outputs", "screenshots", os.path.basename(name))
    r = await fetch(url, max_chars=2_000, screenshot_path=path, full_page=full_page)
    r.pop("text", None)
    return r


if __name__ == "__main__":
    mcp.run()
