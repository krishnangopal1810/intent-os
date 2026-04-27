const DEFAULT_PORT = 58917;

async function serviceUrl() {
  const data = await chrome.storage.local.get({ servicePort: DEFAULT_PORT });
  return `http://127.0.0.1:${data.servicePort}/api/browser-event`;
}

function eventFromTab(tab, extra = {}) {
  if (!tab || !tab.url || !tab.title || !/^https?:\/\//.test(tab.url)) {
    return null;
  }
  return {
    browser_name: "Google Chrome",
    url: tab.url,
    title: tab.title,
    timestamp: new Date().toISOString(),
    duration_seconds: 30,
    tab_id: tab.id,
    window_id: tab.windowId,
    active: Boolean(tab.active),
    source: "chrome_extension_bridge",
    ...extra,
  };
}

async function postTab(tab, extra = {}) {
  const payload = eventFromTab(tab, extra);
  if (!payload) {
    return;
  }
  try {
    await fetch(await serviceUrl(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    console.debug("IntentOS beta bridge unavailable", error);
  }
}

async function postActiveTab(windowId) {
  const tabs = await chrome.tabs.query({ active: true, windowId });
  if (tabs[0]) {
    await postTab(tabs[0]);
  }
}

chrome.tabs.onActivated.addListener((activeInfo) => {
  postActiveTab(activeInfo.windowId);
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (tab.active && (changeInfo.title || changeInfo.url || changeInfo.status === "complete")) {
    postTab(tab);
  }
});

chrome.windows.onFocusChanged.addListener((windowId) => {
  if (windowId !== chrome.windows.WINDOW_ID_NONE) {
    postActiveTab(windowId);
  }
});

chrome.runtime.onMessage.addListener((message, sender) => {
  if (message?.type === "intentos_bounded_metadata" && sender.tab) {
    postTab(sender.tab, {
      page_kind: message.page_kind,
      media_title: message.media_title,
      document_title: message.document_title,
    });
  }
});
