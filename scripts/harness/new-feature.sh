#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

usage() {
  echo "usage: $0 short-slug data-source|classifier|report|ui-workflow|permissioned-live|long-running-process|integration-export|agent-workflow" >&2
  exit 2
}

[ "$#" -eq 2 ] || usage

slug="$1"
feature_class="$2"
case "$slug" in
  *[!a-z0-9-]* | "" | -* | *-)
    echo "new-feature: slug must use lowercase letters, numbers, and hyphens" >&2
    exit 2
    ;;
esac

class_label() {
  case "$1" in
    data-source) echo "New data source or adapter" ;;
    classifier) echo "New classifier or inference path" ;;
    report) echo "New report or narrative" ;;
    ui-workflow) echo "New UI workflow" ;;
    permissioned-live) echo "New permissioned live capability" ;;
    long-running-process) echo "New long-running process" ;;
    integration-export) echo "New export or integration" ;;
    agent-workflow) echo "New agent workflow or parallel work" ;;
    *) return 1 ;;
  esac
}

label="$(class_label "$feature_class" || true)"
if [ -z "$label" ]; then
  echo "new-feature: unknown class '$feature_class'" >&2
  usage
fi

date_value="${INTENTOS_PLAN_DATE:-$(date -u +%Y-%m-%d)}"
plan_dir="${INTENTOS_PLAN_DIR:-docs/plans/active}"
target="$plan_dir/${date_value}-${slug}.md"

mkdir -p "$plan_dir"
if [ -e "$target" ]; then
  echo "new-feature: plan already exists: $target" >&2
  exit 1
fi

emit_acceptance() {
  case "$1" in
    data-source)
      echo "- New source normalizes into the existing ActivityEvent boundary."
      echo "- Parser, privacy filtering, replay, and error behavior are covered by deterministic fixtures."
      ;;
    classifier)
      echo "- New inference behavior has labeled fixtures, deterministic fallback, confidence handling, and unknown fallback."
      echo "- Evaluation thresholds are part of make verify."
      ;;
    report)
      echo "- New report is derived from normalized records and writes deterministic JSON or text artifacts."
      echo "- User-visible report output is covered by UI validation when applicable."
      ;;
    ui-workflow)
      echo "- Workflow is represented in the local UI shell and covered by validate-ui or validate-beta."
      echo "- Render evidence fails on blank screens, overflow, clipped text, and missing workflow states."
      ;;
    permissioned-live)
      echo "- Live capability has a manual diagnostic command outside CI plus a fixture-backed equivalent in make verify."
      echo "- Permission, privacy, and failure states are visible in status and diagnostics."
      ;;
    long-running-process)
      echo "- Process lifecycle is exposed through dev/status/stop commands and structured runtime events."
      echo "- Startup, health, and failure logs are discoverable through diagnose commands."
      ;;
    integration-export)
      echo "- Integration has local fixtures, redaction rules, deterministic dry-run evidence, and no network dependency in make verify."
      echo "- Artifacts clearly show what would be sent or written."
      ;;
    agent-workflow)
      echo "- Ownership, merge order, verification responsibility, and cleanup rules are explicit."
      echo "- Repeated coordination rules are promoted into harness checks."
      ;;
  esac
}

emit_verification() {
  case "$1" in
    data-source) echo "- make adapter-fixture-check" ;;
    ui-workflow) echo "- make validate-ui" ;;
    permissioned-live) echo "- Manual diagnostic command named in this plan" ;;
    long-running-process) echo "- make app-status" ;;
    integration-export) echo "- Deterministic dry-run command named in this plan" ;;
    agent-workflow) echo "- make cleanup-check" ;;
  esac
  echo "- make verify"
}

{
  echo "# Execution Plan: $slug"
  echo
  echo "Date: $date_value"
  echo "Status: Active"
  echo
  echo "## Goal"
  echo
  echo "Implement the $slug $label slice with deterministic, inspectable harness support."
  echo
  echo "## Context"
  echo
  echo "This plan follows docs/HARNESS_FEATURES.md for the $label use-case class."
  echo
  echo "## Scope"
  echo
  echo "- Add the smallest complete product or harness slice for $slug."
  echo "- Keep runtime artifacts, fixtures, diagnostics, and docs aligned with the feature class."
  echo
  echo "## Non-Goals"
  echo
  echo "- Cloud inference, cloud storage, public distribution, or manual-only verification."
  echo
  echo "## Acceptance Criteria"
  echo
  emit_acceptance "$feature_class"
  echo "- make verify remains deterministic and permission-free."
  echo
  echo "## Harness Impact"
  echo
  echo "- Runtime commands and artifacts: add or update documented commands and write stable artifacts under .harness/runtime/artifacts/."
  echo "- Fixtures or fakes required for deterministic make verify: add fixtures or fakes for parser, adapter, model, integration, or UI state as applicable."
  echo "- UI validation: update validate-ui, validate-beta, or screenshot evidence when rendered user-visible behavior changes."
  echo "- Structured logs: emit stable component, event, mode, artifact_path, duration_ms, event_count, and status fields when runtime behavior changes."
  echo "- Privacy, permission: apply redaction and exclusions before persistence; keep permissioned live paths outside CI with fixture-backed equivalents."
  echo "- Docs or harness checks: update runtime, architecture, reliability, quality, active plan, and lints when commands or contracts change."
  echo
  echo "## Verification"
  echo
  emit_verification "$feature_class"
  echo
  echo "## Implementation Notes"
  echo
  echo "Use the existing ActivityEvent boundary and prefer local fixtures over live user state."
  echo
  echo "## Progress Log"
  echo
  echo "- $date_value: Plan created with make new-feature class=$feature_class."
  echo
  echo "## Handoff Notes"
  echo
  echo "Record verification evidence here before moving this plan to docs/plans/completed/."
} > "$target"

echo "$target"
