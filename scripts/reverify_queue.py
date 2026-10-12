#!/usr/bin/env python3
"""reverify_queue.py - merge a freshly generated re-verification queue with earlier ones.

Why: weekly maintenance rewrote outputs/reverify-queue.md from scratch on a new branch each
week, so a mark you had set (`[~]` reviewing, `[-]` rejected) and every item you had not got to
yet vanished with the previous, unmerged branch. This keeps both.

Marks: `[ ]` pending, `[~]` reviewing, `[x]` done, `[-]` rejected.
Rules, per item (identified by its text after the mark):
  - in the new queue and marked `[~]` or `[-]` earlier: the mark is kept
  - in the new queue and marked `[x]` earlier: reset to `[ ]`, because the source changed again
  - not in the new queue, still `[ ]` or `[~]`: carried over, unless its page was verified on or
    after the week it was queued, or the file it names is already cited by a wiki page
  - `[x]` and `[-]` items that are no longer regenerated are dropped

  reverify_queue.py merge --new FILE [--old FILE ...] [--branches N] [--out FILE]

--branches N also reads outputs/reverify-queue.md from the newest N local maintenance/* branches.
Standard library only.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

ITEM = re.compile(r"^- \[([ ~x-])\] (.+)$")
HEADER_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
PAGE = re.compile(r"^`(wiki/[^`]+\.md)`")
FILE = re.compile(r"`(raw/[^`]+)`")
FM_VERIFIED = re.compile(r"(?m)^last_verified:\s*(\d{4}-\d{2}-\d{2})")


def parse(text):
    """Return (date or None, header lines, [(mark, text), ...])."""
    lines = text.splitlines()
    date = None
    for line in lines:
        m = HEADER_DATE.search(line)
        if m and line.startswith("#"):
            date = m.group(1)
            break
    header, items = [], []
    for line in lines:
        m = ITEM.match(line)
        if m:
            items.append((m.group(1), m.group(2)))
        elif not items and not line.startswith("## Carried over"):
            header.append(line)
    return date, header, items


def page_verified(path):
    try:
        with open(path, encoding="utf-8") as f:
            head = f.read(3000)
    except OSError:
        return None
    m = FM_VERIFIED.search(head)
    return m.group(1) if m else None


def cited_anywhere(raw_path, wiki_text):
    return raw_path in wiki_text


def resolved(text, queued_on, wiki_text, verified=page_verified):
    """True when an unfinished item no longer needs doing."""
    m = PAGE.match(text)
    if m:
        if not os.path.exists(m.group(1)):
            return True
        v = verified(m.group(1))
        return bool(queued_on and v and v >= queued_on)
    if text.startswith("ingest "):
        f = FILE.search(text)
        return bool(f and cited_anywhere(f.group(1), wiki_text))
    return False


def merge(new_text, olds, wiki_text="", verified=page_verified):
    """olds: [(queue text)] newest first. Returns the merged queue text."""
    new_date, header, new_items = parse(new_text)
    parsed_olds = [parse(t) for t in olds]
    out_items = []
    seen = set()
    for mark, text in new_items:
        seen.add(text)
        keep = " "
        for _, _, items in parsed_olds:
            old = dict((t, m) for m, t in items).get(text)
            if old in ("~", "-"):
                keep = old
                break
            if old is not None:
                break
        out_items.append((keep, text))
    carried = []
    for date, _, items in parsed_olds:
        for mark, text in items:
            if text in seen or mark not in (" ", "~"):
                continue
            if resolved(text, date, wiki_text, verified):
                continue
            seen.add(text)
            carried.append((mark, text))
    lines = [l for l in header]
    while lines and not lines[-1].strip():
        lines.pop()
    lines.append("")
    for mark, text in out_items:
        lines.append(f"- [{mark}] {text}")
    if carried:
        lines += ["", "## Carried over from earlier weeks", ""]
        lines += [f"- [{mark}] {text}" for mark, text in carried]
    return "\n".join(lines).rstrip("\n") + "\n"


def branch_queues(count):
    ref = subprocess.run(
        ["git", "for-each-ref", "--sort=-refname", f"--count={count}",
         "--format=%(refname:short)", "refs/heads/maintenance/"],
        capture_output=True, text=True).stdout.split()
    out = []
    for r in ref:
        shown = subprocess.run(["git", "show", f"{r}:outputs/reverify-queue.md"],
                               capture_output=True, text=True)
        if shown.returncode == 0:
            out.append(shown.stdout)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--new", required=True)
    m.add_argument("--old", action="append", default=[])
    m.add_argument("--branches", type=int, default=0)
    m.add_argument("--out")
    args = ap.parse_args(argv)
    new_text = open(args.new, encoding="utf-8").read()
    olds = [open(p, encoding="utf-8").read() for p in args.old if os.path.exists(p)]
    if args.branches:
        olds += branch_queues(args.branches)
    wiki_text = ""
    for p in glob.glob("wiki/*/*.md"):
        with open(p, encoding="utf-8") as f:
            wiki_text += f.read()
    merged = merge(new_text, olds, wiki_text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(merged)
    else:
        sys.stdout.write(merged)
    return 0


if __name__ == "__main__":
    sys.exit(main())
