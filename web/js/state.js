const paths = {
  activity: "../artifacts/activity-summary.json",
  liveCapture: [
    "../artifacts/live-session-capture-summary.json",
    "../artifacts/live-capture-summary.json",
  ],
  fixtureCapture: [
    "../artifacts/session-capture-summary.json",
    "../artifacts/capture-summary.json",
  ],
  captureStatus: "../artifacts/live-capture-status.json",
};

const labels = {
  deep_work: "Deep work",
  learning: "Learning",
  communication: "Communication",
  admin: "Admin",
  passive_consumption: "Passive consumption",
  active_creation: "Active creation",
  entertainment: "Entertainment",
  unknown: "Unknown",
};

const focusLabels = ["deep_work", "learning", "active_creation"];
const attentionLeakLabels = ["passive_consumption", "entertainment"];
const reviewLabels = ["unknown"];

let currentSetupGuidance = null;
let navScrollFrame = null;

window.IntentOS = window.IntentOS || {};
