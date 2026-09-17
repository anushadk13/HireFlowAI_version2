from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.schemas import AuthLoginInput, AuthLookupInput, AuthPublicAccount, AuthUpsertInput
from backend.services.auth_store import auth_store

router = APIRouter()


@router.post("/api/auth/lookup", response_model=AuthPublicAccount)
def api_auth_lookup(payload: AuthLookupInput) -> dict[str, Any]:
    account = auth_store.get_account(payload.email)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/api/auth/login", response_model=AuthPublicAccount)
def api_auth_login(payload: AuthLoginInput) -> dict[str, Any]:
    account = auth_store.login_account(payload.email, payload.password)
    if not account:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return account


@router.post("/api/auth/upsert", response_model=AuthPublicAccount)
def api_auth_upsert(payload: AuthUpsertInput) -> dict[str, Any]:
    if payload.role.lower() not in {"student", "hr"}:
        raise HTTPException(status_code=400, detail="Role must be student or hr")
    try:
        account = auth_store.upsert_account(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return account
