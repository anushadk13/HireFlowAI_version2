from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ResumeInput(BaseModel):
    resume_text: str = Field(..., min_length=1)
    job_description: str = ""
    target_role: str = ""
    additional_context: str = ""
    candidate_name: str = ""


class JobDescriptionInput(BaseModel):
    job_description: str = Field(..., min_length=1)


class CareerQuestionInput(BaseModel):
    question: str = Field(..., min_length=1)
    resume_text: str = ""
    job_description: str = ""


class CandidateBatchInput(BaseModel):
    candidates: list[dict[str, Any]]
    job_description: str = ""
    requisition_id: str = ""


class RequisitionInput(BaseModel):
    title: str = Field(..., min_length=1)
    job_description: str = Field(..., min_length=1)
    created_by: str = ""


class Requisition(BaseModel):
    id: str
    title: str
    job_description: str
    status: str = "open"
    created_by: str = ""
    created_at: str
    updated_at: str


class RequisitionStatusInput(BaseModel):
    status: str = Field(..., min_length=1)


class PipelineRecord(BaseModel):
    id: str
    requisition_id: str
    candidate_name: str
    candidate_email: str = ""
    candidate_source: str
    resume_id: str = ""
    resume_user_id: str = ""
    score: int
    ats: int
    skill_match: int
    projects: str
    scoring_method: str
    matched_skills: list[str] = Field(default_factory=list)
    stage: str
    recommended_action: str = ""
    stage_history: list[dict[str, str]] = Field(default_factory=list)
    created_at: str
    updated_at: str


class StageUpdateInput(BaseModel):
    new_stage: str = Field(..., min_length=1)
    note: str = ""


class CandidateEmailUpdateInput(BaseModel):
    email: str = Field(..., min_length=3)


class InterviewAdvanceInput(BaseModel):
    round_label: str = Field(..., min_length=1)
    slots: list[str] = Field(default_factory=list)


class EmailDraft(BaseModel):
    id: str
    requisition_id: str
    pipeline_id: str
    candidate_email: str = ""
    template_type: str
    subject: str
    body_html: str
    body_text: str = ""
    status: str = "pending"
    created_at: str
    sent_at: str = ""
    error: str = ""


class EmailEditInput(BaseModel):
    subject: str = ""
    body_html: str = ""
    body_text: str = ""


class BulkEmailSendInput(BaseModel):
    email_ids: list[str] = Field(default_factory=list)


class AssessmentInput(BaseModel):
    topic: str
    skill_level: str = "intermediate"
    candidate_answers: list[str] = Field(default_factory=list)


class ChatInput(BaseModel):
    message: str
    skills: list[str] = Field(default_factory=list)


class AuthLookupInput(BaseModel):
    email: str = Field(..., min_length=3)


class AuthLoginInput(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class AuthUpsertInput(BaseModel):
    email: str = Field(..., min_length=3)
    display_name: str = ""
    role: str = Field(..., min_length=1)
    password: str = ""
    provider: str = "google"
    firebase_uid: str = ""


class AuthStoredAccount(BaseModel):
    id: str
    email: str
    display_name: str = ""
    role: str
    password: str
    provider: str = "google"
    firebase_uid: str = ""
    created_at: str
    updated_at: str


class AuthPublicAccount(BaseModel):
    id: str
    email: str
    display_name: str = ""
    role: str
    provider: str = "google"
    firebase_uid: str = ""
    created_at: str
    updated_at: str
