// Bring-your-own AI keys (Gemini, Claude, OpenAI) with a model per provider.
// Kept in sessionStorage: survives a refresh, dropped when the tab closes, and
// wiped on sign-out (see clearSessionData). Never put in localStorage.
const STORAGE_KEY = "hireflow-ai-settings";
const LEGACY_KEY = "hireflow-gemini-api-key";

export const AI_PROVIDERS = {
  gemini: {
    label: "Gemini",
    placeholder: "Paste your Gemini API key",
    models: ["gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"],
  },
  claude: {
    label: "Claude",
    placeholder: "Paste your Anthropic API key (sk-ant-...)",
    models: ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"],
  },
  openai: {
    label: "OpenAI",
    placeholder: "Paste your OpenAI API key (sk-...)",
    models: ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"],
  },
};

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function emptySettings() {
  return { active: "gemini", providers: {} };
}

// Clear anything an earlier version persisted in localStorage.
if (typeof window !== "undefined") {
  try {
    window.localStorage.removeItem(LEGACY_KEY);
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // storage unavailable; nothing to clear
  }
}

export function loadAiSettings() {
  if (typeof window === "undefined") {
    return emptySettings();
  }
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        active: AI_PROVIDERS[parsed.active] ? parsed.active : "gemini",
        providers: parsed.providers && typeof parsed.providers === "object" ? parsed.providers : {},
      };
    }
    const legacy = window.sessionStorage.getItem(LEGACY_KEY);
    if (legacy) {
      window.sessionStorage.removeItem(LEGACY_KEY);
      return { active: "gemini", providers: { gemini: { key: legacy, model: "" } } };
    }
  } catch {
    // unreadable storage: behave as if nothing is saved
  }
  return emptySettings();
}

export function saveAiSettings(settings) {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // storage unavailable; settings just won't survive a refresh
  }
}

export function getActiveAiConfig() {
  const { active, providers } = loadAiSettings();
  const entry = providers[active];
  if (!entry?.key) {
    return null;
  }
  return { provider: active, key: entry.key, model: entry.model || "" };
}

export function aiHeaders(config = getActiveAiConfig()) {
  if (!config) {
    return {};
  }
  return {
    "X-AI-Provider": config.provider,
    "X-AI-Api-Key": config.key,
    ...(config.model ? { "X-AI-Model": config.model } : {}),
  };
}

// Asks the backend to make a tiny request with this key. Resolves to
// { ok: true } or { ok: false, error }.
export async function validateAiConfig(config) {
  try {
    const res = await fetch(`${API_BASE}/api/ai/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...aiHeaders(config) },
      body: "{}",
    });
    if (res.ok) {
      return { ok: true };
    }
    const detail = await res
      .json()
      .then((data) => data?.detail)
      .catch(() => null);
    return { ok: false, error: detail || `Validation failed (HTTP ${res.status}).` };
  } catch {
    return { ok: false, error: "Could not reach the server to verify the key." };
  }
}

// Remove every per-session value (AI keys and saved working state). Call on sign-out.
export function clearSessionData() {
  if (typeof window === "undefined") {
    return;
  }
  try {
    const doomed = [];
    for (let i = 0; i < window.sessionStorage.length; i += 1) {
      const name = window.sessionStorage.key(i);
      if (name === STORAGE_KEY || name === LEGACY_KEY || name?.startsWith("hireflow-state:")) {
        doomed.push(name);
      }
    }
    doomed.forEach((name) => window.sessionStorage.removeItem(name));
  } catch {
    // storage unavailable; nothing to clear
  }
}
