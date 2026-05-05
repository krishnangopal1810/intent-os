#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

fail() {
  echo "harness-check: $*" >&2
  exit 1
}

require_file() {
  [ -f "$1" ] || fail "missing required file: $1"
}

require_dir() {
  [ -d "$1" ] || fail "missing required directory: $1"
}

required_files=(
  "AGENTS.md"
  "README.md"
  "docs/README.md"
  "docs/agent-workflow.md"
  "docs/product/BRIEF.md"
  "docs/product/imports.md"
  "docs/product/live-capture.md"
  "docs/product/on-device-inference.md"
  "docs/product/spec-template.md"
  "docs/ARCHITECTURE.md"
  "docs/architecture/long-term-plan.md"
  "docs/architecture/long-term-plan.json"
  "docs/DESIGN.md"
  "docs/SECURITY.md"
  "docs/RELIABILITY.md"
  "docs/QUALITY.md"
  "docs/HARNESS_AUDIT.md"
  "docs/HARNESS_FEATURES.md"
  "docs/APP_RUNTIME.md"
  "docs/OPERATING_MODEL.md"
  "docs/plans/README.md"
  "docs/plans/parallel/README.md"
  "docs/plans/parallel/macos-live-capture/TRACKER.md"
  "docs/plans/parallel/macos-live-capture/agent-1-capture-core.md"
  "docs/plans/parallel/macos-live-capture/agent-2-browser-redaction.md"
  "docs/plans/parallel/macos-live-capture/agent-3-replay-runtime.md"
  "docs/plans/templates/exec-plan.md"
  "docs/decisions/README.md"
  "docs/references/README.md"
  "docs/references/mac-local-capture-and-inference.md"
  "scripts/harness/check-architecture-plan.py"
)

required_dirs=(
  "docs/architecture"
  "docs/plans/active"
  "docs/plans/completed"
  "docs/plans/parallel"
  "docs/plans/parallel/macos-live-capture"
  "scripts/harness"
)

for file in "${required_files[@]}"; do
  require_file "$file"
done

for dir in "${required_dirs[@]}"; do
  require_dir "$dir"
done

agent_lines="$(wc -l < AGENTS.md | tr -d ' ')"
if [ "$agent_lines" -gt 140 ]; then
  fail "AGENTS.md is $agent_lines lines; keep it at or below 140 lines"
fi

check_markdown_links() {
  python3 - <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path


link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
skip_dirs = {".git", ".harness"}

for path in Path(".").rglob("*.md"):
    if skip_dirs.intersection(path.parts):
        continue
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text().splitlines()
    for line_no, line in enumerate(lines, start=1):
        for target in link_pattern.findall(line):
            target = target.split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "/")):
                continue
            if not (path.parent / target).exists():
                print(
                    f"harness-check: {path}:{line_no} has broken markdown link: {target}",
                    file=sys.stderr,
                )
                raise SystemExit(1)
PY
}

check_markdown_links
python3 scripts/harness/check-architecture-plan.py

plan_count=0
while IFS= read -r -d '' plan; do
  plan_count=$((plan_count + 1))
  for heading in "## Goal" "## Scope" "## Non-Goals" "## Acceptance Criteria" "## Harness Impact" "## Verification" "## Progress Log"; do
    if ! grep -q "^$heading$" "$plan"; then
      fail "$plan is missing required heading: $heading"
    fi
  done
done < <(find docs/plans/active -type f -name '*.md' -print0)

echo "harness-check: ok ($plan_count active plan(s) checked)"
