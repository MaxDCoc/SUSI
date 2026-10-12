import { render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";

import Tablero from "./Tablero";

const doble = vi.hoisted(() => ({ ilustrativas: 0 }));

vi.mock("../charts/Chart", () => ({ default: () => null }));

vi.mock("../api/client", () => ({
  mensajeDeError: () => "Error",
  api: (ruta: string) => {
    if (ruta.startsWith("/api/catalogos/")) {
      return Promise.resolve({ regiones: [], facultades: [], ods: [], dimensiones: [] });
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
});

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
