# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""Pydantic I/O schemas for MeshCore Monitor API endpoints.

These are kept separate from the SQLModel table definitions so that the
public API surface can evolve independently of the database schema.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ------------------------------------------------------------------
# Ingest request schemas (from ingestor → server)
# ------------------------------------------------------------------


class PacketIngest(BaseModel):
    """Schema for a single packet submitted by the ingestor.

    Attributes:
        packet_hash: Deduplication key.
        packet_type: Packet classification string.
        route_type: ``FLOOD`` or ``DIRECT``.
        path: JSON-encoded list of hop prefixes.
        hop_count: Derived hop count.
        rssi: Received signal strength.
        snr: Signal-to-noise ratio.
        source_hash: Originator node prefix.
        dest_hash: Destination node prefix.
        payload_hex: Hex-encoded payload bytes.
        raw_json: Original Repeater JSON blob.
        received_at: Timestamp string (ISO-8601).
    """

    packet_hash: Optional[str] = None
    packet_type: str = "UNKNOWN"
    route_type: str = "UNKNOWN"
    path: Optional[str] = None
    hop_count: Optional[int] = None
    rssi: Optional[int] = None
    snr: Optional[float] = None
    source_hash: Optional[str] = None
    dest_hash: Optional[str] = None
    payload_hex: Optional[str] = None
    raw_json: Optional[str] = None
    received_at: Optional[str] = None


class NeighborIngest(BaseModel):
    """Schema for a single neighbor record submitted by the ingestor.

    Attributes:
        node_hash: Observing node (defaults to ``"local"``).
        neighbor_hash: Observed neighbor prefix.
        rssi: Signal strength.
        snr: Signal-to-noise ratio.
    """

    node_hash: str = "local"
    neighbor_hash: Optional[str] = None
    rssi: Optional[int] = None
    snr: Optional[float] = None

    # Allow alternative field names from the Repeater API.
    hash: Optional[str] = None


# ------------------------------------------------------------------
# API response schemas
# ------------------------------------------------------------------


class NodeResponse(BaseModel):
    """Public representation of a mesh node.

    Attributes:
        id: Database primary key.
        node_hash: 2-char hex prefix.
        name: Human-readable name.
        node_type: Node classification.
        lat: Latitude.
        lon: Longitude.
        last_rssi: Most recent RSSI.
        last_snr: Most recent SNR.
        first_seen: First observation timestamp.
        last_seen: Most recent observation timestamp.
        is_local: Whether this is the monitored repeater.
    """

    id: int
    node_hash: str
    name: Optional[str] = None
    node_type: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    last_rssi: Optional[int] = None
    last_snr: Optional[float] = None
    first_seen: datetime
    last_seen: datetime
    is_local: bool = False

    model_config = ConfigDict(from_attributes=True)


class PacketResponse(BaseModel):
    """Public representation of a received packet.

    Attributes:
        id: Database primary key.
        received_at: Reception timestamp.
        packet_hash: Deduplication key.
        packet_type: Packet classification.
        route_type: Routing method.
        path: JSON-encoded hop list.
        hop_count: Number of hops.
        rssi: Signal strength.
        snr: Signal-to-noise ratio.
        source_hash: Origin node.
        dest_hash: Destination node.
    """

    id: int
    received_at: datetime
    packet_hash: Optional[str] = None
    packet_type: str
    route_type: str
    path: Optional[str] = None
    hop_count: Optional[int] = None
    rssi: Optional[int] = None
    snr: Optional[float] = None
    source_hash: Optional[str] = None
    dest_hash: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BotRuleResponse(BaseModel):
    """Public representation of a bot automation rule.

    Attributes:
        id: Database primary key.
        name: Rule name.
        enabled: Active flag.
        trigger_type: Trigger classification.
        trigger_value: Trigger match value.
        action_type: Action classification.
        action_config: JSON action parameters.
        last_triggered: Last firing timestamp.
        trigger_count: Cumulative firing count.
    """

    id: int
    name: str
    enabled: bool
    trigger_type: str
    trigger_value: str
    action_type: str
    action_config: str
    last_triggered: Optional[datetime] = None
    trigger_count: int

    model_config = ConfigDict(from_attributes=True)


class BotRuleCreate(BaseModel):
    """Schema for creating or updating a bot rule.

    Attributes:
        name: Rule name.
        enabled: Active flag.
        trigger_type: Trigger classification.
        trigger_value: Trigger match value.
        action_type: Action classification.
        action_config: JSON action parameters.
    """

    name: str
    enabled: bool = True
    trigger_type: str
    trigger_value: str
    action_type: str
    action_config: str = "{}"


class IngestResult(BaseModel):
    """Response returned by ingest endpoints.

    Attributes:
        saved: Number of records persisted.
    """

    saved: int
