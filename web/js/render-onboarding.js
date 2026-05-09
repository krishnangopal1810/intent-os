function renderOnboarding(betaConfig, onboarding, status) {
  const panel = document.querySelector("[data-onboarding]");
  if (!panel || !betaConfig || !onboarding || !status) {
    if (panel) {
      panel.hidden = true;
    }
    return;
  }
  const readiness = status.readiness?.state || "setup_needed";
  panel.hidden = Boolean(onboarding.dismissed) ||
    (Boolean(onboarding.completed) && readiness !== "setup_needed");
  renderOnboardingSteps(onboarding);
  renderCapturePreview(status.capture_preview || {});
  renderPermissionChecklist(status);
  renderSetupGuidance(currentSetupGuidance);
  updateOnboardingActions(onboarding, status);
  bindOnboardingActions(betaConfig);
}

function renderOnboardingSteps(onboarding) {
  const wrapper = document.querySelector("[data-onboarding-steps]");
  const title = document.querySelector("[data-onboarding-title]");
  if (!wrapper) {
    return;
  }
  const current = onboarding.current_step || "privacy";
  const labels = {
    privacy: "Confirm local privacy",
    app_access: "Grant app access",
    capture_check: "Verify live capture",
    daily_focus: "Set daily focus",
    first_block: "Start first block",
    complete: "Setup complete",
  };
  if (title) {
    title.textContent = labels[current] || "Set up IntentOS";
  }
  wrapper.replaceChildren(
    ...(onboarding.steps || []).map((item) => {
      const step = document.createElement("span");
      step.className = `onboarding-step${item.complete ? " step-complete" : ""}${item.id === current ? " step-current" : ""}`;
      const name = document.createElement("strong");
      name.textContent = item.label || item.id;
      const state = document.createElement("small");
      state.textContent = item.verification || (item.complete ? "Ready" : "Pending");
      step.replaceChildren(name, state);
      return step;
    }),
  );
}

function renderCapturePreview(preview) {
  const wrapper = document.querySelector("[data-capture-preview]");
  if (!wrapper) {
    return;
  }
  const state = preview.state || "unchecked";
  const title = document.createElement("strong");
  title.textContent = state === "ok" ? "Capture verified" : "Capture check";
  const detail = document.createElement("p");
  const evidence = [preview.app_name, preview.window_title, preview.domain]
    .filter(Boolean)
    .join(" - ");
  detail.textContent = state === "ok"
    ? `IntentOS can see current metadata: ${evidence || "current app/window"}.`
    : preview.detail || "Run app access check to verify current app/window metadata.";
  wrapper.replaceChildren(title, detail);
  wrapper.dataset.state = state;
  wrapper.hidden = false;
}

function renderPermissionChecklist(status) {
  const list = document.querySelector("[data-permission-checklist]");
  const permissions = status.permissions || {};
  const captureReady = status.capture_preview?.state === "ok";
  const browserConfigured = status.setup?.browser_detail?.state &&
    status.setup.browser_detail.state !== "not_started";
  const items = [
    permissions.local_service,
    permissions.database,
    permissions.accessibility,
    captureReady || browserConfigured ? permissions.browser_automation : null,
    permissions.native_recorder,
    captureReady || browserConfigured ? permissions.chrome_extension : null,
    permissions.capture,
    permissions.privacy,
    {
      state: "ok",
      label: "Delete local data",
      detail: "Available from the dashboard API and menu bar.",
    },
  ].filter(Boolean);
  list.replaceChildren(
    ...items.map((item) => {
      const copyItem = userFacingPermission(item);
      const row = document.createElement("div");
      row.className = `permission-item permission-${copyItem.state}`;
      const stateText = document.createElement("span");
      stateText.className = "permission-state";
      stateText.textContent = permissionStateLabel(copyItem.state);
      const copy = document.createElement("span");
      copy.className = "permission-copy";
      const title = document.createElement("strong");
      title.textContent = copyItem.label;
      const detail = document.createElement("span");
      detail.textContent = copyItem.detail;
      copy.append(title, detail);
      row.append(stateText, copy);
      return row;
    }),
  );
}

function updateOnboardingActions(onboarding, status) {
  const current = onboarding.current_step || "privacy";
  const captureReady = status.capture_preview?.state === "ok";
  const canComplete = Boolean(onboarding.can_complete);
  setActionVisibility("[data-onboarding-privacy]", current === "privacy");
  setActionVisibility("[data-onboarding-check]", ["app_access", "capture_check"].includes(current));
  setActionVisibility("[data-onboarding-intent]", current === "daily_focus");
  setActionVisibility("[data-open-accessibility]", ["app_access", "capture_check"].includes(current));
  setActionVisibility("[data-open-automation]", captureReady);
  setActionVisibility("[data-open-chrome]", captureReady);
  setActionVisibility("[data-onboarding-browser]", captureReady && onboarding.browser_detail?.state !== "enabled");
  setActionVisibility("[data-onboarding-skip-browser]", captureReady && onboarding.browser_detail?.state !== "skipped");
  const complete = document.querySelector("[data-onboarding-complete]");
  if (complete) {
    complete.disabled = !canComplete;
    complete.title = canComplete
      ? "Finish first-run setup"
      : `Finish after ${onboarding.completion_blockers?.join(", ") || "required steps"}`;
  }
}

function setActionVisibility(selector, visible) {
  const node = document.querySelector(selector);
  if (node) {
    node.hidden = !visible;
  }
}

