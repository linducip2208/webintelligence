"""White-label branding validation + vertical intelligence templates.
Templates are pure configuration over the universal engine (no forks)."""
import re

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def validate_branding(b: dict):
    errs = []
    if not isinstance(b, dict):
        return ["branding must be an object"]
    if "primary_color" in b and not HEX.match(str(b["primary_color"] or "")):
        errs.append("primary_color must be #rrggbb")
    for k in ("logo_url", "favicon_url"):
        if k in b and b[k]:
            u = str(b[k])
            if not (u.startswith("https://") or u.startswith("/static/")):
                errs.append(f"{k} must be https:// or /static/ path")
    if "app_name" in b and len(str(b["app_name"])) > 60:
        errs.append("app_name too long")
    return errs


VERTICALS = {
    "market": {"entities": ["company", "product"], "relationships": ["COMPETES_WITH", "OWNS"],
               "kpis": ["avg_price", "volatility"], "events": ["PRICE_CHANGED"],
               "watch": [{"kind": "keyword", "value": "market"}],
               "questions": ["Which companies entered this market?"]},
    "competitive": {"entities": ["company", "product", "brand"],
                    "relationships": ["COMPETES_WITH"], "kpis": ["price_gap"],
                    "events": ["PRICE_CHANGED", "PRODUCT_ADDED"],
                    "watch": [{"kind": "keyword", "value": "competitor"}],
                    "questions": ["Show competitors with similar pricing."]},
    "pricing": {"entities": ["product"], "relationships": ["HAS_PRICE"],
                "kpis": ["avg_price", "min_price", "max_price"],
                "events": ["PRICE_CHANGED"], "watch": [{"kind": "keyword", "value": "price"}],
                "questions": ["What products increased in price this month?"]},
    "procurement": {"entities": ["company", "product"], "relationships": ["SELLS"],
                    "kpis": ["min_price"], "events": ["PRICE_CHANGED", "PRODUCT_ADDED"],
                    "watch": [{"kind": "keyword", "value": "supplier"}],
                    "questions": ["Which suppliers dropped prices?"]},
    "supply_chain": {"entities": ["company", "location"], "relationships": ["OPERATES"],
                     "kpis": ["availability"], "events": ["AVAILABILITY_CHANGED"],
                     "watch": [{"kind": "keyword", "value": "supply"}],
                     "questions": ["What changed on supplier websites?"]},
    "ecommerce": {"entities": ["product", "brand"], "relationships": ["BELONGS_TO"],
                  "kpis": ["avg_price", "review_volume"], "events": ["PRICE_CHANGED"],
                  "watch": [{"kind": "keyword", "value": "launch"}],
                  "questions": ["What products increased in price this month?"]},
    "brand": {"entities": ["brand", "company"], "relationships": ["OWNS"],
              "kpis": ["sentiment"], "events": ["CONTENT_CHANGED"],
              "watch": [{"kind": "keyword", "value": "brand"}],
              "questions": ["What are recurring complaints?"]},
    "investment": {"entities": ["company", "person"], "relationships": ["WORKS_FOR"],
                   "kpis": ["growth"], "events": ["COMPANY_CHANGED", "PERSON_ADDED"],
                   "watch": [{"kind": "keyword", "value": "funding"}],
                   "questions": ["Which companies entered this market?"]},
    "real_estate": {"entities": ["location", "company"], "relationships": ["LOCATED_IN"],
                    "kpis": ["avg_price"], "events": ["PRICE_CHANGED"],
                    "watch": [{"kind": "keyword", "value": "property"}],
                    "questions": ["What changed in this market?"]},
    "regulatory": {"entities": ["company", "document"], "relationships": ["MENTIONS"],
                   "kpis": ["policy_events"], "events": ["POLICY_CHANGED"],
                   "watch": [{"kind": "keyword", "value": "regulation"}],
                   "questions": ["What policies changed?"]},
}


def get_vertical(name: str):
    return VERTICALS.get((name or "").lower())
