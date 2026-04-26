const paths = {
  activity: "../artifacts/activity-summary.json",
  capture: [
    "../artifacts/live-session-capture-summary.json",
    "../artifacts/session-capture-summary.json",
    "../artifacts/live-capture-summary.json",
    "../artifacts/capture-summary.json",
  ],
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

function labelClass(label) {
  return `label-${label.replaceAll("_", "_")}`;
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
      const meta = document.createElement("span");
      meta.className = "event-meta";
      meta.textContent = `${formatLabel(item.label)} - ${Math.round(item.confidence * 100)}%`;
      row.append(time, title, meta);
      return row;
    }),
  );
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
  const primarySummary = isLiveSession || isSession || isLiveCapture
    ? capture.summary
    : activity.summary;

  document.querySelector("[data-primary-narrative]").textContent =
    formatNarrative(primarySummary.narrative);
  document.querySelector("[data-youtube-narrative]").textContent =
    formatNarrative(youtube.summary.narrative);
  document.querySelector("[data-status]").textContent =
    isLiveSession || isLiveCapture ? "Live capture loaded" : "Fixture reports loaded";
  document.querySelector("[data-activity-source]").textContent = captureSource;
  document.querySelector("[data-capture-source]").textContent = captureSource;

  renderStats(primarySummary);
  renderBars(primarySummary);
  renderTimeline(capture.items || []);
}

boot().catch((error) => {
  document.querySelector("[data-status]").textContent = "Report load failed";
  document.querySelector("[data-primary-narrative]").textContent = error.message;
});
