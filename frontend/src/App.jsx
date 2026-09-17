import { useEffect, useState } from "react";

import HRPortal from "./hr-portal/HRPortal.jsx";
import LoginScreen from "./login/LoginScreen.jsx";
import StudentPortal from "./student-portal/StudentPortal.jsx";

const STUDENT_IMAGE_SRC = import.meta.env.VITE_STUDENT_LOGO_SRC || "/images/student.png";
const HR_IMAGE_SRC = "/images/HR.png";

const navItems = [
  { label: "Home", href: "#home", active: true },
  { label: "Features", href: "#features" },
  { label: "How it Works", href: "#how-it-works" },
  { label: "Pricing", href: "#pricing" },
  { label: "Resources", href: "#resources", caret: true },
];

const studentFeatures = [
  {
    title: "ATS Score",
    copy: "Analyze your resume and get an ATS score.",
    tone: "violet",
    icon: "circle",
  },
  {
    title: "Improve Suggestions",
    copy: "Get AI-powered feedback to improve your resume.",
    tone: "violet",
    icon: "spark",
  },
  {
    title: "Cover Letter",
    copy: "Generate customized cover letters instantly.",
    tone: "violet",
    icon: "document",
  },
  {
    title: "Job Match",
    copy: "Find jobs that match your skills.",
    tone: "violet",
    icon: "briefcase",
  },
];

const hrFeatures = [
  {
    title: "Resume Processing",
    copy: "Bulk upload and AI screens all resumes.",
    tone: "blue",
    icon: "upload",
  },
  {
    title: "Shortlist & Filter",
    copy: "Accept / Reject and get shortlisted candidates.",
    tone: "blue",
    icon: "users",
  },
  {
    title: "Auto Reach Out",
    copy: "Send interview requests automatically.",
    tone: "blue",
    icon: "mail",
  },
  {
    title: "LinkedIn Check",
    copy: "Verify candidate eligibility and profile match.",
    tone: "blue",
    icon: "linkedin",
  },
];

const stats = [
  { value: "10K+", label: "Active Users", tone: "violet", icon: "users" },
  { value: "2K+", label: "Companies", tone: "green", icon: "building" },
  { value: "1M+", label: "Resumes Processed", tone: "amber", icon: "document" },
  { value: "85%", label: "Match Accuracy", tone: "blue", icon: "check" },
];

const steps = [
  {
    number: "1",
    title: "Upload",
    copy: "Upload your resume or job description",
    icon: "upload",
  },
  {
    number: "2",
    title: "AI Analysis",
    copy: "Our AI analyzes and processes the content",
    icon: "brain",
  },
  {
    number: "3",
    title: "Smart Actions",
    copy: "Get suggestions (student) or shortlisted candidates (HR)",
    icon: "spark",
  },
  {
    number: "4",
    title: "Connect & Grow",
    copy: "Connect with the right opportunities and grow your career or team",
    icon: "handshake",
  },
];

