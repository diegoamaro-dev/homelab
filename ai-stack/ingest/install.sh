#!/usr/bin/env bash
# One-shot venv setup + dependency install.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -d venv ]; then
  python3 -m venv venv
fi

. venv/bin/activate
pip install --upgrade pip wheel
# torch comes in as a sentence-transformers transitive dep; CPU build is fine
# on this Zen 4 host. Pinning torch to the cpu-only wheel avoids the ~3 GB
# CUDA download.
pip install --extra-index-url https://download.pytorch.org/whl/cpu \
            "torch<3" \
            -r requirements.txt

echo "==> install complete"
echo "    venv: $ROOT/venv"
echo "    cli:  $ROOT/bin/ingest"
