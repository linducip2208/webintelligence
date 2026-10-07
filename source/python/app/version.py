"""Canonical application version — the single source of truth.

Every component reads this: FastAPI app, /healthz, /api/version, footer,
docs portal, diagnostics. Static files (pyproject, openapi.yaml, README
title) mirror it and are pinned by test_version_consistency.
"""
import os as _os

APP_NAME = "webintel"
APP_VERSION = "2.14.0"
API_VERSION = "v1"
RELEASE_CHANNEL = _os.getenv("ENV", "dev")


def _build_id():
    for var in ("BUILD_ID", "GIT_SHA", "GITHUB_SHA"):
        v = (_os.getenv(var) or "").strip()
        if v:
            return v[:12]
    return "dev"


BUILD_ID = _build_id()
