#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

runtime_dir="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
port="${INTENTOS_APP_PORT:-8765}"

if [ ! -f "$runtime_dir/site/index.html" ]; then
  echo "product-start-ui: missing $runtime_dir/site/index.html; run scripts/product/dev.sh first" >&2
  exit 2
fi

cd "$runtime_dir"
echo "product-start-ui: serving http://127.0.0.1:$port/site/index.html"
exec python3 -m http.server "$port" --bind 127.0.0.1
