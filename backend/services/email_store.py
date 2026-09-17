from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


class EmailDraftStore:
    """Outbound email drafts awaiting HR approval. A draft is created when a
    candidate's stage changes to Rejected/Offer or an interview is scheduled —
    never sent automatically. Partitioned by requisition_id."""

    def __init__(self) -> None:
        self._mode = "memory"
        self._memory: dict[str, list[dict[str, Any]]] = {}
        self._container = None

        endpoint = os.getenv("COSMOS_ENDPOINT", "").strip()
        key = os.getenv("COSMOS_KEY", "").strip()
        database_name = os.getenv("COSMOS_DATABASE", "hireflow-ai").strip()
        container_name = os.getenv("COSMOS_EMAIL_CONTAINER", "email_drafts").strip() or "email_drafts"

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
                partition_key=PartitionKey(path="/requisition_id"),
            )
            self._mode = "cosmos"
        except Exception:
            self._container = None

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

        if self._mode == "cosmos" and self._container is not None:
            self._container.upsert_item(record)
        else:
            self._memory.setdefault(requisition_id, []).append(record)

        return record

    def list_pending(self, requisition_id: str | None = None) -> list[dict[str, Any]]:
        return self._list(status="pending", requisition_id=requisition_id)

    def _list(self, status: str | None, requisition_id: str | None) -> list[dict[str, Any]]:
        if self._mode == "cosmos" and self._container is not None:
            try:
                if requisition_id:
                    query = "SELECT * FROM c WHERE c.requisition_id = @requisition_id"
                    params = [{"name": "@requisition_id", "value": requisition_id}]
                    if status:
                        query += " AND c.status = @status"
                        params.append({"name": "@status", "value": status})
                    query += " ORDER BY c.created_at DESC"
                    items = list(
                        self._container.query_items(
                            query=query, parameters=params, partition_key=requisition_id
                        )
                    )
                else:
                    query = "SELECT * FROM c"
                    params = []
                    if status:
                        query += " WHERE c.status = @status"
                        params.append({"name": "@status", "value": status})
                    query += " ORDER BY c.created_at DESC"
                    items = list(
                        self._container.query_items(
                            query=query, parameters=params, enable_cross_partition_query=True
                        )
                    )
                return items
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
        if self._mode == "cosmos" and self._container is not None:
            try:
                return self._container.read_item(item=email_id, partition_key=requisition_id)
            except Exception:
                return None

        for record in self._memory.get(requisition_id, []):
            if record["id"] == email_id:
                return record
        return None

    def find_draft(self, email_id: str) -> dict[str, Any] | None:
        """Look up a draft by id alone, when its requisition_id isn't known yet."""
        for record in self._list(status=None, requisition_id=None):
            if record["id"] == email_id:
                return record
        return None

    def _save(self, requisition_id: str, record: dict[str, Any]) -> None:
        if self._mode == "cosmos" and self._container is not None:
            self._container.upsert_item(record)
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