function userFacingPermission(item) {
  const label = String(item.label || "");
  if (label === "Local service") {
    return {
      ...item,
      label: "IntentOS connection",
      detail: "The review board can read local activity data.",
    };
  }
  if (label === "Local database") {
    return {
      ...item,
      label: "Local storage",
      detail: "Your review history is available on this Mac.",
    };
  }
  if (label === "Browser Automation") {
    return {
      ...item,
      label: "Browser detail",
      detail: item.state === "not_applicable"
        ? "Optional unless you want richer browser titles and URLs."
        : "IntentOS can add browser titles and URLs when allowed.",
    };
  }
  if (label === "Native recorder") {
    return {
      ...item,
      label: "Activity capture",
      detail: "IntentOS is watching app and window metadata locally.",
    };
  }
  if (label === "Chrome bridge") {
    return {
      ...item,
      label: "Browser extension detail",
      detail: "Optional: adds richer browser tab context when installed.",
    };
  }
  if (label === "Privacy mode") {
    return {
      ...item,
      label: "Privacy",
      detail: "Screenshots, keylogging, page bodies, cookies, and cloud sync stay off.",
    };
  }
  if (label === "Delete local data") {
    return {
      ...item,
      label: "Delete local data",
      detail: "Available from the menu bar when you need to clear this Mac.",
    };
  }
  return item;
}

function permissionStateLabel(state) {
  if (state === "ok") {
    return "Ready";
  }
  if (state === "needs_action") {
    return "Action";
  }
  if (state === "blocked") {
    return "Blocked";
  }
  if (state === "not_applicable") {
    return "Optional";
  }
  return "Check";
}

function renderSetupGuidance(guidance) {
  const wrapper = document.querySelector("[data-setup-guidance]");
  if (!wrapper) {
    return;
  }
  if (!guidance) {
    wrapper.hidden = true;
    wrapper.replaceChildren();
    return;
  }
  const title = document.createElement("h3");
  title.textContent = userFacingSetupCopy(guidance.title || "Setup");
  const summary = document.createElement("p");
  summary.textContent = userFacingSetupCopy(guidance.summary || "");
  const steps = document.createElement("ol");
  (guidance.steps || []).forEach((step) => {
    const row = document.createElement("li");
    row.textContent = userFacingSetupCopy(step);
    steps.append(row);
  });
  const verify = document.createElement("p");
  verify.className = "setup-verify";
  verify.textContent = userFacingSetupCopy(
    guidance.verify || "Run checks again after making changes.",
  );
  wrapper.replaceChildren(title, summary, steps, verify);
  wrapper.hidden = false;
}

function userFacingSetupCopy(text) {
  return String(text || "")
    .replaceAll("Chrome Extensions", "Browser detail")
    .replaceAll("Chrome extension", "browser extension")
    .replaceAll("Chrome bridge", "browser extension")
    .replaceAll("native recorder", "activity capture")
    .replaceAll("Native recorder", "Activity capture")
    .replaceAll("Browser Automation", "Browser access")
    .replaceAll("local beta", "IntentOS")
    .replaceAll("beta", "IntentOS");
}

function bindOnboardingActions(betaConfig) {
  const bindings = [
    ["[data-onboarding-privacy]", async () => postJson(betaConfig, "/api/onboarding", { action: "acknowledge_privacy" })],
    ["[data-onboarding-check]", async () => postJson(betaConfig, "/api/permissions/check", {})],
    ["[data-onboarding-intent]", async () => {
      document.querySelector("#daily-loop-title")?.scrollIntoView({ block: "start", inline: "nearest" });
      return { status: "opened" };
    }],
    ["[data-onboarding-browser]", async () => {
      await postJson(betaConfig, "/api/onboarding", { action: "enable_browser_detail" });
      return openSetting(betaConfig, "automation");
    }],
    ["[data-onboarding-skip-browser]", async () => postJson(betaConfig, "/api/onboarding", { action: "skip_browser_detail" })],
    ["[data-open-accessibility]", async () => openSetting(betaConfig, "accessibility")],
    ["[data-open-automation]", async () => openSetting(betaConfig, "automation")],
    ["[data-open-chrome]", async () => openSetting(betaConfig, "chrome_extensions")],
    ["[data-open-diagnostics]", async () => openSetting(betaConfig, "diagnostics")],
    ["[data-copy-setup-report]", async () => copySetupReport(betaConfig)],
    ["[data-onboarding-reset]", async () => postJson(betaConfig, "/api/onboarding", { action: "reset" })],
    ["[data-onboarding-complete]", async () => postJson(betaConfig, "/api/onboarding", { action: "complete" })],
    ["[data-onboarding-dismiss]", async () => postJson(betaConfig, "/api/onboarding", { action: "dismiss", minutes: 240 })],
  ];
  bindings.forEach(([selector, handler]) => {
    const button = document.querySelector(selector);
    if (!button) {
      return;
    }
    button.onclick = async () => {
      await handler();
      await boot();
    };
  });
}

async function openSetting(betaConfig, target) {
  const result = await postJson(betaConfig, "/api/open-system-settings", { target });
  currentSetupGuidance = result.guidance || null;
  renderSetupGuidance(currentSetupGuidance);
  return result;
}

async function copySetupReport(betaConfig) {
  const report = await loadBetaJson(betaConfig, "/api/setup-report");
  const text = JSON.stringify(report.setup_report || report, null, 2);
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
  }
  currentSetupGuidance = {
    title: "Setup report",
    summary: "A redacted setup report is ready for troubleshooting.",
    steps: navigator.clipboard?.writeText
      ? ["The report was copied to the clipboard."]
      : ["Clipboard access is unavailable here; open diagnostics from the menu bar."],
    verify: "This report excludes raw titles, URLs, screenshots, cookies, and page bodies.",
  };
  renderSetupGuidance(currentSetupGuidance);
  return report;
}
