// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Interactive Leaflet map showing mesh nodes with location data.
 *
 * Nodes are drawn as circle markers coloured by type (local vs remote).
 * Live WebSocket events update node positions and flash recent packet
 * paths on the map.
 */

import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
} from "react-leaflet";
import { useNodes } from "../../hooks/useNodes";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useCallback } from "react";
import type { WsEvent } from "../../api/types";

/** Default map centre — middle of the continental USA. */
const DEFAULT_CENTER: [number, number] = [39.5, -98.35];

/** Primary map component for the dashboard and /map page. */
export function NodeMap() {
  const { nodes, updateNode, addPacketPath } = useNodes();

  const handleWsMessage = useCallback(
    ({ type, data }: WsEvent) => {
      const d = data as Record<string, unknown>;
      if (type === "packet" && d.path) {
        try {
          const path: string[] = JSON.parse(d.path as string);
          addPacketPath(path);
        } catch {
          /* ignore malformed path */
        }
      }
      if (type === "node_updated" && d.node_hash) {
        updateNode(d as unknown as { node_hash: string });
      }
    },
    [updateNode, addPacketPath]
  );

  useWebSocket(`ws://${window.location.host}/ws`, handleWsMessage);

  const nodesWithLocation = nodes.filter((n) => n.lat != null && n.lon != null);

  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={4}
      className="h-full w-full"
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
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
            <div className="text-sm">
              <strong>{node.name || node.node_hash}</strong>
              <br />
              Type: {node.node_type || "unknown"}
              <br />
              RSSI: {node.last_rssi ?? "—"} dBm
              <br />
              SNR: {node.last_snr ?? "—"}
              <br />
              Last seen: {new Date(node.last_seen).toLocaleString()}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
