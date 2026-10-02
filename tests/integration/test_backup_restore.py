"""Backup/restore procedure test on SQLite: snapshot file, mutate, restore,
verify exact state. Mirrors deploy/scripts/backup.sh + restore.sh logic."""
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))

from sqlalchemy import create_engine  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.repo import Repo  # noqa: E402


def test_backup_restore_roundtrip(tmp_path):
    live = str(tmp_path / "live.db")
    bak = str(tmp_path / "live.db.bak")
    r1 = Repo(engine=create_engine(f"sqlite:///{live}", future=True))
    r1.add("projects", {"id": 1, "name": "KeepMe", "description": ""})
    r1.add("prices", {"product_id": 1, "price": 42.0, "currency": "USD",
                      "observed_at": 1.0, "job_id": "j"})
    assert r1.load_all()["projects"][0]["name"] == "KeepMe"
    # backup = file copy (same as backup.sh data.tar.gz step for sqlite)
    shutil.copyfile(live, bak)
    # mutate after backup
    r1.add("projects", {"id": 2, "name": "AfterBackup", "description": ""})
    assert len(r1.load_all()["projects"]) == 2
    # restore = copy back + fresh engine (simulates process restart)
    shutil.copyfile(bak, live)
    r2 = Repo(engine=create_engine(f"sqlite:///{live}", future=True))
    names = [p["name"] for p in r2.load_all()["projects"]]
    assert names == ["KeepMe"], names
    assert r2.load_all()["prices"][0]["price"] == 42.0
