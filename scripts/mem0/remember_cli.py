#!/usr/bin/env python
"""Store one note in the mem0-hot scratch store from the shell (used by the SessionEnd hook)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import open_memory  # noqa: E402
if len(sys.argv) < 2:
    sys.exit("usage: remember_cli.py 'note text'")
with open_memory("hot") as mem:
    mem.add(" ".join(sys.argv[1:]), user_id="hot", infer=bool(os.environ.get("ANTHROPIC_API_KEY")))
