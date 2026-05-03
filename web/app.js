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

const focusLabels = ["deep_work", "learning", "active_creation"];
const attentionLeakLabels = ["passive_consumption", "entertainment"];
const reviewLabels = ["unknown"];

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
  const total = summary.total_seconds || 0;
  const focusSeconds = sumLabelSeconds(summary, focusLabels);
  const leakSeconds = sumLabelSeconds(summary, attentionLeakLabels);
  const unknownSeconds = sumLabelSeconds(summary, reviewLabels);
  if (unknownSeconds && percentage(unknownSeconds, total) >= 10) {
    return `Trust gap: ${formatDuration(unknownSeconds)} needs review before the score is useful.`;
  }
  if (leakSeconds && percentage(leakSeconds, total) >= 20) {
    return `Mixed day: ${formatLabel(label)} led at ${Math.round(data.percentage)}%; ${formatDuration(leakSeconds)} needs a boundary.`;
  }
  if (focusSeconds && percentage(focusSeconds, total) >= 60) {
    return `Aligned day: ${formatDuration(focusSeconds)} stayed in high-value work.`;
  }
  return `${formatLabel(label)} led the day at ${Math.round(data.percentage)}%; ${data.duration} captured.`;
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

function sumLabelSeconds(summary, labelList) {
  return labelList.reduce((sum, label) => sum + labelSeconds(summary, label), 0);
}

function sortedLabelRows(summary) {
  return Object.entries(summary.labels || {}).sort(
    (left, right) => right[1].seconds - left[1].seconds,
  );
}

