# HireFlow AI

An AI-assisted hiring platform with two portals: a **Student portal** for resume analysis and career guidance, and an **HR portal** for job-description parsing, candidate screening, and applicant ranking.

- **Frontend:** React (Vite), Firebase Authentication
- **Backend:** FastAPI (Python 3.11+)
- **AI:** Google Gemini (`google-genai`) for resume/JD extraction and generation
- **Storage:** Firebase Firestore (resume/account records) and Firebase Storage (resume files)

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Overview](#api-overview)
- [Testing](#testing)
- [Deployment](#deployment)

## Features

**Student Portal**
- Resume upload, storage, and management (list, view, delete)
- AI-powered resume scoring and analysis
- Resume improvement suggestions and version history
- AI-generated cover letters
- Interview preparation questions
- Career advisor Q&A

**HR Portal**
- Job description parsing and structured extraction
- Resume screening against a job description
- Candidate ranking across a batch of resumes
- Skills assessment generation and evaluation
- Interview scheduling
- Recruiter chat assistant
- Dashboard and analytics summaries

## Architecture

```
frontend (React/Vite)  --HTTP-->  backend (FastAPI)  -->  Google Gemini (AI extraction/generation)
                                                      -->  Firebase Firestore (accounts, resume metadata)
                                                      -->  Firebase Storage (resume files)
```

The frontend also talks to Firebase directly for authentication state; the backend exposes its own lightweight account lookup/login/upsert endpoints backed by Firestore.

## Folder Structure

```text
HireFlow AI
├── frontend
│   ├── src
│   │   ├── App.jsx
│   │   ├── firebase.js
│   │   ├── login/
│   │   ├── student-portal/
│   │   └── hr-portal/
│   └── vite.config.js
├── backend
│   ├── main.py
│   ├── schemas.py
│   ├── requirements.txt
│   ├── routers/          # thin FastAPI route handlers
│   ├── services/         # resume, HR, AI, storage, and auth logic
│   └── tests/
├── Dockerfile
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Gemini API key
- A Firebase project with Firestore and Storage enabled (for data/resume persistence and frontend authentication)

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The API is now available at `http://127.0.0.1:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:3000` (CORS is preconfigured on the backend for this origin).

## Environment Variables

Set these for the backend (e.g. in a `.env` file at the project or `backend/` root):

| Variable | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Google Gemini API key used for resume/JD extraction and generation |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase service account credentials, as a raw JSON string (use this or `FIREBASE_SERVICE_ACCOUNT_PATH`) |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | Path to a Firebase service account JSON key file (falls back to `GOOGLE_APPLICATION_CREDENTIALS` if unset) |
| `FIREBASE_STORAGE_BUCKET` | Firebase Storage bucket name used for resume files |
| `FIRESTORE_ACCOUNTS_COLLECTION` | Firestore collection for accounts (default `accounts`) |
| `FIRESTORE_RESUME_COLLECTION` | Firestore collection for resume metadata (default `resumes`) |
| `FIRESTORE_EMAIL_COLLECTION` | Firestore collection for email drafts (default `email_drafts`) |
| `FIRESTORE_REQUISITION_COLLECTION` | Firestore collection for job requisitions (default `requisitions`) |
| `FIRESTORE_PIPELINE_COLLECTION` | Firestore collection for candidate pipeline records (default `pipeline_records`) |

Without Firebase credentials configured, the backend falls back to in-memory storage (data does not persist across restarts) — useful for local development.

Firebase configuration for the frontend lives in `frontend/src/firebase.js`.

## API Overview

All routes are prefixed with `/api`. See `backend/routers/` for full request/response models.

**Health**
- `GET /` and `GET /api/health`

**Auth**
- `POST /api/auth/lookup`
- `POST /api/auth/login`
- `POST /api/auth/upsert`

**Resume (Student portal)**
- `POST /api/resume/extract-text` — extract text from an uploaded resume file
- `GET /api/resume/list` — list a user's stored resumes
- `GET /api/resume/{resume_id}/text` — fetch stored resume text
- `DELETE /api/resume/{resume_id}` — delete a stored resume
- `POST /api/resume/analyze` — score and analyze a resume
- `POST /api/resume/improve` — suggest resume improvements
- `POST /api/resume/cover-letter` — generate a cover letter
- `POST /api/resume/interview-prep` — generate interview prep questions
- `POST /api/career-advisor` — career guidance Q&A
- `GET /api/resume/versions` — resume version history

**HR**
- `POST /api/hr/parse-jd` — parse a job description
- `POST /api/hr/screen` — screen a resume against a job description
- `POST /api/hr/rank` — rank a batch of candidates
- `POST /api/hr/assessment` — generate a skills assessment
- `POST /api/hr/evaluate-assessment` — evaluate assessment responses
- `POST /api/hr/schedule-interview` — schedule an interview
- `POST /api/hr/chat` — recruiter chat assistant
- `GET /api/hr/dashboard` — HR dashboard summary
- `GET /api/analytics` — analytics summary

## Testing

Backend unit tests (using `unittest`, run via `pytest`):

```bash
source .venv/bin/activate
pytest backend/tests
```

## Deployment

- `Dockerfile` builds a container that installs backend dependencies and serves the FastAPI app with `uvicorn` on port `8000`.
