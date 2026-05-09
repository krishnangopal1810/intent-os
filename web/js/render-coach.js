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
