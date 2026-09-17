from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_MAX_RESUMES_PER_USER = 5


def _load_env_file() -> None:
    candidates = [
        Path(__file__).resolve().parents[1] / ".env",
        Path(__file__).resolve().parents[2] / ".env",
        Path.cwd() / ".env",
    ]

    for env_path in candidates:
        if not env_path.exists():
            continue

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_user_id(user_id: str) -> str:
    return user_id.strip().lower()


class ResumeStore:
    """Per-user resume metadata, keyed and partitioned by user_id. The actual
    file bytes live in Azure Blob Storage; this store only tracks references
    (blob_name/container) so we never need to list a blob container to answer
    "what resumes does this user have"."""

    def __init__(self) -> None:
        self._mode = "memory"
        self._memory: dict[str, list[dict[str, Any]]] = {}
        self._container = None

        endpoint = os.getenv("COSMOS_ENDPOINT", "").strip()
        key = os.getenv("COSMOS_KEY", "").strip()
        database_name = os.getenv("COSMOS_DATABASE", "hireflow-ai").strip()
        container_name = os.getenv("COSMOS_RESUME_CONTAINER", "resume_records").strip() or "resume_records"

        if not endpoint or not key:
            return

        try:
            from azure.cosmos import CosmosClient, PartitionKey
        except Exception:
            return

        try:
            client = CosmosClient(endpoint, credential=key)
            database = client.create_database_if_not_exists(id=database_name)
            self._container = database.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(path="/user_id"),
            )
            self._mode = "cosmos"
        except Exception:
            self._container = None

    def list_resumes(self, user_id: str) -> list[dict[str, Any]]:
        normalized = _normalize_user_id(user_id)

        if self._mode == "cosmos" and self._container is not None:
            try:
                items = list(
                    self._container.query_items(
                        query="SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.uploaded_at DESC",
                        parameters=[{"name": "@user_id", "value": normalized}],
                        partition_key=normalized,
                    )
                )
                return items
            except Exception:
                return []

        records = self._memory.get(normalized, [])
        return sorted(records, key=lambda r: r.get("uploaded_at", ""), reverse=True)

    def list_all_resumes(self) -> list[dict[str, Any]]:
        """List resumes across every user, for HR-side bulk analysis."""
        if self._mode == "cosmos" and self._container is not None:
            try:
                items = list(
                    self._container.query_items(
                        query="SELECT * FROM c ORDER BY c.uploaded_at DESC",
                        enable_cross_partition_query=True,
                    )
                )
                return items
            except Exception:
                return []

        all_records = [record for records in self._memory.values() for record in records]
        return sorted(all_records, key=lambda r: r.get("uploaded_at", ""), reverse=True)

    def add_resume(
        self,
        user_id: str,
        filename: str,
        blob_name: str,
        container: str,
        content_type: str,
        size: int,
    ) -> dict[str, Any]:
        normalized = _normalize_user_id(user_id)
        existing = self.list_resumes(normalized)

        record = {
            "id": uuid.uuid4().hex,
            "user_id": normalized,
            "filename": filename,
            "blob_name": blob_name,
            "container": container,
            "content_type": content_type,
            "size": size,
            "uploaded_at": _utc_now(),
        }

        # Cap resumes per user; evict the oldest before adding a new one so a
        # single account can't grow the container unbounded.
        overflow = existing[_MAX_RESUMES_PER_USER - 1 :]

        if self._mode == "cosmos" and self._container is not None:
            for old in overflow:
                try:
                    self._container.delete_item(item=old["id"], partition_key=normalized)
                except Exception:
                    pass
            self._container.upsert_item(record)
        else:
            bucket = self._memory.setdefault(normalized, [])
            keep_ids = {r["id"] for r in overflow}
            self._memory[normalized] = [r for r in bucket if r["id"] not in keep_ids]
            self._memory[normalized].append(record)

        return record, [r for r in overflow]

    def get_resume(self, user_id: str, resume_id: str) -> dict[str, Any] | None:
        normalized = _normalize_user_id(user_id)

        if self._mode == "cosmos" and self._container is not None:
            try:
                return self._container.read_item(item=resume_id, partition_key=normalized)
            except Exception:
                return None

        for record in self._memory.get(normalized, []):
            if record["id"] == resume_id:
                return record
        return None

    def delete_resume(self, user_id: str, resume_id: str) -> bool:
        normalized = _normalize_user_id(user_id)

        if self._mode == "cosmos" and self._container is not None:
            try:
                self._container.delete_item(item=resume_id, partition_key=normalized)
                return True
            except Exception:
                return False

        bucket = self._memory.get(normalized, [])
        before = len(bucket)
        self._memory[normalized] = [r for r in bucket if r["id"] != resume_id]
        return len(self._memory[normalized]) < before


resume_store = ResumeStore()
