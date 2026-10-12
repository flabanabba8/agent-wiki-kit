#!/usr/bin/env python3
"""near-duplicates.py - find wiki pages that probably restate each other.

Why: "one home per fact" erodes when a page is rewritten under a new name instead of updated.
Two signals, both over the page body without frontmatter, code fences or links:
  - overlap: Jaccard similarity of word 6-grams (shared sentences, not shared topic words)
  - title:   the same normalized title, or one title/alias equal to the other page's slug
Pages are reported when overlap >= --threshold (default 0.25) or the title signal fires.

  near-duplicates.py             print pairs, most similar first; exit 0
  near-duplicates.py --count     print only how many pairs
  near-duplicates.py --fail-over N   exit 1 when more than N pairs are found
Standard library only.
"""
import os
import re
import subprocess
import sys

N = 6


def root():
    return subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or os.getcwd()


def load(path):
    text = open(path, encoding="utf-8").read()
    fm, body = {}, text
    m = re.match(r"(?s)---\n(.*?)\n---\n(.*)", text)
    if m:
        for line in m.group(1).split("\n"):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
        body = m.group(2)
    body = re.sub(r"(?s)```.*?```", " ", body)
    body = re.sub(r"\[\[([^\]|]+)(\|[^\]]+)?\]\]", r"\1", body)
    body = re.sub(r"[`*_>#|\-]", " ", body.lower())
    words = re.findall(r"[a-z0-9][a-z0-9.']+", body)
    return fm, words


def shingles(words):
    return {" ".join(words[i:i + N]) for i in range(len(words) - N + 1)}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def aliases(fm):
    raw = fm.get("aliases", "").strip("[]")
    return {norm(a) for a in raw.split(",") if a.strip()}


def find(base, threshold=0.25):
    pages = {}
    wiki = os.path.join(base, "wiki")
    for folder in sorted(os.listdir(wiki)):
        d = os.path.join(wiki, folder)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".md"):
                fm, words = load(os.path.join(d, f))
                slug = f[:-3]
                pages[slug] = dict(fm=fm, sh=shingles(words), title=norm(fm.get("title", slug)),
                                   aliases=aliases(fm), folder=folder)
    out = []
    slugs = sorted(pages)
    for i, a in enumerate(slugs):
        for b in slugs[i + 1:]:
            pa, pb = pages[a], pages[b]
            union = len(pa["sh"] | pb["sh"])
            score = len(pa["sh"] & pb["sh"]) / union if union else 0.0
            title = (pa["title"] == pb["title"] or norm(a) in pb["aliases"] or norm(b) in pa["aliases"]
                     or norm(a) == pb["title"] or norm(b) == pa["title"])
            if score >= threshold or title:
                out.append((score, a, b, "same title or alias" if title else "shared sentences"))
    return sorted(out, reverse=True)


def main(argv):
    thr = float(argv[argv.index("--threshold") + 1]) if "--threshold" in argv else 0.25
    pairs = find(root(), thr)
    if "--count" in argv:
        print(len(pairs))
    else:
        for score, a, b, why in pairs:
            print(f"{score:.2f}  {a}  <->  {b}  ({why})")
        if not pairs:
            print("no near-duplicate pages")
    if "--fail-over" in argv and len(pairs) > int(argv[argv.index("--fail-over") + 1]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
