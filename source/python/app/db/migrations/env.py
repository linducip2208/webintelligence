"""Alembic env: runs Base.metadata.create_all as the initial migration path."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.db.base import Base  # noqa
from app.models import entities  # noqa: F401
from app.db.session import engine


def run():
    Base.metadata.create_all(bind=engine)
    print("migrations applied: create_all")


if __name__ == "__main__":
    run()
