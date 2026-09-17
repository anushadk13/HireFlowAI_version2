from __future__ import annotations

import re

_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]\d{3,4}[-.\s]\d{3,4}\b")
_ADDRESS_PATTERN = re.compile(
    r"\b\d{1,5}\s+[A-Za-z0-9.'\s]{2,40}\b(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl)\b\.?,?",
    re.IGNORECASE,
)
_GRAD_YEAR_PATTERN = re.compile(r"(graduat\w*[^.\n]{0,30}?)\b(19|20)\d{2}\b", re.IGNORECASE)
_NAME_LINE_PATTERN = re.compile(r"^[A-Z][a-zA-Z'\-.]+(?:\s+[A-Z][a-zA-Z'\-.]+){1,3}$")


def scrub_pii(resume_text: str) -> str:
    """Best-effort removal of name, address, and graduation year before the text
    reaches an LLM prompt, to reduce identity-linked bias in scoring. Heuristic,
    not guaranteed complete."""
    lines = resume_text.splitlines()
    for i, line in enumerate(lines[:3]):
        stripped = line.strip()
        if stripped and "@" not in stripped and not any(char.isdigit() for char in stripped) and _NAME_LINE_PATTERN.match(stripped):
            lines[i] = "[CANDIDATE NAME]"
            break
    text = "\n".join(lines)
    text = _EMAIL_PATTERN.sub("[EMAIL REDACTED]", text)
    text = _PHONE_PATTERN.sub("[PHONE REDACTED]", text)
    text = _ADDRESS_PATTERN.sub("[ADDRESS REDACTED]", text)
    text = _GRAD_YEAR_PATTERN.sub(lambda m: f"{m.group(1)}[YEAR REDACTED]", text)
    return text
