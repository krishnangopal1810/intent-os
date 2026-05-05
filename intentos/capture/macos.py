"""macOS metadata-only capture adapter."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Sequence

from intentos.capture.core import CaptureObservation


FRONTMOST_APP_SCRIPT = """
tell application "System Events"
  set frontApp to first application process whose frontmost is true
  set appName to name of frontApp
  set appPid to unix id of frontApp
  set appBundle to ""
  try
    set appBundle to bundle identifier of frontApp
  end try
  set windowName to ""
  try
    tell frontApp to set windowName to name of front window
  end try
end tell
return appName & linefeed & appBundle & linefeed & appPid & linefeed & windowName
""".strip()

FRONTMOST_FIELD_SCRIPTS = [
    'tell application "System Events" to get name of first application process whose frontmost is true',
    'tell application "System Events" to get bundle identifier of first application process whose frontmost is true',
    'tell application "System Events" to get unix id of first application process whose frontmost is true',
    'tell application "System Events" to tell first application process whose frontmost is true to get name of front window',
]


class MacOSCaptureError(RuntimeError):
    """Raised when local macOS metadata capture cannot run."""


@dataclass(frozen=True)
class MacOSAppSnapshot:
    app_name: str
    bundle_id: str | None
    process_id: int
    window_title: str | None


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def capture_frontmost_observation(duration_seconds: int) -> CaptureObservation:
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")

    start = utc_now()
    snapshot = frontmost_app_snapshot()
    time.sleep(duration_seconds)
    end = utc_now()
    return snapshot_to_observation(snapshot, start, end)


def frontmost_app_snapshot(
    runner: CommandRunner | None = None,
) -> MacOSAppSnapshot:
    completed = (runner or run_command)(
        ["osascript", "-e", FRONTMOST_APP_SCRIPT],
    )
    if completed.returncode != 0:
        completed = frontmost_app_snapshot_field_fallback(runner or run_command, completed)

    lines = completed.stdout.splitlines()
    if not lines or not lines[0].strip():
        raise MacOSCaptureError("macOS capture returned no frontmost app name")

    bundle_id = value_or_none(lines[1] if len(lines) > 1 else "")
    process_id_text = lines[2].strip() if len(lines) > 2 else ""
    try:
        process_id = int(process_id_text)
    except ValueError as exc:
        raise MacOSCaptureError("macOS capture returned an invalid process id") from exc

    return MacOSAppSnapshot(
        app_name=lines[0].strip(),
        bundle_id=bundle_id,
        process_id=process_id,
        window_title=value_or_none(lines[3] if len(lines) > 3 else ""),
    )


def frontmost_app_snapshot_field_fallback(
    runner: CommandRunner,
    original: subprocess.CompletedProcess[str],
) -> subprocess.CompletedProcess[str]:
    values: list[str] = []
    for script in FRONTMOST_FIELD_SCRIPTS:
        completed = runner(["osascript", "-e", script])
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            if not detail:
                detail = original.stderr.strip() or original.stdout.strip()
            raise MacOSCaptureError(permission_help(detail))
        values.append(completed.stdout.strip())
    return subprocess.CompletedProcess(
        ["osascript", "-e", "frontmost field fallback"],
        0,
        stdout="\n".join(values) + "\n",
        stderr="",
    )


def snapshot_to_observation(
    snapshot: MacOSAppSnapshot,
    start: datetime,
    end: datetime,
) -> CaptureObservation:
    return CaptureObservation(
        start_time=format_timestamp(start),
        end_time=format_timestamp(end),
        app_name=snapshot.app_name,
        bundle_id=snapshot.bundle_id,
        process_id=snapshot.process_id,
        window_title=snapshot.window_title,
        source="macos_frontmost",
        metadata={
            "capture_mode": "manual_live_sensor",
            "adapter": "osascript_system_events",
            "permission": "Accessibility permission may be required",
        },
    )


def run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except FileNotFoundError as exc:
        raise MacOSCaptureError("osascript is required for macOS capture") from exc
    except subprocess.TimeoutExpired as exc:
        raise MacOSCaptureError("macOS capture timed out while reading System Events") from exc


def permission_help(detail: str) -> str:
    message = (
        "macOS frontmost app capture failed. Grant Accessibility permission to "
        "IntentOS in System Settings > Privacy & Security > Accessibility, "
        "then run the app access check again. If you are using the source "
        "harness directly, grant the launcher process shown by macOS."
    )
    if detail:
        return f"{message} System Events said: {detail}"
    return message


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def value_or_none(value: str) -> str | None:
    value = value.strip()
    return value or None
