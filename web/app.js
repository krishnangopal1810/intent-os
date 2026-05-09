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
let navScrollFrame = null;

async function loadJson(path, options = {}) {
  const response = await fetch(path, { cache: "no-store", ...options });
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

function apiHeaders(config) {
  return config?.apiToken ? { "X-IntentOS-Token": config.apiToken } : {};
}

async function loadBetaJson(config, path) {
  return loadJson(apiUrl(config, path), { headers: apiHeaders(config) });
}

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

function bindServiceNotice() {
  const button = document.querySelector("[data-service-retry]");
  if (!button || button.dataset.bound) {
    return;
  }
  button.dataset.bound = "true";
  button.addEventListener("click", () => {
    boot().catch(renderLoadProblem);
  });
}

function renderServiceNotice(title, body, action = "Open the current dashboard from the menu bar.") {
  const panel = document.querySelector("[data-service-notice]");
  if (!panel) {
    return;
  }
  bindServiceNotice();
  panel.hidden = false;
  document.querySelector("[data-service-notice-title]").textContent = title;
  document.querySelector("[data-service-notice-body]").textContent = body;
  document.querySelector("[data-service-notice-action]").textContent = action;
}

function hideServiceNotice() {
  const panel = document.querySelector("[data-service-notice]");
  if (panel) {
    panel.hidden = true;
  }
}

function renderLoadProblem(error) {
  console.error(error);
  if (requiresBetaServiceMode()) {
    renderBetaUnavailable(
      "This dashboard is not connected to IntentOS right now. Open the current dashboard from the menu bar, or restart IntentOS and try again.",
    );
    return;
  }
  renderLiveUnavailable(
    "IntentOS could not load local review data. Restart the local dashboard and try again.",
  );
}

function bindSectionNavigation() {
  const links = Array.from(
    document.querySelectorAll(".nav-item[href^='#'], [data-scroll-link][href^='#']"),
  );
  const workspace = document.querySelector(".workspace");
  if (!links.length || !workspace) {
    return;
  }
  if (!document.body.dataset.sectionNavBound) {
    document.body.dataset.sectionNavBound = "true";
    links.forEach((link) => {
      link.addEventListener("click", (event) => {
        const hash = link.getAttribute("href") || "";
        const target = hash.startsWith("#")
          ? document.getElementById(hash.slice(1))
          : null;
        if (!target) {
          return;
        }
        event.preventDefault();
        openDisclosureForTarget(target);
        setActiveNav(navHashForTarget(hash));
        history.pushState(null, "", hash);
        scrollTargetIntoWorkspace(target);
        window.setTimeout(() => scrollTargetIntoWorkspace(target), 60);
      });
    });
    workspace.addEventListener("scroll", () => {
      if (navScrollFrame) {
        return;
      }
      navScrollFrame = requestAnimationFrame(() => {
        navScrollFrame = null;
        updateActiveNavFromScroll();
      });
    }, { passive: true });
    window.addEventListener("hashchange", () => {
      setActiveNav(window.location.hash || "#summary-title");
    });
  }
  const initialHash = window.location.hash || "#summary-title";
  setActiveNav(initialHash);
  if (window.location.hash) {
    const target = document.getElementById(window.location.hash.slice(1));
    if (target) {
      openDisclosureForTarget(target);
      scrollTargetIntoWorkspace(target);
    }
  }
}

function openDisclosureForTarget(target) {
  const disclosure = target.closest("details");
  if (disclosure && !disclosure.open) {
    disclosure.open = true;
  }
}

function scrollTargetIntoWorkspace(target) {
  const workspace = document.querySelector(".workspace");
  if (!workspace || !target) {
    return;
  }
  openDisclosureForTarget(target);
  const workspaceRect = workspace.getBoundingClientRect();
  const targetRect = target.getBoundingClientRect();
  const nextTop = workspace.scrollTop + targetRect.top - workspaceRect.top - 18;
  workspace.scrollTo({ top: Math.max(0, nextTop), behavior: "auto" });
  window.scrollTo({ top: 0, left: 0, behavior: "auto" });
}

function setActiveNav(hash) {
  const selected = navHashForTarget(hash || "#summary-title");
  document.querySelectorAll(".nav-item[href^='#']").forEach((link) => {
    link.classList.toggle("active", link.getAttribute("href") === selected);
  });
}

function navHashForTarget(hash) {
  if (document.querySelector(`.nav-item[href="${hash}"]`)) {
    return hash;
  }
  if (hash === "#daily-loop-title") {
    return "#summary-title";
  }
  return hash || "#summary-title";
}

function updateActiveNavFromScroll() {
  const workspace = document.querySelector(".workspace");
  const links = Array.from(document.querySelectorAll(".nav-item[href^='#']"));
  if (!workspace || !links.length) {
    return;
  }
  const anchorTop = workspace.getBoundingClientRect().top + 24;
  const hashTarget = window.location.hash
    ? document.getElementById(window.location.hash.slice(1))
    : null;
  if (hashTarget) {
    const workspaceRect = workspace.getBoundingClientRect();
    const targetRect = hashTarget.getBoundingClientRect();
    const targetVisible =
      targetRect.top >= workspaceRect.top - 1 &&
      targetRect.bottom <= workspaceRect.bottom + 1;
    if (targetVisible || Math.abs(targetRect.top - anchorTop) < 80) {
      setActiveNav(window.location.hash);
      return;
    }
  }
  let current = links[0].getAttribute("href") || "#summary-title";
  links.forEach((link) => {
    const hash = link.getAttribute("href") || "";
    const target = hash.startsWith("#")
      ? document.getElementById(hash.slice(1))
      : null;
    if (target && target.getBoundingClientRect().top <= anchorTop) {
      current = hash;
    }
  });
  setActiveNav(current);
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

function renderCoachHero(summary, items, loop, options = {}) {
  const hero = document.querySelector("[data-coach-hero]");
  if (!hero) {
    return;
  }
  const plan = loop?.plan_vs_actual || {};
  const contract = loop?.intent_contract || {};
  const rescue = loop?.focus_rescue || null;
  const rescueMessage = rescueHeroMessage(rescue);
  const profile = attentionProfile(summary);
  const nextMove = buildNextMove(summary, items || [], { ...options, loop });
  const verdict = rescueMessage?.title || plan.verdict || (summary.total_seconds
    ? profile.actionCopy
    : "Work normally for 20 minutes; IntentOS will compare activity to today's plan.");
  const actual = rescueMessage?.note || plan.actual_summary || nextMove.note ||
    "IntentOS will compare local activity against the plan once evidence appears.";
  const focusSide = plan.protected_focus || {};
  const avoidSide = plan.avoid_target || {};

  document.querySelector("[data-coach-verdict]").textContent = verdict;
  document.querySelector("[data-coach-actual]").textContent = actual;
  document.querySelector("[data-coach-focus]").textContent =
    contract.focus_text || focusSide.text || "Set one focus";
  document.querySelector("[data-coach-focus-detail]").textContent =
    focusSide.matched_signal
      ? `${focusSide.duration} matched ${surfaceName(focusSide.matched_signal)}.`
      : contract.focus_tokens?.length
        ? `Watching ${quotedList(contract.focus_tokens)} in app, title, domain, URL, and label signals.`
        : "Add a focus so tonight's review has something to protect.";
  document.querySelector("[data-coach-avoid]").textContent =
    contract.avoid_text || avoidSide.text || "Set one thing to avoid";
  document.querySelector("[data-coach-avoid-detail]").textContent =
    avoidSide.matched_signal
      ? `${avoidSide.duration} touched ${surfaceName(avoidSide.matched_signal)}.`
      : contract.avoid_tokens?.length
        ? `Watching ${quotedList(contract.avoid_tokens)} as avoid-side signals.`
        : "Add an avoid target so leaks are easy to spot.";
  renderCoachReceipts(plan.receipts || [], nextMove);
  renderFocusRescue(rescue, options.betaConfig || null);
}

function rescueHeroMessage(rescue) {
  if (!rescue?.state) {
    return null;
  }
  if (rescue.state === "recovery_available") {
    return {
      title: rescue.label || "Recovery available",
      note: rescue.reason || "The avoid pattern is active enough to rescue this block.",
    };
  }
  if (rescue.state === "avoid_leaking") {
    return {
      title: rescue.label || "Avoid leaking",
      note: rescue.reason || "You chose to continue intentionally; the receipt will keep that visible.",
    };
  }
  if (rescue.state === "focus_protected") {
    return {
      title: rescue.label || "Focus protected",
      note: rescue.reason || "The focus pattern is visible and avoid evidence is below the rescue threshold.",
    };
  }
  if (rescue.state === "intent_needed") {
    return {
      title: "Name today's focus",
      note: rescue.reason || "Set one focus and one thing to avoid before the day gets noisy.",
    };
  }
  return {
    title: rescue.label || "Need evidence",
    note: rescue.reason || "IntentOS needs more strict focus or avoid evidence before making a rescue call.",
  };
}

function renderFocusRescue(rescue, betaConfig) {
  const panel = document.querySelector("[data-focus-rescue]");
  const label = document.querySelector("[data-focus-rescue-label]");
  const reason = document.querySelector("[data-focus-rescue-reason]");
  const actions = document.querySelector("[data-focus-rescue-actions]");
  if (!panel || !label || !reason || !actions) {
    return;
  }
  if (!rescue?.state) {
    panel.hidden = true;
    actions.replaceChildren();
    window.__intentosFocusRescue = null;
    return;
  }
  window.__intentosFocusRescue = rescue;
  panel.hidden = false;
  label.textContent = rescue.label || loopStatusLabel(rescue.state);
  reason.textContent = rescue.reason || "IntentOS is waiting for strict focus or avoid evidence.";
  actions.replaceChildren(
    ...(rescue.available_choices || []).map((choice) => renderFocusRescueAction(choice, rescue, betaConfig)),
  );
  recordFocusRescueShown(rescue, betaConfig);
}

function renderFocusRescueAction(choice, rescue, betaConfig) {
  const button = document.createElement("button");
  button.type = "button";
  button.dataset.action = choice.action;
  button.dataset.kind = choice.kind || "secondary";
  button.textContent = choice.label || choice.action;
  button.addEventListener("click", async () => {
    if (choice.action === "correct_evidence") {
      openEvidenceForCorrection();
      return;
    }
    if (!betaConfig) {
      return;
    }
    await postFocusRescueAction(betaConfig, rescue, choice.action, choice.label || "");
    await boot();
  });
  return button;
}

function openEvidenceForCorrection() {
  const target = document.getElementById("timeline-title");
  if (!target) {
    return;
  }
  openDisclosureForTarget(target);
  setActiveNav("#activity-title");
  history.pushState(null, "", "#timeline-title");
  scrollTargetIntoWorkspace(target);
}

async function postFocusRescueAction(betaConfig, rescue, action, note = "", evidenceId = "") {
  if (!betaConfig || !rescue?.rescue_key) {
    return null;
  }
  return postJson(betaConfig, "/api/focus-rescue-action", {
    date: rescue.date || betaConfig.date,
    rescue_key: rescue.rescue_key,
    action,
    evidence_id: evidenceId || rescue.primary_evidence?.evidence_id || "",
    note,
  });
}

function recordFocusRescueShown(rescue, betaConfig) {
  if (
    !betaConfig ||
    rescue.state !== "recovery_available" ||
    rescue.latest_action ||
    !rescue.rescue_key
  ) {
    return;
  }
  window.__intentosShownRescues = window.__intentosShownRescues || new Set();
  if (window.__intentosShownRescues.has(rescue.rescue_key)) {
    return;
  }
  window.__intentosShownRescues.add(rescue.rescue_key);
  postFocusRescueAction(betaConfig, rescue, "shown", "Recovery card rendered.").catch((error) => {
    console.error(error);
  });
}

function renderCoachReceipts(receipts, fallbackMove) {
  const wrapper = document.querySelector("[data-coach-receipts]");
  if (!wrapper) {
    return;
  }
  const rows = receipts.length
    ? receipts.slice(0, 3)
    : [
        {
          label: "Preview",
          title: fallbackMove.title,
          duration: fallbackMove.metric,
          surface: fallbackMove.note,
        },
      ];
  wrapper.replaceChildren(...rows.map((receipt) => {
    const card = document.createElement("article");
    card.className = `receipt-card ${labelClass(receipt.label || receipt.kind || "unknown")}`;
    const label = document.createElement("span");
    label.textContent = receipt.label || "Evidence";
    const title = document.createElement("strong");
    title.textContent = receipt.title || receipt.surface || "Local activity";
    const note = document.createElement("p");
    const detail = receipt.surface && receipt.title !== receipt.surface
      ? `${receipt.surface} - ${receipt.duration || ""}`.trim()
      : receipt.duration || receipt.label || "";
    note.textContent = detail || "Evidence will appear as activity is captured.";
    card.append(label, title, note);
    return card;
  }));
}

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

async function postJson(betaConfig, path, payload) {
  const response = await fetch(apiUrl(betaConfig, path), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...apiHeaders(betaConfig) },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status}`);
  }
  return response.json();
}

function renderDailyLoop(loop, betaConfig) {
  const panel = document.querySelector("[data-daily-loop]");
  const status = document.querySelector("[data-loop-status]");
  const summary = document.querySelector("[data-loop-summary]");
  const current = document.querySelector("[data-intent-current]");
  const receipt = document.querySelector("[data-evening-receipt]");
  const intentForm = document.querySelector("[data-intent-form]");
  const contract = document.querySelector("[data-intent-contract]");
  const reviewForm = document.querySelector("[data-review-form]");
  if (!panel || !status || !summary || !current || !receipt || !intentForm || !contract || !reviewForm) {
    return;
  }
  bindDailyLoopForms(betaConfig);
  bindIntentContractPreview();
  intentForm.dataset.date = loop?.date || new Date().toISOString().slice(0, 10);
  reviewForm.dataset.date = intentForm.dataset.date;

  if (!betaConfig) {
    status.textContent = "Preview";
    summary.textContent =
      "Start IntentOS to set today's focus and complete an evening review.";
    current.hidden = true;
    receipt.hidden = true;
    intentForm.hidden = true;
    contract.hidden = true;
    reviewForm.hidden = true;
    return;
  }

  const prompt = loop?.prompt || {};
  const intent = loop?.intent || null;
  const checkin = loop?.review_checkin || null;
  const rescue = loop?.focus_rescue || null;
  status.textContent = rescue?.label || loopStatusLabel(prompt.state);
  summary.textContent = loopSummary(loop);
  current.hidden = !intent;
  renderEveningReceipt(loop?.evening_receipt || null, receipt, Boolean(intent));
  intentForm.hidden = Boolean(intent);
  contract.hidden = false;
  reviewForm.hidden = !(intent && prompt.review_due && !checkin);

  if (intent) {
    current.replaceChildren(...intentChips(loop));
    document.querySelector("[data-intent-focus]").value = intent.focus_text || "";
    document.querySelector("[data-intent-avoid]").value = intent.avoid_text || "";
    document.querySelector("[data-intent-note]").value = intent.note || "";
    renderIntentContract(loop.intent_contract || {});
  } else {
    current.replaceChildren();
    renderIntentContractPreview();
  }
}

function renderEveningReceipt(receipt, wrapper, hasIntent) {
  if (!wrapper) {
    return;
  }
  if (!hasIntent || !receipt) {
    wrapper.hidden = true;
    wrapper.replaceChildren();
    return;
  }
  const title = document.createElement("strong");
  title.textContent = receipt.title || "Evening receipt";
  const summary = document.createElement("p");
  summary.textContent = receipt.summary || "IntentOS is collecting local evidence for tonight.";
  const facts = document.createElement("div");
  facts.className = "receipt-facts";
  [
    ["Protected", receipt.protected_focus || "0s"],
    ["Avoid", receipt.avoid_leakage || "0s"],
    ["Rescue", receipt.rescue_state || "Need evidence"],
    ["Corrections", `${receipt.correction_count || 0}`],
  ].forEach(([label, value]) => {
    const fact = document.createElement("span");
    fact.textContent = `${label}: ${value}`;
    facts.append(fact);
  });
  wrapper.replaceChildren(title, summary, facts);
  wrapper.dataset.state = receipt.status || "collecting";
  wrapper.hidden = false;
}

function bindDailyLoopForms(betaConfig) {
  const intentForm = document.querySelector("[data-intent-form]");
  const reviewForm = document.querySelector("[data-review-form]");
  if (intentForm && !intentForm.dataset.bound) {
    intentForm.dataset.bound = "true";
    intentForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!window.__intentosBetaConfig) {
        return;
      }
      await postJson(window.__intentosBetaConfig, "/api/daily-intent", {
        date: intentForm.dataset.date,
        focus_text: document.querySelector("[data-intent-focus]").value,
        avoid_text: document.querySelector("[data-intent-avoid]").value,
        note: document.querySelector("[data-intent-note]").value,
      });
      await boot();
    });
  }
  if (reviewForm && !reviewForm.dataset.bound) {
    reviewForm.dataset.bound = "true";
    reviewForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!window.__intentosBetaConfig) {
        return;
      }
      await postJson(window.__intentosBetaConfig, "/api/review-checkin", {
        date: reviewForm.dataset.date,
        outcome: document.querySelector("[data-review-outcome]").value,
        reflection_text: document.querySelector("[data-review-reflection]").value,
        next_adjustment: document.querySelector("[data-review-next-adjustment]").value,
      });
      await boot();
    });
  }
  window.__intentosBetaConfig = betaConfig || null;
}

function bindIntentContractPreview() {
  const intentForm = document.querySelector("[data-intent-form]");
  if (!intentForm || intentForm.dataset.previewBound) {
    return;
  }
  intentForm.dataset.previewBound = "true";
  ["data-intent-focus", "data-intent-avoid", "data-intent-note"].forEach((attribute) => {
    const input = document.querySelector(`[${attribute}]`);
    if (input) {
      input.addEventListener("input", renderIntentContractPreview);
    }
  });
  renderIntentContractPreview();
}

function renderIntentContractPreview() {
  const focusInput = document.querySelector("[data-intent-focus]");
  const avoidInput = document.querySelector("[data-intent-avoid]");
  const noteInput = document.querySelector("[data-intent-note]");
  const focusTarget = document.querySelector("[data-contract-focus]");
  const avoidTarget = document.querySelector("[data-contract-avoid]");
  const reviewTarget = document.querySelector("[data-contract-review]");
  const questionTarget = document.querySelector("[data-contract-question]");
  if (!focusInput || !avoidInput || !focusTarget || !avoidTarget || !reviewTarget || !questionTarget) {
    return;
  }
  const focus = cleanIntentText(focusInput.value, focusInput.placeholder, "today's focus");
  const avoid = cleanIntentText(avoidInput.value, avoidInput.placeholder, "the avoid surface");
  const note = cleanIntentText(noteInput?.value || "", "", "");
  const focusSubject = contractSubject(focus, ["protect", "preserve", "keep"]);
  const avoidSubject = contractSubject(avoid, ["avoid", "cap", "limit", "reduce", "bound"]);
  const focusTerms = contractTerms(focus, ["deep work", "IntentOS", "code", "docs"]);
  const avoidTerms = contractTerms(avoid, ["LinkedIn feed", "scrolling", "reactive surface"]);
  focusTarget.textContent =
    `Look for ${focusTerms} in captured high-value app, page, title, URL, and label evidence.`;
  avoidTarget.textContent =
    `Flag ${avoidTerms} when it appears as reactive time or a matching surface.`;
  reviewTarget.textContent = note
    ? `Tonight's check-in compares that plan with actual behavior and carries this context forward: ${note}.`
    : "Tonight's check-in compares that plan with actual behavior and carries one adjustment into tomorrow.";
  questionTarget.textContent =
    `Tonight: did "${focusSubject}" stay protected while "${avoidSubject}" stayed bounded?`;
}

function renderIntentContract(contract) {
  const focusTarget = document.querySelector("[data-contract-focus]");
  const avoidTarget = document.querySelector("[data-contract-avoid]");
  const reviewTarget = document.querySelector("[data-contract-review]");
  const questionTarget = document.querySelector("[data-contract-question]");
  if (!focusTarget || !avoidTarget || !reviewTarget || !questionTarget) {
    return;
  }
  const focusTerms = quotedList(contract.focus_tokens || []);
  const avoidTerms = quotedList(contract.avoid_tokens || []);
  const focusMatches = signalSummary(contract.matched_focus_signals || []);
  const avoidMatches = signalSummary(contract.matched_avoid_signals || []);
  focusTarget.textContent = focusMatches
    ? `Matched ${focusMatches}; still watching ${focusTerms || "the focus words"}.`
    : `Watching ${focusTerms || "the focus words"} in app, domain, title, URL, and label evidence.`;
  avoidTarget.textContent = avoidMatches
    ? `Matched ${avoidMatches}; treat this as the avoid side.`
    : `Watching ${avoidTerms || "the avoid words"} for reactive app, domain, title, URL, and label evidence.`;
  reviewTarget.textContent = contract.explanation ||
    "Tonight's check-in compares the plan with actual behavior and carries one adjustment into tomorrow.";
  questionTarget.textContent =
    `Tonight: did "${contract.focus_text || "today's focus"}" stay protected while "${contract.avoid_text || "the avoid target"}" stayed bounded?`;
}

function signalSummary(signals) {
  return signals
    .slice(0, 3)
    .map((signal) => `${signal.kind}: ${signal.value}`)
    .join("; ");
}

function cleanIntentText(value, fallback, emptyFallback) {
  const text = String(value || "").trim() || String(fallback || "").trim();
  return text || emptyFallback;
}

function contractSubject(value, commands) {
  let subject = String(value || "").trim();
  commands.forEach((command) => {
    subject = subject.replace(new RegExp(`^${command}\\s+`, "i"), "");
  });
  return subject || value;
}

function contractTerms(value, fallback) {
  const ignored = new Set([
    "and",
    "cap",
    "for",
    "from",
    "one",
    "protect",
    "the",
    "this",
    "that",
    "today",
    "with",
  ]);
  const terms = String(value || "")
    .split(/[^a-z0-9]+/i)
    .filter((term) => term.length >= 3 && !ignored.has(term.toLowerCase()))
    .slice(0, 4);
  const selected = terms.length ? terms : fallback;
  return selected.map((term) => `"${term}"`).join(", ");
}

function loopStatusLabel(state) {
  if (state === "recovery_available") {
    return "Recovery available";
  }
  if (state === "avoid_leaking") {
    return "Avoid leaking";
  }
  if (state === "focus_protected") {
    return "Focus protected";
  }
  if (state === "evidence_insufficient") {
    return "Need evidence";
  }
  if (state === "intent_needed") {
    return "Intent needed";
  }
  if (state === "intent_due") {
    return "Intent due";
  }
  if (state === "review_due") {
    return "Review due";
  }
  if (state === "review_complete") {
    return "Review complete";
  }
  return "Tracking";
}

function loopSummary(loop) {
  if (!loop) {
    return "Your focus and evening review will appear here once IntentOS reconnects.";
  }
  const prompt = loop.prompt || {};
  const plan = loop.plan_vs_actual || {};
  const rescue = loop.focus_rescue || null;
  if (rescue?.reason) {
    return rescue.reason;
  }
  if (prompt.state === "intent_due") {
    return prompt.reason || "Set one focus and one thing to avoid for today's review.";
  }
  if (prompt.state === "review_due") {
    return `${plan.actual_summary || "The day has enough signal."} Complete the evening review to carry one adjustment forward.`;
  }
  if (prompt.state === "review_complete") {
    const checkin = loop.review_checkin || {};
    return checkin.next_adjustment
      ? `Review complete. Next adjustment: ${checkin.next_adjustment}`
      : "Review complete. Tomorrow's review will use today's corrections.";
  }
  return plan.actual_summary || "Intent is set; keep the dashboard open while the day unfolds.";
}

function intentChips(loop) {
  const intent = loop.intent || {};
  const checkin = loop.review_checkin || null;
  const plan = loop.plan_vs_actual || {};
  const reward = loop.correction_reward || {};
  const rescue = loop.focus_rescue || {};
  const chips = [
    {
      label: "Rescue state",
      value: rescue.label || "Need evidence",
      note: rescue.reason || "IntentOS is waiting for strict focus or avoid evidence.",
    },
    {
      label: "Protected focus",
      value: intent.focus_text,
      note: plan.matched_focus
        ? `${plan.matched_focus.duration} matched ${plan.matched_focus.title}.`
        : `${plan.focus_duration || "0s"} high-value activity so far.`,
    },
    {
      label: "Avoided surface",
      value: intent.avoid_text,
      note: plan.matched_avoid
        ? `${plan.matched_avoid.duration} touched ${plan.matched_avoid.title}.`
        : `${plan.reactive_duration || "0s"} reactive time is visible.`,
    },
    {
      label: "Accuracy",
      value: `${reward.correction_count || loop.correction_count || 0} corrections`,
      note: reward.message || plan.accuracy_note || "Corrections make future reviews sharper.",
    },
    {
      label: checkin ? "Handoff" : "Tonight",
      value: checkin ? checkin.outcome : loopStatusLabel(loop.prompt?.state),
      note: checkin?.next_adjustment || loop.prompt?.reason || "Evening review is not due yet.",
    },
  ];
  return chips.map(renderIntentChip);
}

function renderIntentChip(item) {
  const chip = document.createElement("div");
  chip.className = "intent-chip";
  const label = document.createElement("span");
  label.textContent = item.label;
  const value = document.createElement("strong");
  value.textContent = item.value || "Not set";
  const note = document.createElement("p");
  note.textContent = item.note || "";
  chip.append(label, value, note);
  return chip;
}

function renderBetaQueues(review) {
  const wrapper = document.querySelector("[data-beta-review-queues]");
  const disclosure = document.querySelector("[data-queue-details]");
  const correctionMarker = document.querySelector("[data-correction-controls]");
  if (!review) {
    wrapper.hidden = true;
    if (disclosure) {
      disclosure.hidden = true;
      disclosure.open = false;
    }
    correctionMarker.hidden = true;
    return;
  }
  wrapper.hidden = false;
  if (disclosure) {
    disclosure.hidden = false;
  }
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
  bindSectionNavigation();
  const mode = dashboardMode();
  const betaRequired = requiresBetaServiceMode();
  const requiredLivePaths = liveCapturePaths(mode);
  const betaConfig = await loadOptionalJson("./beta-config.json");
  if (betaConfig?.serviceUrl) {
    try {
      await bootBeta(betaConfig);
    } catch (error) {
      console.error(error);
      renderBetaUnavailable(
        "This dashboard is not connected to IntentOS right now. Open the current dashboard from the menu bar, or restart IntentOS and try again.",
      );
    }
    return;
  }
  if (betaRequired) {
    renderBetaUnavailable(
      "This dashboard needs a fresh IntentOS connection. Open the current dashboard from the menu bar or restart IntentOS.",
    );
    return;
  }
  await bootArtifacts({ requiredLivePaths });
}

function renderBetaUnavailable(message) {
  const emptySummary = { labels: {}, total_seconds: 0 };
  renderServiceNotice(
    "Reconnect IntentOS",
    message,
    "After reconnecting, use Try again or open the current dashboard link.",
  );
  document.querySelector("[data-primary-total]").textContent = "--";
  document.querySelector("[data-primary-narrative]").textContent =
    "IntentOS needs to reconnect before it can show today's review.";
  document.querySelector("[data-status]").textContent =
    "Waiting for reconnect";
  document.querySelector("[data-activity-source]").textContent =
    "Local review";
  document.querySelector("[data-capture-source]").textContent =
    "Reconnect needed";
  document.querySelector("[data-stats]").replaceChildren();
  document.querySelector("[data-insights]").replaceChildren();
  document.querySelector("[data-activity-bars]").replaceChildren();
  renderBriefMoments(emptySummary);
  renderFocusMeter(emptySummary);
  renderScore(emptySummary);
  renderCoachHero(emptySummary, [], null, { beta: true, unavailable: true });
  renderNextMove(emptySummary, [], { beta: true, unavailable: true });
  renderCommandCenter(emptySummary, [], null, { beta: true, unavailable: true });
  renderActionDeck(emptySummary, [], { beta: true, unavailable: true });
  renderDailyLoop(null, null);
  renderWeeklyPatterns(null);
  renderTimelineWithOptions([], null);
  renderBetaQueues(null);
  renderOnboarding(null, null, null);
}

function renderLiveUnavailable(message) {
  const emptySummary = { labels: {}, total_seconds: 0 };
  renderServiceNotice(
    "Start a local review session",
    message,
    "Start IntentOS again, then use Try again.",
  );
  document.querySelector("[data-primary-total]").textContent = "--";
  document.querySelector("[data-primary-narrative]").textContent =
    "IntentOS is waiting for local review data.";
  document.querySelector("[data-status]").textContent =
    "Live capture unavailable";
  document.querySelector("[data-activity-source]").textContent =
    "Live capture";
  document.querySelector("[data-capture-source]").textContent =
    "Waiting for data";
  document.querySelector("[data-stats]").replaceChildren();
  document.querySelector("[data-insights]").replaceChildren();
  document.querySelector("[data-activity-bars]").replaceChildren();
  renderBriefMoments(emptySummary);
  renderFocusMeter(emptySummary);
  renderScore(emptySummary);
  renderCoachHero(emptySummary, [], null, { live: true });
  renderNextMove(emptySummary, [], { live: true });
  renderCommandCenter(emptySummary, [], null, { live: true });
  renderActionDeck(emptySummary, [], { live: true });
  renderDailyLoop(null, null);
  renderWeeklyPatterns(null);
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
  hideServiceNotice();
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
  renderCoachHero(primarySummary, dayItems, null, options);
  renderNextMove(primarySummary, dayItems, options);
  renderCommandCenter(primarySummary, dayItems, null, options);
  renderActionDeck(primarySummary, dayItems, options);
  renderDailyLoop(null, null);
  renderWeeklyPatterns(null);
  renderInsights(primarySummary, capture, options);
  renderStats(primarySummary);
  renderBars(primarySummary);
  renderTimeline(capture.items || []);
  renderBetaQueues(null);
  renderOnboarding(null, null, null);
}

async function bootBeta(betaConfig) {
  const date = betaConfig.date || new Date().toISOString().slice(0, 10);
  const weekStart = weekStartDate(date);
  const [review, onboarding, dailyLoop, weekly] = await Promise.all([
    loadBetaJson(betaConfig, `/api/daily-review?date=${encodeURIComponent(date)}`),
    loadBetaJson(betaConfig, "/api/onboarding"),
    loadBetaJson(betaConfig, `/api/daily-loop?date=${encodeURIComponent(date)}`),
    loadBetaJson(betaConfig, `/api/weekly-patterns?week_start=${encodeURIComponent(weekStart)}`),
  ]);
  hideServiceNotice();
  const status = review.status || {};
  const scopeLabel = review.scope?.label || "Today since midnight";

  document.querySelector("[data-primary-total]").textContent =
    review.summary.total_duration || formatDuration(review.summary.total_seconds || 0);
  document.querySelector("[data-primary-narrative]").textContent =
    summaryHeadline(review.summary);
  document.querySelector("[data-status]").textContent = sidebarStatusText(status);
  document.querySelector("[data-activity-source]").textContent =
    `Local review - ${scopeLabel}`;
  document.querySelector("[data-capture-source]").textContent =
    `Daily timeline - ${scopeLabel}`;

  renderFocusMeter(review.summary);
  renderScore(review.summary);
  renderBriefMoments(review.summary);
  renderCoachHero(review.summary, review.items || [], dailyLoop, { beta: true, betaConfig });
  renderNextMove(review.summary, review.items || [], { beta: true, loop: dailyLoop });
  renderCommandCenter(review.summary, review.items || [], dailyLoop, { beta: true });
  renderActionDeck(review.summary, review.items || [], { beta: true, loop: dailyLoop });
  renderDailyLoop(dailyLoop, betaConfig);
  renderWeeklyPatterns(weekly);
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

boot().catch(renderLoadProblem);

setInterval(() => {
  boot().catch(renderLoadProblem);
}, 2000);
