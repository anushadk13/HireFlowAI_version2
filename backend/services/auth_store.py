from __future__ import annotations
import base64
import binascii
import hashlib
import os
import hmac
import secrets
from datetime import datetime, timezone
from typing import Any

from backend.services.firebase_client import get_firestore_client

_PASSWORD_SCHEME = "pbkdf2_sha256"
_PASSWORD_ITERATIONS = 310_000
_PASSWORD_SALT_BYTES = 16


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(_PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.strip().encode("utf-8"),
        salt,
        _PASSWORD_ITERATIONS,
    )
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    digest_b64 = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"{_PASSWORD_SCHEME}${_PASSWORD_ITERATIONS}${salt_b64}${digest_b64}"


def _verify_password(password: str, stored_password: str) -> bool:
    if stored_password.startswith(f"{_PASSWORD_SCHEME}$"):
        try:
            _, iterations_raw, salt_b64, digest_b64 = stored_password.split("$", 3)
            iterations = int(iterations_raw)
            salt = base64.urlsafe_b64decode(salt_b64 + "=" * (-len(salt_b64) % 4))
            expected_digest = base64.urlsafe_b64decode(digest_b64 + "=" * (-len(digest_b64) % 4))
        except (ValueError, TypeError, binascii.Error):
            return False

        candidate_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.strip().encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(candidate_digest, expected_digest)

    return hmac.compare_digest(stored_password.strip(), password.strip())


def _is_password_hash(value: str) -> bool:
    return value.startswith(f"{_PASSWORD_SCHEME}$")


class AuthStore:
    """Accounts keyed by email. The Firestore document id is the normalized
    email, so lookups never need a query."""

    def __init__(self) -> None:
        self._memory: dict[str, dict[str, Any]] = {}
        self._db = get_firestore_client()
        self._mode = "firestore" if self._db is not None else "memory"
        self._collection_name = os.getenv("FIRESTORE_ACCOUNTS_COLLECTION", "accounts").strip() or "accounts"

    def _save(self, email: str, account: dict[str, Any]) -> None:
        if self._mode == "firestore" and self._db is not None:
            self._db.collection(self._collection_name).document(email).set(account)
        else:
            self._memory[email] = account

    def get_account(self, email: str) -> dict[str, Any] | None:
        normalized = _normalize_email(email)

        if self._mode == "firestore" and self._db is not None:
            try:
                doc = self._db.collection(self._collection_name).document(normalized).get()
                return doc.to_dict() if doc.exists else None
            except Exception:
                return None

        return self._memory.get(normalized)

    def login_account(self, email: str, password: str) -> dict[str, Any] | None:
        normalized = _normalize_email(email)
        account = self.get_account(normalized)

        if not account:
            return None

        stored_password = str(account.get("password", "")).strip()
        if not stored_password or not _verify_password(password, stored_password):
            return None

        if not _is_password_hash(stored_password):
            migrated_account = dict(account)
            migrated_account["password"] = _hash_password(password)
            migrated_account["updated_at"] = _utc_now()
            self._save(normalized, migrated_account)
            return migrated_account

        return account

    def upsert_account(self, payload: dict[str, Any]) -> dict[str, Any]:
        email = _normalize_email(str(payload.get("email", "")))
        existing = self.get_account(email)
        if existing:
            raise ValueError("Account already exists")

        now = _utc_now()
        account = {
            "id": email,
            "email": email,
            "display_name": str(payload.get("display_name", "")).strip(),
            "role": str(payload.get("role", "")).strip().lower(),
            "password": "",
            "provider": str(payload.get("provider", "google")).strip().lower(),
            "firebase_uid": str(payload.get("firebase_uid", "")).strip(),
            "created_at": now,
            "updated_at": now,
        }

        raw_password = str(payload.get("password", "")).strip()
        if raw_password:
            account["password"] = raw_password if _is_password_hash(raw_password) else _hash_password(raw_password)

        self._save(email, account)
        return account


auth_store = AuthStore()
