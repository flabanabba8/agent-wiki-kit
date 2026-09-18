"""Hermes Agent adapter for the agent-wiki-kit wiki (installed by scripts/agents/hermes/setup.sh).

Hermes plugins are user-level, so every callback first checks that the session is inside this
repository and otherwise does nothing. The rules themselves live in scripts/hooks/ and are shared
with Claude Code, Codex and OpenCode through scripts/agents/shared.py.
"""
import importlib.util
import os

_HERE = os.path.dirname(os.path.realpath(__file__))


def _find_shared():
    """setup.sh symlinks this directory into ~/.hermes/plugins/, so realpath normally leads back to
    the repository. A copied install (or `hermes plugins doctor`, which copies into a temporary
    home) needs AGENT_WIKI_KIT_REPO or the repo.path file that setup.sh writes beside this file."""
    roots = [os.path.join(_HERE, "..", "..", "..", "..")]
    if os.environ.get("AGENT_WIKI_KIT_REPO"):
        roots.append(os.environ["AGENT_WIKI_KIT_REPO"])
    try:
        roots.append(open(os.path.join(_HERE, "repo.path"), encoding="utf-8").read().strip())
    except OSError:
        pass
    for root in roots:
        candidate = os.path.join(root, "scripts", "agents", "shared.py")
        if os.path.exists(candidate):
            return candidate
    return None


shared = None
_path = _find_shared()
if _path:
    _spec = importlib.util.spec_from_file_location("agent_wiki_kit_shared", _path)
    shared = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(shared)

WRITE_TOOLS = {"write_file", "patch"}
FETCH_TOOLS = {"web_extract"}


def guard_raw(tool_name, args, task_id="", **kwargs):
    """pre_tool_call: block edits to an existing raw/ source. The path decides, not the cwd, so
    the rule holds even when Hermes was started elsewhere and reaches into this repo."""
    if shared is None or tool_name not in WRITE_TOOLS:  # repo not found: stay out of the way
        return None
    reason = shared.blocked_reason(shared.candidate_paths(args), kwargs.get("cwd"))
    return {"action": "block", "message": reason} if reason else None


def camoufox_fallback(tool_name, args, result, task_id="", **kwargs):
    """transform_tool_result: when web_extract came back empty, blocked or as a JavaScript shell,
    render the page in Camoufox and append where the real text was saved."""
    if shared is None or tool_name not in FETCH_TOOLS or not shared.inside_repo(kwargs.get("cwd")):
        return None
    failed = kwargs.get("status") not in (None, "ok", "success") or bool(kwargs.get("error_type"))
    notices = [n for n in (shared.camoufox_notice(u, result or "", failed=failed, tool="web_extract")
                           for u in shared.urls_from(args)[:3]) if n]
    return (result or "") + "\n\n" + "\n\n".join(notices) if notices else None


def turn_context(is_first_turn=False, **kwargs):
    """pre_llm_call: harness health on the first turn, and the log reminder whenever wiki pages
    changed without a wiki/log.md entry (Claude Code enforces that one at Stop)."""
    if shared is None or not shared.inside_repo(kwargs.get("cwd")):
        return None
    parts = [shared.session_banner()] if is_first_turn else []
    parts.append(shared.unlogged_wiki_changes())
    text = "\n".join(p for p in parts if p)
    return {"context": text} if text else None


def register(ctx):
    ctx.register_hook("pre_tool_call", guard_raw)
    ctx.register_hook("transform_tool_result", camoufox_fallback)
    ctx.register_hook("pre_llm_call", turn_context)
