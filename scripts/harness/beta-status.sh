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
sed 's/^INTENTOS_BETA_API_TOKEN=.*/INTENTOS_BETA_API_TOKEN=<redacted>/' "$BETA_ENV"
for key in INTENTOS_BETA_SERVICE_PID INTENTOS_BETA_NATIVE_RECORDER_PID INTENTOS_BETA_FAKE_BRIDGE_PID INTENTOS_BETA_UI_PID; do
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
api_token="$(value_from_env INTENTOS_BETA_API_TOKEN || true)"
if [ "${runtime_status:-}" = "stopped" ]; then
  echo "service_health=stopped"
elif [ -n "${url:-}" ]; then
  python3 - "$url/api/status" "$api_token" <<'PY'
import sys
from urllib.request import Request, urlopen

try:
    request = Request(sys.argv[1], headers={"X-IntentOS-Token": sys.argv[2]} if sys.argv[2] else {})
    with urlopen(request, timeout=1) as response:
        print(f"service_health=http_{response.status}")
except Exception as exc:
    print(f"service_health=failed:{exc}")
    raise SystemExit(1)
PY
fi
