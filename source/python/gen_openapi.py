"""Regenerate contracts/openapi/openapi.json from the FastAPI app. Run from repo root:
python source/python/gen_openapi.py"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.main import app
out = os.path.join(os.path.dirname(__file__), "..", "..", "contracts", "openapi", "openapi.json")
spec = app.openapi()
json.dump(spec, open(out, "w"), indent=1)
print("wrote", out, "paths:", len(spec.get("paths", {})))
