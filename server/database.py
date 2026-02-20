# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""Database engine and session helpers for MeshCore Monitor."""

import os
from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./meshcore_monitor.db")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)


def create_db() -> None:
    """Create all tables defined in :mod:`server.models`."""
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yield a database session that auto-closes on exit.

    Yields:
        A :class:`sqlmodel.Session` bound to the module-level engine.
    """
    with Session(engine) as session:
        yield session


def get_session_dep() -> Generator[Session, None, None]:
    """FastAPI-compatible dependency that yields a session.

    Yields:
        A :class:`sqlmodel.Session` for use in route handlers.
    """
    with Session(engine) as session:
        yield session
