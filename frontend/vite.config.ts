import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { configDefaults } from "vitest/config";

const apiProxyTarget = process.env.FLICKR8K_API_PROXY_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": apiProxyTarget } },
  test: { environment: "jsdom", setupFiles: ["./src/test/setup.ts"], exclude: [...configDefaults.exclude, "e2e/**"] },
});
