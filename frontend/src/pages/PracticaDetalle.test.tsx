import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";

import PracticaDetalle from "./PracticaDetalle";

// Dobles con funciones simples (no vi.fn): en Vitest 4 un vi.fn que devuelve una promesa rechazada falla el test.
const doble = vi.hoisted(() => ({
  llamadas: [] as { ruta: string; opciones?: { method?: string; body?: unknown } }[],
  estado: "identificada",
  admin: false,
  liberar: null as null | (() => void),
}));

vi.mock("../api/client", () => ({
  mensajeDeError: (e: unknown) => (e instanceof Error ? e.message : "Error inesperado"),
  api: (ruta: string, opciones?: { method?: string; body?: unknown }) => {
    doble.llamadas.push({ ruta, opciones });
    if (opciones?.method === "POST" && ruta.endsWith("/promover/")) {
      return new Promise((resolver) => {
        doble.liberar = () => resolver({});
      });
    }
    if (opciones?.method === "POST") return Promise.resolve({});
    if (ruta.startsWith("/api/catalogos/")) {
      return Promise.resolve({
        estados: [
          { valor: "identificada", etiqueta: "Identificada" },
          { valor: "formalizada", etiqueta: "Formalizada" },
          { valor: "medida", etiqueta: "Medida" },
          { valor: "optimizada", etiqueta: "Optimizada" },
        ],
        periodicidades: [],
        tipos_indicador: [],
      });
    }
    if (ruta.startsWith("/api/practicas/1/")) {
      return Promise.resolve({
        id: 1,
        facultad: 3,
        facultad_nombre: "Resistencia",
        nombre: "Paneles solares",
        dimension: "ambiental",
        estado: doble.estado,
        proposito: "",
        ods: [],
        responsable: 5,
        responsable_nombre: "ana",
        origen: "cargada",
      });
    }
    return Promise.resolve({ count: 0, next: null, previous: null, results: [] });
  },
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    sesion: { authenticated: true, id: 5, es_admin: doble.admin, membresias: [] },
    tieneRol: () => true,
  }),
}));

beforeEach(() => {
  doble.llamadas.length = 0;
  doble.estado = "identificada";
  doble.admin = false;
  doble.liberar = null;
});

function renderizar() {
  return render(
    <MemoryRouter initialEntries={["/practicas/1"]}>
      <Routes>
        <Route path="/practicas/:id" element={<PracticaDetalle />} />
      </Routes>
    </MemoryRouter>,
  );
}

const promociones = () => doble.llamadas.filter((l) => l.ruta.endsWith("/promover/"));

it("promover manda el estado que ve el usuario y ignora el segundo clic mientras espera", async () => {
  renderizar();
  const boton = await screen.findByRole("button", { name: "Promover a Formalizada" });

  await userEvent.click(boton);
  await userEvent.click(boton);

  expect(promociones()).toHaveLength(1);
  expect(promociones()[0].opciones?.body).toEqual({ desde: "identificada" });
  doble.liberar?.();
  await waitFor(() => expect(boton).toBeEnabled());
});

it("el administrador retrocede una práctica con motivo", async () => {
  doble.admin = true;
  doble.estado = "formalizada";
  renderizar();

  await userEvent.type(await screen.findByLabelText("Motivo del retroceso"), "Error de carga");
  await userEvent.click(screen.getByRole("button", { name: "Retroceder" }));

  const llamada = doble.llamadas.find((l) => l.ruta === "/api/practicas/1/retroceder/");
  expect(llamada?.opciones?.body).toEqual({ motivo: "Error de carga" });
});

it("quien no es administrador, o una práctica identificada, no muestra Retroceder", async () => {
  doble.estado = "formalizada";
  const { unmount } = renderizar();
  await screen.findByRole("button", { name: "Promover a Medida" });
  expect(screen.queryByRole("button", { name: "Retroceder" })).not.toBeInTheDocument();
  unmount();

  doble.admin = true;
  doble.estado = "identificada";
  renderizar();
  await screen.findByRole("button", { name: "Promover a Formalizada" });
  expect(screen.queryByRole("button", { name: "Retroceder" })).not.toBeInTheDocument();
});
