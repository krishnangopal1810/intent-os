const paths = {
  activity: "../artifacts/activity-summary.json",
  capture: [
    "../artifacts/live-session-capture-summary.json",
    "../artifacts/session-capture-summary.json",
    "../artifacts/live-capture-summary.json",
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

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json();
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

function renderInsights(summary, capture, youtube) {
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
  const youtubeLearning = Math.round(
    youtube.summary?.learning_percentage || 0,
  );
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
      note: `${captureItems.length} capture event${captureItems.length === 1 ? "" : "s"} loaded. YouTube learning mix is ${youtubeLearning}%.`,
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

function captureStatusText(isLiveCapture, status) {
  if (!isLiveCapture) {
    return "Fixture reports loaded";
  }
  if (!status) {
    return "Live capture starting";
  }
  if (status.state === "running") {
    return `Live capture running - ${status.events} event${status.events === 1 ? "" : "s"}`;
  }
  return `Live capture ${status.state}`;
}

async function boot() {
  const [activity, captureResult, youtube] = await Promise.all([
    loadJson(paths.activity),
    loadFirst(paths.capture),
    loadJson(paths.youtube),
  ]);
  const capture = captureResult.data;
  const isLiveSession = captureResult.path.includes("live-session");
  const isSession = captureResult.path.includes("session-capture");
  const isLiveCapture = captureResult.path.includes("live-capture");
  const captureSource = isLiveSession
    ? "Live session timeline"
    : isSession
      ? "Fixture session timeline"
      : isLiveCapture
        ? "Live capture replay"
        : "Fixture replay";
  const primarySummary = isLiveSession || isLiveCapture
    ? capture.summary
    : activity.summary;
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
    formatNarrative(youtube.summary.narrative);
  const statusText = isLiveCapture
    ? captureStatusText(isLiveCapture, status)
    : isLiveSession
      ? "Live capture loaded"
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
  renderInsights(primarySummary, capture, youtube);
  renderStats(primarySummary);
  renderBars(primarySummary);
  renderTimeline(capture.items || []);
  renderYoutubeMeter(youtube.summary);
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
