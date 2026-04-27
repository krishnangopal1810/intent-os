#!/usr/bin/env python3
"""Validate the harness-readable long-term architecture graph."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GRAPH_PATH = ROOT / "docs/architecture/long-term-plan.json"
DOC_PATH = ROOT / "docs/architecture/long-term-plan.md"

VALID_STATUSES = {"current", "next", "planned", "future"}
REQUIRED_NODE_IDS = {
    "manual_import",
    "browser_history_import",
    "chatgpt_export_parser",
    "macos_metadata_capture",
    "screencapturekit_fallback",
    "vision_ocr_fallback",
    "privacy_policy",
    "activity_event_boundary",
    "deterministic_classifier",
    "local_model_second_pass",
    "daily_narratives",
    "intent_mismatch_detection",
    "local_ui",
    "execution_actions",
    "harness_fixtures",
    "runtime_artifacts_and_events",
    "make_verify",
    "ui_validation",
    "architecture_graph_check",
}


def main() -> int:
    failures: list[str] = []
    graph = load_graph(failures)
    if graph is not None:
        validate_graph(graph, failures)
    validate_markdown(failures)

    if failures:
        for failure in failures:
            print(f"architecture-plan-check: {failure}", file=sys.stderr)
        return 1

    print("architecture-plan-check: ok")
    return 0


def load_graph(failures: list[str]) -> dict[str, object] | None:
    if not GRAPH_PATH.is_file():
        failures.append("missing docs/architecture/long-term-plan.json")
        return None
    try:
        loaded = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON in {GRAPH_PATH.relative_to(ROOT)}: {exc}")
        return None
    if not isinstance(loaded, dict):
        failures.append("long-term-plan.json must contain a JSON object")
        return None
    return loaded


def validate_graph(graph: dict[str, object], failures: list[str]) -> None:
    if graph.get("schema_version") != 1:
        failures.append("long-term-plan.json schema_version must be 1")

    phases = graph.get("phases")
    layers = graph.get("layers")
    nodes = graph.get("nodes")
    edges = graph.get("edges")

    if not isinstance(phases, list) or not phases:
        failures.append("long-term-plan.json must include non-empty phases")
        phases = []
    if not isinstance(layers, list) or not layers:
        failures.append("long-term-plan.json must include non-empty layers")
        layers = []
    if not isinstance(nodes, list) or not nodes:
        failures.append("long-term-plan.json must include non-empty nodes")
        nodes = []
    if not isinstance(edges, list) or not edges:
        failures.append("long-term-plan.json must include non-empty edges")
        edges = []

    phase_ids = validate_items("phase", phases, failures)
    layer_ids = validate_items("layer", layers, failures)
    node_ids = validate_nodes(nodes, phase_ids, layer_ids, failures)
    validate_edges(edges, node_ids, failures)
    validate_top_level_lists(graph, failures)

    missing = sorted(REQUIRED_NODE_IDS - node_ids)
    if missing:
        failures.append("long-term-plan.json is missing required roadmap node(s): " + ", ".join(missing))


def validate_items(name: str, items: list[object], failures: list[str]) -> set[str]:
    ids: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            failures.append(f"{name} at index {index} must be an object")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            failures.append(f"{name} at index {index} is missing id")
            continue
        if item_id in ids:
            failures.append(f"duplicate {name} id {item_id}")
        ids.add(item_id)
        if name == "phase" and item.get("status") not in VALID_STATUSES:
            failures.append(f"phase {item_id} has invalid status {item.get('status')!r}")
    return ids


def validate_nodes(
    nodes: list[object],
    phase_ids: set[str],
    layer_ids: set[str],
    failures: list[str],
) -> set[str]:
    ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            failures.append(f"node at index {index} must be an object")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            failures.append(f"node at index {index} is missing id")
            continue
        if node_id in ids:
            failures.append(f"duplicate node id {node_id}")
        ids.add(node_id)

        if node.get("status") not in VALID_STATUSES:
            failures.append(f"node {node_id} has invalid status {node.get('status')!r}")
        if node.get("phase") not in phase_ids:
            failures.append(f"node {node_id} references unknown phase {node.get('phase')!r}")
        if node.get("layer") not in layer_ids:
            failures.append(f"node {node_id} references unknown layer {node.get('layer')!r}")

        docs = node.get("docs")
        if not isinstance(docs, list) or not docs:
            failures.append(f"node {node_id} must list at least one doc path")
        else:
            for doc in docs:
                if not isinstance(doc, str) or not doc:
                    failures.append(f"node {node_id} has invalid doc path {doc!r}")
                elif not (ROOT / doc).exists():
                    failures.append(f"node {node_id} links missing doc path {doc}")

        contracts = node.get("harness_contracts")
        if not isinstance(contracts, list) or not contracts:
            failures.append(f"node {node_id} must list harness_contracts")

    return ids


def validate_edges(edges: list[object], node_ids: set[str], failures: list[str]) -> None:
    seen: set[tuple[str, str]] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            failures.append(f"edge at index {index} must be an object")
            continue
        source = edge.get("from")
        target = edge.get("to")
        if not isinstance(source, str) or source not in node_ids:
            failures.append(f"edge at index {index} references unknown source {source!r}")
            continue
        if not isinstance(target, str) or target not in node_ids:
            failures.append(f"edge {source} references unknown target {target!r}")
            continue
        pair = (source, target)
        if pair in seen:
            failures.append(f"duplicate edge {source} -> {target}")
        seen.add(pair)
        if not isinstance(edge.get("contract"), str) or not edge["contract"]:
            failures.append(f"edge {source} -> {target} must include a contract")


def validate_top_level_lists(graph: dict[str, object], failures: list[str]) -> None:
    for key in ["artifact_contracts", "verification_gates", "harness_usage"]:
        value = graph.get(key)
        if not isinstance(value, list) or not value:
            failures.append(f"long-term-plan.json must include non-empty {key}")

    gates = graph.get("verification_gates", [])
    if isinstance(gates, list) and "make verify" not in gates:
        failures.append("verification_gates must include make verify")


def validate_markdown(failures: list[str]) -> None:
    if not DOC_PATH.is_file():
        failures.append("missing docs/architecture/long-term-plan.md")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    for phrase in [
        "```mermaid",
        "long-term-plan.json",
        "## Harness Usage",
        "ActivityEvent boundary",
        "Local model second pass",
        "ScreenCaptureKit fallback",
        "make verify",
    ]:
        if phrase not in text:
            failures.append(f"docs/architecture/long-term-plan.md must mention {phrase!r}")


if __name__ == "__main__":
    raise SystemExit(main())
