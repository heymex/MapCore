// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Single row in the bot rules table with toggle and delete actions.
 */

import type { BotRule, BotRuleCreate } from "../../api/types";
import { updateBotRule, deleteBotRule } from "../../api/client";

/** Props for {@link BotRuleRow}. */
interface Props {
  /** The rule to render. */
  rule: BotRule;
  /** Callback to refresh the rules list after a mutation. */
  onUpdate: () => void;
}

/** Renders a single bot rule as a table row. */
export function BotRuleRow({ rule, onUpdate }: Props) {
  /** Toggle the enabled state. */
  async function handleToggle() {
    const payload: BotRuleCreate = {
      name: rule.name,
      enabled: !rule.enabled,
      trigger_type: rule.trigger_type,
      trigger_value: rule.trigger_value,
      action_type: rule.action_type,
      action_config: rule.action_config,
    };
    await updateBotRule(rule.id, payload);
    onUpdate();
  }

  /** Delete the rule after confirmation. */
  async function handleDelete() {
    await deleteBotRule(rule.id);
    onUpdate();
  }

  return (
    <tr className="border-b border-gray-800 hover:bg-gray-800/50">
      <td className="px-3 py-2">{rule.name}</td>
      <td className="px-3 py-2">
        <button
          onClick={handleToggle}
          className={`px-2 py-0.5 rounded text-xs font-semibold ${
            rule.enabled
              ? "bg-green-800 text-green-200"
              : "bg-gray-700 text-gray-400"
          }`}
        >
          {rule.enabled ? "ON" : "OFF"}
        </button>
      </td>
      <td className="px-3 py-2 text-gray-400">
        {rule.trigger_type}: {rule.trigger_value || "—"}
      </td>
      <td className="px-3 py-2 text-gray-400">{rule.action_type}</td>
      <td className="px-3 py-2 text-gray-500 text-xs">
        {rule.last_triggered
          ? new Date(rule.last_triggered).toLocaleString()
          : "never"}
      </td>
      <td className="px-3 py-2 text-gray-500">{rule.trigger_count}</td>
      <td className="px-3 py-2">
        <button
          onClick={handleDelete}
          className="text-red-500 hover:text-red-300 text-xs"
        >
          Delete
        </button>
      </td>
    </tr>
  );
}
