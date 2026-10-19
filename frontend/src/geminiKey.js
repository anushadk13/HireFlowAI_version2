// Bring-your-own Gemini key, kept in sessionStorage: it survives a refresh but
// is dropped when the tab or browser is closed, and is never put in localStorage.
const STORAGE_KEY = "hireflow-gemini-api-key";

// Remove any key an earlier version of the app persisted in localStorage.
if (typeof window !== "undefined") {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // storage unavailable; nothing to clear
  }
}

export function getGeminiApiKey() {
  if (typeof window === "undefined") {
    return "";
  }
  try {
    return window.sessionStorage.getItem(STORAGE_KEY) || "";
  } catch {
    return "";
  }
}

export function setGeminiApiKey(key) {
  if (typeof window === "undefined") {
    return;
  }
  const value = (key || "").trim();
  try {
    if (value) {
      window.sessionStorage.setItem(STORAGE_KEY, value);
    } else {
      window.sessionStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // storage unavailable; key just won't persist across refresh
  }
}
