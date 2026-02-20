# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""REST endpoints for querying node telemetry data."""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..database import get_session_dep
from ..models import Telemetry

router = APIRouter(tags=["telemetry"])


@router.get("/telemetry")
def get_telemetry(
    node_hash: Optional[str] = None,
    limit: int = 100,
    session: Session = Depends(get_session_dep),
) -> list[Telemetry]:
    """Return telemetry snapshots, optionally filtered by node.

    Args:
        node_hash: Filter to a specific node.
        limit: Maximum number of records to return (default 100).
        session: Injected database session.

    Returns:
        List of :class:`Telemetry` records, newest first.
    """
    query = select(Telemetry).order_by(Telemetry.recorded_at.desc()).limit(limit)
    if node_hash:
        query = query.where(Telemetry.node_hash == node_hash)
    return list(session.exec(query).all())
