(function () {
  const url = new URL(window.location.href);
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
})();
