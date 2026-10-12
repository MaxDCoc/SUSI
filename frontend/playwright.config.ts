import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:8000",
    // Navegador ya instalado en el equipo (Edge viene con Windows), así no hace falta descargar Chromium.
    // En otros entornos: E2E_CHANNEL=chrome (o vacío para usar el Chromium de Playwright).
    channel: process.env.E2E_CHANNEL === undefined ? "msedge" : process.env.E2E_CHANNEL || undefined,
    trace: "retain-on-failure",
  },
});
