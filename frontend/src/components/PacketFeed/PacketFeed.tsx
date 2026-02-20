// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Live packet feed that streams incoming mesh packets via WebSocket.
 *
 * Each row shows timestamp, type, source, path, and signal strength.
 * The feed keeps the most recent 200 packets and automatically scrolls.
 */

import { useState, useCallback } from "react";
import { useWebSocket } from "../../hooks/useWebSocket";
import type { Packet, WsEvent } from "../../api/types";

/** Colour map for packet type badges. */
const PACKET_TYPE_COLORS: Record<string, string> = {
  ADVERT: "text-blue-400",
  TXT_MSG: "text-green-400",
  ACK: "text-gray-400",
  RESPONSE: "text-purple-400",
  TRACE: "text-yellow-400",
  CHANNEL_MSG: "text-cyan-400",
};

/** Maximum packets retained in the live feed. */
const MAX_FEED_SIZE = 200;

/** Real-time packet feed panel. */
export function PacketFeed() {
  const [packets, setPackets] = useState<Packet[]>([]);

  const handleMessage = useCallback(({ type, data }: WsEvent) => {
    if (type === "packet") {
      setPackets((prev) =>
        [data as Packet, ...prev].slice(0, MAX_FEED_SIZE)
      );
    }
  }, []);

  useWebSocket(`ws://${window.location.host}/ws`, handleMessage);

  return (
    <div className="font-mono text-sm overflow-y-auto h-full bg-gray-900 p-2">
      <h3 className="text-xs text-gray-500 uppercase tracking-wide mb-2">
        Live Packet Feed
      </h3>
      {packets.length === 0 && (
        <p className="text-gray-600 text-xs italic">
          Waiting for packets…
        </p>
      )}
      {packets.map((pkt, i) => {
        let parsedPath: string[] = [];
        try {
          parsedPath = JSON.parse(pkt.path || "[]");
        } catch {
          /* ignore */
        }

        return (
          <div
            key={`${pkt.packet_hash ?? ""}-${i}`}
            className="flex gap-2 border-b border-gray-800 py-1"
          >
            <span className="text-gray-500 w-20 shrink-0">
              {new Date(pkt.received_at).toLocaleTimeString()}
            </span>
            <span
              className={`w-24 shrink-0 ${
                PACKET_TYPE_COLORS[pkt.packet_type] || "text-white"
              }`}
            >
              {pkt.packet_type}
            </span>
            <span className="text-gray-400 w-16 shrink-0">
              {pkt.source_hash || "??"}
            </span>
            <span className="text-gray-500 truncate">
              [{parsedPath.join(" → ")}]
            </span>
            <span className="text-gray-600 ml-auto shrink-0">
              {pkt.rssi != null ? `${pkt.rssi}dBm` : "—"}
            </span>
          </div>
        );
      })}
    </div>
  );
}
