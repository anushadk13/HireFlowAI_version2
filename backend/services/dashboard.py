from __future__ import annotations

from collections import Counter
from typing import Any

from backend.services.pipeline import STAGES
from backend.services.requisition_store import pipeline_store

_FUNNEL_STAGES = [s for s in STAGES if s != "Rejected"]


def _records_for(requisition_id: str | None) -> list[dict[str, Any]]:
    if requisition_id:
        return pipeline_store.list_records(requisition_id)
    return pipeline_store.list_all_records()


def _reached_stage(record: dict[str, Any], stage: str) -> bool:
    if record.get("stage") == stage:
        return True
    return any(h.get("stage") == stage for h in record.get("stage_history", []))


def _skills_distribution(records: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for record in records:
        for skill in record.get("matched_skills", []):
            counter[skill] += 1
    return [{"label": skill, "value": count} for skill, count in counter.most_common(limit)]


def build_dashboard(requisition_id: str | None) -> dict[str, Any]:
    records = _records_for(requisition_id)
    total = len(records)

    rejected = sum(1 for r in records if r.get("stage") == "Rejected")
    accepted = sum(1 for r in records if r.get("stage") == "Accepted")
    shortlisted = sum(1 for r in records if _reached_stage(r, "Shortlisted"))
    offers = sum(1 for r in records if _reached_stage(r, "Offer"))
    pending = max(0, total - rejected - accepted)

    funnel = [
        {"label": stage, "value": sum(1 for r in records if _reached_stage(r, stage))}
        for stage in _FUNNEL_STAGES
    ]

    sample_candidates = [
        {
            "name": r.get("candidate_name", "Candidate"),
            "ats": r.get("ats", 0),
            "skill_match": r.get("skill_match", 0),
            "projects": r.get("projects", ""),
            "recommendation": "Reject" if r.get("recommended_action") == "reject" else "Interview",
            "stage": r.get("stage", ""),
        }
        for r in sorted(records, key=lambda r: r.get("score", 0), reverse=True)[:5]
    ]

    return {
        "applications": {
            "total": total,
            "shortlisted": shortlisted,
            "rejected": rejected,
            "pending": pending,
        },
        "shortlist_rate": round(shortlisted / total * 100, 1) if total else 0,
        "offers": offers,
        "funnel": funnel,
        "skills_distribution": _skills_distribution(records),
        "sample_candidates": sample_candidates,
    }


def build_analytics(requisition_id: str | None) -> dict[str, Any]:
    records = _records_for(requisition_id)
    total = len(records)

    rejected = sum(1 for r in records if r.get("stage") == "Rejected")
    accepted = sum(1 for r in records if r.get("stage") == "Accepted")
    shortlisted = sum(1 for r in records if _reached_stage(r, "Shortlisted"))
    pending = max(0, total - rejected - accepted)

    avg_ats = round(sum(r.get("ats", 0) for r in records) / total, 1) if total else 0

    return {
        "avg_ats": avg_ats,
        "skills_distribution": _skills_distribution(records),
        "pipeline": [
            {"label": "Applications", "value": total},
            {"label": "Shortlisted", "value": shortlisted},
            {"label": "Rejected", "value": rejected},
            {"label": "Pending", "value": pending},
        ],
    }
