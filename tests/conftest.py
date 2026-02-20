# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""Shared pytest fixtures for MeshCore Monitor tests."""

import os

# Configure environment *before* any server imports
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["INGEST_API_KEY"] = "testkey"
os.environ["BOT_ENABLED"] = "false"

import pytest  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

import server.models  # noqa: E402, F401  — ensure models are registered
from fastapi.testclient import TestClient  # noqa: E402
from server.main import app  # noqa: E402
import server.database as db_module  # noqa: E402

# Override the module-level engine with one that uses StaticPool so the
# in-memory SQLite database is shared across all connections.
_test_engine = create_engine(
    "sqlite://",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
db_module.engine = _test_engine


@pytest.fixture(autouse=True)
def _reset_database():
    """Create a fresh schema before each test and drop afterwards."""
    SQLModel.metadata.create_all(_test_engine)
    yield
    SQLModel.metadata.drop_all(_test_engine)


@pytest.fixture()
def client():
    """Return a :class:`TestClient` wired to the FastAPI app.

    Returns:
        A ``TestClient`` instance.
    """
    return TestClient(app)


@pytest.fixture()
def auth_headers():
    """Return headers with a valid ingest API key.

    Returns:
        Dict suitable for passing as ``headers=`` to ``TestClient``.
    """
    return {"X-API-Key": "testkey"}
