"""scripts/log-archive.py and scripts/build-context-guide.py."""
import datetime as dt

from conftest import load

la = load("log_archive", "scripts/log-archive.py")
bg = load("build_context_guide", "scripts/build-context-guide.py")

LOG = """---
title: Change Log
---

# Change Log

## 2026-10-11 - newer thing

body one

## 2026-09-25 - older thing

body two

## undated heading

kept
"""


def test_old_months_move_and_current_month_stays():
    pre, stay, move = la.plan(LOG, dt.date(2026, 10, 12))
    assert list(move) == ["2026-09"] and len(move["2026-09"]) == 1
    assert [s.split("\n")[0] for s in stay] == ["## 2026-10-11 - newer thing", "## undated heading"]


def test_keep_two_months_keeps_september():
    _, _, move = la.plan(LOG, dt.date(2026, 10, 12), keep=2)
    assert move == {}


def test_cutoff_wraps_year():
    assert la.cutoff(dt.date(2026, 1, 5), 2) == "2025-12"


def test_newest_first_is_stable_and_undated_stays_on_top():
    secs = ["## 2026-09-01 a\n", "## undated\n", "## 2026-10-01 b\n"]
    assert [s.split()[1] for s in la.newest_first(secs)] == ["undated", "2026-10-01", "2026-09-01"]


def test_guide_block_is_bounded_and_replaces_in_place():
    folders = {"a": [f"slug-{i}" for i in range(400)], "b": ["x"]}
    block = bg.compile_block(folders)
    assert len(block) <= bg.MAX_CHARS and "more" in block
    text = "intro\n\n" + block + "\n\n## Page frontmatter\n"
    assert bg.apply(text, bg.compile_block({"a": ["only"]})).count(bg.START) == 1
    assert "slug-399" not in bg.apply(text, bg.compile_block({"a": ["only"]}))


def test_guide_inserts_before_frontmatter_section_the_first_time():
    out = bg.apply("# T\n\n## Where\n\n## Page frontmatter\nx\n", bg.compile_block({"a": ["p"]}))
    assert out.index(bg.START) < out.index("## Page frontmatter")
