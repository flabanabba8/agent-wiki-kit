#!/usr/bin/env python
"""Fetch a page with Camoufox from the shell — the Bash-callable path Claude can always use,
even in a session where the MCP server isn't approved or loaded.

Usage:
  ./.venv/bin/python scripts/camoufox/fetch.py https://example.com
  ./.venv/bin/python scripts/camoufox/fetch.py URL --links --max-chars 20000
  ./.venv/bin/python scripts/camoufox/fetch.py URL --screenshot outputs/shot.png
  ./.venv/bin/python scripts/camoufox/fetch.py URL --json            # machine-readable
  ./.venv/bin/python scripts/camoufox/fetch.py URL --headless virtual  # Xvfb, if headless leaks

Prefer WebFetch first; use this when WebFetch returns 403, an empty page, a JS shell,
or a summary when you need the full text (see wiki/ecosystem/camoufox.md).
"""
import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browse import DEFAULT_MAX_CHARS, fetch  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--wait-until", default="domcontentloaded", choices=["load", "domcontentloaded", "networkidle", "commit"])
    ap.add_argument("--timeout-ms", type=int, default=45_000)
    ap.add_argument("--settle-ms", type=int, default=1_500)
    ap.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    ap.add_argument("--links", action="store_true", help="include up to 300 links")
    ap.add_argument("--html", action="store_true", help="include page HTML (truncated to --max-chars)")
    ap.add_argument("--screenshot", metavar="PATH")
    ap.add_argument("--headless", default=None, help="true | false | virtual (default: $CAMOUFOX_HEADLESS or true)")
    ap.add_argument("--block-images", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    try:
        r = asyncio.run(fetch(
            a.url, wait_until=a.wait_until, timeout_ms=a.timeout_ms, settle_ms=a.settle_ms,
            max_chars=a.max_chars, include_links=a.links, include_html=a.html,
            screenshot_path=a.screenshot, headless=a.headless, block_images=a.block_images,
        ))
    except Exception as e:  # surface a one-line reason instead of a Playwright stack
        print(f"camoufox fetch failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    if a.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0
    print(f"# {r['title']}\n")
    print(f"status: {r['status']}  final_url: {r['final_url']}  chars: {r['chars']}{' (truncated)' if r['truncated'] else ''}")
    if r.get("screenshot"):
        print(f"screenshot: {r['screenshot']}")
    print()
    print(r["text"])
    if r.get("links"):
        print("\n## Links")
        for l in r["links"]:
            print(f"- [{l['text'] or l['href']}]({l['href']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
