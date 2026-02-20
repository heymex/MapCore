# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""Tests for the ingest router — packet and neighbor ingestion."""

import pytest
from fastapi.testclient import TestClient


class TestIngestPackets:
    """Tests for ``POST /ingest/packets``."""

    def test_ingest_single_packet(self, client: TestClient, auth_headers: dict):
        """A single valid packet should be saved and returned."""
        resp = client.post(
            "/ingest/packets",
            json=[
                {
                    "packet_hash": "abc123",
                    "packet_type": "ADVERT",
                    "route_type": "FLOOD",
                    "path": '["FA","79"]',
                    "hop_count": 2,
                    "rssi": -85,
                    "snr": 7.5,
                    "source_hash": "FA",
                }
            ],
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["saved"] == 1

    def test_dedup_packets(self, client: TestClient, auth_headers: dict):
        """Duplicate packet_hash values should be silently skipped."""
        payload = [
            {
                "packet_hash": "dup999",
                "packet_type": "ADVERT",
                "route_type": "FLOOD",
                "source_hash": "BB",
            }
        ]
        client.post("/ingest/packets", json=payload, headers=auth_headers)
        resp = client.post("/ingest/packets", json=payload, headers=auth_headers)
        assert resp.json()["saved"] == 0

        # Verify only one packet exists
        packets = client.get("/api/packets").json()
        hashes = [p["packet_hash"] for p in packets]
        assert hashes.count("dup999") == 1

    def test_node_created_from_packet(self, client: TestClient, auth_headers: dict):
        """Ingesting a packet with a source_hash should auto-create the node."""
        client.post(
            "/ingest/packets",
            json=[
                {
                    "packet_hash": "n001",
                    "source_hash": "AA",
                    "packet_type": "ADVERT",
                }
            ],
            headers=auth_headers,
        )
        resp = client.get("/api/nodes/AA")
        assert resp.status_code == 200
        assert resp.json()["node_hash"] == "AA"

    def test_reject_bad_api_key(self, client: TestClient):
        """Requests with an invalid API key should be rejected with 403."""
        resp = client.post(
            "/ingest/packets",
            json=[],
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 403

    def test_reject_missing_api_key(self, client: TestClient):
        """Requests without an API key header should be rejected with 422."""
        resp = client.post("/ingest/packets", json=[])
        assert resp.status_code == 422


class TestIngestNeighbors:
    """Tests for ``POST /ingest/neighbors``."""

    def test_ingest_neighbor(self, client: TestClient, auth_headers: dict):
        """A valid neighbor payload should be accepted."""
        resp = client.post(
            "/ingest/neighbors",
            json=[
                {
                    "node_hash": "local",
                    "neighbor_hash": "CC",
                    "rssi": -90,
                    "snr": 5.0,
                }
            ],
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_neighbor_creates_node(self, client: TestClient, auth_headers: dict):
        """Ingesting a neighbor should auto-create a node record."""
        client.post(
            "/ingest/neighbors",
            json=[{"neighbor_hash": "DD", "rssi": -80}],
            headers=auth_headers,
        )
        resp = client.get("/api/nodes/DD")
        assert resp.status_code == 200
