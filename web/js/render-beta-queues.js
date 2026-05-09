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
