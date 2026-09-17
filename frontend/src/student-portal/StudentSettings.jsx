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
    <section className="student-portal__settings">
      <div className="student-portal__settings-shell">
        <header className="student-portal__settings-header">
          <div>
            <p className="student-portal__settings-kicker">Settings</p>
            <h1>General account information</h1>
            <p>Manage your profile, theme color, and manual API key from one place.</p>
          </div>
          
        </header>

        <div className="student-portal__settings-grid">
          <article className="student-portal__settings-card">
            <h2>Profile photo</h2>
            <p className="student-portal__settings-note">Upload a profile picture to personalize your account.</p>
            <div className="student-portal__photo-row">
              <div className="student-portal__photo-preview" aria-hidden="true">
                {profilePhoto ? <img src={profilePhoto} alt="" /> : <span>{profileInitials}</span>}
              </div>
              <div className="student-portal__photo-actions">
                <button className="student-portal__primary-pill" type="button" onClick={onOpenProfilePhotoPicker}>
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
            <div className="student-portal__settings-stack">
              {accountInfo.map((item) => (
                <div key={item.label} className="student-portal__settings-row">
                  <div className="student-portal__settings-row-left">
                    <span className="student-portal__settings-row-icon" aria-hidden="true">
                      {item.label === "Name" ? "👤" : "✉"}
                    </span>
                    <span>{item.label}</span>
                  </div>
                  <div className="student-portal__settings-row-right">
                    <strong>{item.value}</strong>
                    <button className="student-portal__settings-row-action" type="button" aria-label={`Edit ${item.label}`}>
                      ✎
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
              {themeOptions.map((theme) => (
                <button
                  key={theme.value}
                  className={`student-portal__theme-chip${selectedTheme.value === theme.value ? " is-active" : ""}`}
                  type="button"
                  onClick={() => onSelectTheme(theme)}
                  aria-pressed={selectedTheme.value === theme.value}
                >
                  <span className="student-portal__theme-chip-swatch" style={{ background: theme.value }} aria-hidden="true" />
                  <span>{theme.name}</span>
                </button>
              ))}
            </div>
          </article>

        </div>
      </div>
    </section>
  );
}
