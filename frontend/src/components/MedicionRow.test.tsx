import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";

import type { EstadoMedicion, Medicion } from "../api/types";
import MedicionRow from "./MedicionRow";

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

function medicion(estado: EstadoMedicion): Medicion {
  return {
    id: 5,
    indicador: 1,
    indicador_nombre: "Consumo de agua",
    unidad: "m3",
    practica_id: 1,
    practica_nombre: "PRUEBA",
    practica_origen: "cargada",
    facultad_id: 3,
    facultad_nombre: "Mendoza",
    periodo: "2026-09",
    valor: "120.0000",
    estado,
    cargado_por: 9,
    cargado_por_nombre: "ana",
    validado_por: null,
    validado_por_nombre: null,
    validado_en: null,
    comentario_validacion: "",
    evidencias: [],
    n_evidencias: 0,
  };
}

function renderizar(estado: EstadoMedicion, puedeEscribir = true) {
  const onCambio = vi.fn();
  render(
    <table>
      <tbody>
        <MedicionRow medicion={medicion(estado)} puedeEscribir={puedeEscribir} onCambio={onCambio} />
      </tbody>
    </table>,
  );
  return onCambio;
}

const boton = (nombre: string) => screen.getByRole("button", { name: nombre });
const hayBoton = (nombre: string) => screen.queryByRole("button", { name: nombre }) !== null;

it("un borrador se puede enviar, editar y eliminar", () => {
  renderizar("borrador");

  expect(hayBoton("Enviar a validación") && hayBoton("Editar") && hayBoton("Eliminar")).toBe(true);
});

it("una medición enviada se puede retirar, pero no editar ni eliminar", async () => {
  const onCambio = renderizar("enviada");

  expect(hayBoton("Editar") || hayBoton("Eliminar")).toBe(false);
  await userEvent.click(boton("Retirar de validación"));

  expect(doble.llamadas).toEqual([{ ruta: "/api/mediciones/5/retirar/", opciones: { method: "POST" } }]);
  await waitFor(() => expect(onCambio).toHaveBeenCalledTimes(1));
});

it("una rechazada solo se reabre y una validada no tiene acciones", () => {
  const { unmount } = render(
    <table>
      <tbody>
        <MedicionRow medicion={medicion("rechazada")} puedeEscribir onCambio={() => {}} />
      </tbody>
    </table>,
  );
  expect(hayBoton("Reabrir")).toBe(true);
  expect(hayBoton("Editar") || hayBoton("Eliminar") || hayBoton("Retirar de validación")).toBe(false);
  unmount();

  renderizar("validada");
  expect(screen.queryAllByRole("button", { name: /Enviar|Retirar|Reabrir|Editar|Eliminar/ })).toHaveLength(0);
});

it("sin permiso de escritura no hay botones", () => {
  renderizar("borrador", false);

  expect(screen.queryAllByRole("button")).toHaveLength(0);
});

it("editar parte de los valores actuales, manda los cambios y avisa", async () => {
  const onCambio = renderizar("borrador");

  await userEvent.click(boton("Editar"));
  expect(screen.getByLabelText("Período")).toHaveValue("2026-09");
  const campoValor = screen.getByLabelText("Valor");
  expect(campoValor).toHaveValue(120);
  await userEvent.clear(campoValor);
  await userEvent.type(campoValor, "135");
  await userEvent.click(boton("Guardar cambios"));

  expect(doble.llamadas).toEqual([
    { ruta: "/api/mediciones/5/", opciones: { method: "PATCH", body: { periodo: "2026-09", valor: "135" } } },
  ]);
  await waitFor(() => expect(onCambio).toHaveBeenCalledTimes(1));
});

it("cancelar la edición vuelve a la fila sin llamar a la API", async () => {
  renderizar("borrador");

  await userEvent.click(boton("Editar"));
  await userEvent.click(boton("Cancelar"));

  expect(doble.llamadas).toHaveLength(0);
  expect(hayBoton("Editar")).toBe(true);
});

it("eliminar pide confirmación y 'No, conservar' no borra nada", async () => {
  renderizar("borrador");

  await userEvent.click(boton("Eliminar"));
  expect(screen.getByText(/¿Eliminar esta medición\?/)).toBeInTheDocument();
  await userEvent.click(boton("No, conservar"));

  expect(doble.llamadas).toHaveLength(0);
  expect(hayBoton("Eliminar")).toBe(true);
});

it("al confirmar se elimina la medición", async () => {
  const onCambio = renderizar("borrador");

  await userEvent.click(boton("Eliminar"));
  await userEvent.click(boton("Sí, eliminar"));

  expect(doble.llamadas).toEqual([{ ruta: "/api/mediciones/5/", opciones: { method: "DELETE" } }]);
  await waitFor(() => expect(onCambio).toHaveBeenCalledTimes(1));
});

it("si el servidor rechaza el borrado muestra el motivo y vuelve a los botones", async () => {
  doble.rechazar = "Solo se pueden eliminar mediciones en borrador.";
  const onCambio = renderizar("borrador");

  await userEvent.click(boton("Eliminar"));
  await userEvent.click(boton("Sí, eliminar"));

  expect(await screen.findByRole("alert")).toHaveTextContent("Solo se pueden eliminar mediciones en borrador.");
  expect(onCambio).not.toHaveBeenCalled();
  expect(hayBoton("Eliminar")).toBe(true);
});
