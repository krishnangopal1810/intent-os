#!/usr/bin/env python3
"""Export privacy-redacted beta correction candidates for future fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        default=os.environ.get("INTENTOS_BETA_DB", ".harness/runtime/beta/intentos.sqlite"),
        help="Beta SQLite database path.",
    )
    parser.add_argument(
        "--output",
        default=os.environ.get(
            "INTENTOS_FEEDBACK_FIXTURE_OUTPUT",
            ".harness/runtime/artifacts/feedback-fixture-candidates.json",
        ),
        help="Output artifact path.",
    )
    args = parser.parse_args()

    db_path = ROOT / args.db
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.is_file():
        payload = {
            "status": "blocked",
            "reason": f"beta database not found at {rel(db_path)}",
            "items": [],
        }
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"feedback-fixture-candidates: {payload['reason']}", file=sys.stderr)
        print(f"feedback-fixture-candidates: wrote {output}")
        return 2

    try:
        items = export_candidates(db_path)
    except Exception as exc:
        payload = {"status": "failed", "reason": str(exc), "items": []}
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"feedback-fixture-candidates: failed: {exc}", file=sys.stderr)
        return 1

    payload = {
        "status": "ok",
        "db_path": rel(db_path),
        "privacy": "raw titles and URLs are hashed; page bodies, cookies, tokens, and keystrokes are not exported",
        "item_count": len(items),
        "items": items,
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"feedback-fixture-candidates: wrote {len(items)} item(s) to {output}")
    return 0


def export_candidates(db_path: Path) -> list[dict[str, Any]]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT corrected_label, scope, apply_to_future, app, surface, domain,
                   title_pattern, url_pattern, created_at
            FROM corrections
            ORDER BY created_at, id
            """
        ).fetchall()
    finally:
        conn.close()

    return [candidate_from_row(row) for row in rows]


def candidate_from_row(row: sqlite3.Row) -> dict[str, Any]:
    title = row["title_pattern"]
    url = row["url_pattern"]
    return {
        "source": "beta_correction",
        "corrected_label": row["corrected_label"],
        "scope": row["scope"],
        "apply_to_future": bool(row["apply_to_future"]),
        "app": row["app"],
        "surface": row["surface"],
        "domain": row["domain"],
        "title_pattern_hash": short_hash(title),
        "url_pattern_hash": short_hash(url),
        "has_title_pattern": bool(title),
        "has_url_pattern": bool(url),
        "created_at": row["created_at"],
    }


def short_hash(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
