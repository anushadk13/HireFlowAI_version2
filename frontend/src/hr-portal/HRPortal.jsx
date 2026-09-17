import { useEffect, useState } from "react";
import "./HRPortal.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "grid", blurb: "Track pipeline health and hiring analytics at a glance." },
  { id: "analyze", label: "Analyze", icon: "upload", blurb: "Upload a job description, pick a resume source, and rank every candidate in one run." },
  { id: "interviews", label: "Interviews", icon: "calendar", blurb: "Move candidates through interview rounds for a requisition." },
];

// Mirrors backend/services/pipeline.py::STAGES.
const STAGES = ["Screened", "Shortlisted", "Interview Round 1", "Interview Round 2", "Offer", "Accepted", "Rejected"];

const SAMPLE_JD = `Software Engineer JD

We are looking for a Software Engineer with strong Python, SQL, React, and FastAPI experience.
You will build internal tools, work with Docker and AWS, and collaborate with product, design, and engineering teams.
Experience with APIs, analytics dashboards, and scalable workflows is preferred.
Bachelor's degree or equivalent experience required.`;

async function postJSON(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed with status ${res.status}`);
  }
  return res.json();
}

async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`Request to ${path} failed with status ${res.status}`);
  }
  return res.json();
}

async function patchJSON(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed with status ${res.status}`);
  }
  return res.json();
}

async function extractFileText(file, userId = "") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", userId);
  const res = await fetch(`${API_BASE}/api/resume/extract-text`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    throw new Error(`${file.name}: could not be read (status ${res.status})`);
  }
  const data = await res.json();
  return data.text || "";
}

function pillList(values) {
  const items = Array.isArray(values) ? values : [];
  return (
    <div className="hr-portal__pill-list">
      {items.length ? items.map((value) => <span key={String(value)} className="hr-portal__pill">{String(value)}</span>) : <span className="hr-portal__pill hr-portal__pill--muted">None</span>}
    </div>
  );
}

function initialsOf(name) {
  return (name || "?")
    .split(" ")
    .filter(Boolean)
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function stripExtension(filename) {
  return (filename || "Candidate").replace(/\.[^./\\]+$/, "");
}

function CandidateEmailEditor({ value, onSave }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value || "");

  if (!editing) {
    return (
      <button
        type="button"
        className="hr-portal__clear-link"
        onClick={() => {
          setDraft(value || "");
          setEditing(true);
        }}
      >
        {value ? value : "Add email"}
      </button>
    );
  }

  return (
    <form
      className="hr-portal__inline-email-form"
      onSubmit={(e) => {
        e.preventDefault();
        if (!draft.trim()) return;
        onSave(draft.trim());
        setEditing(false);
      }}
    >
      <input
        className="hr-portal__text-input hr-portal__text-input--small"
        type="email"
        value={draft}
        autoFocus
        onChange={(e) => setDraft(e.target.value)}
        placeholder="candidate@email.com"
      />
      <button type="submit" className="hr-portal__btn hr-portal__btn--ghost hr-portal__btn--small">
        Save
      </button>
    </form>
  );
}

function formatBytes(size) {
  if (!size && size !== 0) return "";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function NavIcon({ name }) {
  switch (name) {
    case "upload":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 15.5a3.5 3.5 0 0 1 1.3-6.7 5 5 0 0 1 9.6 1.6 3.3 3.3 0 0 1 0 5.1" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M12 17V9.5M9.2 12.3 12 9.5l2.8 2.8" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "folder":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 7a1.5 1.5 0 0 1 1.5-1.5h4l2 2h7A1.5 1.5 0 0 1 20 9v8a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 17V7z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
        </svg>
      );
    case "cloud":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M7 18a4 4 0 0 1-.6-7.96A5 5 0 0 1 16.2 8.3 4.5 4.5 0 0 1 17.5 17H7.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "bars":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 19v-5.5M12 19V7M18 19v-9" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
        </svg>
      );
    case "calendar":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="4" y="5.5" width="16" height="14.5" rx="2.2" stroke="currentColor" strokeWidth="1.7" />
          <path d="M4 9.8h16M8 3.5v3.2M16 3.5v3.2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
          <path d="M8.5 13.3h2.2M13.3 13.3h2.2M8.5 16.4h2.2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
      );
    case "grid":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="4" y="4" width="7" height="7" rx="1.6" stroke="currentColor" strokeWidth="1.7" />
          <rect x="13" y="4" width="7" height="7" rx="1.6" stroke="currentColor" strokeWidth="1.7" />
          <rect x="4" y="13" width="7" height="7" rx="1.6" stroke="currentColor" strokeWidth="1.7" />
          <rect x="13" y="13" width="7" height="7" rx="1.6" stroke="currentColor" strokeWidth="1.7" />
        </svg>
      );
    case "close":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 6l12 12M18 6 6 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case "attach":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M8 12.5l6.5-6.5a3 3 0 1 1 4.2 4.2L10.8 18a5 5 0 1 1-7-7L12 3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "arrow-right":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "download":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 4v11m0 0 4-4m-4 4-4-4M5 19h14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "chevron-down":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "users":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="9" cy="8.5" r="3" stroke="currentColor" strokeWidth="1.7" />
          <path d="M3.5 19c0-3 2.5-5 5.5-5s5.5 2 5.5 5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
          <path d="M15.5 6.2a3 3 0 0 1 0 5.8M18 19c0-2.4-1.6-4.3-3.8-4.9" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
      );
    case "bolt":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M13 3 5 13h5l-1 8 8-10h-5l1-8z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round" />
        </svg>
      );
    case "shield":
      return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 3.5 19 6v6c0 5-3 7.8-7 8.5-4-.7-7-3.5-7-8.5V6l7-2.5z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
          <path d="M9 12.2l2 2 4-4.4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    default:
      return null;
  }
}

