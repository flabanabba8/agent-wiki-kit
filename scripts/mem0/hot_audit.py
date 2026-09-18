#!/usr/bin/env python
"""Audit the hot-recall store — enforce the 'don't let durable facts rot in hot' discipline.

Hot-recall (reason 2) is for EPHEMERAL cross-session scratch facts ("mid-refactor on X",
"user prefers Y"). Durable knowledge belongs in wiki/ pages, not here. Over time, keepers
silently accumulate in hot and never get promoted (anti-evaporation failure). This lists
entries oldest-first and flags anything older than --days so you can, per entry:
  * promote it into a wiki/ page (then delete from hot), or
  * delete it if it's spent.

Read-only by default; pass --purge to delete the flagged-stale entries after you've promoted
the keepers. No API key needed (get_all doesn't call the LLM).

  scripts/mem0/hot_audit.py              # list + flag stale (>14d)
  scripts/mem0/hot_audit.py --days 7     # stricter staleness window
  scripts/mem0/hot_audit.py --purge      # delete the stale-flagged entries
"""
import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import get_memory, store_lock, close_memory  # noqa: E402

USER_ID = "hot"


def age_days(ts):
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    except (ValueError, TypeError):
        return None


def get_all(mem):
    # mem0 2.x: scope goes through filters=, not a top-level user_id kwarg (same convention
    # as search() in mcp_server.py / query_wiki.py). Fall back for older signatures.
    try:
        res = mem.get_all(filters={"user_id": USER_ID})
    except (TypeError, ValueError):
        res = mem.get_all()
    if isinstance(res, dict):
        return res.get("results", []) or []
    return res or []


def _main_locked():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14, help="flag entries older than this (default 14)")
    ap.add_argument("--purge", action="store_true", help="delete the stale-flagged entries")
    args = ap.parse_args()

    mem = get_memory(USER_ID)
    import atexit; atexit.register(close_memory, mem)
    items = get_all(mem)
    if not items:
        print("hot-recall is empty — nothing to audit.")
        return

    rows = []
    for m in items:
        rows.append((age_days(m.get("created_at")), m.get("memory", ""), m.get("id", "")))
    # oldest first; unknown-age sorts last
    rows.sort(key=lambda r: (r[0] is None, -(r[0] or 0)))

    stale = [r for r in rows if r[0] is not None and r[0] >= args.days]
    print(f"{len(items)} hot entr{'y' if len(items) == 1 else 'ies'}; "
          f"{len(stale)} older than {args.days}d\n")
    for age, text, _ in rows:
        a = f"{age}d" if age is not None else "  ?"
        flag = "  <- PROMOTE or DELETE" if (age is not None and age >= args.days) else ""
        print(f"  [{a:>4}] {text[:88]}{flag}")

    if stale:
        print(f"\n{len(stale)} stale. Promote durable ones into wiki/ pages first, then "
              f"`hot_audit.py --purge` to clear them.")
        if args.purge:
            for _, _, mid in stale:
                if mid:
                    try:
                        mem.delete(memory_id=mid)
                    except Exception:
                        pass
            print(f"Purged {len(stale)} stale entr{'y' if len(stale) == 1 else 'ies'}.")


def main():
    # Hold the turnstile for the whole run: other agents wait instead of crashing on Qdrant's lock.
    with store_lock(USER_ID):
        return _main_locked()

if __name__ == "__main__":
    main()
