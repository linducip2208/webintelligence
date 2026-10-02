"""Integration tests — live-gated: skip when MySQL/Redis/creds absent."""
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") and not os.getenv("REDIS_URL"),
    reason="no live services configured",
)


def test_placeholder_live():
    assert True
