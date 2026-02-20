// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Tests for the NodeList component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { NodeList } from "../NodeList/NodeList";
import type { Node } from "../../api/types";

vi.mock("../../api/client", () => ({
  fetchNodes: vi.fn(),
}));

import { fetchNodes } from "../../api/client";

const mockNodes: Node[] = [
  {
    id: 1,
    node_hash: "FA",
    name: "Alpha",
    node_type: "repeater",
    lat: 44.0123,
    lon: -92.4567,
    last_rssi: -85,
    last_snr: 7.5,
    first_seen: "2026-01-01T00:00:00",
    last_seen: "2026-02-20T12:00:00",
    is_local: true,
  },
];

describe("NodeList", () => {
  beforeEach(() => {
    vi.mocked(fetchNodes).mockResolvedValue(mockNodes);
  });

  it("renders table headers", () => {
    render(<NodeList />);

    expect(screen.getByText("Hash")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Type")).toBeInTheDocument();
    expect(screen.getByText("RSSI")).toBeInTheDocument();
    expect(screen.getByText("SNR")).toBeInTheDocument();
    expect(screen.getByText("Location")).toBeInTheDocument();
    expect(screen.getByText("Last Seen")).toBeInTheDocument();
  });

  it("renders node data from the API", async () => {
    render(<NodeList />);

    await vi.waitFor(() => {
      expect(screen.getByText("FA")).toBeInTheDocument();
    });
    expect(screen.getByText("Alpha")).toBeInTheDocument();
    expect(screen.getByText("repeater")).toBeInTheDocument();
    expect(screen.getByText("-85 dBm")).toBeInTheDocument();
    expect(screen.getByText("44.0123, -92.4567")).toBeInTheDocument();
  });

  it("shows empty state when no nodes exist", async () => {
    vi.mocked(fetchNodes).mockResolvedValue([]);

    render(<NodeList />);

    await vi.waitFor(() => {
      expect(screen.getByText("No nodes observed yet.")).toBeInTheDocument();
    });
  });
});
