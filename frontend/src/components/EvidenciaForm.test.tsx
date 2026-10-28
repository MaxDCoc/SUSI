import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";

import EvidenciaForm from "./EvidenciaForm";

// Dobles con funciones simples (no vi.fn): en Vitest 4 un vi.fn que devuelve una promesa rechazada falla el test.
const doble = vi.hoisted(() => ({
  llamadas: [] as { ruta: string; opciones?: { method?: string; body?: unknown } }[],
  liberar: null as null | (() => void),
  rechazar: null as null | string,
}));

vi.mock("../api/client", () => ({
  mensajeDeError: (e: unknown) => (e instanceof Error ? e.message : "Error inesperado"),
  api: (ruta: string, opciones?: { method?: string; body?: unknown }) => {
    doble.llamadas.push({ ruta, opciones });
    if (doble.rechazar) return Promise.reject(new Error(doble.rechazar));
    return new Promise((resolver) => {
      doble.liberar = () => resolver({});
    });
  },
}));

beforeEach(() => {
  doble.llamadas.length = 0;
  doble.liberar = null;
  doble.rechazar = null;
});

const MB = 1024 * 1024;
const archivoDe = (bytes: number) => new File([new Uint8Array(bytes)], "informe.pdf", { type: "application/pdf" });

function renderizar() {
  const onCreada = vi.fn();
  const onCancelar = vi.fn();
  render(<EvidenciaForm medicionId={7} onCreada={onCreada} onCancelar={onCancelar} />);
  return { onCreada, onCancelar };
}

// jsdom no da por cargado el archivo que pone userEvent.upload en un campo "required" y bloquea el envío con un clic;
// en un navegador real sí se envía. Por eso se dispara el envío del formulario directamente.
function enviarFormulario() {
  fireEvent.submit(screen.getByRole("button", { name: "Subir evidencia" }).closest("form") as HTMLFormElement);
}

async function elegirArchivo(bytes: number) {
  await userEvent.selectOptions(screen.getByLabelText("Tipo de evidencia"), "archivo");
  await userEvent.upload(document.querySelector('input[type="file"]') as HTMLInputElement, archivoDe(bytes));
}

it("Cancelar cierra el formulario sin subir nada", async () => {
  const { onCancelar, onCreada } = renderizar();

  await userEvent.click(screen.getByRole("button", { name: "Cancelar" }));

  expect(onCancelar).toHaveBeenCalledTimes(1);
  expect(onCreada).not.toHaveBeenCalled();
  expect(doble.llamadas).toHaveLength(0);
});

it("antes de elegir un archivo ya avisa qué se acepta; con un enlace no hace falta", async () => {
  renderizar();
  expect(screen.queryByText(/hasta 2 MB/)).not.toBeInTheDocument();

  await userEvent.selectOptions(screen.getByLabelText("Tipo de evidencia"), "archivo");

  expect(screen.getByText("Solo se aceptan archivos PDF, PNG o JPG de hasta 2 MB.")).toBeInTheDocument();
});

it("un archivo de más de 2 MB se rechaza al elegirlo: avisa de inmediato y no se sube", async () => {
  renderizar();

  await elegirArchivo(3 * MB);

  expect(await screen.findByRole("alert")).toHaveTextContent("El archivo supera el máximo de 2 MB (pesa 3 MB).");
  expect(screen.getByRole("button", { name: "Subir evidencia" })).toBeDisabled();
  expect(doble.llamadas).toHaveLength(0);
});

it("elegir después un archivo que sí entra borra el aviso y permite subirlo", async () => {
  renderizar();
  await elegirArchivo(3 * MB);
  await screen.findByRole("alert");

  await userEvent.upload(document.querySelector('input[type="file"]') as HTMLInputElement, archivoDe(1 * MB));

  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Subir evidencia" })).toBeEnabled();
});

it("mientras sube muestra 'Subiendo…' y no deja enviar dos veces ni cancelar", async () => {
  const { onCreada } = renderizar();
  await elegirArchivo(1 * MB);

  enviarFormulario();

  const boton = await screen.findByRole("button", { name: "Subiendo…" });
  expect(boton).toBeDisabled();
  expect(screen.getByRole("button", { name: "Cancelar" })).toBeDisabled();
  expect(doble.llamadas).toHaveLength(1);
  doble.liberar?.();
  await waitFor(() => expect(onCreada).toHaveBeenCalledTimes(1));
});

it("si el servidor rechaza la subida, muestra su mensaje y deja reintentar", async () => {
  doble.rechazar = "archivo: El contenido del archivo no coincide con su extensión.";
  renderizar();
  await elegirArchivo(1 * MB);

  enviarFormulario();

  expect(await screen.findByRole("alert")).toHaveTextContent("no coincide con su extensión");
  expect(screen.getByRole("button", { name: "Subir evidencia" })).toBeEnabled();
});
