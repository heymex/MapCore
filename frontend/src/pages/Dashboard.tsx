// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Dashboard page — primary landing view with stats bar, map, and
 * live packet feed side-by-side.
 */

import { NodeMap } from "../components/Map/NodeMap";
import { PacketFeed } from "../components/PacketFeed/PacketFeed";
import { StatsBar } from "../components/StatsBar";

/** Dashboard page combining map and live feed. */
export function Dashboard() {
  return (
    <div className="flex flex-col h-full">
      <StatsBar />
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1">
          <NodeMap />
        </div>
        <div className="w-96 border-l border-gray-800">
          <PacketFeed />
        </div>
      </div>
    </div>
  );
}
