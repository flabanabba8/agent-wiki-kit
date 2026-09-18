#!/usr/bin/env python3
"""freshness.py — mechanical half of the freshness workflow (no LLM, no deps).

Why: `last_verified` decays on a calendar, but pages only actually go stale when
their SOURCE changes (a frozen article never drifts) or when the product moves past a
scraped doc (raw/docs/*.md is a snapshot). Treating both the same either lies (blind
bumps) or wastes review time (re-reading 120 pages). This tool separates the cases.

Classes for a page past the staleness window (default 90 days):
  frozen   — every source is under raw/articles/ (published papers/posts) or a raw/docs
             snapshot that is itself younger than the window, AND no source has a git
             commit newer than last_verified. Claims can't have drifted → safe to bump.
  drifted  — a cited raw file has a commit newer than last_verified → re-verify by hand.
  snapshot — cites a raw/docs/ scrape older than the window → the wiki may be behind the
             PRODUCT even though the file didn't change; refetch, then re-check.
  no-src   — no raw sources listed (reference/meta pages) → human judgement.
  unfetched— the cited source is listed in sources/manifest.tsv but not on disk → fetch first.

raw/ is gitignored by default, so "changed" is decided from sources/manifest.tsv (a body hash per
source, recorded at the last verification). If you track raw/ in git, its history is used as well.

Usage:
  scripts/freshness.py                 # report, grouped by class
  scripts/freshness.py --bump          # set last_verified=today on `frozen` pages
  scripts/freshness.py --refetch       # re-snapshot code.claude.com into raw/docs/official/
                                       # via scripts/refetch-docs.sh (curl only); then report
  scripts/freshness.py --days 60 --json
"""
import argparse, datetime as dt, json, os, re, subprocess, sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or os.getcwd()
os.chdir(ROOT)
TODAY = dt.date.today()
FM_RE = re.compile(r"^---\n(.*?)\n---", re.S)


def frontmatter(text):
    m = FM_RE.match(text)
    return m.group(1) if m else ""


def field(fm, name):
    m = re.search(rf"^{name}:\s*(.*)$", fm, re.M)
    return m.group(1).strip() if m else ""


def sources(fm):
    """Handle `sources: [a, b]` and the YAML list form."""
    m = re.search(r"^sources:\s*\[(.*?)\]", fm, re.M | re.S)
    if m:
        return [s.strip().strip('"\'') for s in m.group(1).split(",") if s.strip()]
    m = re.search(r"^sources:\s*\n((?:\s+-\s+.*\n?)+)", fm, re.M)
    if m:
        return [re.sub(r"^\s*-\s+", "", l).strip().strip('"\'') for l in m.group(1).splitlines() if l.strip()]
    return []


_commit_cache = {}


def commit_dates(path):
    """(first, last) commit dates for path. A raw file whose ONLY commit is its creation has
    never changed — the wiki page may simply have been written from the working copy before
    the raw file was committed, so that is NOT drift."""
    if path not in _commit_cache:
        out = subprocess.run(["git", "log", "--format=%cs", "--", path], capture_output=True, text=True).stdout.split()
        _commit_cache[path] = (dt.date.fromisoformat(out[-1]), dt.date.fromisoformat(out[0])) if out else (None, None)
    return _commit_cache[path]


def last_commit(path):
    return commit_dates(path)[1]


_manifest = None


def manifest_row(path):
    """raw/ is gitignored by default (the sources are other people's text), so git history cannot
    say whether a source changed. sources/manifest.tsv records a body hash and fetch date for each
    source as of the last verification; scripts/sources.py owns the format."""
    global _manifest
    if _manifest is None:
        _manifest = {}
        if os.path.exists("sources/manifest.tsv"):
            for line in open("sources/manifest.tsv", encoding="utf-8"):
                if line.strip() and not line.startswith("#"):
                    parts = line.rstrip("\n").split("\t")
                    _manifest[parts[0]] = {"sha256": parts[1], "fetched": parse_date(parts[3]) if len(parts) > 3 else None}
    return _manifest.get(path)


