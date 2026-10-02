"""Data quality — stdlib only."""
def score(record: dict, required: list, fresh_hours=None, age_hours=None):
    required = required or []
    comp = sum(1 for f in required if record.get(f) not in (None, "")) / len(required) if required else 1.0
    valid = 1.0 if all(isinstance(record.get(f), (str, int, float)) or record.get(f) is None for f in required) else 0.6
    fresh = 1.0
    if fresh_hours is not None and age_hours is not None:
        fresh = 1.0 if age_hours <= fresh_hours else max(0.0, 1 - (age_hours - fresh_hours) / fresh_hours)
    schema = 1.0 if not record.get("_schema_errors") else 0.5
    overall = round(0.4*comp + 0.25*valid + 0.2*fresh + 0.15*schema, 3)
    return {"completeness": round(comp,3), "validity": valid, "freshness": round(fresh,3),
            "schema_conformity": schema, "overall": overall}
