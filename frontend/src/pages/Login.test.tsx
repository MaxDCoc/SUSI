import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";

import { ApiError } from "../api/client";
import Login from "./Login";

// Se usa una función simple (no vi.fn): en Vitest 4 un vi.fn que devuelve una promesa rechazada hace
// fallar el test aunque el componente la maneje.
const doble = vi.hoisted(() => ({
  llamadas: [] as [string, string][],
  respuesta: null as null | (() => Promise<void>),
}));
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    login: (usuario: string, clave: string) => {
      doble.llamadas.push([usuario, clave]);
      return doble.respuesta ? doble.respuesta() : Promise.resolve();
    },
  }),
}));

beforeEach(() => {
  doble.llamadas.length = 0;
  doble.respuesta = null;
});

function renderizar() {
  return render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>,
  );
}

it("envía usuario y contraseña", async () => {
  renderizar();

  await userEvent.type(screen.getByLabelText("Usuario"), "ana");
  await userEvent.type(screen.getByLabelText("Contraseña"), "secreta");
  await userEvent.click(screen.getByRole("button", { name: "Ingresar" }));

  expect(doble.llamadas).toEqual([["ana", "secreta"]]);
});

it("muestra el error que devuelve el servidor", async () => {
  doble.respuesta = () => Promise.reject(new ApiError(400, { detail: "Usuario o contraseña incorrectos." }));
  renderizar();

  await userEvent.type(screen.getByLabelText("Usuario"), "ana");
  await userEvent.type(screen.getByLabelText("Contraseña"), "mala");
  await userEvent.click(screen.getByRole("button", { name: "Ingresar" }));

  expect(await screen.findByRole("alert")).toHaveTextContent("Usuario o contraseña incorrectos.");
});
