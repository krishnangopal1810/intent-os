const paths = {
  activity: "../artifacts/activity-summary.json",
  liveCapture: [
    "../artifacts/live-session-capture-summary.json",
    "../artifacts/live-capture-summary.json",
  ],
  fixtureCapture: [
    "../artifacts/session-capture-summary.json",
    "../artifacts/capture-summary.json",
  ],
  captureStatus: "../artifacts/live-capture-status.json",
  youtube: "../artifacts/youtube-summary.json",
};

const labels = {
  deep_work: "Deep work",
  learning: "Learning",
  communication: "Communication",
  admin: "Admin",
  passive_consumption: "Passive consumption",
  active_creation: "Active creation",
  entertainment: "Entertainment",
  unknown: "Unknown",
};

let currentSetupGuidance = null;

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json();
}

async function loadOptionalJson(path) {
  try {
    return await loadJson(path);
  } catch (error) {
    return null;
  }
}

function apiUrl(config, path) {
  return `${config.serviceUrl}${path}`;
}

function dashboardMode() {
  const params = new URLSearchParams(window.location.search);
  return params.get("mode") || "";
}

function requiresBetaServiceMode() {
  return dashboardMode() === "beta" ||
    new URLSearchParams(window.location.search).get("beta") === "1";
}

function liveCapturePaths(mode) {
  if (mode === "live-session") {
    return ["../artifacts/live-session-capture-summary.json"];
  }
  if (mode === "live-capture") {
    return ["../artifacts/live-capture-summary.json"];
  }
  if (mode === "live") {
    return paths.liveCapture;
  }
  return null;
}

async function loadFirst(pathsToTry) {
  const errors = [];
  for (const path of pathsToTry) {
    try {
      return { path, data: await loadJson(path) };
    } catch (error) {
      errors.push(error.message);
    }
  }
  throw new Error(errors.join("; "));
}

function formatLabel(label) {
  return labels[label] || label.replaceAll("_", " ");
}

function formatNarrative(text) {
  return text.replace(/\b[a-z]+(?:_[a-z]+)+\b/g, (match) =>
    formatLabel(match).toLowerCase(),
  );
}

function summaryHeadline(summary) {
  const rows = Object.entries(summary.labels || {}).sort(
    (left, right) => right[1].seconds - left[1].seconds,
  );
  if (!rows.length) {
    return formatNarrative(summary.narrative);
  }
  const [label, data] = rows[0];
  return `${formatLabel(label)} led the day at ${Math.round(data.percentage)}%, with ${data.duration} captured across tracked activity.`;
}

function labelClass(label) {
  return `label-${label.replaceAll("_", "_")}`;
}

function percentage(value, total) {
  if (!total) {
    return 0;
  }
  return Math.round((value / total) * 100);
}

function labelSeconds(summary, label) {
  return summary.labels?.[label]?.seconds || 0;
}

function labelDuration(summary, label) {
  return summary.labels?.[label]?.duration || "0s";
}

function formatClock(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDuration(seconds) {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  if (seconds >= 3600) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.round((seconds % 3600) / 60);
    return minutes ? `${hours}h ${minutes}m` : `${hours}h`;
  }
  const minutes = Math.round(seconds / 60);
  return `${minutes}m`;
}

function renderStats(summary) {
  const stats = document.querySelector("[data-stats]");
  const rows = Object.entries(summary.labels || {})
    .sort((left, right) => right[1].seconds - left[1].seconds)
    .slice(0, 4);

  stats.replaceChildren(
    ...rows.map(([label, data]) => {
      const wrapper = document.createElement("div");
      wrapper.className = `stat ${labelClass(label)}`;
      const term = document.createElement("dt");
      term.textContent = formatLabel(label);
      const value = document.createElement("dd");
      value.textContent = data.duration;
      wrapper.append(term, value);
      return wrapper;
    }),
  );
}