def differs_from_manifest(path):
    row = manifest_row(path)
    if not row:
        return False
    out = subprocess.run([sys.executable, "scripts/sources.py", "changed", "--prefix", path], capture_output=True, text=True).stdout.split()
    return path in out


def parse_date(s):
    try:
        return dt.date.fromisoformat(s[:10])
    except Exception:
        return None


def set_last_verified(path, text, day):
    new = re.sub(r"^last_verified:.*$", f"last_verified: {day.isoformat()}", text, count=1, flags=re.M)
    if new == text:
        return False
    with open(path, "w") as f:
        f.write(new)
    return True


def classify(page, days):
    text = open(page, encoding="utf-8").read()
    fm = frontmatter(text)
    lv = parse_date(field(fm, "last_verified"))
    if lv is None:
        return None
    age = (TODAY - lv).days
    if age <= days:
        return None
    srcs = [s for s in sources(fm) if s.startswith("raw/")]
    if not srcs:
        return dict(page=page, cls="no-src", age=age, why="no raw sources listed")
    for s in srcs:
        if not os.path.exists(s):
            if manifest_row(s):
                return dict(page=page, cls="unfetched", age=age, why=f"{s} is not on disk; run ./scripts/sources.py fetch")
            return dict(page=page, cls="drifted", age=age, why=f"source missing: {s}")
        first, last = commit_dates(s)
        if last and last > lv and last != first:
            return dict(page=page, cls="drifted", age=age, why=f"{s} changed {last}")
        if last is None and differs_from_manifest(s):
            return dict(page=page, cls="drifted", age=age, why=f"{s} differs from the snapshot this wiki was verified against")
    for s in srcs:
        if s.startswith("raw/docs/"):
            c = last_commit(s) or (manifest_row(s) or {}).get("fetched")
            if c and (TODAY - c).days > days:
                return dict(page=page, cls="snapshot", age=age, why=f"{s} scraped {c} (> {days}d)")
    return dict(page=page, cls="frozen", age=age, why="sources unchanged since last_verified")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--bump", action="store_true", help="bump last_verified on `frozen` pages")
    ap.add_argument("--refetch", action="store_true", help="re-snapshot code.claude.com into raw/docs/official/ (curl)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.refetch:
        print("refetch: running scripts/refetch-docs.sh (curl snapshot of code.claude.com into raw/docs/official/)")
        rc = subprocess.run(["bash", "scripts/refetch-docs.sh"]).returncode
        if rc:
            return rc

    pages = sorted(
        os.path.join(d, f)
        for d, _, fs in os.walk("wiki")
        for f in fs
        if f.endswith(".md") and os.path.dirname(os.path.join(d, f)) != "wiki"
    )
    rows = [r for r in (classify(p, a.days) for p in pages) if r]
    groups = {k: [r for r in rows if r["cls"] == k] for k in ("drifted", "snapshot", "frozen", "no-src", "unfetched")}

    bumped = []
    if a.bump:
        for r in groups["frozen"]:
            t = open(r["page"], encoding="utf-8").read()
            if set_last_verified(r["page"], t, TODAY):
                bumped.append(r["page"])

    if a.json:
        print(json.dumps(dict(date=TODAY.isoformat(), days=a.days, counts={k: len(v) for k, v in groups.items()}, bumped=bumped, rows=rows), indent=2))
        return 0

    print(f"freshness — {TODAY} (window {a.days}d) — {len(rows)} page(s) past window")
    for k, label in (("drifted", "DRIFTED  re-verify by hand (source changed)"),
                     ("snapshot", "SNAPSHOT product may have moved; run --refetch, then re-check"),
                     ("frozen", "FROZEN   safe to bump (--bump)"),
                     ("no-src", "NO-SRC   judgement call"),
                     ("unfetched", "UNFETCHED run ./scripts/sources.py fetch, then re-check")):
        if groups[k]:
            print(f"\n{label}: {len(groups[k])}")
            for r in groups[k]:
                print(f"  {r['page']}  ({r['age']}d) — {r['why']}")
    if a.bump:
        print(f"\nbumped last_verified → {TODAY} on {len(bumped)} frozen page(s)")
        if bumped:
            print("next: append a log.md line, add a 🔄 hot.md entry, rerun scripts/wiki-lint.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
