from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter

from backend.services.firebase_client import get_firestore_client


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RequisitionStore:
    """Job requisitions — a job opening that can be reopened later as a
    separate, independently trackable record (e.g. "AI Engineer" opened in
    Jan 2026 and again in Sept 2026 are two rows, not one overwritten row)."""

    def __init__(self) -> None:
        self._memory: dict[str, dict[str, Any]] = {}
        self._db = get_firestore_client()
        self._mode = "firestore" if self._db is not None else "memory"
        self._collection_name = (
            os.getenv("FIRESTORE_REQUISITION_COLLECTION", "requisitions").strip() or "requisitions"
        )

    def _collection(self):
        return self._db.collection(self._collection_name)

    def create_requisition(self, title: str, job_description: str, created_by: str = "") -> dict[str, Any]:
        now = _utc_now()
        record = {
            "id": uuid.uuid4().hex,
            "title": title.strip(),
            "job_description": job_description,
            "status": "open",
            "created_by": created_by.strip().lower(),
            "created_at": now,
            "updated_at": now,
        }

        if self._mode == "firestore" and self._db is not None:
            self._collection().document(record["id"]).set(record)
        else:
            self._memory[record["id"]] = record

        return record

    def list_requisitions(self) -> list[dict[str, Any]]:
        if self._mode == "firestore" and self._db is not None:
            try:
                records = [doc.to_dict() for doc in self._collection().stream()]
                return sorted(records, key=lambda r: r.get("created_at", ""), reverse=True)
            except Exception:
                return []

        return sorted(self._memory.values(), key=lambda r: r.get("created_at", ""), reverse=True)

    def get_requisition(self, requisition_id: str) -> dict[str, Any] | None:
        if self._mode == "firestore" and self._db is not None:
            try:
                doc = self._collection().document(requisition_id).get()
                return doc.to_dict() if doc.exists else None
            except Exception:
                return None

        return self._memory.get(requisition_id)

    def update_status(self, requisition_id: str, status: str) -> dict[str, Any] | None:
        record = self.get_requisition(requisition_id)
        if record is None:
            return None

        record["status"] = status
        record["updated_at"] = _utc_now()

        if self._mode == "firestore" and self._db is not None:
            self._collection().document(requisition_id).set(record)
        else:
            self._memory[requisition_id] = record

        return record


class PipelineStore:
    """Per-requisition candidate pipeline records, filtered by requisition_id
    since nearly every query is scoped to one requisition."""

    def __init__(self) -> None:
        self._memory: dict[str, list[dict[str, Any]]] = {}
        self._db = get_firestore_client()
        self._mode = "firestore" if self._db is not None else "memory"
        self._collection_name = (
            os.getenv("FIRESTORE_PIPELINE_COLLECTION", "pipeline_records").strip() or "pipeline_records"
        )

    def _collection(self):
        return self._db.collection(self._collection_name)

    def create_records_bulk(self, requisition_id: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        now = _utc_now()
        created: list[dict[str, Any]] = []

        for candidate in records:
            record = {
                "id": uuid.uuid4().hex,
                "requisition_id": requisition_id,
                "stage_history": [{"stage": candidate["stage"], "changed_at": now, "note": ""}],
                "created_at": now,
                "updated_at": now,
                **candidate,
            }
            created.append(record)

        if self._mode == "firestore" and self._db is not None:
            batch = self._db.batch()
            for record in created:
                batch.set(self._collection().document(record["id"]), record)
            batch.commit()
        else:
            bucket = self._memory.setdefault(requisition_id, [])
            bucket.extend(created)

        return created

    def list_records(self, requisition_id: str) -> list[dict[str, Any]]:
        if self._mode == "firestore" and self._db is not None:
            try:
                docs = self._collection().where(filter=FieldFilter("requisition_id", "==", requisition_id)).stream()
                records = [doc.to_dict() for doc in docs]
                return sorted(records, key=lambda r: r.get("score", 0), reverse=True)
            except Exception:
                return []

        records = self._memory.get(requisition_id, [])
        return sorted(records, key=lambda r: r.get("score", 0), reverse=True)

    def list_all_records(self) -> list[dict[str, Any]]:
        """Records across every requisition, for the "all requisitions" dashboard view."""
        if self._mode == "firestore" and self._db is not None:
            try:
                records = [doc.to_dict() for doc in self._collection().stream()]
                return sorted(records, key=lambda r: r.get("score", 0), reverse=True)
            except Exception:
                return []

        all_records = [record for records in self._memory.values() for record in records]
        return sorted(all_records, key=lambda r: r.get("score", 0), reverse=True)

    def get_record(self, requisition_id: str, pipeline_id: str) -> dict[str, Any] | None:
        if self._mode == "firestore" and self._db is not None:
            try:
                doc = self._collection().document(pipeline_id).get()
                if not doc.exists:
                    return None
                record = doc.to_dict()
                return record if record.get("requisition_id") == requisition_id else None
            except Exception:
                return None

        for record in self._memory.get(requisition_id, []):
            if record["id"] == pipeline_id:
                return record
        return None

    def find_by_resume(self, requisition_id: str, resume_id: str) -> dict[str, Any] | None:
        if not resume_id:
            return None
        for record in self.list_records(requisition_id):
            if record.get("resume_id") == resume_id:
                return record
        return None

    def _save(self, requisition_id: str, record: dict[str, Any]) -> None:
        record["updated_at"] = _utc_now()

        if self._mode == "firestore" and self._db is not None:
            self._collection().document(record["id"]).set(record)
            return

        bucket = self._memory.setdefault(requisition_id, [])
        for i, existing in enumerate(bucket):
            if existing["id"] == record["id"]:
                bucket[i] = record
                return
        bucket.append(record)

    def update_stage(
        self, requisition_id: str, pipeline_id: str, new_stage: str, note: str = ""
    ) -> dict[str, Any] | None:
        record = self.get_record(requisition_id, pipeline_id)
        if record is None:
            return None

        record["stage"] = new_stage
        record.setdefault("stage_history", []).append(
            {"stage": new_stage, "changed_at": _utc_now(), "note": note}
        )
        self._save(requisition_id, record)
        return record

    def update_email(self, requisition_id: str, pipeline_id: str, email: str) -> dict[str, Any] | None:
        record = self.get_record(requisition_id, pipeline_id)
        if record is None:
            return None

        record["candidate_email"] = email.strip().lower()
        self._save(requisition_id, record)
        return record

    def replace_score(self, requisition_id: str, pipeline_id: str, fields: dict[str, Any]) -> dict[str, Any] | None:
        record = self.get_record(requisition_id, pipeline_id)
        if record is None:
            return None

        record.update(fields)
        self._save(requisition_id, record)
        return record


requisition_store = RequisitionStore()
pipeline_store = PipelineStore()
