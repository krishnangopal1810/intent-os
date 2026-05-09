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
