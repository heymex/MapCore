// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/**
 * Nodes page — table view of all observed mesh nodes.
 */

import { NodeList } from "../components/NodeList/NodeList";

/** Node listing page. */
export function Nodes() {
  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Mesh Nodes</h2>
      <NodeList />
    </div>
  );
}
