"""Shared mem0 configuration for the wiki — local-first, no API key required for indexing.

Two ISOLATED stores (separate Qdrant paths — the embedded Qdrant takes a single-writer
lock per path, so the wiki index and the hot-recall MCP server must not share one):

  - "wiki": semantic index of wiki/ pages          (reason 1, query_wiki.py / index_wiki.py)
  - "hot" : ephemeral cross-session scratch memory (reason 2, mcp_server.py)

Embeddings run locally via sentence-transformers (HuggingFace) — no Ollama, no OpenAI.
An LLM (Anthropic) is configured but ONLY invoked when a memory is added with infer=True.
Indexing and search use infer=False and never call it, so reason 1 needs no API key.
Set ANTHROPIC_API_KEY to enable fact-extraction on the hot-recall layer.
"""
import contextlib
import os
import logging
import time
import warnings

# Run the embedder fully offline — setup.sh downloads the model once, so queries never need the
# network. Override with HF_HUB_OFFLINE=0 to (re)download.
# mem0 ships PostHog telemetry on by default. This is a local-only index, so turn it off.
os.environ.setdefault("MEM0_TELEMETRY", "false")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
# Quiet the local model load (progress bars / advisory warnings) so CLI output stays clean.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
warnings.filterwarnings("ignore", category=FutureWarning)
# mem0 warns about optional extras (spaCy entity-linking, fastembed BM25); httpx/HF log INFO.
# Pure vector search works without them — silence the noise. Add mem0ai[nlp]+fastembed to enable.
for _noisy in ("mem0", "httpx", "httpcore", "huggingface_hub", "sentence_transformers", "transformers"):
    logging.getLogger(_noisy).setLevel(logging.ERROR)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.environ.get("WIKI_MEM0_DATA", os.path.join(REPO_ROOT, ".mem0-data"))

EMBED_MODEL = os.environ.get("WIKI_MEM0_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBED_DIMS = int(os.environ.get("WIKI_MEM0_EMBED_DIMS", "384"))  # all-MiniLM-L6-v2 -> 384

# A placeholder lets the Anthropic client construct; it is never called under infer=False.
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "indexing-needs-no-key")
LLM_MODEL = os.environ.get("WIKI_MEM0_LLM_MODEL", "claude-haiku-4-5")


def build_config(namespace: str) -> dict:
    return {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": namespace,
                "path": os.path.join(DATA_DIR, namespace),
                "embedding_model_dims": EMBED_DIMS,
                "on_disk": True,
            },
        },
        "embedder": {
            "provider": "huggingface",
            "config": {"model": EMBED_MODEL},
        },
        "llm": {
            "provider": "anthropic",
            "config": {"model": LLM_MODEL, "api_key": ANTHROPIC_KEY},
        },
        "history_db_path": os.path.join(DATA_DIR, "history.db"),
    }


# ── Sharing the stores between agents ────────────────────────────────────────────────────
# Embedded Qdrant takes an EXCLUSIVE, NON-BLOCKING lock on the store path, so a second process
# (another Claude Code session, Codex, OpenCode, Hermes, a hook, the weekly cron job) crashes
# with "Storage folder ... is already accessed by another instance of Qdrant client" if anyone
# else has it open. Nothing here needs the store for long, so every caller takes a blocking
# turnstile lock, opens the store, does one operation and closes the client again. A second
# agent then waits a moment instead of failing. No Qdrant server needed.
LOCK_WAIT_S = float(os.environ.get("WIKI_MEM0_LOCK_WAIT", "120"))


class StoreBusy(RuntimeError):
    """Another process held the store for longer than the caller was willing to wait."""


@contextlib.contextmanager
def store_lock(namespace: str, wait: float = None):
    """Hold the cross-process turnstile for one store. Standard library only."""
    wait = LOCK_WAIT_S if wait is None else wait
    os.makedirs(DATA_DIR, exist_ok=True)
    # Beside the namespace directory, not inside it: index_wiki.py --rebuild deletes that directory.
    path = os.path.join(DATA_DIR, f"{namespace}.turnstile")
    try:
        import fcntl
    except ImportError:  # Windows: no flock. Callers fall back to Qdrant's own fail-fast lock.
        yield
        return
    with open(path, "a+") as fh:
        deadline = time.monotonic() + wait
        while True:
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise StoreBusy(
                        f"the '{namespace}' store stayed busy for {wait:g}s (another agent or "
                        f"index_wiki.py is using it). Retry, or raise WIKI_MEM0_LOCK_WAIT."
                    )
                time.sleep(0.2)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def close_memory(mem) -> None:
    """Release embedded Qdrant's path lock so the next process can open the store."""
    try:
        mem.vector_store.client.close()
    except Exception:
        pass


class Store:
    """One store, opened per operation. A long-lived process (the MCP server) keeps the Memory
    object, and with it the loaded embedding model, and only reopens the Qdrant client."""

    def __init__(self, namespace: str):
        self.namespace = namespace
        self._mem = None

    @contextlib.contextmanager
    def session(self, wait: float = None, before_open=None):
        with store_lock(self.namespace, wait):
            if before_open:
                before_open()  # e.g. wipe the namespace directory for a rebuild, safely inside the lock
            if self._mem is None:
                self._mem = get_memory(self.namespace)
            else:
                from qdrant_client import QdrantClient
                self._mem.vector_store.client = QdrantClient(path=os.path.join(DATA_DIR, self.namespace))
            try:
                yield self._mem
            finally:
                close_memory(self._mem)


def open_memory(namespace: str, wait: float = None, before_open=None):
    """`with open_memory("wiki") as mem:` for short-lived scripts."""
    return Store(namespace).session(wait=wait, before_open=before_open)


def get_memory(namespace: str):
    try:
        from mem0 import Memory
    except ImportError as e:
        raise SystemExit(
            f"mem0 not installed ({e}).\nRun: scripts/mem0/setup.sh"
        )
    return Memory.from_config(build_config(namespace))
