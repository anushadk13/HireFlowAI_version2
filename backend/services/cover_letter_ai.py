from __future__ import annotations

import logging

from google import genai
from google.genai import types

from backend.services.prompts import COVER_LETTER_PROMPT

logger = logging.getLogger(__name__)

MODEL = "gemini-3.5-flash-lite"


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    text = text.strip("`")
    if "\n" in text:
        first_line, rest = text.split("\n", 1)
        if first_line.strip().lower() in {"", "text", "markdown"}:
            return rest.strip()
    return text


def generate_cover_letter_with_ai(
    resume_text: str, job_description: str, additional_context: str, api_key: str
) -> str | None:
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL,
            contents=COVER_LETTER_PROMPT.format(
                resume_text=resume_text,
                job_description=job_description,
                additional_context=additional_context or "(none provided)",
            ),
            config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=1024),
        )
        text = _strip_code_fence(response.text or "")
        if not text:
            return None
        return text
    except Exception as exc:  # noqa: BLE001 - any failure here should fall back to the template generator
        logger.warning("AI cover letter generation failed, falling back to template generator: %s", exc)
        return None
