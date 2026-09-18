#!/usr/bin/env python3
"""answer-eval.py — on-demand answer-quality eval: does Claude answer from the wiki correctly?

Retrieval eval checks the right page is FOUND; this checks the ANSWER. Each question in
evals/answer-eval.yaml lists pages the answer must cite and facts it must contain. Answers
come from `claude -p` on a non-Fable model with hooks disabled; grading is deterministic
(citations + required strings), so no judge model is spent.

Usage:
  ./.venv/bin/python scripts/answer-eval.py                # all questions (spends tokens)
  ./.venv/bin/python scripts/answer-eval.py --limit 2
  ./.venv/bin/python scripts/answer-eval.py --model sonnet
Writes outputs/answer-eval-<date>.json.
"""
import argparse, datetime, json, os, re, subprocess, sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPT = ("Answer this question about Claude Code using ONLY this repository's wiki (read wiki/index.md or run "
          "./.venv/bin/python scripts/mem0/query_wiki.py first). Cite the wiki pages you used as [[page-name]]. "
          "Be brief. Do not edit any files.\n\nQuestion: {q}")


def ask(q, model, timeout):
    cmd = ["claude", "-p", PROMPT.format(q=q), "--model", model, "--settings", json.dumps({"disableAllHooks": True}),
           "--allowedTools", "Read,Grep,Glob,Bash(./.venv/bin/python scripts/mem0/query_wiki.py:*)"]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="sonnet", help="never fable")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()
    if "fable" in a.model.lower():
        sys.exit("refusing to run the eval on a Fable model")
    spec = yaml.safe_load(open(os.path.join(ROOT, "evals", "answer-eval.yaml"), encoding="utf-8"))
    items = spec["questions"][: a.limit or None]
    rows, passed = [], 0
    for it in items:
        answer, rc = ask(it["q"], a.model, a.timeout)
        cited = set(re.findall(r"\[\[([a-z0-9-]+)", answer))
        cite_ok = bool(cited & set(it["must_cite"]))
        missing = [m for m in it["must_mention"] if m.lower() not in answer.lower()]
        ok = rc == 0 and cite_ok and not missing
        passed += ok
        rows.append({"q": it["q"], "ok": ok, "cited": sorted(cited), "cite_ok": cite_ok, "missing": missing, "answer": answer[:2000]})
        print(f"{'PASS' if ok else 'FAIL'}  {it['q'][:70]}" + ("" if ok else f"   cite_ok={cite_ok} missing={missing}"))
    out = {"date": datetime.date.today().isoformat(), "model": a.model, "passed": passed, "n": len(items), "rows": rows}
    path = os.path.join(ROOT, "outputs", f"answer-eval-{out['date']}.json")
    json.dump(out, open(path, "w"), indent=2)
    print(f"answer-eval: {passed}/{len(items)} passed -> {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
