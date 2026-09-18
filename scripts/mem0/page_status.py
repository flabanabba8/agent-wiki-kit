"""Page-status helpers shared by query_wiki.py and wiki-eval.py.

Why: a page marked `status: deprecated` keeps its content, so it still matches queries and
can outrank its replacement. Status is read from the page file at query time rather than from index
metadata, so deprecating a page takes effect immediately without a reindex.
"""
import os
import re

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_cache = {}


def is_deprecated(path: str) -> bool:
    if path not in _cache:
        full = path if os.path.isabs(path) else os.path.join(_REPO, path)
        try:
            head = open(full, encoding="utf-8").read(4000)
            fm = head.split("\n---", 1)[0] if head.startswith("---") else ""
            _cache[path] = bool(re.search(r"^status:\s*deprecated\b", fm, re.M))
        except OSError:
            _cache[path] = False
    return _cache[path]


def demote_deprecated(paths):
    """Stable reorder: current pages first, deprecated pages after, each group in score order."""
    return [p for p in paths if not is_deprecated(p)] + [p for p in paths if is_deprecated(p)]
