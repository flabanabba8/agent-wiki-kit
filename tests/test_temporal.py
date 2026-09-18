"""scripts/wiki-temporal.sh exit codes for valid_until expiry."""
import os, shutil, subprocess
from conftest import REPO


def make(tmp_path, pages):
    (tmp_path / "scripts").mkdir()
    shutil.copy(os.path.join(REPO, "scripts/wiki-temporal.sh"), tmp_path / "scripts/wiki-temporal.sh")
    for name, fm in pages.items():
        d = tmp_path / "wiki/concepts"; d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.md").write_text(f"---\ntitle: {name}\n{fm}\n---\nbody\n")
    return subprocess.run(["bash", str(tmp_path / "scripts/wiki-temporal.sh")], capture_output=True, text=True)


def test_current_page_passes(tmp_path):
    r = make(tmp_path, {"page": "valid_until: 2999-01-01"})
    assert r.returncode == 0, r.stdout


def test_supersedes_field_is_ignored(tmp_path):
    r = make(tmp_path, {"new": 'supersedes: "[[deleted-page]]"'})
    assert r.returncode == 0, r.stdout


def test_expired_valid_until_fails(tmp_path):
    r = make(tmp_path, {"vol": "valid_until: 2000-01-01"})
    assert r.returncode == 1 and "EXPIRED" in r.stdout


def test_deprecated_page_expiry_ignored(tmp_path):
    r = make(tmp_path, {"vol": "status: deprecated\nvalid_until: 2000-01-01"})
    assert r.returncode == 0
