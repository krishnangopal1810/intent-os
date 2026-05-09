#!/usr/bin/env python3
"""Repository structural checks for agent-legible development."""

from __future__ import annotations

import sys

from lint_checks.beta import check_beta_harness_contract
from lint_checks.docs import (
    check_architecture_flow_rules,
    check_live_capture_contract,
    check_next_feature_harness_contract,
    check_public_harness_commands,
    check_quality_scorecard,
)
from lint_checks.fixtures import (
    check_capture_adapter_fixtures,
    check_evaluation_set,
    check_live_observation_harness,
)
from lint_checks.plans import check_no_stale_active_plans, check_parallel_plan_contract
from lint_checks.python_layers import (
    check_file_sizes,
    check_generated_files_not_tracked,
    check_python_syntax_and_imports,
    check_required_python_files,
)
from lint_checks.ui import check_ui_harness


def main() -> int:
    failures: list[str] = []
    check_required_python_files(failures)
    check_python_syntax_and_imports(failures)
    check_file_sizes(failures)
    check_generated_files_not_tracked(failures)
    check_no_stale_active_plans(failures)
    check_public_harness_commands(failures)
    check_architecture_flow_rules(failures)
    check_quality_scorecard(failures)
    check_evaluation_set(failures)
    check_capture_adapter_fixtures(failures)
    check_live_observation_harness(failures)
    check_ui_harness(failures)
    check_live_capture_contract(failures)
    check_beta_harness_contract(failures)
    check_next_feature_harness_contract(failures)
    check_parallel_plan_contract(failures)

    if failures:
        for failure in failures:
            print(f"harness-lint: {failure}", file=sys.stderr)
        return 1

    print("harness-lint: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
