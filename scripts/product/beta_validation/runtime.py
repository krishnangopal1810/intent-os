"""Runtime process management for beta validation."""

from __future__ import annotations

import os
import secrets
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from .artifacts import BETA_DATE, ValidationPaths, write_json


@dataclass
class RuntimeContext:
    paths: ValidationPaths
    api_token: str
    service_port: int
    ui_port: int
    service_url: str
    ui_url: str
    service_process: subprocess.Popen | None = None
    ui_process: subprocess.Popen | None = None


def prepare_runtime(paths: ValidationPaths) -> RuntimeContext:
    paths.runtime_dir.mkdir(parents=True, exist_ok=True)
    acquire_lock(paths.lock_dir)
    paths.work_dir.mkdir(parents=True, exist_ok=True)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        (Path(str(paths.db_path) + suffix)).unlink(missing_ok=True)
    api_token = secrets.token_urlsafe(32)
    service_port = choose_port()
    ui_port = choose_port()
    service_url = f"http://127.0.0.1:{service_port}"
    ui_url = f"http://127.0.0.1:{ui_port}/site/index.html?mode=beta"
    return RuntimeContext(paths, api_token, service_port, ui_port, service_url, ui_url)


def acquire_lock(lock_dir: Path) -> None:
    try:
        lock_dir.mkdir()
    except FileExistsError:
        pid_path = lock_dir / "pid"
        lock_pid = pid_path.read_text(encoding="utf-8").strip() if pid_path.is_file() else ""
        live_pid = int(lock_pid) if lock_pid.isdecimal() else None
        if live_pid is not None and process_alive(live_pid):
            raise SystemExit(
                f"validate-beta: another beta validation is already using {lock_dir.parent / 'beta-validation'} "
                f"(pid {lock_pid})"
            )
        shutil.rmtree(lock_dir, ignore_errors=True)
        try:
            lock_dir.mkdir()
        except FileExistsError as exc:
            raise SystemExit(
                f"validate-beta: another beta validation is already using {lock_dir.parent / 'beta-validation'}"
            ) from exc
    (lock_dir / "pid").write_text(f"{os.getpid()}\n", encoding="utf-8")


def choose_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def start_service(ctx: RuntimeContext) -> None:
    ctx.paths.service_log.write_text("", encoding="utf-8")
    log = ctx.paths.service_log.open("a", encoding="utf-8")
    ctx.service_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "intentos.beta_cli",
            "serve",
            "--db",
            str(ctx.paths.db_path),
            "--privacy-policy",
            "data/capture/privacy_policy.json",
            "--port",
            str(ctx.service_port),
            "--service-log",
            str(ctx.paths.service_log),
            "--runtime-dir",
            str(ctx.paths.work_dir),
            "--permission-mode",
            "fake",
            "--api-token",
            ctx.api_token,
            "--allowed-origin",
            f"http://127.0.0.1:{ctx.ui_port}",
            "--disable-system-open",
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    wait_for_url(f"{ctx.service_url}/api/status", ctx.service_process, ctx.api_token)


def run_fake_bridge(ctx: RuntimeContext) -> None:
    with (ctx.paths.log_dir / "beta-fake-bridge.log").open("w", encoding="utf-8") as log:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "intentos.beta_cli",
                "fake-bridge",
                "--service-url",
                f"{ctx.service_url}/api/browser-event",
                "--input",
                "data/beta/fake_chrome_events.json",
                "--api-token",
                ctx.api_token,
                "--once",
            ],
            check=True,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )


def mark_native_recorder_running(db_path: Path) -> None:
    from intentos.beta import store

    with store.connect(db_path) as conn:
        store.init_db(conn)
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_pid", "fixture")
        store.set_status(conn, "native_recorder_last_event_at", store.utc_now())
        store.set_status(conn, "native_recorder_log", "fixture")


def build_ui(ctx: RuntimeContext) -> None:
    env = {**os.environ, "INTENTOS_RUNTIME_DIR": str(ctx.paths.work_dir), "INTENTOS_PRESERVE_LIVE_ARTIFACTS": "1"}
    with (ctx.paths.log_dir / "beta-ui-build.log").open("w", encoding="utf-8") as log:
        subprocess.run(["scripts/product/dev.sh"], check=True, env=env, stdout=log, stderr=subprocess.STDOUT, text=True)
    write_json(
        ctx.paths.site_dir / "beta-config.json",
        {"serviceUrl": ctx.service_url, "date": BETA_DATE, "apiToken": ctx.api_token},
    )


def start_ui(ctx: RuntimeContext) -> None:
    env = {**os.environ, "INTENTOS_RUNTIME_DIR": str(ctx.paths.work_dir), "INTENTOS_APP_PORT": str(ctx.ui_port)}
    log = (ctx.paths.log_dir / "beta-ui.log").open("w", encoding="utf-8")
    ctx.ui_process = subprocess.Popen(
        ["scripts/product/start-ui.sh"],
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    wait_for_url(ctx.ui_url, ctx.ui_process)


def wait_for_url(url: str, process: subprocess.Popen, token: str = "") -> None:
    last: object = None
    headers = {"X-IntentOS-Token": token} if token else {}
    for _ in range(40):
        if process.poll() is not None:
            raise SystemExit(f"process {process.pid} exited with {process.returncode}")
        try:
            with urlopen(Request(url, headers=headers), timeout=1) as response:
                if 200 <= response.status < 400:
                    return
                last = response.status
        except Exception as exc:
            last = exc
        time.sleep(0.1)
    raise SystemExit(f"timed out waiting for {url}: {last}")


def find_browser() -> str | None:
    configured = os.environ.get("INTENTOS_BROWSER_BIN")
    if configured and os.access(configured, os.X_OK):
        return configured
    for candidate in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ):
        if os.access(candidate, os.X_OK):
            return candidate
    for command_name in ("google-chrome", "chromium", "chromium-browser"):
        resolved = shutil.which(command_name)
        if resolved:
            return resolved
    return None


def cleanup(ctx: RuntimeContext) -> None:
    for process in (ctx.service_process, ctx.ui_process):
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
    shutil.rmtree(ctx.paths.lock_dir, ignore_errors=True)
