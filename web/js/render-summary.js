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

function renderCommandCenter(summary, items, loop, options = {}) {
  const reviewItems = items || [];
  const nextMove = buildNextMove(summary, reviewItems, { ...options, loop });
  const rescue = loop?.focus_rescue || null;
  const lowConfidence = lowConfidenceItems(reviewItems);
  const confidence = averageConfidence(reviewItems);
  const correctionCount = loop?.correction_count || 0;
  if (rescue && ["recovery_available", "avoid_leaking"].includes(rescue.state)) {
    setCommandStep("now", {
      title: rescue.label || "Recovery available",
      note: rescue.reason || "The avoid pattern is active enough to rescue this block.",
      action: "Open rescue",
      href: "#summary-title",
    });
  } else {
    setCommandStep("now", {
      title: nextMove.title,
      note: `${nextMove.metric} - ${nextMove.note}`,
      action: "Open next block",
      href: "#decision-title",
    });
  }

  let trustTitle = "Waiting for evidence";
  let trustNote = "IntentOS will show unclear rows here when the review needs correction.";
  let trustAction = "Review evidence";
  if (options.unavailable) {
    trustTitle = "Reconnect first";
    trustNote = "The review needs local activity data before it can show trust gaps.";
    trustAction = "Open timeline";
  } else if (lowConfidence.length) {
    trustTitle = `${lowConfidence.length} row${lowConfidence.length === 1 ? "" : "s"} need review`;
    trustNote = `Start with ${itemTitle(lowConfidence[0])}; corrections make future reviews sharper.`;
    trustAction = "Fix labels";
  } else if (correctionCount) {
    trustTitle = `${correctionCount} correction${correctionCount === 1 ? "" : "s"} applied`;
    trustNote = "Future reviews will classify these surfaces better.";
    trustAction = "Check evidence";
  } else if (reviewItems.length) {
    trustTitle = `${confidence}% readable evidence`;
    trustNote = "No low-confidence segment is asking for review right now.";
    trustAction = "Review evidence";
  }
  setCommandStep("trust", {
    title: trustTitle,
    note: trustNote,
    action: trustAction,
    href: "#timeline-title",
  });

  const prompt = loop?.prompt || {};
  const plan = loop?.plan_vs_actual || {};
  const checkin = loop?.review_checkin || null;
  let tonightTitle = "Set today's intent";
  let tonightNote = "Pick one focus and one thing to avoid so tonight's review has a plan to compare.";
  let tonightAction = "Set intent";
  if (options.unavailable) {
    tonightTitle = "Reconnect to plan";
    tonightNote = "Today's intent and evening review will appear once IntentOS reconnects.";
    tonightAction = "Open intent";
  } else if (prompt.state === "review_due") {
    tonightTitle = "Evening review is ready";
    tonightNote = plan.actual_summary || "The day has enough signal to compare plan with reality.";
    tonightAction = "Review today";
  } else if (prompt.state === "review_complete") {
    tonightTitle = "Tomorrow is sharper";
    tonightNote = checkin?.next_adjustment
      ? `Next adjustment: ${checkin.next_adjustment}`
      : "Today's reflection and corrections will carry into the next review.";
    tonightAction = "Open review";
  } else if (["running", "tracking"].includes(prompt.state)) {
    tonightTitle = "Intent is set";
    tonightNote = plan.actual_summary || "Keep working; the evening review will unlock after enough signal.";
    tonightAction = "Open intent";
  }
  setCommandStep("tonight", {
    title: tonightTitle,
    note: tonightNote,
    action: tonightAction,
    href: "#daily-loop-title",
  });
}

function setCommandStep(key, values) {
  const title = document.querySelector(`[data-command-${key}-title]`);
  const note = document.querySelector(`[data-command-${key}-note]`);
  const action = document.querySelector(`[data-command-${key}-action]`);
  if (!title || !note || !action) {
    return;
  }
  title.textContent = values.title;
  note.textContent = values.note;
  action.textContent = values.action;
  action.setAttribute("href", values.href);
}
