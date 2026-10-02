"""Connector registry: manifest validation + capability match — stdlib."""
REQUIRED = ("name", "category", "version", "capabilities")
CATEGORIES = ("WEB","API","DOCUMENT","DATABASE","CLOUD","NEWS","ECOMMERCE","GOVERNMENT",
              "JOBS","REAL_ESTATE","FINANCE","SOCIAL","CUSTOM")
def validate_manifest(m: dict):
    errs = [f"missing {k}" for k in REQUIRED if not m.get(k)]
    if m.get("category") not in CATEGORIES: errs.append(f"bad category {m.get('category')}")
    if not isinstance(m.get("capabilities", []), list): errs.append("capabilities must be list")
    return errs
def match(connectors: list, need: str, category: str = ""):
    return [c for c in connectors
            if need in (c.get("manifest", {}).get("capabilities", []))
            and (not category or c.get("category") == category) and c.get("enabled")]