function scrollToId(id) {
  const node = document.getElementById(id);
  if (node) {
    node.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function LogoMark() {
  return (
    <div className="logo-mark" aria-hidden="true">
      <span />
      <span />
      <span />
    </div>
  );
}

function Icon({ name }) {
  switch (name) {
    case "circle":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <circle cx="24" cy="24" r="16" fill="none" stroke="currentColor" strokeWidth="6" />
          <path d="M24 8a16 16 0 0 1 16 16" fill="none" stroke="currentColor" strokeWidth="6" strokeLinecap="round" />
        </svg>
      );
    case "spark":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <path d="M24 6l3.7 10.5L38 20l-10.3 3.5L24 34l-3.7-10.5L10 20l10.3-3.5L24 6z" fill="currentColor" />
          <path d="M36 30l1.5 4.5L42 36l-4.5 1.5L36 42l-1.5-4.5L30 36l4.5-1.5L36 30z" fill="currentColor" opacity="0.75" />
        </svg>
      );
    case "document":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <path d="M14 8h14l8 8v24H14z" fill="none" stroke="currentColor" strokeWidth="3.5" />
          <path d="M28 8v8h8" fill="none" stroke="currentColor" strokeWidth="3.5" />
          <path d="M18 22h12M18 28h12M18 34h8" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" />
        </svg>
      );
    case "briefcase":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <rect x="10" y="16" width="28" height="20" rx="4" fill="none" stroke="currentColor" strokeWidth="3.5" />
          <path d="M18 16v-3a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v3" fill="none" stroke="currentColor" strokeWidth="3.5" />
          <path d="M10 24h28" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" />
        </svg>
      );
    case "upload":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <path d="M12 31a8 8 0 0 1 3-15 11 11 0 0 1 21 4 7 7 0 0 1 0 11" fill="none" stroke="currentColor" strokeWidth="3.5" />
          <path d="M24 34V16M18 22l6-6 6 6" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "users":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <circle cx="18" cy="18" r="6" fill="currentColor" />
          <circle cx="31" cy="20" r="5" fill="currentColor" opacity="0.75" />
          <path d="M10 36c1.6-5.8 6-9 12-9s10.4 3.2 12 9" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" />
        </svg>
      );
    case "mail":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <rect x="10" y="14" width="28" height="20" rx="4" fill="none" stroke="currentColor" strokeWidth="3.5" />
          <path d="M12 18l12 9 12-9" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "linkedin":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <rect x="10" y="10" width="28" height="28" rx="6" fill="currentColor" />
          <path d="M18 20v14M18 16v.2M24 20v14M24 24.5c1.3-2.5 3.7-4 6.3-4 4.4 0 6.7 2.8 6.7 7.3V34" fill="none" stroke="#fff" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "building":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <path d="M12 36V14l10-4 14 4v22" fill="none" stroke="currentColor" strokeWidth="3.5" />
          <path d="M18 36V24h6v12M26 36V20h6v16" fill="none" stroke="currentColor" strokeWidth="3.5" />
        </svg>
      );
    case "check":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <circle cx="24" cy="24" r="16" fill="none" stroke="currentColor" strokeWidth="3.5" />
          <path d="M17 24l5 5 9-11" fill="none" stroke="currentColor" strokeWidth="3.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "brain":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <path d="M18 14c-4 0-7 3-7 7 0 2.2 1 4.2 2.6 5.5C12.6 28.6 12 30.2 12 32c0 3.3 2.7 6 6 6h12c3.3 0 6-2.7 6-6 0-1.8-.6-3.4-1.6-4.5C36 26.2 37 24.2 37 22c0-4-3-7-7-7-1.7 0-3.2.6-4.5 1.6C24.2 15.6 21.6 14 18 14z" fill="none" stroke="currentColor" strokeWidth="3.4" strokeLinejoin="round" />
          <path d="M24 12v24M18 20c2 0 3.6 1.3 4 3.2M30 20c-2 0-3.6 1.3-4 3.2" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" />
        </svg>
      );
    case "handshake":
      return (
        <svg viewBox="0 0 48 48" aria-hidden="true">
          <path d="M8 27l8-8 7 7 5-5 7 7-7 7a6 6 0 0 1-8 0l-3-3" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M20 31l4 4M28 19l4 4" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" />
        </svg>
      );
    default:
      return null;
  }
}

function FeatureCard({ label, title, copy, features, tone, cta, illustration }) {
  return (
    <article className="feature-card">
      <div className="feature-card-head">
        <div className={`card-tag ${tone}`}>{label}</div>
        <div className="feature-copy">
          <h2>{title}</h2>
          <p>{copy}</p>
        </div>
        <div className="feature-illustration">{illustration}</div>
      </div>
      <div className="feature-grid">
        {features.map((feature) => (
          <div key={feature.title} className="mini-card">
            <div className={`mini-icon ${feature.tone}`}>
              <Icon name={feature.icon} />
            </div>
            <h3>{feature.title}</h3>
            <p>{feature.copy}</p>
          </div>
        ))}
      </div>
      {cta ? (
        <button className={`cta-button ${tone}`} type="button" onClick={cta.onClick}>
          {cta.label}
          <span aria-hidden="true">→</span>
        </button>
      ) : null}
    </article>
  );
}

