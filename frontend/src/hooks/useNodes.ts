// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * React hook for managing mesh node state, including live updates
 * from the WebSocket feed and packet-path tracking.
 */

import { useState, useEffect, useCallback } from "react";
import type { Node } from "../api/types";
import { fetchNodes } from "../api/client";

/** Return value of the {@link useNodes} hook. */
export interface UseNodesResult {
  /** All known nodes. */
  nodes: Node[];
  /** Merge or insert a node record (from a WS update). */
  updateNode: (node: Partial<Node> & { node_hash: string }) => void;
  /** Record a packet path for map animation (future use). */
  addPacketPath: (path: string[]) => void;
  /** Recent packet paths (capped at 20). */
  recentPaths: string[][];
}

/**
 * Load nodes from the API on mount and expose helpers for live updates.
 *
 * @returns {@link UseNodesResult}
 */
export function useNodes(): UseNodesResult {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [recentPaths, setRecentPaths] = useState<string[][]>([]);

  useEffect(() => {
    fetchNodes(500).then(setNodes).catch(console.error);
  }, []);

  const updateNode = useCallback(
    (incoming: Partial<Node> & { node_hash: string }) => {
      setNodes((prev) => {
        const idx = prev.findIndex((n) => n.node_hash === incoming.node_hash);
        if (idx >= 0) {
          const updated = [...prev];
          updated[idx] = { ...updated[idx], ...incoming };
          return updated;
        }
        return [...prev, incoming as Node];
      });
    },
    []
  );

  const addPacketPath = useCallback((path: string[]) => {
    setRecentPaths((prev) => [path, ...prev].slice(0, 20));
  }, []);

  return { nodes, updateNode, addPacketPath, recentPaths };
}
