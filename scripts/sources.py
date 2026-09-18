#!/usr/bin/env python3
"""sources.py — the wiki's primary sources, without shipping them.

Every wiki claim traces to a file under raw/. Those files are copies of other people's
documentation and papers, so this repository does not distribute them: raw/ is gitignored and a
fresh clone has none. What IS committed is sources/manifest.tsv (where each file came from and a
hash of its content when the wiki was last verified against it) and sources/identifiers.txt (every
environment variable, slash command and CLI flag that appears in them, so the identifier lint still
works with no sources present).

  sources.py fetch [--all] [--only PREFIX]   download the sources listed in the manifest into raw/
  sources.py status                          how many are present, missing, or differ from the manifest
                                             (rendered web pages are fetched but never compared)
  sources.py changed [--prefix P]            paths whose content differs from the verified snapshot
  sources.py new [--prefix P]                files in raw/ that the manifest does not list yet
  sources.py manifest [--accept PATH ...]    rebuild the manifest and identifier index from raw/
                                             (--accept: only re-record the named files)

Hashes cover the BODY only: the SOURCE header carries the fetch date, so a byte hash would never
match a refetch. A page that upstream has not changed therefore matches exactly, and one that has
changed is reported, which is the signal freshness.py and the weekly maintenance job act on.
A refetch that differs does not mean the wiki is wrong. It means nobody has checked the page
against the new text yet. After re-verifying, record the new state with `manifest --accept`.

Standard library only. The Camoufox fallback for JavaScript-rendered pages needs the project venv.
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or os.getcwd()
os.chdir(ROOT)
MANIFEST = "sources/manifest.tsv"
IDENTIFIERS = "sources/identifiers.txt"
COLUMNS = ["path", "sha256", "bytes", "fetched", "method", "url"]
NO_HEADER_EXT = {".pdf", ".json", ".js", ".txt"}
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0 agent-wiki-kit-sources/1.0"
CHANGELOG_URL = "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md"
IGNORED = {"raw/README.md"}

# Captures that were saved without a SOURCE header.
OVERRIDES = {
    "raw/docs/toolaria/README.md": "https://raw.githubusercontent.com/Sahil-SS9/Toolaria/main/README.md",
    "raw/docs/toolaria/ARCHITECTURE.md": "https://raw.githubusercontent.com/Sahil-SS9/Toolaria/main/docs/ARCHITECTURE.md",
    "raw/docs/toolaria/DESIGN.md": "https://raw.githubusercontent.com/Sahil-SS9/Toolaria/main/docs/DESIGN.md",
    "raw/docs/computer-use-linux/README.md": "https://raw.githubusercontent.com/agent-sh/computer-use-linux/main/README.md",
    "raw/docs/computer-use-linux/CHANGELOG.md": "https://raw.githubusercontent.com/agent-sh/computer-use-linux/main/CHANGELOG.md",
    "raw/docs/computer-use-linux/CONTRIBUTING.md": "https://raw.githubusercontent.com/agent-sh/computer-use-linux/main/CONTRIBUTING.md",
    "raw/docs/computer-use-linux/SECURITY.md": "https://raw.githubusercontent.com/agent-sh/computer-use-linux/main/SECURITY.md",
    "raw/docs/computer-use-linux/SKILL.md": "https://raw.githubusercontent.com/agent-sh/computer-use-linux/main/skills/computer-use-linux/SKILL.md",
    "raw/docs/headroom/headroom-docs-full.md": "https://docs.headroomlabs.ai/llms-full.txt",
    "raw/articles/skillopt-2026.pdf": "https://arxiv.org/pdf/2605.23904",
    "raw/articles/skillsvote-2026.pdf": "https://arxiv.org/pdf/2605.18401",
    "raw/articles/hasp-2026.pdf": "https://arxiv.org/pdf/2605.17734",
    "raw/docs/openrouter/models-api-2026-09-14.json": "https://openrouter.ai/api/v1/models",
    "raw/docs/nvidia-nim/models-api-2026-09-14.json": "https://integrate.api.nvidia.com/v1/models",
    "raw/articles/karpathy-coding-pitfalls.md": "https://raw.githubusercontent.com/multica-ai/andrej-karpathy-skills/main/README.md",
}
# Files other tools produce; `fetch` runs the tool instead of downloading the path.
GENERATED = {
    "raw/docs/official/llms.txt": "official",
    "raw/docs/official/MANIFEST.txt": "official",
}
LOCAL_ONLY = {  # produced on this machine, not downloadable
    "raw/docs/mem0/": "introspection of the installed mem0ai package; regenerate by inspecting mem0.Memory in the project venv",
}

HEADER_PATTERNS = [
    re.compile(r"\A<!--.*?-->\s*\n", re.S),                                   # <!-- SOURCE: ... -->
    re.compile(r"\A---\n(?=[^\n]*SOURCE)(?:.*?\n)---\s*\n", re.S | re.I),       # ---\nSOURCE: ...\n---
    re.compile(r"\A#\s*source\b[^\n]*\n(?:(?!\n)[^\n]*\n)*\n", re.I),          # "# SOURCE" block to first blank line
]
ID_PATTERNS = [
    re.compile(r"\b(?:CLAUDE_CODE_[A-Z0-9_]+|CLAUDE_[A-Z0-9_]{3,}|ANTHROPIC_[A-Z0-9_]+)\b"),
    re.compile(r"(?<![\w-])--[a-z][a-z0-9-]+"),
    re.compile(r"(?<![\w.])/[a-z][a-z0-9-]{2,}"),
]


# ── reading ──────────────────────────────────────────────────────────────────────────────
def raw_files():
    return sorted(f for f in glob.glob("raw/**/*", recursive=True) if os.path.isfile(f) and f not in IGNORED)


def split_header(path, data):
    """(header_text, body_bytes). Binary and data files have no header."""
    if os.path.splitext(path)[1].lower() in NO_HEADER_EXT:
        return "", data
    text = data.decode("utf-8", errors="replace")
    for pat in HEADER_PATTERNS:
        m = pat.match(text)
        if m:
            return m.group(0), text[m.end():].encode("utf-8")
    return "", data


def body_hash(path, data=None):
    if data is None:
        data = open(path, "rb").read()
    header, body = split_header(path, data)
    if os.path.splitext(path)[1].lower() == ".pdf":
        return hashlib.sha256(body).hexdigest()
    # Compare text, not layout: drop blank lines, trailing spaces and bare code-fence lines, so a capture
    # that was wrapped in a fence or spaced differently still matches when its words are the same.
    lines = (l.rstrip() for l in body.decode("utf-8", errors="replace").replace("\r\n", "\n").split("\n"))
    norm = "\n".join(l for l in lines if l and not re.fullmatch(r"\s*(```|~~~)[\w-]*", l)) + "\n"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def header_facts(path, header, head_text=""):
    """URL and fetch date. Older captures have no header block, just `> Source: <url>` and
    `> Retrieved: <date>` lines under the title, so fall back to the first lines of the file."""
    url = OVERRIDES.get(path, "")
    where = header or head_text
    if not url:
        m = re.search(r"(?i)(?:source|repo)\b[^\n]*?(https?://[^\s|>\"')]+)", where) or re.search(r"https?://[^\s|>\"')]+", header)
        url = (m.group(1) if m and m.groups() else m.group(0) if m else "").rstrip(".,")
    m = re.search(r"(?i)(?:fetched|retrieved):?\s*(\d{4}-\d{2}-\d{2})", where)
    return url, (m.group(1) if m else "")


def method_for(path, url):
    if path in GENERATED or path.startswith("raw/docs/official/"):
        return "official"
    if re.match(r"raw/docs/changelog-[\d.]+-to-[\d.]+\.md$", path):
        return "changelog"
    if any(path.startswith(p) for p in LOCAL_ONLY):
        return "local"
    if not url:
        return "unknown"
    # A text endpoint (.md, raw GitHub file, PDF, JSON API) can be compared byte for word. A rendered web
    # page cannot: the verified copy was converted to Markdown by hand or by a browser, so a refetch never
    # reproduces it. Those are published articles, which do not drift; they are fetched but not compared.
    texty = re.search(r"\.(md|txt|json|pdf|toml|ya?ml|rs|ts|js|py)(\?|$)", url) or "raw.githubusercontent.com" in url \
        or "arxiv.org/pdf/" in url or "/api/" in url or "/v1/models" in url
    return "url" if texty else "page"


def load_manifest():
    rows = {}
    if os.path.exists(MANIFEST):
        for line in open(MANIFEST, encoding="utf-8"):
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            rows[parts[0]] = dict(zip(COLUMNS, parts + [""] * (len(COLUMNS) - len(parts))))
    return rows


def save_manifest(rows):
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        f.write("# The primary sources this wiki was verified against. Generated by scripts/sources.py manifest.\n")
        f.write("# sha256 covers the body only (the SOURCE header holds the fetch date). `fetch` rebuilds raw/ from this.\n")
        f.write("# " + "\t".join(COLUMNS) + "\n")
        for path in sorted(rows):
            f.write("\t".join(str(rows[path].get(c, "")) for c in COLUMNS) + "\n")


def state(path, rows=None):
    """'missing' | 'same' | 'changed' | 'untracked' for one raw path."""
    rows = load_manifest() if rows is None else rows
    if path not in rows:
        return "untracked" if os.path.exists(path) else "missing"
    if not os.path.exists(path):
        return "missing"
    if rows[path].get("method") == "page":
        return "same"  # present; a rendered page is not comparable (see method_for)
    return "same" if body_hash(path) == rows[path]["sha256"] else "changed"


# ── manifest ─────────────────────────────────────────────────────────────────────────────
def cmd_manifest(args):
    files = raw_files()
    if not files:
        sys.exit("raw/ is empty. Run `./scripts/sources.py fetch` first; the manifest is built from the files on disk.")
    rows = load_manifest()
    targets = set(args.accept) if args.accept else set(files)
    for path in sorted(targets):
        if not os.path.exists(path):
            print(f"  skip (not on disk): {path}")
            continue
        data = open(path, "rb").read()
        header, _ = split_header(path, data)
        head_text = "" if os.path.splitext(path)[1].lower() in NO_HEADER_EXT else data[:900].decode("utf-8", errors="replace")
        url, fetched = header_facts(path, header, head_text)
        old = rows.get(path, {})
        rows[path] = {"path": path, "sha256": body_hash(path, data), "bytes": len(data),
                      "fetched": fetched or old.get("fetched") or dt.date.fromtimestamp(os.path.getmtime(path)).isoformat(),
                      "url": url or old.get("url", ""), "method": ""}
        rows[path]["method"] = method_for(path, rows[path]["url"])
    if not args.accept:
        for path in [p for p in rows if p not in files]:
            del rows[path]
    save_manifest(rows)

    idents = set()
    for path in files:
        if os.path.splitext(path)[1].lower() == ".pdf" or os.path.getsize(path) > 20_000_000:
            continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        for pat in ID_PATTERNS:
            idents.update(pat.findall(text))
    with open(IDENTIFIERS, "w", encoding="utf-8") as f:
        f.write("# Every environment variable, CLI flag and slash-like token found in raw/. Facts only, no prose.\n")
        f.write("# scripts/lint_identifiers.py reads this, so the no-invented-names check works without raw/.\n")
        f.write("\n".join(sorted(idents)) + "\n")
    unknown = [p for p, r in rows.items() if r["method"] == "unknown"]
    print(f"manifest: {len(rows)} sources, {len(idents)} identifiers, {len(unknown)} with no known origin")
    for p in unknown:
        print(f"  no origin: {p}")


# ── status ───────────────────────────────────────────────────────────────────────────────
def cmd_status(args):
    rows = load_manifest()
    counts = {"same": [], "changed": [], "missing": []}
    for path in rows:
        counts[state(path, rows)].append(path)
    extra = [p for p in raw_files() if p not in rows]
    if args.json:
        print(json.dumps({k: v for k, v in counts.items()} | {"untracked": extra}))
    else:
        print(f"sources: {len(rows)} in manifest | {len(counts['same'])} match | {len(counts['changed'])} differ | "
              f"{len(counts['missing'])} missing | {len(extra)} not in manifest")
        if counts["missing"] and len(counts["missing"]) == len(rows):
            print("  nothing fetched yet: run ./scripts/sources.py fetch")


def cmd_changed(args):
    rows = load_manifest()
    for path in sorted(rows):
        if path.startswith(args.prefix) and state(path, rows) == "changed":
            print(path)


def cmd_new(args):
    rows = load_manifest()
    for path in raw_files():
        if path.startswith(args.prefix) and path not in rows:
            print(path)


# ── fetch ────────────────────────────────────────────────────────────────────────────────
def http_get(url, timeout=60):
    url = re.sub(r"^https://github\.com/([^/]+/[^/]+)/blob/", r"https://raw.githubusercontent.com/\1/", url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def camoufox_get(url):
    py, script = os.path.join(".venv", "bin", "python"), os.path.join("scripts", "camoufox", "fetch.py")
    if not (os.path.exists(py) and os.path.exists(script)):
        return None
    r = subprocess.run([py, script, url, "--json", "--max-chars", "4000000"], capture_output=True, text=True, timeout=240)
    try:
        d = json.loads(r.stdout)
        return (d.get("text") or "").encode("utf-8") if (d.get("status") or 0) < 400 else None
    except Exception:
        return None


class _Text(__import__("html.parser").parser.HTMLParser):
    """Minimal HTML to text, for article pages when Camoufox is not installed."""
    SKIP = {"script", "style", "noscript", "svg", "head", "nav", "footer", "form"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "section", "article", "blockquote"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.out.append("\n")
        if tag in ("h1", "h2", "h3") and not self.skip:
            self.out.append("#" * int(tag[1]) + " ")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_to_text(data):
    p = _Text()
    p.feed(data.decode("utf-8", errors="replace"))
    text = re.sub(r"[ \t]+", " ", "".join(p.out))
    return (re.sub(r"\n\s*\n+", "\n\n", text).strip() + "\n").encode("utf-8")


def looks_like_shell(path, data):
    if os.path.splitext(path)[1].lower() in (".pdf", ".json", ".js"):
        return False
    head = data[:600].lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def changelog_slice(path, full):
    lo, hi = (tuple(int(x) for x in v.split(".")) for v in re.match(r".*changelog-([\d.]+)-to-([\d.]+)\.md$", path).groups())
    out, keep = [], False
    for block in re.split(r"(?m)^(?=## \d)", full):
        m = re.match(r"## (\d+(?:\.\d+)+)", block)
        if m and lo <= tuple(int(x) for x in m.group(1).split(".")) <= hi:
            out.append(block.rstrip() + "\n")
    return "\n".join(out)


def write_source(path, url, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        if os.path.splitext(path)[1].lower() not in NO_HEADER_EXT:
            f.write(f"<!-- SOURCE: {url} | fetched: {dt.date.today()} | via scripts/sources.py -->\n".encode("utf-8"))
        f.write(body)


def cmd_fetch(args):
    rows = load_manifest()
    if not rows:
        sys.exit(f"{MANIFEST} is missing or empty.")
    todo = [r for p, r in sorted(rows.items())
            if p.startswith(args.only) and (args.all or not os.path.exists(p))]
    print(f"{len(todo)} of {len(rows)} sources to fetch" + (" (everything already present)" if not todo else ""))
    done = {"ok": 0, "differs": 0, "failed": 0, "skipped": 0}
    report = []

    if any(r["method"] == "official" for r in todo):
        print("official Claude Code docs: scripts/refetch-docs.sh ...")
        subprocess.run(["bash", "scripts/refetch-docs.sh"], stdout=subprocess.DEVNULL)
    changelog = None
    for r in todo:
        path, url, method = r["path"], r["url"], r["method"]
        try:
            if method == "official":
                if not os.path.exists(path):
                    raise RuntimeError("no longer listed in llms.txt")
            elif method == "local":
                done["skipped"] += 1
                report.append(f"  local-only  {path}  ({next(v for k, v in LOCAL_ONLY.items() if path.startswith(k))})")
                continue
            elif method == "changelog":
                if changelog is None:
                    changelog = http_get(CHANGELOG_URL).decode("utf-8", errors="replace")
                body = changelog_slice(path, changelog)
                if not body.strip():
                    raise RuntimeError("those versions are no longer in CHANGELOG.md")
                write_source(path, CHANGELOG_URL, body.encode("utf-8"))
            elif method in ("url", "page"):
                try:
                    data = http_get(url)
                except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                    data = camoufox_get(url)
                    if data is None:
                        raise RuntimeError(f"{type(e).__name__}: {e}")
                if looks_like_shell(path, data):
                    # An HTML page, not a text endpoint. A real browser gives the best text; without
                    # Camoufox, strip the markup so the file is still readable and searchable.
                    data = camoufox_get(url) or html_to_text(data)
                write_source(path, url, data)
            else:
                raise RuntimeError("origin unknown")
            same = method == "page" or body_hash(path) == r["sha256"]
            done["ok" if same else "differs"] += 1
            if not same:
                report.append(f"  differs     {path}")
        except Exception as e:
            done["failed"] += 1
            report.append(f"  FAILED      {path}  ({str(e)[:90]})")
    print(f"fetched: {done['ok']} identical to the verified snapshot, {done['differs']} differ, "
          f"{done['failed']} failed, {done['skipped']} local-only")
    if report:
        print("\n".join(report[:60]) + (f"\n  ... and {len(report) - 60} more" if len(report) > 60 else ""))
    if done["differs"]:
        print("A source that differs is not an error: upstream moved since the wiki was last checked against it.\n"
              "./scripts/freshness.py lists the pages that cite those files.")
    return 1 if done["failed"] and not (done["ok"] or done["differs"]) else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("fetch"); p.add_argument("--all", action="store_true"); p.add_argument("--only", default="raw/")
    p = sub.add_parser("status"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("changed"); p.add_argument("--prefix", default="raw/")
    p = sub.add_parser("new"); p.add_argument("--prefix", default="raw/")
    p = sub.add_parser("manifest"); p.add_argument("--accept", nargs="*", default=[])
    args = ap.parse_args()
    return {"fetch": cmd_fetch, "status": cmd_status, "changed": cmd_changed, "new": cmd_new,
            "manifest": cmd_manifest}[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
