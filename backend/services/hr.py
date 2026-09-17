from __future__ import annotations

import re
from typing import Any

from backend.services.data import PIPELINE_COUNTS, SAMPLE_CANDIDATES
from backend.services.resume import ats_score
from backend.services.text_utils import detect_skills, extract_keywords


ROLE_SUFFIXES = (
    r"(?:Engineer|Developer|Designer|Analyst|Scientist|Manager|Specialist|Consultant|"
    r"Intern|Architect|Administrator|Coordinator|Director|Lead|Officer|Executive)"
)

RESPONSIBILITY_HEADERS = [
    r"key responsibilities",
    r"responsibilities",
    r"what you.?ll be doing",
    r"what you.?ll do",
    r"what you will do",
    r"what you.?ll work on",
    r"duties",
    r"your role",
    r"the role",
    r"day.to.day",
    r"role overview",
    r"potential roles(?: include)?",
    r"roles include",
    r"opportunities include",
]

OTHER_SECTION_HEADERS = [
    r"requirements",
    r"qualifications",
    r"minimum qualifications",
    r"preferred qualifications",
    r"what we.?re looking for",
    r"who you are",
    r"about you",
    r"must.have",
    r"nice.to.have",
    r"skills(?: required)?",
    r"benefits",
    r"perks",
    r"what we offer",
    r"why join us",
    r"about (?:us|the company|the team)",
    r"how to apply",
    r"potential teams(?: you could join)?",
    r"teams you could join",
]

RHETORICAL_QUESTION_PATTERN = re.compile(r"\?\s*$")

BOILERPLATE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"equal opportunity",
        r"reasonable accommodations?",
        r"drug.free workplace",
        r"accessibility is a fundamental",
        r"committed to inclusion",
        r"diversity and inclusion",
    ]
]


def _find_section(text: str, start_headers: list[str], all_headers: list[str]) -> str | None:
    lines = text.splitlines()
    start_pattern = re.compile(rf"^\s*[-*•]?\s*(?:{'|'.join(start_headers)})\s*:?\s*$", re.IGNORECASE)
    any_pattern = re.compile(rf"^\s*[-*•]?\s*(?:{'|'.join(all_headers)})\s*:?\s*$", re.IGNORECASE)
    start_idx = None
    for i, line in enumerate(lines):
        if start_pattern.match(line.strip()):
            start_idx = i + 1
            break
    if start_idx is None:
        return None
    end_idx = len(lines)
    for j in range(start_idx, len(lines)):
        if any_pattern.match(lines[j].strip()):
            end_idx = j
            break
    section = "\n".join(lines[start_idx:end_idx]).strip()
    return section or None


