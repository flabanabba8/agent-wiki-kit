"""Shared Camoufox page fetcher for the CLI (fetch.py) and the MCP server (mcp_server.py).

Why a local wrapper instead of a community MCP server: it uses only the official
`camoufox` Python library (daijro/camoufox, MPL-2.0), exposes two tools instead of
dozens, and lives in the repo where it can be read and tested.

Each call launches a fresh Camoufox instance (fresh fingerprint, no shared state) and
closes it afterwards. That costs a few seconds per call but keeps runs isolated.
"""
from __future__ import annotations

import os
from typing import Any

from camoufox.async_api import AsyncCamoufox

DEFAULT_MAX_CHARS = 40_000


def _headless_mode(value: str | bool | None) -> Any:
    """'true' → True, 'false' → False, 'virtual' → 'virtual' (Xvfb). Default: CAMOUFOX_HEADLESS or True."""
    if value is None:
        value = os.environ.get("CAMOUFOX_HEADLESS", "true")
    if isinstance(value, bool):
        return value
    v = str(value).strip().lower()
    if v == "virtual":
        return "virtual"
    return v not in ("false", "0", "no")


async def fetch(
    url: str,
    *,
    wait_until: str = "domcontentloaded",
    timeout_ms: int = 45_000,
    settle_ms: int = 1_500,
    max_chars: int = DEFAULT_MAX_CHARS,
    include_links: bool = False,
    include_html: bool = False,
    screenshot_path: str | None = None,
    full_page: bool = True,
    headless: str | bool | None = None,
    block_images: bool = False,
) -> dict:
    """Load `url` in Camoufox and return title, final URL, HTTP status and visible text."""
    async with AsyncCamoufox(headless=_headless_mode(headless), block_images=block_images) as browser:
        page = await browser.new_page()
        response = await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        if settle_ms:
            await page.wait_for_timeout(settle_ms)  # let late JS render before reading
        text = await page.inner_text("body") if await page.query_selector("body") else ""
        result: dict = {
            "url": url,
            "final_url": page.url,
            "status": response.status if response else None,
            "title": await page.title(),
            "chars": len(text),
            "truncated": len(text) > max_chars,
            "text": text[:max_chars],
        }
        if include_links:
            result["links"] = await page.eval_on_selector_all(
                "a[href]", "els => els.slice(0, 300).map(e => ({text: e.innerText.trim().slice(0, 120), href: e.href}))"
            )
        if include_html:
            html = await page.content()
            result["html"] = html[:max_chars]
        if screenshot_path:
            os.makedirs(os.path.dirname(os.path.abspath(screenshot_path)), exist_ok=True)
            await page.screenshot(path=screenshot_path, full_page=full_page)
            result["screenshot"] = os.path.abspath(screenshot_path)
        return result
