from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def index() -> dict[str, str]:
    return {
        "service": "HireFlow AI backend",
        "status": "ok",
        "hint": "Run the frontend separately from the frontend/ directory.",
    }


@router.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/health/storage")
def storage_health() -> dict[str, str]:
    """Report whether Firestore is reachable and writable (no secrets exposed)."""
    from backend.services.firebase_client import get_firestore_client

    db = get_firestore_client()
    if db is None:
        return {"mode": "memory", "detail": "Firebase not initialised; check FIREBASE_SERVICE_ACCOUNT_JSON"}
    try:
        db.collection("_health").document("ping").set({"ok": True})
        return {"mode": "firestore", "project": str(db.project), "write": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"mode": "firestore", "write": "failed", "error": f"{type(exc).__name__}: {str(exc)[:300]}"}

