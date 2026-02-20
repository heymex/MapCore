# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""
MeshCore Monitor Ingestor.

Polls pyMC_Repeater's HTTP API and forwards normalized data to the
MeshCore Monitor server.  Designed to run on the Pi alongside
pyMC_Repeater, or remotely if the Pi is reachable over the network.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

logger = logging.getLogger("mc-ingestor")


class MCIngestor:
    """Bridges pyMC_Repeater → MeshCore Monitor via HTTP polling.

    Attributes:
        repeater_url: Base URL of the pyMC_Repeater CherryPy server.
        repeater_api_key: Optional API key for Repeater authentication.
        monitor_url: Base URL of the MeshCore Monitor server.
        monitor_api_key: API key accepted by the monitor's ingest endpoints.
        poll_interval: Seconds between poll cycles.
        seen_packet_hashes: In-memory set used for deduplication across polls.
    """

    def __init__(self, config: dict) -> None:
        self.repeater_url: str = config["repeater"]["url"]
        self.repeater_api_key: str | None = config["repeater"].get("api_key")
        self.monitor_url: str = config["monitor"]["url"]
        self.monitor_api_key: str = config["monitor"]["api_key"]
        self.poll_interval: int = config.get("poll_interval_seconds", 5)
        self.seen_packet_hashes: set[str] = set()

    # ------------------------------------------------------------------
    # Polling helpers
    # ------------------------------------------------------------------

    async def poll_packets(self, client: httpx.AsyncClient) -> list[dict]:
        """Fetch recent packets from pyMC_Repeater and deduplicate.

        Args:
            client: Shared async HTTP client.

        Returns:
            List of normalized packet dicts not yet seen by this process.
        """
        resp = await client.get(f"{self.repeater_url}/api/packets")
        resp.raise_for_status()
        packets: list[dict] = resp.json()

        new_packets: list[dict] = []
        for pkt in packets:
            pkt_hash = pkt.get("hash") or pkt.get("id")
            if pkt_hash and pkt_hash in self.seen_packet_hashes:
                continue
            if pkt_hash:
                self.seen_packet_hashes.add(pkt_hash)
            new_packets.append(self.normalize_packet(pkt))
        return new_packets

    def normalize_packet(self, raw: dict) -> dict:
        """Transform a pyMC_Repeater packet into the monitor server schema.

        Field names are placeholders — update once the actual Repeater API
        response schema is mapped.

        Args:
            raw: Single packet dict from the Repeater API.

        Returns:
            Normalized packet dict matching the monitor ingest schema.
        """
        path = raw.get("path", [])
        return {
            "packet_hash": raw.get("hash") or raw.get("id"),
            "packet_type": raw.get("type", "UNKNOWN"),
            "route_type": raw.get("route_type", "UNKNOWN"),
            "path": json.dumps(path),
            "hop_count": len(path),
            "rssi": raw.get("rssi"),
            "snr": raw.get("snr"),
            "source_hash": raw.get("source") or (path[0] if path else None),
            "dest_hash": raw.get("destination"),
            "payload_hex": raw.get("payload_hex"),
            "raw_json": json.dumps(raw),
            "received_at": (
                raw.get("timestamp") or datetime.now(timezone.utc).isoformat()
            ),
        }

    async def poll_neighbors(self, client: httpx.AsyncClient) -> list[dict]:
        """Fetch the current neighbor table from pyMC_Repeater.

        Args:
            client: Shared async HTTP client.

        Returns:
            Raw neighbor list from the Repeater API.
        """
        resp = await client.get(f"{self.repeater_url}/api/neighbors")
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Monitor server communication
    # ------------------------------------------------------------------

    async def post_to_monitor(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        data: list[dict],
    ) -> None:
        """POST a batch of records to the monitor server's ingest API.

        Args:
            client: Shared async HTTP client.
            endpoint: Ingest sub-path (e.g. ``"packets"`` or ``"neighbors"``).
            data: List of dicts to send as JSON body.
        """
        if not data:
            return
        resp = await client.post(
            f"{self.monitor_url}/ingest/{endpoint}",
            json=data,
            headers={"X-API-Key": self.monitor_api_key},
        )
        resp.raise_for_status()
        logger.info(
            "POST /ingest/%s → %s (%d items)", endpoint, resp.status_code, len(data)
        )

    # ------------------------------------------------------------------
    # Main event loop
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Start the infinite poll → forward loop."""
        logger.info(
            "Ingestor starting  repeater=%s  monitor=%s  interval=%ds",
            self.repeater_url,
            self.monitor_url,
            self.poll_interval,
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            while True:
                try:
                    packets = await self.poll_packets(client)
                    await self.post_to_monitor(client, "packets", packets)

                    neighbors = await self.poll_neighbors(client)
                    await self.post_to_monitor(client, "neighbors", neighbors)
                except httpx.RequestError as exc:
                    logger.warning("Request error: %s", exc)
                except Exception:
                    logger.exception("Unexpected error during poll cycle")
                await asyncio.sleep(self.poll_interval)


def main() -> None:
    """Load config and start the ingestor."""
    config = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    log_level = config.get("logging", {}).get("level", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )
    asyncio.run(MCIngestor(config).run())


if __name__ == "__main__":
    main()
