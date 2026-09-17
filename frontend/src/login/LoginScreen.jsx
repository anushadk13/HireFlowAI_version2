import { useEffect, useState } from "react";
import { onAuthStateChanged, signInWithPopup, signInWithRedirect } from "firebase/auth";

import { auth, googleProvider } from "../firebase.js";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
const STUDENT_PREVIEW_SRC = import.meta.env.VITE_STUDENT_LOGO_SRC || "/images/student.png";

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="google-icon">
      <path d="M21.35 11.1H12v3.8h5.36c-.23 1.24-.94 2.28-2.01 2.99v2.49h3.25c1.9-1.75 2.99-4.34 2.99-7.39 0-.73-.07-1.43-.24-1.89z" fill="#4285F4" />
      <path d="M12 22c2.7 0 4.97-.89 6.63-2.42l-3.25-2.49c-.9.6-2.05.96-3.38.96-2.6 0-4.81-1.75-5.6-4.11H3.04v2.58A10 10 0 0 0 12 22z" fill="#34A853" />
      <path d="M6.4 13.94A5.98 5.98 0 0 1 6.08 12c0-.67.11-1.32.32-1.94V7.48H3.04A10 10 0 0 0 2 12c0 1.61.38 3.13 1.04 4.48l3.36-2.54z" fill="#FBBC05" />
      <path d="M12 5.98c1.47 0 2.78.5 3.82 1.47l2.87-2.87C16.96 2.9 14.7 2 12 2A10 10 0 0 0 3.04 7.48l3.36 2.58C7.19 7.73 9.4 5.98 12 5.98z" fill="#EA4335" />
    </svg>
  );
}

function ModeTabs({ mode, onChange }) {
  return (
    <div className="auth-switcher" role="tablist" aria-label="Authentication mode">
      <button
        className={`auth-switcher__tab ${mode === "signin" ? "active" : ""}`}
        type="button"
        onClick={() => onChange("signin")}
      >
        Sign in
      </button>
      <button
        className={`auth-switcher__tab ${mode === "signup" ? "active" : ""}`}
        type="button"
        onClick={() => onChange("signup")}
      >
        Create account
      </button>
    </div>
  );
}

async function postJSON(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const error = new Error(data.detail || `Request to ${path} failed with status ${res.status}`);
    error.status = res.status;
    throw error;
  }

  return data;
}

function getInitialMode() {
  if (typeof window === "undefined") {
    return "signin";
  }

  return window.sessionStorage.getItem("auth_flow_mode") || "signin";
}

