#!/usr/bin/env python3
"""Run deterministic dogfood beta validation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from beta_validation.artifacts import paths_from_runtime, read_json
from beta_validation.render import run_render_checks
from beta_validation.runtime import (
    build_ui,
    cleanup,
    mark_native_recorder_running,
    prepare_runtime,
    run_fake_bridge,
    start_service,
    start_ui,
)
from beta_validation.scenarios import (
    reset_onboarding,
    run_api_scenario,
    run_delete_scenario,
)


def main() -> int:
    paths = paths_from_runtime(os.environ.get("INTENTOS_RUNTIME_DIR", ".harness/runtime"))
    ctx = prepare_runtime(paths)
    try:
        start_service(ctx)
        run_fake_bridge(ctx)
        mark_native_recorder_running(paths.db_path)
        build_ui(ctx)
        start_ui(ctx)
        run_api_scenario(ctx)
        reset_onboarding(paths.db_path)
        run_render_checks(ctx)
        run_delete_scenario(ctx)
        run_render_checks(ctx, after_delete=True)
        print_json(paths.validation_json)
        print("validate-beta: ok")
        return 0
    finally:
        cleanup(ctx)


def print_json(path) -> None:
    print(json.dumps(read_json(path), indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
