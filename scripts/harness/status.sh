#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "Repository: $(basename "$ROOT")"
echo

echo "Harness:"
scripts/harness/check.sh
echo

echo "Product brief:"
grep -m 1 '^## Current State' -A 2 docs/product/BRIEF.md | sed 's/^/  /'
echo

echo "Active plans:"
plans="$(find docs/plans/active -type f -name '*.md' | sort)"
if [ -z "$plans" ]; then
  echo "  none"
else
  printf '%s\n' "$plans" | sed 's/^/  /'
fi
echo

echo "Quality:"
grep -m 8 '^| ' docs/QUALITY.md | sed 's/^/  /'
