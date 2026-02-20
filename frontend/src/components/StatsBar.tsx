// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Top-level statistics bar showing node and packet counts.
 *
 * Polls the REST API every 10 seconds to update summary numbers.
 */

import { useEffect, useState } from "react";
import type { Node, Packet } from "../api/types";
import { fetchNodes, fetchPackets } from "../api/client";

/** Single statistic card. */
function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col items-center px-4 py-2">
      <span className="text-2xl font-bold text-indigo-400">{value}</span>
      <span className="text-xs text-gray-500 uppercase tracking-wide">
        {label}
      </span>
    </div>
  );
}

/** Summary statistics strip rendered at the top of the dashboard. */
export function StatsBar() {
  const [nodeCount, setNodeCount] = useState(0);
  const [packetCount, setPacketCount] = useState(0);
  const [nodesWithLocation, setNodesWithLocation] = useState(0);
  const [latestPacketType, setLatestPacketType] = useState("—");

  useEffect(() => {
    /** Fetch summary stats from the API. */
    async function refresh() {
      try {
        const [nodes, packets]: [Node[], Packet[]] = await Promise.all([
          fetchNodes(500),
          fetchPackets({ limit: 1 }),
        ]);
        setNodeCount(nodes.length);
        setNodesWithLocation(
          nodes.filter((n) => n.lat != null && n.lon != null).length
        );
        if (packets.length > 0) {
          setLatestPacketType(packets[0].packet_type);
        }
        // Use node count as proxy; real packet count needs a dedicated endpoint
        setPacketCount(nodes.reduce((acc, n) => acc + (n.last_rssi ? 1 : 0), 0));
      } catch {
        /* silent — stats are best-effort */
      }
    }

    refresh();
    const timer = setInterval(refresh, 10_000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex items-center gap-4 px-4 py-1 bg-gray-900 border-b border-gray-800">
      <StatCard label="Nodes" value={nodeCount} />
      <StatCard label="With Location" value={nodesWithLocation} />
      <StatCard label="Active Signals" value={packetCount} />
      <StatCard label="Latest Type" value={latestPacketType} />
    </div>
  );
}
