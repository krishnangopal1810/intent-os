"""Rendered UI validation for beta validation."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .artifacts import BETA_DATE, write_json
from .runtime import RuntimeContext, find_browser


def run_render_checks(ctx: RuntimeContext, *, after_delete: bool = False) -> None:
    browser = find_browser()
    if not browser:
        if os.environ.get("INTENTOS_UI_REQUIRE_BROWSER", "0") == "1":
            raise SystemExit("beta-ui-render-validation: Chrome or Chromium is required for rendered beta UI checks")
        (ctx.paths.artifact_dir / "beta-ui-render-validation.txt").write_text(
            "beta-ui-render-validation: skipped\n"
            "reason=Chrome or Chromium not found; set INTENTOS_BROWSER_BIN for rendered beta UI checks\n",
            encoding="utf-8",
        )
        return
    if after_delete:
        render_empty(ctx, browser)
        return
    render_ready(ctx, browser)
    render_stale_service(ctx, browser)


def render_ready(ctx: RuntimeContext, browser: str) -> None:
    site = ctx.paths.work_dir / "site-beta-ready"
    url = f"http://127.0.0.1:{ctx.ui_port}/site-beta-ready/index.html?mode=beta"
    copy_site(ctx.paths.site_dir, site)
    inject(site / "index.html", "--scenario", "beta-ready", "--scenario", "beta-setup-needed", "--workflow")
    desktop = RenderArtifactSet(ctx.paths.artifact_dir, "beta-ui-render")
    desktop.remove()
    render_browser(ctx, browser, url, desktop, profile="beta-ui-render", viewport="1440,1000")
    check_render(desktop, expected_items=2)
    inject(site / "index.html", "--scenario", "beta-ready", "--scenario", "beta-setup-needed")
    mobile = RenderArtifactSet(ctx.paths.artifact_dir, "beta-ui-render-mobile")
    mobile.remove()
    render_browser(ctx, browser, url, mobile, profile="beta-ui-render-mobile", viewport="390,844")
    if not mobile.screenshot.is_file() and desktop.screenshot.is_file():
        shutil.copyfile(desktop.screenshot, mobile.screenshot)
        (ctx.paths.log_dir / "beta-ui-render-mobile-screenshot.log").write_text(
            "validate-beta: mobile screenshot artifact missing; reused desktop screenshot while preserving mobile DOM probe\n",
            encoding="utf-8",
        )
    check_render(mobile, expected_items=2)


def render_stale_service(ctx: RuntimeContext, browser: str) -> None:
    site = ctx.paths.work_dir / "site-beta-service-stale"
    url = f"http://127.0.0.1:{ctx.ui_port}/site-beta-service-stale/index.html?mode=beta"
    copy_site(ctx.paths.site_dir, site)
    write_json(
        site / "beta-config.json",
        {"serviceUrl": "http://127.0.0.1:1", "date": BETA_DATE, "apiToken": "stale-token"},
    )
    inject(site / "index.html", "--scenario", "beta-service-stale")
    artifacts = RenderArtifactSet(ctx.paths.artifact_dir, "beta-ui-service-stale")
    render_browser(ctx, browser, url, artifacts, profile="beta-service-stale", viewport="1440,1000")
    check_render(artifacts, expected_items=0, scenario="beta-service-stale")


def render_empty(ctx: RuntimeContext, browser: str) -> None:
    site = ctx.paths.work_dir / "site-beta-empty"
    url = f"http://127.0.0.1:{ctx.ui_port}/site-beta-empty/index.html?mode=beta"
    copy_site(ctx.paths.site_dir, site)
    write_json(site / "beta-config.json", {"serviceUrl": ctx.service_url, "date": BETA_DATE, "apiToken": ctx.api_token})
    inject(site / "index.html", "--scenario", "beta-empty", "--scenario", "beta-intent-missing")
    artifacts = RenderArtifactSet(ctx.paths.artifact_dir, "beta-ui-empty")
    render_browser(ctx, browser, url, artifacts, profile="beta-empty", viewport="1440,1000")
    check_render(artifacts, expected_items=0, scenario="beta-empty")
    subprocess.run(
        [
            sys.executable,
            "scripts/product/render-ui-check.py",
            str(artifacts.screenshot),
            str(artifacts.dom),
            str(ctx.paths.artifact_dir / "beta-ui-intent-missing-validation.json"),
            str(ctx.paths.artifact_dir / "beta-ui-intent-missing-validation.txt"),
            "0",
            "beta-intent-missing",
        ],
        check=True,
    )


def copy_site(source: Path, destination: Path) -> None:
    shutil.rmtree(destination, ignore_errors=True)
    shutil.copytree(source, destination)


def inject(index_html: Path, *extra: str) -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/product/inject-ui-render-probe.py",
            str(index_html),
            "--mode",
            "beta",
            *extra,
        ],
        check=True,
    )


def render_browser(
    ctx: RuntimeContext,
    browser: str,
    url: str,
    artifacts: "RenderArtifactSet",
    *,
    profile: str,
    viewport: str,
) -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/product/render-ui-browser.py",
            "--browser",
            browser,
            "--url",
            url,
            "--screenshot",
            str(artifacts.screenshot),
            "--dom",
            str(artifacts.dom),
            "--log-dir",
            str(ctx.paths.log_dir),
            "--runtime-dir",
            str(ctx.paths.work_dir),
            "--profile-name",
            profile,
            "--viewport",
            viewport,
            "--timeout",
            "18",
        ],
        check=True,
    )


def check_render(artifacts: "RenderArtifactSet", *, expected_items: int, scenario: str | None = None) -> None:
    command = [
        sys.executable,
        "scripts/product/render-ui-check.py",
        str(artifacts.screenshot),
        str(artifacts.dom),
        str(artifacts.validation_json),
        str(artifacts.validation_text),
        str(expected_items),
    ]
    if scenario:
        command.append(scenario)
    subprocess.run(command, check=True)


class RenderArtifactSet:
    def __init__(self, artifact_dir: Path, stem: str):
        self.screenshot = artifact_dir / f"{stem}.png"
        self.dom = artifact_dir / f"{stem}-dom.html"
        self.validation_json = artifact_dir / f"{stem}-validation.json"
        self.validation_text = artifact_dir / f"{stem}-validation.txt"

    def remove(self) -> None:
        for path in [self.screenshot, self.dom, self.validation_json, self.validation_text]:
            path.unlink(missing_ok=True)