def parse_jd(job_description: str) -> dict[str, Any]:
    cleaned = re.sub(r"\s+", " ", job_description).strip()
    skills = detect_skills(job_description)
    keywords = extract_keywords(job_description, 10)
    experience = []
    lower = job_description.lower()
    role_title = "Role not specified"
    title_patterns = [
        r"(?:job\s*title|position|role|title)\s*[:\-]\s*([^\n.]+)",
        rf"^\**\s*([A-Z][A-Za-z0-9 /&+-]*{ROLE_SUFFIXES})\**\s*(?:\n|$|[-@|]|\bat\b)",
        rf"\b(?:hiring|looking for|seeking)\s+(?:an?\s+)?([A-Za-z0-9 /&+-]*{ROLE_SUFFIXES})\b",
    ]
    for pattern in title_patterns:
        match = re.search(pattern, job_description.strip(), re.IGNORECASE | re.MULTILINE)
        if match:
            role_title = match.group(1).strip(" -:,.*")[:80]
            break

    experience_match = re.search(
        r"(\d+)\s*(?:-|to)\s*(\d+)\+?\s+years?|(\d+)\+?\s+years?",
        lower,
    )
    if experience_match:
        if experience_match.group(1) and experience_match.group(2):
            experience.append(f"{experience_match.group(1)}-{experience_match.group(2)} years")
        else:
            experience.append(f"{experience_match.group(3)}+ years")
    if "degree" in lower or "bachelor" in lower:
        experience.append("Bachelor's degree or equivalent")

    salary = "Not specified"
    currency = r"(?:\$|£|€|aud|usd|gbp|inr|eur)"
    amount = r"\d{2,3}(?:,\d{3})?(?:k)?"
    salary_match = re.search(
        rf"{currency}\s?{amount}(?:\s*(?:-|–|to)\s*{currency}?\s?{amount})?"
        rf"|{amount}(?:\s*(?:-|–|to)\s*{amount})?\s*{currency}\b",
        job_description,
        re.IGNORECASE,
    )
    if salary_match:
        salary = salary_match.group(0).strip()

    employment_type = "Not specified"
    type_map = [
        ("Full-time", ["full-time", "full time", "permanent"]),
        ("Part-time", ["part-time", "part time"]),
        ("Contract", ["contract", "contractor"]),
        ("Internship", ["internship", "intern"]),
        ("Casual", ["casual"]),
    ]
    for label, terms in type_map:
        if any(term in lower for term in terms):
            employment_type = label
            break

    location = "Not specified"
    location_match = re.search(
        r"(?:location|based in|located in|position is located in)\s*[:\-]?\s*([A-Za-z ,/-]+)",
        job_description,
        re.IGNORECASE,
    )
    if location_match:
        location = location_match.group(1).strip(" -:,.")[:80]
    elif "remote" in lower:
        location = "Remote"
    elif "hybrid" in lower:
        location = "Hybrid"

    action_words = [
        "build",
        "design",
        "maintain",
        "develop",
        "own",
        "implement",
        "collaborate",
        "manage",
        "deliver",
        "create",
        "work",
        "lead",
        "drive",
        "solve",
        "research",
        "prototype",
        "partner",
        "support",
        "coordinate",
        "analyze",
        "analyse",
        "conduct",
        "ensure",
        "define",
        "architect",
        "optimize",
        "optimise",
        "troubleshoot",
        "mentor",
        "review",
        "monitor",
        "assist",
        "contribute",
        "improve",
        "plan",
        "execute",
        "translate",
        "responsible for",
        "accountable for",
        "you will",
        "you'll",
    ]

    def clean_item(item: str) -> str:
        cleaned = re.sub(r"\s+", " ", item or "").strip(" -*•\t\r\n").strip()
        return cleaned

    def dedupe_bullets(chunks: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for chunk in chunks:
            cleaned = clean_item(chunk)
            if not cleaned or len(cleaned) < 4:
                continue
            normalized = re.sub(r"\s+", " ", cleaned).lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            result.append(cleaned)
        return result

    metadata_label_pattern = re.compile(
        r"^(?:salary|compensation|location|employment type|job type|experience|education|"
        r"degree|company|industry|department|team|apply|how to apply|contact|email|phone)\s*[:\-]",
        re.IGNORECASE,
    )

    def strip_metadata_lines(items: list[str]) -> list[str]:
        return [item for item in items if not metadata_label_pattern.match(item)]

    def strip_boilerplate(items: list[str]) -> list[str]:
        return [
            item
            for item in items
            if not RHETORICAL_QUESTION_PATTERN.search(item)
            and not any(pattern.search(item) for pattern in BOILERPLATE_PATTERNS)
        ]

    responsibility_candidates: list[str] = []
    section_text = _find_section(job_description, RESPONSIBILITY_HEADERS, OTHER_SECTION_HEADERS)
    if section_text:
        section_chunks = re.split(r"\n+|(?:^|\n)\s*(?:[-*•]|\d+\.)\s*", section_text)
        responsibility_candidates = strip_metadata_lines(dedupe_bullets(section_chunks))

    if not responsibility_candidates:
        candidates = dedupe_bullets(
            re.split(r"\n+|(?:^|\n)\s*(?:[-*•]|\d+\.)\s*|(?<=[.!?])\s+", job_description.strip())
        )
        candidates = strip_boilerplate(strip_metadata_lines(candidates))
        responsibility_candidates = [item for item in candidates if any(word in item.lower() for word in action_words)]

    if not responsibility_candidates:
        responsibility_candidates = [
            "Own the end-to-end delivery of product features.",
            "Collaborate with cross-functional stakeholders.",
            "Write maintainable and testable code.",
        ]

    responsibilities = [item for item in responsibility_candidates if item][:5]
    role_summary = responsibilities[:5]
    if not role_summary:
        fallback_summary = cleaned[:180].strip()
        if len(fallback_summary) > 180:
            fallback_summary = f"{fallback_summary[:177].rstrip()}..."
        role_summary = [fallback_summary]

    return {
        "role_title": role_title,
        "role_summary": role_summary,
        "salary": salary,
        "employment_type": employment_type,
        "location": location,
        "skills": skills,
        "experience": experience or ["2+ years of relevant experience"],
        "degree": "Bachelor's degree preferred" if ("degree" in lower or "bachelor" in lower) else "Not specified",
        "keywords": keywords,
        "responsibilities": responsibilities,
    }


def project_evaluation(project_text: str) -> dict[str, Any]:
    lower = project_text.lower()
    score = 35
    reasons: list[str] = []
    if any(term in lower for term in ["rag", "llm", "vector", "embedding", "semantic"]):
        score += 25
        reasons.append("Uses modern AI retrieval or generation concepts.")
    if any(term in lower for term in ["fastapi", "django", "express", "api"]):
        score += 15
        reasons.append("Shows backend architecture and integration depth.")
    if any(term in lower for term in ["docker", "aws", "kubernetes", "deployment"]):
        score += 10
        reasons.append("Includes production-oriented delivery details.")
    if any(term in lower for term in ["dashboard", "analytics", "metric", "visualization"]):
        score += 10
        reasons.append("Demonstrates product and business impact.")
    if any(term in lower for term in ["clone", "todo", "weather app"]):
        score -= 12
        reasons.append("Looks like a common tutorial project.")
    if len(project_text.split()) > 40:
        score += 5
    score = max(0, min(100, score))
    if score >= 80:
        tier = "High"
    elif score >= 55:
        tier = "Medium"
    else:
        tier = "Low"
    if not reasons:
        reasons = ["Project is understandable, but the differentiation is not obvious."]
    return {"score": score, "tier": tier, "reasons": reasons}


def fraud_detection(resume_text: str) -> dict[str, Any]:
    lower = resume_text.lower()
    flags = []
    if lower.count("intern") > 4:
        flags.append("Possible keyword stuffing around internships.")
    if lower.count("developed") > 8 or lower.count("built") > 8:
        flags.append("Repeated verbs may indicate template reuse.")
    if "github.com" not in lower and "portfolio" not in lower and len(resume_text.split()) > 300:
        flags.append("Long resume without supporting links can look overstated.")
    if any(phrase in lower for phrase in ["managed a team of 100", "led 50 engineers"]):
        flags.append("Large scale claims should be verified.")
    return {"risk": "Low" if not flags else "Moderate", "flags": flags or ["No obvious fraud signals detected."]}


def auto_evaluation(answers: list[str]) -> dict[str, Any]:
    combined = " ".join(answers).lower()
    positive = sum(term in combined for term in ["python", "sql", "api", "test", "optimize", "design"])
    score = min(100, 40 + positive * 10 + min(20, len(answers) * 5))
    return {
        "score": score,
        "status": "Passed" if score >= 70 else "Needs Review",
        "feedback": [
            "Use more concrete terms and include steps or tradeoffs." if score < 70 else "Answers are strong enough to advance.",
            "Add examples where you measured impact.",
        ],
    }


def interview_slots(score: int) -> dict[str, Any]:
    if score <= 80:
        return {"eligible": False, "message": "Score must be above 80 to trigger scheduling."}
    return {
        "eligible": True,
        "message": "Interview slot options prepared and ready to send.",
        "slots": ["Mon 10:00", "Tue 14:30", "Wed 09:00"],
    }


def api_dashboard() -> dict[str, Any]:
    pipeline = PIPELINE_COUNTS.copy()
    shortlist_rate = round(pipeline["shortlisted"] / pipeline["total"] * 100, 1)
    return {
        "applications": pipeline,
        "shortlist_rate": shortlist_rate,
        "skills_distribution": [
            {"label": "Python", "value": 92},
            {"label": "SQL", "value": 77},
            {"label": "React", "value": 64},
            {"label": "Docker", "value": 51},
            {"label": "AWS", "value": 44},
        ],
        "funnel": [
            {"label": "Applied", "value": 327},
            {"label": "Screened", "value": 188},
            {"label": "Shortlisted", "value": 58},
            {"label": "Interviewed", "value": 31},
            {"label": "Offered", "value": 12},
        ],
        "top_colleges": [
            {"label": "University of Adelaide", "value": 18},
            {"label": "Monash University", "value": 16},
            {"label": "University of Melbourne", "value": 15},
            {"label": "UNSW", "value": 13},
        ],
        "experience_distribution": [
            {"label": "0-2", "value": 41},
            {"label": "3-5", "value": 93},
            {"label": "6-8", "value": 54},
            {"label": "8+", "value": 17},
        ],
        "sample_candidates": SAMPLE_CANDIDATES,
    }


def api_analytics() -> dict[str, Any]:
    return {
        "avg_ats": 84.2,
        "skills_distribution": [
            {"label": "Python", "value": 92},
            {"label": "React", "value": 64},
            {"label": "SQL", "value": 77},
            {"label": "FastAPI", "value": 58},
            {"label": "LangChain", "value": 49},
        ],
        "pipeline": [
            {"label": "Applications", "value": 327},
            {"label": "Shortlisted", "value": 58},
            {"label": "Rejected", "value": 190},
            {"label": "Pending", "value": 79},
        ],
    }
