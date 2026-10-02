"""Alembic env: models are the single source of truth.

Usage (with MySQL running + .env DATABASE_URL set):
    cd source/python
    python -m app.db.migrations.env
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from app.db.base import Base  # noqa: E402
from app.models import entities  # noqa: F401,E402
from app.db.session import engine  # noqa: E402


def run():
    Base.metadata.create_all(bind=engine)
    print("migrations applied: create_all (%d tables)" % len(Base.metadata.tables))


if __name__ == "__main__":
    run()
