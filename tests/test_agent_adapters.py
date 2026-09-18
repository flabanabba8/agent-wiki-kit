"""The rules Claude Code enforces with hooks must hold in Codex, OpenCode and Hermes too.

Each agent has its own hook payload, so each adapter translates and then calls the same rule
scripts. These tests cover the shared translation layer and the Hermes plugin callbacks. They use
the standard library only, so they run in CI.
"""
import os

from conftest import REPO, load

shared = load("agent_wiki_kit_shared_t", "scripts/agents/shared.py")
hermes = load("agent_wiki_kit_hermes_t", "scripts/agents/hermes/agent-wiki-kit/__init__.py")

# raw/ is not distributed, but raw/README.md always exists, and it is an existing file under raw/.
EXISTING_RAW = "raw/README.md"
V4A = "*** Begin Patch\n*** Update File: {}\n@@\n-old\n+new\n*** End Patch\n"


def test_explicit_path_arguments_are_found_under_every_agents_key_name():
    for key in ("path", "file_path", "filePath"):
        assert shared.candidate_paths({key: "a/b.md"}) == ["a/b.md"]


def test_paths_inside_a_patch_body_are_found():
    body = V4A.format("raw/x.md") + "*** Delete File: raw/y.md\n*** Add File: raw/new.md\n"
    found = shared.candidate_paths({"input": body})
    assert "raw/x.md" in found and "raw/y.md" in found
    assert "raw/new.md" not in found, "creating a raw file is allowed, so Add File is not a target"


def test_existing_raw_source_is_blocked_with_the_shared_message():
    reason = shared.blocked_reason([EXISTING_RAW], cwd=REPO)
    assert reason and "immutable" in reason


def test_new_raw_file_and_ordinary_files_are_allowed():
    assert shared.blocked_reason(["raw/docs/never-existed-before.md"], cwd=REPO) is None
    assert shared.blocked_reason(["wiki/index.md"], cwd=REPO) is None
    assert shared.blocked_reason([], cwd=REPO) is None


def test_absolute_path_into_the_repo_is_blocked_from_any_cwd(tmp_path):
    assert shared.blocked_reason([os.path.join(REPO, EXISTING_RAW)], cwd=str(tmp_path))


def test_relative_raw_path_in_another_project_is_not_our_business(tmp_path):
    other = tmp_path / "raw"
    other.mkdir()
    (other / "notes.md").write_text("x")
    assert shared.blocked_reason(["raw/notes.md"], cwd=str(tmp_path)) is None


def test_dot_dot_routes_into_raw_are_blocked():
    """Found by running the Codex hook from wiki/: ../raw/... used to slip past the prefix match."""
    assert shared.blocked_reason(["../" + EXISTING_RAW], cwd=os.path.join(REPO, "wiki"))
    assert shared.blocked_reason(["wiki/../" + EXISTING_RAW], cwd=REPO)


def test_claude_code_hook_blocks_dot_dot_routes_too():
    import json, subprocess
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": os.path.join(REPO, "wiki", "..", EXISTING_RAW)}})
    r = subprocess.run(["bash", os.path.join(REPO, "scripts/hooks/guard-raw.sh")], input=payload,
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 2, "the Claude Code PreToolUse hook must normalise the path before matching"


def test_symlink_into_raw_is_blocked(tmp_path):
    link = tmp_path / "innocent.md"
    link.symlink_to(os.path.join(REPO, EXISTING_RAW))
    assert shared.blocked_reason([str(link)], cwd=str(tmp_path))


def test_inside_repo(tmp_path):
    assert shared.inside_repo(REPO) and shared.inside_repo(os.path.join(REPO, "wiki"))
    assert not shared.inside_repo(str(tmp_path))


def test_urls_are_found_in_a_string_or_a_list():
    assert shared.urls_from({"url": "https://a.example/x"}) == ["https://a.example/x"]
    assert shared.urls_from({"urls": ["https://a.example", "not a url", "https://b.example"]}) == [
        "https://a.example", "https://b.example"]


def test_hermes_blocks_write_file_and_patch_on_raw_sources():
    for tool, args in (("write_file", {"path": os.path.join(REPO, EXISTING_RAW), "content": "x"}),
                       ("patch", {"patch": V4A.format(os.path.join(REPO, EXISTING_RAW))})):
        out = hermes.guard_raw(tool, args, "task")
        assert out and out["action"] == "block" and out["message"]


def test_hermes_leaves_other_tools_and_other_files_alone():
    assert hermes.guard_raw("terminal", {"command": "ls raw/"}, "t") is None
    assert hermes.guard_raw("write_file", {"path": os.path.join(REPO, "wiki/index.md")}, "t") is None


def test_hermes_plugin_is_silent_outside_this_repository(tmp_path):
    assert hermes.turn_context(is_first_turn=True, cwd=str(tmp_path)) is None
    assert hermes.camoufox_fallback("web_extract", {"urls": ["https://a.example"]}, "", "t", cwd=str(tmp_path)) is None


def test_hermes_only_post_processes_the_fetch_tool():
    assert hermes.camoufox_fallback("read_file", {"path": "x"}, "text", "t", cwd=REPO) is None


def test_hermes_manifest_declares_exactly_the_hooks_it_registers():
    registered = []

    class Ctx:
        def register_hook(self, name, fn):
            registered.append(name)

    hermes.register(Ctx())
    manifest = open(os.path.join(REPO, "scripts/agents/hermes/agent-wiki-kit/plugin.yaml"), encoding="utf-8").read()
    for name in registered:
        assert f"  - {name}" in manifest
    assert len(registered) == 3
