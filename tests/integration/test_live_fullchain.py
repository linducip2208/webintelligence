"""Gated LIVE test: real uvicorn + real Go binary + real RESP (MiniRedis).

Run: LIVE_FULLCHAIN=1 python -m pytest tests/integration/test_live_fullchain.py
Skipped by default (spawns processes, ~60-120s).
"""
import os
import sys

import pytest

pytestmark = pytest.mark.skipif(not os.getenv("LIVE_FULLCHAIN"),
                               reason="set LIVE_FULLCHAIN=1 for the live chain")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from live_fullchain import run_chain  # noqa: E402


def test_live_fullchain():
    out = run_chain(timeout_s=75)
    assert out["price_points"] >= 1
    assert os.path.exists(out["db"])
