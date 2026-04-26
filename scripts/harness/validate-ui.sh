#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [ -x scripts/product/validate-ui.sh ]; then
  exec scripts/product/validate-ui.sh
fi

if [ -f package.json ] && command -v node >/dev/null 2>&1 && node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts['validate:ui'] ? 0 : 1)"; then
  exec npm run validate:ui
fi

echo "validate-ui: no UI validation configured" >&2
echo "validate-ui: add scripts/product/validate-ui.sh or an npm validate:ui script once a UI exists" >&2
exit 2
