import { useState } from "react";

import { AI_PROVIDERS, loadAiSettings, saveAiSettings, validateAiConfig } from "./aiSettings.js";

const CUSTOM = "__custom__";

// Provider/key/model editor shared by the student and HR settings pages.
// `classes` maps onto each portal's own stylesheet.
export default function AiKeySettings({ classes }) {
  const [settings, setSettings] = useState(loadAiSettings);
  const [provider, setProvider] = useState(settings.active);
  const entry = settings.providers[provider] || { key: "", model: "" };
  const meta = AI_PROVIDERS[provider];
  const [keyDraft, setKeyDraft] = useState(entry.key);
  const [modelDraft, setModelDraft] = useState(entry.model || meta.models[0]);
  const [customModel, setCustomModel] = useState(false);
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [showKey, setShowKey] = useState(false);

  function selectProvider(next) {
    const saved = settings.providers[next] || { key: "", model: "" };
    setProvider(next);
    setKeyDraft(saved.key);
    setModelDraft(saved.model || AI_PROVIDERS[next].models[0]);
    setCustomModel(Boolean(saved.model) && !AI_PROVIDERS[next].models.includes(saved.model));
    setStatus(null);
  }

  function persist(next) {
    setSettings(next);
    saveAiSettings(next);
  }

  async function handleSave(event) {
    event.preventDefault();
    const key = keyDraft.trim();
    const model = modelDraft.trim();
    if (!key) {
      setStatus({ ok: false, text: "Enter an API key first." });
      return;
    }
    persist({ active: provider, providers: { ...settings.providers, [provider]: { key, model } } });
    setBusy(true);
    setStatus({ ok: null, text: `Testing your ${meta.label} key...` });
    const result = await validateAiConfig({ provider, key, model });
    setBusy(false);
    setStatus(
      result.ok
        ? { ok: true, text: `${meta.label} key verified. It's now your active AI provider.` }
        : { ok: false, text: `API key is not working: ${result.error}` },
    );
  }

  function handleRemove() {
    const providers = { ...settings.providers };
    delete providers[provider];
    const remaining = Object.keys(providers);
    const active = settings.active === provider ? remaining[0] || "gemini" : settings.active;
    persist({ active, providers });
    setKeyDraft("");
    setStatus(null);
  }

  function handleMakeActive() {
    persist({ ...settings, active: provider });
    setStatus({ ok: true, text: `${meta.label} is now your active AI provider.` });
  }

  const modelChoice = customModel ? CUSTOM : modelDraft;
  const isActive = settings.active === provider && Boolean(entry.key);

  return (
    <form className={classes.stack} onSubmit={handleSave}>
      <div className={classes.fields}>
        <div className={classes.field}>
          <label className={classes.label} htmlFor="ai-key-input">
            API key
          </label>
          <div className={classes.inputWrap}>
            <input
              id="ai-key-input"
              type={showKey ? "text" : "password"}
              autoComplete="off"
              spellCheck={false}
              placeholder={meta.placeholder}
              value={keyDraft}
              onChange={(event) => setKeyDraft(event.target.value)}
              className={classes.input}
            />
            <button
              type="button"
              className={classes.reveal}
              onClick={() => setShowKey((prev) => !prev)}
              aria-label={showKey ? "Hide API key" : "Show API key"}
              aria-pressed={showKey}
            >
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
                <circle cx="12" cy="12" r="3" />
                {showKey ? <path d="M4 4l16 16" /> : null}
              </svg>
            </button>
          </div>
        </div>
        <div className={classes.field}>
          <label className={classes.label} htmlFor="ai-provider-select">
            Provider
          </label>
          <select
            id="ai-provider-select"
            className={classes.input}
            value={provider}
            onChange={(event) => selectProvider(event.target.value)}
          >
            {Object.entries(AI_PROVIDERS).map(([id, info]) => (
              <option key={id} value={id}>
                {info.label}
                {settings.providers[id]?.key ? (settings.active === id ? " (active)" : " (saved)") : ""}
              </option>
            ))}
          </select>
        </div>
        <div className={classes.field}>
          <label className={classes.label} htmlFor="ai-model-select">
            Model
          </label>
          <select
            id="ai-model-select"
            className={classes.input}
            value={modelChoice}
            onChange={(event) => {
              if (event.target.value === CUSTOM) {
                setCustomModel(true);
                setModelDraft("");
              } else {
                setCustomModel(false);
                setModelDraft(event.target.value);
              }
            }}
          >
            {meta.models.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
            <option value={CUSTOM}>Other (type a model name)</option>
          </select>
          {customModel ? (
            <input
              type="text"
              spellCheck={false}
              placeholder="Model name"
              value={modelDraft}
              onChange={(event) => setModelDraft(event.target.value)}
              className={classes.input}
              aria-label="Custom model name"
            />
          ) : null}
        </div>
      </div>
      <div className={classes.actions}>
        <button className={classes.primary} type="submit" disabled={busy}>
          {classes.lockIcon ? (
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="5" y="11" width="14" height="9" rx="2" />
              <path d="M8 11V8a4 4 0 0 1 8 0v3" />
            </svg>
          ) : null}
          {busy ? "Testing..." : "Save & test key"}
        </button>
        {entry.key && !isActive ? (
          <button className={classes.ghost} type="button" onClick={handleMakeActive}>
            Use this provider
          </button>
        ) : null}
        {entry.key ? (
          <button className={classes.ghost} type="button" onClick={handleRemove}>
            Remove
          </button>
        ) : null}
      </div>
      {status ? (
        <p
          className={classes.hint}
          role={status.ok === false ? "alert" : "status"}
          style={status.ok === false ? { color: "#dc2626" } : status.ok ? { color: "#059669" } : undefined}
        >
          {status.text}
        </p>
      ) : null}
    </form>
  );
}
