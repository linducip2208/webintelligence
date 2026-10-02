"""Document intelligence: metadata/text/chunk/fingerprint — stdlib.
PDF/DOCX need optional libs; without them extraction reports honestly
extracted=False instead of faking content.
"""
import hashlib, re, json
def fingerprint(content: bytes) -> str: return hashlib.sha256(content or b"").hexdigest()
def strip_html(html: str) -> str:
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>|<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", t).strip()
def extract(kind: str, content: bytes, filename=""):
    meta = {"filename": filename, "kind": kind, "size": len(content or b"")}
    k = (kind or "").lower()
    if k in ("txt", "csv", "json", "xml"):
        try: text = (content or b"").decode("utf-8", "ignore")
        except Exception: text = ""
        return {"extracted": True, "text": text[:200000], "meta": meta, "tables": []}
    if k == "html":
        return {"extracted": True, "text": strip_html((content or b"").decode("utf-8", "ignore"))[:200000], "meta": meta, "tables": []}
    if k == "pdf":
        try:
            from pypdf import PdfReader
            import io as _io
            r = PdfReader(_io.BytesIO(content))
            text = "\\n".join((p.extract_text() or "") for p in r.pages)[:200000]
            meta["pages"] = len(r.pages)
            return {"extracted": True, "text": text, "meta": meta, "tables": []}
        except ImportError:
            return {"extracted": False, "reason": "pypdf not installed", "meta": meta}
        except Exception as e:
            return {"extracted": False, "reason": f"pdf parse failed: {e}"[:200], "meta": meta}
    return {"extracted": False, "reason": f"no extractor for {kind}", "meta": meta}
def chunk(text: str, size=800, overlap=100):
    out, i = [], 0
    while i < len(text or ""):
        out.append(text[i:i+size]); i += size - overlap
    return out
