// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Full-page map view dedicated to node location visualisation.
 */

import { NodeMap } from "../components/Map/NodeMap";

/** Full-screen map page. */
export function MapPage() {
  return (
    <div className="h-full">
      <NodeMap />
    </div>
  );
}
