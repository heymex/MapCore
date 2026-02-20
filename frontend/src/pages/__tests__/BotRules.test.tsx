// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Tests for the BotRules page.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BotRules } from "../BotRules";
import type { BotRule } from "../../api/types";

vi.mock("../../api/client", () => ({
  fetchBotRules: vi.fn(),
  createBotRule: vi.fn().mockResolvedValue({}),
  updateBotRule: vi.fn().mockResolvedValue({}),
  deleteBotRule: vi.fn().mockResolvedValue({}),
}));

import { fetchBotRules, createBotRule } from "../../api/client";

const mockRules: BotRule[] = [
  {
    id: 1,
    name: "Log ADVERTs",
    enabled: true,
    trigger_type: "packet_type",
    trigger_value: "ADVERT",
    action_type: "log",
    action_config: "{}",
    last_triggered: null,
    trigger_count: 0,
  },
];

describe("BotRules", () => {
  beforeEach(() => {
    vi.mocked(fetchBotRules).mockResolvedValue(mockRules);
  });

  it("renders the page title and new rule button", () => {
    render(<BotRules />);

    expect(screen.getByText("Bot Rules")).toBeInTheDocument();
    expect(screen.getByText("+ New Rule")).toBeInTheDocument();
  });

  it("renders rules from the API", async () => {
    render(<BotRules />);

    await vi.waitFor(() => {
      expect(screen.getByText("Log ADVERTs")).toBeInTheDocument();
    });
  });

  it("shows empty state with no rules", async () => {
    vi.mocked(fetchBotRules).mockResolvedValue([]);

    render(<BotRules />);

    await vi.waitFor(() => {
      expect(screen.getByText("No rules configured.")).toBeInTheDocument();
    });
  });

  it("toggles the new rule form on button click", async () => {
    const user = userEvent.setup();
    render(<BotRules />);

    await user.click(screen.getByText("+ New Rule"));

    expect(screen.getByPlaceholderText("Rule name")).toBeInTheDocument();
    expect(screen.getByText("Create Rule")).toBeInTheDocument();

    // Click cancel
    await user.click(screen.getByText("Cancel"));
    expect(screen.queryByPlaceholderText("Rule name")).not.toBeInTheDocument();
  });

  it("creates a rule via the form", async () => {
    vi.mocked(fetchBotRules)
      .mockResolvedValueOnce(mockRules) // initial load
      .mockResolvedValueOnce(mockRules); // reload after create

    const user = userEvent.setup();
    render(<BotRules />);

    await user.click(screen.getByText("+ New Rule"));

    await user.type(screen.getByPlaceholderText("Rule name"), "My New Rule");
    await user.type(screen.getByPlaceholderText("Trigger value"), "TRACE");
    await user.click(screen.getByText("Create Rule"));

    expect(createBotRule).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "My New Rule",
        trigger_value: "TRACE",
        trigger_type: "packet_type",
        action_type: "log",
      })
    );
  });
});
