// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Packets page — searchable historical packet table with type filters.
 */

import { useEffect, useState } from "react";
import type { Packet } from "../api/types";
import { fetchPackets } from "../api/client";

/** Colour map for packet type badges. */
const TYPE_COLORS: Record<string, string> = {
  ADVERT: "bg-blue-900 text-blue-300",
  TXT_MSG: "bg-green-900 text-green-300",
  ACK: "bg-gray-700 text-gray-300",
  RESPONSE: "bg-purple-900 text-purple-300",
  TRACE: "bg-yellow-900 text-yellow-300",
  CHANNEL_MSG: "bg-cyan-900 text-cyan-300",
};

/** Historical packet listing page. */
export function Packets() {
  const [packets, setPackets] = useState<Packet[]>([]);
  const [typeFilter, setTypeFilter] = useState("");

  useEffect(() => {
    const params: { limit: number; packet_type?: string } = { limit: 200 };
    if (typeFilter) params.packet_type = typeFilter;
    fetchPackets(params).then(setPackets).catch(console.error);
  }, [typeFilter]);

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">Packet History</h2>
        <select
          className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All types</option>
          <option value="ADVERT">ADVERT</option>
          <option value="TXT_MSG">TXT_MSG</option>
          <option value="ACK">ACK</option>
          <option value="RESPONSE">RESPONSE</option>
          <option value="TRACE">TRACE</option>
          <option value="CHANNEL_MSG">CHANNEL_MSG</option>
        </select>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-400 uppercase border-b border-gray-700">
            <tr>
              <th className="px-3 py-2">Time</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Route</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Dest</th>
              <th className="px-3 py-2">Path</th>
              <th className="px-3 py-2">Hops</th>
              <th className="px-3 py-2">RSSI</th>
              <th className="px-3 py-2">SNR</th>
            </tr>
          </thead>
          <tbody>
            {packets.map((pkt) => {
              let parsedPath: string[] = [];
              try {
                parsedPath = JSON.parse(pkt.path || "[]");
              } catch {
                /* ignore */
              }
              return (
                <tr
                  key={pkt.id}
                  className="border-b border-gray-800 hover:bg-gray-800/50"
                >
                  <td className="px-3 py-2 text-gray-400 text-xs whitespace-nowrap">
                    {new Date(pkt.received_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        TYPE_COLORS[pkt.packet_type] || "bg-gray-700 text-gray-300"
                      }`}
                    >
                      {pkt.packet_type}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-gray-500">{pkt.route_type}</td>
                  <td className="px-3 py-2 font-mono text-indigo-400">
                    {pkt.source_hash || "—"}
                  </td>
                  <td className="px-3 py-2 font-mono text-gray-400">
                    {pkt.dest_hash || "—"}
                  </td>
                  <td className="px-3 py-2 text-gray-500 font-mono text-xs">
                    {parsedPath.join(" → ") || "—"}
                  </td>
                  <td className="px-3 py-2 text-gray-500">
                    {pkt.hop_count ?? "—"}
                  </td>
                  <td className="px-3 py-2 text-gray-400">
                    {pkt.rssi != null ? `${pkt.rssi}` : "—"}
                  </td>
                  <td className="px-3 py-2 text-gray-400">
                    {pkt.snr != null ? `${pkt.snr}` : "—"}
                  </td>
                </tr>
              );
            })}
            {packets.length === 0 && (
              <tr>
                <td colSpan={9} className="px-3 py-6 text-center text-gray-600">
                  No packets recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
