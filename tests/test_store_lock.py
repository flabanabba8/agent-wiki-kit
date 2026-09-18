"""The mem0 stores must be shareable between agents.

Why: embedded Qdrant takes an exclusive, non-blocking lock on its path, so a second process
(another Claude Code session, Codex, OpenCode, Hermes, a hook, cron) used to crash with
"Storage folder ... is already accessed by another instance of Qdrant client". config.store_lock
is the blocking turnstile every caller now takes first. These tests need only the standard
library, so they run in CI where mem0 is not installed.
"""
import os
import subprocess
import sys
import time

from conftest import REPO

MEM0_DIR = os.path.join(REPO, "scripts", "mem0")

HOLDER = """
import sys, time
sys.path.insert(0, {mem0_dir!r})
from config import store_lock
with store_lock("t"):
    print("held", flush=True)
    time.sleep({hold})
"""

WAITER = """
import sys, time
sys.path.insert(0, {mem0_dir!r})
from config import store_lock, StoreBusy
t = time.monotonic()
try:
    with store_lock("t", wait={wait}):
        print(f"acquired {{time.monotonic() - t:.2f}}")
except StoreBusy as e:
    print("busy:", e)
    sys.exit(3)
"""


def _env(tmp_path):
    return dict(os.environ, WIKI_MEM0_DATA=str(tmp_path))


def _hold(tmp_path, seconds):
    p = subprocess.Popen([sys.executable, "-c", HOLDER.format(mem0_dir=MEM0_DIR, hold=seconds)],
                         stdout=subprocess.PIPE, text=True, env=_env(tmp_path))
    assert p.stdout.readline().strip() == "held"
    return p


def _wait(tmp_path, wait):
    return subprocess.run([sys.executable, "-c", WAITER.format(mem0_dir=MEM0_DIR, wait=wait)],
                          capture_output=True, text=True, env=_env(tmp_path))


def test_second_process_waits_instead_of_failing(tmp_path):
    holder = _hold(tmp_path, 1.5)
    r = _wait(tmp_path, 15)
    holder.wait()
    assert r.returncode == 0, r.stdout + r.stderr
    assert float(r.stdout.split()[1]) >= 0.5, "the second process did not actually wait for the first"


def test_gives_a_clear_error_when_the_store_stays_busy(tmp_path):
    holder = _hold(tmp_path, 3)
    r = _wait(tmp_path, 0.3)
    holder.kill()
    assert r.returncode == 3
    assert "busy" in r.stdout and "WIKI_MEM0_LOCK_WAIT" in r.stdout


def test_lock_is_released_when_the_holder_dies(tmp_path):
    holder = _hold(tmp_path, 60)
    holder.kill()
    holder.wait()
    r = _wait(tmp_path, 5)
    assert r.returncode == 0, "a crashed agent must not wedge the store"


def test_turnstile_survives_an_index_rebuild(tmp_path):
    """index_wiki.py --rebuild deletes <data>/<namespace>/, so the lock file must sit beside it."""
    _wait(tmp_path, 1)
    assert os.path.exists(os.path.join(tmp_path, "t.turnstile"))
    assert not os.path.exists(os.path.join(tmp_path, "t", "t.turnstile"))