function renderFocusMeter(summary) {
  const meter = document.querySelector("[data-focus-meter]");
  const labelsInOrder = [
    "deep_work",
    "learning",
    "active_creation",
    "admin",
    "communication",
    "passive_consumption",
    "entertainment",
    "unknown",
  ];
  const total = summary.total_seconds || 0;
  meter.replaceChildren(
    ...labelsInOrder
      .filter((label) => labelSeconds(summary, label) > 0)
      .map((label) => {
        const segment = document.createElement("div");
        segment.className = `meter-segment meter-${label}`;
        segment.style.width = `${Math.max(2, percentage(labelSeconds(summary, label), total))}%`;
        segment.title = `${formatLabel(label)}: ${labelDuration(summary, label)}`;
        return segment;
      }),
  );
}

function focusShare(summary) {
  const focusSeconds =
    labelSeconds(summary, "deep_work") +
    labelSeconds(summary, "learning") +
    labelSeconds(summary, "active_creation");
  return percentage(focusSeconds, summary.total_seconds || 0);
}

function renderScore(summary) {
  const score = focusShare(summary);
  const ring = document.querySelector("[data-focus-ring]");
  const scoreValue = document.querySelector("[data-focus-score]");
  const scoreTitle = document.querySelector("[data-score-title]");
  const scoreCaption = document.querySelector("[data-score-caption]");
  const drift =
    labelSeconds(summary, "passive_consumption") +
    labelSeconds(summary, "entertainment");

  ring.style.setProperty("--score", `${score}%`);
  scoreValue.textContent = `${score}`;
  scoreTitle.textContent = score >= 60 ? "Strong alignment" : "Mixed alignment";
  scoreCaption.textContent =
    drift > 0
      ? `${formatDuration(drift)} of reactive activity is visible in the review.`
      : "No reactive activity appeared in this report.";
}

function renderInsights(summary, capture, youtube, options = {}) {
  const insights = document.querySelector("[data-insights]");
  const focusSeconds =
    labelSeconds(summary, "deep_work") +
    labelSeconds(summary, "learning") +
    labelSeconds(summary, "active_creation");
  const driftSeconds =
    labelSeconds(summary, "passive_consumption") +
    labelSeconds(summary, "entertainment");
  const total = summary.total_seconds || 0;
  const captureItems = capture.items || [];
  const averageConfidence = captureItems.length
    ? Math.round(
        (captureItems.reduce((sum, item) => sum + item.confidence, 0) /
          captureItems.length) *
          100,
      )
    : 0;
  const youtubeLearning = Math.round(youtube.summary?.learning_percentage || 0);
  const replayNote = options.beta
    ? `${captureItems.length} live service segment${captureItems.length === 1 ? "" : "s"} loaded from SQLite.`
    : options.live
      ? `${captureItems.length} live capture segment${captureItems.length === 1 ? "" : "s"} loaded.`
      : `${captureItems.length} capture event${captureItems.length === 1 ? "" : "s"} loaded. YouTube learning mix is ${youtubeLearning}%.`;
  const rows = [
    {
      label: "Focused work",
      value: `${percentage(focusSeconds, total)}%`,
      note: `${formatDuration(focusSeconds)} in deep work, learning, or active creation.`,
      className: "label-deep_work",
    },
    {
      label: "Reactive time",
      value: `${percentage(driftSeconds, total)}%`,
      note: `${formatDuration(driftSeconds)} in passive consumption or entertainment.`,
      className: "label-passive_consumption",
    },
    {
      label: "Replay confidence",
      value: captureItems.length ? `${averageConfidence}%` : "No rows",
      note: replayNote,
      className: "label-learning",
    },
  ];

  insights.replaceChildren(
    ...rows.map((item) => {
      const wrapper = document.createElement("article");
      wrapper.className = `insight ${item.className}`;
      const title = document.createElement("div");
      title.className = "insight-title";
      title.textContent = item.label;
      const value = document.createElement("div");
      value.className = "insight-value";
      value.textContent = item.value;
      const note = document.createElement("p");
      note.className = "insight-note";
      note.textContent = item.note;
      wrapper.append(title, value, note);
      return wrapper;
    }),
  );
}

