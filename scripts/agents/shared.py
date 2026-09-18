"""Agent-neutral helpers behind the Codex, OpenCode and Hermes adapters.

Claude Code enforces this repo's rules with hooks in .claude/settings.json. Other agents have
their own hook systems with different payloads, so each adapter translates its payload and then
calls the SAME rule scripts Claude Code uses: scripts/hooks/guard-raw.sh (never edit an existing
raw/ source) and scripts/hooks/webfetch_camoufox_fallback.py (re-render pages a fetch tool could
not read). One rule, one message, four agents. Standard library only.
"""
import os
import re
import subprocess
import tempfile

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
GUARD = os.path.join(REPO, "scripts", "hooks", "guard-raw.sh")
FALLBACK = os.path.join(REPO, "scripts", "hooks", "webfetch_camoufox_fallback.py")
SESSION_START = os.path.join(REPO, "scripts", "hooks", "session-start.sh")
LOG_CHECK = os.path.join(REPO, "scripts", "hooks", "stop-anti-evaporation.sh")
PY = os.path.join(REPO, ".venv", "bin", "python")

PATH_KEYS = ("path", "file_path", "filePath", "filepath", "notebook_path", "target_file", "file")
URL_KEYS = ("url", "urls", "uri", "link")
# V4A patch headers, used by Codex's apply_patch and by Hermes's and OpenCode's patch tools.
PATCH_HEADER = re.compile(r"^\*\*\* (?:Update|Delete) File: (.+?)\s*$", re.M)
MOVE_HEADER = re.compile(r"^\*\*\* Move to: (.+?)\s*$", re.M)


def inside_repo(cwd=None):
    """True when the agent is working in this repository. Adapters installed at user level
    (Hermes) see every project, so they must stay silent everywhere else."""
    cwd = os.path.realpath(cwd or os.getcwd())
    return cwd == REPO or cwd.startswith(REPO + os.sep)


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _strings(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)


def candidate_paths(args):
    """Every file a write-type tool call would modify: explicit path arguments plus the files
    named in a V4A patch body. Creating files is never blocked, so 'Add File' is ignored."""
    found = []
    if not isinstance(args, dict):
        return found
    for key in PATH_KEYS:
        v = args.get(key)
        if isinstance(v, str) and v.strip():
            found.append(v.strip())
    for text in _strings(args):
        if "*** " in text:
            found += PATCH_HEADER.findall(text) + MOVE_HEADER.findall(text)
    return list(dict.fromkeys(found))


def blocked_reason(paths, cwd=None):
    """Ask guard-raw.sh. Returns its message when any path is an existing raw/ source, else None."""
    cwd = cwd or os.getcwd()
    argv = []
    for p in paths:
        # Relative paths are relative to the agent's cwd, and may climb out of it (../raw/x.md).
        argv += ["--path", os.path.realpath(p if os.path.isabs(p) else os.path.join(cwd, p))]
    if not argv:
        return None
    r = subprocess.run(["bash", GUARD] + argv, cwd=REPO, capture_output=True, text=True, timeout=10)
    return (r.stderr.strip() or "BLOCKED: existing raw/ source.") if r.returncode == 2 else None


def urls_from(args):
    out = []
    if isinstance(args, dict):
        for key in URL_KEYS:
            for s in _strings(args.get(key)):
                if re.match(r"https?://", s):
                    out.append(s)
    return list(dict.fromkeys(out))


def camoufox_notice(url, result_text="", failed=False, tool="web fetch", timeout=170):
    """Run the shared fallback. Returns the notice to show the model, or '' when the fetch was fine."""
    if not (os.path.exists(PY) and os.path.exists(FALLBACK)):
        return ""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(result_text or "")
        path = f.name
    try:
        argv = [PY, FALLBACK, "--url", url, "--result-file", path, "--tool", tool] + (["--failed"] if failed else [])
        r = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""  # a broken fallback must never break the agent's fetch
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def session_banner():
    """Harness health plus the hot-cache pointer, the text Claude Code gets at SessionStart."""
    try:
        r = subprocess.run(["bash", SESSION_START], cwd=REPO, capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    except Exception:
        return ""


def unlogged_wiki_changes():
    """The anti-evaporation rule: wiki pages changed but wiki/log.md did not. Returns the reminder or ''."""
    try:
        r = subprocess.run(["bash", LOG_CHECK], cwd=REPO, input="{}", capture_output=True, text=True, timeout=10)
        return r.stderr.strip() if r.returncode == 2 else ""
    except Exception:
        return ""
