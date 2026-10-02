"""Unit tests — stdlib only (no fastapi/sqlalchemy/redis needed)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
