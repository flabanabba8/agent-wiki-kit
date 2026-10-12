#!/usr/bin/env python3
"""log-archive.py - move old entries out of wiki/log.md so the startup path stays small.

wiki/log.md is append-only and read at the start of work. Entries from earlier months move to
wiki/log-YYYY-MM.md (not indexed), so log.md holds the current month plus any entry whose heading
has no date, newest first. Each entry starts with a `## ` heading that contains a YYYY-MM-DD date. Running it
twice changes nothing, and an entry already present in a month file is not written again.

  log-archive.py             archive entries older than the current month
  log-archive.py --check     exit 1 when entries are waiting to move; changes nothing
  log-archive.py --keep N    keep the current month and the N-1 before it (default 1)
Standard library only.
"""
import datetime as dt
import os
import re
import subprocess
import sys

DATE = re.compile(r"(\d{4})-(\d{2})-\d{2}")


def split(text):
    """(preamble, [section text, ...]); every section starts at a '## ' line."""
    parts = re.split(r"(?m)^(?=## )", text)
    return parts[0], parts[1:]


def month_of(section):
    m = DATE.search(section.split("\n", 1)[0])
    return f"{m.group(1)}-{m.group(2)}" if m else None


def cutoff(today, keep):
    y, mo = today.year, today.month - (keep - 1)
    while mo < 1:
        mo += 12
        y -= 1
    return f"{y:04d}-{mo:02d}"


def plan(text, today, keep=1):
    pre, sections = split(text)
    limit = cutoff(today, keep)
    stay, move = [], {}
    for s in sections:
        mo = month_of(s)
        if mo and mo < limit:
            move.setdefault(mo, []).append(s)
        else:
            stay.append(s)
    return pre, stay, move


def newest_first(sections):
    """Stable sort: newest date first; an undated entry keeps the top."""
    def key(s):
        m = DATE.search(s.split("\n", 1)[0])
        return m.group(0) if m else "9999-99-99"
    return sorted(sections, key=key, reverse=True)


def pointer(months):
    if not months:
        return ""
    names = ", ".join(f"`wiki/log-{m}.md`" for m in sorted(months, reverse=True))
    return f"> Older entries: {names} (not indexed).\n\n"


def main(argv):
    base = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or os.getcwd()
    keep = int(argv[argv.index("--keep") + 1]) if "--keep" in argv else 1
    log = os.path.join(base, "wiki", "log.md")
    text = open(log, encoding="utf-8").read()
    pre, stay, move = plan(text, dt.date.today(), keep)
    waiting = sum(len(v) for v in move.values())
    ordered = newest_first(stay)
    reorder = ordered != stay
    if "--check" in argv:
        if waiting or reorder:
            why = []
            if waiting:
                why.append(f"{waiting} entr{'y' if waiting == 1 else 'ies'} older than the current month")
            if reorder:
                why.append("entries out of newest-first order")
            print("log.md: " + " and ".join(why) + ": run scripts/log-archive.py")
            return 1
        print("log.md holds only the current month, newest first")
        return 0
    if not waiting and not reorder:
        print("nothing to archive")
        return 0
    stay = ordered
    for mo, secs in move.items():
        path = os.path.join(base, "wiki", f"log-{mo}.md")
        existing = open(path, encoding="utf-8").read() if os.path.exists(path) else f"# Log {mo}\n\nArchived from wiki/log.md.\n\n"
        for s in secs:
            if s.split("\n", 1)[0] not in existing:
                existing = existing.rstrip("\n") + "\n\n" + s.rstrip("\n") + "\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(existing)
    months = {m for m in (os.path.basename(p)[4:11] for p in os.listdir(os.path.join(base, "wiki")) if re.match(r"log-\d{4}-\d{2}\.md$", p))}
    pre = re.sub(r"(?m)^> Older entries:.*\n\n?", "", pre)
    pre = pre.rstrip("\n") + "\n\n" + pointer(months)
    with open(log, "w", encoding="utf-8") as f:
        f.write(pre + "".join(stay))
    print(f"archived {waiting} into {', '.join(f'wiki/log-{m}.md' for m in sorted(move)) or 'nothing'}; log.md is newest first")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
