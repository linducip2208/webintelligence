"""Secret encryption at rest: Fernet when CREDENTIALS_KEY is set, else
plaintext with a one-time warning (honest, never silent). stdlib + cryptography."""
import base64
import os

_warned = False


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return None
    key = os.getenv("CREDENTIALS_KEY", "")
    if not key:
        return None
    raw = key.encode()
    if len(raw) == 44:
        token = raw
    else:
        token = base64.urlsafe_b64encode(raw.ljust(32, b"\0")[:32])
    try:
        return Fernet(token)
    except Exception:
        return None


def encrypt(plaintext: str) -> str:
    global _warned
    f = _fernet()
    if f is None:
        if not _warned:
            _warned = True
            from .logging import log
            log("crypto-plaintext", warning="CREDENTIALS_KEY unset or cryptography missing")
        return "plain:" + (plaintext or "")
    return "enc:" + f.encrypt((plaintext or "").encode()).decode()


def decrypt(stored: str) -> str:
    if not stored:
        return ""
    if stored.startswith("plain:"):
        return stored[6:]
    if stored.startswith("enc:"):
        f = _fernet()
        if f is None:
            raise RuntimeError("encrypted secret but no CREDENTIALS_KEY available")
        return f.decrypt(stored[4:].encode()).decode()
    return stored  # legacy plaintext
