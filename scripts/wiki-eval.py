#!/usr/bin/env python
"""wiki-eval.py — retrieval capability eval over the mem0 wiki index.

Runs every question in evals/wiki-eval.yaml through the same semantic search that
`query_wiki.py` uses, and checks whether an expected page appears in the top-k.
Reports hit@k and MRR; writes outputs/eval-<date>.json for `--diff`-style tracking.

Usage:
  ./.venv/bin/python scripts/wiki-eval.py            # table + summary
  ./.venv/bin/python scripts/wiki-eval.py --json     # machine-readable
  ./.venv/bin/python scripts/wiki-eval.py --ci 0.8   # exit 1 if hit rate < 0.8
Requires: scripts/mem0/setup.sh + index_wiki.py (see scripts/doctor.sh).
"""
import argparse, datetime as dt, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "mem0"))
import yaml  # noqa: E402  (PyYAML ships with the mem0 venv)
from config import get_memory, store_lock, close_memory  # noqa: E402
from page_status import demote_deprecated  # noqa: E402

USER_ID = "wiki"


def search_pages(mem, q, k):
    res = mem.search(q, filters={"user_id": USER_ID}, top_k=max(k * 8, 24))
    results = res.get("results") if isinstance(res, dict) else res
    paths = []
    for r in results or []:
        p = (r.get("metadata") or {}).get("path", "")
        if p and p not in paths:
            paths.append(p)
    # Rank exactly like query_wiki.py: deprecated pages sort below current ones.
    return [os.path.splitext(os.path.basename(p))[0] for p in demote_deprecated(paths)[:k]]


def _main_locked():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ci", type=float, default=None, help="fail if hit rate below this")
    ap.add_argument("--file", default=os.path.join(ROOT, "evals", "wiki-eval.yaml"))
    a = ap.parse_args()

    spec = yaml.safe_load(open(a.file, encoding="utf-8"))
    k = int(spec.get("k", 5))
    existing = {os.path.splitext(f)[0] for d, _, fs in os.walk(os.path.join(ROOT, "wiki")) for f in fs if f.endswith(".md")}
    mem = get_memory(USER_ID)
    import atexit; atexit.register(close_memory, mem)

    rows, hits, rr_sum, n = [], 0, 0.0, 0
    hard_n = hard_hits = 0
    for item in spec["questions"]:
        if item.get("skip"):
            continue
        expect = [e for e in item["expect"] if e in existing]
        missing = [e for e in item["expect"] if e not in existing]
        got = search_pages(mem, item["q"], k)
        rank = next((i + 1 for i, p in enumerate(got) if p in expect), None)
        if item.get("top1") and rank != 1:
            rank = None  # top1 questions must put an expected page first
        n += 1
        if rank:
            hits += 1
            rr_sum += 1.0 / rank
        if item.get("hard"):
            hard_n += 1
            hard_hits += bool(rank)
        rows.append(dict(q=item["q"], expect=expect, missing_pages=missing, got=got, rank=rank, hard=bool(item.get("hard")), top1=bool(item.get("top1"))))

    hit_rate = hits / n if n else 0.0
    mrr = rr_sum / n if n else 0.0
    report = dict(date=dt.date.today().isoformat(), k=k, n=n, hits=hits, hit_rate=round(hit_rate, 3), mrr=round(mrr, 3),
                  hard_n=hard_n, hard_hits=hard_hits, hard_hit_rate=round(hard_hits / hard_n, 3) if hard_n else None, rows=rows)
    os.makedirs(os.path.join(ROOT, "outputs"), exist_ok=True)
    out = os.path.join(ROOT, "outputs", f"eval-{report['date']}.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)

    if a.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"wiki-eval — {report['date']} — hit@{k} {hits}/{n} = {hit_rate:.0%}, MRR {mrr:.2f}"
              + (f" | hard subset {hard_hits}/{hard_n}" if hard_n else ""))
        for r in rows:
            mark = f"ok  #{r['rank']}" if r["rank"] else "MISS   "
            print(f"  {mark}  {r['q'][:70]}")
            if not r["rank"]:
                print(f"           expected {r['expect']}  got {r['got']}")
            if r["missing_pages"]:
                print(f"           (expected pages not in wiki yet: {r['missing_pages']})")
        print(f"saved {os.path.relpath(out, ROOT)}")

    if a.ci is not None and hit_rate < a.ci:
        return 1
    return 0


def main():
    # Hold the turnstile for the whole run: other agents wait instead of crashing on Qdrant's lock.
    with store_lock(USER_ID):
        return _main_locked()

if __name__ == "__main__":
    sys.exit(main())
