#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

usage() {
  echo "usage: $0 short-slug" >&2
  exit 2
}

[ "$#" -eq 1 ] || usage

slug="$1"
case "$slug" in
  *[!a-z0-9-]* | "" | -* | *-)
    echo "new-plan: slug must use lowercase letters, numbers, and hyphens" >&2
    exit 2
    ;;
esac

date_utc="$(date -u +%Y-%m-%d)"
target="docs/plans/active/${date_utc}-${slug}.md"
template="docs/plans/templates/exec-plan.md"

[ -f "$template" ] || {
  echo "new-plan: missing template: $template" >&2
  exit 1
}

if [ -e "$target" ]; then
  echo "new-plan: plan already exists: $target" >&2
  exit 1
fi

sed \
  -e "s/{{SLUG}}/$slug/g" \
  -e "s/{{DATE}}/$date_utc/g" \
  "$template" > "$target"

echo "$target"
