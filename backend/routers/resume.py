from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.schemas import CareerQuestionInput, ResumeInput
from backend.services.blob_storage import resume_blob_storage
from backend.services.document_extract import extract_document_text
from backend.services.resume import (
    CoverLetterError,
    ats_score,
    build_improvement_bundle,
    career_advice,
    generate_cover_letter,
    interview_questions,
    role_resume_version,
)
from backend.services.resume_store import resume_store

router = APIRouter()


@router.post("/api/resume/extract-text")
async def api_resume_extract_text(
    file: UploadFile = File(...),
    user_id: str = Form(""),
) -> dict[str, Any]:
    content = await file.read()
    try:
        text = extract_document_text(file.filename or "", content, file.content_type or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not text:
        raise HTTPException(status_code=400, detail="No readable text was found in the uploaded resume.")

    blob = resume_blob_storage.upload_resume(
        file.filename or "resume",
        content,
        file.content_type or "",
        user_id=user_id,
    )

    resume_id = None
    download_url = None
    if blob and user_id.strip():
        record, evicted = resume_store.add_resume(
            user_id=user_id,
            filename=file.filename or "resume",
            blob_name=blob["blob_name"],
            container=blob["container"],
            content_type=file.content_type or "application/octet-stream",
            size=blob["size"],
        )
        for old in evicted:
            resume_blob_storage.delete_resume(old["blob_name"])
        resume_id = record["id"]
        download_url = resume_blob_storage.generate_download_url(blob["blob_name"])

    return {
        "text": text,
        "resume_id": resume_id,
        "blob_name": blob["blob_name"] if blob else None,
        "download_url": download_url,
    }


@router.get("/api/resume/list")
def api_resume_list(user_id: str) -> dict[str, Any]:
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required.")

    records = resume_store.list_resumes(user_id)
    for record in records:
        record["download_url"] = resume_blob_storage.generate_download_url(record["blob_name"])
    return {"resumes": records}


@router.get("/api/resume/{resume_id}/text")
def api_resume_text(resume_id: str, user_id: str) -> dict[str, Any]:
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required.")

    record = resume_store.get_resume(user_id, resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="Resume not found.")

    content = resume_blob_storage.download_resume(record["blob_name"])
    if content is None:
        raise HTTPException(status_code=502, detail="Could not retrieve the resume file from storage.")

    try:
        text = extract_document_text(record["filename"], content, record.get("content_type", ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"text": text}


@router.delete("/api/resume/{resume_id}")
def api_resume_delete(resume_id: str, user_id: str) -> dict[str, Any]:
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required.")

    record = resume_store.get_resume(user_id, resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="Resume not found.")

    resume_blob_storage.delete_resume(record["blob_name"])
    resume_store.delete_resume(user_id, resume_id)
    return {"deleted": True}


@router.post("/api/resume/analyze")
def api_resume_analyze(payload: ResumeInput) -> dict[str, Any]:
    analysis = ats_score(payload.resume_text, payload.job_description)
    analysis["summary"] = (
        "The resume is well aligned for screening." if analysis["ats_score"] >= 80 else "The resume needs tighter keyword alignment and clearer achievement language."
    )
    return analysis


@router.post("/api/resume/improve")
def api_resume_improve(payload: ResumeInput) -> dict[str, Any]:
    return build_improvement_bundle(payload.resume_text, payload.job_description, payload.target_role)


@router.post("/api/resume/cover-letter")
def api_cover_letter(payload: ResumeInput) -> dict[str, str]:
    try:
        letter = generate_cover_letter(payload.resume_text, payload.job_description, payload.additional_context)
    except CoverLetterError as exc:
        status_code = 400 if "job description is required" in str(exc) else 503
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return {"cover_letter": letter}


@router.post("/api/resume/interview-prep")
def api_interview_prep(payload: ResumeInput) -> dict[str, list[str]]:
    return interview_questions(payload.resume_text, payload.job_description)


@router.post("/api/career-advisor")
def api_career_advisor(payload: CareerQuestionInput) -> dict[str, str]:
    return {"answer": career_advice(payload.question, payload.resume_text, payload.job_description)}


@router.get("/api/resume/versions")
def api_resume_versions(resume_text: str = "") -> dict[str, Any]:
    roles = ["Data Scientist", "Frontend Engineer", "AI Engineer", "Backend Engineer"]
    return {role: role_resume_version(role, resume_text) for role in roles}
