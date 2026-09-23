from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.services.firebase_client import get_storage_bucket

logger = logging.getLogger(__name__)

_SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")
_DEFAULT_URL_EXPIRY_MINUTES = 15


def _safe_filename(filename: str) -> str:
    name = _SAFE_NAME_PATTERN.sub("_", filename or "resume").strip("_") or "resume"
    return name[:150]


def _safe_user_prefix(user_id: str) -> str:
    name = _SAFE_NAME_PATTERN.sub("_", (user_id or "anonymous").strip().lower()).strip("_")
    return name[:150] or "anonymous"


class ResumeBlobStorage:
    def __init__(self) -> None:
        self._bucket = get_storage_bucket()
        self._enabled = self._bucket is not None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def upload_resume(
        self,
        filename: str,
        content: bytes,
        content_type: str = "",
        user_id: str = "",
    ) -> dict[str, Any] | None:
        if not self._enabled or self._bucket is None:
            return None

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        blob_name = f"{_safe_user_prefix(user_id)}/{timestamp}_{uuid.uuid4().hex[:8]}_{_safe_filename(filename)}"

        try:
            blob = self._bucket.blob(blob_name)
            blob.upload_from_string(content, content_type=content_type or "application/octet-stream")
            return {
                "blob_name": blob_name,
                "container": self._bucket.name,
                "url": blob.public_url,
                "size": len(content),
            }
        except Exception as exc:  # noqa: BLE001 - storage must never block resume upload
            logger.warning("Failed to upload resume to Firebase Storage: %s", exc)
            return None

    def generate_download_url(
        self,
        blob_name: str,
        expiry_minutes: int = _DEFAULT_URL_EXPIRY_MINUTES,
    ) -> str | None:
        """Return a short-lived, read-only signed URL for a file. The bucket is
        private, so the raw storage URL is never usable on its own."""
        if not self._enabled or self._bucket is None:
            return None

        try:
            blob = self._bucket.blob(blob_name)
            return blob.generate_signed_url(expiration=timedelta(minutes=expiry_minutes))
        except Exception as exc:  # noqa: BLE001 - a missing download link must never break the request
            logger.warning("Failed to generate signed URL for %s: %s", blob_name, exc)
            return None

    def download_resume(self, blob_name: str) -> bytes | None:
        if not self._enabled or self._bucket is None:
            return None

        try:
            return self._bucket.blob(blob_name).download_as_bytes()
        except Exception as exc:  # noqa: BLE001 - storage must never break the caller
            logger.warning("Failed to download %s: %s", blob_name, exc)
            return None

    def delete_resume(self, blob_name: str) -> bool:
        if not self._enabled or self._bucket is None:
            return False

        try:
            self._bucket.blob(blob_name).delete()
            return True
        except Exception as exc:  # noqa: BLE001 - storage must never block the caller
            logger.warning("Failed to delete %s: %s", blob_name, exc)
            return False


resume_blob_storage = ResumeBlobStorage()
