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
  "docs/product/spec-template.md"
  "docs/ARCHITECTURE.md"
  "docs/DESIGN.md"
  "docs/SECURITY.md"
  "docs/RELIABILITY.md"
  "docs/QUALITY.md"
  "docs/HARNESS_AUDIT.md"
  "docs/APP_RUNTIME.md"
  "docs/OPERATING_MODEL.md"
  "docs/plans/README.md"
  "docs/plans/templates/exec-plan.md"
  "docs/decisions/README.md"
  "docs/references/README.md"
)

required_dirs=(
  "docs/plans/active"
  "docs/plans/completed"
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
  local file line_no links link target base_dir target_path

  while IFS= read -r file; do
    base_dir="$(dirname "$file")"
    line_no=0
    while IFS= read -r line; do
      line_no=$((line_no + 1))
      links="$(printf '%s\n' "$line" | grep -Eo '\[[^]]+\]\([^)]+\)' || true)"
      [ -n "$links" ] || continue

      while IFS= read -r link; do
        target="$(printf '%s\n' "$link" | sed -E 's/^.*\]\(([^)]+)\).*$/\1/')"
        target="${target%%#*}"
        [ -n "$target" ] || continue
        case "$target" in
          http://* | https://* | mailto:* | /*)
            continue
            ;;
        esac

        target_path="$base_dir/$target"
        if [ ! -e "$target_path" ]; then
          fail "$file:$line_no has broken markdown link: $target"
        fi
      done <<< "$links"
    done < "$file"
  done < <(find . -path './.git' -prune -o -path './.harness' -prune -o -type f -name '*.md' -print)
}

check_markdown_links

plan_count=0
while IFS= read -r -d '' plan; do
  plan_count=$((plan_count + 1))
  for heading in "## Goal" "## Scope" "## Non-Goals" "## Acceptance Criteria" "## Verification" "## Progress Log"; do
    if ! grep -q "^$heading$" "$plan"; then
      fail "$plan is missing required heading: $heading"
    fi
  done
done < <(find docs/plans/active -type f -name '*.md' -print0)

echo "harness-check: ok ($plan_count active plan(s) checked)"
