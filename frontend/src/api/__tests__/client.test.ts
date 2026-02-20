// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Tests for the typed API client functions.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  fetchNodes,
  fetchNode,
  fetchPackets,
  fetchBotRules,
  createBotRule,
  updateBotRule,
  deleteBotRule,
} from "../client";

const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
});

describe("fetchNodes", () => {
  it("calls GET /api/nodes with default limit", async () => {
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve([{ node_hash: "FA", name: "TestNode" }]),
    });

    const nodes = await fetchNodes();

    expect(mockFetch).toHaveBeenCalledWith("/api/nodes?limit=100");
    expect(nodes).toHaveLength(1);
    expect(nodes[0].node_hash).toBe("FA");
  });

  it("passes a custom limit", async () => {
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve([]),
    });

    await fetchNodes(50);

    expect(mockFetch).toHaveBeenCalledWith("/api/nodes?limit=50");
  });
});

describe("fetchNode", () => {
  it("calls GET /api/nodes/:hash", async () => {
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve({ node_hash: "AB" }),
    });

    const node = await fetchNode("AB");

    expect(mockFetch).toHaveBeenCalledWith("/api/nodes/AB");
    expect(node.node_hash).toBe("AB");
  });
});

describe("fetchPackets", () => {
  it("calls GET /api/packets with no filters", async () => {
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve([]),
    });

    await fetchPackets();

    expect(mockFetch).toHaveBeenCalledWith("/api/packets?");
  });

  it("applies packet_type and source_hash filters", async () => {
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve([]),
    });

    await fetchPackets({
      limit: 10,
      packet_type: "ADVERT",
      source_hash: "FA",
    });

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("limit=10");
    expect(url).toContain("packet_type=ADVERT");
    expect(url).toContain("source_hash=FA");
  });
});

describe("fetchBotRules", () => {
  it("calls GET /api/bot/rules", async () => {
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve([{ id: 1, name: "Test" }]),
    });

    const rules = await fetchBotRules();

    expect(mockFetch).toHaveBeenCalledWith("/api/bot/rules");
    expect(rules).toHaveLength(1);
  });
});

describe("createBotRule", () => {
  it("sends POST with JSON body", async () => {
    const newRule = {
      name: "New Rule",
      enabled: true,
      trigger_type: "packet_type",
      trigger_value: "ADVERT",
      action_type: "log",
      action_config: "{}",
    };

    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve({ id: 1, ...newRule }),
    });

    const result = await createBotRule(newRule);

    expect(mockFetch).toHaveBeenCalledWith("/api/bot/rules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newRule),
    });
    expect(result.id).toBe(1);
  });
});

describe("updateBotRule", () => {
  it("sends PUT to /api/bot/rules/:id", async () => {
    const updated = {
      name: "Updated",
      enabled: false,
      trigger_type: "keyword",
      trigger_value: "ping",
      action_type: "send_message",
      action_config: '{"message":"pong"}',
    };

    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve({ id: 5, ...updated }),
    });

    await updateBotRule(5, updated);

    expect(mockFetch).toHaveBeenCalledWith("/api/bot/rules/5", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updated),
    });
  });
});

describe("deleteBotRule", () => {
  it("sends DELETE to /api/bot/rules/:id", async () => {
    mockFetch.mockResolvedValueOnce({});

    await deleteBotRule(3);

    expect(mockFetch).toHaveBeenCalledWith("/api/bot/rules/3", {
      method: "DELETE",
    });
  });
});
