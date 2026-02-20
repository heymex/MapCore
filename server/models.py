# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""SQLModel table definitions for MeshCore Monitor.

Each class maps to a SQLite table and doubles as a Pydantic model for
serialization.  Fields are intentionally nullable to accommodate the
varied data pyMC_Repeater may return at different times.
"""

from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(UTC)


class Node(SQLModel, table=True):
    """A mesh node identified by its 2-char hex prefix (``node_hash``).

    Attributes:
        node_hash: 2-char hex prefix extracted from packet paths.
        public_key: Full public key when seen in an advert.
        name: Human-readable name from advert payload.
        node_type: One of ``"repeater"``, ``"companion"``, ``"room_server"``.
        lat: Latitude from tracked advert.
        lon: Longitude from tracked advert.
        last_rssi: Most recent RSSI reading (dBm).
        last_snr: Most recent SNR reading.
        first_seen: Timestamp of first observation.
        last_seen: Timestamp of most recent observation.
        is_local: ``True`` for the monitored repeater node itself.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    node_hash: str = Field(index=True, unique=True)
    public_key: Optional[str] = None
    name: Optional[str] = None
    node_type: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    last_rssi: Optional[int] = None
    last_snr: Optional[float] = None
    first_seen: datetime = Field(default_factory=_utcnow)
    last_seen: datetime = Field(default_factory=_utcnow)
    is_local: bool = False


class Packet(SQLModel, table=True):
    """A single packet received from the mesh network.

    Attributes:
        packet_hash: Unique deduplication key from the Repeater.
        packet_type: e.g. ``ADVERT``, ``TXT_MSG``, ``ACK``, ``TRACE``.
        route_type: ``FLOOD`` or ``DIRECT``.
        payload_hex: Hex-encoded payload (encrypted for most message types).
        path: JSON-encoded list of 2-char hex node prefixes.
        hop_count: Number of hops in the path.
        rssi: Signal strength (dBm).
        snr: Signal-to-noise ratio.
        source_hash: Originator node hash.
        dest_hash: Destination node hash (if direct).
        raw_json: Full API response blob for future parsing.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    received_at: datetime = Field(default_factory=_utcnow)
    packet_hash: Optional[str] = Field(default=None, index=True)
    packet_type: str = "UNKNOWN"
    route_type: str = "UNKNOWN"
    payload_hex: Optional[str] = None
    path: Optional[str] = None
    hop_count: Optional[int] = None
    rssi: Optional[int] = None
    snr: Optional[float] = None
    source_hash: Optional[str] = Field(default=None, index=True)
    dest_hash: Optional[str] = None
    raw_json: Optional[str] = None


class Telemetry(SQLModel, table=True):
    """Time-series telemetry snapshot for a single node.

    Attributes:
        node_hash: Foreign reference to :class:`Node.node_hash`.
        battery_pct: Battery percentage.
        voltage: Battery voltage.
        temperature: Ambient temperature (°C).
        humidity: Relative humidity (%).
        pressure: Barometric pressure (hPa).
        uptime_seconds: Device uptime.
        tx_count: Cumulative transmit count.
        rx_count: Cumulative receive count.
        raw_json: Full telemetry blob.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    node_hash: str = Field(index=True)
    recorded_at: datetime = Field(default_factory=_utcnow)
    battery_pct: Optional[float] = None
    voltage: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    uptime_seconds: Optional[int] = None
    tx_count: Optional[int] = None
    rx_count: Optional[int] = None
    raw_json: Optional[str] = None


class Neighbor(SQLModel, table=True):
    """A directional neighbor observation (node A heard node B).

    Attributes:
        node_hash: The observing node.
        neighbor_hash: The observed neighbor.
        rssi: Signal strength of the observation.
        snr: Signal-to-noise ratio.
        observation_count: Running tally of how often this edge is seen.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    observed_at: datetime = Field(default_factory=_utcnow)
    node_hash: str = Field(index=True)
    neighbor_hash: str = Field(index=True)
    rssi: Optional[int] = None
    snr: Optional[float] = None
    observation_count: int = 1


class BotRule(SQLModel, table=True):
    """A configurable bot automation rule.

    Attributes:
        name: Human-readable rule name.
        enabled: Whether the rule is active.
        trigger_type: One of ``"packet_type"``, ``"keyword"``, ``"node_seen"``,
            ``"schedule"``.
        trigger_value: Value to match against (e.g. ``"ADVERT"``, ``"ping"``).
        action_type: One of ``"send_message"``, ``"log"``, ``"webhook"``,
            ``"telemetry_request"``.
        action_config: JSON blob of action parameters.
        last_triggered: Timestamp of last rule firing.
        trigger_count: Cumulative trigger count.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    enabled: bool = True
    trigger_type: str
    trigger_value: str
    action_type: str
    action_config: str = "{}"
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
