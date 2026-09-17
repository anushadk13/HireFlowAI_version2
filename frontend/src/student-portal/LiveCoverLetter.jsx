import { useEffect, useState } from "react";

export default function LiveCoverLetter({
  jobDescription = "",
  setJobDescription,
  hasParsedJobDetails = false,
  parsedJobDetails = null,
  roleSummaryPoints = [],
  resume = "",
  setResume,
  resumeFileName = "Uploaded_Resume.pdf",
  coverLetter = "",
  loading = null,
  uploadedResumes = [],
  onSelectResumeFromLibrary,
  onGenerateCoverLetter,
}) {
  const [editableText, setEditableText] = useState("");
  const [selectedResumeOption, setSelectedResumeOption] = useState("current");

  useEffect(() => {
    if (coverLetter) {
      setEditableText(coverLetter);
    }
  }, [coverLetter]);

  const handleDownloadPDF = () => {
    const textToDownload = editableText || coverLetter;
    if (!textToDownload) return;

    const roleTitle = parsedJobDetails?.role_title;
    const documentTitle = roleTitle && roleTitle !== "Role not specified" ? `${roleTitle} Application` : "Application";

    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>${documentTitle.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</title>
            <style>
              body {
                font-family: Arial, sans-serif;
                padding: 40px;
                line-height: 1.65;
                color: #1e293b;
                max-width: 800px;
                margin: 0 auto;
              }
              p { margin-bottom: 16px; white-space: pre-wrap; font-size: 15px; }
            </style>
          </head>
          <body>
            <p>${textToDownload.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</p>
            <script>
              window.onload = function() {
                window.print();
              };
            </script>
          </body>
        </html>
      `);
      printWindow.document.close();
    } else {
      const element = document.createElement("a");
      const file = new Blob([textToDownload], { type: "text/plain" });
      element.href = URL.createObjectURL(file);
      element.download = `${documentTitle.replace(/\s+/g, "_")}.txt`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }
  };

  return (
    <section className="student-portal__cover-page">
      <header className="student-portal__cover-hero" style={{ display: "flex", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <h1 className="student-portal__cover-title">
            AI <span>Cover Letter Generator</span> ✨
          </h1>
          <p className="student-portal__cover-subtitle">
            Generate and edit a personalized cover letter matching your target job description.
          </p>
        </div>
      </header>

      <div className="student-portal__cover-layout">
        {/* Column 1 — Job Description, About the role, Select Resume & Generate button */}
        <article className="student-portal__panel">
          <div className="student-portal__panel-header">
            <div className="student-portal__panel-step">
              <span>1</span>
              <h2>Job Description</h2>
            </div>
          </div>

          <textarea
            className="student-portal__textarea student-portal__textarea--job"
            placeholder="Paste the job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription?.(e.target.value)}
          />

          <div className="student-portal__job-section">
            <h3>About the role</h3>
            {hasParsedJobDetails ? (
              <div className="student-portal__parsed-panel">
                <strong>{parsedJobDetails?.role_title || "Role details"}</strong>
                {roleSummaryPoints && roleSummaryPoints.length ? (
                  <ul className="student-portal__parsed-list">
                    {roleSummaryPoints.slice(0, 5).map((item, index) => (
                      <li key={`${item}-${index}`}>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>Role summary was extracted from the job description.</p>
                )}
              </div>
            ) : (
              <div className="student-portal__empty-panel">
                <div className="student-portal__empty-panel-icon" aria-hidden="true">
                  ◌
                </div>
                <strong>Your pasted job description will appear here.</strong>
                <p>We&apos;ll extract key details and requirements automatically.</p>
              </div>
            )}
          </div>

          {/* Select Resume Label & Dropdown */}
          <div className="student-portal__select-resume-group" style={{ marginTop: "16px" }}>
            <label
              htmlFor="cover-letter-resume-select"
              style={{
                display: "block",
                fontWeight: "700",
                fontSize: "0.92rem",
                color: "#1e293b",
                marginBottom: "8px",
              }}
            >
              Select Resume
            </label>
            <select
              id="cover-letter-resume-select"
              value={selectedResumeOption}
              onChange={(e) => {
                const value = e.target.value;
                setSelectedResumeOption(value);
                if (value !== "current" && value !== "default" && value !== "custom") {
                  onSelectResumeFromLibrary?.(value);
                }
              }}
              className="student-portal__select"
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: "12px",
                border: "1px solid rgba(130, 138, 180, 0.25)",
                background: "#ffffff",
                fontSize: "0.92rem",
                color: "#1e293b",
                outline: "none",
                cursor: "pointer",
              }}
            >
              <option value="current">
                {resumeFileName ? `📄 ${resumeFileName}` : "📄 Uploaded / Active Resume"}
              </option>
              {uploadedResumes.length > 0 && (
                <optgroup label="Resume Library">
                  {uploadedResumes.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      📄 {resume.name}
                    </option>
                  ))}
                </optgroup>
              )}
              <option value="default">📄 Default Resume (Software Engineer)</option>
              <option value="custom">📄 Custom Resume Text</option>
            </select>
          </div>

          {/* Generate Cover Letter Button */}
          <div style={{ marginTop: "18px" }}>
            <button
              className="student-portal__action-button student-portal__action-button--primary"
              type="button"
              onClick={onGenerateCoverLetter}
              disabled={loading === "cover-letter"}
              style={{ width: "100%", justifyContent: "center" }}
            >
              <span>{loading === "cover-letter" ? "⟳" : "✨"}</span>
              <span>{loading === "cover-letter" ? "Generating Cover Letter..." : "Generate Cover Letter"}</span>
            </button>
          </div>
        </article>

        {/* Column 2 — Generated Cover Letter (Editable) & Download PDF Option */}
        <aside className="student-portal__panel">
          <div className="student-portal__panel-header">
            <div className="student-portal__panel-step">
              <span>2</span>
              <h2>Generated Cover Letter</h2>
            </div>
          </div>

          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <textarea
              className="student-portal__textarea"
              style={{
                width: "100%",
                flex: 1,
                minHeight: "460px",
                border: "1px solid rgba(130, 138, 180, 0.18)",
                borderRadius: "14px",
                padding: "16px",
                background: "#ffffff",
                fontSize: "0.95rem",
                lineHeight: "1.65",
                color: "#1e293b",
                fontFamily: "inherit",
                outline: "none",
                resize: "vertical",
              }}
              value={editableText || coverLetter || ""}
              onChange={(e) => setEditableText(e.target.value)}
              placeholder="Click 'Generate Cover Letter' on the left. Your customized cover letter will appear here and you can edit every word directly before downloading!"
            />
          </div>

          {/* Download PDF Option */}
          <div style={{ marginTop: "16px" }}>
            <button
              className="student-portal__action-button student-portal__action-button--primary"
              type="button"
              onClick={handleDownloadPDF}
              disabled={!editableText && !coverLetter}
              style={{
                width: "100%",
                justifyContent: "center",
                background: "linear-gradient(135deg, #2563eb, #3b82f6)",
              }}
            >
              <span>⬇</span>
              <span>Download Cover Letter (PDF)</span>
            </button>
          </div>
        </aside>
      </div>
    </section>
  );
}
