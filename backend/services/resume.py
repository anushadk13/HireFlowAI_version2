from __future__ import annotations

import math
import os
from typing import Any

from backend.services.cover_letter_ai import generate_cover_letter_with_ai
from backend.services.data import ROLE_PROFILES
from backend.services.resume_scoring import score_resume_with_ai
from backend.services.text_utils import (
    count_bullets,
    detect_skills,
    detect_weak_bullets,
    extract_keywords,
    formatting_suggestions,
    grammar_notes,
)


def _keywords_score(resume_text: str, job_description: str) -> int:
    if not job_description:
        return 0
    resume_kw = {kw.lower() for kw in extract_keywords(resume_text, 20)}
    jd_kw = {kw.lower() for kw in extract_keywords(job_description, 20)}
    if not jd_kw:
        return 0
    return round(len(resume_kw & jd_kw) / len(jd_kw) * 100)


def _formatting_score(resume_text: str) -> int:
    return max(40, 100 - len(formatting_suggestions(resume_text)) * 20)


def _improvement_suggestions(
    missing_skills: list[str],
    weak_bullet_points: list[str],
    format_suggestions: list[str],
    grammar_issues: list[str],
) -> list[str]:
    suggestions: list[str] = []
    for skill in missing_skills[:2]:
        suggestions.append(f"Add or highlight experience with {skill} — it's in the job description but not detected in your resume.")
    if weak_bullet_points:
        suggestions.append("Rewrite vague bullets (e.g. \"worked on\", \"responsible for\") with specific actions and outcomes.")
    suggestions.extend(format_suggestions)
    suggestions.extend(grammar_issues)
    if not suggestions:
        suggestions.append("Your resume already covers the detected job requirements well — consider adding metrics to strengthen existing bullets.")
    return suggestions[:4]


def _ats_score_regex(resume_text: str, job_description: str = "") -> dict[str, Any]:
    resume_skills = detect_skills(resume_text)
    job_skills = detect_skills(job_description) if job_description else []
    matched_skills = sorted(set(resume_skills) & set(job_skills))
    missing_skills = sorted(set(job_skills) - set(resume_skills))
    bullet_bonus = min(10, count_bullets(resume_text) * 2)
    keyword_bonus = min(15, len(extract_keywords(resume_text)) * 1.3)
    alignment = 0
    if job_skills:
        alignment = math.floor((len(matched_skills) / max(1, len(set(job_skills)))) * 45)
    content_bonus = 30 if len(resume_text.split()) > 120 else 18
    score = max(20, min(100, 20 + bullet_bonus + keyword_bonus + alignment + content_bonus))
    skills_match_score = round((len(matched_skills) / len(job_skills)) * 100) if job_skills else 0
    return {
        "ats_score": score,
        "resume_score": min(100, score + 2),
        "scoring_method": "regex_fallback",
        "score_type": "coverage_score",
        "grammar_notes": grammar_notes(resume_text),
        "formatting_suggestions": formatting_suggestions(resume_text),
        "missing_skills": missing_skills,
        "weak_bullet_points": detect_weak_bullets(resume_text),
        "keyword_optimization": missing_skills[:6] or extract_keywords(job_description, 6),
        "matched_skills": matched_skills,
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "skills_match_score": skills_match_score,
        "experience_score": min(100, round(bullet_bonus / 10 * 60 + 20)),
        "gates": [],
        "flags": {"keyword_stuffing": []},
    }


def ats_score(resume_text: str, job_description: str = "", *, use_ai: bool = True) -> dict[str, Any]:
    result: dict[str, Any] | None = None
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if use_ai and api_key and job_description.strip():
        result = score_resume_with_ai(resume_text, job_description, api_key)

    if result is None:
        result = _ats_score_regex(resume_text, job_description)

    result["keywords_score"] = _keywords_score(resume_text, job_description)
    result["formatting_score"] = _formatting_score(resume_text)
    result.setdefault("grammar_notes", grammar_notes(resume_text))
    result.setdefault("formatting_suggestions", formatting_suggestions(resume_text))
    result.setdefault("weak_bullet_points", detect_weak_bullets(resume_text))
    result.setdefault("keyword_optimization", result.get("missing_skills", [])[:6] or extract_keywords(job_description, 6))
    result.setdefault("resume_skills", detect_skills(resume_text))
    result.setdefault("job_skills", detect_skills(job_description) if job_description else [])
    suggestions = _improvement_suggestions(
        result.get("missing_skills", []),
        result.get("weak_bullet_points", []),
        result.get("formatting_suggestions", []),
        result.get("grammar_notes", []),
    )
    result["improvement_suggestions"] = suggestions
    result.setdefault("improvement", {})["improvement_suggestions"] = suggestions
    result["match_score"] = result["ats_score"]
    result["skills_match"] = result["matched_skills"]
    result["recommendation"] = (
        "Strong match" if result["ats_score"] >= 85 else "Promising" if result["ats_score"] >= 70 else "Needs tailoring"
    )
    return result


