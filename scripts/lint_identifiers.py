#!/usr/bin/env python3
"""lint_identifiers.py — flag Claude Code identifiers in wiki pages that appear in no raw source.

Why: the worst errors this wiki carried were invented names that looked plausible:
`$CLAUDE_FILE_PATH`, `/debug-config`, `user_invocable`, `/setup-foundry`. Each was found by
hand. This check makes that mechanical: every env var, slash command and `claude --flag` in
wiki/*/*.md must appear somewhere in raw/, or in sources/identifiers.txt (the committed index of
raw/, which is not distributed), or in the repo's own scripts/skills for names this project defines. Third-party names that raw/ covers only indirectly go in
scripts/lint-identifiers-allow.txt with a reason.

Usage:
  scripts/lint_identifiers.py            # human report
  scripts/lint_identifiers.py --lines    # "page: kind id" per finding (used by wiki-lint.sh)
  scripts/lint_identifiers.py --json
  scripts/lint_identifiers.py --ci       # exit 1 if anything is found
"""
import glob, json, os, re, subprocess, sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or os.getcwd()
os.chdir(ROOT)
ALLOW_FILE = "scripts/lint-identifiers-allow.txt"

PATTERNS = {
    "env": re.compile(r"\b(?:CLAUDE_CODE_[A-Z0-9_]+|CLAUDE_[A-Z0-9_]{3,}|ANTHROPIC_[A-Z0-9_]+)\b"),
    "slash": re.compile(r"^(/[a-z][a-z0-9-]{2,})(?=\s|$)"),  # applied to inline code-span contents only
    "flag": re.compile(r"\bclaude(?:\s+[a-z][a-z-]*)*\s+(--[a-z][a-z0-9-]+)"),
}


def corpus():
    parts = []
    # sources/identifiers.txt lists every identifier found in raw/, so this check still works in a
    # fresh clone and in CI, where raw/ is absent (this repository does not redistribute its sources).
    for pattern in ("raw/**/*.md", "raw/**/*.txt", "raw/**/*.json", "sources/identifiers.txt", "scripts/**/*", ".claude/**/*.md", ".claude/*.json", ".mcp.json", "CLAUDE.md"):
        for f in glob.glob(pattern, recursive=True):
            if os.path.isfile(f) and os.path.getsize(f) < 20_000_000:
                try:
                    parts.append(open(f, encoding="utf-8", errors="ignore").read())
                except OSError:
                    pass
    return "\n".join(parts)


def allowlist():
    allow = set()
    if os.path.exists(ALLOW_FILE):
        for line in open(ALLOW_FILE, encoding="utf-8"):
            token = line.split("#", 1)[0].strip()
            if token:
                allow.add(token)
    allow |= {"/" + os.path.basename(d.rstrip("/")) for d in glob.glob(".claude/skills/*/")}
    return allow


def scan():
    text_corpus, allow, findings = corpus(), allowlist(), []
    for page in sorted(glob.glob("wiki/*/*.md")):
        for n, line in enumerate(open(page, encoding="utf-8"), 1):
            candidates = []
            for kind in ("env", "flag"):
                candidates += [(kind, m.group(1) if m.groups() else m.group(0)) for m in PATTERNS[kind].finditer(line)]
            # Slash commands: only whole inline code spans such as `/compact` or `/loop 5m`, so text
            # like `llmfit`/btop (a closing backtick followed by a slash) is not mistaken for one.
            for span in re.findall(r"`([^`\n]+)`", line):
                m = PATTERNS["slash"].match(span.strip())
                if m and not span.strip()[m.end(1):m.end(1) + 1] == "/":
                    candidates.append(("slash", m.group(1)))
            for kind, ident in candidates:
                if ident in allow or ident in text_corpus:
                    continue
                findings.append({"page": page, "line": n, "kind": kind, "id": ident})
    return findings


def main():
    f = scan()
    if "--json" in sys.argv:
        print(json.dumps({"count": len(f), "items": f}, indent=2))
    elif "--lines" in sys.argv:
        for x in f:
            print(f"{x['page']}:{x['line']}: {x['kind']} {x['id']}")
    else:
        print(f"unsourced identifiers: {len(f)}")
        for x in f:
            print(f"  {x['page']}:{x['line']}  {x['kind']:5s} {x['id']}")
    return 1 if ("--ci" in sys.argv and f) else 0


if __name__ == "__main__":
    sys.exit(main())
