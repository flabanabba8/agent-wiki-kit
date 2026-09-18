---
title: Camoufox
type: entity
tldr: "Stealth Firefox; repo's WebFetch fallback"
sources:
  - raw/docs/camoufox/readme.md
  - raw/docs/camoufox/pythonlib-readme.md
  - raw/docs/camoufox/site-index.md
  - raw/docs/camoufox/site-python__installation.md
  - raw/docs/camoufox/site-python__usage.md
  - raw/docs/camoufox/site-python__virtual-display.md
  - raw/docs/camoufox/site-python__remote-server.md
  - raw/docs/camoufox/site-python__main-world-eval.md
  - raw/docs/camoufox/site-python__geoip.md
  - raw/docs/camoufox/site-features.md
  - raw/docs/camoufox/site-stealth.md
  - raw/docs/camoufox/site-community.md
  - raw/docs/camoufox/site-legal.md
  - scripts/camoufox/browse.py
  - scripts/camoufox/fetch.py
  - raw/docs/claude-tag/overview.md
  - scripts/camoufox/mcp_server.py
  - scripts/hooks/webfetch_camoufox_fallback.py
  - .mcp.json
  - .claude/settings.json
  - scripts/agents/shared.py
related: ["[[harness]]", "[[hooks]]", "[[mcp]]", "[[tools-reference]]", "[[chrome-and-computer-use]]"]
created: 2026-09-15
updated: 2026-09-17
confidence: high
last_verified: 2026-09-17
aliases: [camoufox-browser, stealth-firefox, webfetch-fallback, js-rendered-pages]
---

# Camoufox

Camoufox (`daijro/camoufox`, MPL-2.0) is an open-source anti-detect browser for web scraping and AI agents. It is a debloated Firefox fork that spoofs fingerprints at the C++ level instead of through injected JavaScript, and it is driven through Playwright. Several community projects named **Camofox** (`jo-inc/camofox-browser`, `redf0x1/camofox-browser`, `redf0x1/camofox-mcp`) are built on top of it, but they are different software. This repo uses Camoufox to read pages that Claude Code's `WebFetch` can't: JavaScript-rendered sites and bot-walled pages. For the WebFetch tool itself, see [[tools-reference]].

## What it does

