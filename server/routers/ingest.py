# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""Ingest endpoints — accept data POSTed by the Pi-side ingestor."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, select

from ..database import get_session_dep
from ..models import Neighbor, Node, Packet
from ..routers.ws import manager
from ..schemas import IngestResult, NeighborIngest, PacketIngest

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])


def verify_api_key(x_api_key: str = Header(...)) -> None:
    """Validate the ``X-API-Key`` header against the configured secret.

    Args:
        x_api_key: Header value to validate.

    Raises:
        HTTPException: If the key does not match ``INGEST_API_KEY``.
    """
    expected = os.getenv("INGEST_API_KEY", "changeme")
    if x_api_key != expected:
        raise HTTPException(status_code=403, detail="Invalid API key")


def _upsert_node(session: Session, node_hash: str, data: dict) -> None:
    """Create or update a :class:`Node` record from ingested data.

    Args:
        session: Active database session.
        node_hash: 2-char hex prefix to look up.
        data: Dict of fields that may update the node record.
    """
    node = session.exec(select(Node).where(Node.node_hash == node_hash)).first()
    if not node:
        node = Node(node_hash=node_hash)
    node.last_seen = datetime.now(UTC)
    node.last_rssi = data.get("rssi", node.last_rssi)
    node.last_snr = data.get("snr", node.last_snr)
    if data.get("name"):
        node.name = data["name"]
    if data.get("lat") is not None:
        node.lat = data["lat"]
    if data.get("lon") is not None:
        node.lon = data["lon"]
    if data.get("node_type"):
        node.node_type = data["node_type"]
    session.add(node)


@router.post("/packets", dependencies=[Depends(verify_api_key)])
async def ingest_packets(
    packets: list[PacketIngest],
    session: Session = Depends(get_session_dep),
) -> IngestResult:
    """Receive a batch of packets from the ingestor and persist them.

    Duplicate packets (same ``packet_hash``) are silently skipped.
    New source nodes are auto-created via upsert.

    Args:
        packets: List of packet payloads from the ingestor.
        session: Injected database session.

    Returns:
        :class:`IngestResult` with the count of newly saved packets.
    """
    # Import here to avoid circular import at module level
    from ..bot.worker import event_queue  # noqa: WPS433

    saved: list[Packet] = []
    for pkt_in in packets:
        pkt_data = pkt_in.model_dump(exclude_none=True)

        # Dedup by packet_hash
        if pkt_data.get("packet_hash"):
            existing = session.exec(
                select(Packet).where(Packet.packet_hash == pkt_data["packet_hash"])
            ).first()
            if existing:
                continue

        packet = Packet(**{k: v for k, v in pkt_data.items() if hasattr(Packet, k)})
        session.add(packet)

        # Upsert originating node
        if pkt_data.get("source_hash"):
            _upsert_node(session, pkt_data["source_hash"], pkt_data)

        saved.append(packet)

    session.commit()

    # Broadcast each new packet over WebSocket and push to bot queue
    for packet in saved:
        packet_dict = packet.model_dump()
        # Convert datetime objects for JSON serialization
        for key, val in packet_dict.items():
            if isinstance(val, datetime):
                packet_dict[key] = val.isoformat()
        await manager.broadcast("packet", packet_dict)
        await event_queue.put({"type": "packet", "data": packet_dict})

    logger.info("Ingested %d new packets", len(saved))
    return IngestResult(saved=len(saved))


@router.post("/neighbors", dependencies=[Depends(verify_api_key)])
async def ingest_neighbors(
    neighbors: list[NeighborIngest],
    session: Session = Depends(get_session_dep),
) -> dict:
    """Receive a batch of neighbor observations from the ingestor.

    Args:
        neighbors: List of neighbor payloads from the ingestor.
        session: Injected database session.

    Returns:
        Simple ``{"ok": True}`` acknowledgement.
    """
    for nbr_in in neighbors:
        nbr_data = nbr_in.model_dump(exclude_none=True)
        neighbor_hash = nbr_data.get("neighbor_hash") or nbr_data.get("hash")
        if not neighbor_hash:
            continue

        neighbor = Neighbor(
            node_hash=nbr_data.get("node_hash", "local"),
            neighbor_hash=neighbor_hash,
            rssi=nbr_data.get("rssi"),
            snr=nbr_data.get("snr"),
        )
        session.add(neighbor)

        # Update / create node for this neighbor
        _upsert_node(session, neighbor_hash, nbr_data)

    session.commit()
    await manager.broadcast("neighbors_updated", {})
    return {"ok": True}
