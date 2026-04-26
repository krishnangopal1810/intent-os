"""CLI formatting for capture replay reports."""

from __future__ import annotations


def print_activity_report(result: dict[str, object]) -> None:
    summary = result["summary"]
    print(summary["narrative"])
    print()
    for label, data in summary["labels"].items():
        print(f"- {label}: {data['duration']} ({data['percentage']}%)")
    print()
    for item in result["items"]:
        confidence = int(round(item["confidence"] * 100))
        print(
            f"- {item['label']} ({confidence}%, {item['duration']}): "
            f"{item['source_app']} - {item['title']}"
        )
        print(f"  {item['reason']}")
