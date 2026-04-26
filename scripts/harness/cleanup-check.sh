#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

scripts/harness/lint.py
scripts/harness/audit.py
echo "cleanup-check: ok"
