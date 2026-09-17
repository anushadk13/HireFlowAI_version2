from __future__ import annotations
import base64
import binascii
import hashlib
import os
import hmac
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PASSWORD_SCHEME = "pbkdf2_sha256"
_PASSWORD_ITERATIONS = 310_000
_PASSWORD_SALT_BYTES = 16


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


def _set_account(account: dict[str, Any]) -> None:
    email = str(account.get("email", "")).strip().lower()
    if not email:
        return

    if auth_store._mode == "cosmos" and auth_store._container is not None:
        auth_store._container.upsert_item(account)
    else:
        auth_store._memory[email] = account


class AuthStore:
    def __init__(self) -> None:
        self._mode = "memory"
        self._memory: dict[str, dict[str, Any]] = {}
        self._container = None

        endpoint = os.getenv("COSMOS_ENDPOINT", "").strip()
        key = os.getenv("COSMOS_KEY", "").strip()
        database_name = os.getenv("COSMOS_DATABASE", "hireflow-ai").strip()
        container_name = os.getenv("COSMOS_CONTAINER", "accounts").strip()
        partition_key_path = os.getenv("COSMOS_PARTITION_KEY_PATH", "/a3189094").strip() or "/a3189094"
        self._partition_key_path = partition_key_path
        self._partition_key_name = partition_key_path.lstrip("/")

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
                partition_key=PartitionKey(path=partition_key_path),
            )
            self._mode = "cosmos"
        except Exception:
            self._container = None

    def _partition_value(self, email: str, payload: dict[str, Any] | None = None) -> str:
        if payload is not None:
            value = payload.get(self._partition_key_name, "")
            if value:
                return str(value)
        return email

    def get_account(self, email: str) -> dict[str, Any] | None:
        normalized = _normalize_email(email)

        if self._mode == "cosmos" and self._container is not None:
            try:
                query = "SELECT * FROM c WHERE c.email = @email"
                items = list(
                    self._container.query_items(
                        query=query,
                        parameters=[{"name": "@email", "value": normalized}],
                        partition_key=self._partition_value(normalized),
                    )
                )
                if items:
                    return items[0]
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
            _set_account(migrated_account)
            return migrated_account

        return account

    def upsert_account(self, payload: dict[str, Any]) -> dict[str, Any]:
        email = _normalize_email(str(payload.get("email", "")))
        existing = self.get_account(email)
        if existing:
            raise ValueError("Account already exists")

        now = _utc_now()
        partition_value = self._partition_value(email, payload)
        account = {
            "id": email,
            "email": email,
            "display_name": str(payload.get("display_name", "")).strip(),
            "role": str(payload.get("role", "")).strip().lower(),
            "password": "",
            "provider": str(payload.get("provider", "google")).strip().lower(),
            "firebase_uid": str(payload.get("firebase_uid", "")).strip(),
            self._partition_key_name: partition_value,
            "created_at": now,
            "updated_at": now,
        }

        raw_password = str(payload.get("password", "")).strip()
        if raw_password:
            account["password"] = raw_password if _is_password_hash(raw_password) else _hash_password(raw_password)

        if self._mode == "cosmos" and self._container is not None:
            self._container.upsert_item(account)
        else:
            self._memory[email] = account

        return account


auth_store = AuthStore()
