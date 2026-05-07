(function () {
  const configNode = document.getElementById("intentos-render-probe-config");
  const config = configNode ? JSON.parse(configNode.textContent || "{}") : {};
  const scenarios = new Set(config.scenarios || []);
  const copyPolicy = config.copy_policy || {};
  const workflowProbe = {
    clicked: [],
    correction_changed: false,
    setup_guidance_visible: false,
  };
  let workflowRan = false;
  let longTextApplied = false;
  let writeProbeRunning = false;
  let probeWritten = false;

  function delay(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  function isRendered(element) {
    if (!element) {
      return false;
    }
    const closedDetails = element.closest("details:not([open])");
    if (closedDetails && !element.closest("summary")) {
      return false;
    }
    const style = window.getComputedStyle(element);
    if (
      style.display === "none" ||
      style.visibility === "hidden" ||
      Number(style.opacity) === 0
    ) {
      return false;
    }
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function isVisible(element) {
    if (!isRendered(element)) {
      return false;
    }
    const rect = element.getBoundingClientRect();
    return (
      rect.bottom > 0 &&
      rect.right > 0 &&
      rect.top < window.innerHeight &&
      rect.left < window.innerWidth
    );
  }

  function visibleCount(selector) {
    return Array.from(document.querySelectorAll(selector)).filter(isVisible).length;
  }

  function visibleCountInsideOpenDetail(detailSelector, childSelector) {
    const detail = document.querySelector(detailSelector);
    if (!detail || !detail.open) {
      return 0;
    }
    return Array.from(detail.querySelectorAll(childSelector)).filter(isVisible).length;
  }

  function normalizedText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function describeElement(element) {
    return {
      tag: element.tagName.toLowerCase(),
      class_name: element.className || "",
      text: normalizedText(element.textContent).slice(0, 90),
    };
  }

  function visibleLeafTextElements() {
    return Array.from(document.querySelectorAll("body *")).filter((element) => {
      const tag = element.tagName.toLowerCase();
      if (["script", "style", "noscript"].includes(tag)) {
        return false;
      }
      const text = normalizedText(element.textContent);
      return Boolean(text) && element.children.length === 0 && isVisible(element);
    });
  }

  function textLayoutDiagnostics(options = {}) {
    const leafText = visibleLeafTextElements();
    const clippedText = [];
    const cutOffText = [];
    const guardedTextSelector = [
      ".command-step",
      ".coach-hero",
      ".focus-rescue",
      ".score-card",
      ".decision-card",
      ".next-move",
      ".stat",
      ".insight",
      ".queue-panel",
      "[data-service-notice]",
    ].join(", ");
    const bottomEdgeGuardSelector = [
      ".command-step",
      ".coach-hero",
      ".focus-rescue",
      ".decision-card",
      ".next-move",
      ".stat",
      ".insight",
      ".queue-panel",
    ].join(", ");
    leafText.forEach((element) => {
      if (options.ignoreSelector && element.closest(options.ignoreSelector)) {
        return;
      }
      const rect = element.getBoundingClientRect();
      const style = window.getComputedStyle(element);
      const horizontalClip =
        ["hidden", "clip"].includes(style.overflowX) &&
        element.scrollWidth > element.clientWidth + 1;
      const verticalClip =
        ["hidden", "clip"].includes(style.overflowY) &&
        element.scrollHeight > element.clientHeight + 1;
      if (horizontalClip || verticalClip) {
        clippedText.push(describeElement(element));
      }
      const horizontalOrTopCut =
        rect.left < -1 ||
        rect.top < -1 ||
        rect.right > window.innerWidth + 1;
      const primaryBottomCut =
        rect.bottom > window.innerHeight + 1 &&
        rect.top < window.innerHeight - 1 &&
        Boolean(element.closest(bottomEdgeGuardSelector)) &&
        !Boolean(options.ignoreBottomSelector && element.closest(options.ignoreBottomSelector));
      if (horizontalOrTopCut || primaryBottomCut) {
        if (element.closest(guardedTextSelector)) {
          cutOffText.push(describeElement(element));
        }
      }
    });
    return {
      visible_leaf_text_count: leafText.length,
      visible_word_count: leafText.reduce((total, element) => {
        const words = normalizedText(element.textContent).split(/\s+/).filter(Boolean);
        return total + words.length;
      }, 0),
      clipped_text_count: clippedText.length,
      cut_off_text_count: cutOffText.length,
      clipped_text: clippedText.slice(0, 5),
      cut_off_text: cutOffText.slice(0, 5),
    };
  }

  function defaultDensitySnapshot(textLayout) {
    const supportingDetails = Array.from(
      document.querySelectorAll(
        "[data-signal-details], [data-queue-details], [data-evidence-details]"
          + ", [data-weekly-details]"
      )
    ).filter((element) => !element.hidden);
    return {
      visible_decision_cards: visibleCount(".decision-card"),
      visible_stats: visibleCountInsideOpenDetail("[data-signal-details]", ".stat"),
      visible_insights: visibleCountInsideOpenDetail("[data-signal-details]", ".insight"),
      visible_queue_panels: visibleCountInsideOpenDetail("[data-queue-details]", ".queue-panel"),
      visible_report_panels: visibleCountInsideOpenDetail("[data-evidence-details]", ".panel"),
      supporting_detail_count: supportingDetails.length,
      collapsed_supporting_detail_count: supportingDetails.filter((element) => !element.open)
        .length,
      open_supporting_detail_count: supportingDetails.filter((element) => element.open).length,
      visible_leaf_text_count: textLayout.visible_leaf_text_count,
      visible_word_count: textLayout.visible_word_count,
    };
  }

  function firstViewportSnapshot(textLayout) {
    return {
      command_center_present: Boolean(document.querySelector("[data-command-center]")),
      coach_hero_present: Boolean(document.querySelector("[data-coach-hero]")),
      focus_rescue_present: isVisible(document.querySelector("[data-focus-rescue]")),
      focus_rescue_action_count: visibleCount("[data-focus-rescue-actions] button"),
      focus_rescue_text: normalizedText(document.querySelector("[data-focus-rescue]")?.textContent),
      coach_receipt_count: visibleCount(".receipt-card"),
      weekly_details_present: Boolean(document.querySelector("[data-weekly-details]")),
      next_move_present: Boolean(normalizedText(document.querySelector("[data-next-move-title]")?.textContent)),
      daily_loop_present: Boolean(document.querySelector("[data-daily-loop]")),
      visible_word_count: textLayout.visible_word_count,
      visible_report_panels: visibleCountInsideOpenDetail("[data-evidence-details]", ".panel"),
      visible_stats: visibleCountInsideOpenDetail("[data-signal-details]", ".stat"),
      nav_visible: isVisible(document.querySelector(".nav-list")),
    };
  }

  function copyPolicyDiagnostics() {
    const visibleText = normalizedText(document.body.innerText);
    const lowerText = visibleText.toLowerCase();
    const forbiddenHits = (copyPolicy.forbidden_phrases || []).filter((phrase) =>
      lowerText.includes(String(phrase).toLowerCase())
    );
    const rawErrorHits = (copyPolicy.raw_error_patterns || []).filter((pattern) => {
      try {
        return new RegExp(pattern, "i").test(visibleText);
      } catch (_error) {
        return false;
      }
    });
    return {
      policy_version: copyPolicy.version || 0,
      visible_text_length: visibleText.length,
      forbidden_hits: forbiddenHits,
      raw_error_hits: rawErrorHits,
    };
  }

  function serviceStateDiagnostics() {
    const notice = document.querySelector("[data-service-notice]");
    const noticeText = normalizedText(notice?.textContent);
    return {
      notice_visible: isVisible(notice),
      notice_text: noticeText.slice(0, 160),
      reconnect_visible: noticeText.includes("Reconnect IntentOS"),
      status_text: normalizedText(document.querySelector("[data-status]")?.textContent),
      loop_status_text: normalizedText(document.querySelector("[data-loop-status]")?.textContent),
    };
  }

  function applyLongTextScenario() {
    if (longTextApplied) {
      return;
    }
    longTextApplied = true;
    const longTitle =
      "Inspect an intentionally long IntentOS review title with repository paths, localhost URLs, and detailed next-step language that must wrap cleanly in compact panels";
    const longUrl =
      "https://example.local/intentos/review/very-long-fixture-url-that-should-wrap-without-clipping-or-horizontal-overflow?focus=deep-work&avoid=reactive-feed";
    const targets = [
      "[data-next-move-title]",
      "[data-coach-verdict]",
      "[data-coach-actual]",
      "[data-coach-focus-detail]",
      "[data-coach-avoid-detail]",
      "[data-loop-summary]",
      "[data-contract-question]",
      "[data-contract-focus]",
      "[data-contract-avoid]",
      "[data-contract-review]",
      "[data-primary-narrative]",
    ];
    targets.forEach((selector) => {
      const element = document.querySelector(selector);
      if (element && isVisible(element)) {
        element.textContent = `${longTitle}: ${longUrl}`;
      }
    });
    document.querySelectorAll("[data-capture-events] li, .queue-panel, .decision-card").forEach(
      (element, index) => {
        if (index < 4 && isVisible(element)) {
          element.textContent = `${longTitle} ${index + 1}: ${longUrl}`;
        }
      }
    );
  }

  function setInputValue(selector, value) {
    const input = document.querySelector(selector);
    if (!input || !isRendered(input)) {
      return false;
    }
    input.value = value;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    return true;
  }

  function intentPreviewDiagnostics() {
    const form = document.querySelector("[data-intent-form]");
    const formVisible = isRendered(form);
    const focusValue =
      "Protect IntentOS implementation review with a deliberately long focus phrase";
    const avoidValue =
      "Cap LinkedIn feed and reactive status pages with a deliberately long avoid phrase";
    const noteValue = "Carry one adjustment into tomorrow without clipping the preview.";
    const typed =
      formVisible &&
      setInputValue("[data-intent-focus]", focusValue) &&
      setInputValue("[data-intent-avoid]", avoidValue) &&
      setInputValue("[data-intent-note]", noteValue);
    const focusText = normalizedText(document.querySelector("[data-contract-focus]")?.textContent);
    const avoidText = normalizedText(document.querySelector("[data-contract-avoid]")?.textContent);
    const reviewText = normalizedText(document.querySelector("[data-contract-review]")?.textContent);
    const questionText = normalizedText(document.querySelector("[data-contract-question]")?.textContent);
    return {
      form_visible: formVisible,
      typed,
      focus_preview_mentions_input: !typed || focusText.includes("IntentOS"),
      avoid_preview_mentions_input: !typed || avoidText.includes("LinkedIn"),
      review_preview_mentions_note: !typed || reviewText.includes("tomorrow"),
      question_text: questionText.slice(0, 180),
    };
  }

  async function runSectionNavProbe() {
    const workspace = document.querySelector(".workspace");
    const nav = document.querySelector(".nav-list");
    const activityLink = document.querySelector(".nav-item[href='#activity-title']");
    const activeBefore = document.querySelector(".nav-item.active")?.getAttribute("href") || "";
    const originalHash = window.location.hash;
    const originalPath = window.location.pathname + window.location.search;
    const evidenceDetails = document.querySelector("[data-evidence-details]");
    const evidenceWasOpen = evidenceDetails?.open === true;
    if (!workspace || !nav || !activityLink) {
      return { available: false };
    }
    const bodyBefore = window.scrollY;
    const workspaceBefore = workspace.scrollTop;
    const previousScrollBehavior = workspace.style.scrollBehavior;
    const targetBefore = document.getElementById("activity-title")?.getBoundingClientRect();
    const workspaceBeforeRect = workspace.getBoundingClientRect();
    const activityRequiredScroll = Boolean(targetBefore) &&
      (targetBefore.top < workspaceBeforeRect.top ||
        targetBefore.bottom > workspaceBeforeRect.bottom);
    activityLink.click();
    await delay(550);
    const navRect = nav.getBoundingClientRect();
    const activeAfter = document.querySelector(".nav-item.active")?.getAttribute("href") || "";
    const activityTextLayout = textLayoutDiagnostics({ ignoreSelector: ".decision-card" });
    const state = {
      available: true,
      activity_required_scroll: activityRequiredScroll,
      nav_visible_after_activity: navRect.top >= -1 && navRect.bottom <= window.innerHeight + 1,
      workspace_scrolled_after_activity: workspace.scrollTop > workspaceBefore + 20,
      document_scroll_delta: Math.abs(window.scrollY - bodyBefore),
      active_href_after_activity: activeAfter,
      evidence_open_after_activity: evidenceDetails?.open === true,
      visible_report_panels_after_activity: visibleCount(".panel"),
      cut_off_text_after_activity: activityTextLayout.cut_off_text_count,
      cut_off_text_after_activity_items: activityTextLayout.cut_off_text,
      clipped_text_after_activity: activityTextLayout.clipped_text_count,
    };
    workspace.style.scrollBehavior = "auto";
    workspace.scrollTo({ top: workspaceBefore, behavior: "auto" });
    window.scrollTo(0, bodyBefore);
    history.replaceState(null, "", originalPath + originalHash);
    if (activeBefore) {
      document.querySelectorAll(".nav-item[href^='#']").forEach((link) => {
        link.classList.toggle("active", link.getAttribute("href") === activeBefore);
      });
    }
    if (evidenceDetails && !evidenceWasOpen) {
      evidenceDetails.open = false;
    }
    workspace.style.scrollBehavior = previousScrollBehavior;
    return state;
  }

  function click(selector) {
    const element = document.querySelector(selector);
    if (!element || !isVisible(element)) {
      return false;
    }
    element.click();
    workflowProbe.clicked.push(selector);
    return true;
  }

  async function runWorkflowProbe() {
    if (!config.workflow || workflowRan) {
      return;
    }
    workflowRan = true;
    const onboarding = document.querySelector("[data-onboarding]");
    if (onboarding && isRendered(onboarding) && !isVisible(onboarding)) {
      onboarding.scrollIntoView({ block: "center", inline: "nearest" });
      await delay(150);
    }
    for (const selector of [
      "[data-onboarding-privacy]",
      "[data-onboarding-check]",
      "[data-copy-setup-report]",
      "[data-open-accessibility]",
      "[data-open-automation]",
      "[data-open-chrome]",
    ]) {
      const target = document.querySelector(selector);
      if (target && isRendered(target) && !isVisible(target)) {
        target.scrollIntoView({ block: "center", inline: "nearest" });
        await delay(90);
      }
      click(selector);
    }
    await delay(700);
    for (let attempt = 0; attempt < 10; attempt += 1) {
      if (isVisible(document.querySelector("[data-setup-guidance]"))) {
        workflowProbe.setup_guidance_visible = true;
        break;
      }
      await delay(100);
    }
    const evidenceDetails = document.querySelector("[data-evidence-details]");
    if (evidenceDetails && !evidenceDetails.open) {
      evidenceDetails.open = true;
      await delay(50);
    }
    const select = document.querySelector(".event-correction select");
    if (select) {
      select.scrollIntoView({ block: "center", inline: "nearest" });
      await delay(100);
    }
    if (select && isVisible(select) && select.options.length > 1) {
      select.value = "learning";
      select.dispatchEvent(new Event("change", { bubbles: true }));
      workflowProbe.correction_changed = true;
    }
    await delay(900);
    workflowProbe.setup_guidance_visible =
      workflowProbe.setup_guidance_visible ||
      isVisible(document.querySelector("[data-setup-guidance]"));
  }

  function baseState(defaultUx, currentTextLayout, sectionNav, intentPreview) {
    const body = document.body;
    const state = {
      schema_version: 1,
      mode: config.mode || "fixture",
      scenarios: Array.from(scenarios),
      root_present: Boolean(document.querySelector("[data-ui-root]")),
      body_text_length: normalizedText(body.innerText).length,
      panel_count: document.querySelectorAll(".panel").length,
      stat_count: document.querySelectorAll(".stat").length,
      decision_count: document.querySelectorAll(".decision-card").length,
      event_count: document.querySelectorAll("[data-capture-events] li").length,
      next_move_text: normalizedText(document.querySelector("[data-next-move-title]")?.textContent),
      coach_hero_present: Boolean(document.querySelector("[data-coach-hero]")),
      focus_rescue_present: isRendered(document.querySelector("[data-focus-rescue]")),
      focus_rescue_action_count: document.querySelectorAll("[data-focus-rescue-actions] button").length,
      focus_rescue_text: normalizedText(document.querySelector("[data-focus-rescue]")?.textContent),
      weekly_details_present: Boolean(document.querySelector("[data-weekly-details]")),
      daily_loop_present: Boolean(document.querySelector("[data-daily-loop]")),
      daily_loop_text: normalizedText(document.querySelector("[data-daily-loop]")?.textContent),
      evening_receipt_present: isRendered(document.querySelector("[data-evening-receipt]")),
      evening_receipt_text: normalizedText(document.querySelector("[data-evening-receipt]")?.textContent),
      command_center_present: Boolean(document.querySelector("[data-command-center]")),
      command_step_count: document.querySelectorAll(".command-step").length,
      command_center_text: normalizedText(document.querySelector("[data-command-center]")?.textContent),
      onboarding_visible: document.querySelector("[data-onboarding]")?.hidden === false,
      onboarding_step_count: document.querySelectorAll("[data-onboarding-steps] .onboarding-step").length,
      onboarding_step_text: normalizedText(document.querySelector("[data-onboarding-steps]")?.textContent),
      capture_preview_state: document.querySelector("[data-capture-preview]")?.dataset.state || "",
      browser_detail_action_visible: isVisible(document.querySelector("[data-onboarding-browser]")),
      browser_detail_permission_visible: normalizedText(document.querySelector("[data-permission-checklist]")?.textContent).includes("Browser detail"),
      correction_controls: document.querySelectorAll(".event-correction").length,
      workflow_probe: workflowProbe,
      workflow_expected: Boolean(config.workflow),
      section_nav: sectionNav,
      youtube_visible: document.querySelector(".youtube-panel")?.hidden === false,
      text_layout: defaultUx.text_layout,
      current_text_layout: currentTextLayout,
      default_density: defaultUx.default_density,
      first_viewport: defaultUx.first_viewport,
      copy_policy: copyPolicyDiagnostics(),
      intent_preview: intentPreview,
      service_state: serviceStateDiagnostics(),
      horizontal_overflow:
        document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      out_of_view_count: Array.from(document.querySelectorAll("body *"))
        .filter((element) => {
          const text = normalizedText(element.textContent);
          if (!text || element.offsetParent === null) {
            return false;
          }
          const rect = element.getBoundingClientRect();
          return rect.left < -1 || rect.right > window.innerWidth + 1;
        }).length,
      clipped_text_count: defaultUx.text_layout.clipped_text_count,
      cut_off_text_count: defaultUx.text_layout.cut_off_text_count,
    };
    state.scenario_results = Object.fromEntries(
      Array.from(scenarios).map((scenario) => [
        scenario,
        {
          text_layout: currentTextLayout,
          copy_policy: state.copy_policy,
          first_viewport: state.first_viewport,
          service_state: state.service_state,
          intent_preview: state.intent_preview,
        },
      ])
    );
    return state;
  }

  function captureDefaultUxSnapshot() {
    const textLayout = textLayoutDiagnostics();
    const snapshot = {
      text_layout: textLayout,
      default_density: defaultDensitySnapshot(textLayout),
      first_viewport: firstViewportSnapshot(textLayout),
    };
    const betaReadyNeedsData =
      scenarios.has("beta-ready") &&
      !scenarios.has("beta-service-stale") &&
      !scenarios.has("beta-empty");
    const ready =
      document.querySelectorAll(".decision-card").length >= 1 &&
      Boolean(document.querySelector("[data-daily-loop]")) &&
      Boolean(document.querySelector("[data-command-center]")) &&
      (!betaReadyNeedsData ||
        (document.querySelectorAll(".stat").length >= 2 &&
          document.querySelectorAll(".event-correction").length >= 1 &&
          !isVisible(document.querySelector("[data-service-notice]"))));
    const previous = window.__intentosDefaultUxSnapshot;
    if (!previous || (!previous.ready && ready)) {
      window.__intentosDefaultUxSnapshot = { ...snapshot, ready };
    }
    return window.__intentosDefaultUxSnapshot;
  }

  async function writeProbe() {
    if (writeProbeRunning) {
      return;
    }
    writeProbeRunning = true;
    try {
      const defaultUx = captureDefaultUxSnapshot();
      if (!defaultUx.ready) {
        return;
      }
      await runWorkflowProbe();
      if (scenarios.has("beta-intent-missing")) {
        const intentAction = document.querySelector("[data-command-tonight-action]");
        if (intentAction) {
          intentAction.click();
          await delay(600);
        }
      }
      const intentPreview = intentPreviewDiagnostics();
      if (scenarios.has("fixture-long-text")) {
        applyLongTextScenario();
        await delay(50);
      }
      const currentTextLayout = textLayoutDiagnostics();
      const sectionNav = await runSectionNavProbe();
      const state = baseState(defaultUx, currentTextLayout, sectionNav, intentPreview);
      let node = document.getElementById("intentos-render-probe");
      if (!node) {
        node = document.createElement("script");
        node.id = "intentos-render-probe";
        node.type = "application/json";
        document.body.appendChild(node);
      }
      node.textContent = JSON.stringify(state);
      probeWritten = true;
    } finally {
      writeProbeRunning = false;
    }
  }

  function scheduleProbeWrites() {
    [0, 700, 1800, 3200, 4600, 6200, 7600].forEach((ms) => {
      window.setTimeout(writeProbe, ms);
    });
    let attempts = 0;
    const interval = window.setInterval(() => {
      attempts += 1;
      if (probeWritten || attempts > 30) {
        window.clearInterval(interval);
        return;
      }
      writeProbe();
    }, 500);
  }

  if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", scheduleProbeWrites, { once: true });
  } else {
    scheduleProbeWrites();
  }
  window.addEventListener("load", scheduleProbeWrites, { once: true });
})();
