#!/usr/bin/env bash
# Install the mem0 wiki-integration deps into the project .venv.
# Local-first: no API keys required to build or query the semantic index.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

REQ="scripts/mem0/requirements.txt"
if command -v uv >/dev/null 2>&1; then
  # uv-managed venv (no pip inside) — the layout this repo uses.
  # --torch-backend cpu forces the CPU torch wheel, avoiding the ~2GB CUDA/nvidia stack.
  [ -d .venv ] || uv venv .venv
  uv pip install --python .venv/bin/python --torch-backend cpu -r "$REQ"
elif [ -x ./.venv/bin/pip ]; then
  ./.venv/bin/pip install --upgrade pip >/dev/null
  ./.venv/bin/pip install -r "$REQ"
else
  [ -d .venv ] || python3 -m venv .venv
  ./.venv/bin/python -m ensurepip --upgrade
  ./.venv/bin/python -m pip install -r "$REQ"
fi

# Vendor the embedding model now (online) so runtime can stay fully offline.
echo "Fetching embedding model (one-time, ~90MB)…"
HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 ./.venv/bin/python -c \
  "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" \
  2>/dev/null && echo "  model cached." || echo "  (warmup skipped — first index will fetch it; unset HF_HUB_OFFLINE if so)"

cat <<'EOF'

mem0 integration installed. Next steps:
  ./.venv/bin/python scripts/mem0/index_wiki.py          # build the semantic index
  ./.venv/bin/python scripts/mem0/query_wiki.py 'hooks'  # test a query

First index run downloads the embedding model (~80MB) once, then runs fully offline.
Hot-recall MCP server (scripts/mem0/mcp_server.py) is wired in .mcp.json; approve it when you next run claude here.
EOF