function renderBars(summary) {
  const bars = document.querySelector("[data-activity-bars]");
  const rows = Object.entries(summary.labels || {}).sort(
    (left, right) => right[1].percentage - left[1].percentage,
  );

  bars.replaceChildren(
    ...rows.map(([label, data]) => {
      const row = document.createElement("div");
      row.className = `bar-row ${labelClass(label)}`;

      const labelRow = document.createElement("div");
      labelRow.className = "bar-label";
      const name = document.createElement("span");
      name.textContent = formatLabel(label);
      const value = document.createElement("span");
      value.textContent = `${data.duration} - ${data.percentage}%`;
      labelRow.append(name, value);

      const track = document.createElement("div");
      track.className = "track";
      const fill = document.createElement("div");
      fill.className = "fill";
      fill.style.width = `${Math.max(2, data.percentage)}%`;
      track.append(fill);

      row.append(labelRow, track);
      return row;
    }),
  );
}

function renderTimeline(items) {
  return renderTimelineWithOptions(items, null);
}

function renderTimelineWithOptions(items, betaConfig) {
  const list = document.querySelector("[data-capture-events]");
  if (!items.length) {
    const row = document.createElement("li");
    row.className = "timeline-empty";
    row.textContent = "No capture rows available";
    list.replaceChildren(row);
    return;
  }

  list.replaceChildren(
    ...items.slice(0, 8).map((item) => {
      const row = document.createElement("li");
      row.className = `timeline-item ${labelClass(item.label)}`;
      const time = document.createElement("span");
      time.className = "event-time";
      time.textContent = `${formatClock(item.started_at)} · ${formatDuration(
        item.duration_seconds,
      )}`;
      const title = document.createElement("span");
      title.className = "event-title";
      title.textContent = `${item.source_app} - ${item.title}`;
      const surface = document.createElement("span");
      surface.className = "event-surface";
      surface.textContent = item.url
        ? `${item.surface} - ${item.url}`
        : item.surface;
      const meta = document.createElement("span");
      meta.className = "event-meta";
      const samples =
        item.sample_count && item.sample_count > 1
          ? ` - ${item.sample_count} samples`
          : "";
      const duration = item.duration || formatDuration(item.duration_seconds);
      meta.textContent = `${duration} - ${formatLabel(item.label)} - ${Math.round(item.confidence * 100)}%${samples}`;
      row.append(time, title, surface, meta);
      if (betaConfig && item.segment_key) {
        row.append(renderCorrectionControl(item, betaConfig));
      }
      return row;
    }),
  );
}

function renderCorrectionControl(item, betaConfig) {
  const wrapper = document.createElement("div");
  wrapper.className = "event-correction";
  const select = document.createElement("select");
  select.setAttribute("aria-label", `Correct label for ${item.title}`);
  Object.keys(labels).forEach((label) => {
    const option = document.createElement("option");
    option.value = label;
    option.textContent = formatLabel(label);
    select.append(option);
  });
  select.value = item.label;
  const future = document.createElement("label");
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = false;
  future.append(checkbox, document.createTextNode("Apply to future"));
  select.addEventListener("change", async () => {
    await postCorrection(betaConfig, item, select.value, checkbox.checked);
    await boot();
  });
  wrapper.append(select, future);
  return wrapper;
}

async function postCorrection(betaConfig, item, correctedLabel, applyToFuture) {
  const endpointNote = "POST /api/corrections";
  await postJson(betaConfig, "/api/corrections", {
      segment: item,
      corrected_label: correctedLabel,
      apply_to_future: applyToFuture,
      endpoint: endpointNote,
    });
}

