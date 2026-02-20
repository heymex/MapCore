// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Tests for the useNodes hook — node state management.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useNodes } from "../useNodes";
import type { Node } from "../../api/types";

// Mock the API client so the hook doesn't make real HTTP requests.
vi.mock("../../api/client", () => ({
  fetchNodes: vi.fn().mockResolvedValue([
    {
      id: 1,
      node_hash: "FA",
      name: "Alpha",
      node_type: "repeater",
      lat: 44.0,
      lon: -92.0,
      last_rssi: -85,
      last_snr: 7.5,
      first_seen: "2026-01-01T00:00:00",
      last_seen: "2026-02-20T12:00:00",
      is_local: true,
    },
  ] satisfies Node[]),
}));

describe("useNodes", () => {
  it("loads nodes from the API on mount", async () => {
    const { result } = renderHook(() => useNodes());

    // Wait for the async fetchNodes to resolve
    await vi.waitFor(() => {
      expect(result.current.nodes).toHaveLength(1);
    });

    expect(result.current.nodes[0].node_hash).toBe("FA");
  });

  it("updateNode merges into existing nodes", async () => {
    const { result } = renderHook(() => useNodes());

    await vi.waitFor(() => {
      expect(result.current.nodes).toHaveLength(1);
    });

    act(() => {
      result.current.updateNode({ node_hash: "FA", name: "Alpha-Updated" });
    });

    expect(result.current.nodes[0].name).toBe("Alpha-Updated");
  });

  it("updateNode inserts a new node if hash not found", async () => {
    const { result } = renderHook(() => useNodes());

    await vi.waitFor(() => {
      expect(result.current.nodes).toHaveLength(1);
    });

    act(() => {
      result.current.updateNode({
        node_hash: "BB",
        name: "Bravo",
      } as Node);
    });

    expect(result.current.nodes).toHaveLength(2);
    expect(result.current.nodes[1].node_hash).toBe("BB");
  });

  it("addPacketPath keeps recent paths capped at 20", async () => {
    const { result } = renderHook(() => useNodes());

    act(() => {
      for (let i = 0; i < 25; i++) {
        result.current.addPacketPath([`${i}`]);
      }
    });

    expect(result.current.recentPaths).toHaveLength(20);
    // Most recent should be first
    expect(result.current.recentPaths[0]).toEqual(["24"]);
  });
});
