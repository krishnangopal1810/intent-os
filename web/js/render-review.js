function renderWeeklyPatterns(weekly) {
  const detail = document.querySelector("[data-weekly-details]");
  const narrative = document.querySelector("[data-weekly-narrative]");
  const wrapper = document.querySelector("[data-weekly-patterns]");
  if (!detail || !narrative || !wrapper) {
    return;
  }
  if (!weekly) {
    detail.hidden = true;
    detail.open = false;
    wrapper.replaceChildren();
    return;
  }
  detail.hidden = false;
  narrative.textContent = weekly.narrative || "Weekly patterns will appear after local activity accumulates.";
  wrapper.replaceChildren(...(weekly.patterns || []).slice(0, 3).map((pattern) => {
    const card = document.createElement("article");
    card.className = "weekly-card";
    const label = document.createElement("span");
    label.textContent = pattern.title || "Pattern";
    const value = document.createElement("strong");
    value.textContent = pattern.value || "Building";
    const note = document.createElement("p");
    note.textContent = pattern.detail || "Keep IntentOS running while you work.";
    card.append(label, value, note);
    return card;
  }));
}

function quotedList(tokens) {
  return tokens.slice(0, 4).map((token) => `"${token}"`).join(", ");
}

function surfaceName(item) {
  return item?.surface || item?.title || item?.source_app || "the matching surface";
}

function sidebarStatusText(status) {
  const readiness = status.readiness?.label || "Review";
  if (status.pause?.paused) {
    return `${readiness}. Capture paused`;
  }
  const recorderState = friendlyState(status.native_recorder?.state || "not started");
  if (recorderState === "running") {
    return `${readiness}. Capture running`;
  }
  if (recorderState === "not started") {
    return `${readiness}. Capture waiting`;
  }
  return `${readiness}. Capture ${recorderState}`;
}

function renderActionDeck(summary, items, options = {}) {
  const deck = document.querySelector("[data-action-deck]");
  const reviewItems = items || [];
  const nextMove = buildNextMove(summary, reviewItems, options);

  const cards = [
    {
      label: nextMove.label,
      kicker: "Do next",
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
    ? `${captureItems.length} timeline segment${captureItems.length === 1 ? "" : "s"} loaded from local activity.`
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
      value: captureItems.length ? `${replayConfidence}%` : "Waiting",
      note: captureItems.length
        ? replayNote
        : "No captured activity yet. IntentOS will fill this in as local metadata arrives.",
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
    row.textContent = "Activity evidence will appear after about 20 minutes of normal work.";
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
  const rescue = window.__intentosFocusRescue;
  if (rescue?.rescue_key && ["recovery_available", "avoid_leaking"].includes(rescue.state)) {
    await postFocusRescueAction(
      betaConfig,
      rescue,
      "corrected_evidence",
      "Correction submitted from the evidence timeline.",
      item.segment_key || "",
    );
  }
}
