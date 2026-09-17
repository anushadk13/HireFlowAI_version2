import { useRef } from "react";

export default function ResumeLibrary({
  uploadedResumes = [],
  onAddResume,
  onDeleteResume,
  onSelectResume,
  onNavigateToAnalyzer,
}) {
  const resumeLibraryInputRef = useRef(null);

  const handleAddResumeToLibrary = async (event) => {
    if (onAddResume) {
      await onAddResume(event);
    }
  };

  return (
    <section className="student-portal__cover-page" style={{ background: "#f8f9fc", minHeight: "100vh" }}>
      <header style={{ padding: "24px 24px 20px", textAlign: "center" }}>
        <div
          style={{
            fontSize: "0.65rem",
            fontWeight: "600",
            letterSpacing: "1.5px",
            color: "#64748b",
            marginBottom: "8px",
            textTransform: "uppercase",
          }}
        >
          YOUR CAREER, ORGANIZED
        </div>
        <h1
          style={{
            fontSize: "2rem",
            fontWeight: "700",
            color: "#1e293b",
            marginBottom: "8px",
            lineHeight: "1.1",
          }}
        >
          Resume <span style={{ color: "#4f46e5" }}>Library</span>
        </h1>
        <p
          style={{
            fontSize: "0.95rem",
            color: "#64748b",
            maxWidth: "500px",
            margin: "0 auto",
          }}
        >
          Upload and manage your resumes for quick access in cover letter generation.
        </p>
      </header>

      {/* Feature Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "12px",
          maxWidth: "800px",
          margin: "0 auto 24px",
          padding: "0 24px",
        }}
      >
        <div
          style={{
            background: "linear-gradient(135deg, #f8f9fc 0%, #eef2f7 100%)",
            padding: "16px 12px",
            borderRadius: "12px",
            textAlign: "center",
            boxShadow: "0 2px 4px rgba(0,0,0,0.06)",
            border: "1px solid rgba(79, 70, 229, 0.08)",
          }}
        >
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "50%",
              background: "rgba(79, 70, 229, 0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 10px",
              fontSize: "18px",
            }}
          >
            🔒
          </div>
          <h3 style={{ fontSize: "0.85rem", fontWeight: "700", color: "#1e293b", marginBottom: "4px" }}>
            Secure Storage
          </h3>
          <p style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: "1.4" }}>Your files are safe and private</p>
        </div>

        <div
          style={{
            background: "linear-gradient(135deg, #f8f9fc 0%, #eef2f7 100%)",
            padding: "16px 12px",
            borderRadius: "12px",
            textAlign: "center",
            boxShadow: "0 2px 4px rgba(0,0,0,0.06)",
            border: "1px solid rgba(79, 70, 229, 0.08)",
          }}
        >
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "50%",
              background: "rgba(79, 70, 229, 0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 10px",
              fontSize: "18px",
            }}
          >
            ⚡
          </div>
          <h3 style={{ fontSize: "0.85rem", fontWeight: "700", color: "#1e293b", marginBottom: "4px" }}>
            Quick Access
          </h3>
          <p style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: "1.4" }}>Use anytime, anywhere</p>
        </div>

        <div
          style={{
            background: "linear-gradient(135deg, #f8f9fc 0%, #eef2f7 100%)",
            padding: "16px 12px",
            borderRadius: "12px",
            textAlign: "center",
            boxShadow: "0 2px 4px rgba(0,0,0,0.06)",
            border: "1px solid rgba(79, 70, 229, 0.08)",
          }}
        >
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "50%",
              background: "rgba(79, 70, 229, 0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 10px",
              fontSize: "18px",
            }}
          >
            📄
          </div>
          <h3 style={{ fontSize: "0.85rem", fontWeight: "700", color: "#1e293b", marginBottom: "4px" }}>
            Multiple Formats
          </h3>
          <p style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: "1.4" }}>PDF, DOCX, TXT and Markdown</p>
        </div>

        <div
          style={{
            background: "linear-gradient(135deg, #f8f9fc 0%, #eef2f7 100%)",
            padding: "16px 12px",
            borderRadius: "12px",
            textAlign: "center",
            boxShadow: "0 2px 4px rgba(0,0,0,0.06)",
            border: "1px solid rgba(79, 70, 229, 0.08)",
          }}
        >
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "50%",
              background: "rgba(79, 70, 229, 0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 10px",
              fontSize: "18px",
            }}
          >
            ❤️
          </div>
          <h3 style={{ fontSize: "0.85rem", fontWeight: "700", color: "#1e293b", marginBottom: "4px" }}>
            Easy to Manage
          </h3>
          <p style={{ fontSize: "0.75rem", color: "#64748b", lineHeight: "1.4" }}>
            Organize, update and keep it ready
          </p>
        </div>
      </div>

      <div style={{ maxWidth: "900px", margin: "0 auto", padding: "0 24px 32px" }}>
        <input
          ref={resumeLibraryInputRef}
          className="student-portal__hidden-input"
          type="file"
          accept=".pdf,.docx,.txt,.md,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={handleAddResumeToLibrary}
        />

        {/* Resumes Flex Layout with Add Card */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "16px",
          }}
        >
          {/* Uploaded Resume Cards */}
          {uploadedResumes.map((resume) => (
            <div
              key={resume.id}
              style={{
                flex: "0 0 280px",
                padding: "20px",
                border: "1px solid rgba(130, 138, 180, 0.2)",
                borderRadius: "12px",
                background: "#ffffff",
                boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                transition: "all 0.2s ease",
                display: "flex",
                flexDirection: "column",
                position: "relative",
                minHeight: "180px",
              }}
            >
              <button
                type="button"
                onClick={() => onDeleteResume?.(resume.id)}
                style={{
                  position: "absolute",
                  top: "12px",
                  right: "12px",
                  width: "32px",
                  height: "32px",
                  borderRadius: "6px",
                  background: "transparent",
                  border: "none",
                  color: "#94a3b8",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.2s ease",
                  padding: "0",
                }}
                title="Delete resume"
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = "#ef4444";
                  e.currentTarget.style.background = "rgba(239, 68, 68, 0.08)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = "#94a3b8";
                  e.currentTarget.style.background = "transparent";
                }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  <line x1="10" y1="11" x2="10" y2="17"></line>
                  <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>
              </button>
              <div>
                <div
                  style={{
                    fontWeight: "600",
                    color: "#1e293b",
                    marginBottom: "6px",
                    fontSize: "1rem",
                    wordBreak: "break-word",
                    paddingRight: "40px",
                  }}
                >
                  📄 {resume.name}
                </div>
                <div style={{ fontSize: "0.8rem", color: "#64748b" }}>{resume.size}</div>
                <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "4px" }}>
                  {new Date(resume.uploadDate).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}

          {/* Add New Resume Card */}
          <div
            onClick={() => resumeLibraryInputRef.current?.click()}
            style={{
              flex: "0 0 280px",
              padding: "20px",
              border: "2px dashed rgba(79, 70, 229, 0.3)",
              borderRadius: "12px",
              background: "rgba(79, 70, 229, 0.02)",
              cursor: "pointer",
              transition: "all 0.2s ease",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              minHeight: "180px",
              textAlign: "center",
            }}
            role="button"
            tabIndex={0}
          >
            <div
              style={{
                width: "50px",
                height: "50px",
                borderRadius: "50%",
                background: "#4f46e5",
                color: "#ffffff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "28px",
                marginBottom: "12px",
                fontWeight: "300",
              }}
            >
              +
            </div>
            <p
              style={{
                fontSize: "0.9rem",
                color: "#4f46e5",
                fontWeight: "600",
              }}
            >
              Add New Resume
            </p>
            <p
              style={{
                fontSize: "0.75rem",
                color: "#94a3b8",
                marginTop: "4px",
              }}
            >
              Click to upload
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
