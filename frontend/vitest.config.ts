// Copyright © 2025-26 l5yth & contributors
// Licensed under BSD 3-Clause License

/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/__tests__/setup.ts"],
    include: ["src/**/__tests__/**/*.test.{ts,tsx}"],
  },
});
