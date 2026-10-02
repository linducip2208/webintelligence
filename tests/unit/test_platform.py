import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "source", "python", "app"))

from core.ssrf import validate_url, SSRFError  # noqa


def test_ssrf_localhost_blocked():
    try:
        validate_url("http://localhost/admin")
        assert False
    except SSRFError:
        pass


def test_ssrf_public_ok():
    assert validate_url("https://example.com/a") is True


def test_ssrf_metadata_blocked():
    try:
        validate_url("http://169.254.169.254/latest/meta-data/")
        assert False
    except SSRFError:
        pass
