from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.schemas import (
    AssessmentInput,
    BulkEmailSendInput,
    CandidateBatchInput,
    CandidateEmailUpdateInput,
    ChatInput,
    EmailEditInput,
    InterviewAdvanceInput,
    JobDescriptionInput,
    RequisitionInput,
    RequisitionStatusInput,
    ResumeInput,
    StageUpdateInput,
)
from backend.services.ai_extraction import extract_jd_with_ai

from backend.services.dashboard import build_analytics, build_dashboard
from backend.services.email_service import send_email
from backend.services.email_store import email_draft_store
from backend.services.email_templates import (
    render_interview_invite_email,
    render_offer_email,
    render_rejection_email,
)
from backend.services.hr import auto_evaluation, fraud_detection, interview_slots, parse_jd, project_evaluation
from backend.services.pipeline import assign_initial_stage
from backend.services.requisition_store import pipeline_store, requisition_store
from backend.services.resume import ats_score
from backend.services.resume_store import resume_store
from backend.services.text_utils import detect_skills

router = APIRouter()


@router.post("/api/hr/parse-jd")
def api_parse_jd(payload: JobDescriptionInput) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        ai_result = extract_jd_with_ai(payload.job_description, api_key)
        if ai_result is not None:
            return ai_result
    return parse_jd(payload.job_description)


@router.post("/api/hr/screen")
def api_hr_screen(payload: ResumeInput) -> dict[str, Any]:
    analysis = ats_score(payload.resume_text, payload.job_description)
    project = project_evaluation(payload.resume_text)
    fraud = fraud_detection(payload.resume_text)
    return {
        "candidate": payload.candidate_name.strip() or "Candidate",
        "ats": f'{analysis["ats_score"]}%',
        "skill_match": f'{min(100, analysis["ats_score"] - 3)}%',
        "projects": project["tier"],
        "experience": "Relevant" if len(detect_skills(payload.resume_text)) >= 3 else "Limited",
        "education": "Good",
        "recommendation": "Strong Hire" if analysis["ats_score"] >= 85 else "Interview" if analysis["ats_score"] >= 70 else "Reject",
        "flags": fraud["flags"],
    }


@router.get("/api/hr/resumes")
def api_hr_resumes() -> dict[str, Any]:
    records = resume_store.list_all_resumes()
    return {
        "resumes": [
            {
                "id": record["id"],
                "user_id": record["user_id"],
                "filename": record["filename"],
                "uploaded_at": record.get("uploaded_at"),
                "size": record.get("size"),
            }
            for record in records
        ]
    }


def _score_candidate(candidate: dict[str, Any], job_description: str) -> dict[str, Any]:
    text = candidate.get("resume_text", "")
    name = candidate.get("name", "Candidate")
    # use_ai=True: falls back to the regex scorer automatically (see ats_score) if
    # GEMINI_API_KEY is missing or the AI call fails.
    analysis = ats_score(text, job_description, use_ai=True)
    project = project_evaluation(text)
    total = min(100, round(analysis["ats_score"] * 0.65 + project["score"] * 0.35))
    return {
        "name": name,
        "score": total,
        "ats": analysis["ats_score"],
        "skill_match": len(analysis["matched_skills"]),
        "matched_skills": analysis["matched_skills"],
        "projects": project["tier"],
        "scoring_method": analysis.get("scoring_method", "regex_fallback"),
        # Identity passthrough so requisition-scoped ranking can attach a real
        # candidate email for blob-sourced resumes (see resume_store: user_id
        # there is the candidate's account email). Local-file candidates have
        # no account, hence no email, until HR adds one manually.
        "candidate_source": candidate.get("candidate_source", "local"),
        "resume_id": candidate.get("resume_id", ""),
        "resume_user_id": candidate.get("resume_user_id", ""),
    }


