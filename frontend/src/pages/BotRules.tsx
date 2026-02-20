// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Bot Rules page — CRUD table for managing automation rules.
 *
 * Supports creating, toggling, and deleting rules.  Each rule defines
 * a trigger condition and an action to execute when matched.
 */

import { useEffect, useState, useCallback } from "react";
import type { BotRule, BotRuleCreate } from "../api/types";
import { fetchBotRules, createBotRule } from "../api/client";
import { BotRuleRow } from "../components/BotRules/BotRuleRow";

/** Default values for the new-rule form. */
const EMPTY_RULE: BotRuleCreate = {
  name: "",
  enabled: true,
  trigger_type: "packet_type",
  trigger_value: "",
  action_type: "log",
  action_config: "{}",
};

/** Bot rules management page. */
export function BotRules() {
  const [rules, setRules] = useState<BotRule[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<BotRuleCreate>({ ...EMPTY_RULE });

  const loadRules = useCallback(() => {
    fetchBotRules().then(setRules).catch(console.error);
  }, []);

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  /** Submit the new-rule form. */
  async function handleCreate() {
    if (!form.name.trim()) return;
    await createBotRule(form);
    setForm({ ...EMPTY_RULE });
    setShowForm(false);
    loadRules();
  }

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Bot Rules</h2>
        <button
          className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 rounded text-sm font-medium"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Cancel" : "+ New Rule"}
        </button>
      </div>

      {/* New rule form */}
      {showForm && (
        <div className="bg-gray-900 border border-gray-700 rounded p-4 mb-4 grid grid-cols-2 gap-3">
          <input
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm"
            placeholder="Rule name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <select
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm"
            value={form.trigger_type}
            onChange={(e) => setForm({ ...form, trigger_type: e.target.value })}
          >
            <option value="packet_type">packet_type</option>
            <option value="keyword">keyword</option>
            <option value="node_seen">node_seen</option>
          </select>
          <input
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm"
            placeholder="Trigger value"
            value={form.trigger_value}
            onChange={(e) => setForm({ ...form, trigger_value: e.target.value })}
          />
          <select
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm"
            value={form.action_type}
            onChange={(e) => setForm({ ...form, action_type: e.target.value })}
          >
            <option value="log">log</option>
            <option value="send_message">send_message</option>
            <option value="webhook">webhook</option>
            <option value="telemetry_request">telemetry_request</option>
          </select>
          <input
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm col-span-2"
            placeholder='Action config (JSON), e.g. {"message":"pong"}'
            value={form.action_config}
            onChange={(e) => setForm({ ...form, action_config: e.target.value })}
          />
          <button
            className="col-span-2 px-3 py-1 bg-green-700 hover:bg-green-600 rounded text-sm font-medium"
            onClick={handleCreate}
          >
            Create Rule
          </button>
        </div>
      )}

      {/* Rules table */}
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-400 border-b border-gray-700 text-xs uppercase">
            <th className="px-3 py-2">Name</th>
            <th className="px-3 py-2">Enabled</th>
            <th className="px-3 py-2">Trigger</th>
            <th className="px-3 py-2">Action</th>
            <th className="px-3 py-2">Last Triggered</th>
            <th className="px-3 py-2">Count</th>
            <th className="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {rules.map((rule) => (
            <BotRuleRow key={rule.id} rule={rule} onUpdate={loadRules} />
          ))}
          {rules.length === 0 && (
            <tr>
              <td colSpan={7} className="px-3 py-6 text-center text-gray-600">
                No rules configured.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
