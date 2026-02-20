// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Tabular list of all known mesh nodes with sortable columns.
 */

import { useEffect, useState } from "react";
import type { Node } from "../../api/types";
import { fetchNodes } from "../../api/client";

/** Displays all nodes in a table format. */
export function NodeList() {
  const [nodes, setNodes] = useState<Node[]>([]);

  useEffect(() => {
    fetchNodes(500).then(setNodes).catch(console.error);
  }, []);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead className="text-xs text-gray-400 uppercase border-b border-gray-700">
          <tr>
            <th className="px-3 py-2">Hash</th>
            <th className="px-3 py-2">Name</th>
            <th className="px-3 py-2">Type</th>
            <th className="px-3 py-2">RSSI</th>
            <th className="px-3 py-2">SNR</th>
            <th className="px-3 py-2">Location</th>
            <th className="px-3 py-2">Last Seen</th>
          </tr>
        </thead>
        <tbody>
          {nodes.map((node) => (
            <tr
              key={node.node_hash}
              className="border-b border-gray-800 hover:bg-gray-800/50"
            >
              <td className="px-3 py-2 font-mono text-indigo-400">
                {node.node_hash}
              </td>
              <td className="px-3 py-2">{node.name || "—"}</td>
              <td className="px-3 py-2 text-gray-400">
                {node.node_type || "unknown"}
              </td>
              <td className="px-3 py-2 text-gray-400">
                {node.last_rssi != null ? `${node.last_rssi} dBm` : "—"}
              </td>
              <td className="px-3 py-2 text-gray-400">
                {node.last_snr != null ? node.last_snr : "—"}
              </td>
              <td className="px-3 py-2 text-gray-500 font-mono text-xs">
                {node.lat != null && node.lon != null
                  ? `${node.lat.toFixed(4)}, ${node.lon.toFixed(4)}`
                  : "—"}
              </td>
              <td className="px-3 py-2 text-gray-500 text-xs">
                {new Date(node.last_seen).toLocaleString()}
              </td>
            </tr>
          ))}
          {nodes.length === 0 && (
            <tr>
              <td colSpan={7} className="px-3 py-6 text-center text-gray-600">
                No nodes observed yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
