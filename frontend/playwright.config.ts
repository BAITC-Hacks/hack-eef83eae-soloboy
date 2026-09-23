import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";
const localPython =
  process.platform === "win32"
    ? "../.venv/Scripts/python.exe"
    : "../.venv/bin/python";
const python = existsSync(localPython) ? localPython : "python";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8001",
    viewport: { width: 1440, height: 1050 },
    screenshot: "only-on-failure",
  },
  reporter: "list",
  webServer: {
    command: `"${python}" ../scripts/e2e_server.py`,
    url: "http://127.0.0.1:8001/health",
    reuseExistingServer: false,
    timeout: 30000,
  },
});
