"""Version consistency gate (repo layout wrapper).

The implementation lives with the backend suite; this wrapper runs the same
checks from the root unit-test target (see Makefile).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "..", "source", "python"))

from tests.test_version_consistency import (  # noqa: E402,F401
    test_version_consistency,
    test_no_stale_version_literals,
)
