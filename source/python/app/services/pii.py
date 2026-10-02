"""PII detection + masking (emails, phones, national IDs, API-looking tokens).
Applied at ingest (findings stored in metadata) and on export (?mask_pii=1).
Heuristic, labeled as such — never presented as certified redaction.
"""
import re

PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "phone": re.compile(r"\+?\d[\d\s\-().]{7,}\d"),
    "nik_like": re.compile(r"\b\d{16}\b"),
    "token_like": re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"),
}


def detect(text: str):
    found = {}
    for kind, rx in PATTERNS.items():
        hits = sorted(set(rx.findall(text or "")))
        if hits:
            found[kind] = hits[:20]
    return found


def mask(text: str):
    out = text or ""
    for rx in PATTERNS.values():
        out = rx.sub("[REDACTED]", out)
    return out
