from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter

from backend.services.firebase_client import get_firestore_client


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EmailDraftStore:
    """Outbound email drafts awaiting HR approval. A draft is created when a
    candidate's stage changes to Rejected/Offer or an interview is scheduled —
    never sent automatically."""

    def __init__(self) -> None:
        self._memory: dict[str, list[dict[str, Any]]] = {}
        self._db = get_firestore_client()
        self._mode = "firestore" if self._db is not None else "memory"
        self._collection_name = os.getenv("FIRESTORE_EMAIL_COLLECTION", "email_drafts").strip() or "email_drafts"

    def _collection(self):
        return self._db.collection(self._collection_name)

    def create_draft(
        self,
        requisition_id: str,
        pipeline_id: str,
        candidate_email: str,
        template_type: str,
        subject: str,
        body_html: str,
        body_text: str = "",
    ) -> dict[str, Any]:
        record = {
            "id": uuid.uuid4().hex,
            "requisition_id": requisition_id,
            "pipeline_id": pipeline_id,
            "candidate_email": candidate_email.strip().lower(),
            "template_type": template_type,
            "subject": subject,
            "body_html": body_html,
            "body_text": body_text,
            "status": "pending",
            "created_at": _utc_now(),
            "sent_at": "",
            "error": "",
        }

        if self._mode == "firestore" and self._db is not None:
            self._collection().document(record["id"]).set(record)
        else:
            self._memory.setdefault(requisition_id, []).append(record)

        return record

    def list_pending(self, requisition_id: str | None = None) -> list[dict[str, Any]]:
        return self._list(status="pending", requisition_id=requisition_id)

    def _list(self, status: str | None, requisition_id: str | None) -> list[dict[str, Any]]:
        if self._mode == "firestore" and self._db is not None:
            try:
                query = self._collection()
                if requisition_id:
                    query = query.where(filter=FieldFilter("requisition_id", "==", requisition_id))
                if status:
                    query = query.where(filter=FieldFilter("status", "==", status))
                records = [doc.to_dict() for doc in query.stream()]
                return sorted(records, key=lambda r: r.get("created_at", ""), reverse=True)
            except Exception:
                return []

        if requisition_id:
            records = self._memory.get(requisition_id, [])
        else:
            records = [record for records in self._memory.values() for record in records]

        if status:
            records = [r for r in records if r.get("status") == status]

        return sorted(records, key=lambda r: r.get("created_at", ""), reverse=True)

    def get_draft(self, email_id: str, requisition_id: str) -> dict[str, Any] | None:
        if self._mode == "firestore" and self._db is not None:
            try:
                doc = self._collection().document(email_id).get()
                if not doc.exists:
                    return None
                record = doc.to_dict()
                return record if record.get("requisition_id") == requisition_id else None
            except Exception:
                return None

        for record in self._memory.get(requisition_id, []):
            if record["id"] == email_id:
                return record
        return None

    def find_draft(self, email_id: str) -> dict[str, Any] | None:
        """Look up a draft by id alone, when its requisition_id isn't known yet."""
        if self._mode == "firestore" and self._db is not None:
            try:
                doc = self._collection().document(email_id).get()
                return doc.to_dict() if doc.exists else None
            except Exception:
                return None

        for record in self._list(status=None, requisition_id=None):
            if record["id"] == email_id:
                return record
        return None

    def _save(self, requisition_id: str, record: dict[str, Any]) -> None:
        if self._mode == "firestore" and self._db is not None:
            self._collection().document(record["id"]).set(record)
            return

        bucket = self._memory.setdefault(requisition_id, [])
        for i, existing in enumerate(bucket):
            if existing["id"] == record["id"]:
                bucket[i] = record
                return
        bucket.append(record)

    def update_draft(self, email_id: str, requisition_id: str, **fields: Any) -> dict[str, Any] | None:
        record = self.get_draft(email_id, requisition_id)
        if record is None:
            return None
        record.update(fields)
        self._save(requisition_id, record)
        return record

    def mark_sent(self, email_id: str, requisition_id: str, provider_id: str = "") -> dict[str, Any] | None:
        return self.update_draft(
            email_id, requisition_id, status="sent", sent_at=_utc_now(), error="", provider_id=provider_id
        )

    def mark_failed(self, email_id: str, requisition_id: str, error: str) -> dict[str, Any] | None:
        return self.update_draft(email_id, requisition_id, status="failed", error=error)

    def mark_cancelled(self, email_id: str, requisition_id: str) -> dict[str, Any] | None:
        return self.update_draft(email_id, requisition_id, status="cancelled")


email_draft_store = EmailDraftStore()
