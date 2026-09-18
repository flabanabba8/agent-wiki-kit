#!/usr/bin/env python
"""Index wiki/ markdown pages into the mem0 'wiki' vector store for semantic search (reason 1).

Incremental: a manifest tracks each page's content hash + the memory ids it produced, so
unchanged pages are skipped, edited pages are re-synced, and deleted pages are pruned.
Pages are stored as raw chunks with infer=False (no LLM extraction) — this is a document
index, not conversational memory, so it needs no API key.

Information richness — the index is built to be as rich as the wiki page it mirrors, not a
bag of bare blobs (contextual-retrieval style):
  * YAML frontmatter is fully parsed (type, aliases, related, confidence, last_verified).
  * Chunking is SECTION-AWARE — each chunk knows its heading trail ("Section > Subsection").
  * A CONTEXT HEADER (title - tldr, [type], section, aliases) is prepended to every chunk
    before embedding, so each vector self-describes like a mini wiki entry and recall works
    even on a chunk pulled from the middle of a page.
  * Chunk size fits all-MiniLM's 256-token budget alongside that header (no silent tail loss).
  * Each chunk carries the full metadata set, so query results show type/section/related.

Usage:
  scripts/mem0/index_wiki.py            # incremental sync
  scripts/mem0/index_wiki.py --rebuild  # wipe + reindex everything (needed after format changes)
"""
import argparse
import hashlib
import json
import os
import re
import shutil

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import REPO_ROOT, DATA_DIR, get_memory, store_lock, close_memory, EMBED_MODEL, EMBED_DIMS  # noqa: E402

try:
    import yaml
except ImportError:
    yaml = None

WIKI_DIR = os.path.join(REPO_ROOT, "wiki")
MANIFEST = os.path.join(DATA_DIR, "wiki-manifest.json")
# Records the embedder the store was built with. A vector store is only coherent under one
# embedding model + dimensionality; swapping WIKI_MEM0_EMBED_MODEL/DIMS silently mixes
# incompatible vectors. We stamp it here and auto-force --rebuild on mismatch (footgun fix).
STAMP = os.path.join(DATA_DIR, "index-meta.json")
USER_ID = "wiki"
# all-MiniLM-L6-v2 truncates at 256 tokens (~190 words). The context header eats ~30-50 words,
# so cap body chunks low enough that header+chunk embeds without losing the tail.
CHUNK_WORDS = 150

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")


def parse(md):
    """Return (frontmatter_dict, body). Robust YAML parse; falls back to {} on bad/missing FM."""
    m = FM_RE.match(md)
    if not m:
        return {}, md
    fm = {}
    if yaml is not None:
        try:
            loaded = yaml.safe_load(m.group(1))
            if isinstance(loaded, dict):
                fm = loaded
        except yaml.YAMLError:
            fm = {}
    else:  # minimal fallback: scalar k: v only
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t", "-")):
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, md[m.end():]


def _norm_list(v):
    if v is None:
        return []
    if isinstance(v, str):
        return [v] if v.strip() else []
    return [str(x) for x in v if str(x).strip()]


def segments(body):
    """Yield (section_label, text) blocks split on markdown headings.

    section_label is the heading trail, e.g. "Tools > inject_turn". Text before the first
    heading is labelled "" (intro). Fenced code blocks are passed through untouched.
    """
    stack = []  # (level, title)
    buf = []
    in_fence = False

    def label():
        return " > ".join(t for _, t in stack)

    cur = ""
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            buf.append(line)
            continue
        h = None if in_fence else HEADING_RE.match(line)
        if h:
            if any(s.strip() for s in buf):
                yield cur, "\n".join(buf).strip()
            buf = []
            level = len(h.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, h.group(2).strip()))
            cur = label()
        else:
            buf.append(line)
    if any(s.strip() for s in buf):
        yield cur, "\n".join(buf).strip()


def section_chunks(body):
    """Yield (section_label, chunk_text), sub-chunking long sections to CHUNK_WORDS."""
    for label, text in segments(body):
        words = text.split()
        if not words:
            continue
        for i in range(0, len(words), CHUNK_WORDS):
            yield label, " ".join(words[i:i + CHUNK_WORDS])


def context_header(fm, title, tldr, section, aliases):
    """Short self-describing preamble prepended to a chunk before embedding."""
    typ = str(fm.get("type", "")).strip()
    head = f"[{typ}] {title}" if typ else title
    if tldr:
        head += f" — {tldr}"
    parts = [head]
    if section:
        parts.append(f"Section: {section}")
    if aliases:
        parts.append("Aliases: " + ", ".join(aliases))
    return "\n".join(parts)


