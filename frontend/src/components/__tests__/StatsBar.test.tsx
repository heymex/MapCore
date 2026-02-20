// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Tests for the StatsBar component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatsBar } from "../StatsBar";
import type { Node, Packet } from "../../api/types";

// Mock the API client.
vi.mock("../../api/client", () => ({
  fetchNodes: vi.fn(),
  fetchPackets: vi.fn(),
}));

import { fetchNodes, fetchPackets } from "../../api/client";

const mockNodes: Node[] = [
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
  {
    id: 2,
    node_hash: "BB",
    name: "Bravo",
    node_type: null,
    lat: null,
    lon: null,
    last_rssi: null,
    last_snr: null,
    first_seen: "2026-02-01T00:00:00",
    last_seen: "2026-02-20T11:00:00",
    is_local: false,
  },
];

const mockPackets: Packet[] = [
  {
    id: 1,
    received_at: "2026-02-20T12:00:00",
    packet_hash: "pkt1",
    packet_type: "ADVERT",
    route_type: "FLOOD",
    path: '["FA"]',
    hop_count: 1,
    rssi: -85,
    snr: 7.5,
    source_hash: "FA",
    dest_hash: null,
    payload_hex: null,
  },
];

beforeEach(() => {
  vi.mocked(fetchNodes).mockResolvedValue(mockNodes);
  vi.mocked(fetchPackets).mockResolvedValue(mockPackets);
});

describe("StatsBar", () => {
  it("renders node count from API", async () => {
    render(<StatsBar />);

    await vi.waitFor(() => {
      expect(screen.getByText("2")).toBeInTheDocument();
    });
    expect(screen.getByText("Nodes")).toBeInTheDocument();
  });

  it("renders count of nodes with location", async () => {
    render(<StatsBar />);

    await vi.waitFor(() => {
      expect(screen.getByText("With Location")).toBeInTheDocument();
      expect(screen.getByText("1")).toBeInTheDocument();
    });
  });

  it("renders the latest packet type", async () => {
    render(<StatsBar />);

    await vi.waitFor(() => {
      expect(screen.getByText("ADVERT")).toBeInTheDocument();
    });
    expect(screen.getByText("Latest Type")).toBeInTheDocument();
  });
});
