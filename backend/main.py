from __future__ import annotations
import logging
import os
from typing import Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.routers.health import router as health_router
from backend.routers.auth import router as auth_router
from backend.routers.hr import router as hr_router
from backend.routers.resume import router as resume_router

logger = logging.getLogger(__name__)

app = FastAPI(title="HireFlow AI", version="1.0.0")

_DEFAULT_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
# Comma-separated list of deployed frontend origins, e.g. https://hireflow.vercel.app
_EXTRA_ORIGINS = [o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_DEFAULT_ORIGINS + _EXTRA_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(hr_router)


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never echo the raw exception back to the client: it can contain secrets
    # (e.g. an API key embedded in a third-party SDK's error message). Log the
    # detail server-side instead, where it's actually needed for debugging.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse({"detail": "Internal server error"}, status_code=500)
