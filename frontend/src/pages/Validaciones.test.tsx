import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";

import Validaciones from "./Validaciones";

function medicion(id: number, origen: "cargada" | "ilustrativa") {
  return {
    id,
    indicador: id,
    indicador_nombre: "Huella de carbono",
    unidad: "tCO2e",
    practica_id: id,
    practica_nombre: `Práctica ${id}`,
    practica_origen: origen,
    facultad_id: 3,
    facultad_nombre: "Resistencia",
    periodo: "2026-01",
    valor: "410",
    estado: "enviada",
    cargado_por: 9,
    cargado_por_nombre: "ana",
    evidencias: [],
  };
}

vi.mock("../api/client", () => ({
  mensajeDeError: () => "Error",
  api: () =>
    Promise.resolve({
      count: 2,
      next: null,
      previous: null,
      results: [medicion(1, "ilustrativa"), medicion(2, "cargada")],
    }),
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({ sesion: { authenticated: true, id: 7, membresias: [] }, tieneRol: () => true }),
}));

it("rotula como datos ilustrativos solo las mediciones de prácticas de ejemplo", async () => {
  render(
    <MemoryRouter>
      <Validaciones />
    </MemoryRouter>,
  );

  await screen.findByText("Práctica 2");

  expect(screen.getAllByText("Datos ilustrativos")).toHaveLength(1);
});
