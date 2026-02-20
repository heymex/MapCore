// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/** Mesh node as returned by ``GET /api/nodes``. */
export interface Node {
  id: number;
  node_hash: string;
  name: string | null;
  node_type: string | null;
  lat: number | null;
  lon: number | null;
  last_rssi: number | null;
  last_snr: number | null;
  first_seen: string;
  last_seen: string;
  is_local: boolean;
}

/** Received packet as returned by ``GET /api/packets``. */
export interface Packet {
  id: number;
  received_at: string;
  packet_hash: string | null;
  packet_type: string;
  route_type: string;
  path: string | null;
  hop_count: number | null;
  rssi: number | null;
  snr: number | null;
  source_hash: string | null;
  dest_hash: string | null;
  payload_hex: string | null;
}

/** Bot rule as returned by ``GET /api/bot/rules``. */
export interface BotRule {
  id: number;
  name: string;
  enabled: boolean;
  trigger_type: string;
  trigger_value: string;
  action_type: string;
  action_config: string;
  last_triggered: string | null;
  trigger_count: number;
}

/** Payload for creating / updating a bot rule. */
export interface BotRuleCreate {
  name: string;
  enabled: boolean;
  trigger_type: string;
  trigger_value: string;
  action_type: string;
  action_config: string;
}

/** WebSocket event envelope. */
export interface WsEvent<T = unknown> {
  type: string;
  data: T;
}
