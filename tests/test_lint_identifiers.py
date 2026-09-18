"""scripts/lint_identifiers.py against a throwaway repo."""
import json, os, shutil, subprocess
from conftest import REPO


def run(tmp_path, page_text, raw_text, allow=""):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "scripts").mkdir()
    shutil.copy(os.path.join(REPO, "scripts/lint_identifiers.py"), tmp_path / "scripts/lint_identifiers.py")
    (tmp_path / "scripts/lint-identifiers-allow.txt").write_text(allow)
    (tmp_path / "raw/docs").mkdir(parents=True)
    (tmp_path / "raw/docs/official.md").write_text(raw_text)
    (tmp_path / "wiki/concepts").mkdir(parents=True)
    (tmp_path / "wiki/concepts/p.md").write_text(page_text)
    r = subprocess.run(["python3", "scripts/lint_identifiers.py", "--json"], cwd=tmp_path, capture_output=True, text=True, check=True)
    return {x["id"] for x in json.loads(r.stdout)["items"]}


PAGE = """Set `CLAUDE_REAL_VAR` or `CLAUDE_FAKE_VAR`. Run `/real-cmd` or `/fake-cmd`.
See `/docs/en/hooks` and run `claude --real-flag` or `claude mcp add --fake-flag`.
"""
RAW = "CLAUDE_REAL_VAR /real-cmd --real-flag"


def test_flags_only_unsourced_names(tmp_path):
    assert run(tmp_path, PAGE, RAW) == {"CLAUDE_FAKE_VAR", "/fake-cmd", "--fake-flag"}


def test_allowlist_suppresses(tmp_path):
    assert run(tmp_path, PAGE, RAW, allow="/fake-cmd  # third-party tool\nCLAUDE_FAKE_VAR\n--fake-flag\n") == set()


def test_ci_mode_exit_code(tmp_path):
    run(tmp_path, PAGE, RAW)
    r = subprocess.run(["python3", "scripts/lint_identifiers.py", "--ci"], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 1


def test_closing_backtick_before_slash_is_not_a_command(tmp_path):
    page = "`llmfit`/btop matter most, and `/fake-cmd arg` is a command.\n"
    assert run(tmp_path, page, "nothing") == {"/fake-cmd"}