function MetricCard({ value, label, tone, icon }) {
  return (
    <div className="metric-card">
      <div className={`metric-icon ${tone}`}>
        <Icon name={icon} />
      </div>
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

function StepCard({ number, title, copy, icon, isLast }) {
  return (
    <div className={`step-card ${isLast ? "last" : ""}`}>
      <div className="step-badge">{number}</div>
      <div className="step-icon">
        <Icon name={icon} />
      </div>
      <div>
        <h3>{title}</h3>
        <p>{copy}</p>
      </div>
    </div>
  );
}

function HomePage({ onLogin }) {
  return (
    <main className="home-page" id="home">
      <header className="topbar">
        <a className="brand" href="#home" aria-label="HireFlow AI home">
          <LogoMark />
          <span>HireFlow AI</span>
        </a>

        <nav className="nav">
          {navItems.map((item) => (
            <a
              key={item.label}
              className={`nav-link ${item.active ? "active" : ""}`}
              href={item.href}
              onClick={(event) => {
                event.preventDefault();
                scrollToId(item.href.slice(1));
              }}
            >
              {item.label}
              {item.caret ? <span className="caret">⌄</span> : null}
            </a>
          ))}
        </nav>

        <div className="topbar-actions">
          <button className="ghost-button" type="button" onClick={onLogin}>
            Sign In
          </button>
        </div>
      </header>

      <section className="hero" id="hero">
        <div className="hero-ribbon">
          <span className="ribbon-icon">✦</span>
          <span>AI-Powered Hiring &amp; Career Assistant</span>
        </div>

        <h1>
          Smarter <span className="gradient-text blue">Hiring</span>. Better{" "}
          <span className="gradient-text purple">Careers</span>.
        </h1>

        <p className="hero-copy">
          HireFlow AI connects talent with opportunities.
          <br />
          For students to grow. For HR to hire the best.
        </p>
      </section>

      <section className="feature-panels" aria-label="Audience features" id="features">
        <FeatureCard
          label="For Students"
          title="Kickstart Your Career"
          copy="Upload, analyze and improve your application to stand out and get hired."
          tone="violet"
          features={studentFeatures}
          illustration={
            <img
              className="feature-card-image feature-card-image--student"
              src={STUDENT_IMAGE_SRC}
              alt="Student"
            />
          }
        />

        <FeatureCard
          label="For HR / Recruiters"
          title="Hire Top Talent Faster"
          copy="Let AI screen, analyze and shortlist the best candidates for you."
          tone="blue"
          features={hrFeatures}
          illustration={
            <img
              className="feature-card-image feature-card-image--hr"
              src={HR_IMAGE_SRC}
              alt="HR recruiter"
            />
          }
        />
      </section>

      <section className="stats-strip" id="pricing" aria-label="Platform metrics">
        {stats.map((stat) => (
          <MetricCard key={stat.label} {...stat} />
        ))}
      </section>

      <section className="works" id="how-it-works">
        <h2>How HireFlow AI Works</h2>
        <div className="steps">
          {steps.map((step, index) => (
            <StepCard key={step.number} {...step} isLast={index === steps.length - 1} />
          ))}
        </div>
      </section>

      <section className="footer-cta" id="resources">
        <div>
          <p className="eyebrow">Ready to start</p>
          <h2>One platform for students and recruiters.</h2>
        </div>
      </section>
    </main>
  );
}

function getInitialView() {
  if (typeof window === "undefined") {
    return "home";
  }

  return window.sessionStorage.getItem("hireflow-auth-view") || "home";
}

export default function App() {
  const [view, setView] = useState(getInitialView);

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem("hireflow-auth-view", view);
    }
  }, [view]);

  useEffect(() => {
    const handleRouteEvent = (event) => {
      const nextView = event.detail?.view;
      if (nextView === "student" || nextView === "hr" || nextView === "login" || nextView === "home") {
        setView(nextView);
      }
    };

    if (typeof window === "undefined") {
      return undefined;
    }

    window.addEventListener("hireflow-auth-route", handleRouteEvent);
    return () => window.removeEventListener("hireflow-auth-route", handleRouteEvent);
  }, []);

  const handleSelectStudent = () => {
    setView("student");
  };

  const handleSelectHr = () => {
    setView("hr");
  };

  if (view === "login") {
    return (
      <LoginScreen
        onBack={() => setView("home")}
        onSelectStudent={handleSelectStudent}
        onSelectHr={handleSelectHr}
        LogoMark={LogoMark}
      />
    );
  }

  if (view === "student") {
    return <StudentPortal onSignOut={() => setView("login")} />;
  }

  if (view === "hr") {
    return <HRPortal onBack={() => setView("login")} />;
  }

  return <HomePage onLogin={() => setView("login")} />;
}
