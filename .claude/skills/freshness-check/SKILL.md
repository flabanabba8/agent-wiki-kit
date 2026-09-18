---
name: freshness-check
description: Check whether wiki pages are behind their sources and work the re-verification queue. Use when the user asks if the wiki is up to date, or after weekly maintenance ran.
user-invocable: true
---

# Freshness check

1. **Queue first:** read `outputs/reverify-queue.md` (written by the weekly cron job on branch `maintenance/<date>`). For each unticked page, re-check its claims against the changed source, fix the page, tick it, then merge the maintenance branch.
2. **Classify:** `./scripts/freshness.py` sorts pages past 90 days into `frozen` (sources unchanged: `--bump` is honest), `drifted` (a cited raw file differs from the snapshot in `sources/manifest.tsv`: re-verify), `snapshot` (cites a docs snapshot older than 90 days: `./scripts/refetch-docs.sh` first) and `unfetched` (the source is not on disk: `./scripts/sources.py fetch`). After re-verifying a page, record the new state with `./scripts/sources.py manifest --accept <raw files>`, or the page stays `drifted`.
3. **New releases:** `./scripts/changelog-delta.sh`, then ingest the saved file into the owning pages and [[whats-new]].
4. **Expiry:** `./scripts/wiki-temporal.sh` lists pages past `valid_until`.
5. **Log** a line in `wiki/log.md` and a `🔄` line in `wiki/hot.md`.
