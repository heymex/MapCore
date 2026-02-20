# MeshCore Monitor — CLAUDE.md

> **Project:** MeshCore Monitor  
> **Goal:** A MeshMonitor-equivalent web platform for MeshCore networks, built on the pyMC_Repeater HTTP API.  
> **Architecture:** Decoupled — Pi runs pyMC_Core + pyMC_Repeater; this stack runs anywhere.  
> **PoC Targets:** Packet ingestion → SQLite persistence → map view → basic bot/auto-responder framework.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Repository Structure](#2-repository-structure)
3. [Technology Stack](#3-technology-stack)
4. [Data Model](#4-data-model)
5. [Phase 1 — Ingestor (Pi-side bridge)](#5-phase-1--ingestor-pi-side-bridge)
6. [Phase 2 — Backend API Server](#6-phase-2--backend-api-server)
7. [Phase 3 — Frontend Dashboard](#7-phase-3--frontend-dashboard)
8. [Phase 4 — Bot Framework](#8-phase-4--bot-framework)
9. [Phase 5 — PoC Integration & Smoke Tests](#9-phase-5--poc-integration--smoke-tests)
10. [Configuration Reference](#10-configuration-reference)
11. [Deployment](#11-deployment)
12. [Known Constraints & MeshCore-Specific Notes](#12-known-constraints--meshcore-specific-notes)
13. [Future Work (Post-PoC)](#13-future-work-post-poc)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│  Raspberry Pi (field hardware)                           │
│                                                          │
│  LoRa Radio (SX1262 via SPI/GPIO)                        │
│       ↕                                                  │
│  pyMC_Core  ←→  pyMC_Repeater (CherryPy HTTP :8000)     │
│                      ↓  HTTP poll or POST push           │
│                  mc-ingestor.py  (lightweight bridge)    │
└──────────────────────────────────────────────────────────┘
                         ↓  HTTPS / local network
┌──────────────────────────────────────────────────────────┐
│  MeshCore Monitor Server (runs anywhere)                 │
│                                                          │
│  FastAPI backend  ←→  SQLite (via SQLModel/SQLAlchemy)   │
│       ↕                                                  │
│  React + TypeScript frontend (Vite)                      │
│       • Live packet feed (WebSocket)                     │
│       • Node map (Leaflet / MapLibre)                    │
│       • Topology graph                                   │
│       • Packet history & search                          │
│       • Bot framework UI                                 │
│                                                          │
│  Bot Worker (async Python process)                       │
│       • Rule engine                                      │
│       • Sends commands back via pyMC_Repeater API        │
└──────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- The Pi-side ingestor is intentionally minimal — poll pyMC_Repeater's HTTP API, normalize the data, POST to the monitor server. It can alternatively run on the monitor server and pull from the Pi if the Pi is reachable.
- The monitor server exposes its own REST API + WebSocket stream. The frontend is a separate SPA that consumes it.
- The bot framework runs as a separate async worker that reads from the database and writes commands back through the ingestor → pyMC_Repeater API pathway.

---

## 2. Repository Structure

```
meshcore-monitor/
├── CLAUDE.md                  ← this file
├── README.md
├── .env.example
├── docker-compose.yml
├── docker-compose.dev.yml
├── Dockerfile                 ← monitor server + frontend
│
├── ingestor/                  ← Pi-side bridge (deploy separately)
│   ├── mc_ingestor.py
│   ├── requirements.txt
│   ├── config.yaml.example
│   └── mc-ingestor.service    ← systemd unit
│
├── server/                    ← FastAPI backend
│   ├── main.py
│   ├── database.py
│   ├── models.py              ← SQLModel table definitions
│   ├── schemas.py             ← Pydantic I/O schemas
│   ├── routers/
│   │   ├── ingest.py          ← POST endpoints for ingestor
│   │   ├── nodes.py
│   │   ├── packets.py
│   │   ├── telemetry.py
│   │   └── ws.py              ← WebSocket broadcast
│   ├── bot/
│   │   ├── worker.py          ← async bot event loop
│   │   ├── rules.py           ← rule engine
│   │   ├── actions.py         ← action executor (calls Repeater API)
│   │   └── built_in_rules/
│   │       ├── ping_reply.py
│   │       ├── position_reply.py
│   │       └── telemetry_request.py
│   └── requirements.txt
│
├── frontend/                  ← React + TypeScript SPA
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/               ← typed API client
│       ├── components/
│       │   ├── Map/
│       │   ├── PacketFeed/
│       │   ├── NodeList/
│       │   ├── Topology/
│       │   └── BotRules/
│       ├── hooks/
│       │   ├── useWebSocket.ts
│       │   └── useNodes.ts
│       └── pages/
│           ├── Dashboard.tsx
│           ├── Packets.tsx
│           ├── Nodes.tsx
│           ├── Map.tsx
│           └── BotRules.tsx
│
└── tests/
    ├── test_ingest.py
    ├── test_models.py
    └── test_bot_rules.py
```

---

## 3. Technology Stack

### Backend (monitor server)
| Component | Choice | Rationale |
|---|---|---|
| API framework | **FastAPI** | Async-native, auto-docs, WebSocket support built-in |
| ORM / models | **SQLModel** | Pydantic + SQLAlchemy unified, ideal for FastAPI |
| Database (PoC) | **SQLite** | Zero-ops, file-based, matches MeshMonitor precedent |
| Database (prod) | **PostgreSQL** | Drop-in upgrade path via SQLAlchemy |
| WebSocket | **FastAPI native** | No extra deps, broadcast to all connected clients |
| Task runner | **asyncio** (built-in) | Bot worker runs as asyncio task in same process for PoC |
| HTTP client | **httpx** | Async HTTP for calling pyMC_Repeater API |

### Ingestor (Pi-side)
| Component | Choice | Rationale |
|---|---|---|
| Language | **Python 3.9+** | Matches pyMC_Core requirement |
| HTTP polling | **httpx** (async) | Consistent with server side |
| Config | **PyYAML** | Matches pyMC_Repeater's own config format |
| Scheduler | **asyncio** loop | No extra deps |

### Frontend
| Component | Choice | Rationale |
|---|---|---|
| Framework | **React 18 + TypeScript** | Matches MeshMonitor, large ecosystem |
| Build tool | **Vite** | Fast dev server, matches MeshMonitor |
| Map | **Leaflet + react-leaflet** | Open tiles, no API key needed, simpler than MapLibre for PoC |
| Topology graph | **vis-network** or **d3-force** | Flexible graph rendering |
| Charts | **Recharts** | React-native, lightweight |
| WebSocket | **native browser WS** via custom hook | No extra lib needed |
| Styling | **Tailwind CSS** | Utility-first, rapid PoC development |

---

## 4. Data Model

These are the core SQLModel tables. Design them to be additive — add columns as the pyMC_Repeater API reveals more data.

### `nodes` table
```python
class Node(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    node_hash: str = Field(index=True, unique=True)  # 2-char hex prefix from path
    public_key: Optional[str] = None                  # full pubkey if seen in advert
    name: Optional[str] = None                        # from advert payload
    node_type: Optional[str] = None                   # "repeater" | "companion" | "room_server"
    lat: Optional[float] = None
    lon: Optional[float] = None
    last_rssi: Optional[int] = None
    last_snr: Optional[float] = None
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    is_local: bool = False                            # True for the monitored repeater itself
```

### `packets` table
```python
class Packet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    received_at: datetime = Field(default_factory=datetime.utcnow)
    packet_hash: Optional[str] = Field(default=None, index=True)  # dedup key
    packet_type: str        # ADVERT | TXT_MSG | ACK | RESPONSE | TRACE | CHANNEL_MSG
    route_type: str         # FLOOD | DIRECT
    payload_hex: Optional[str] = None
    # Path is a list of 2-char hex node prefixes
    path: Optional[str] = None   # stored as JSON string e.g. '["FA","79","24"]'
    hop_count: Optional[int] = None
    rssi: Optional[int] = None
    snr: Optional[float] = None
    # Source and destination are node_hash references
    source_hash: Optional[str] = Field(default=None, foreign_key="node.node_hash")
    dest_hash: Optional[str] = None
    raw_json: Optional[str] = None   # full API response blob for future parsing
```

### `telemetry` table
```python
class Telemetry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    node_hash: str = Field(foreign_key="node.node_hash", index=True)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    battery_pct: Optional[float] = None
    voltage: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    uptime_seconds: Optional[int] = None
    tx_count: Optional[int] = None
    rx_count: Optional[int] = None
    raw_json: Optional[str] = None
```

### `neighbors` table
```python
class Neighbor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    node_hash: str          # the node that observed this neighbor
    neighbor_hash: str      # the neighbor observed
    rssi: Optional[int] = None
    snr: Optional[float] = None
    # Edge confidence (computed, updated on each observation)
    observation_count: int = 1
```

### `bot_rules` table
```python
class BotRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    enabled: bool = True
    trigger_type: str       # "packet_type" | "keyword" | "node_seen" | "schedule"
    trigger_value: str      # e.g. "TXT_MSG" or "ping" or "!abc123" or "*/5 * * * *"
    action_type: str        # "send_message" | "log" | "webhook" | "telemetry_request"
    action_config: str      # JSON blob of action parameters
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
```

---

## 5. Phase 1 — Ingestor (Pi-side bridge)

**Goal:** A single Python script running on the Pi that polls pyMC_Repeater's HTTP API and POSTs normalized data to the monitor server. This is the entire Pi-side deliverable for PoC.

### 5.1 What to poll from pyMC_Repeater

Before writing the ingestor, map the pyMC_Repeater API. Run the Repeater and inspect:

```bash
# Discover all available endpoints
curl http://<pi-ip>:8000/api/stats
curl http://<pi-ip>:8000/api/packets
curl http://<pi-ip>:8000/api/neighbors
# Check the CherryPy dashboard source or network tab in browser for additional routes
```

Document every endpoint, its response schema, and poll frequency. This is the most important pre-coding step. The ingestor's entire behavior depends on it.

**Expected endpoints based on pyMC_Repeater's dashboard:**
- `/api/stats` — packet counts, forwarded/received/dropped, system info
- `/api/packets` (or `/api/recent_packets`) — recent packet list with type, path, RSSI, SNR
- `/api/neighbors` — neighbor table with signal quality
- Potentially `/api/node` — local node identity and config

### 5.2 Ingestor implementation

```python
# ingestor/mc_ingestor.py
"""
Polls pyMC_Repeater HTTP API and forwards normalized data to MeshCore Monitor server.
Designed to run on the Pi alongside pyMC_Repeater, or remotely if Pi is reachable.
"""

import asyncio
import httpx
import yaml
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("mc-ingestor")

class MCIngestor:
    def __init__(self, config: dict):
        self.repeater_url = config["repeater"]["url"]          # e.g. http://localhost:8000
        self.repeater_api_key = config["repeater"].get("api_key")
        self.monitor_url = config["monitor"]["url"]             # e.g. https://monitor.example.com
        self.monitor_api_key = config["monitor"]["api_key"]
        self.poll_interval = config.get("poll_interval_seconds", 5)
        self.seen_packet_hashes = set()   # in-memory dedup; restart clears it (acceptable for PoC)

    async def poll_packets(self, client: httpx.AsyncClient):
        resp = await client.get(f"{self.repeater_url}/api/packets")
        resp.raise_for_status()
        packets = resp.json()
        new_packets = []
        for pkt in packets:
            h = pkt.get("hash") or pkt.get("id")
            if h and h in self.seen_packet_hashes:
                continue
            if h:
                self.seen_packet_hashes.add(h)
            new_packets.append(self.normalize_packet(pkt))
        return new_packets

    def normalize_packet(self, raw: dict) -> dict:
        """
        Transform pyMC_Repeater packet schema → monitor server schema.
        Field names here are placeholders — update once actual API is mapped.
        """
        return {
            "packet_hash": raw.get("hash") or raw.get("id"),
            "packet_type": raw.get("type", "UNKNOWN"),
            "route_type": raw.get("route_type", "UNKNOWN"),
            "path": json.dumps(raw.get("path", [])),
            "hop_count": len(raw.get("path", [])),
            "rssi": raw.get("rssi"),
            "snr": raw.get("snr"),
            "source_hash": raw.get("source") or (raw.get("path", [None])[0]),
            "dest_hash": raw.get("destination"),
            "raw_json": json.dumps(raw),
            "received_at": raw.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        }

    async def poll_neighbors(self, client: httpx.AsyncClient):
        resp = await client.get(f"{self.repeater_url}/api/neighbors")
        resp.raise_for_status()
        return resp.json()

    async def post_to_monitor(self, client: httpx.AsyncClient, endpoint: str, data: list):
        if not data:
            return
        resp = await client.post(
            f"{self.monitor_url}/ingest/{endpoint}",
            json=data,
            headers={"X-API-Key": self.monitor_api_key},
        )
        resp.raise_for_status()

    async def run(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            while True:
                try:
                    packets = await self.poll_packets(client)
                    await self.post_to_monitor(client, "packets", packets)

                    neighbors = await self.poll_neighbors(client)
                    await self.post_to_monitor(client, "neighbors", neighbors)
                except httpx.RequestError as e:
                    logger.warning(f"Request error: {e}")
                except Exception as e:
                    logger.exception(f"Unexpected error: {e}")
                await asyncio.sleep(self.poll_interval)

def main():
    config = yaml.safe_load(Path("config.yaml").read_text())
    logging.basicConfig(level=logging.INFO)
    asyncio.run(MCIngestor(config).run())

if __name__ == "__main__":
    main()
```

### 5.3 Ingestor config

```yaml
# ingestor/config.yaml.example
repeater:
  url: http://localhost:8000    # pyMC_Repeater address (local on Pi)
  api_key: null                 # if Repeater adds auth later

monitor:
  url: https://your-monitor-server.example.com
  api_key: your-secret-key-here

poll_interval_seconds: 5

logging:
  level: INFO
```

### 5.4 Systemd service

```ini
# ingestor/mc-ingestor.service
[Unit]
Description=MeshCore Monitor Ingestor
After=network.target pymc-repeater.service
Requires=pymc-repeater.service

[Service]
Type=simple
User=repeater
WorkingDirectory=/opt/mc-ingestor
ExecStart=/opt/mc-ingestor/venv/bin/python mc_ingestor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 6. Phase 2 — Backend API Server

**Goal:** FastAPI server that accepts ingested data, persists it to SQLite, serves it via REST, and streams live updates via WebSocket.

### 6.1 Database setup

```python
# server/database.py
from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./meshcore_monitor.db")
engine = create_engine(DATABASE_URL, echo=False)

def create_db():
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
```

### 6.2 WebSocket broadcast manager

```python
# server/routers/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, event_type: str, data: dict):
        msg = json.dumps({"type": event_type, "data": data})
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### 6.3 Ingest router (accepts data from ingestor)

```python
# server/routers/ingest.py
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, select
from ..database import get_session
from ..models import Packet, Node, Neighbor, Telemetry
from ..routers.ws import manager
import json
import os

router = APIRouter(prefix="/ingest")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("INGEST_API_KEY", "changeme"):
        raise HTTPException(status_code=403, detail="Invalid API key")

@router.post("/packets", dependencies=[Depends(verify_api_key)])
async def ingest_packets(packets: list[dict], session: Session = Depends(get_session)):
    saved = []
    for p in packets:
        # Dedup by packet_hash
        if p.get("packet_hash"):
            existing = session.exec(
                select(Packet).where(Packet.packet_hash == p["packet_hash"])
            ).first()
            if existing:
                continue

        packet = Packet(**{k: v for k, v in p.items() if hasattr(Packet, k)})
        session.add(packet)

        # Upsert node from source_hash
        if p.get("source_hash"):
            upsert_node(session, p["source_hash"], p)

        saved.append(packet)

    session.commit()

    # Broadcast to WebSocket clients
    for packet in saved:
        await manager.broadcast("packet", packet.dict())

    return {"saved": len(saved)}

@router.post("/neighbors", dependencies=[Depends(verify_api_key)])
async def ingest_neighbors(neighbors: list[dict], session: Session = Depends(get_session)):
    for n in neighbors:
        neighbor = Neighbor(
            node_hash=n.get("node_hash", "local"),
            neighbor_hash=n.get("neighbor_hash") or n.get("hash"),
            rssi=n.get("rssi"),
            snr=n.get("snr"),
        )
        session.add(neighbor)

        # Update node record with signal info
        if neighbor.neighbor_hash:
            upsert_node(session, neighbor.neighbor_hash, n)

    session.commit()
    await manager.broadcast("neighbors_updated", {})
    return {"ok": True}

def upsert_node(session: Session, node_hash: str, data: dict):
    node = session.exec(select(Node).where(Node.node_hash == node_hash)).first()
    if not node:
        node = Node(node_hash=node_hash)
    node.last_seen = datetime.utcnow()
    node.last_rssi = data.get("rssi", node.last_rssi)
    node.last_snr = data.get("snr", node.last_snr)
    if data.get("name"):
        node.name = data["name"]
    if data.get("lat"):
        node.lat = data["lat"]
    if data.get("lon"):
        node.lon = data["lon"]
    session.add(node)
```

### 6.4 Public REST routers

```python
# server/routers/nodes.py
@router.get("/nodes")
def get_nodes(limit: int = 100, session: Session = Depends(get_session)):
    nodes = session.exec(select(Node).order_by(Node.last_seen.desc()).limit(limit)).all()
    return nodes

@router.get("/nodes/{node_hash}")
def get_node(node_hash: str, session: Session = Depends(get_session)):
    node = session.exec(select(Node).where(Node.node_hash == node_hash)).first()
    if not node:
        raise HTTPException(status_code=404)
    return node

# server/routers/packets.py
@router.get("/packets")
def get_packets(
    limit: int = 100,
    packet_type: Optional[str] = None,
    source_hash: Optional[str] = None,
    session: Session = Depends(get_session),
):
    query = select(Packet).order_by(Packet.received_at.desc()).limit(limit)
    if packet_type:
        query = query.where(Packet.packet_type == packet_type)
    if source_hash:
        query = query.where(Packet.source_hash == source_hash)
    return session.exec(query).all()
```

### 6.5 Main app entrypoint

```python
# server/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .database import create_db
from .routers import ingest, nodes, packets, telemetry, ws
from .bot.worker import start_bot_worker
import asyncio

app = FastAPI(title="MeshCore Monitor", version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(ingest.router)
app.include_router(nodes.router, prefix="/api")
app.include_router(packets.router, prefix="/api")
app.include_router(telemetry.router, prefix="/api")
app.include_router(ws.router)

@app.on_event("startup")
async def startup():
    create_db()
    asyncio.create_task(start_bot_worker())

# Serve built frontend
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

---

## 7. Phase 3 — Frontend Dashboard

**Goal:** React SPA with four primary views: Dashboard, Node Map, Packet Feed, and Bot Rules. Connects to the FastAPI backend via REST and WebSocket.

### 7.1 WebSocket hook

```typescript
// frontend/src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from "react";

type MessageHandler = (event: { type: string; data: unknown }) => void;

export function useWebSocket(url: string, onMessage: MessageHandler) {
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        onMessage(parsed);
      } catch (e) {
        console.error("WS parse error", e);
      }
    };

    ws.onclose = () => {
      // Reconnect after 3 seconds
      setTimeout(connect, 3000);
    };

    return () => ws.close();
  }, [url, onMessage]);

  useEffect(() => {
    const cleanup = connect();
    return cleanup;
  }, [connect]);
}
```

### 7.2 Node Map component

The map is the primary PoC deliverable for the frontend.

```typescript
// frontend/src/components/Map/NodeMap.tsx
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup } from "react-leaflet";
import { useNodes } from "../../hooks/useNodes";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useState, useCallback } from "react";
import type { Node } from "../../api/types";

export function NodeMap() {
  const { nodes, updateNode, addPacketPath } = useNodes();
  const [recentPaths, setRecentPaths] = useState<string[][][]>([]);

  const handleWsMessage = useCallback(({ type, data }: any) => {
    if (type === "packet" && data.path) {
      // Flash the packet path on the map
      const path = JSON.parse(data.path || "[]");
      addPacketPath(path);
    }
    if (type === "node_updated") {
      updateNode(data);
    }
  }, [updateNode, addPacketPath]);

  useWebSocket(`ws://${window.location.host}/ws`, handleWsMessage);

  const nodesWithLocation = nodes.filter((n) => n.lat && n.lon);

  return (
    <MapContainer
      center={[39.5, -98.35]}  // Center of USA; make configurable
      zoom={4}
      className="h-full w-full"
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="© OpenStreetMap contributors"
      />
      {nodesWithLocation.map((node) => (
        <CircleMarker
          key={node.node_hash}
          center={[node.lat!, node.lon!]}
          radius={node.is_local ? 10 : 6}
          pathOptions={{
            color: node.is_local ? "#f59e0b" : "#6366f1",
            fillOpacity: 0.8,
          }}
        >
          <Popup>
            <div>
              <strong>{node.name || node.node_hash}</strong>
              <br />
              Type: {node.node_type || "unknown"}
              <br />
              Last RSSI: {node.last_rssi ?? "—"} dBm
              <br />
              Last seen: {new Date(node.last_seen).toLocaleString()}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
```

### 7.3 Live Packet Feed component

```typescript
// frontend/src/components/PacketFeed/PacketFeed.tsx
import { useState, useCallback } from "react";
import { useWebSocket } from "../../hooks/useWebSocket";

const PACKET_TYPE_COLORS: Record<string, string> = {
  ADVERT: "text-blue-400",
  TXT_MSG: "text-green-400",
  ACK: "text-gray-400",
  RESPONSE: "text-purple-400",
  TRACE: "text-yellow-400",
  CHANNEL_MSG: "text-cyan-400",
};

export function PacketFeed() {
  const [packets, setPackets] = useState<any[]>([]);

  const handleMessage = useCallback(({ type, data }: any) => {
    if (type === "packet") {
      setPackets((prev) => [data, ...prev].slice(0, 200));  // keep last 200
    }
  }, []);

  useWebSocket(`ws://${window.location.host}/ws`, handleMessage);

  return (
    <div className="font-mono text-sm overflow-y-auto h-full bg-gray-900 p-2">
      {packets.map((pkt, i) => (
        <div key={i} className="flex gap-2 border-b border-gray-800 py-1">
          <span className="text-gray-500 w-20 shrink-0">
            {new Date(pkt.received_at).toLocaleTimeString()}
          </span>
          <span className={`w-24 shrink-0 ${PACKET_TYPE_COLORS[pkt.packet_type] || "text-white"}`}>
            {pkt.packet_type}
          </span>
          <span className="text-gray-400 w-16 shrink-0">
            {pkt.source_hash || "??"}
          </span>
          <span className="text-gray-500">
            [{JSON.parse(pkt.path || "[]").join(" → ")}]
          </span>
          <span className="text-gray-600 ml-auto">
            {pkt.rssi}dBm
          </span>
        </div>
      ))}
    </div>
  );
}
```

### 7.4 Dashboard page layout

```typescript
// frontend/src/pages/Dashboard.tsx
import { NodeMap } from "../components/Map/NodeMap";
import { PacketFeed } from "../components/PacketFeed/PacketFeed";
import { StatsBar } from "../components/StatsBar";

export function Dashboard() {
  return (
    <div className="flex flex-col h-screen bg-gray-950 text-white">
      <StatsBar />
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1">
          <NodeMap />
        </div>
        <div className="w-96 border-l border-gray-800">
          <PacketFeed />
        </div>
      </div>
    </div>
  );
}
```

---

## 8. Phase 4 — Bot Framework

**Goal:** An async rule engine that monitors the event stream and can dispatch responses back through pyMC_Repeater. For PoC, implement ping reply and node-seen notification.

### 8.1 Architecture

The bot runs as an asyncio task inside the FastAPI process for PoC simplicity. It subscribes to the same internal event queue that the WebSocket broadcast uses, evaluates rules, and executes actions by POSTing back to pyMC_Repeater's API (or directly through pyMC_Core if running on the Pi — for remote deployment it goes through pyMC_Repeater).

**Critical note:** MeshCore's message encryption means the bot can only respond to messages it was the intended recipient of (direct messages to the repeater node) or to network-level events (packet receipt, neighbor discovery, trace requests). Channel message content is encrypted per-contact and will be opaque to the bot unless it holds the relevant keys.

### 8.2 Internal event queue

```python
# server/bot/worker.py
import asyncio
from .rules import RuleEngine
from .actions import ActionExecutor
from ..database import get_session
from ..models import BotRule, Packet

# Module-level queue shared with ingest router
event_queue: asyncio.Queue = asyncio.Queue()

async def start_bot_worker():
    engine = RuleEngine()
    executor = ActionExecutor()
    
    while True:
        try:
            event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
            await engine.evaluate(event, executor)
        except asyncio.TimeoutError:
            pass  # Normal — no events
        except Exception as e:
            logger.exception(f"Bot worker error: {e}")
```

In `ingest.py`, after saving a packet, add:
```python
from ..bot.worker import event_queue
await event_queue.put({"type": "packet", "data": packet.dict()})
```

### 8.3 Rule engine

```python
# server/bot/rules.py
import json
from sqlmodel import select, Session
from ..database import get_session
from ..models import BotRule

class RuleEngine:
    async def evaluate(self, event: dict, executor: "ActionExecutor"):
        with get_session() as session:
            rules = session.exec(select(BotRule).where(BotRule.enabled == True)).all()
        
        for rule in rules:
            if await self._matches(rule, event):
                await executor.execute(rule, event)
                # Update trigger stats
                with get_session() as session:
                    r = session.get(BotRule, rule.id)
                    r.last_triggered = datetime.utcnow()
                    r.trigger_count += 1
                    session.add(r)
                    session.commit()

    async def _matches(self, rule: BotRule, event: dict) -> bool:
        trigger = rule.trigger_type
        value = rule.trigger_value
        data = event.get("data", {})

        if trigger == "packet_type":
            return data.get("packet_type") == value

        if trigger == "keyword":
            # Only works on decrypted/cleartext payloads
            payload = data.get("payload_hex", "")
            try:
                text = bytes.fromhex(payload).decode("utf-8", errors="ignore")
                return value.lower() in text.lower()
            except Exception:
                return False

        if trigger == "node_seen":
            # Fires when a specific node_hash is seen for the first time
            return data.get("source_hash") == value

        return False
```

### 8.4 Action executor

```python
# server/bot/actions.py
import httpx
import json
import os
import logging

logger = logging.getLogger("bot-actions")
REPEATER_URL = os.getenv("REPEATER_URL", "http://localhost:8000")

class ActionExecutor:
    async def execute(self, rule: "BotRule", event: dict):
        config = json.loads(rule.action_config)
        action = rule.action_type

        if action == "log":
            logger.info(f"[BOT] Rule '{rule.name}' triggered: {event}")

        elif action == "send_message":
            await self._send_message(
                destination=config.get("destination", "flood"),
                message=config["message"],
            )

        elif action == "webhook":
            await self._call_webhook(config["url"], event)

        elif action == "telemetry_request":
            await self._request_telemetry(config.get("node_hash"))

    async def _send_message(self, destination: str, message: str):
        """
        POST a message through pyMC_Repeater's command API.
        Endpoint TBD — map the Repeater API first.
        For PoC, log the intent if the endpoint isn't yet known.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{REPEATER_URL}/api/send",   # PLACEHOLDER — verify endpoint
                    json={"destination": destination, "message": message},
                    timeout=5.0,
                )
                resp.raise_for_status()
                logger.info(f"[BOT] Sent message to {destination}: {message}")
        except Exception as e:
            logger.warning(f"[BOT] Failed to send message: {e}")

    async def _call_webhook(self, url: str, event: dict):
        async with httpx.AsyncClient() as client:
            await client.post(url, json=event, timeout=5.0)

    async def _request_telemetry(self, node_hash: str | None):
        logger.info(f"[BOT] Telemetry request for {node_hash} — endpoint TBD")
```

### 8.5 Built-in rules (seed data)

Add these to the database on startup if they don't exist:

```python
BUILTIN_RULES = [
    {
        "name": "Log all ADVERT packets",
        "enabled": False,
        "trigger_type": "packet_type",
        "trigger_value": "ADVERT",
        "action_type": "log",
        "action_config": "{}",
    },
    {
        "name": "Ping reply",
        "enabled": False,
        "trigger_type": "keyword",
        "trigger_value": "ping",
        "action_type": "send_message",
        "action_config": json.dumps({"destination": "flood", "message": "pong"}),
    },
    {
        "name": "New node alert webhook",
        "enabled": False,
        "trigger_type": "node_seen",
        "trigger_value": "",   # fill in node_hash or make wildcard
        "action_type": "webhook",
        "action_config": json.dumps({"url": "https://hooks.example.com/meshcore"}),
    },
]
```

### 8.6 Bot Rules UI

```typescript
// frontend/src/pages/BotRules.tsx
// Simple CRUD table for bot rules
// Columns: Name | Enabled toggle | Trigger | Action | Last triggered | Trigger count
// Actions: Edit (modal form), Delete, Test (fires the rule manually)

export function BotRules() {
  const [rules, setRules] = useState<BotRule[]>([]);

  useEffect(() => {
    fetch("/api/bot/rules").then((r) => r.json()).then(setRules);
  }, []);

  return (
    <div className="p-4">
      <div className="flex justify-between mb-4">
        <h2 className="text-xl font-bold">Bot Rules</h2>
        <button className="btn-primary" onClick={() => setEditing({})}>
          + New Rule
        </button>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-400 border-b border-gray-700">
            <th>Name</th>
            <th>Enabled</th>
            <th>Trigger</th>
            <th>Action</th>
            <th>Last triggered</th>
            <th>Count</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rules.map((rule) => (
            <BotRuleRow key={rule.id} rule={rule} onUpdate={fetchRules} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## 9. Phase 5 — PoC Integration & Smoke Tests

### 9.1 PoC success criteria

The PoC is considered complete when all of the following are true:

- [ ] Ingestor runs on Pi, successfully polls pyMC_Repeater, and POSTs data to monitor server
- [ ] Monitor server persists packets, nodes, and neighbors to SQLite without errors
- [ ] At least one real node with location data appears on the map
- [ ] Live packet feed updates in browser without page refresh
- [ ] At least one bot rule (ping reply or log) fires correctly on a matching event
- [ ] Bot send-message action either sends through Repeater API or logs clearly that the endpoint needs mapping

### 9.2 Manual integration checklist

```
□ pyMC_Repeater running on Pi, dashboard accessible at http://<pi>:8000
□ All Repeater API endpoints documented (run: curl http://<pi>:8000/api/*)
□ Ingestor config.yaml updated with Pi address and monitor server URL
□ Monitor server .env configured with INGEST_API_KEY and REPEATER_URL
□ docker compose up (or uvicorn server.main:app) starts without errors
□ curl -H "X-API-Key: ..." http://monitor:8001/ingest/packets -d '[{...}]' returns {"saved": 1}
□ Browser opens http://monitor:8001, Dashboard loads
□ Map renders (even if no nodes with location yet — check that map tiles load)
□ WebSocket connection shown as open in browser DevTools
□ Ingestor logs show successful POSTs: "saved N packets"
□ /api/nodes returns at least one node after ingestor runs
□ /api/packets returns packets
□ Enable "Log all ADVERT packets" bot rule, verify log output on next ADVERT
□ Verify /api/bot/rules CRUD works from frontend
```

### 9.3 Key unknowns to resolve before/during coding

These require hands-on inspection of pyMC_Repeater:

1. **Exact API endpoint paths and response schemas** — The most important unknown. Map every route the CherryPy server exposes before writing the ingestor's `normalize_*` methods.

2. **Does the Repeater expose a "send message" endpoint?** — Critical for bot action execution. Check the CherryPy routes in `repeater/` source code for any POST endpoints that trigger transmission.

3. **Packet dedup field** — Does the Repeater include a stable unique ID or hash per packet in its API responses? If not, implement timestamp + source_hash + type composite dedup.

4. **How locations appear in API responses** — Tracked adverts carry lat/lon in pyMC_Core, but does pyMC_Repeater surface this in its HTTP API, or only in the HTML dashboard?

5. **Neighbor table schema** — What fields does `/api/neighbors` (or equivalent) return?

To answer these: clone pyMC_Repeater, run it against a live radio or mock, inspect the CherryPy route handlers in `repeater/` source, and capture actual HTTP responses.

### 9.4 Basic tests

```python
# tests/test_ingest.py
from fastapi.testclient import TestClient
from server.main import app
import os

os.environ["INGEST_API_KEY"] = "testkey"
client = TestClient(app)

def test_ingest_packet():
    resp = client.post(
        "/ingest/packets",
        json=[{
            "packet_hash": "abc123",
            "packet_type": "ADVERT",
            "route_type": "FLOOD",
            "path": '["FA","79"]',
            "hop_count": 2,
            "rssi": -85,
            "snr": 7.5,
            "source_hash": "FA",
        }],
        headers={"X-API-Key": "testkey"},
    )
    assert resp.status_code == 200
    assert resp.json()["saved"] == 1

def test_dedup_packet():
    # Second insert of same hash should not create duplicate
    for _ in range(2):
        client.post("/ingest/packets", json=[{"packet_hash": "dup999", ...}],
                    headers={"X-API-Key": "testkey"})
    resp = client.get("/api/packets")
    hashes = [p["packet_hash"] for p in resp.json()]
    assert hashes.count("dup999") == 1

def test_node_created_from_packet():
    client.post("/ingest/packets",
                json=[{"packet_hash": "n001", "source_hash": "AA", "packet_type": "ADVERT"}],
                headers={"X-API-Key": "testkey"})
    resp = client.get("/api/nodes/AA")
    assert resp.status_code == 200

# tests/test_bot_rules.py
def test_packet_type_trigger_matches():
    from server.bot.rules import RuleEngine
    from server.models import BotRule
    engine = RuleEngine()
    rule = BotRule(trigger_type="packet_type", trigger_value="ADVERT", ...)
    event = {"data": {"packet_type": "ADVERT"}}
    assert asyncio.run(engine._matches(rule, event)) is True
```

---

## 10. Configuration Reference

### Monitor server `.env`

```bash
# .env
DATABASE_URL=sqlite:///./meshcore_monitor.db
INGEST_API_KEY=change-this-to-something-secret

# For bot actions that call back to Repeater
REPEATER_URL=http://<pi-ip>:8000
REPEATER_API_KEY=

# CORS origins (space-separated, or * for PoC)
ALLOWED_ORIGINS=*

# Bot worker settings
BOT_ENABLED=true
```

### Docker compose

```yaml
# docker-compose.yml
services:
  monitor:
    build: .
    ports:
      - "8001:8001"
    volumes:
      - ./data:/data
    environment:
      - DATABASE_URL=sqlite:////data/meshcore_monitor.db
      - INGEST_API_KEY=${INGEST_API_KEY}
      - REPEATER_URL=${REPEATER_URL}
    restart: unless-stopped
```

---

## 11. Deployment

### Development (no Docker)

```bash
# Backend
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Frontend (separate terminal)
cd frontend
npm install
npm run dev   # Vite dev server on :5173, proxies /api and /ws to :8001

# Ingestor (on Pi, or locally pointing at Pi)
cd ingestor
pip install -r requirements.txt
cp config.yaml.example config.yaml  # edit with Pi address
python mc_ingestor.py
```

### Production

```bash
docker compose up -d

# On Pi: install ingestor as systemd service
sudo cp ingestor/mc-ingestor.service /etc/systemd/system/
sudo systemctl enable --now mc-ingestor
```

### Vite proxy config (dev)

```typescript
// frontend/vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      "/api": "http://localhost:8001",
      "/ingest": "http://localhost:8001",
      "/ws": { target: "ws://localhost:8001", ws: true },
    },
  },
});
```

---

## 12. Known Constraints & MeshCore-Specific Notes

**Encryption opacity.** MeshCore uses per-contact E2E encryption (Ed25519/X25519). Message payloads in `TXT_MSG` packets are encrypted and cannot be read by the monitor unless it holds the recipient's private key. The monitor will see metadata (packet type, path, RSSI, timing) but not message content. The bot can only respond to message content if it runs with the repeater's own identity and is the intended recipient. For PoC, accept this limitation and display encrypted payloads as `[encrypted]`.

**2-character node prefix collisions.** MeshCore identifies nodes by a 2-char hex prefix (1/256 collision probability). pyMC_Console has already implemented a 4-factor disambiguation algorithm (position, co-occurrence, geographic proximity, recency). For PoC, store raw prefixes and accept ambiguity. Add disambiguation as a post-PoC enhancement — the pyMC_Console source is the reference implementation.

**No remote connection interface (yet).** Unlike Meshtastic's TCP connection mode, pyMC_Core requires physical hardware access. The ingestor must run on the Pi or on a machine with direct access to a KISS TNC. The HTTP polling through pyMC_Repeater is the only remote data path available today.

**Bot send-message pathway is a TBD.** The pyMC_Repeater send API endpoint (if it exists) must be mapped from source inspection before the bot's `_send_message` action will work. If no such endpoint exists, an alternative is to run the bot worker on the Pi itself (accessing pyMC_Core directly), pushing results to the monitor server for display. For PoC, log the intent and mark this as a known gap.

**Location data sparsity.** Not all MeshCore nodes broadcast location. Only nodes sending tracked adverts will appear on the map. Expect the node list to be richer than the map for any given deployment.

**Poll-based latency.** With a 5-second poll interval, the live feed will lag by up to 5 seconds. Acceptable for PoC monitoring. Reduce interval cautiously — pyMC_Repeater is CherryPy-based and not designed for high-frequency polling.

---

## 13. Future Work (Post-PoC)

In rough priority order:

1. **Map pyMC_Repeater's full API surface** and harden the ingestor's normalization layer. The PoC uses placeholder field names that must be corrected against actual responses.

2. **Topology graph view.** Port pyMC_Console's prefix disambiguation algorithm. Display nodes as graph vertices, packet paths as edges. Weight edges by observation count.

3. **Airtime and RF statistics.** Add duty cycle tracking, channel utilization, LBT insights — pyMC_Repeater already collects this; surface it in charts (Recharts).

4. **WebSocket push from Repeater.** If/when pyMC_Repeater adds a WebSocket event stream, replace the polling ingestor with a subscription model. This eliminates poll lag and the need for the ingestor process.

5. **Authentication.** Add JWT-based auth to the monitor server. For PoC, the API key on the ingest endpoint is sufficient.

6. **PostgreSQL migration.** The SQLModel setup is database-agnostic. Change `DATABASE_URL` to a Postgres connection string. Add Alembic for schema migrations.

7. **Notification system.** Add Apprise integration in the bot's action executor for 100+ notification channels (Slack, Discord, email, PushOver, etc.).

8. **Multi-repeater support.** Allow multiple ingestor instances (one per Pi/repeater) to POST to the same monitor server. Packets already carry source_hash; add a `repeater_id` field to the ingest schema to track which repeater heard each packet.

9. **Device configuration UI.** If pyMC_Repeater's roadmap delivers a configuration API, surface radio settings (frequency, SF, bandwidth, power) in the frontend — equivalent to MeshMonitor's settings panel.

10. **Contribution to pyMC_Repeater.** The most impactful upstream contribution would be adding a WebSocket event endpoint to pyMC_Repeater that streams raw packet events. This would benefit every tool in the ecosystem.
