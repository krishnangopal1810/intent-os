#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python_bin=""
if command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
elif command -v python >/dev/null 2>&1; then
  python_bin="python"
else
  echo "product-verify: Python is required" >&2
  exit 1
fi

echo "+ $python_bin -m unittest discover -s tests"
"$python_bin" -m unittest discover -s tests

echo "+ $python_bin -m intentos.cli data/youtube/sample_watch_history.json"
"$python_bin" -m intentos.cli data/youtube/sample_watch_history.json
