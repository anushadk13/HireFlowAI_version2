import AiKeySettings from "../AiKeySettings.jsx";

export default function StudentSettings({
  accountInfo,
  currentUser,
  onBackToDashboard,
  onHandleProfilePhotoUpload,
  onRemoveProfilePhoto,
  onOpenProfilePhotoPicker,
  profileInitials,
  profilePhoto,
  profilePhotoInputRef,
  selectedTheme,
  themeOptions,
  onSelectTheme,
}) {
  return (
    <section className="student-portal__settings student-portal__settings--v2">
      <div className="student-portal__settings-shell">
        <header className="student-portal__settings-header">
          <div>
            <h1>Settings</h1>
            <p>Manage your profile, theme color, and manual API key from one place.</p>
          </div>
        </header>

        <div className="student-portal__settings-grid">
          <article className="student-portal__settings-card">
            <h2>Profile photo</h2>
            <p className="student-portal__settings-note">Upload a profile picture to personalize your account.</p>
            <div className="student-portal__photo-row">
              <div className="student-portal__photo-wrap">
                <div className="student-portal__photo-preview" aria-hidden="true">
                  {profilePhoto ? <img src={profilePhoto} alt="" /> : <span>{profileInitials}</span>}
                </div>
                <button
                  className="student-portal__photo-camera"
                  type="button"
                  onClick={onOpenProfilePhotoPicker}
                  aria-label="Change profile picture"
                >
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
                    <path d="M9 4l-1.5 2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-2.5L15 4H9zm3 4.5a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9zm0 2a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z" />
                  </svg>
                </button>
              </div>
              <div className="student-portal__photo-side">
                <div className="student-portal__photo-actions">
                  <button className="student-portal__primary-pill" type="button" onClick={onOpenProfilePhotoPicker}>
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M12 16V4M7 9l5-5 5 5M4 20h16" />
                    </svg>
                    Upload picture
                  </button>
                  {profilePhoto ? (
                    <button className="student-portal__ghost-button" type="button" onClick={onRemoveProfilePhoto}>
                      Remove
                    </button>
                  ) : null}
                </div>
                <p className="student-portal__settings-hint">JPG, PNG or WEBP. Max 5MB.</p>
              </div>
            </div>
            <input
              ref={profilePhotoInputRef}
              className="student-portal__hidden-input"
              type="file"
              accept="image/*"
              onChange={onHandleProfilePhotoUpload}
            />
          </article>

          <article className="student-portal__settings-card">
            <h2>Account</h2>
            <p className="student-portal__settings-note">Your personal information and login details.</p>
            <div className="student-portal__settings-stack">
              {accountInfo.map((item) => (
                <div key={item.label} className="student-portal__settings-row">
                  <div className="student-portal__settings-row-left">
                    <span className="student-portal__settings-row-icon" aria-hidden="true">
                      {item.label === "Name" ? (
                        <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
                          <circle cx="12" cy="8" r="4.5" />
                          <path d="M3.5 21c.6-4.4 4-7 8.5-7s7.9 2.6 8.5 7z" />
                        </svg>
                      ) : (
                        <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
                          <path d="M3 5h18a1 1 0 0 1 1 1v.4l-10 6.6L2 6.4V6a1 1 0 0 1 1-1zm-1 4.3l10 6.6 10-6.6V18a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1z" />
                        </svg>
                      )}
                    </span>
                    <span>{item.label}</span>
                  </div>
                  <div className="student-portal__settings-row-right">
                    <strong>{item.value}</strong>
                    <button className="student-portal__settings-row-action" type="button" aria-label={`Edit ${item.label}`}>
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
                        <path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zM20.7 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="student-portal__settings-card">
            <h2>Theme color</h2>
            <p className="student-portal__settings-note">Choose the accent color used across the student portal.</p>
            <div className="student-portal__theme-grid" role="list" aria-label="Theme color options">
              {themeOptions.map((theme) => {
                const isActive = selectedTheme.value === theme.value;
                return (
                  <button
                    key={theme.value}
                    className={`student-portal__theme-chip${isActive ? " is-active" : ""}`}
                    style={{ "--chip-color": theme.value, "--chip-rgb": theme.rgb }}
                    type="button"
                    onClick={() => onSelectTheme(theme)}
                    aria-pressed={isActive}
                  >
                    {isActive ? (
                      <span className="student-portal__theme-chip-check" aria-hidden="true">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M5 12.5l4.5 4.5L19 7.5" />
                        </svg>
                      </span>
                    ) : null}
                    <span className="student-portal__theme-chip-swatch" style={{ background: theme.value }} aria-hidden="true" />
                    <span>{theme.name}</span>
                  </button>
                );
              })}
            </div>
          </article>

          <article className="student-portal__settings-card">
            <h2>AI API key</h2>
            <p className="student-portal__settings-note">
              Bring your own Gemini, Claude or OpenAI key to power resume analysis and cover letters. It's kept only
              for this browser session and is cleared when you sign out.
            </p>
            <AiKeySettings
              classes={{
                stack: "student-portal__settings-stack student-portal__ai-form",
                fields: "student-portal__ai-fields",
                field: "student-portal__ai-field",
                inputWrap: "student-portal__ai-input-wrap",
                reveal: "student-portal__ai-reveal",
                input: "student-portal__settings-input",
                actions: "student-portal__photo-actions",
                primary: "student-portal__primary-pill",
                ghost: "student-portal__ghost-button",
                hint: "student-portal__ai-status",
                label: "student-portal__ai-label",
                lockIcon: true,
              }}
            />
          </article>
        </div>
      </div>
    </section>
  );
}
