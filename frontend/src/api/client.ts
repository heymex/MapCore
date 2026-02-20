// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Typed HTTP client for the MeshCore Monitor REST API.
 *
 * All functions hit the Vite dev-server proxy in development (same
 * origin), or the FastAPI backend directly in production.
 */

import type { BotRule, BotRuleCreate, Node, Packet } from "./types";

const BASE = "";

/**
 * Fetch mesh nodes.
 *
 * @param limit - Maximum number of nodes to return.
 * @returns Array of {@link Node} records.
 */
export async function fetchNodes(limit = 100): Promise<Node[]> {
  const resp = await fetch(`${BASE}/api/nodes?limit=${limit}`);
  return resp.json();
}

/**
 * Fetch a single node by hash.
 *
 * @param nodeHash - 2-char hex prefix.
 * @returns The matching {@link Node}.
 */
export async function fetchNode(nodeHash: string): Promise<Node> {
  const resp = await fetch(`${BASE}/api/nodes/${nodeHash}`);
  return resp.json();
}

/**
 * Fetch received packets.
 *
 * @param params - Optional filter parameters.
 * @returns Array of {@link Packet} records.
 */
export async function fetchPackets(params?: {
  limit?: number;
  packet_type?: string;
  source_hash?: string;
}): Promise<Packet[]> {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.packet_type) query.set("packet_type", params.packet_type);
  if (params?.source_hash) query.set("source_hash", params.source_hash);
  const resp = await fetch(`${BASE}/api/packets?${query}`);
  return resp.json();
}

/**
 * Fetch all bot rules.
 *
 * @returns Array of {@link BotRule} records.
 */
export async function fetchBotRules(): Promise<BotRule[]> {
  const resp = await fetch(`${BASE}/api/bot/rules`);
  return resp.json();
}

/**
 * Create a new bot rule.
 *
 * @param rule - Rule creation payload.
 * @returns The newly created {@link BotRule}.
 */
export async function createBotRule(rule: BotRuleCreate): Promise<BotRule> {
  const resp = await fetch(`${BASE}/api/bot/rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rule),
  });
  return resp.json();
}

/**
 * Update an existing bot rule.
 *
 * @param id - Rule primary key.
 * @param rule - Updated fields.
 * @returns The updated {@link BotRule}.
 */
export async function updateBotRule(
  id: number,
  rule: BotRuleCreate
): Promise<BotRule> {
  const resp = await fetch(`${BASE}/api/bot/rules/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rule),
  });
  return resp.json();
}

/**
 * Delete a bot rule.
 *
 * @param id - Rule primary key.
 */
export async function deleteBotRule(id: number): Promise<void> {
  await fetch(`${BASE}/api/bot/rules/${id}`, { method: "DELETE" });
}
