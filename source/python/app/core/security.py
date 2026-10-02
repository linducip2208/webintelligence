import hashlib, hmac, secrets
try:
    from passlib.context import CryptContext
    _ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def hash_password(pw: str) -> str: return _ctx.hash(pw)
    def verify_password(pw: str, h: str) -> bool: return _ctx.verify(pw, h)
except Exception:
    def hash_password(pw: str) -> str: return "sha256$" + hashlib.sha256(pw.encode()).hexdigest()
    def verify_password(pw: str, h: str) -> bool: return hmac.compare_digest(h, hash_password(pw))
def new_token(n=32) -> str: return secrets.token_urlsafe(n)
def redact(s: str) -> str:
    if not s: return ""
    return (s[:2] + "***" + s[-2:]) if len(s) > 6 else "***"
