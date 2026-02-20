// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Tests for the BotRuleRow component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BotRuleRow } from "../BotRules/BotRuleRow";
import type { BotRule } from "../../api/types";

vi.mock("../../api/client", () => ({
  updateBotRule: vi.fn().mockResolvedValue({}),
  deleteBotRule: vi.fn().mockResolvedValue({}),
}));

import { updateBotRule, deleteBotRule } from "../../api/client";

const sampleRule: BotRule = {
  id: 1,
  name: "Test Rule",
  enabled: true,
  trigger_type: "packet_type",
  trigger_value: "ADVERT",
  action_type: "log",
  action_config: "{}",
  last_triggered: "2026-02-20T10:00:00",
  trigger_count: 5,
};

describe("BotRuleRow", () => {
  const onUpdate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  /** Helper: render the row inside a table. */
  function renderRow(rule: BotRule = sampleRule) {
    return render(
      <table>
        <tbody>
          <BotRuleRow rule={rule} onUpdate={onUpdate} />
        </tbody>
      </table>
    );
  }

  it("displays rule name, trigger, and action", () => {
    renderRow();

    expect(screen.getByText("Test Rule")).toBeInTheDocument();
    expect(screen.getByText("packet_type: ADVERT")).toBeInTheDocument();
    expect(screen.getByText("log")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("shows ON when enabled", () => {
    renderRow();
    expect(screen.getByText("ON")).toBeInTheDocument();
  });

  it("shows OFF when disabled", () => {
    renderRow({ ...sampleRule, enabled: false });
    expect(screen.getByText("OFF")).toBeInTheDocument();
  });

  it("calls updateBotRule and onUpdate when toggled", async () => {
    const user = userEvent.setup();
    renderRow();

    await user.click(screen.getByText("ON"));

    expect(updateBotRule).toHaveBeenCalledWith(1, expect.objectContaining({ enabled: false }));
    expect(onUpdate).toHaveBeenCalled();
  });

  it("calls deleteBotRule and onUpdate when deleted", async () => {
    const user = userEvent.setup();
    renderRow();

    await user.click(screen.getByText("Delete"));

    expect(deleteBotRule).toHaveBeenCalledWith(1);
    expect(onUpdate).toHaveBeenCalled();
  });
});
