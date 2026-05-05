#!/usr/bin/env python3
"""Capture screenshot and dumped DOM for a local UI URL with Chrome/Chromium."""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--screenshot", required=True)
    parser.add_argument("--dom", required=True)
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("--runtime-dir", required=True)
    parser.add_argument("--viewport", default="1440,1000")
    parser.add_argument("--profile-name", default="render")
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()

    screenshot = Path(args.screenshot).resolve()
    dom = Path(args.dom).resolve()
    log_dir = Path(args.log_dir).resolve()
    runtime_dir = Path(args.runtime_dir).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    screenshot.unlink(missing_ok=True)
    dom.unlink(missing_ok=True)

    base_flags = [
        "--headless=new",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-extensions",
        "--disable-gpu",
        "--disable-sync",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        f"--window-size={args.viewport}",
    ]
    run_browser(
        args.browser,
        args.url,
        base_flags,
        runtime_dir,
        log_dir,
        args.profile_name,
        "screenshot",
        ["--virtual-time-budget=9000", f"--screenshot={screenshot}"],
        args.timeout,
        artifact=screenshot,
    )
    run_browser(
        args.browser,
        args.url,
        base_flags,
        runtime_dir,
        log_dir,
        args.profile_name,
        "dom",
        ["--virtual-time-budget=9000", "--dump-dom"],
        args.timeout,
        stdout_path=dom,
    )
    return 0


def run_browser(
    browser: str,
    url: str,
    base_flags: list[str],
    runtime_dir: Path,
    log_dir: Path,
    profile_name: str,
    name: str,
    extra: list[str],
    timeout: int,
    *,
    artifact: Path | None = None,
    stdout_path: Path | None = None,
) -> None:
    profile = runtime_dir / f"{profile_name}-{name}"
    shutil.rmtree(profile, ignore_errors=True)
    command = [browser, *base_flags, f"--user-data-dir={profile}", *extra, url]
    log_path = log_dir / f"{profile_name}-{name}.log"
    with log_path.open("w", encoding="utf-8") as log:
        stdout = log
        if artifact is not None:
            process = subprocess.Popen(
                command,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
            )
            if wait_for_artifact(artifact, seconds=timeout):
                stop_process(process)
                return
            stop_process(process)
            raise SystemExit(f"browser {name} did not write {artifact}; see {log_path}")
        if stdout_path is not None:
            stdout_path.unlink(missing_ok=True)
            with stdout_path.open("w", encoding="utf-8") as output:
                process = subprocess.Popen(
                    command,
                    stdout=output,
                    stderr=log,
                    start_new_session=True,
                    text=True,
                )
                if wait_for_stdout_marker(
                    stdout_path,
                    "intentos-render-probe",
                    seconds=timeout,
                    process=process,
                ):
                    stop_process(process)
                    return
                if process.poll() is None:
                    stop_process(process)
                    raise SystemExit(f"browser {name} did not write probe marker; see {log_path}")
                if process.returncode != 0:
                    raise SystemExit(f"browser {name} failed; see {log_path}")
                if not wait_for_artifact(stdout_path, seconds=1):
                    raise SystemExit(f"browser {name} did not write {stdout_path}; see {log_path}")
                return
        try:
            result = subprocess.run(
                command,
                check=True,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                timeout=timeout,
                text=True,
            )
        except subprocess.TimeoutExpired as exc:
            captured = exc.stdout or ""
            if isinstance(captured, bytes):
                captured = captured.decode("utf-8", errors="replace")
            if stdout_path and "intentos-render-probe" in captured:
                stdout_path.write_text(captured, encoding="utf-8")
                return
            if artifact and wait_for_artifact(artifact):
                return
            raise SystemExit(f"browser {name} timed out; see {log_path}") from exc
        except subprocess.CalledProcessError as exc:
            raise SystemExit(f"browser {name} failed; see {log_path}") from exc
    if stdout_path:
        stdout_path.write_text(result.stdout or "", encoding="utf-8")


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=2)


def wait_for_artifact(path: Path, seconds: float = 5.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.is_file() and path.stat().st_size > 0:
            return True
        time.sleep(0.1)
    return path.is_file() and path.stat().st_size > 0


def wait_for_stdout_marker(
    path: Path,
    marker: str,
    *,
    seconds: float = 5.0,
    process: subprocess.Popen | None = None,
) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.is_file() and marker in path.read_text(encoding="utf-8", errors="ignore"):
            return True
        if process is not None and process.poll() is not None:
            break
        time.sleep(0.1)
    return path.is_file() and marker in path.read_text(encoding="utf-8", errors="ignore")


if __name__ == "__main__":
    raise SystemExit(main())
