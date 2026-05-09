"""Dogfood beta harness lint checks."""

from __future__ import annotations

from .beta_runtime import check_beta_runtime_contract
from .beta_security import check_beta_security_contract
from .beta_ui import check_beta_ui_contract


def check_beta_harness_contract(failures: list[str]) -> None:
    """Keep the dogfood beta runnable, inspectable, and local-only."""
    check_beta_runtime_contract(failures)
    check_beta_security_contract(failures)
    check_beta_ui_contract(failures)