- **Fingerprint injection and rotation:** navigator, screen and window, WebGL, fonts, voices, geolocation, timezone, locale, and WebRTC IP. [BrowserForge](https://github.com/daijro/browserforge) generates the values to match real-world device distributions.
- **Hidden automation:** Playwright's page agent runs in an isolated world, so pages can't see its injected JS. Firefox automation goes through Juggler, not CDP.
- **Built for automation:** human-like cursor movement (`humanize`), uBlock Origin, no CSS animations, and about 200 MB of memory.

The README warns that the project "may not be suitable for stable production use". Its stealth page says detection performance has dropped because of fingerprint inconsistencies and that the project is under active development. Camoufox's terms forbid, among other uses, accessing any service in a way that violates that service's terms without authorization.

## Install

```bash
pip install -U "camoufox[geoip]"   # geoip strongly recommended with proxies
python3 -m camoufox fetch          # downloads the browser (camoufox fetch on Windows)
```

Manage browser versions with the CLI: `camoufox sync`, `camoufox set official/stable` (the default channel), `camoufox active`, `camoufox list`, `camoufox path`, `camoufox version`, `camoufox test <url>` (opens the Playwright inspector) and `camoufox remove`.

## Python API

Existing Playwright code works once you swap the launcher:

```python
from camoufox.async_api import AsyncCamoufox

async with AsyncCamoufox(headless=True, block_images=True) as browser:
    page = await browser.new_page()
    await page.goto("https://example.com")
```

| Parameter | Use |
|---|---|
| `headless` | `True`, `False`, or `"virtual"` (Xvfb on Linux, recommended if headless mode gets detected) |
| `os`, `screen`, `fonts`, `locale` | Constrain the generated fingerprint |
| `geoip`, `proxy` | Match geolocation, timezone and locale to the proxy IP |
| `humanize` | `True`, or the maximum cursor-move time in seconds |
| `block_images`, `block_webrtc`, `block_webgl` | Toggles |
| `main_world_eval` | Allow `page.evaluate("mw:...")` to modify the DOM. The page can detect this |
| `persistent_context` + `user_data_dir` | Keep a profile between runs |
| `config` | Raw property overrides (advanced; Camoufox warns about leaks) |

`python -m camoufox server` runs Camoufox as a Playwright websocket server. A server uses a single browser instance, so fingerprints don't rotate between sessions.

## This repo's integration

All three entry points share `scripts/camoufox/browse.py`. Each call launches a fresh `AsyncCamoufox`, and therefore a fresh fingerprint, loads the URL, and returns `url`, `final_url`, `status`, `title`, `chars`, `truncated` and `text`, cut at 40,000 characters by default. `CAMOUFOX_HEADLESS` sets the default headless mode.

### 1. Fetch CLI (always available through Bash)

```bash
./.venv/bin/python scripts/camoufox/fetch.py https://example.com
./.venv/bin/python scripts/camoufox/fetch.py URL --links --max-chars 20000
./.venv/bin/python scripts/camoufox/fetch.py URL --screenshot outputs/shot.png
./.venv/bin/python scripts/camoufox/fetch.py URL --json --wait-until networkidle
./.venv/bin/python scripts/camoufox/fetch.py URL --headless virtual
```

Other flags are `--timeout-ms` (45000), `--settle-ms` (1500), `--html` and `--block-images`. `.claude/settings.json` pre-approves this command.

### 2. MCP server

`.mcp.json` declares `camoufox` as `./.venv/bin/python scripts/camoufox/mcp_server.py` using FastMCP from `mcp<2`. Approve it the first time you run `claude` in the repo. It provides two tools:

- `fetch_page(url, wait_until, max_chars, include_links)`
- `screenshot_page(url, full_page, filename)`, which saves a PNG under `outputs/screenshots/` and returns its path so you can open it with Read

For how project MCP servers load, see [[mcp]].

### 3. Automatic WebFetch fallback hook

The same fallback runs in OpenCode after its `webfetch` tool and in Hermes after `web_extract`, through adapters that call this script as `webfetch_camoufox_fallback.py --url URL --result-file FILE` and append the notice to the tool result. Codex has no page-fetch tool and its hosted web search bypasses hooks, so there the MCP server above is the route. See [[cross-agent-setup]].

`.claude/settings.json` runs `scripts/hooks/webfetch_camoufox_fallback.py` on both `PostToolUse` and `PostToolUseFailure` with matcher `WebFetch` and a 120 s timeout. For hook mechanics, see [[hooks]]. After every WebFetch it checks two independent signals:

1. **The WebFetch result:** it failed, or its summary matches a "strong" phrase such as "requires javascript", "access denied" or "no content". "Weak" words like `captcha` or `403` count only when the summary is under 600 characters.
2. **A quick raw fetch** of the same URL (8 s timeout): HTTP 401/403/406/429/451/503, a Cloudflare-style challenge marker, a `<noscript>` JavaScript-required notice, a script-heavy shell with under 400 visible characters, or an empty SPA mount point.

If either signal fires, the hook renders the page with `fetch.py --json --max-chars 200000 --settle-ms 2500 --wait-until load` and a 100 s limit. It saves the text to `outputs/webfetch-fallback/<timestamp>-<slug>.md`. The page text is **not** injected. `additionalContext` carries only a short notice with the saved file's path, telling Claude to open it with Read and to treat it as untrusted content. That way the text arrives as a tool result rather than a system reminder.

- **Still blocked:** if the render comes back with status ≥ 400 or under 50 characters, the domain is cached in `outputs/.webfetch-blocked.json` for **7 days**. Later WebFetches to that domain skip the render and say "Treat the page as unavailable; do not retry in a loop."
- **Logging:** every decision is logged to `outputs/.webfetch-fallback.log`.
- **Failure handling:** the hook always exits 0, so a broken fallback never breaks WebFetch.
- **Cleanup:** `scripts/doctor.sh` prunes renders older than 30 days and checks that the hook and MCP server are wired (see [[harness]]).

## When a render still isn't the source

A successful render is not always the content you want. Some documentation sites serve an application
shell to every browser, Camoufox included, and keep the prose in a separate source file. On
claude.com's documentation the fix is to append `.md` to the path: the HTML URL comes back as footer
chrome, and the same path with `.md` returns the full page text. Check a site for an `llms.txt` index
first, since it lists the fetchable paths. When a render returns a page that is technically fine but
carries no content, look for that variant before concluding the page is unavailable.
