from __future__ import annotations

import re
from collections import Counter

from backend.services.data import SKILL_ALIASES


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]*", text.lower())


_ALIAS_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    skill: [re.compile(rf"\b{re.escape(alias)}\b") for alias in aliases]
    for skill, aliases in SKILL_ALIASES.items()
}


def detect_skills(text: str) -> list[str]:
    normalized = normalize(text)
    detected: list[str] = []
    for skill, patterns in _ALIAS_PATTERNS.items():
        if any(pattern.search(normalized) for pattern in patterns):
            detected.append(skill)
    return detected


def count_bullets(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip().startswith(("-", "*", "•")))


def detect_weak_bullets(text: str) -> list[str]:
    weak_markers = [
        "worked on",
        "responsible for",
        "helped with",
        "assisted",
        "various tasks",
        "team member",
    ]
    bullets = [line.strip(" -*•") for line in text.splitlines() if line.strip().startswith(("-", "*", "•"))]
    return [bullet for bullet in bullets if any(marker in bullet.lower() for marker in weak_markers)]


def grammar_notes(text: str) -> list[str]:
    notes: list[str] = []
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if sentences and any(sentence and sentence[0].islower() for sentence in sentences):
        notes.append("Some sentences start in lowercase.")
    if "  " in text:
        notes.append("Remove repeated spaces.")
    if len(text) > 0 and len(text.split()) < 80:
        notes.append("Resume content is short; add more measurable detail.")
    if text.count(",") > 20:
        notes.append("Several long sentences could be tightened for readability.")
    return notes[:4]


def formatting_suggestions(text: str) -> list[str]:
    suggestions = []
    if count_bullets(text) < 3:
        suggestions.append("Use bullet points under each role to improve scannability.")
    if not re.search(r"\b(education|experience|projects|skills|summary)\b", text.lower()):
        suggestions.append("Add clear section headings such as Summary, Experience, Projects, and Skills.")
    if not re.search(r"\b\d+%|\b\d+\+|\$\d+|[0-9]{4}\b", text):
        suggestions.append("Add metrics, years, or outcomes where possible to make impact concrete.")
    return suggestions[:4]


def extract_keywords(text: str, limit: int = 12) -> list[str]:
    tokens = [token for token in words(text) if len(token) > 2]
    common = Counter(tokens)
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "from",
        "this",
        "have",
        "your",
        "you",
        "will",
        "are",
        "was",
        "into",
        "using",
        "work",
        "worked",
        "experience",
        "skills",
    }
    items = [word for word, _count in common.most_common() if word not in stopwords]
    return items[:limit]

