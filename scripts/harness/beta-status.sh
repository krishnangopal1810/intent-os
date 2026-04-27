#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BETA_DIR=".harness/runtime/beta"
BETA_ENV="$BETA_DIR/app.env"

value_from_env() {
  local key="$1"
  grep "^$key=" "$BETA_ENV" | tail -n 1 | cut -d= -f2-
}

if [ ! -f "$BETA_ENV" ]; then
  echo "beta-status: no beta runtime recorded"
  exit 2
fi

runtime_status="$(value_from_env INTENTOS_BETA_STATUS || true)"
cat "$BETA_ENV"
for key in INTENTOS_BETA_SERVICE_PID INTENTOS_BETA_FAKE_BRIDGE_PID INTENTOS_BETA_UI_PID; do
  pid="$(value_from_env "$key" || true)"
  if [ -n "${pid:-}" ] && kill -0 "$pid" >/dev/null 2>&1; then
    echo "$key=running"
  else
    echo "$key=not_running"
  fi
done

db="$(value_from_env INTENTOS_BETA_DB || true)"
if [ -n "${db:-}" ] && [ -f "$db" ]; then
  python3 -m intentos.beta_cli status --db "$db" --json
else
  echo "beta-status: missing db $db"
  exit 1
fi

url="$(value_from_env INTENTOS_BETA_SERVICE_URL || true)"
if [ "${runtime_status:-}" = "stopped" ]; then
  echo "service_health=stopped"
elif [ -n "${url:-}" ]; then
  python3 - "$url/api/status" <<'PY'
import sys
from urllib.request import urlopen

try:
    with urlopen(sys.argv[1], timeout=1) as response:
        print(f"service_health=http_{response.status}")
except Exception as exc:
    print(f"service_health=failed:{exc}")
    raise SystemExit(1)
PY
fi
