import { useEffect, useState } from "react";

// useState that survives a page refresh by mirroring into sessionStorage.
// Entries live under "hireflow-state:" so sign-out can clear them (see
// clearSessionData in aiSettings.js).
export function usePersistedState(name, initial) {
  const storageKey = `hireflow-state:${name}`;
  const [value, setValue] = useState(() => {
    try {
      const raw = window.sessionStorage.getItem(storageKey);
      if (raw !== null) {
        return JSON.parse(raw);
      }
    } catch {
      // unreadable storage: fall through to the default
    }
    return typeof initial === "function" ? initial() : initial;
  });

  useEffect(() => {
    try {
      window.sessionStorage.setItem(storageKey, JSON.stringify(value));
    } catch {
      // storage full/unavailable; state just won't survive a refresh
    }
  }, [storageKey, value]);

  return [value, setValue];
}
