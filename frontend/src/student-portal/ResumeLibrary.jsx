import { useRef, useState } from "react";

const MAX_RESUMES = 5;

const FEATURES = [
  {
    title: "Secure storage",
    copy: "Your files are private to your account.",
    path: "M12 3l7 3v5c0 4.4-2.9 8.3-7 10-4.1-1.7-7-5.6-7-10V6l7-3zm-1 11.2l5-5-1.4-1.4-3.6 3.6-1.6-1.6-1.4 1.4 3 3z",
  },
  {
    title: "Quick access",
    copy: "Reuse a saved resume in one click.",
    path: "M13 2L4 14h6l-1 8 9-12h-6l1-8z",
  },
  {
    title: "Multiple formats",
    copy: "PDF, DOCX, TXT and Markdown.",
    path: "M6 2h8l6 6v14H6V2zm7 1.5V9h5.5L13 3.5zM9 13h8v1.5H9V13zm0 3.5h8V18H9v-1.5z",
  },
  {
    title: "Easy to manage",
    copy: "Keep up to five resumes ready to go.",
    path: "M4 6h16v2H4V6zm0 5h16v2H4v-2zm0 5h10v2H4v-2z",
  },
];

function fileKind(name = "") {
  const ext = name.split(".").pop()?.toLowerCase();
  return ["pdf", "docx", "txt", "md"].includes(ext) ? ext.toUpperCase() : "FILE";
}

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export default function ResumeLibrary({
  uploadedResumes = [],
  onAddResume,
  onDeleteResume,
  onSelectResume,
  onNavigateToAnalyzer,
}) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const handleAdd = async (event) => {
    if (onAddResume) {
      await onAddResume(event);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    const files = event.dataTransfer?.files;
    if (files?.length) {
      handleAdd({ target: { files, value: "" } });
    }
  };

  const handleUse = async (id) => {
    await onSelectResume?.(id);
    onNavigateToAnalyzer?.();
  };

  const atLimit = uploadedResumes.length >= MAX_RESUMES;

  return (
    <section className="student-portal__library">
      <div className="student-portal__library-shell">
        <header className="student-portal__library-header">
          <div>
            <h1>Resume library</h1>
            <p>Upload and manage your resumes for quick access in the analyzer and cover letter generator.</p>
          </div>
          <span className="student-portal__library-count">
            {uploadedResumes.length} of {MAX_RESUMES} saved
          </span>
        </header>

        <ul className="student-portal__library-features">
          {FEATURES.map((feature) => (
            <li key={feature.title}>
              <span className="student-portal__library-feature-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                  <path d={feature.path} />
                </svg>
              </span>
              <div>
                <strong>{feature.title}</strong>
                <span>{feature.copy}</span>
              </div>
            </li>
          ))}
        </ul>

        <input
          ref={inputRef}
          className="student-portal__hidden-input"
          type="file"
          accept=".pdf,.docx,.txt,.md,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={handleAdd}
        />

        <button
          type="button"
          className={`student-portal__library-drop${dragging ? " is-dragging" : ""}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <span className="student-portal__library-drop-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 16V4M7 9l5-5 5 5M4 20h16" />
            </svg>
          </span>
          <span className="student-portal__library-drop-text">
            <strong>Click to upload</strong> or drag and drop a resume
            <small>PDF, DOCX, TXT or Markdown{atLimit ? ` · the oldest is replaced after ${MAX_RESUMES}` : ""}</small>
          </span>
        </button>

        {uploadedResumes.length === 0 ? (
          <p className="student-portal__library-empty">No resumes yet. Upload one to see it here.</p>
        ) : (
          <ul className="student-portal__library-list">
            {uploadedResumes.map((resume) => (
              <li key={resume.id} className="student-portal__library-item">
                <span className="student-portal__library-badge" aria-hidden="true">
                  {fileKind(resume.name)}
                </span>
                <div className="student-portal__library-meta">
                  <strong title={resume.name}>{resume.name}</strong>
                  <span>
                    {[resume.size, formatDate(resume.uploadDate)].filter(Boolean).join(" · ")}
                  </span>
                </div>
                <div className="student-portal__library-actions">
                  <button className="student-portal__primary-pill" type="button" onClick={() => handleUse(resume.id)}>
                    Use resume
                  </button>
                  <button
                    className="student-portal__library-delete"
                    type="button"
                    onClick={() => onDeleteResume?.(resume.id)}
                    aria-label={`Delete ${resume.name}`}
                    title="Delete resume"
                  >
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
                      <path d="M10 11v6M14 11v6" />
                    </svg>
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