def _persist_ranked_candidates(requisition_id: str, ranked: list[dict[str, Any]]) -> None:
    """Creates or refreshes a pipeline record per ranked candidate. Re-ranking
    a requisition updates a blob-sourced candidate's score in place (matched by
    resume_id) without resetting any stage progress HR has already made."""
    for item in ranked:
        candidate_source = item.get("candidate_source", "local")
        resume_id = item.get("resume_id", "")
        candidate_email = item.get("resume_user_id", "") if candidate_source == "blob" else ""

        existing = pipeline_store.find_by_resume(requisition_id, resume_id) if resume_id else None

        score_fields = {
            "candidate_name": item["name"],
            "candidate_source": candidate_source,
            "resume_id": resume_id,
            "resume_user_id": item.get("resume_user_id", ""),
            "score": item["score"],
            "ats": item["ats"],
            "skill_match": item["skill_match"],
            "matched_skills": item.get("matched_skills", []),
            "projects": item["projects"],
            "scoring_method": item["scoring_method"],
        }

        if existing:
            record = pipeline_store.replace_score(requisition_id, existing["id"], score_fields)
        else:
            stage, recommended_action = assign_initial_stage(item["score"])
            record = pipeline_store.create_records_bulk(
                requisition_id,
                [{**score_fields, "candidate_email": candidate_email, "stage": stage, "recommended_action": recommended_action}],
            )[0]

        item["pipeline_id"] = record["id"]
        item["stage"] = record["stage"]
        item["recommended_action"] = record.get("recommended_action", "")
        item["candidate_email"] = record.get("candidate_email", "")


@router.post("/api/hr/rank")
def api_rank_candidates(payload: CandidateBatchInput) -> dict[str, Any]:
    # Each candidate's AI call is a blocking network request, so score candidates
    # concurrently instead of one-by-one to keep total request latency reasonable.
    with ThreadPoolExecutor(max_workers=min(8, len(payload.candidates)) or 1) as pool:
        ranked = list(pool.map(lambda c: _score_candidate(c, payload.job_description), payload.candidates))
    ranked.sort(key=lambda item: item["score"], reverse=True)

    requisition_id = payload.requisition_id.strip()
    if not requisition_id:
        # No requisition given: pure ephemeral scoring, nothing persisted (today's behavior).
        return {"ranked": ranked}

    if requisition_store.get_requisition(requisition_id) is None:
        raise HTTPException(status_code=404, detail="Requisition not found")

    _persist_ranked_candidates(requisition_id, ranked)
    return {"requisition_id": requisition_id, "ranked": ranked}


@router.post("/api/hr/assessment")
def api_assessment(payload: AssessmentInput) -> dict[str, Any]:
    topic = payload.topic.strip().title()
    count = 20 if topic.lower() == "python" else 15 if topic.lower() == "react" else 10
    questions = [
        f"{topic} question {i + 1}: Explain a practical concept at {payload.skill_level} level."
        for i in range(count)
    ]
    return {"topic": topic, "count": count, "questions": questions}


@router.post("/api/hr/evaluate-assessment")
def api_evaluate_assessment(payload: AssessmentInput) -> dict[str, Any]:
    return auto_evaluation(payload.candidate_answers)


@router.post("/api/hr/chat")
def api_hr_chat(payload: ChatInput) -> dict[str, Any]:
    message = payload.message.lower()
    if "python" in message and "react" in message and "docker" in message:
        return {
            "answer": "Top candidates are those whose resumes show at least two of Python, React, and Docker, plus one production project and measurable impact.",
        }
    if "shortlist" in message:
        return {
            "answer": "Shortlisting is based on ATS score, skill match, project complexity, and whether the resume shows real delivery rather than keyword repetition.",
        }
    if "experience" in message:
        return {
            "answer": "Look for repeated ownership patterns, production context, and tools used to ship work, not just a total number of years.",
        }
    return {
        "answer": "Ask for candidate names, skills, or screening criteria and I can summarize the strongest matches.",
    }


# ---------------------------------------------------------------------------
# Requisitions
# ---------------------------------------------------------------------------


@router.post("/api/hr/requisitions")
def api_create_requisition(payload: RequisitionInput) -> dict[str, Any]:
    return requisition_store.create_requisition(payload.title, payload.job_description, payload.created_by)


@router.get("/api/hr/requisitions")
def api_list_requisitions() -> dict[str, Any]:
    return {"requisitions": requisition_store.list_requisitions()}


