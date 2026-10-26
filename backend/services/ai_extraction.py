from __future__ import annotations

import json
import logging
from typing import Any

from backend.services.llm import LLMConfig, LLMError, generate
from backend.services.prompts import JD_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


class AIExtractionError(Exception):
    pass


def _coerce_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    role_summary = _coerce_list(raw.get("role_summary"))
    responsibilities = _coerce_list(raw.get("responsibilities")) or role_summary
    return {
        "role_title": str(raw.get("role_title") or "Role not specified").strip()[:120],
        "role_summary": role_summary[:5],
        "salary": str(raw.get("salary") or "Not specified").strip()[:80],
        "employment_type": str(raw.get("employment_type") or "Not specified").strip()[:40],
        "location": str(raw.get("location") or "Not specified").strip()[:80],
        "skills": _coerce_list(raw.get("skills")),
        "experience": _coerce_list(raw.get("experience")) or ["2+ years of relevant experience"],
        "degree": str(raw.get("degree") or "Not specified").strip()[:80],
        "keywords": _coerce_list(raw.get("keywords"))[:10],
        "responsibilities": responsibilities[:5],
    }


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


def extract_jd_with_ai(job_description: str, llm: LLMConfig) -> dict[str, Any] | None:
    try:
        text = generate(
            llm, JD_EXTRACTION_PROMPT.format(job_description=job_description), max_tokens=1024, json_mode=True
        )
        raw = json.loads(_strip_code_fence(text))
        if not isinstance(raw, dict):
            raise AIExtractionError("Model did not return a JSON object")
        return _normalize(raw)
    except LLMError:
        raise
    except Exception as exc:  # noqa: BLE001 - any failure here should fall back to the regex parser
        logger.warning("AI job description extraction failed, falling back to regex parser: %s", exc)
        return None
