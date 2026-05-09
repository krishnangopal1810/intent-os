async function loadJson(path, options = {}) {
  const response = await fetch(path, { cache: "no-store", ...options });
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json();
}

async function loadOptionalJson(path) {
  try {
    return await loadJson(path);
  } catch (error) {
    return null;
  }
}

function apiUrl(config, path) {
  return `${config.serviceUrl}${path}`;
}

function apiHeaders(config) {
  return config?.apiToken ? { "X-IntentOS-Token": config.apiToken } : {};
}

async function loadBetaJson(config, path) {
  return loadJson(apiUrl(config, path), { headers: apiHeaders(config) });
}

async function postJson(betaConfig, path, payload) {
  const response = await fetch(apiUrl(betaConfig, path), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...apiHeaders(betaConfig) },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status}`);
  }
  return response.json();
}

Object.assign(window.IntentOS, { loadJson, loadOptionalJson, loadBetaJson, postJson, apiUrl, apiHeaders });
