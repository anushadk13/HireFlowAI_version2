from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

_SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")
_DEFAULT_SAS_EXPIRY_MINUTES = 15


def _safe_filename(filename: str) -> str:
    name = _SAFE_NAME_PATTERN.sub("_", filename or "resume").strip("_") or "resume"
    return name[:150]


def _safe_user_prefix(user_id: str) -> str:
    name = _SAFE_NAME_PATTERN.sub("_", (user_id or "anonymous").strip().lower()).strip("_")
    return name[:150] or "anonymous"


class ResumeBlobStorage:
    def __init__(self) -> None:
        self._service_client = None
        self._client = None
        self._account_key: str | None = None
        self._container_name = os.getenv("AZURE_STORAGE_CONTAINER", "resumes").strip() or "resumes"
        self._enabled = False

        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "").strip()
        if not connection_string:
            return

        try:
            from azure.storage.blob import BlobServiceClient
        except Exception:
            logger.warning("azure-storage-blob is not installed; resume blob storage is disabled.")
            return

        try:
            service_client = BlobServiceClient.from_connection_string(connection_string)
            container_client = service_client.get_container_client(self._container_name)
            if not container_client.exists():
                container_client.create_container()
            self._service_client = service_client
            self._client = container_client
            self._account_key = getattr(service_client.credential, "account_key", None)
            self._enabled = True
        except Exception as exc:  # noqa: BLE001 - storage must never block resume upload
            logger.warning("Failed to initialize Azure Blob Storage; resume blob storage is disabled: %s", exc)
            self._client = None

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
        if not self._enabled or self._client is None:
            return None

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        blob_name = f"{_safe_user_prefix(user_id)}/{timestamp}_{uuid.uuid4().hex[:8]}_{_safe_filename(filename)}"

        try:
            from azure.storage.blob import ContentSettings

            blob_client = self._client.get_blob_client(blob_name)
            blob_client.upload_blob(
                content,
                overwrite=False,
                content_settings=ContentSettings(content_type=content_type or "application/octet-stream"),
            )
            return {
                "blob_name": blob_name,
                "container": self._container_name,
                "url": blob_client.url,
                "size": len(content),
            }
        except Exception as exc:  # noqa: BLE001 - storage must never block resume upload
            logger.warning("Failed to upload resume to Azure Blob Storage: %s", exc)
            return None

    def generate_download_url(
        self,
        blob_name: str,
        expiry_minutes: int = _DEFAULT_SAS_EXPIRY_MINUTES,
    ) -> str | None:
        """Return a short-lived, read-only SAS URL for a blob. The raw blob URL is
        never usable on its own because the container is private."""
        if not self._enabled or self._client is None or self._service_client is None or not self._account_key:
            return None

        try:
            from azure.storage.blob import BlobSasPermissions, generate_blob_sas

            sas_token = generate_blob_sas(
                account_name=self._service_client.account_name,
                container_name=self._container_name,
                blob_name=blob_name,
                account_key=self._account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
            )
            blob_client = self._client.get_blob_client(blob_name)
            return f"{blob_client.url}?{sas_token}"
        except Exception as exc:  # noqa: BLE001 - a missing download link must never break the request
            logger.warning("Failed to generate SAS URL for blob %s: %s", blob_name, exc)
            return None

    def download_resume(self, blob_name: str) -> bytes | None:
        if not self._enabled or self._client is None:
            return None

        try:
            return self._client.get_blob_client(blob_name).download_blob().readall()
        except Exception as exc:  # noqa: BLE001 - storage must never break the caller
            logger.warning("Failed to download blob %s: %s", blob_name, exc)
            return None

    def delete_resume(self, blob_name: str) -> bool:
        if not self._enabled or self._client is None:
            return False

        try:
            self._client.get_blob_client(blob_name).delete_blob()
            return True
        except Exception as exc:  # noqa: BLE001 - storage must never block the caller
            logger.warning("Failed to delete blob %s: %s", blob_name, exc)
            return False


resume_blob_storage = ResumeBlobStorage()
