"""Hermetic tests: force in-memory DB before app modules are imported."""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