export default function LoginScreen({ onBack, onSelectStudent, onSelectHr, LogoMark }) {
  const [mode, setMode] = useState(getInitialMode);
  const [currentUser, setCurrentUser] = useState(null);
  const [selectedRole, setSelectedRole] = useState("");
  const [signinEmail, setSigninEmail] = useState("");
  const [signinPassword, setSigninPassword] = useState("");
  const [signupName, setSignupName] = useState("");
  const [signupEmail, setSignupEmail] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [loadingAction, setLoadingAction] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [hasPendingGoogleLookup, setHasPendingGoogleLookup] = useState(false);

  function persistMode(nextMode) {
    setMode(nextMode);
    setSelectedRole("");
    setSigninEmail("");
    setSigninPassword("");
    setSignupName("");
    setSignupEmail("");
    setSignupPassword("");
    setErrorMessage("");
    setStatusMessage("");
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem("auth_flow_mode", nextMode);
    }
  }

  function clearFlow() {
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem("auth_flow_mode");
    }
  }

  function routeByRole(role) {
    clearFlow();
    const normalizedRole = String(role || "student").trim().toLowerCase();
    const nextView = normalizedRole === "hr" ? "hr" : "student";

    if (typeof window !== "undefined") {
      window.sessionStorage.setItem("hireflow-auth-view", nextView);
      window.dispatchEvent(new CustomEvent("hireflow-auth-route", { detail: { view: nextView } }));
    }

    if (normalizedRole === "hr") {
      onSelectHr?.();
      return;
    }

    onSelectStudent?.();
  }

  async function resolveAccount(user) {
    setLoadingAction("resolve");
    setErrorMessage("");

    try {
      const account = await postJSON("/api/auth/lookup", {
        email: user.email,
      });
      routeByRole(account.role);
    } catch (error) {
      if (error?.status !== 404) {
        setErrorMessage(error?.message || "Google sign-in failed.");
      }
    } finally {
      setHasPendingGoogleLookup(false);
      setLoadingAction("");
    }
  }

  async function handleGoogleAuth(nextMode) {
    persistMode(nextMode);
    setHasPendingGoogleLookup(true);
    setLoadingAction("google");
    setErrorMessage("");
    setStatusMessage("");

    try {
      let user = null;
      try {
        const result = await signInWithPopup(auth, googleProvider);
        user = result?.user;
      } catch (popupErr) {
        if (popupErr?.code === "auth/popup-blocked" || popupErr?.code === "auth/popup-closed-by-user") {
          await signInWithRedirect(auth, googleProvider);
          return;
        }
        throw popupErr;
      }

      if (user) {
        await resolveAccount(user);
      }
    } catch (error) {
      setHasPendingGoogleLookup(false);
      setLoadingAction("");
      setErrorMessage(error?.message || "Google sign-in failed.");
    }
  }

  async function handleEmailSignIn() {
    const trimmedEmail = signinEmail.trim().toLowerCase();
    const trimmedPassword = signinPassword.trim();

    if (!trimmedEmail || !trimmedPassword) {
      setErrorMessage("Please enter your email and password.");
      return;
    }

    setLoadingAction("signin");
    setErrorMessage("");
    setStatusMessage("");

    try {
      const account = await postJSON("/api/auth/login", {
        email: trimmedEmail,
        password: trimmedPassword,
      });

      routeByRole(account.role);
    } catch (error) {
      setErrorMessage(error?.message || "Could not sign in.");
    } finally {
      setLoadingAction("");
    }
  }

  async function handleWorkspaceSelect(role) {
    setSelectedRole(role);
    setErrorMessage("");
    setStatusMessage(`Workspace selected: ${role === "hr" ? "HR" : "Student"}. Complete the form below to create your account.`);
  }

  async function handleCreateAccount() {
    if (!selectedRole) {
      setErrorMessage("Choose Student or HR before creating your account.");
      return;
    }

    const trimmedName = signupName.trim();
    const trimmedEmail = signupEmail.trim().toLowerCase();
    const trimmedPassword = signupPassword.trim();

    if (!trimmedName || !trimmedEmail || !trimmedPassword) {
      setErrorMessage("Please enter your name, email, and password.");
      return;
    }

    setLoadingAction("signup");
    setErrorMessage("");
    setStatusMessage("");

    try {
      const account = await postJSON("/api/auth/upsert", {
        email: trimmedEmail,
        display_name: trimmedName,
        role: selectedRole,
        password: trimmedPassword,
        provider: "email",
        workspace: selectedRole,
      });

      routeByRole(account.role);
    } catch (error) {
      setErrorMessage(error?.message || "Could not create the account.");
    } finally {
      setLoadingAction("");
    }
  }

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setCurrentUser(user || null);
    });

    return unsubscribe;
  }, []);

  useEffect(() => {
    if (!currentUser?.email) {
      return;
    }

    if (mode === "signin" || hasPendingGoogleLookup) {
      void resolveAccount(currentUser);
    }
  }, [currentUser, mode, hasPendingGoogleLookup]);

  return (
    <main className="login-page">
      <section className="login-shell login-shell--auth">
        <header className="login-topbar">
          <a
            className="brand"
            href="#home"
            aria-label="HireFlow AI home"
            onClick={(event) => event.preventDefault()}
          >
            <LogoMark />
            <span>HireFlow AI</span>
          </a>

          <button className="login-link" type="button" onClick={onBack}>
            <span className="login-link-icon">⎋</span>
            Go back
          </button>
        </header>

        <div className="auth-layout">
          <aside className="auth-visual">
            <div className="auth-visual__badge">AI hiring + career flow</div>
            <h1>
              One workspace for <span className="gradient-text blue">students</span> and{" "}
              <span className="gradient-text purple">HR teams</span>.
            </h1>
            <p>
              Switch between sign in and sign up on the right. Use Google email for a quick
              start, then jump into the student or HR portal.
            </p>

            <div className="auth-visual__stack">
              <article className="auth-preview auth-preview--student">
                <img src={STUDENT_PREVIEW_SRC} alt="Student preview" />
                <div>
                  <strong>Student mode</strong>
                  <span>Resume help, job match, interview prep</span>
                </div>
              </article>

              <article className="auth-preview auth-preview--hr">
                <img src="/images/HR.png" alt="HR preview" />
                <div>
                  <strong>HR mode</strong>
                  <span>Screening, ranking, analytics</span>
                </div>
              </article>
            </div>
          </aside>

          <section className="auth-panel auth-panel--surface">
            <ModeTabs mode={mode} onChange={persistMode} />

            {errorMessage ? <div className="auth-status auth-status--error">{errorMessage}</div> : null}
            {statusMessage ? <div className="auth-status auth-status--success">{statusMessage}</div> : null}

            {mode === "signin" ? (
              <div className="auth-panel__body auth-panel__body--enter">
                <div className="auth-panel__header">
                  <span className="auth-panel__eyebrow">Returning users</span>
                  <h2>Sign in</h2>
                  <p>Use Google email or your existing account details to continue.</p>
                </div>

                <button
                  className="google-button"
                  type="button"
                  onClick={() => handleGoogleAuth("signin")}
                  disabled={loadingAction === "google" || loadingAction === "resolve"}
                >
                  <GoogleIcon />
                  {loadingAction === "google" ? "Connecting..." : "Continue with Google"}
                </button>



                <div className="auth-divider">
                  <span />
                  <strong>or use email</strong>
                  <span />
                </div>

                <label className="auth-field">
                  <span>Email</span>
                  <input
                    type="email"
                    placeholder="you@example.com"
                    value={signinEmail}
                    onChange={(event) => setSigninEmail(event.target.value)}
                  />
                </label>

                <label className="auth-field">
                  <span>Password</span>
                  <input
                    type="password"
                    placeholder="Your password"
                    value={signinPassword}
                    onChange={(event) => setSigninPassword(event.target.value)}
                  />
                </label>

                <button
                  className="auth-primary"
                  type="button"
                  onClick={handleEmailSignIn}
                  disabled={!signinEmail.trim() || !signinPassword.trim() || loadingAction === "signin"}
                >
                  {loadingAction === "signin" ? "Signing in..." : "Sign in"}
                </button>

                <p className="auth-note">
                  New here? Switch to <button type="button" onClick={() => persistMode("signup")}>create account</button>.
                </p>
              </div>
            ) : (
              <div className="auth-panel__body auth-panel__body--enter">
                <div className="auth-panel__header">
                  <span className="auth-panel__eyebrow">First time here</span>
                  <h2>Create account</h2>
                 
                </div>


                <label className="auth-field">
                  <span>Name</span>
                  <input
                    type="text"
                    placeholder="Your name"
                    value={signupName}
                    onChange={(event) => setSignupName(event.target.value)}
                  />
                </label>

                <label className="auth-field">
                  <span>Email</span>
                  <input
                    type="email"
                    placeholder="you@example.com"
                    value={signupEmail}
                    onChange={(event) => setSignupEmail(event.target.value)}
                  />
                </label>

                <label className="auth-field">
                  <span>Password</span>
                  <input
                    type="password"
                    placeholder="Create a password"
                    value={signupPassword}
                    onChange={(event) => setSignupPassword(event.target.value)}
                  />
                </label>

                <p className="auth-note">Choose a workspace.</p>

                <div className="workspace-picker">
                  <div className="workspace-picker__grid">
                    <button
                      className={`workspace-chip student ${selectedRole === "student" ? "active" : ""}`}
                      type="button"
                      onClick={() => handleWorkspaceSelect("student")}
                      disabled={loadingAction === "student"}
                    >
                      <span>Student portal</span>
                    </button>
                    <button
                      className={`workspace-chip hr ${selectedRole === "hr" ? "active" : ""}`}
                      type="button"
                      onClick={() => handleWorkspaceSelect("hr")}
                      disabled={loadingAction === "hr"}
                    >
                      <span>HR portal</span>
                    </button>
                  </div>
                </div>

                <button
                  className="auth-primary auth-primary--blue"
                  type="button"
                  onClick={handleCreateAccount}
                  disabled={!selectedRole || !signupName.trim() || !signupEmail.trim() || !signupPassword.trim() || loadingAction === "signup"}
                >
                  {loadingAction === "signup" ? "Creating..." : "Create account"}
                </button>

                <p className="auth-note">
                  Already have an account? Switch to <button type="button" onClick={() => persistMode("signin")}>sign in</button>.
                </p>
              </div>
            )}
          </section>
        </div>

        <footer className="login-footer">
          <span>Google email supported</span>
          <span>Secure sign in</span>
          <span>Student and HR access</span>
        </footer>
      </section>
    </main>
  );
}