export default function HRPortal({ onBack }) {
  const [activeTab, setActiveTab] = useState("analyze");

  // Job description
  const [jobDescription, setJobDescription] = useState("");

  // Job requisition (a job opening that can be reopened later as its own record)
  const [requisitions, setRequisitions] = useState([]);
  const [requisitionMode, setRequisitionMode] = useState("new");
  const [newRequisitionTitle, setNewRequisitionTitle] = useState("");
  const [selectedRequisitionId, setSelectedRequisitionId] = useState("");
  const [activeRequisitionId, setActiveRequisitionId] = useState("");

  // Resume source
  const [resumeSource, setResumeSource] = useState("local");
  const [localFiles, setLocalFiles] = useState([]);
  const [azureResumes, setAzureResumes] = useState([]);
  const [selectedAzureIds, setSelectedAzureIds] = useState(new Set());
  const [azureLoading, setAzureLoading] = useState(false);
  const [azureLoaded, setAzureLoaded] = useState(false);

  // Analysis run
  const [rankedCandidates, setRankedCandidates] = useState([]);
  const [analysisProgress, setAnalysisProgress] = useState(null);
  const [failedFiles, setFailedFiles] = useState([]);

  const [dashboard, setDashboard] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [dashboardRequisitionId, setDashboardRequisitionId] = useState("");
  const [pendingEmails, setPendingEmails] = useState([]);
  const [emailsLoading, setEmailsLoading] = useState(false);

  // Interview pipeline (per-requisition, persisted)
  const [interviewsRequisitionId, setInterviewsRequisitionId] = useState("");
  const [pipelineRecords, setPipelineRecords] = useState([]);
  const [pipelineLoading, setPipelineLoading] = useState(false);
  const [moveTarget, setMoveTarget] = useState({});

  const [loading, setLoading] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    loadRequisitions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadRequisitions() {
    try {
      const data = await getJSON("/api/hr/requisitions");
      setRequisitions(data.requisitions || []);
    } catch (err) {
      setError(err.message);
    }
  }

  function handleExportResults() {
    if (rankedCandidates.length === 0) return;
    const rows = rankedCandidates.map(
      (c, i) => `${i + 1},"${(c.name || "").replace(/"/g, '""')}",${c.score}`
    );
    const csv = ["Rank,Name,Score", ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ranked-candidates.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleLocalFilesChange(event) {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    if (files.length === 0) return;
    setLocalFiles((prev) => [...prev, ...files]);
  }

  function removeLocalFile(index) {
    setLocalFiles((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleLoadAzureResumes() {
    setError("");
    setAzureLoading(true);
    try {
      const data = await getJSON("/api/hr/resumes");
      const resumes = data.resumes || [];
      setAzureResumes(resumes);
      setSelectedAzureIds(new Set(resumes.map((r) => r.id)));
      setAzureLoaded(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setAzureLoading(false);
    }
  }

  function toggleAzureResume(id) {
    setSelectedAzureIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAllAzureResumes() {
    setSelectedAzureIds((prev) =>
      prev.size === azureResumes.length ? new Set() : new Set(azureResumes.map((r) => r.id))
    );
  }

  async function handleLoadDashboard(requisitionId = dashboardRequisitionId) {
    setError("");
    setLoading("dashboard");
    try {
      const query = requisitionId ? `?requisition_id=${encodeURIComponent(requisitionId)}` : "";
      const [dash, stats] = await Promise.all([
        getJSON(`/api/hr/dashboard${query}`),
        getJSON(`/api/analytics${query}`),
      ]);
      setDashboard(dash);
      setAnalytics(stats);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(null);
    }
  }

  async function loadPendingEmails(requisitionId = dashboardRequisitionId) {
    setEmailsLoading(true);
    try {
      const query = requisitionId ? `?requisition_id=${encodeURIComponent(requisitionId)}` : "";
      const data = await getJSON(`/api/hr/emails/pending${query}`);
      setPendingEmails(data.drafts || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setEmailsLoading(false);
    }
  }

  async function handleSendEmail(draft) {
    setError("");
    try {
      const result = await postJSON(
        `/api/hr/emails/${draft.id}/send?requisition_id=${encodeURIComponent(draft.requisition_id)}`,
        {}
      );
      setPendingEmails((prev) => prev.filter((d) => d.id !== draft.id));
      if (result.status === "failed") {
        setError(`Could not send to ${draft.candidate_email || "candidate"}: ${result.error}`);
      } else {
        setNotice(`Sent to ${draft.candidate_email}.`);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSendAllEmails() {
    if (pendingEmails.length === 0) return;
    setError("");
    try {
      const result = await postJSON("/api/hr/emails/send-bulk", { email_ids: pendingEmails.map((d) => d.id) });
      const results = result.results || [];
      const failedCount = results.filter((r) => r.status !== "sent").length;
      setNotice(
        failedCount > 0
          ? `Sent ${results.length - failedCount}, ${failedCount} failed.`
          : `Sent ${results.length} email(s).`
      );
      loadPendingEmails();
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadPipeline(requisitionId) {
    if (!requisitionId) {
      setPipelineRecords([]);
      return;
    }
    setPipelineLoading(true);
    setError("");
    try {
      const data = await getJSON(`/api/hr/requisitions/${requisitionId}/pipeline`);
      setPipelineRecords(data.pipeline || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setPipelineLoading(false);
    }
  }

  async function handleMoveStage(record) {
    const target = moveTarget[record.id];
    if (!target) return;
    setError("");
    try {
      let updated;
      let draftEmail;
      if (target.startsWith("Interview")) {
        const res = await postJSON(
          `/api/hr/requisitions/${interviewsRequisitionId}/pipeline/${record.id}/advance-interview`,
          { round_label: target }
        );
        updated = res.record;
        draftEmail = res.draft_email;
      } else {
        const res = await patchJSON(
          `/api/hr/requisitions/${interviewsRequisitionId}/pipeline/${record.id}/stage`,
          { new_stage: target }
        );
        updated = res.record;
        draftEmail = res.draft_email;
      }
      setPipelineRecords((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setMoveTarget((prev) => ({ ...prev, [record.id]: "" }));
      if (draftEmail) setNotice("Draft email created — review it in Pending approvals on the Dashboard.");
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleUpdateCandidateEmail(requisitionId, pipelineId, email, onSuccess) {
    setError("");
    try {
      const updated = await patchJSON(`/api/hr/requisitions/${requisitionId}/pipeline/${pipelineId}/email`, {
        email,
      });
      onSuccess(updated);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleRunAnalysis() {
    if (!jobDescription.trim()) {
      setError("Upload or paste a job description first.");
      return;
    }
    if (requisitionMode === "new" && !newRequisitionTitle.trim()) {
      setError("Give this job requisition a title first.");
      return;
    }
    if (requisitionMode === "existing" && !selectedRequisitionId) {
      setError("Select an existing requisition first.");
      return;
    }

    const azureSelected = azureResumes.filter((r) => selectedAzureIds.has(r.id));
    const items = resumeSource === "local" ? localFiles : azureSelected;

    if (items.length === 0) {
      setError(
        resumeSource === "local"
          ? "Choose a resume folder or files first."
          : "Select at least one resume from Azure Blob Storage."
      );
      return;
    }

    setError("");
    setNotice("");
    setFailedFiles([]);
    setLoading("analyze");
    setAnalysisProgress({ done: 0, total: items.length });

    const extractOne =
      resumeSource === "local"
        ? async (file) => ({
            name: stripExtension(file.name),
            resume_text: await extractFileText(file),
            candidate_source: "local",
          })
        : async (record) => {
            const res = await fetch(
              `${API_BASE}/api/resume/${record.id}/text?user_id=${encodeURIComponent(record.user_id)}`
            );
            if (!res.ok) throw new Error(`${record.filename}: could not be read (status ${res.status})`);
            const data = await res.json();
            return {
              name: stripExtension(record.filename),
              resume_text: data.text || "",
              candidate_source: "blob",
              resume_id: record.id,
              resume_user_id: record.user_id,
            };
          };

    const settled = await Promise.allSettled(
      items.map((item) =>
        extractOne(item).finally(() => setAnalysisProgress((prev) => ({ ...prev, done: prev.done + 1 })))
      )
    );

    const candidates = [];
    const failed = [];
    settled.forEach((result, index) => {
      if (result.status === "fulfilled") {
        candidates.push(result.value);
      } else {
        failed.push(resumeSource === "local" ? items[index].name : items[index].filename);
      }
    });
    setFailedFiles(failed);

    if (candidates.length === 0) {
      setError("None of the selected resumes could be read. Check the files and try again.");
      setLoading(null);
      setAnalysisProgress(null);
      return;
    }

    try {
      let requisitionId = selectedRequisitionId;
      if (requisitionMode === "new") {
        const created = await postJSON("/api/hr/requisitions", {
          title: newRequisitionTitle.trim(),
          job_description: jobDescription,
          created_by: "",
        });
        requisitionId = created.id;
        setRequisitions((prev) => [created, ...prev]);
        setSelectedRequisitionId(created.id);
        setRequisitionMode("existing");
        setNewRequisitionTitle("");
      }

      const result = await postJSON("/api/hr/rank", {
        job_description: jobDescription,
        requisition_id: requisitionId,
        candidates,
      });
      setRankedCandidates(result.ranked || []);
      setActiveRequisitionId(requisitionId);
      setInterviewsRequisitionId(requisitionId);
      loadPipeline(requisitionId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(null);
      setAnalysisProgress(null);
    }
  }

  const activeNavItem = NAV_ITEMS.find((item) => item.id === activeTab) || NAV_ITEMS[0];
  const allAzureSelected = azureResumes.length > 0 && selectedAzureIds.size === azureResumes.length;

  const hasResumesSelected = resumeSource === "local" ? localFiles.length > 0 : selectedAzureIds.size > 0;
  const requisitionReady =
    requisitionMode === "new" ? newRequisitionTitle.trim().length > 0 : selectedRequisitionId.length > 0;
  const canRunAnalysis =
    jobDescription.trim().length > 0 && hasResumesSelected && requisitionReady && loading !== "analyze";

  return (
    <div className="hr-portal">
      <aside className="hr-portal__sidebar">
        <div className="hr-portal__brand">
          <div className="hr-portal__brand-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <div>
            <div className="hr-portal__brand-name">HireFlow AI</div>
            <div className="hr-portal__brand-sub">HR Suite</div>
          </div>
        </div>

       
        <nav className="hr-portal__nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={
                "hr-portal__nav-item" +
                (activeTab === item.id ? " hr-portal__nav-item--active" : "")
              }
              onClick={() => {
                setActiveTab(item.id);
                setNotice("");
                if (item.id === "dashboard" && !dashboard) {
                  handleLoadDashboard().catch((err) => setError(err.message));
                  loadPendingEmails().catch(() => {});
                }
                if (item.id === "interviews" && !interviewsRequisitionId && activeRequisitionId) {
                  setInterviewsRequisitionId(activeRequisitionId);
                  loadPipeline(activeRequisitionId);
                }
              }}
            >
              <span className="hr-portal__nav-icon">
                <NavIcon name={item.icon} />
              </span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="hr-portal__sidebar-footer">
          <span className="hr-portal__avatar hr-portal__avatar--brand">HR</span>
          <div>
            <div className="hr-portal__footer-name">Recruiter workspace</div>
            <div className="hr-portal__footer-sub">Admin access</div>
          </div>
        </div>
      </aside>

      <main className="hr-portal__main">
        <header className="hr-portal__header">
          <div>
            <p className="hr-portal__eyebrow">HR Portal</p>
            <h1>{activeNavItem.label}</h1>
            <p className="hr-portal__header-sub">{activeNavItem.blurb}</p>
          </div>
          {activeTab === "analyze" && (
            <div className="hr-portal__hero-art" aria-hidden="true">
              <svg viewBox="0 0 220 170" fill="none">
                <rect x="6" y="46" width="88" height="118" rx="14" fill="#e9edfb" transform="rotate(-9 50 105)" />
                <rect x="122" y="34" width="88" height="118" rx="14" fill="#e9edfb" transform="rotate(8 166 93)" />
                <rect x="58" y="14" width="100" height="140" rx="16" fill="#ffffff" stroke="#e1e6f6" strokeWidth="1.4" />
                <circle cx="108" cy="52" r="17" fill="#7a40ff" opacity="0.9" />
                <path d="M99 56c3-5 15-5 18 0" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
                <rect x="76" y="86" width="64" height="6" rx="3" fill="#d4d9ee" />
                <rect x="76" y="100" width="46" height="6" rx="3" fill="#d4d9ee" />
                <rect x="76" y="118" width="52" height="7" rx="3.5" fill="#ffb23e" />
                <path d="M79 122l3 3 6-7M96 122l3 3 6-7M113 122l3 3 6-7" stroke="#7a4c00" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" opacity="0.5" />
              </svg>
              <p className="hr-portal__hero-caption">Find the best talent faster</p>
            </div>
          )}
        </header>

        {error && (
          <div className="hr-portal__error">
            <span aria-hidden="true">!</span>
            {error}
          </div>
        )}

        {notice && !error && (
          <div className="hr-portal__notice">
            {notice}
          </div>
        )}

        {activeTab !== "analyze" && (
          <div className="hr-portal__stats">
            <div className="hr-portal__stat">
              <span className="hr-portal__stat-icon hr-portal__stat-icon--purple"><NavIcon name="grid" /></span>
              <div>
                <div className="hr-portal__stat-label">Open roles</div>
                <div className="hr-portal__stat-value">{dashboard?.applications?.total ?? "--"}</div>
              </div>
            </div>
            <div className="hr-portal__stat">
              <span className="hr-portal__stat-icon hr-portal__stat-icon--green"><NavIcon name="bars" /></span>
              <div>
                <div className="hr-portal__stat-label">Candidates ranked</div>
                <div className="hr-portal__stat-value">
                  {rankedCandidates.length > 0 ? rankedCandidates.length : dashboard?.applications?.shortlisted ?? "--"}
                </div>
              </div>
            </div>
            <div className="hr-portal__stat">
              <span className="hr-portal__stat-icon hr-portal__stat-icon--amber"><NavIcon name="bars" /></span>
              <div>
                <div className="hr-portal__stat-label">Avg match score</div>
                <div className="hr-portal__stat-value">{analytics?.avg_ats ?? "--"}%</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "analyze" && (
          <div className="hr-portal__analyze-grid">
            <div className="hr-portal__analyze-col">
              <div className="hr-portal__card">
                <div className="hr-portal__step-header">
                  <span className="hr-portal__step-badge">1</span>
                  <div className="hr-portal__step-headings">
                    <p className="hr-portal__step-title">Job requisition</p>
                    <p className="hr-portal__step-sub">Create a new opening, or run this against one already being tracked.</p>
                  </div>
                  <select
                    className="hr-portal__select"
                    value={requisitionMode}
                    onChange={(e) => {
                      const mode = e.target.value;
                      setRequisitionMode(mode);
                      if (mode === "new") {
                        setJobDescription("");
                      } else {
                        const req = requisitions.find((r) => r.id === selectedRequisitionId);
                        setJobDescription(req ? req.job_description : "");
                      }
                    }}
                  >
                    <option value="new">New requisition</option>
                    <option value="existing">Existing requisition</option>
                  </select>
                </div>

                {requisitionMode === "new" ? (
                  <div className="hr-portal__field">
                    <label htmlFor="req-title-input">Role title</label>
                    <input
                      id="req-title-input"
                      className="hr-portal__text-input"
                      placeholder="e.g. AI Engineer"
                      value={newRequisitionTitle}
                      onChange={(e) => setNewRequisitionTitle(e.target.value)}
                    />
                  </div>
                ) : (
                  <div className="hr-portal__field">
                    <label htmlFor="req-select">Select requisition</label>
                    <select
                      id="req-select"
                      className="hr-portal__select hr-portal__select--full"
                      value={selectedRequisitionId}
                      onChange={(e) => {
                        const id = e.target.value;
                        setSelectedRequisitionId(id);
                        const req = requisitions.find((r) => r.id === id);
                        setJobDescription(req ? req.job_description : "");
                      }}
                    >
                      <option value="">Choose a requisition&hellip;</option>
                      {requisitions.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.title} — opened {new Date(r.created_at).toLocaleDateString()}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              <div className="hr-portal__card">
                <div className="hr-portal__step-header">
                  <span className="hr-portal__step-badge">2</span>
                  <div className="hr-portal__step-headings">
                    <p className="hr-portal__step-title">Job description</p>
                    <p className="hr-portal__step-sub">
                      {requisitionMode === "existing"
                        ? "Loaded from the selected requisition."
                        : "Paste the job description for the role you want to analyze."}
                    </p>
                  </div>
                </div>

                <div className="hr-portal__field">
                  <label htmlFor="jd-input">Job description text</label>
                  <textarea
                    id="jd-input"
                    placeholder={SAMPLE_JD}
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    readOnly={requisitionMode === "existing"}
                  />
                </div>
              </div>

              <div className="hr-portal__card">
                <div className="hr-portal__step-header">
                  <span className="hr-portal__step-badge">3</span>
                  <div className="hr-portal__step-headings">
                    <p className="hr-portal__step-title">Resume source</p>
                    <p className="hr-portal__step-sub">Select where the resumes are stored.</p>
                  </div>
                  <select
                    className="hr-portal__select"
                    value={resumeSource}
                    onChange={(e) => setResumeSource(e.target.value)}
                  >
                    <option value="local">Local folder</option>
                    <option value="azure">Azure Blob Storage</option>
                  </select>
                </div>

                {resumeSource === "local" ? (
                  <div className="hr-portal__source-panel">
                    <label className="hr-portal__file-btn" htmlFor="resume-folder-input">
                      <NavIcon name="folder" />
                      Choose folder
                    </label>
                    <input
                      id="resume-folder-input"
                      type="file"
                      webkitdirectory=""
                      directory=""
                      multiple
                      onChange={handleLocalFilesChange}
                      hidden
                    />
                    <label className="hr-portal__file-btn hr-portal__file-btn--ghost" htmlFor="resume-files-input">
                      <NavIcon name="attach" />
                      Or add files
                    </label>
                    <input
                      id="resume-files-input"
                      type="file"
                      multiple
                      accept=".pdf,.docx,.txt,.md"
                      onChange={handleLocalFilesChange}
                      hidden
                    />

                    {localFiles.length === 0 ? (
                      <div className="hr-portal__source-hint">
                        <p className="hr-portal__muted">No resumes selected yet.</p>
                        <p className="hr-portal__muted hr-portal__source-hint-sub">Supported formats: PDF, DOCX, TXT</p>
                      </div>
                    ) : (
                      <button type="button" className="hr-portal__clear-link" onClick={() => setLocalFiles([])}>
                        Clear all ({localFiles.length})
                      </button>
                    )}

                    {localFiles.length > 0 && (
                      <ul className="hr-portal__file-list">
                        {localFiles.map((file, i) => (
                          <li key={`${file.name}-${i}`} className="hr-portal__file-row">
                            <span className="hr-portal__file-row-name">{file.webkitRelativePath || file.name}</span>
                            <span className="hr-portal__muted">{formatBytes(file.size)}</span>
                            <button type="button" className="hr-portal__icon-btn" onClick={() => removeLocalFile(i)} aria-label={`Remove ${file.name}`}>
                              <NavIcon name="close" />
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ) : (
                  <div className="hr-portal__source-panel">
                    <button
                      type="button"
                      className="hr-portal__btn hr-portal__btn--ghost"
                      onClick={handleLoadAzureResumes}
                      disabled={azureLoading}
                    >
                      <NavIcon name="cloud" />
                      {azureLoading ? "Loading..." : azureLoaded ? "Refresh resumes" : "Connect to Azure Blob Storage"}
                    </button>

                    {azureLoaded && azureResumes.length > 0 && (
                      <button type="button" className="hr-portal__clear-link" onClick={toggleAllAzureResumes}>
                        {allAzureSelected ? "Deselect all" : "Select all"} ({selectedAzureIds.size}/{azureResumes.length})
                      </button>
                    )}

                    {azureLoaded && azureResumes.length === 0 && (
                      <p className="hr-portal__muted hr-portal__empty">No resumes found in Azure Blob Storage yet.</p>
                    )}

                    {azureResumes.length > 0 && (
                      <ul className="hr-portal__file-list">
                        {azureResumes.map((record) => (
                          <li key={record.id} className="hr-portal__file-row">
                            <label className="hr-portal__checkbox-row">
                              <input
                                type="checkbox"
                                checked={selectedAzureIds.has(record.id)}
                                onChange={() => toggleAzureResume(record.id)}
                              />
                              <span className="hr-portal__file-row-name">{record.filename}</span>
                            </label>
                            <span className="hr-portal__muted">{record.user_id}</span>
                            <span className="hr-portal__muted">{formatBytes(record.size)}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>

              <button
                type="button"
                className="hr-portal__btn hr-portal__btn--primary hr-portal__run-btn"
                onClick={handleRunAnalysis}
                disabled={!canRunAnalysis}
                style={{
                  background: canRunAnalysis ? "#0b3d91" : "#93a5c9",
                  color: "#fff",
                  opacity: 1,
                }}
              >
                <NavIcon name="bars" />
                {loading === "analyze" ? "Analyzing..." : "Run Analysis"}
                <NavIcon name="arrow-right" />
              </button>

              {loading === "analyze" && analysisProgress && (
                <div className="hr-portal__progress">
                  <div className="hr-portal__progress-bar">
                    <span
                      className="hr-portal__progress-fill"
                      style={{ width: `${Math.round((analysisProgress.done / analysisProgress.total) * 100)}%` }}
                    />
                  </div>
                  <span className="hr-portal__muted">
                    Reading resume {analysisProgress.done} of {analysisProgress.total}&hellip;
                  </span>
                </div>
              )}

              {failedFiles.length > 0 && (
                <p className="hr-portal__badge hr-portal__badge--warn hr-portal__failed-note">
                  Skipped {failedFiles.length} file{failedFiles.length > 1 ? "s" : ""} that could not be read: {failedFiles.join(", ")}
                </p>
              )}
            </div>

            <div className="hr-portal__analyze-col">
              <div className="hr-portal__card">
                <div className="hr-portal__card-header">
                  <p className="hr-portal__card-title">
                    <span className="hr-portal__card-icon"><NavIcon name="bars" /></span>
                    Results
                  </p>
                  <button
                    type="button"
                    className="hr-portal__btn hr-portal__btn--ghost hr-portal__export-btn"
                    onClick={handleExportResults}
                    disabled={rankedCandidates.length === 0}
                  >
                    <NavIcon name="download" />
                    Export
                    <NavIcon name="chevron-down" />
                  </button>
                </div>

                {rankedCandidates.length === 0 && !loading ? (
                  <>
                    <div className="hr-portal__results-empty">
                      <span className="hr-portal__results-empty-icon"><NavIcon name="bars" /></span>
                      <h3>Ready to find your best candidates?</h3>
                      <p>Upload a job description and select a resume source, then run an analysis to see ranked candidates here.</p>
                    </div>

                    <div className="hr-portal__feature-grid">
                      <div className="hr-portal__feature">
                        <span className="hr-portal__feature-icon hr-portal__stat-icon--purple"><NavIcon name="users" /></span>
                        <h4>AI-powered matching</h4>
                        <p>Get accurate, skill-based candidate rankings</p>
                      </div>
                      <div className="hr-portal__feature">
                        <span className="hr-portal__feature-icon hr-portal__stat-icon--green"><NavIcon name="bolt" /></span>
                        <h4>Save time</h4>
                        <p>Analyze multiple resumes in seconds</p>
                      </div>
                      <div className="hr-portal__feature">
                        <span className="hr-portal__feature-icon hr-portal__stat-icon--amber"><NavIcon name="shield" /></span>
                        <h4>Data privacy</h4>
                        <p>Your files are secure and confidential</p>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="hr-portal__ranked-list">
                    {rankedCandidates.map((c, i) => (
                      <div key={i} className="hr-portal__rank-row">
                        <span className={"hr-portal__rank-badge" + (i < 3 ? ` hr-portal__rank-badge--${i}` : "")}>{i + 1}</span>
                        <div className="hr-portal__candidate">
                          <span className="hr-portal__avatar">{initialsOf(c.name)}</span>
                          <div>
                            <div>{c.name}</div>
                            {c.stage && (
                              <span
                                className={
                                  "hr-portal__badge hr-portal__badge--small " +
                                  (c.stage === "Rejected"
                                    ? "hr-portal__badge--bad"
                                    : c.stage === "Shortlisted"
                                    ? "hr-portal__badge--good"
                                    : "hr-portal__badge--neutral")
                                }
                              >
                                {c.stage}
                              </span>
                            )}
                            {c.candidate_source === "local" && (
                              <CandidateEmailEditor
                                value={c.candidate_email}
                                onSave={(email) =>
                                  handleUpdateCandidateEmail(activeRequisitionId, c.pipeline_id, email, (updated) =>
                                    setRankedCandidates((prev) =>
                                      prev.map((x) =>
                                        x.pipeline_id === c.pipeline_id ? { ...x, candidate_email: updated.candidate_email } : x
                                      )
                                    )
                                  )
                                }
                              />
                            )}
                          </div>
                        </div>
                        <div className="hr-portal__score-bar">
                          <span className="hr-portal__score-bar-fill" style={{ width: `${c.score}%` }} />
                        </div>
                        <span className="hr-portal__score-value">{c.score}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "interviews" && (
          <div className="hr-portal__card">
            <div className="hr-portal__card-header">
              <p className="hr-portal__card-title">
                <span className="hr-portal__card-icon"><NavIcon name="calendar" /></span>
                Interview scheduling
              </p>
              <select
                className="hr-portal__select"
                value={interviewsRequisitionId}
                onChange={(e) => {
                  const id = e.target.value;
                  setInterviewsRequisitionId(id);
                  loadPipeline(id);
                }}
              >
                <option value="">Choose a requisition&hellip;</option>
                {requisitions.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title} — opened {new Date(r.created_at).toLocaleDateString()}
                  </option>
                ))}
              </select>
            </div>
            {!interviewsRequisitionId ? (
              <p className="hr-portal__muted hr-portal__empty">Select a requisition to see its pipeline.</p>
            ) : pipelineLoading ? (
              <p className="hr-portal__muted hr-portal__empty">Loading&hellip;</p>
            ) : pipelineRecords.length === 0 ? (
              <p className="hr-portal__muted hr-portal__empty">
                No candidates in this requisition's pipeline yet — run an analysis for it first.
              </p>
            ) : (
              <div className="hr-portal__interview-list">
                {pipelineRecords.map((r) => (
                  <div key={r.id} className="hr-portal__interview-row">
                    <div className="hr-portal__candidate">
                      <span className="hr-portal__avatar">{initialsOf(r.candidate_name)}</span>
                      <div>
                        <div>{r.candidate_name}</div>
                        <span className="hr-portal__muted">Match score {r.score}%</span>
                        {r.candidate_source === "local" && (
                          <div>
                            <CandidateEmailEditor
                              value={r.candidate_email}
                              onSave={(email) =>
                                handleUpdateCandidateEmail(interviewsRequisitionId, r.id, email, (updated) =>
                                  setPipelineRecords((prev) => prev.map((x) => (x.id === r.id ? updated : x)))
                                )
                              }
                            />
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="hr-portal__interview-status">
                      <span
                        className={
                          "hr-portal__badge " +
                          (r.stage === "Rejected"
                            ? "hr-portal__badge--bad"
                            : r.stage === "Accepted" || r.stage === "Offer"
                            ? "hr-portal__badge--good"
                            : "hr-portal__badge--neutral")
                        }
                      >
                        {r.stage}
                      </span>
                      <select
                        className="hr-portal__select"
                        value={moveTarget[r.id] || ""}
                        onChange={(e) => setMoveTarget((prev) => ({ ...prev, [r.id]: e.target.value }))}
                      >
                        <option value="">Move to&hellip;</option>
                        {STAGES.filter((s) => s !== r.stage).map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        className="hr-portal__btn hr-portal__btn--ghost"
                        onClick={() => handleMoveStage(r)}
                        disabled={!moveTarget[r.id]}
                      >
                        Move
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "dashboard" && (
          <>
            <div className="hr-portal__card">
              <div className="hr-portal__card-header">
                <p className="hr-portal__card-title">
                  <span className="hr-portal__card-icon"><NavIcon name="grid" /></span>
                  Dashboard
                </p>
                <div className="hr-portal__dashboard-controls">
                  <select
                    className="hr-portal__select"
                    value={dashboardRequisitionId}
                    onChange={(e) => {
                      const id = e.target.value;
                      setDashboardRequisitionId(id);
                      handleLoadDashboard(id);
                      loadPendingEmails(id);
                    }}
                  >
                    <option value="">All requisitions</option>
                    {requisitions.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.title} — opened {new Date(r.created_at).toLocaleDateString()}
                      </option>
                    ))}
                  </select>
                  <button
                    className="hr-portal__btn hr-portal__btn--primary"
                    onClick={() => {
                      handleLoadDashboard();
                      loadPendingEmails();
                    }}
                    disabled={loading === "dashboard"}
                  >
                    {loading === "dashboard" ? "Loading..." : "Refresh"}
                  </button>
                </div>
              </div>
              {dashboard ? (
                <div className="hr-portal__section">
                  <div className="hr-portal__stats hr-portal__stats--compact">
                    <div className="hr-portal__stat">
                      <div className="hr-portal__stat-label">Applications</div>
                      <div className="hr-portal__stat-value">{dashboard.applications?.total ?? "--"}</div>
                    </div>
                    <div className="hr-portal__stat">
                      <div className="hr-portal__stat-label">Shortlisted</div>
                      <div className="hr-portal__stat-value">{dashboard.applications?.shortlisted ?? "--"}</div>
                    </div>
                    <div className="hr-portal__stat">
                      <div className="hr-portal__stat-label">Shortlist rate</div>
                      <div className="hr-portal__stat-value">{dashboard.shortlist_rate ?? "--"}%</div>
                    </div>
                    <div className="hr-portal__stat">
                      <div className="hr-portal__stat-label">Avg ATS</div>
                      <div className="hr-portal__stat-value">{analytics?.avg_ats ?? "--"}%</div>
                    </div>
                    <div className="hr-portal__stat">
                      <div className="hr-portal__stat-label">Offers rolled out</div>
                      <div className="hr-portal__stat-value">{dashboard.offers ?? "--"}</div>
                    </div>
                  </div>

                  {dashboard.funnel && dashboard.funnel.length > 0 && (
                    <div className="hr-portal__funnel">
                      <h3>Pipeline funnel</h3>
                      {(() => {
                        const max = Math.max(1, ...dashboard.funnel.map((f) => f.value));
                        return dashboard.funnel.map((f) => (
                          <div key={f.label} className="hr-portal__funnel-row">
                            <span className="hr-portal__funnel-label">{f.label}</span>
                            <div className="hr-portal__funnel-track">
                              <div className="hr-portal__funnel-bar" style={{ width: `${(f.value / max) * 100}%` }} />
                            </div>
                            <span className="hr-portal__funnel-value">{f.value}</span>
                          </div>
                        ));
                      })()}
                    </div>
                  )}

                  <div className="hr-portal__dash-grid">
                    <div>
                      <h3>Top skills</h3>
                      {pillList((dashboard.skills_distribution || []).map((item) => `${item.label} ${item.value}`))}
                    </div>
                    <div>
                      <h3>Pipeline</h3>
                      {pillList((analytics?.pipeline || []).map((item) => `${item.label} ${item.value}`))}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="hr-portal__muted hr-portal__empty">Load the dashboard to see analytics.</p>
              )}
            </div>

            <div className="hr-portal__card">
              <div className="hr-portal__card-header">
                <p className="hr-portal__card-title">
                  <span className="hr-portal__card-icon"><NavIcon name="bolt" /></span>
                  Pending approvals
                </p>
                <button
                  type="button"
                  className="hr-portal__btn hr-portal__btn--primary"
                  onClick={handleSendAllEmails}
                  disabled={pendingEmails.length === 0}
                >
                  Send all ({pendingEmails.length})
                </button>
              </div>
              {emailsLoading ? (
                <p className="hr-portal__muted hr-portal__empty">Loading&hellip;</p>
              ) : pendingEmails.length === 0 ? (
                <p className="hr-portal__muted hr-portal__empty">No emails waiting for approval.</p>
              ) : (
                <ul className="hr-portal__email-list">
                  {pendingEmails.map((draft) => (
                    <li key={draft.id} className="hr-portal__email-row">
                      <div className="hr-portal__email-row-main">
                        <span
                          className={
                            "hr-portal__badge " +
                            (draft.template_type === "rejection"
                              ? "hr-portal__badge--bad"
                              : draft.template_type === "offer"
                              ? "hr-portal__badge--good"
                              : "hr-portal__badge--neutral")
                          }
                        >
                          {draft.template_type.replace("_", " ")}
                        </span>
                        <div>
                          <div className="hr-portal__email-subject">{draft.subject}</div>
                          <div className="hr-portal__muted">{draft.candidate_email || "No email on file"}</div>
                        </div>
                      </div>
                      <button
                        type="button"
                        className="hr-portal__btn hr-portal__btn--ghost"
                        onClick={() => handleSendEmail(draft)}
                        disabled={!draft.candidate_email}
                      >
                        Send
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
