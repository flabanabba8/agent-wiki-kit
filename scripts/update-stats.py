#!/usr/bin/env python3
"""update-stats.py — regenerate every hand-maintained count from the repo itself.

Why: counts in README and wiki/hot.md drift as soon as they are edited by hand. This computes them and rewrites the known spots.

Usage: ./scripts/update-stats.py            # rewrite files, print a summary
       ./scripts/update-stats.py --check    # exit 1 if any file would change (for CI)
"""
import glob, json, os, re, subprocess, sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or os.getcwd()
os.chdir(ROOT)
CHECK = "--check" in sys.argv
DIRS = ["start", "using", "extending", "automation", "surfaces", "deployment", "reference", "sdk-and-api", "research", "ecosystem", "project"]


def lint_json():
    out = subprocess.run(["./scripts/wiki-lint.sh", "--json"], capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {}


def gather():
    pages = {d: len(glob.glob(f"wiki/{d}/*.md")) for d in DIRS}
    texts = [open(p, encoding="utf-8").read() for p in glob.glob("wiki/*/*.md")]
    links = [m for t in texts for m in re.findall(r"\[\[([^\]|#]+)", t)]
    lj = lint_json()
    manifest = [l.split("\t")[0] for l in open("sources/manifest.tsv", encoding="utf-8") if l.strip() and not l.startswith("#")] if os.path.exists("sources/manifest.tsv") else []
    evals = sorted(glob.glob("outputs/eval-*.json"))
    ev = json.load(open(evals[-1])) if evals else {}
    return {
        "pages": pages, "total": sum(pages.values()),
        "words": sum(len(t.split()) for t in texts),
        "links": len(links), "unique_links": len(set(l.strip() for l in links)),
        # raw/ is not distributed, so count the sources the manifest lists rather than what is on disk.
        "raw": len(manifest) or sum(1 for p in glob.glob("raw/**/*", recursive=True) if os.path.isfile(p)),
        "official": sum(1 for r in manifest if r.startswith("raw/docs/official/") and r.endswith(".md")) or len(glob.glob("raw/docs/official/*.md")),
        "skills": len([d for d in glob.glob(".claude/skills/*/") if os.path.exists(d + "SKILL.md")]),
        "agents": len(glob.glob(".claude/agents/*.md")),
        "checks": lj.get("checks") or len(re.findall(r"^# *Check \d+|^# \d+\. ", open("scripts/wiki-lint.sh").read(), re.M)) or None,
        "health": lj.get("health_score"),
        "eval": (ev.get("hits"), ev.get("n"), ev.get("mrr")),
    }


def sub(text, pattern, repl, flags=re.M):
    new, n = re.subn(pattern, repl, text, flags=flags)
    return new


def rewrite(path, fn, st):
    if not os.path.exists(path):
        return False
    old = open(path, encoding="utf-8").read()
    new = fn(old, st)
    if new != old and not CHECK:
        open(path, "w", encoding="utf-8").write(new)
    return new != old


def fmt(n):
    return f"{n:,}"


def readme(t, st):
    p = st["pages"]
    t = sub(t, r"\*\*\d[\d,]* wiki pages\*\*", f"**{st['total']} wiki pages**")
    t = sub(t, r"\*\*[\d,]+\+? wikilinks\*\*", f"**{fmt(st['links'] // 100 * 100)}+ wikilinks**")
    t = sub(t, r"\*\*\d[\d,]* raw source files\*\*", f"**{st['raw']} raw source files**")
    t = sub(t, r"full \d+-page snapshot", f"full {st['official']}-page snapshot")
    labels = {"Start": "start", "Using": "using", "Extending": "extending", "Automation": "automation", "Surfaces": "surfaces",
              "Deployment": "deployment", "Reference": "reference", "SDK & API": "sdk-and-api", "Research": "research",
              "Ecosystem": "ecosystem", "Project": "project"}
    for label, key in labels.items():
        t = sub(t, rf"^(\| \*\*{re.escape(label)}\*\* \| )\d+( \|)", rf"\g<1>{p[key]}\g<2>")
    t = sub(t, r"(official/ \()\d+( code\.claude\.com pages\))", rf"\g<1>{st['official']}\g<2>")
    rows = {"Wiki pages": str(st["total"]), "Words": f"{fmt(st['words'] // 1000 * 1000)}+",
            "Wikilinks": f"{fmt(st['links'])} ({st['unique_links']} unique)", "Raw sources": f"{st['raw']} files",
            "Official doc pages snapshotted": str(st["official"]), "Skills": str(st["skills"]), "Agents": str(st["agents"])}
    if st["health"] is not None:
        rows["Health score"] = f"{st['health']}/100"
    if st["eval"][0] is not None:
        rows["Retrieval eval"] = f"{st['eval'][0]}/{st['eval'][1]} hit@5, MRR {st['eval'][2]:.2f}"
    for k, v in rows.items():
        t = sub(t, rf"^\| {re.escape(k)} \| [^|\n]+ \|$", f"| {k} | {v} |")
    return t


def wiki_stats(t, st):
    rows = {"Wiki pages": str(st["total"]), "Words": f"{fmt(st['words'] // 1000 * 1000)}+",
            "Wikilinks": f"{fmt(st['links'])} ({st['unique_links']} unique)", "Raw source files": str(st["raw"])}
    for k, v in rows.items():
        t = sub(t, rf"^\| {re.escape(k)} \| [^|\n]+ \|$", f"| {k} | {v} |")
    return t


def hot(t, st):
    p = st["pages"]
    line = f"- **{st['total']} pages**: " + ", ".join(f"{k} ({v})" for k, v in p.items())
    t = sub(t, r"^- \*\*\d+ pages\*\*:.*$", line)
    t = sub(t, r"^- \*\*~[\d.]+K words\*\*, [\d,]+ wikilinks \(\d+ unique\), \d+ raw files",
            f"- **~{st['words'] // 1000}K words**, {fmt(st['links'])} wikilinks ({st['unique_links']} unique), {st['raw']} raw files")
    return t


def main():
    st = gather()
    changed = [p for p, fn in (("README.md", readme), ("wiki/hot.md", hot)) if rewrite(p, fn, st)]
    print(json.dumps({k: v for k, v in st.items()}, default=str))
    print(("would change: " if CHECK else "updated: ") + (", ".join(changed) or "nothing"))
    return 1 if (CHECK and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
