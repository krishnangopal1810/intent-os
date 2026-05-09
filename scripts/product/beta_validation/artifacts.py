"""Paths and JSON helpers for beta validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BETA_DATE = "2026-04-27"


@dataclass(frozen=True)
class ValidationPaths:
    runtime_dir: Path
    work_dir: Path
    artifact_dir: Path
    log_dir: Path
    site_dir: Path
    db_path: Path
    service_log: Path
    validation_json: Path
    daily_review_json: Path
    lock_dir: Path


def paths_from_runtime(runtime_dir: str) -> ValidationPaths:
    runtime = Path(runtime_dir)
    work = runtime / "beta-validation"
    artifact = runtime / "artifacts"
    log = work / "logs"
    return ValidationPaths(
        runtime_dir=runtime,
        work_dir=work,
        artifact_dir=artifact,
        log_dir=log,
        site_dir=work / "site",
        db_path=work / "intentos.sqlite",
        service_log=log / "beta-service.log",
        validation_json=artifact / "beta-validation.json",
        daily_review_json=artifact / "beta-daily-review.json",
        lock_dir=runtime / "beta-validation.lock",
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def redacted_config(config: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(config)
    if sanitized.get("apiToken"):
        sanitized["apiToken"] = "<redacted>"
    return sanitized
