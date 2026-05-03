#!/usr/bin/env python3
"""Write local PR and CI review status when GitHub tooling is available."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    runtime_dir = ROOT / os.environ.get("INTENTOS_RUNTIME_DIR", ".harness/runtime")
    output = runtime_dir / "artifacts/review-status.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = build_status()
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"review-status: wrote {output}")
    if payload["github"]["status"] == "skipped":
        print(f"review-status: {payload['github']['reason']}")
    return 0


def build_status() -> dict[str, Any]:
    branch = run_text(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    commit = run_text(["git", "rev-parse", "HEAD"])
    porcelain = run_text(["git", "status", "--short"])
    payload: dict[str, Any] = {
        "status": "ok",
        "generated_at": utc_now(),
        "git": {
            "branch": branch,
            "commit": commit,
            "dirty": bool(porcelain.strip()),
            "changed_paths": [line[3:] for line in porcelain.splitlines() if len(line) > 3],
        },
        "github": github_status(),
    }
    return payload


def github_status() -> dict[str, Any]:
    if shutil.which("gh") is None:
        return {"status": "skipped", "reason": "GitHub CLI is not installed"}

    pr = run_json(
        [
            "gh",
            "pr",
            "view",
            "--json",
            "number,url,state,headRefName,baseRefName,statusCheckRollup,reviewDecision",
        ]
    )
    if pr is None:
        return {
            "status": "skipped",
            "reason": "no GitHub pull request is associated with the current branch or gh is not authenticated",
        }
    return {"status": "ok", "pull_request": pr}


def run_text(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return result.stdout.strip()


def run_json(command: list[str]) -> dict[str, Any] | None:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=20,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
