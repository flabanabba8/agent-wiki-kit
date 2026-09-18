#!/usr/bin/env python3
"""eval-harvest.py — turn real wiki queries into retrieval-eval questions.

Why: an eval written by the same agent that wrote the pages sits at 100% and can't catch
regressions. Real queries (logged by query_wiki.py to outputs/.query-log.jsonl) are harder.

Usage:
  scripts/eval-harvest.py                          # list logged queries not yet in the eval, with top results
  scripts/eval-harvest.py --add "query" page [page ...]   # append a labelled question to evals/wiki-eval.yaml
"""
import json, os, subprocess, sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or os.getcwd()
LOG = os.path.join(ROOT, "outputs", ".query-log.jsonl")
EVAL = os.path.join(ROOT, "evals", "wiki-eval.yaml")


def existing_questions():
    return {l.split('q:', 1)[1].strip().strip('"').lower() for l in open(EVAL, encoding="utf-8") if l.strip().startswith("- q:")}


def main():
    if len(sys.argv) >= 4 and sys.argv[1] == "--add":
        q, pages = sys.argv[2], sys.argv[3:]
        missing = [p for p in pages if not any(os.path.exists(os.path.join(ROOT, "wiki", d, p + ".md")) for d in os.listdir(os.path.join(ROOT, "wiki")) if os.path.isdir(os.path.join(ROOT, "wiki", d)))]
        if missing:
            sys.exit(f"unknown page(s): {missing}")
        with open(EVAL, "a", encoding="utf-8") as f:
            f.write(f'  - q: {json.dumps(q)}\n    expect: [{", ".join(pages)}]\n    source: harvested\n')
        print(f"added: {q} -> {pages}")
        return 0
    seen, have = set(), existing_questions()
    if not os.path.exists(LOG):
        print("no queries logged yet (outputs/.query-log.jsonl)")
        return 0
    for line in open(LOG, encoding="utf-8"):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        q = e["query"].strip()
        if q.lower() in have or q.lower() in seen:
            continue
        seen.add(q.lower())
        print(f"- {q!r}\n    top: {', '.join(e.get('top', [])[:3])}")
    print("\nLabel a question with: scripts/eval-harvest.py --add \"query\" expected-page [expected-page ...]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
