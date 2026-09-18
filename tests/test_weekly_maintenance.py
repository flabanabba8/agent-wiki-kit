"""Every path weekly-maintenance.sh stages must be committable.

Why: `git add` exits 1 on an explicitly named path that is gitignored. The script sets
-uo pipefail but not -e, so ignoring outputs/reverify-queue.md would fail silently and the
weekly maintenance commit would simply lose the queue.
"""
import os
import subprocess

from conftest import REPO

SCRIPT = os.path.join(REPO, "scripts", "weekly-maintenance.sh")


def staged_paths():
    paths = []
    for line in open(SCRIPT, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("git add"):
            continue
        for tok in line.split()[2:]:
            if tok.startswith(("-", "$", '"', "'", "|", "&")):
                continue
            paths.append(tok)
    return paths


def test_script_stages_paths():
    assert staged_paths(), "no `git add` paths found in weekly-maintenance.sh"


def test_staged_paths_are_not_gitignored():
    for p in staged_paths():
        r = subprocess.run(["git", "check-ignore", "-q", p], cwd=REPO)
        assert r.returncode == 1, (
            f"weekly-maintenance.sh stages {p!r} but git check-ignore returned "
            f"{r.returncode} (0 means gitignored, so `git add` would fail)"
        )


def test_git_add_failure_is_not_silent():
    """The script must not let a failed `git add` pass unnoticed."""
    body = open(SCRIPT, encoding="utf-8").read()
    add_lines = [l.strip() for l in body.splitlines() if l.strip().startswith("git add")]
    for line in add_lines:
        assert "||" in line or "set -e" in body, (
            f"{line!r} can fail silently: the script has no `set -e` and the line "
            "has no failure branch"
        )
