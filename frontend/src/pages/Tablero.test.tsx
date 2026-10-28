import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";

import Tablero from "./Tablero";

const doble = vi.hoisted(() => ({ ilustrativas: 0, llamadas: [] as string[] }));

vi.mock("../charts/Chart", () => ({ default: () => null }));

vi.mock("../api/client", () => ({
  mensajeDeError: () => "Error",
  api: (ruta: string) => {
    doble.llamadas.push(ruta);
    if (ruta.startsWith("/api/catalogos/")) {
      return Promise.resolve({
        regiones: [
          { id: 1, nombre: "Cuyo" },
          { id: 2, nombre: "NEA" },
        ],
        facultades: [
          { id: 10, nombre: "Mendoza", region_id: 1, es_nivel_central: false },
          { id: 11, nombre: "San Rafael", region_id: 1, es_nivel_central: false },
          { id: 20, nombre: "Resistencia", region_id: 2, es_nivel_central: false },
        ],
        ods: [],
        dimensiones: [],
      });
    }
    const grupos: never[] = [];
    return Promise.resolve({
      total_practicas: 9,
      ilustrativas: doble.ilustrativas,
      kpis: {
        con_responsable: { cantidad: 1, porcentaje: 11.1 },
        con_indicador: { cantidad: 1, porcentaje: 11.1 },
        con_evidencia_validada: { cantidad: 0, porcentaje: 0 },
      },
      cobertura: { facultades_con_practicas: 3, facultades_total: 30, porcentaje: 10 },
      embudo: { identificada: 9, formalizada: 0, medida: 0, optimizada: 0 },
      por_facultad: grupos,
      por_region: grupos,
      por_dimension: grupos,
      por_ods: grupos,
    });
  },
}));

beforeEach(() => {
  doble.ilustrativas = 0;
  doble.llamadas.length = 0;
});

const opciones = (etiqueta: string) => within(screen.getByLabelText(etiqueta)).getAllByRole("option").map((o) => o.textContent);

it("avisa cuántas prácticas del tablero son datos ilustrativos", async () => {
  doble.ilustrativas = 8;
  render(<Tablero />);

  expect(await screen.findByText(/8 de 9 prácticas son datos ilustrativos/)).toBeInTheDocument();
});

it("no muestra el aviso cuando todo fue cargado por las facultades", async () => {
  render(<Tablero />);

  await screen.findByText("Prácticas registradas");

  expect(screen.queryByText(/datos ilustrativos/)).not.toBeInTheDocument();
});

it("sin región elegida, el filtro de facultad ofrece todas", async () => {
  render(<Tablero />);
  await screen.findByText("Prácticas registradas");

  expect(opciones("Facultad")).toEqual(["Todas", "Mendoza", "San Rafael", "Resistencia"]);
});

it("al elegir una región, el filtro de facultad ofrece solo las de esa región", async () => {
  render(<Tablero />);
  await screen.findByText("Prácticas registradas");

  await userEvent.selectOptions(screen.getByLabelText("Región"), "Cuyo");

  expect(opciones("Facultad")).toEqual(["Todas", "Mendoza", "San Rafael"]);
});

it("si la facultad elegida no es de la nueva región, se descarta y no se manda al servidor", async () => {
  render(<Tablero />);
  await screen.findByText("Prácticas registradas");

  await userEvent.selectOptions(screen.getByLabelText("Facultad"), "Resistencia");
  await userEvent.selectOptions(screen.getByLabelText("Región"), "Cuyo");

  expect(screen.getByLabelText("Facultad")).toHaveValue("");
  const ultima = doble.llamadas.filter((r) => r.startsWith("/api/dashboard/resumen/")).at(-1);
  expect(ultima).toContain("region=1");
  expect(ultima).not.toContain("facultad=");
});

it("una facultad de la misma región se conserva", async () => {
  render(<Tablero />);
  await screen.findByText("Prácticas registradas");

  await userEvent.selectOptions(screen.getByLabelText("Facultad"), "Mendoza");
  await userEvent.selectOptions(screen.getByLabelText("Región"), "Cuyo");

  expect(screen.getByLabelText("Facultad")).toHaveValue("10");
});
