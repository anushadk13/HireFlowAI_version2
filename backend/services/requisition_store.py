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


class RequisitionStore:
    """Job requisitions — a job opening that can be reopened later as a
    separate, independently trackable record (e.g. "AI Engineer" opened in
    Jan 2026 and again in Sept 2026 are two rows, not one overwritten row)."""

    def __init__(self) -> None:
        self._mode = "memory"
        self._memory: dict[str, dict[str, Any]] = {}
        self._container = None

        endpoint = os.getenv("COSMOS_ENDPOINT", "").strip()
        key = os.getenv("COSMOS_KEY", "").strip()
        database_name = os.getenv("COSMOS_DATABASE", "hireflow-ai").strip()
        container_name = os.getenv("COSMOS_REQUISITION_CONTAINER", "requisitions").strip() or "requisitions"

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
                partition_key=PartitionKey(path="/id"),
            )
            self._mode = "cosmos"
        except Exception:
            self._container = None

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

        if self._mode == "cosmos" and self._container is not None:
            self._container.upsert_item(record)
        else:
            self._memory[record["id"]] = record

        return record

    def list_requisitions(self) -> list[dict[str, Any]]:
        if self._mode == "cosmos" and self._container is not None:
            try:
                items = list(
                    self._container.query_items(
                        query="SELECT * FROM c ORDER BY c.created_at DESC",
                        enable_cross_partition_query=True,
                    )
                )
                return items
            except Exception:
                return []

        return sorted(self._memory.values(), key=lambda r: r.get("created_at", ""), reverse=True)

    def get_requisition(self, requisition_id: str) -> dict[str, Any] | None:
        if self._mode == "cosmos" and self._container is not None:
            try:
                return self._container.read_item(item=requisition_id, partition_key=requisition_id)
            except Exception:
                return None

        return self._memory.get(requisition_id)

    def update_status(self, requisition_id: str, status: str) -> dict[str, Any] | None:
        record = self.get_requisition(requisition_id)
        if record is None:
            return None

        record["status"] = status
        record["updated_at"] = _utc_now()

        if self._mode == "cosmos" and self._container is not None:
            self._container.upsert_item(record)
        else:
            self._memory[requisition_id] = record

        return record


class PipelineStore:
    """Per-requisition candidate pipeline records, partitioned by
    requisition_id since nearly every query is scoped to one requisition."""

    def __init__(self) -> None:
        self._mode = "memory"
        self._memory: dict[str, list[dict[str, Any]]] = {}
        self._container = None

        endpoint = os.getenv("COSMOS_ENDPOINT", "").strip()
        key = os.getenv("COSMOS_KEY", "").strip()
        database_name = os.getenv("COSMOS_DATABASE", "hireflow-ai").strip()
        container_name = os.getenv("COSMOS_PIPELINE_CONTAINER", "pipeline_records").strip() or "pipeline_records"

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

        if self._mode == "cosmos" and self._container is not None:
            for record in created:
                self._container.upsert_item(record)
        else:
            bucket = self._memory.setdefault(requisition_id, [])
            bucket.extend(created)

        return created

    def list_records(self, requisition_id: str) -> list[dict[str, Any]]:
        if self._mode == "cosmos" and self._container is not None:
            try:
                items = list(
                    self._container.query_items(
                        query="SELECT * FROM c WHERE c.requisition_id = @requisition_id ORDER BY c.score DESC",
                        parameters=[{"name": "@requisition_id", "value": requisition_id}],
                        partition_key=requisition_id,
                    )
                )
                return items
            except Exception:
                return []

        records = self._memory.get(requisition_id, [])
        return sorted(records, key=lambda r: r.get("score", 0), reverse=True)

    def list_all_records(self) -> list[dict[str, Any]]:
        """Records across every requisition, for the "all requisitions" dashboard view."""
        if self._mode == "cosmos" and self._container is not None:
            try:
                items = list(
                    self._container.query_items(
                        query="SELECT * FROM c ORDER BY c.score DESC",
                        enable_cross_partition_query=True,
                    )
                )
                return items
            except Exception:
                return []

        all_records = [record for records in self._memory.values() for record in records]
        return sorted(all_records, key=lambda r: r.get("score", 0), reverse=True)

    def get_record(self, requisition_id: str, pipeline_id: str) -> dict[str, Any] | None:
        if self._mode == "cosmos" and self._container is not None:
            try:
                return self._container.read_item(item=pipeline_id, partition_key=requisition_id)
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

        if self._mode == "cosmos" and self._container is not None:
            self._container.upsert_item(record)
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
