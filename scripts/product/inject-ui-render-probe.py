#!/usr/bin/env python3
"""Inject the shared rendered UI probe into a generated dashboard shell."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE_JS = ROOT / "scripts/product/ui-render-probe.js"
DEFAULT_COPY_POLICY = ROOT / "data/ui/visible_copy_policy.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_path")
    parser.add_argument("--mode", default="fixture")
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--copy-policy", default=str(DEFAULT_COPY_POLICY.relative_to(ROOT)))
    parser.add_argument("--workflow", action="store_true")
    args = parser.parse_args()

    html_path = resolve(args.html_path)
    copy_policy_path = resolve(args.copy_policy)
    html = html_path.read_text(encoding="utf-8")
    config = {
        "mode": args.mode,
        "scenarios": args.scenario or [f"{args.mode}-default"],
        "workflow": args.workflow,
        "copy_policy": json.loads(copy_policy_path.read_text(encoding="utf-8")),
    }
    config_json = json.dumps(config, separators=(",", ":")).replace("</", "<\\/")
    if "intentos-render-probe-config" in html:
        html = re.sub(
            r'(<script id="intentos-render-probe-config" type="application/json">).*?(</script>)',
            lambda match: f"{match.group(1)}{config_json}{match.group(2)}",
            html,
            count=1,
            flags=re.DOTALL,
        )
        html_path.write_text(html, encoding="utf-8")
        return 0

    probe_js = PROBE_JS.read_text(encoding="utf-8")
    injection = (
        f'<script id="intentos-render-probe-config" type="application/json">{config_json}</script>\n'
        f"<script>\n{probe_js}\n</script>"
    )
    if "</body>" not in html:
        raise SystemExit(f"{html_path} does not contain </body>")
    html_path.write_text(html.replace("</body>", injection + "\n  </body>"), encoding="utf-8")
    return 0


def resolve(path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate


if __name__ == "__main__":
    raise SystemExit(main())
