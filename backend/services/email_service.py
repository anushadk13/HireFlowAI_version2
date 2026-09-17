from __future__ import annotations

import os
from typing import Any


def send_email(to: str, subject: str, html_body: str, text_body: str = "") -> dict[str, Any]:
    """Sends via Resend. Never raises — always returns
    {"success": bool, "provider_id": str | None, "error": str | None} so
    callers (approval-gated by design: only ever invoked from an explicit
    HR "Send" action, never from ranking or automatic stage changes) can
    surface a clean failure instead of a 500."""
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email = os.getenv("RESEND_FROM_EMAIL", "").strip()
    from_name = os.getenv("RESEND_FROM_NAME", "HireFlow AI").strip()

    if not api_key or not from_email:
        return {
            "success": False,
            "provider_id": None,
            "error": "Email sending is not configured (missing RESEND_API_KEY/RESEND_FROM_EMAIL).",
        }

    if not to.strip():
        return {"success": False, "provider_id": None, "error": "No candidate email on file."}

    try:
        import resend

        resend.api_key = api_key
        result = resend.Emails.send(
            {
                "from": f"{from_name} <{from_email}>" if from_name else from_email,
                "to": [to],
                "subject": subject,
                "html": html_body,
                "text": text_body,
            }
        )
        provider_id = result.get("id") if isinstance(result, dict) else None
        return {"success": True, "provider_id": provider_id, "error": None}
    except Exception as exc:  # noqa: BLE001 - any provider/network failure surfaces as a clean error
        return {"success": False, "provider_id": None, "error": str(exc)}
