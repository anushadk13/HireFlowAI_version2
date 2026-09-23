from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter

from backend.services.firebase_client import get_firestore_client

_MAX_RESUMES_PER_USER = 5


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_user_id(user_id: str) -> str:
    return user_id.strip().lower()


class ResumeStore:
    """Per-user resume metadata, keyed by user_id. The actual file bytes live
    in Firebase Storage; this store only tracks references (blob_name/container)
    so we never need to list a storage bucket to answer "what resumes does this
    user have"."""

    def __init__(self) -> None:
        self._memory: dict[str, list[dict[str, Any]]] = {}
        self._db = get_firestore_client()
        self._mode = "firestore" if self._db is not None else "memory"
        self._collection_name = os.getenv("FIRESTORE_RESUME_COLLECTION", "resumes").strip() or "resumes"

    def _collection(self):
        return self._db.collection(self._collection_name)

    def list_resumes(self, user_id: str) -> list[dict[str, Any]]:
        normalized = _normalize_user_id(user_id)

        if self._mode == "firestore" and self._db is not None:
            try:
                docs = self._collection().where(filter=FieldFilter("user_id", "==", normalized)).stream()
                records = [doc.to_dict() for doc in docs]
                return sorted(records, key=lambda r: r.get("uploaded_at", ""), reverse=True)
            except Exception:
                return []

        records = self._memory.get(normalized, [])
        return sorted(records, key=lambda r: r.get("uploaded_at", ""), reverse=True)

    def list_all_resumes(self) -> list[dict[str, Any]]:
        """List resumes across every user, for HR-side bulk analysis."""
        if self._mode == "firestore" and self._db is not None:
            try:
                docs = self._collection().stream()
                records = [doc.to_dict() for doc in docs]
                return sorted(records, key=lambda r: r.get("uploaded_at", ""), reverse=True)
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
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
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
        # single account can't grow the collection unbounded.
        overflow = existing[_MAX_RESUMES_PER_USER - 1 :]

        if self._mode == "firestore" and self._db is not None:
            for old in overflow:
                try:
                    self._collection().document(old["id"]).delete()
                except Exception:
                    pass
            self._collection().document(record["id"]).set(record)
        else:
            bucket = self._memory.setdefault(normalized, [])
            keep_ids = {r["id"] for r in overflow}
            self._memory[normalized] = [r for r in bucket if r["id"] not in keep_ids]
            self._memory[normalized].append(record)

        return record, [r for r in overflow]

    def get_resume(self, user_id: str, resume_id: str) -> dict[str, Any] | None:
        normalized = _normalize_user_id(user_id)

        if self._mode == "firestore" and self._db is not None:
            try:
                doc = self._collection().document(resume_id).get()
                if not doc.exists:
                    return None
                record = doc.to_dict()
                return record if record.get("user_id") == normalized else None
            except Exception:
                return None

        for record in self._memory.get(normalized, []):
            if record["id"] == resume_id:
                return record
        return None

    def delete_resume(self, user_id: str, resume_id: str) -> bool:
        normalized = _normalize_user_id(user_id)

        if self._mode == "firestore" and self._db is not None:
            if self.get_resume(normalized, resume_id) is None:
                return False
            try:
                self._collection().document(resume_id).delete()
                return True
            except Exception:
                return False

        bucket = self._memory.get(normalized, [])
        before = len(bucket)
        self._memory[normalized] = [r for r in bucket if r["id"] != resume_id]
        return len(self._memory[normalized]) < before


resume_store = ResumeStore()
