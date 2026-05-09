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

boot().catch(renderLoadProblem);

setInterval(() => {
  boot().catch(renderLoadProblem);
}, 2000);
