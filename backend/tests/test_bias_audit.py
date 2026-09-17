import unittest

from backend.services.resume import ats_score

# Names drawn from groups used in the Bertrand-Mullainathan resume-callback audit design:
# identical resume content, name swapped across groups commonly associated with different
# race/ethnicity perceptions in US hiring contexts.
CANDIDATE_NAMES = [
    "Emily Johnson",
    "Lakisha Washington",
    "Wei Chen",
    "Carlos Hernandez",
    "Aisha Mohammed",
]

RESUME_TEMPLATE = """{name}
Email: candidate@example.com | Phone: 555-123-4567

Experience
Software Engineer, Acme Corp (2020-2024)
- Built and shipped REST APIs serving 1M+ requests/day using Python and FastAPI
- Deployed containerized services on AWS using Docker, cutting release time by 40%

Skills
Python, FastAPI, AWS, Docker, SQL
"""

JOB_DESCRIPTION = (
    "Backend Engineer. Requirements: 2+ years experience with Python, FastAPI, AWS, and Docker."
)

# Regex scorer never reads the name, so this should hold near-exactly; the AI path relies on
# PII scrubbing removing the name line before it ever reaches the model.
SCORE_DELTA_TOLERANCE = 2


class BiasAuditTests(unittest.TestCase):
    def test_score_is_invariant_to_candidate_name(self):
        scores = {
            name: ats_score(RESUME_TEMPLATE.format(name=name), JOB_DESCRIPTION, use_ai=False)["ats_score"]
            for name in CANDIDATE_NAMES
        }
        spread = max(scores.values()) - min(scores.values())
        self.assertLessEqual(
            spread,
            SCORE_DELTA_TOLERANCE,
            f"ATS score varied by {spread} points across an identical resume with only the name swapped: {scores}",
        )


if __name__ == "__main__":
    unittest.main()
