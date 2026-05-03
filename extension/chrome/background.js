const DEFAULT_PORT = 58917;
const BRIDGE_VERSION = "0.1.0";
const HEARTBEAT_ALARM = "intentos-heartbeat";

async function serviceBaseUrl() {
  const data = await chrome.storage.local.get({ servicePort: DEFAULT_PORT });
  return `http://127.0.0.1:${data.servicePort}`;
}

async function serviceUrl(path) {
  return `${await serviceBaseUrl()}${path}`;
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

async function postHeartbeat() {
  try {
    await fetch(await serviceUrl("/api/extension-heartbeat"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        version: BRIDGE_VERSION,
        timestamp: new Date().toISOString(),
        source: "chrome_extension_bridge",
      }),
    });
  } catch (error) {
    console.debug("IntentOS beta heartbeat unavailable", error);
  }
}

async function postTab(tab, extra = {}) {
  const payload = eventFromTab(tab, extra);
  if (!payload) {
    return;
  }
  try {
    await postHeartbeat();
    await fetch(await serviceUrl("/api/browser-event"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    console.debug("IntentOS beta bridge unavailable", error);
  }
}

async function postActiveTab(windowId) {
  const query = windowId
    ? { active: true, windowId }
    : { active: true, lastFocusedWindow: true };
  const tabs = await chrome.tabs.query(query);
  if (tabs[0]) {
    await postTab(tabs[0]);
  }
}

function startHeartbeat() {
  chrome.alarms.create(HEARTBEAT_ALARM, { periodInMinutes: 1 });
  postHeartbeat();
  postActiveTab();
}

chrome.runtime.onInstalled.addListener(startHeartbeat);
chrome.runtime.onStartup.addListener(startHeartbeat);

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === HEARTBEAT_ALARM) {
    postHeartbeat();
    postActiveTab();
  }
});

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
