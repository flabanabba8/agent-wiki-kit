"""This repository must stay usable from Claude Code, Codex, OpenCode and Hermes.

Claude Code's files are the source of truth. The other agents read symlinks (instructions, skills)
and generated files (agents, MCP servers, Codex hooks). These tests fail when the two drift apart,
or when a skill is written in a way only some of the agents accept.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

from conftest import REPO


def test_generated_configs_are_up_to_date():
    r = subprocess.run([sys.executable, os.path.join(REPO, "scripts/agents/sync.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, "run ./scripts/agents/sync.py and commit the result:\n" + r.stdout


def test_instructions_and_skills_are_shared_by_symlink():
    """Codex reads only AGENTS.md and .agents/skills; OpenCode and Hermes load the first instruction
    file they find, so a separate AGENTS.md would shadow CLAUDE.md and drift."""
    assert os.path.realpath(os.path.join(REPO, "AGENTS.md")) == os.path.join(REPO, "CLAUDE.md")
    assert os.path.realpath(os.path.join(REPO, ".agents/skills")) == os.path.join(REPO, ".claude/skills")


def test_instructions_fit_codex_default_limit():
    """Codex stops reading project instructions at project_doc_max_bytes, 32 KiB by default, silently."""
    assert os.path.getsize(os.path.join(REPO, "CLAUDE.md")) < 32 * 1024


def test_every_skill_is_valid_for_every_agent():
    """An unquoted value containing ': ' (easy to write in argument-hint) is invalid YAML. Claude Code
    tolerates it and Codex repairs it, but OpenCode silently drops the whole skill."""
    yaml = pytest.importorskip("yaml")
    skills = sorted(glob.glob(os.path.join(REPO, ".claude/skills/*/SKILL.md")))
    assert skills
    for path in skills:
        folder = os.path.basename(os.path.dirname(path))
        text = open(path, encoding="utf-8").read()
        assert text.startswith("---\n"), path
        meta = yaml.safe_load(text.split("---", 2)[1])  # strict YAML, as OpenCode and Hermes parse it
        assert meta["name"] == folder, f"{path}: name must equal its directory (OpenCode, Hermes)"
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", meta["name"]) and len(meta["name"]) <= 64
        assert isinstance(meta["description"], str) and 1 <= len(meta["description"]) <= 1024
        assert not os.path.islink(path), "Codex skips a symlinked SKILL.md file"


def test_generated_codex_files_parse():
    tomllib = pytest.importorskip("tomllib")
    cfg = tomllib.load(open(os.path.join(REPO, ".codex/config.toml"), "rb"))
    servers = json.load(open(os.path.join(REPO, ".mcp.json")))["mcpServers"]
    assert set(cfg["mcp_servers"]) == set(servers)
    for path in glob.glob(os.path.join(REPO, ".codex/agents/*.toml")):
        agent = tomllib.load(open(path, "rb"))
        assert agent["name"] and agent["description"] and agent["developer_instructions"].strip()
    hooks = json.load(open(os.path.join(REPO, ".codex/hooks.json")))["hooks"]
    assert {"SessionStart", "PreToolUse", "Stop", "SessionEnd"} <= set(hooks)
    for groups in hooks.values():
        for group in groups:
            for h in group["hooks"]:
                assert "git rev-parse --show-toplevel" in h["command"], "Codex runs hooks from the session cwd"


def test_opencode_config_matches_claude_code():
    oc = json.load(open(os.path.join(REPO, "opencode.json")))
    servers = json.load(open(os.path.join(REPO, ".mcp.json")))["mcpServers"]
    assert set(oc["mcp"]) == set(servers)
    for s in oc["mcp"].values():
        assert s["type"] == "local" and isinstance(s["command"], list) and "args" not in s
    agents = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(REPO, ".claude/agents/*.md"))}
    assert {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(REPO, ".opencode/agents/*.md"))} == agents


@pytest.mark.skipif(not shutil.which("node"), reason="node is not installed")
def test_opencode_plugin_enforces_the_same_rules():
    r = subprocess.run(["node", os.path.join(REPO, "tests/opencode_plugin_check.mjs")], capture_output=True,
                       text=True, env=dict(os.environ, NODE_NO_WARNINGS="1"), timeout=120)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert "immutable" in out["editExistingRaw"] and "immutable" in out["patchExistingRaw"]
    assert out["writeNewRaw"] is False and out["patchAddRaw"] is False, "ingest must still create raw files"
    assert out["editWiki"] is False and out["readIsIgnored"] is False
    assert out["bannerLines"] == 1, "the health banner is added once per session, not once per message"
