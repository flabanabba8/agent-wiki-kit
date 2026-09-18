"""The wiki's sources are not distributed, so the checks that read raw/ must work from
sources/manifest.tsv and sources/identifiers.txt instead."""
import os
import subprocess
import sys

from conftest import REPO, load


def run(*args, cwd=REPO):
    return subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True)


def test_no_third_party_source_is_tracked_in_git():
    """raw/ holds other publishers' text. Only raw/README.md may ever be committed."""
    tracked = subprocess.run(["git", "ls-files", "raw"], cwd=REPO, capture_output=True, text=True).stdout.split()
    assert tracked in ([], ["raw/README.md"]), f"third-party sources are tracked: {tracked[:5]}"
    ignored = subprocess.run(["git", "check-ignore", "-q", "raw/docs/official/hooks.md"], cwd=REPO)
    assert ignored.returncode == 0, "raw/* must stay gitignored"


def test_manifest_lists_an_origin_for_every_source():
    rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(REPO, "sources/manifest.tsv"), encoding="utf-8")
            if l.strip() and not l.startswith("#")]
    assert len(rows) > 100
    for path, sha, size, fetched, method, *url in rows:
        assert path.startswith("raw/") and len(sha) == 64 and method in {"official", "changelog", "url", "page", "local"}, path
        if method in ("url", "page"):
            assert url and url[0].startswith("http"), f"{path} has no origin URL"


def test_identifier_lint_passes_without_any_sources(tmp_path):
    """The no-invented-names check must hold in a fresh clone and in CI, where raw/ is empty."""
    r = run(os.path.join(REPO, "scripts/lint_identifiers.py"), "--ci")
    assert r.returncode == 0, r.stdout


def test_body_hash_ignores_the_source_header():
    src = load("awk_sources_t", "scripts/sources.py")
    a = b"<!-- SOURCE: https://example.com/x | fetched: 2026-01-01 -->\n# Title\n\nBody text.\n"
    b = b"<!-- SOURCE: https://example.com/x | fetched: 2027-12-31 | via scripts/sources.py -->\n# Title\n\nBody text.\n\n"
    c = b"<!-- SOURCE: https://example.com/x | fetched: 2026-01-01 -->\n# Title\n\nBody text, edited upstream.\n"
    assert src.body_hash("raw/x.md", a) == src.body_hash("raw/x.md", b), "a refetch of unchanged text must match"
    assert src.body_hash("raw/x.md", a) != src.body_hash("raw/x.md", c), "changed text must be detected"


def test_changelog_slice_keeps_only_the_named_versions():
    src = load("awk_sources_t2", "scripts/sources.py")
    full = "# Changelog\n\n## 2.1.5\n- e\n\n## 2.1.4\n- d\n\n## 2.1.3\n- c\n\n## 2.1.2\n- b\n"
    out = src.changelog_slice("raw/docs/changelog-2.1.3-to-2.1.4.md", full)
    assert "## 2.1.4" in out and "## 2.1.3" in out and "## 2.1.5" not in out and "## 2.1.2" not in out
