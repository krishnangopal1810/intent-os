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
