(function () {
  const url = new URL(window.location.href);
  if (isIntentOSDashboard(url)) {
    fetch(new URL("beta-config.json", window.location.href))
      .then((response) => (response.ok ? response.json() : null))
      .then((config) => {
        if (config?.serviceUrl && config?.apiToken) {
          chrome.runtime.sendMessage({
            type: "intentos_service_config",
            dashboardOrigin: url.origin,
            serviceUrl: config.serviceUrl,
            apiToken: config.apiToken,
          });
        }
      })
      .catch(() => {});
    return;
  }
  if (url.hostname === "127.0.0.1") {
    return;
  }

  const payload = {
    type: "intentos_bounded_metadata",
    document_title: document.title || "",
  };

  if (url.hostname === "www.youtube.com") {
    payload.page_kind = "youtube";
    payload.media_title =
      document.querySelector('meta[property="og:title"]')?.content ||
      document.title ||
      "";
  } else if (url.hostname.endsWith("docs.google.com")) {
    payload.page_kind = "document";
  } else if (url.hostname.endsWith("notion.so") || url.hostname.endsWith("notion.site")) {
    payload.page_kind = "document";
  }

  chrome.runtime.sendMessage(payload);

  function isIntentOSDashboard(candidate) {
    return (
      candidate.protocol === "http:" &&
      candidate.hostname === "127.0.0.1" &&
      candidate.pathname === "/site/index.html" &&
      candidate.searchParams.get("mode") === "beta"
    );
  }
})();
