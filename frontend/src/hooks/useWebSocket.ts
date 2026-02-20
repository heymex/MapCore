// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * React hook that maintains a WebSocket connection with automatic
 * reconnect and JSON message parsing.
 */

import { useEffect, useRef, useCallback } from "react";
import type { WsEvent } from "../api/types";

/** Callback signature for incoming WebSocket events. */
export type MessageHandler = (event: WsEvent) => void;

/**
 * Connect to a WebSocket endpoint and invoke `onMessage` for each
 * parsed JSON event.  Automatically reconnects after 3 s on close.
 *
 * @param url - WebSocket URL (e.g. `ws://host/ws`).
 * @param onMessage - Handler invoked with each parsed {@link WsEvent}.
 */
export function useWebSocket(url: string, onMessage: MessageHandler): void {
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const parsed: WsEvent = JSON.parse(event.data);
        onMessage(parsed);
      } catch {
        console.error("WebSocket parse error");
      }
    };

    ws.onclose = () => {
      setTimeout(connect, 3000);
    };

    return () => ws.close();
  }, [url, onMessage]);

  useEffect(() => {
    const cleanup = connect();
    return cleanup;
  }, [connect]);
}
