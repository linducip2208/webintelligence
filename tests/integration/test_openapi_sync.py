"""OpenAPI sync: committed openapi.json must match the app's route set."""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from app.main import app  # noqa: E402


def test_openapi_in_sync():
    p = os.path.join(os.path.dirname(__file__), "..", "..", "contracts", "openapi", "openapi.json")
    committed = json.load(open(p))
    live = app.openapi()
    assert set(committed["paths"]) == set(live["paths"]), (
        "regenerate: python source/python/gen_openapi.py")
    assert len(live["paths"]) >= 70