@router.get("/api/hr/requisitions/{requisition_id}")
def api_get_requisition(requisition_id: str) -> dict[str, Any]:
    requisition = requisition_store.get_requisition(requisition_id)
    if requisition is None:
        raise HTTPException(status_code=404, detail="Requisition not found")
    return requisition


@router.patch("/api/hr/requisitions/{requisition_id}/status")
def api_update_requisition_status(requisition_id: str, payload: RequisitionStatusInput) -> dict[str, Any]:
    requisition = requisition_store.update_status(requisition_id, payload.status)
    if requisition is None:
        raise HTTPException(status_code=404, detail="Requisition not found")
    return requisition


# ---------------------------------------------------------------------------
# Pipeline (per-requisition candidate stages)
# ---------------------------------------------------------------------------


def _draft_email_for_event(
    requisition: dict[str, Any],
    record: dict[str, Any],
    event: str,
    round_label: str = "",
    slots: list[str] | None = None,
) -> dict[str, Any] | None:
    """Only ever called from an explicit HR action (a stage change or an
    interview scheduling call) — never from ranking. This is what makes
    sending approval-gated: a draft is queued here, but api_send_email_draft
    is the only path that actually talks to Resend."""
    role_title = requisition.get("title", "")
    candidate_name = record.get("candidate_name", "Candidate")
    candidate_email = record.get("candidate_email", "")

    if event == "reject":
        template_type = "rejection"
        subject, html, text = render_rejection_email(candidate_name, role_title)
    elif event == "offer":
        template_type = "offer"
        subject, html, text = render_offer_email(candidate_name, role_title)
    elif event == "interview_invite":
        template_type = "interview_invite"
        subject, html, text = render_interview_invite_email(candidate_name, role_title, round_label, slots or [])
    else:
        return None

    return email_draft_store.create_draft(
        requisition_id=requisition["id"],
        pipeline_id=record["id"],
        candidate_email=candidate_email,
        template_type=template_type,
        subject=subject,
        body_html=html,
        body_text=text,
    )


@router.get("/api/hr/requisitions/{requisition_id}/pipeline")
def api_list_pipeline(requisition_id: str, stage: str = "") -> dict[str, Any]:
    records = pipeline_store.list_records(requisition_id)
    if stage:
        records = [r for r in records if r.get("stage") == stage]
    return {"pipeline": records}


@router.patch("/api/hr/requisitions/{requisition_id}/pipeline/{pipeline_id}/stage")
def api_update_pipeline_stage(requisition_id: str, pipeline_id: str, payload: StageUpdateInput) -> dict[str, Any]:
    requisition = requisition_store.get_requisition(requisition_id)
    if requisition is None:
        raise HTTPException(status_code=404, detail="Requisition not found")

    record = pipeline_store.update_stage(requisition_id, pipeline_id, payload.new_stage, payload.note)
    if record is None:
        raise HTTPException(status_code=404, detail="Pipeline record not found")

    draft = None
    if payload.new_stage == "Rejected":
        draft = _draft_email_for_event(requisition, record, "reject")
    elif payload.new_stage == "Offer":
        draft = _draft_email_for_event(requisition, record, "offer")

    return {"record": record, "draft_email": draft}


@router.patch("/api/hr/requisitions/{requisition_id}/pipeline/{pipeline_id}/email")
def api_update_pipeline_email(requisition_id: str, pipeline_id: str, payload: CandidateEmailUpdateInput) -> dict[str, Any]:
    record = pipeline_store.update_email(requisition_id, pipeline_id, payload.email)
    if record is None:
        raise HTTPException(status_code=404, detail="Pipeline record not found")
    return record


