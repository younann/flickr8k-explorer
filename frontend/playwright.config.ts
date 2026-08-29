import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  use: { baseURL: "http://127.0.0.1:5173" },
  projects: [
    { name: "desktop", use: { viewport: { width: 1280, height: 720 } } },
    { name: "mobile", use: { viewport: { width: 375, height: 720 } } },
  ],
  webServer: [
    {
      command: "cd ../backend && FLICKR8K_DATA_DIR=../frontend/e2e/fixtures/data uv run python ../frontend/e2e/fixtures/prepare_dataset.py && FLICKR8K_DATA_DIR=../frontend/e2e/fixtures/data uv run uvicorn app.main:app --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: false,
    },
  ],
});