async function postJson(betaConfig, path, payload) {
  const response = await fetch(apiUrl(betaConfig, path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status}`);
  }
  return response.json();
}

function renderBetaQueues(review) {
  const wrapper = document.querySelector("[data-beta-review-queues]");
  const correctionMarker = document.querySelector("[data-correction-controls]");
  if (!review) {
    wrapper.hidden = true;
    correctionMarker.hidden = true;
    return;
  }
  wrapper.hidden = false;
  correctionMarker.hidden = false;
  renderQueue("[data-top-deep-work]", review.top_deep_work || []);
  renderQueue("[data-top-reactive-surfaces]", review.top_reactive_surfaces || []);
  renderQueue("[data-low-confidence-segments]", review.low_confidence_segments || []);
}

function renderQueue(selector, items) {
  const list = document.querySelector(selector);
  if (!items.length) {
    const row = document.createElement("li");
    row.textContent = "None";
    list.replaceChildren(row);
    return;
  }
  list.replaceChildren(
    ...items.slice(0, 3).map((item) => {
      const row = document.createElement("li");
      row.textContent = `${formatLabel(item.label)} - ${item.title} (${item.duration || formatDuration(item.duration_seconds)})`;
      return row;
    }),
  );
}

function renderYoutubeMeter(summary) {
  const meter = document.querySelector("[data-youtube-meter]");
  const learning = summary.learning_percentage || 0;
  const passive = summary.passive_consumption_percentage || 0;
  const unknown = summary.unknown_percentage || 0;
  const entertainment = Math.max(0, 100 - learning - passive - unknown);
  const rows = [
    ["learning", learning],
    ["passive_consumption", passive],
    ["entertainment", entertainment],
    ["unknown", unknown],
  ].filter((row) => row[1] > 0);

  meter.replaceChildren(
    ...rows.map(([label, value]) => {
      const segment = document.createElement("div");
      segment.className = `meter-segment meter-${label}`;
      segment.style.width = `${Math.max(2, Math.round(value))}%`;
      segment.title = `${formatLabel(label)}: ${Math.round(value)}%`;
      return segment;
    }),
  );
}

function setDomainSliceVisible(visible) {
  const youtubePanel = document.querySelector(".youtube-panel");
  const youtubeNav = document.querySelector('a[href="#youtube-title"]');
  if (youtubePanel) {
    youtubePanel.hidden = !visible;
  }
  if (youtubeNav) {
    youtubeNav.hidden = !visible;
  }
}

function captureStatusText(isLiveCapture, status) {
  if (!isLiveCapture) {
    return "Fixture reports loaded";
  }
  if (!status) {
    return "Timeline starting";
  }
  if (status.state === "running") {
    const segments = status.timeline_events ?? status.events ?? 0;
    return `Timeline running - ${segments} segment${segments === 1 ? "" : "s"}`;
  }
  return `Timeline ${status.state}`;
}

async function boot() {
  const mode = dashboardMode();
  const betaRequired = requiresBetaServiceMode();
  const requiredLivePaths = liveCapturePaths(mode);
  const betaConfig = await loadOptionalJson("./beta-config.json");
  if (betaConfig?.serviceUrl) {
    await bootBeta(betaConfig);
    return;
  }
  if (betaRequired) {
    renderBetaUnavailable(
      "Live beta configuration is missing. Start Beta from the menu bar or run make beta-dev so the dashboard can connect to local SQLite data.",
    );
    return;
  }
  await bootArtifacts({ requiredLivePaths });
}

function renderBetaUnavailable(message) {
  setDomainSliceVisible(false);
  document.querySelector("[data-primary-total]").textContent = "--";
  document.querySelector("[data-primary-narrative]").textContent = message;
  document.querySelector("[data-youtube-narrative]").textContent = "";
  document.querySelector("[data-status]").textContent =
    "Live beta service unavailable";
  document.querySelector("[data-activity-source]").textContent =
    "Local beta service";
  document.querySelector("[data-capture-source]").textContent =
    "No fixture fallback";
  document.querySelector("[data-stats]").replaceChildren();
  document.querySelector("[data-insights]").replaceChildren();
  document.querySelector("[data-activity-bars]").replaceChildren();
  renderFocusMeter({ labels: {}, total_seconds: 0 });
  renderScore({ labels: {}, total_seconds: 0 });
  renderTimelineWithOptions([], null);
  renderYoutubeMeter({});
  renderBetaQueues(null);
  renderOnboarding(null, null, null);
}

function renderLiveUnavailable(message) {
  setDomainSliceVisible(false);
  document.querySelector("[data-primary-total]").textContent = "--";
  document.querySelector("[data-primary-narrative]").textContent = message;
  document.querySelector("[data-youtube-narrative]").textContent = "";
  document.querySelector("[data-status]").textContent =
    "Live capture unavailable";
  document.querySelector("[data-activity-source]").textContent =
    "Live capture";
  document.querySelector("[data-capture-source]").textContent =
    "No fixture fallback";
  document.querySelector("[data-stats]").replaceChildren();
  document.querySelector("[data-insights]").replaceChildren();
  document.querySelector("[data-activity-bars]").replaceChildren();
  renderFocusMeter({ labels: {}, total_seconds: 0 });
  renderScore({ labels: {}, total_seconds: 0 });
  renderTimelineWithOptions([], null);
  renderYoutubeMeter({});
  renderBetaQueues(null);
  renderOnboarding(null, null, null);
}

async function bootArtifacts(options = {}) {
  const requiredLivePaths = options.requiredLivePaths || null;
  setDomainSliceVisible(!requiredLivePaths);
  if (requiredLivePaths) {
    let captureResult;
    try {
      captureResult = await loadFirst(requiredLivePaths);
    } catch (error) {
      renderLiveUnavailable(
        `Live capture data is missing. Start a live session with make dev-live or start the beta app so IntentOS can load real local data. ${error.message}`,
      );
      return;
    }
    await renderArtifactReport(captureResult, null, null, { live: true });
    return;
  }

  const [activity, captureResult, youtube] = await Promise.all([
    loadJson(paths.activity),
    loadFirst([...paths.liveCapture, ...paths.fixtureCapture]),
    loadJson(paths.youtube),
  ]);
  await renderArtifactReport(captureResult, activity, youtube, { live: false });
}

async function renderArtifactReport(captureResult, activity, youtube, options) {
  const capture = captureResult.data;
  const isLiveSession = captureResult.path.includes("live-session");
  const isSession = captureResult.path.includes("session-capture");
  const isLiveCapture = captureResult.path.includes("live-capture");
  const captureSource = isLiveSession
      ? "Live session timeline"
      : isSession
        ? "Fixture session timeline"
        : isLiveCapture
          ? "Live background timeline"
          : "Fixture replay";
  const primarySummary = isLiveSession || isLiveCapture
    ? capture.summary
    : activity?.summary;
  const primarySource = isLiveSession || isLiveCapture
    ? captureSource
    : "Daily activity report";
  let status = null;
  if (isLiveCapture) {
    try {
      status = await loadJson(paths.captureStatus);
    } catch (error) {
      status = null;
    }
  }

  document.querySelector("[data-primary-total]").textContent =
    primarySummary.total_duration || formatDuration(primarySummary.total_seconds || 0);
  document.querySelector("[data-primary-narrative]").textContent =
    summaryHeadline(primarySummary);
  document.querySelector("[data-youtube-narrative]").textContent =
    youtube ? formatNarrative(youtube.summary.narrative) : "";
  const statusText = isLiveCapture
    ? captureStatusText(isLiveCapture, status)
    : isLiveSession
      ? "Live session loaded"
      : "Fixture reports loaded";
  const captureLabel =
    isLiveCapture && status
      ? `${captureSource} - ${status.interval_seconds}s`
      : captureSource;
  document.querySelector("[data-status]").textContent = statusText;
  document.querySelector("[data-activity-source]").textContent = primarySource;
  document.querySelector("[data-capture-source]").textContent = captureLabel;

  renderFocusMeter(primarySummary);
  renderScore(primarySummary);
  renderInsights(primarySummary, capture, youtube || {}, options);
  renderStats(primarySummary);
  renderBars(primarySummary);
  renderTimeline(capture.items || []);
  renderYoutubeMeter(youtube?.summary || {});
  renderBetaQueues(null);
  renderOnboarding(null, null, null);
}

async function bootBeta(betaConfig) {
  setDomainSliceVisible(false);
  const date = betaConfig.date || new Date().toISOString().slice(0, 10);
  const [review, onboarding] = await Promise.all([
    loadJson(apiUrl(betaConfig, `/api/daily-review?date=${encodeURIComponent(date)}`)),
    loadJson(apiUrl(betaConfig, "/api/onboarding")),
  ]);
  const betaContext = {
    summary: {
      narrative: "",
      learning_percentage: 0,
      passive_consumption_percentage: 0,
      unknown_percentage: 0,
    },
  };
  const status = review.status || {};
  const scopeLabel = review.scope?.label || "Today since midnight";
  const extensionState = status.extension?.state || "not connected";
  const recorderState = status.native_recorder?.state || "not started";
  const paused = status.pause?.paused ? "Paused" : "Running";
  const readiness = status.readiness?.label || "Beta";

  document.querySelector("[data-primary-total]").textContent =
    review.summary.total_duration || formatDuration(review.summary.total_seconds || 0);
  document.querySelector("[data-primary-narrative]").textContent =
    summaryHeadline(review.summary);
  document.querySelector("[data-youtube-narrative]").textContent = "";
  document.querySelector("[data-status]").textContent =
    `${readiness} - ${paused} - Native recorder ${recorderState} - Chrome bridge ${extensionState}`;
  document.querySelector("[data-activity-source]").textContent =
    `Local beta service - ${scopeLabel}`;
  document.querySelector("[data-capture-source]").textContent =
    `SQLite daily timeline - ${scopeLabel}`;

  renderFocusMeter(review.summary);
  renderScore(review.summary);
  renderInsights(review.summary, review, betaContext, { beta: true });
  renderStats(review.summary);
  renderBars(review.summary);
  renderTimelineWithOptions(review.items || [], betaConfig);
  renderYoutubeMeter(betaContext.summary);
  renderBetaQueues(review);
  renderOnboarding(betaConfig, onboarding.onboarding, status);
}

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
  renderPermissionChecklist(status);
  renderSetupGuidance(currentSetupGuidance);
  bindOnboardingActions(betaConfig);
}

function renderPermissionChecklist(status) {
  const list = document.querySelector("[data-permission-checklist]");
  const permissions = status.permissions || {};
  const items = [
    permissions.local_service,
    permissions.database,
    permissions.accessibility,
    permissions.browser_automation,
    permissions.native_recorder,
    permissions.chrome_extension,
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
      const row = document.createElement("div");
      row.className = `permission-item permission-${item.state}`;
      const stateText = document.createElement("span");
      stateText.className = "permission-state";
      stateText.textContent = permissionStateLabel(item.state);
      const copy = document.createElement("span");
      copy.className = "permission-copy";
      const title = document.createElement("strong");
      title.textContent = item.label;
      const detail = document.createElement("span");
      detail.textContent = item.detail;
      copy.append(title, detail);
      row.append(stateText, copy);
      return row;
    }),
  );
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
  title.textContent = guidance.title || "Setup";
  const summary = document.createElement("p");
  summary.textContent = guidance.summary || "";
  const steps = document.createElement("ol");
  (guidance.steps || []).forEach((step) => {
    const row = document.createElement("li");
    row.textContent = step;
    steps.append(row);
  });
  const verify = document.createElement("p");
  verify.className = "setup-verify";
  verify.textContent = guidance.verify || "Run checks again after making changes.";
  wrapper.replaceChildren(title, summary, steps, verify);
  wrapper.hidden = false;
}

function bindOnboardingActions(betaConfig) {
  const bindings = [
    ["[data-onboarding-check]", async () => postJson(betaConfig, "/api/permissions/check", {})],
    ["[data-open-accessibility]", async () => openSetting(betaConfig, "accessibility")],
    ["[data-open-automation]", async () => openSetting(betaConfig, "automation")],
    ["[data-open-chrome]", async () => openSetting(betaConfig, "chrome_extensions")],
    ["[data-open-diagnostics]", async () => openSetting(betaConfig, "diagnostics")],
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

boot().catch((error) => {
  document.querySelector("[data-status]").textContent = "Report load failed";
  document.querySelector("[data-primary-narrative]").textContent = error.message;
});

setInterval(() => {
  boot().catch((error) => {
    document.querySelector("[data-status]").textContent = "Report load failed";
    document.querySelector("[data-primary-narrative]").textContent = error.message;
  });
}, 2000);