function compactText(text, maxLength = 74) {
  const value = String(text || "").trim();
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength - 3).trim()}...`;
}

function itemDuration(item) {
  return item.duration || formatDuration(item.duration_seconds || 0);
}

function itemSurface(item) {
  if (!item) {
    return "";
  }
  return item.url || item.surface || item.source_app || "";
}

function itemTitle(item) {
  if (!item) {
    return "";
  }
  const source = item.source_app ? `${item.source_app}: ` : "";
  return compactText(`${source}${item.title || item.surface || "Untitled"}`);
}

function topItemForLabels(items, labelList) {
  return [...(items || [])]
    .filter((item) => labelList.includes(item.label))
    .sort((left, right) => (right.duration_seconds || 0) - (left.duration_seconds || 0))[0] || null;
}

function lowConfidenceItems(items) {
  return (items || []).filter((item) => item.label === "unknown" || item.confidence < 0.7);
}

function averageConfidence(items) {
  if (!items.length) {
    return 0;
  }
  return Math.round(
    (items.reduce((sum, item) => sum + (item.confidence || 0), 0) /
      items.length) *
      100,
  );
}

function attentionProfile(summary) {
  const total = summary.total_seconds || 0;
  const focusSeconds = sumLabelSeconds(summary, focusLabels);
  const leakSeconds = sumLabelSeconds(summary, attentionLeakLabels);
  const unknownSeconds = sumLabelSeconds(summary, reviewLabels);
  const focusPercent = percentage(focusSeconds, total);
  const leakPercent = percentage(leakSeconds, total);
  const unknownPercent = percentage(unknownSeconds, total);
  if (!total) {
    return {
      title: "No signal yet",
      kicker: "Waiting for local data",
      scoreTitle: "No review yet",
      scoreCaption: "Start capture or load fixture reports to see the day.",
      actionCopy: "No tracked activity is available for this review.",
    };
  }
  if (unknownPercent >= 10) {
    return {
      title: "Trust gap visible",
      kicker: "Needs review",
      scoreTitle: "Needs correction",
      scoreCaption: `${formatDuration(unknownSeconds)} is still unknown or low-confidence.`,
      actionCopy: "Clear the ambiguous rows before treating the score as truth.",
    };
  }
  if (leakPercent >= 30) {
    return {
      title: "Attention leak",
      kicker: "Pull here",
      scoreTitle: "Recoverable drift",
      scoreCaption: `${formatDuration(leakSeconds)} went to passive or entertainment surfaces.`,
      actionCopy: "The next block needs a boundary before another open-ended tab.",
    };
  }
  if (focusPercent >= 60) {
    return {
      title: "Aligned day",
      kicker: "Strong signal",
      scoreTitle: "Strong alignment",
      scoreCaption: `${formatDuration(focusSeconds)} was focused, learning, or creation time.`,
      actionCopy: "Repeat the block that made the day work.",
    };
  }
  return {
    title: "Mixed alignment",
    kicker: "Today's signal",
    scoreTitle: "Mixed alignment",
    scoreCaption: `${formatDuration(focusSeconds)} was high-value activity and ${formatDuration(leakSeconds)} was reactive.`,
    actionCopy: "Start the next block with one constraint, then let the review keep score.",
  };
}

function buildNextMove(summary, items, options = {}) {
  const total = summary.total_seconds || 0;
  const focusSeconds = sumLabelSeconds(summary, focusLabels);
  const leakSeconds = sumLabelSeconds(summary, attentionLeakLabels);
  const unknownSeconds = sumLabelSeconds(summary, reviewLabels);
  const lowConfidence = lowConfidenceItems(items);
  const topFocus = topItemForLabels(items, focusLabels);
  const topLeak = topItemForLabels(items, attentionLeakLabels);

  if (!total) {
    return {
      label: "unknown",
      metric: "No rows",
      title: options.beta ? "Check the local service" : "Start a clean review window",
      note: options.beta
        ? "The beta dashboard is connected, but no daily activity is available yet."
        : "Run a local capture session or keep the dashboard open while you work.",
    };
  }
  if (leakSeconds > 0 && leakSeconds >= unknownSeconds) {
    const leakName = topLeak ? itemTitle(topLeak) : "passive surfaces";
    return {
      label: topLeak?.label || "passive_consumption",
      metric: formatDuration(leakSeconds),
      title: "Close the leak before the next block",
      note: `${compactText(leakName, 84)} is the clearest place to set a cap or remove the surface.`,
    };
  }
  if (unknownSeconds > 0 || lowConfidence.length > 0) {
    return {
      label: "unknown",
      metric: unknownSeconds ? formatDuration(unknownSeconds) : `${lowConfidence.length} rows`,
      title: "Resolve the trust gap",
      note: "Correct or inspect ambiguous evidence before changing behavior from this review.",
    };
  }
  if (focusSeconds > 0) {
    return {
      label: topFocus?.label || "deep_work",
      metric: `${percentage(focusSeconds, total)}% focus`,
      title: "Repeat the strongest block",
      note: topFocus
        ? `${itemTitle(topFocus)} is the behavior to protect next.`
        : "Your highest-value labels are carrying the review.",
    };
  }
  return {
    label: "admin",
    metric: formatDuration(total),
    title: "Name the next intent",
    note: "The review is populated, but it has not found a high-value block yet.",
  };
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

function renderBriefMoments(summary) {
  const wrapper = document.querySelector("[data-brief-moments]");
  const rows = sortedLabelRows(summary).slice(0, 3);
  if (!rows.length) {
    const empty = document.createElement("span");
    empty.className = "brief-moment label-unknown";
    empty.textContent = "No behavior signal yet";
    wrapper.replaceChildren(empty);
    return;
  }

  wrapper.replaceChildren(
    ...rows.map(([label, data]) => {
      const item = document.createElement("span");
      item.className = `brief-moment ${labelClass(label)}`;
      const value = document.createElement("strong");
      value.textContent = data.duration;
      const name = document.createElement("span");
      name.textContent = formatLabel(label);
      item.append(value, name);
      return item;
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
  const focusSeconds = sumLabelSeconds(summary, focusLabels);
  return percentage(focusSeconds, summary.total_seconds || 0);
}

function renderScore(summary) {
  const score = focusShare(summary);
  const profile = attentionProfile(summary);
  const ring = document.querySelector("[data-focus-ring]");
  const scoreValue = document.querySelector("[data-focus-score]");
  const scoreTitle = document.querySelector("[data-score-title]");
  const scoreCaption = document.querySelector("[data-score-caption]");

  ring.style.setProperty("--score", `${score}%`);
  scoreValue.textContent = `${score}`;
  scoreTitle.textContent = profile.scoreTitle;
  scoreCaption.textContent = profile.scoreCaption;
}

function renderNextMove(summary, items, options = {}) {
  const profile = attentionProfile(summary);
  const nextMove = buildNextMove(summary, items, options);
  document.querySelector("[data-brief-kicker]").textContent = profile.kicker;
  document.querySelector("[data-primary-action-copy]").textContent =
    profile.actionCopy;
  document.querySelector("[data-next-move-title]").textContent = nextMove.title;
  document.querySelector("[data-next-move-note]").textContent =
    `${nextMove.metric} - ${nextMove.note}`;
}

function renderActionDeck(summary, items, options = {}) {
  const deck = document.querySelector("[data-action-deck]");
  const reviewItems = items || [];
  const topFocus = topItemForLabels(reviewItems, focusLabels);
  const topLeak = topItemForLabels(reviewItems, attentionLeakLabels);
  const lowConfidence = lowConfidenceItems(reviewItems);
  const nextMove = buildNextMove(summary, reviewItems, options);
  const focusSeconds = sumLabelSeconds(summary, focusLabels);
  const leakSeconds = sumLabelSeconds(summary, attentionLeakLabels);
  const confidence = averageConfidence(reviewItems);

  const cards = [
    topFocus
      ? {
          label: topFocus.label,
          kicker: "Repeat",
          metric: itemDuration(topFocus),
          title: itemTitle(topFocus),
          note: `Best high-value block from ${itemSurface(topFocus)}.`,
        }
      : {
          label: "deep_work",
          kicker: "Repeat",
          metric: formatDuration(focusSeconds),
          title: "No focus block found yet",
          note: "The review has not seen deep work, learning, or creation.",
        },
    topLeak
      ? {
          label: topLeak.label,
          kicker: "Contain",
          metric: itemDuration(topLeak),
          title: itemTitle(topLeak),
          note: `${formatDuration(leakSeconds)} total attention leak is visible.`,
        }
      : {
          label: "active_creation",
          kicker: "Contain",
          metric: "Clean",
          title: "No passive loop in the evidence",
          note: "The current review is not dominated by consumption or entertainment.",
        },
    lowConfidence.length
      ? {
          label: "unknown",
          kicker: "Trust",
          metric: `${lowConfidence.length} rows`,
          title: itemTitle(lowConfidence[0]),
          note: "Correct the label so future reviews feel sharper.",
        }
      : {
          label: "learning",
          kicker: "Trust",
          metric: reviewItems.length ? `${confidence}%` : "No rows",
          title: reviewItems.length ? "Evidence is readable" : "Waiting for evidence",
          note: reviewItems.length
            ? "No low-confidence segment is asking for review."
            : "Open the dashboard during a work session to collect local metadata.",
        },
    {
      label: nextMove.label,
      kicker: "Next",
      metric: nextMove.metric,
      title: nextMove.title,
      note: nextMove.note,
    },
  ];

  deck.replaceChildren(...cards.map(renderDecisionCard));
}

function renderDecisionCard(card) {
  const wrapper = document.createElement("article");
  wrapper.className = `decision-card ${labelClass(card.label || "unknown")}`;
  const kicker = document.createElement("p");
  kicker.className = "decision-kicker";
  kicker.textContent = card.kicker;
  const metric = document.createElement("div");
  metric.className = "decision-metric";
  metric.textContent = card.metric;
  const title = document.createElement("h3");
  title.textContent = card.title;
  const note = document.createElement("p");
  note.className = "decision-note";
  note.textContent = card.note;
  wrapper.append(kicker, metric, title, note);
  return wrapper;
}

function renderInsights(summary, capture, options = {}) {
  const insights = document.querySelector("[data-insights]");
  const focusSeconds = sumLabelSeconds(summary, focusLabels);
  const driftSeconds = sumLabelSeconds(summary, attentionLeakLabels);
  const total = summary.total_seconds || 0;
  const captureItems = capture.items || [];
  const replayConfidence = averageConfidence(captureItems);
  const replayNote = options.beta
    ? `${captureItems.length} live service segment${captureItems.length === 1 ? "" : "s"} loaded from SQLite.`
    : options.live
      ? `${captureItems.length} live capture segment${captureItems.length === 1 ? "" : "s"} loaded.`
      : `${captureItems.length} capture event${captureItems.length === 1 ? "" : "s"} loaded from local fixture replay.`;
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
      value: captureItems.length ? `${replayConfidence}%` : "No rows",
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
  const emptySummary = { labels: {}, total_seconds: 0 };
  document.querySelector("[data-primary-total]").textContent = "--";
  document.querySelector("[data-primary-narrative]").textContent = message;
  document.querySelector("[data-status]").textContent =
    "Live beta service unavailable";
  document.querySelector("[data-activity-source]").textContent =
    "Local beta service";
  document.querySelector("[data-capture-source]").textContent =
    "No fixture fallback";
  document.querySelector("[data-stats]").replaceChildren();
  document.querySelector("[data-insights]").replaceChildren();
  document.querySelector("[data-activity-bars]").replaceChildren();
  renderBriefMoments(emptySummary);
  renderFocusMeter(emptySummary);
  renderScore(emptySummary);
  renderNextMove(emptySummary, [], { beta: true });
  renderActionDeck(emptySummary, [], { beta: true });
  renderTimelineWithOptions([], null);
  renderBetaQueues(null);
  renderOnboarding(null, null, null);
}

function renderLiveUnavailable(message) {
  const emptySummary = { labels: {}, total_seconds: 0 };
  document.querySelector("[data-primary-total]").textContent = "--";
  document.querySelector("[data-primary-narrative]").textContent = message;
  document.querySelector("[data-status]").textContent =
    "Live capture unavailable";
  document.querySelector("[data-activity-source]").textContent =
    "Live capture";
  document.querySelector("[data-capture-source]").textContent =
    "No fixture fallback";
  document.querySelector("[data-stats]").replaceChildren();
  document.querySelector("[data-insights]").replaceChildren();
  document.querySelector("[data-activity-bars]").replaceChildren();
  renderBriefMoments(emptySummary);
  renderFocusMeter(emptySummary);
  renderScore(emptySummary);
  renderNextMove(emptySummary, [], { live: true });
  renderActionDeck(emptySummary, [], { live: true });
  renderTimelineWithOptions([], null);
  renderBetaQueues(null);
  renderOnboarding(null, null, null);
}

async function bootArtifacts(options = {}) {
  const requiredLivePaths = options.requiredLivePaths || null;
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
    await renderArtifactReport(captureResult, null, { live: true });
    return;
  }

  const [activity, captureResult] = await Promise.all([
    loadJson(paths.activity),
    loadFirst([...paths.liveCapture, ...paths.fixtureCapture]),
  ]);
  await renderArtifactReport(captureResult, activity, { live: false });
}

async function renderArtifactReport(captureResult, activity, options) {
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
  const dayItems = isLiveSession || isLiveCapture
    ? capture.items || []
    : activity?.items || capture.items || [];
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

  renderBriefMoments(primarySummary);
  renderFocusMeter(primarySummary);
  renderScore(primarySummary);
  renderNextMove(primarySummary, dayItems, options);
  renderActionDeck(primarySummary, dayItems, options);
  renderInsights(primarySummary, capture, options);
  renderStats(primarySummary);
  renderBars(primarySummary);
  renderTimeline(capture.items || []);
  renderBetaQueues(null);
  renderOnboarding(null, null, null);
}

async function bootBeta(betaConfig) {
  const date = betaConfig.date || new Date().toISOString().slice(0, 10);
  const [review, onboarding] = await Promise.all([
    loadJson(apiUrl(betaConfig, `/api/daily-review?date=${encodeURIComponent(date)}`)),
    loadJson(apiUrl(betaConfig, "/api/onboarding")),
  ]);
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
  document.querySelector("[data-status]").textContent =
    `${readiness} - ${paused} - Native recorder ${recorderState} - Chrome bridge ${extensionState}`;
  document.querySelector("[data-activity-source]").textContent =
    `Local beta service - ${scopeLabel}`;
  document.querySelector("[data-capture-source]").textContent =
    `SQLite daily timeline - ${scopeLabel}`;

  renderFocusMeter(review.summary);
  renderScore(review.summary);
  renderBriefMoments(review.summary);
  renderNextMove(review.summary, review.items || [], { beta: true });
  renderActionDeck(review.summary, review.items || [], { beta: true });
  renderInsights(review.summary, review, { beta: true });
  renderStats(review.summary);
  renderBars(review.summary);
  renderTimelineWithOptions(review.items || [], betaConfig);
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
