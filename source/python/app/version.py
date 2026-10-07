"""Canonical application version — the single source of truth.

Every component reads this: FastAPI app, /healthz, /api/version, footer,
docs portal, diagnostics. Static files (pyproject, openapi.yaml, README
title) mirror it and are pinned by test_version_consistency.
"""
APP_VERSION = "2.14.0"
