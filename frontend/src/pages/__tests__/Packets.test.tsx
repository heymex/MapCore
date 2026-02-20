// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Tests for the Packets page.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Packets } from "../Packets";
import type { Packet } from "../../api/types";

vi.mock("../../api/client", () => ({
  fetchPackets: vi.fn(),
}));

import { fetchPackets } from "../../api/client";

const mockPackets: Packet[] = [
  {
    id: 1,
    received_at: "2026-02-20T12:00:00",
    packet_hash: "pkt1",
    packet_type: "ADVERT",
    route_type: "FLOOD",
    path: '["FA","BB"]',
    hop_count: 2,
    rssi: -85,
    snr: 7.5,
    source_hash: "FA",
    dest_hash: null,
    payload_hex: null,
  },
];

describe("Packets", () => {
  beforeEach(() => {
    vi.mocked(fetchPackets).mockResolvedValue(mockPackets);
  });

  it("renders the page title and filter dropdown", () => {
    render(<Packets />);

    expect(screen.getByText("Packet History")).toBeInTheDocument();
    expect(screen.getByDisplayValue("All types")).toBeInTheDocument();
  });

  it("renders packet data from the API", async () => {
    render(<Packets />);

    // Wait for actual row data — "FA → BB" only appears in the packet table,
    // not in the dropdown options.
    await vi.waitFor(() => {
      expect(screen.getByText("FA → BB")).toBeInTheDocument();
    });

    // The packet type badge should also be rendered in a <span>, distinct
    // from the dropdown <option> values.
    expect(screen.getAllByText("ADVERT").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("FLOOD")).toBeInTheDocument();
  });

  it("shows empty state with no packets", async () => {
    vi.mocked(fetchPackets).mockResolvedValue([]);

    render(<Packets />);

    await vi.waitFor(() => {
      expect(screen.getByText("No packets recorded yet.")).toBeInTheDocument();
    });
  });

  it("re-fetches when filter changes", async () => {
    const user = userEvent.setup();
    render(<Packets />);

    const select = screen.getByDisplayValue("All types");
    await user.selectOptions(select, "TXT_MSG");

    expect(fetchPackets).toHaveBeenCalledWith(
      expect.objectContaining({ packet_type: "TXT_MSG" })
    );
  });
});
