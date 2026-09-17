from __future__ import annotations

import json
import logging
from typing import Any

from google import genai
from google.genai import types

from backend.services.pii import scrub_pii
from backend.services.prompts import RESUME_SCORING_PROMPT

logger = logging.getLogger(__name__)

# Note: pro-tier models (e.g. gemini-3.1-pro-preview) return 429 RESOURCE_EXHAUSTED on
# free-tier API keys — no quota, not just access. gemini-2.5-flash-lite is also deprecated
# for new keys (404); gemini-3.5-flash-lite is its live successor, confirmed working
# against this project's key. Switch to a pro-tier model if the key's plan is upgraded.
MODEL = "gemini-3.5-flash-lite"

# Stage 3 weights — published and easy to tune per job. Must sum to 100.
WEIGHTS = {
    "required_skills": 35,
    "experience_relevance": 25,
    "seniority_fit": 15,
    "preferred_skills": 10,
    "domain_fit": 10,
    "education": 5,
}

_EVIDENCE_WEIGHT = {"strong": 1.0, "weak": 0.6, "none": 0.0}


class ScoringError(Exception):
    pass


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    text = text.strip("`")
    if "\n" in text:
        first_line, rest = text.split("\n", 1)
        if first_line.strip().lower() in {"json", ""}:
            return rest.strip()
    return text


def _skill_component(skill_evidence: list[dict[str, Any]], requirement: str) -> tuple[int, list[str]]:
    relevant = [item for item in skill_evidence if item.get("requirement") == requirement]
    if not relevant:
        return 100, []
    total = sum(_EVIDENCE_WEIGHT.get(item.get("evidence_strength"), 0.0) for item in relevant)
    score = round((total / len(relevant)) * 100)
    stuffing = [
        item["skill"]
        for item in relevant
        if item.get("match_type") in {"exact", "alias", "related"} and item.get("evidence_strength") == "none" and item.get("skill")
    ]
    return max(0, min(100, score)), stuffing


def _experience_relevance(responsibility_matches: list[dict[str, Any]]) -> int:
    scores = [item.get("match_score") for item in responsibility_matches if isinstance(item.get("match_score"), (int, float))]
    if not scores:
        return 50
    return max(0, min(100, round(sum(scores) / len(scores))))


def _seniority_fit(candidate_years: float | None, minimum_years: float | None, maximum_years: float | None) -> int:
    if candidate_years is None or minimum_years is None:
        return 70
    target = minimum_years if maximum_years is None else (minimum_years + maximum_years) / 2
    spread = max(2.0, (maximum_years - minimum_years) if maximum_years else max(2.0, minimum_years * 0.6))
    diff = abs(candidate_years - target)
    score = 100 - (diff / spread) * 40
    return max(20, min(100, round(score)))


def _education_component(education_requirement: str, meets: bool | None) -> tuple[int, dict[str, Any] | None]:
    if education_requirement == "required":
        status = "pass" if meets is True else "fail" if meets is False else "unknown"
        gate = {
            "name": "Education requirement",
            "status": status,
            "detail": "Job description states a required education level.",
        }
        score = 100 if meets is True else 0 if meets is False else 50
        return score, gate
    if education_requirement == "preferred":
        score = 100 if meets is True else 60 if meets is False else 75
        return score, None
    return 100, None


def _minimum_years_gate(candidate_years: float | None, minimum_years: float | None) -> dict[str, Any] | None:
    if minimum_years is None:
        return None
    if candidate_years is None:
        return {"name": "Minimum years of experience", "status": "unknown", "detail": f"JD requires {minimum_years}+ years; could not determine candidate's total years."}
    status = "pass" if candidate_years >= minimum_years else "fail"
    return {
        "name": "Minimum years of experience",
        "status": status,
        "detail": f"JD requires {minimum_years}+ years; candidate has approximately {candidate_years} years.",
    }


def score_resume_with_ai(resume_text: str, job_description: str, api_key: str) -> dict[str, Any] | None:
    try:
        scrubbed_resume = scrub_pii(resume_text)
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL,
            contents=RESUME_SCORING_PROMPT.format(resume_text=scrubbed_resume, job_description=job_description),
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=4096,
                response_mime_type="application/json",
            ),
        )
        text = response.text or ""
        raw = json.loads(_strip_code_fence(text))
        if not isinstance(raw, dict):
            raise ScoringError("Model did not return a JSON object")

        resume_structure = raw.get("resume_structure") or {}
        jd_structure = raw.get("jd_structure") or {}
        skill_evidence = raw.get("skill_evidence") or []
        responsibility_matches = raw.get("responsibility_matches") or []
        domain_fit = raw.get("domain_fit") or {}
        education_assessment = raw.get("education_assessment") or {}

        candidate_years = resume_structure.get("total_years_experience")
        minimum_years = jd_structure.get("minimum_years")
        maximum_years = jd_structure.get("maximum_years")
        education_requirement = jd_structure.get("education_requirement", "none")

        required_score, required_stuffing = _skill_component(skill_evidence, "required")
        preferred_score, preferred_stuffing = _skill_component(skill_evidence, "preferred")
        experience_score = _experience_relevance(responsibility_matches)
        seniority_score = _seniority_fit(candidate_years, minimum_years, maximum_years)
        domain_score = max(0, min(100, round(domain_fit.get("score", 50))))
        education_score, education_gate = _education_component(
            education_requirement, education_assessment.get("candidate_meets_requirement")
        )

        component_scores = {
            "required_skills": required_score,
            "preferred_skills": preferred_score,
            "experience_relevance": experience_score,
            "seniority_fit": seniority_score,
            "domain_fit": domain_score,
            "education": education_score,
        }

        overall = round(sum(component_scores[key] * WEIGHTS[key] for key in WEIGHTS) / 100)
        overall = max(0, min(100, overall))

        gates = [gate for gate in [education_gate, _minimum_years_gate(candidate_years, minimum_years)] if gate]
        gates.append(
            {
                "name": "Work authorization",
                "status": "unknown",
                "detail": "Not collected from candidate profile; verify manually before rejecting on this basis.",
            }
        )

        matched_skills = [
            item["skill"]
            for item in skill_evidence
            if item.get("evidence_strength") in {"strong", "weak"} and item.get("skill")
        ]
        missing_skills = [
            item["skill"]
            for item in skill_evidence
            if item.get("evidence_strength") == "none" and item.get("skill")
        ]

        return {
            "ats_score": overall,
            "resume_score": overall,
            "scoring_method": "ai_structured",
            "score_type": "coverage_score",
            "component_scores": component_scores,
            "weights": WEIGHTS,
            "gates": gates,
            "flags": {"keyword_stuffing": sorted(set(required_stuffing + preferred_stuffing))},
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "skill_evidence": skill_evidence,
            "responsibility_matches": responsibility_matches,
            "resume_structure": resume_structure,
            "jd_structure": jd_structure,
            "skills_match_score": round((required_score * WEIGHTS["required_skills"] + preferred_score * WEIGHTS["preferred_skills"]) / (WEIGHTS["required_skills"] + WEIGHTS["preferred_skills"])),
            "experience_score": experience_score,
        }
    except Exception as exc:  # noqa: BLE001 - any failure here should fall back to the regex scorer
        logger.warning("AI resume scoring failed, falling back to regex scorer: %s", exc)
        return None
