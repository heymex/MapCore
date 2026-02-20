// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

import { Routes, Route, NavLink } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { Packets } from "./pages/Packets";
import { Nodes } from "./pages/Nodes";
import { MapPage } from "./pages/Map";
import { BotRules } from "./pages/BotRules";

/** Navigation link style helper. */
function navClass({ isActive }: { isActive: boolean }): string {
  return `px-3 py-2 rounded text-sm font-medium transition-colors ${
    isActive
      ? "bg-indigo-600 text-white"
      : "text-gray-400 hover:text-white hover:bg-gray-800"
  }`;
}

/** Root application shell with top-level routing. */
export default function App() {
  return (
    <div className="flex flex-col h-screen bg-gray-950 text-white">
      {/* Navbar */}
      <nav className="flex items-center gap-2 px-4 py-2 bg-gray-900 border-b border-gray-800">
        <span className="text-lg font-bold text-indigo-400 mr-4">
          MeshCore Monitor
        </span>
        <NavLink to="/" className={navClass} end>
          Dashboard
        </NavLink>
        <NavLink to="/map" className={navClass}>
          Map
        </NavLink>
        <NavLink to="/nodes" className={navClass}>
          Nodes
        </NavLink>
        <NavLink to="/packets" className={navClass}>
          Packets
        </NavLink>
        <NavLink to="/bot" className={navClass}>
          Bot Rules
        </NavLink>
      </nav>

      {/* Page content */}
      <div className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/nodes" element={<Nodes />} />
          <Route path="/packets" element={<Packets />} />
          <Route path="/bot" element={<BotRules />} />
        </Routes>
      </div>
    </div>
  );
}
