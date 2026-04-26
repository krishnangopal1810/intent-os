#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

run() {
  echo "+ $*"
  "$@"
}

has_script() {
  local script="$1"
  command -v node >/dev/null 2>&1 || return 1
  node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts['$script'] ? 0 : 1)"
}

npm_runner() {
  if [ -f pnpm-lock.yaml ] && command -v pnpm >/dev/null 2>&1; then
    echo "pnpm"
  elif [ -f yarn.lock ] && command -v yarn >/dev/null 2>&1; then
    echo "yarn"
  elif [ -f bun.lockb ] && command -v bun >/dev/null 2>&1; then
    echo "bun"
  elif command -v npm >/dev/null 2>&1; then
    echo "npm"
  else
    echo ""
  fi
}

run scripts/harness/check.sh
run scripts/harness/lint.py

product_specified=false
if grep -q '^# Product Brief: IntentOS' docs/product/BRIEF.md; then
  product_specified=true
fi

product_checks=0

if [ -f package.json ]; then
  runner="$(npm_runner)"
  if [ -z "$runner" ]; then
    echo "verify: package.json found, but no JS package runner is available"
    exit 1
  fi

  for script in lint test build; do
    if has_script "$script"; then
      product_checks=$((product_checks + 1))
      case "$runner" in
        pnpm) run pnpm "$script" ;;
        yarn) run yarn "$script" ;;
        bun) run bun run "$script" ;;
        npm) run npm run "$script" ;;
      esac
    else
      echo "verify: skipped npm script '$script' (not defined)"
    fi
  done
else
  echo "verify: skipped JS checks (no package.json)"
fi

if [ -f pyproject.toml ] || [ -f setup.py ] || [ -f requirements.txt ]; then
  if command -v ruff >/dev/null 2>&1; then
    product_checks=$((product_checks + 1))
    run ruff check .
  else
    echo "verify: skipped ruff (not installed)"
  fi

  if [ -d tests ]; then
    product_checks=$((product_checks + 1))
    if command -v python3 >/dev/null 2>&1; then
      run python3 -m pytest
    elif command -v python >/dev/null 2>&1; then
      run python -m pytest
    else
      echo "verify: Python project detected, but no python executable is available"
      exit 1
    fi
  else
    echo "verify: skipped pytest (no tests directory)"
  fi
else
  echo "verify: skipped Python checks (no Python project files)"
fi

if [ -f Cargo.toml ]; then
  if command -v cargo >/dev/null 2>&1; then
    product_checks=$((product_checks + 1))
    run cargo test
  else
    echo "verify: Cargo project detected, but cargo is unavailable"
    exit 1
  fi
else
  echo "verify: skipped Rust checks (no Cargo.toml)"
fi

if [ -f go.mod ]; then
  if command -v go >/dev/null 2>&1; then
    product_checks=$((product_checks + 1))
    run go test ./...
  else
    echo "verify: Go project detected, but go is unavailable"
    exit 1
  fi
else
  echo "verify: skipped Go checks (no go.mod)"
fi

if [ -x scripts/product/verify.sh ]; then
  product_checks=$((product_checks + 1))
  run scripts/product/verify.sh
fi

if [ "$product_specified" = true ] && [ "$product_checks" -eq 0 ]; then
  echo "verify: product brief exists, but no product verification path is configured" >&2
  echo "verify: add product code plus tests, or provide scripts/product/verify.sh" >&2
  exit 1
fi

echo "verify: ok"
