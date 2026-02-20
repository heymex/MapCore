# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""REST endpoints for querying received packets."""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..database import get_session_dep
from ..models import Packet

router = APIRouter(tags=["packets"])


@router.get("/packets")
def get_packets(
    limit: int = 100,
    packet_type: Optional[str] = None,
    source_hash: Optional[str] = None,
    session: Session = Depends(get_session_dep),
) -> list[Packet]:
    """Return received packets with optional filters.

    Args:
        limit: Maximum number of packets to return (default 100).
        packet_type: Filter by packet type (e.g. ``"ADVERT"``).
        source_hash: Filter by originating node hash.
        session: Injected database session.

    Returns:
        List of :class:`Packet` records, newest first.
    """
    query = select(Packet).order_by(Packet.received_at.desc()).limit(limit)
    if packet_type:
        query = query.where(Packet.packet_type == packet_type)
    if source_hash:
        query = query.where(Packet.source_hash == source_hash)
    return list(session.exec(query).all())