@router.post("/api/hr/requisitions/{requisition_id}/pipeline/{pipeline_id}/advance-interview")
def api_advance_interview(requisition_id: str, pipeline_id: str, payload: InterviewAdvanceInput) -> dict[str, Any]:
    requisition = requisition_store.get_requisition(requisition_id)
    if requisition is None:
        raise HTTPException(status_code=404, detail="Requisition not found")

    existing = pipeline_store.get_record(requisition_id, pipeline_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Pipeline record not found")

    slots = payload.slots or interview_slots(existing.get("score", 0)).get("slots", [])
    record = pipeline_store.update_stage(requisition_id, pipeline_id, payload.round_label, note="Interview scheduled")
    draft = _draft_email_for_event(requisition, record, "interview_invite", round_label=payload.round_label, slots=slots)

    return {"record": record, "draft_email": draft}


# ---------------------------------------------------------------------------
# Outbound emails (approval-gated — drafted on stage change, sent only on
# an explicit HR click)
# ---------------------------------------------------------------------------


@router.get("/api/hr/emails/pending")
def api_list_pending_emails(requisition_id: str = "") -> dict[str, Any]:
    drafts = email_draft_store.list_pending(requisition_id or None)
    for draft in drafts:
        draft["candidate_email"] = _live_candidate_email(draft)
    return {"drafts": drafts}


@router.patch("/api/hr/emails/{email_id}")
def api_edit_email_draft(email_id: str, payload: EmailEditInput, requisition_id: str) -> dict[str, Any]:
    draft = email_draft_store.get_draft(email_id, requisition_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Email draft not found")

    fields = {k: v for k, v in payload.model_dump().items() if v}
    return email_draft_store.update_draft(email_id, requisition_id, **fields)


def _live_candidate_email(draft: dict[str, Any]) -> str:
    """A draft snapshots candidate_email at creation time, but HR can add/fix a
    local-file candidate's email on the pipeline record afterwards (see
    api_update_pipeline_email). Resolve against the live pipeline record so an
    email added after the draft was created still lets it be sent."""
    record = pipeline_store.get_record(draft["requisition_id"], draft["pipeline_id"])
    if record is not None and record.get("candidate_email"):
        return record["candidate_email"]
    return draft.get("candidate_email", "")


@router.post("/api/hr/emails/{email_id}/send")
def api_send_email_draft(email_id: str, requisition_id: str) -> dict[str, Any]:
    draft = email_draft_store.get_draft(email_id, requisition_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Email draft not found")

    to = _live_candidate_email(draft)
    result = send_email(to, draft["subject"], draft["body_html"], draft.get("body_text", ""))
    if result["success"]:
        return email_draft_store.mark_sent(email_id, requisition_id, result.get("provider_id") or "")
    return email_draft_store.mark_failed(email_id, requisition_id, result.get("error") or "Unknown error")


@router.post("/api/hr/emails/send-bulk")
def api_send_emails_bulk(payload: BulkEmailSendInput) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for email_id in payload.email_ids:
        draft = email_draft_store.find_draft(email_id)
        if draft is None:
            results.append({"id": email_id, "status": "not_found", "error": "Draft not found"})
            continue

        requisition_id = draft["requisition_id"]
        to = _live_candidate_email(draft)
        result = send_email(to, draft["subject"], draft["body_html"], draft.get("body_text", ""))
        if result["success"]:
            email_draft_store.mark_sent(email_id, requisition_id, result.get("provider_id") or "")
            results.append({"id": email_id, "status": "sent", "error": None})
        else:
            email_draft_store.mark_failed(email_id, requisition_id, result.get("error") or "Unknown error")
            results.append({"id": email_id, "status": "failed", "error": result.get("error")})

    return {"results": results}


@router.post("/api/hr/emails/{email_id}/cancel")
def api_cancel_email_draft(email_id: str, requisition_id: str) -> dict[str, Any]:
    draft = email_draft_store.mark_cancelled(email_id, requisition_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Email draft not found")
    return draft


# ---------------------------------------------------------------------------
# Dashboard / analytics — real data from persisted pipeline records
# ---------------------------------------------------------------------------


@router.get("/api/hr/dashboard")
def api_dashboard_route(requisition_id: str = "") -> dict[str, Any]:
    return build_dashboard(requisition_id or None)


@router.get("/api/analytics")
def api_analytics_route(requisition_id: str = "") -> dict[str, Any]:
    return build_analytics(requisition_id or None)
