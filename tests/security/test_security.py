import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python", "app"))

from core.ssrf import validate_url, SSRFError  # noqa
from core.security import hash_password, verify_password  # noqa


def test_injection_strings_rejected_as_urls():
    for bad in ["javascript:alert(1)", "file:///etc/passwd", "gopher://x/", "http://[::1]/"]:
        try:
            validate_url(bad)
            assert False, bad
        except (SSRFError, ValueError):
            pass


def test_password_roundtrip():
    h = hash_password("s3cret!")
    assert verify_password("s3cret!", h)
    assert not verify_password("wrong", h)
