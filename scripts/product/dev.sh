#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

runtime_dir="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
artifact_dir="$runtime_dir/artifacts"
mkdir -p "$artifact_dir"

python_bin=""
if command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
elif command -v python >/dev/null 2>&1; then
  python_bin="python"
else
  echo "product-dev: Python is required" >&2
  exit 1
fi

"$python_bin" -m intentos.cli data/youtube/sample_watch_history.json > "$artifact_dir/youtube-summary.txt"
"$python_bin" -m intentos.cli data/youtube/sample_watch_history.json --json > "$artifact_dir/youtube-summary.json"

echo "product-dev: wrote $artifact_dir/youtube-summary.txt"
echo "product-dev: wrote $artifact_dir/youtube-summary.json"
echo "product-dev: latest summary"
cat "$artifact_dir/youtube-summary.txt"
