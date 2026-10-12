import { describe, expect, it } from "vitest";

import type { Rol, Sesion } from "../api/types";
import { accionesDeMedicion, puedeValidar } from "./acciones";

describe("accionesDeMedicion", () => {
  it("un responsable puede enviar un borrador y reabrir una rechazada", () => {
    expect(accionesDeMedicion("borrador", true)).toEqual(["enviar"]);
    expect(accionesDeMedicion("rechazada", true)).toEqual(["reabrir"]);
  });

  it("no hay acciones para estados que ya avanzaron", () => {
    expect(accionesDeMedicion("enviada", true)).toEqual([]);
    expect(accionesDeMedicion("validada", true)).toEqual([]);
  });

  it("sin permiso de escritura no hay acciones", () => {
    expect(accionesDeMedicion("borrador", false)).toEqual([]);
  });
});

describe("puedeValidar", () => {
  const sesion: Sesion = { authenticated: true, id: 7, username: "ana", membresias: [] };
  const medicion = { estado: "enviada" as const, facultad_id: 3, cargado_por: 9 };
  const conRol = (facultad: number, rol: Rol) => facultad === 3 && rol === "validador";

  it("valida una medición enviada de su facultad cargada por otra persona", () => {
    expect(puedeValidar(medicion, sesion, conRol)).toBe(true);
  });

  it("no valida lo que cargó él mismo", () => {
    expect(puedeValidar({ ...medicion, cargado_por: 7 }, sesion, conRol)).toBe(false);
  });

  it("no valida si no tiene el rol en esa facultad o si no está enviada", () => {
    expect(puedeValidar({ ...medicion, facultad_id: 4 }, sesion, conRol)).toBe(false);
    expect(puedeValidar({ ...medicion, estado: "borrador" }, sesion, conRol)).toBe(false);
  });

  it("sin sesión no valida", () => {
    expect(puedeValidar(medicion, null, conRol)).toBe(false);
  });
});
