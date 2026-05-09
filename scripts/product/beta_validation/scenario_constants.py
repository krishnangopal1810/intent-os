"""Static beta validation scenario expectations."""

UI_TOKENS = [
    "data-correction-controls", "data-onboarding", "data-setup-guidance", "data-daily-loop",
    "data-intent-form", "data-intent-contract", "data-evening-receipt", "data-service-notice",
    "data-command-center", "data-command-now-title", "data-command-trust-title", "data-command-tonight-title",
    "data-coach-hero", "data-coach-verdict", "data-coach-receipts", "data-focus-rescue",
    "data-focus-rescue-actions", "data-signal-details", "data-weekly-details", "data-weekly-patterns",
    "data-queue-details", "data-evidence-details", "data-review-form", "Native recorder",
    "/api/permissions/check", "/api/setup-report", "data-onboarding-steps", "data-capture-preview",
    "POST /api/corrections", "/api/daily-loop", "/api/daily-intent", "/api/review-checkin",
    "/api/focus-rescue-action", "/api/weekly-patterns", "bindSectionNavigation", "renderCoachHero",
    "weekStartDate", "openDisclosureForTarget", "scrollTargetIntoWorkspace", "daily-review",
]


SCENARIO_EXPECTATIONS = {
    "all_ok": ("ok", "ok", "running", "connected", False, "ready"),
    "accessibility_blocked": ("blocked", "unchecked", "running", "never_connected", False, "setup_needed"),
    "automation_blocked": ("ok", "blocked", "running", "never_connected", False, "ready"),
    "chrome_bridge_missing": ("ok", "not_applicable", "running", "never_connected", False, "ready"),
    "recorder_stale": ("ok", "ok", "stale", "connected", False, "setup_needed"),
    "paused_capture": ("ok", "ok", "running", "connected", True, "setup_needed"),
    "setup_needed": ("needs_action", "unchecked", "not_started", "never_connected", False, "setup_needed"),
    "fresh_install": ("needs_action", "unchecked", "not_started", "never_connected", False, "setup_needed"),
    "capture_preview_blocked": ("ok", "unchecked", "running", "never_connected", False, "setup_needed"),
    "browser_detail_skipped": ("ok", "not_applicable", "running", "never_connected", False, "ready"),
    "browser_detail_granted": ("ok", "ok", "running", "connected", False, "ready"),
    "duplicate_permission_identity": ("blocked", "unchecked", "running", "never_connected", False, "setup_needed"),
}
