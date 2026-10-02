import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.db.repo import Repo, resolve_engine  # noqa: E402


def test_production_rejects_sqlite():
    try:
        resolve_engine("sqlite:///./x.db", "production")
        assert False, "must fail closed"
    except RuntimeError as e:
        assert "MySQL" in str(e) and "silent" in str(e)


def test_production_unreachable_mysql_fails_clearly():
    r = Repo(url="mysql://u:p@127.0.0.1:1/db", env="production")
    assert r.available is False and r.backend == "unavailable"
    assert "db-unavailable" in r.boot_error
    try:
        r.add("projects", {"name": "x"})
        assert False, "writes must not disappear silently"
    except RuntimeError as e:
        assert "db-unavailable" in str(e)


def test_production_repo_unavailable_flag():
    r = Repo.__new__(Repo)
    r.available = False
    r.boot_error = "db-unavailable: down"
    r.backend = "unavailable"
    try:
        r.add("projects", {"name": "x"})
        assert False
    except RuntimeError as e:
        assert "db-unavailable" in str(e)


def test_development_memory_works():
    r = Repo(url="sqlite:///:memory:")
    assert r.available and r.backend == "memory"
    r.add("projects", {"id": 1, "name": "P", "description": ""})
    assert r.load_all()["projects"] == [{"id": 1, "name": "P", "description": ""}]
