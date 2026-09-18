"""scripts/freshness.py classification against a throwaway git repo."""
import os, shutil, subprocess
import pytest
from conftest import REPO, load


def git(cwd, *args, date=None):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    if date:
        env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(["git", *args], cwd=cwd, check=True, env=env, capture_output=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q")
    (tmp_path / "raw/articles").mkdir(parents=True)
    (tmp_path / "wiki/concepts").mkdir(parents=True)
    (tmp_path / "raw/articles/a.md").write_text("v1\n")
    (tmp_path / "wiki/concepts/p.md").write_text("---\ntitle: P\nsources:\n  - raw/articles/a.md\nlast_verified: 2026-05-01\n---\nbody\n")
    git(tmp_path, "add", "-A"); git(tmp_path, "commit", "-qm", "init", date="2026-06-01T12:00:00")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_single_creation_commit_is_frozen_not_drifted(repo):
    fr = load("freshness_a", "scripts/freshness.py")
    row = fr.classify("wiki/concepts/p.md", 90)
    assert row and row["cls"] == "frozen"


def test_later_edit_to_source_is_drifted(repo):
    (repo / "raw/articles/a.md").write_text("v2\n")
    git(repo, "commit", "-qam", "edit", date="2026-07-01T12:00:00")
    fr = load("freshness_b", "scripts/freshness.py")
    assert fr.classify("wiki/concepts/p.md", 90)["cls"] == "drifted"