def load_stamp():
    if os.path.exists(STAMP):
        try:
            with open(STAMP) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def save_stamp():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STAMP, "w") as f:
        json.dump({"embed_model": EMBED_MODEL, "embed_dims": EMBED_DIMS}, f, indent=2)


def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            return json.load(f)
    return {}


def save_manifest(man):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MANIFEST, "w") as f:
        json.dump(man, f, indent=2)


def delete_ids(mem, ids):
    for mid in ids:
        try:
            mem.delete(memory_id=mid)
        except Exception:
            pass


def _main_locked():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()

    # Embedder-swap guard: if the store was built with a different embed model/dims than the
    # current config, the vectors are incompatible — force a clean rebuild instead of mixing
    # them. A missing stamp (first run after this upgrade) is NOT treated as a mismatch: the
    # existing store is assumed to match the current default, and we just stamp it below.
    prev = load_stamp()
    cur = {"embed_model": EMBED_MODEL, "embed_dims": EMBED_DIMS}
    if not args.rebuild and prev is not None and prev != cur:
        print(f"[mem0] embedder changed {prev} -> {cur}; forcing --rebuild for a coherent index")
        args.rebuild = True

    if args.rebuild:
        # mem0 2.x delete_all() is paginated/capped (it deletes only ~a page of vectors per
        # call, not all of them), so it cannot reliably clear the store and leaves stale
        # vectors behind. The store is a derived cache rebuildable from wiki/, so wipe the
        # namespace dir + manifest on disk for a deterministic rebuild; get_memory recreates
        # it empty. (Wipe BEFORE constructing Memory — embedded Qdrant locks the path.)
        shutil.rmtree(os.path.join(DATA_DIR, USER_ID), ignore_errors=True)
        if os.path.exists(MANIFEST):
            os.remove(MANIFEST)

    mem = get_memory(USER_ID)
    import atexit; atexit.register(close_memory, mem)
    man = {} if args.rebuild else load_manifest()

    pages = []
    for root, _, files in os.walk(WIKI_DIR):
        for fn in files:
            # Monthly logs (wiki/log.md, wiki/log-YYYY-MM.md) are history, not knowledge: indexing them let
            # old entries outrank current pages in search, so they are left out.
            if fn.endswith(".md") and not (os.path.abspath(root) == os.path.abspath(WIKI_DIR) and fn.startswith("log")):
                pages.append(os.path.join(root, fn))

    seen, changed, skipped = set(), 0, 0
    for path in sorted(pages):
        rel = os.path.relpath(path, REPO_ROOT)
        seen.add(rel)
        raw = open(path).read()
        sha = hashlib.sha256(raw.encode()).hexdigest()
        if man.get(rel, {}).get("sha") == sha:
            skipped += 1
            continue
        delete_ids(mem, man.get(rel, {}).get("ids", []))  # remove stale vectors
        fm, body = parse(raw)
        title = str(fm.get("title", os.path.basename(path)))
        tldr = str(fm.get("tldr", ""))
        aliases = _norm_list(fm.get("aliases"))
        related = _norm_list(fm.get("related"))
        base_meta = {
            "path": rel,
            "title": title,
            "tldr": tldr,
            "type": str(fm.get("type", "")),
            "aliases": aliases,
            "related": related,
            "confidence": str(fm.get("confidence", "")),
            "last_verified": str(fm.get("last_verified", "")),
        }
        ids = []
        for idx, (section, ch) in enumerate(section_chunks(body)):
            header = context_header(fm, title, tldr, section, aliases)
            text = f"{header}\n\n{ch}"  # contextual-retrieval: embed identity + section + chunk
            meta = dict(base_meta, section=section, chunk=idx)
            res = mem.add(text, user_id=USER_ID, metadata=meta, infer=False)
            for r in (res.get("results") if isinstance(res, dict) else []) or []:
                if r.get("id"):
                    ids.append(r["id"])
        man[rel] = {"sha": sha, "ids": ids}
        changed += 1
        print(f"  synced {rel} ({len(ids)} chunks)")

    for rel in [r for r in man if r not in seen]:  # prune deleted pages
        delete_ids(mem, man[rel].get("ids", []))
        del man[rel]
        print(f"  pruned {rel}")

    save_manifest(man)
    save_stamp()  # record the embedder this store was built with (embedder-swap guard)
    print(f"\nDone. {changed} synced, {skipped} unchanged, {len(man)} pages indexed.")


def main():
    # Hold the turnstile for the whole run: other agents wait instead of crashing on Qdrant's lock.
    with store_lock(USER_ID):
        return _main_locked()

if __name__ == "__main__":
    main()
