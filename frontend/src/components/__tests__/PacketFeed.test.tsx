// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Tests for the PacketFeed component.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { PacketFeed } from "../PacketFeed/PacketFeed";

// Mock the WebSocket hook so no real connection is attempted.
vi.mock("../../hooks/useWebSocket", () => ({
  useWebSocket: vi.fn(),
}));

describe("PacketFeed", () => {
  it("renders the empty state message", () => {
    render(<PacketFeed />);

    expect(screen.getByText("Live Packet Feed")).toBeInTheDocument();
    expect(screen.getByText("Waiting for packets…")).toBeInTheDocument();
  });
});
