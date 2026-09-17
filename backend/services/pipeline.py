from __future__ import annotations

STAGES = [
    "Screened",
    "Shortlisted",
    "Interview Round 1",
    "Interview Round 2",
    "Offer",
    "Accepted",
    "Rejected",
]


def assign_initial_stage(score: int) -> tuple[str, str]:
    """Reuses the 85/70 thresholds from api_hr_screen's recommendation logic.
    Returns (stage, recommended_action) — recommended_action is "reject" as a
    flag for HR review, never an automatic move to the Rejected stage."""
    if score >= 85:
        return "Shortlisted", ""
    if score >= 70:
        return "Screened", ""
    return "Screened", "reject"
