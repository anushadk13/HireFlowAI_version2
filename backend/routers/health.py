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

