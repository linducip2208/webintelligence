import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from core.crypto import encrypt, decrypt  # noqa: E402


def test_roundtrip_plain():
    os.environ.pop("CREDENTIALS_KEY", None)
    import importlib
    import core.crypto as C
    importlib.reload(C)
    s = C.encrypt("hunter2")
    assert s != "hunter2" and C.decrypt(s) == "hunter2"
    assert C.decrypt("") == ""


def test_fernet_if_available():
    try:
        from cryptography.fernet import Fernet  # noqa
    except ImportError:
        return
    from cryptography.fernet import Fernet as F
    os.environ["CREDENTIALS_KEY"] = F.generate_key().decode()
    import importlib
    import core.crypto as C
    importlib.reload(C)
    s = C.encrypt("s3cr3t!")
    assert s.startswith("enc:") and C.decrypt(s) == "s3cr3t!"
    os.environ.pop("CREDENTIALS_KEY", None)
    importlib.reload(C)
