#!/usr/bin/env python3
"""One command line behind every non-Claude adapter. Reads a JSON object on stdin.

  adapter.py guard          {"args": {...}, "cwd": "..."}            exit 2 + reason on stderr if blocked
  adapter.py fetch-notice   {"args": {...}, "result": "...", "failed": false, "tool": "webfetch", "cwd": "..."}
                                                                    prints the Camoufox notice, or nothing
  adapter.py banner         {"cwd": "..."}                          prints harness health for a new session
  adapter.py log-reminder   {"cwd": "..."}                          prints the reminder when wiki pages changed
                                                                    without a wiki/log.md entry

The OpenCode plugin (.opencode/plugins/agent-wiki-kit.js) and the Codex hooks call this; the Hermes
plugin imports scripts/agents/shared.py directly. Standard library only, so plain python3 runs it.
Every mode except `guard` exits 0 whatever happens: a broken adapter must never break the agent.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import shared  # noqa: E402


def main(argv):
    mode = argv[0] if argv else ""
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    cwd = data.get("cwd") or os.getcwd()
    # OpenCode and Hermes callers send {"args": ...}; Codex sends its Claude-style hook payload, where the
    # arguments are under "tool_input" (for apply_patch: {"command": "<patch text>"}, no file_path).
    args = data.get("args") or data.get("tool_input") or {}

    if mode == "guard":
        reason = shared.blocked_reason(shared.candidate_paths(args), cwd)
        if reason:
            print(reason, file=sys.stderr)
            return 2
        return 0
    if not shared.inside_repo(cwd):
        return 0
    if mode == "fetch-notice":
        for url in shared.urls_from(args)[:3]:
            notice = shared.camoufox_notice(url, data.get("result") or "", failed=bool(data.get("failed")),
                                            tool=data.get("tool") or "web fetch")
            if notice:
                print(notice)
    elif mode == "banner":
        print(shared.session_banner())
    elif mode == "log-reminder":
        print(shared.unlogged_wiki_changes())
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # guard fails open too: the Claude Code hook has the same policy
        print(f"agent-wiki-kit adapter error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(0)
