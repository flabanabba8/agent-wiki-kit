#!/usr/bin/env python3
"""build-index.py — regenerate wiki/index.md from every page's frontmatter.

Why: the catalog is derived data (folder, slug, tldr), and a hand-kept list goes stale the moment a
page is added, renamed or deleted. Lint check 3 fails when a page is missing from the index.

Usage: ./scripts/build-index.py            # rewrite wiki/index.md
       ./scripts/build-index.py --check    # exit 1 if it would change
Folder headings and blurbs come from HEADINGS below; a folder not listed there gets its name in title
case, so a new wiki works before anyone edits this file. Standard library only.
"""
import datetime
import glob
import os
import re
import subprocess
import sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or os.getcwd()
os.chdir(ROOT)
HEADINGS = {
    "start": ("Start here", "Install Claude Code and learn how it works."),
    "using": ("Using Claude Code", "Day-to-day work: prompting, memory, context, permissions, models, cost."),
    "extending": ("Extending", "Skills, subagents, agent teams, hooks, MCP servers and plugins."),
    "automation": ("Automation", "Background work, workflows, schedules, channels, artifacts and headless runs."),
    "surfaces": ("Surfaces", "Where Claude Code runs besides the terminal."),
    "deployment": ("Deployment", "Providers, gateways, settings, org administration, networks and privacy."),
    "reference": ("Reference", "Complete lists of commands, flags, variables and tools."),
    "sdk-and-api": ("SDK and API", "Building on the Agent SDK, Managed Agents and the Claude API."),
    "research": ("Research", "Findings on agentic systems, mostly from Anthropic."),
    "ecosystem": ("Ecosystem", "Other agents and tools this project uses or compares against."),
    "project": ("This project", "How the harness works and how it runs from four agents."),
}


def tldr(path):
    fm = open(path, encoding="utf-8").read().split("---", 2)[1]
    m = re.search(r'^tldr:\s*(.*)$', fm, re.M)
    return (m.group(1).strip().strip("\"'") if m else "").rstrip(".")


def build():
    folders = sorted({os.path.basename(os.path.dirname(p)) for p in glob.glob("wiki/*/*.md")},
                     key=lambda f: (list(HEADINGS).index(f) if f in HEADINGS else len(HEADINGS), f))
    out = ["---", "title: Wiki Index", f"updated: {datetime.date.today()}", "---", "", "# Wiki Index", "",
           "Every page in this wiki, by folder. Each topic has exactly one page that owns it; other pages link "
           "there rather than restating facts. Search first with "
           "`./.venv/bin/python scripts/mem0/query_wiki.py \"<question>\"`.", ""]
    total = 0
    for folder in folders:
        heading, blurb = HEADINGS.get(folder, (folder.replace("-", " ").title(), ""))
        out += [f"## {heading}", ""] + ([blurb, ""] if blurb else [])
        for page in sorted(glob.glob(f"wiki/{folder}/*.md")):
            out.append(f"- [[{os.path.basename(page)[:-3]}]] — {tldr(page)}")
            total += 1
        out.append("")
    out += ["## Session files", "", "- `hot.md` — recent decisions, fixes and gotchas, newest first.",
            "- `log.md` — append-only record of changes to this wiki.", "", f"{total} pages.", ""]
    return "\n".join(out)


def main():
    new = build()
    path = "wiki/index.md"
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    same = re.sub(r"^updated: .*$", "", old, flags=re.M) == re.sub(r"^updated: .*$", "", new, flags=re.M)
    if "--check" in sys.argv:
        print("wiki/index.md is up to date" if same else "wiki/index.md is stale: run ./scripts/build-index.py")
        return 0 if same else 1
    if not same:
        open(path, "w", encoding="utf-8").write(new)
    print(f"wiki/index.md: {new.count('- [[')} pages" + ("" if not same else " (unchanged)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