def infer_role(resume_text: str, job_description: str = "", target_role: str = "") -> str:
    target_role = target_role.strip()
    if target_role:
        return target_role
    combined = f"{resume_text}\n{job_description}".lower()
    if any(term in combined for term in ["react", "frontend", "typescript", "ui"]):
        return "Frontend Engineer"
    if any(term in combined for term in ["fastapi", "api", "backend", "docker", "postgres"]):
        return "Backend Engineer"
    if any(term in combined for term in ["rag", "llm", "langchain", "chromadb", "openai"]):
        return "AI Engineer"
    if any(term in combined for term in ["data", "model", "statistics", "ml", "machine learning"]):
        return "Data Scientist"
    return "AI Engineer"


def build_improvement_bundle(resume_text: str, job_description: str = "", target_role: str = "") -> dict[str, Any]:
    role = infer_role(resume_text, job_description, target_role)
    profile = ROLE_PROFILES.get(role, ROLE_PROFILES["AI Engineer"])
    resume_skills = detect_skills(resume_text)
    highlighted_skills = sorted(set(resume_skills + profile["skills"]))[:8]
    return {
        "target_role": role,
        "summary": profile["summary"],
        "experience": [
            "Led delivery of a hiring workflow that scores resumes, explains matches, and prioritizes candidates for recruiters.",
            "Collaborated with product and engineering stakeholders to turn ambiguous requirements into measurable system behavior.",
        ],
        "projects": profile["projects"],
        "skills": highlighted_skills,
        "tailored_bullets": [
            "Improved screening quality by combining rule-based ATS scoring with skill extraction and ranking heuristics.",
            "Built reusable UI and backend workflows that reduce recruiter effort and keep candidate feedback consistent.",
        ],
    }


class CoverLetterError(Exception):
    pass


def generate_cover_letter(resume_text: str, job_description: str = "", additional_context: str = "") -> str:
    if not job_description.strip():
        raise CoverLetterError("A job description is required to generate a tailored cover letter.")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise CoverLetterError("Cover letter generation is not configured (missing GEMINI_API_KEY).")

    letter = generate_cover_letter_with_ai(resume_text, job_description, additional_context, api_key)
    if not letter:
        raise CoverLetterError("Cover letter generation failed. Please try again.")
    return letter


def interview_questions(resume_text: str, job_description: str = "") -> dict[str, list[str]]:
    skills = detect_skills(f"{resume_text}\n{job_description}")
    primary = skills[:5] or ["problem solving", "system design"]
    role = infer_role(resume_text, job_description)
    return {
        "hr_questions": [
            f"Tell me about a project where you used {primary[0]}.",
            "What kind of team environment helps you do your best work?",
            "Describe a time you handled changing requirements.",
        ],
        "technical_questions": [
            f"How would you design and test a production feature that uses {skill}?" for skill in primary[:3]
        ],
        "coding_questions": [
            "Write a function that ranks candidates by weighted skills and experience.",
            "How would you optimize text matching for resume-to-job description similarity?",
        ],
        "behavioral_questions": [
            "Tell me about a difficult bug you diagnosed.",
            "Describe a time you improved a process for your team.",
            f"What makes you a strong fit for a {role} role?",
        ],
    }


def career_advice(question: str, resume_text: str = "", job_description: str = "") -> str:
    q = question.lower()
    skills = detect_skills(f"{resume_text}\n{job_description}")
    if "project" in q:
        missing = [skill for skill in ["Docker", "AWS", "React", "LangChain"] if skill not in skills]
        return (
            "Build a project that closes a visible gap in your stack. "
            f"For example, pair {', '.join(missing[:2] or ['LLM orchestration', 'APIs'])} with a clear user workflow, "
            "a dashboard, and measurable outcomes."
        )
    if "certification" in q or "certification" in question.lower():
        return (
            "Choose a certification that supports the direction of your portfolio. "
            f"Given your current profile, the highest-leverage options are: {', '.join(skills[:3] or ['cloud fundamentals', 'system design', 'data literacy'])}."
        )
    if "google" in q or "ready" in q:
        return (
            "You are ready when your resume shows repeated depth in one domain, clean projects, and evidence of ownership. "
            "If those are weak, add one flagship project, strengthen metrics, and practice coding plus system design interviews."
        )
    return (
        "Focus on one portfolio story that proves you can solve a real problem end-to-end. "
        "Strong candidates demonstrate scope, tradeoffs, and measurable results, not just tools."
    )


def role_resume_version(role: str, resume_text: str) -> dict[str, Any]:
    profile = ROLE_PROFILES.get(role, ROLE_PROFILES["AI Engineer"])
    base_skills = detect_skills(resume_text)
    return {
        "role": role,
        "summary": profile["summary"],
        "experience": profile["projects"],
        "skills": sorted(set(base_skills + profile["skills"]))[:10],
    }
