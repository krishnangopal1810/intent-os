const paths = {
  activity: "../artifacts/activity-summary.json",
  capture: [
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

function renderStats(summary) {
  const stats = document.querySelector("[data-stats]");
  const rows = Object.entries(summary.labels || {})
    .sort((left, right) => right[1].seconds - left[1].seconds)
    .slice(0, 4);

  stats.replaceChildren(
    ...rows.map(([label, data]) => {
      const wrapper = document.createElement("div");
      wrapper.className = "stat";
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
      row.className = "bar-row";

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

function renderEvents(items) {
  const list = document.querySelector("[data-capture-events]");
  list.replaceChildren(
    ...items.slice(0, 5).map((item) => {
      const row = document.createElement("li");
      const title = document.createElement("span");
      title.className = "event-title";
      title.textContent = `${item.source_app} - ${item.title}`;
      const meta = document.createElement("span");
      meta.className = "event-meta";
      meta.textContent = `${formatLabel(item.label)} - ${Math.round(item.confidence * 100)}%`;
      row.append(title, meta);
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
  const isLiveCapture = captureResult.path.includes("live-capture");

  document.querySelector("[data-primary-narrative]").textContent =
    isLiveCapture ? capture.summary.narrative : activity.summary.narrative;
  document.querySelector("[data-youtube-narrative]").textContent =
    youtube.summary.narrative;
  document.querySelector("[data-status]").textContent = isLiveCapture
    ? "Live capture loaded"
    : "Fixture reports loaded";
  document.querySelector("[data-activity-source]").textContent = isLiveCapture
    ? "Live capture replay"
    : "Fixture replay";

  renderStats(isLiveCapture ? capture.summary : activity.summary);
  renderBars(isLiveCapture ? capture.summary : activity.summary);
  renderEvents(capture.items || []);
}

boot().catch((error) => {
  document.querySelector("[data-status]").textContent = "Report load failed";
  document.querySelector("[data-primary-narrative]").textContent = error.message;
});
