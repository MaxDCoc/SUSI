import { expect, type Page, test } from "@playwright/test";

const clave = process.env.E2E_PASSWORD ?? "";

async function ingresar(page: Page, usuario: string) {
  await page.goto("/login");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill(clave);
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page.getByRole("heading", { name: "Prácticas sostenibles" })).toBeVisible();
}

// Requiere una base recién sembrada: el test cambia datos (valida una medición y promueve una práctica).
test("el validador valida la medición de Delta y el responsable promueve la práctica a Medida", async ({ page }) => {
  expect(clave, "definí E2E_PASSWORD con la clave de los usuarios de demo").not.toBe("");

  await ingresar(page, "validador.demo");
  await page.getByRole("link", { name: "Validaciones" }).click();
  await expect(page.getByRole("link", { name: /Cálculo de huella de carbono institucional/ })).toBeVisible();
  await page.getByRole("button", { name: "Validar" }).first().click();
  await expect(page.getByText("No hay mediciones pendientes de validación.")).toBeVisible();
  await page.getByRole("button", { name: "Salir" }).click();

  await ingresar(page, "responsable.demo");
  await page.getByRole("link", { name: "Cálculo de huella de carbono institucional (ISO 14064)" }).click();
  await page.getByRole("button", { name: "Promover a Medida" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("medida");

  await page.getByRole("link", { name: "Tablero" }).click();
  await expect(page.getByRole("heading", { name: "Tablero comparable" })).toBeVisible();
});
