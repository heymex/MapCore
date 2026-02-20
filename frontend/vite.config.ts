// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8001",
      "/ingest": "http://localhost:8001",
      "/ws": { target: "ws://localhost:8001", ws: true },
    },
  },
});
