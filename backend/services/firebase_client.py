from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


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

_firestore_client = None
_storage_bucket = None
_initialized = False


def _initialize() -> None:
    """Lazily boot the Firebase Admin app once per process and cache the
    Firestore client / Storage bucket handles for every store to share."""
    global _firestore_client, _storage_bucket, _initialized

    if _initialized:
        return
    _initialized = True

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    service_account_path = (
        os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    )
    storage_bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "").strip()

    if not service_account_json and not service_account_path:
        return

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage
    except Exception:
        logger.warning("firebase-admin is not installed; Firebase persistence is disabled.")
        return

    try:
        if not firebase_admin._apps:
            credential = (
                credentials.Certificate(json.loads(service_account_json))
                if service_account_json
                else credentials.Certificate(service_account_path)
            )
            options = {"storageBucket": storage_bucket_name} if storage_bucket_name else {}
            firebase_admin.initialize_app(credential, options)

        _firestore_client = firestore.client()
        if storage_bucket_name:
            _storage_bucket = storage.bucket()
    except Exception as exc:  # noqa: BLE001 - a bad config must never crash the app at import time
        logger.warning("Failed to initialize Firebase: %s", exc)
        _firestore_client = None
        _storage_bucket = None


def get_firestore_client():
    """Return the shared Firestore client, or None if Firebase isn't configured."""
    _initialize()
    return _firestore_client


def get_storage_bucket():
    """Return the shared Firebase Storage bucket, or None if it isn't configured."""
    _initialize()
    return _storage_bucket
