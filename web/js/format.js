function weekStartDate(dateString) {
  const parts = String(dateString || "").split("-").map((part) => Number(part));
  if (parts.length !== 3 || parts.some((part) => Number.isNaN(part))) {
    return dateString;
  }
  const date = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]));
  if (Number.isNaN(date.getTime())) {
    return dateString;
  }
  const daysSinceMonday = (date.getUTCDay() + 6) % 7;
  date.setUTCDate(date.getUTCDate() - daysSinceMonday);
  return date.toISOString().slice(0, 10);
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

function friendlyState(value) {
  const state = String(value || "").replaceAll("_", " ").toLowerCase();
  if (state === "never connected") {
    return "not connected";
  }
  if (state === "posting events") {
    return "connected";
  }
  return state || "unknown";
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
    actionCopy: "Start the next block with one constraint, then check the evidence tonight.",
  };
}

function buildNextMove(summary, items, options = {}) {
  if (options.loop?.next_block) {
    const block = options.loop.next_block;
    const confidence = Math.round((block.confidence || 0) * 100);
    return {
      label: nextBlockLabel(block),
      metric: confidence ? `${confidence}% match` : "Next",
      title: block.title || "Choose the next block",
      note: [block.detail, block.suggested_constraint].filter(Boolean).join(" "),
    };
  }
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
      metric: "Waiting",
      title: options.beta ? "Waiting for today's activity" : "Start a clean review window",
      note: options.beta
        ? options.unavailable
          ? "Reconnect IntentOS to continue today's review."
          : "Keep IntentOS running while you work; the review will fill in automatically."
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

function nextBlockLabel(block) {
  const text = `${block.title || ""} ${block.detail || ""}`.toLowerCase();
  if (text.includes("trust") || text.includes("unclear") || text.includes("correct")) {
    return "unknown";
  }
  if (text.includes("close") || text.includes("leak") || text.includes("cap")) {
    return "passive_consumption";
  }
  if (text.includes("start")) {
    return "deep_work";
  }
  return "admin";
}
