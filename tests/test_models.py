# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""Tests for SQLModel table definitions and basic ORM operations."""

from datetime import datetime

from sqlmodel import Session, select

from server.database import engine
from server.models import BotRule, Neighbor, Node, Packet, Telemetry


class TestNodeModel:
    """Tests for the :class:`Node` model."""

    def test_create_node(self):
        """A node can be created and retrieved by hash."""
        with Session(engine) as session:
            node = Node(node_hash="AB", name="TestNode")
            session.add(node)
            session.commit()

            result = session.exec(select(Node).where(Node.node_hash == "AB")).first()
            assert result is not None
            assert result.name == "TestNode"
            assert result.is_local is False

    def test_node_defaults(self):
        """Default values should be applied correctly."""
        node = Node(node_hash="CD")
        assert node.is_local is False
        assert node.lat is None
        assert node.lon is None


class TestPacketModel:
    """Tests for the :class:`Packet` model."""

    def test_create_packet(self):
        """A packet can be persisted and retrieved."""
        with Session(engine) as session:
            pkt = Packet(
                packet_hash="pkt001",
                packet_type="ADVERT",
                route_type="FLOOD",
                rssi=-85,
                snr=7.5,
                source_hash="FA",
            )
            session.add(pkt)
            session.commit()

            result = session.exec(
                select(Packet).where(Packet.packet_hash == "pkt001")
            ).first()
            assert result is not None
            assert result.packet_type == "ADVERT"
            assert result.rssi == -85

    def test_packet_defaults(self):
        """Default values should be applied correctly."""
        pkt = Packet()
        assert pkt.packet_type == "UNKNOWN"
        assert pkt.route_type == "UNKNOWN"
        assert pkt.packet_hash is None


class TestTelemetryModel:
    """Tests for the :class:`Telemetry` model."""

    def test_create_telemetry(self):
        """A telemetry snapshot can be persisted."""
        with Session(engine) as session:
            tel = Telemetry(
                node_hash="EF",
                battery_pct=85.0,
                voltage=3.7,
                temperature=22.5,
            )
            session.add(tel)
            session.commit()

            result = session.exec(
                select(Telemetry).where(Telemetry.node_hash == "EF")
            ).first()
            assert result is not None
            assert result.battery_pct == 85.0


class TestNeighborModel:
    """Tests for the :class:`Neighbor` model."""

    def test_create_neighbor(self):
        """A neighbor observation can be persisted."""
        with Session(engine) as session:
            nbr = Neighbor(
                node_hash="GH",
                neighbor_hash="IJ",
                rssi=-75,
                snr=9.0,
            )
            session.add(nbr)
            session.commit()

            result = session.exec(
                select(Neighbor).where(Neighbor.neighbor_hash == "IJ")
            ).first()
            assert result is not None
            assert result.observation_count == 1


class TestBotRuleModel:
    """Tests for the :class:`BotRule` model."""

    def test_create_bot_rule(self):
        """A bot rule can be persisted with default values."""
        with Session(engine) as session:
            rule = BotRule(
                name="Test Rule",
                trigger_type="packet_type",
                trigger_value="ADVERT",
                action_type="log",
            )
            session.add(rule)
            session.commit()

            result = session.exec(
                select(BotRule).where(BotRule.name == "Test Rule")
            ).first()
            assert result is not None
            assert result.enabled is True
            assert result.trigger_count == 0
            assert result.last_triggered is None
