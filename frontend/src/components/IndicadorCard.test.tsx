import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";

import type { Indicador } from "../api/types";
import IndicadorCard from "./IndicadorCard";

// Dobles con funciones simples (no vi.fn): en Vitest 4 un vi.fn que devuelve una promesa rechazada falla el test.
const doble = vi.hoisted(() => ({
  llamadas: [] as { ruta: string; opciones?: { method?: string; body?: unknown } }[],
  rechazar: null as null | string,
}));

vi.mock("../api/client", () => ({
  mensajeDeError: (e: unknown) => (e instanceof Error ? e.message : "Error inesperado"),
  api: (ruta: string, opciones?: { method?: string; body?: unknown }) => {
    doble.llamadas.push({ ruta, opciones });
    if (doble.rechazar) return Promise.reject(new Error(doble.rechazar));
    return Promise.resolve({});
  },
}));

beforeEach(() => {
  doble.llamadas.length = 0;
  doble.rechazar = null;
});

function indicador(meta: string | null): Indicador {
  return {
    id: 7,
    practica: 1,
    nombre: "Consumo de agua",
    formula: "m³ facturados en el mes",
    unidad: "m3",
    periodicidad: "mensual",
    tipo: "institucional",
    fuente: "",
    linea_base: null,
    meta,
    tolerancia: null,
    referencia_estandar: "",
  };
}

function renderizar(meta: string | null, puedeEscribir = true) {
  const onCambio = vi.fn();
  render(<IndicadorCard indicador={indicador(meta)} mediciones={[]} puedeEscribir={puedeEscribir} onCambio={onCambio} />);
  return onCambio;
}

const patches = () => doble.llamadas.filter((l) => l.opciones?.method === "PATCH");

it("el responsable define la meta de un indicador que no la tenía", async () => {
  const onCambio = renderizar(null);
  expect(screen.getByText("Sin meta definida.")).toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: "Definir meta" }));
  await userEvent.type(screen.getByLabelText("Meta (m3)"), "100");
  await userEvent.click(screen.getByRole("button", { name: "Guardar meta" }));

  expect(patches()).toHaveLength(1);
  expect(patches()[0].ruta).toBe("/api/indicadores/7/");
  expect(patches()[0].opciones?.body).toEqual({ meta: "100" });
  await waitFor(() => expect(onCambio).toHaveBeenCalledTimes(1));
  expect(screen.queryByLabelText("Meta (m3)")).not.toBeInTheDocument();
});

it("editar una meta existente parte del valor actual y deja quitarla", async () => {
  renderizar("80.0000");
  expect(screen.getByText(/Meta: 80 m3/)).toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: "Editar meta" }));
  const campo = screen.getByLabelText("Meta (m3)");
  expect(campo).toHaveValue(80);

  await userEvent.clear(campo);
  await userEvent.click(screen.getByRole("button", { name: "Guardar meta" }));

  expect(patches()[0].opciones?.body).toEqual({ meta: null });
});

it("cancelar cierra el formulario sin llamar a la API", async () => {
  renderizar("80.0000");

  await userEvent.click(screen.getByRole("button", { name: "Editar meta" }));
  await userEvent.click(screen.getByRole("button", { name: "Cancelar" }));

  expect(patches()).toHaveLength(0);
  expect(screen.getByText(/Meta: 80 m3/)).toBeInTheDocument();
});

it("quien no puede escribir ve la meta pero no el botón, y sin meta no ve nada", () => {
  const { unmount } = render(
    <IndicadorCard indicador={indicador("80.0000")} mediciones={[]} puedeEscribir={false} onCambio={() => {}} />,
  );
  expect(screen.getByText(/Meta: 80 m3/)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /meta/i })).not.toBeInTheDocument();
  unmount();

  render(<IndicadorCard indicador={indicador(null)} mediciones={[]} puedeEscribir={false} onCambio={() => {}} />);
  expect(screen.queryByText("Sin meta definida.")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /meta/i })).not.toBeInTheDocument();
});

it("si el servidor rechaza el cambio, muestra el error y deja el formulario abierto", async () => {
  doble.rechazar = "No tenés permiso para editar este indicador.";
  const onCambio = renderizar(null);

  await userEvent.click(screen.getByRole("button", { name: "Definir meta" }));
  await userEvent.type(screen.getByLabelText("Meta (m3)"), "5");
  await userEvent.click(screen.getByRole("button", { name: "Guardar meta" }));

  expect(await screen.findByRole("alert")).toHaveTextContent("No tenés permiso para editar este indicador.");
  expect(screen.getByLabelText("Meta (m3)")).toBeInTheDocument();
  expect(onCambio).not.toHaveBeenCalled();
});
