import { describe, expect, it } from "vitest";

import type { Rol, Sesion } from "../api/types";
import { accionesDeMedicion, puedeAgregarEvidencia, puedeModificar, puedeRetroceder, puedeValidar } from "./acciones";

describe("puedeAgregarEvidencia", () => {
  it("se agrega evidencia antes de validar, no después", () => {
    expect(puedeAgregarEvidencia("borrador", true)).toBe(true);
    expect(puedeAgregarEvidencia("enviada", true)).toBe(true);
    expect(puedeAgregarEvidencia("rechazada", true)).toBe(true);
    expect(puedeAgregarEvidencia("validada", true)).toBe(false);
  });

  it("sin permiso de escritura no se agrega", () => {
    expect(puedeAgregarEvidencia("borrador", false)).toBe(false);
  });
});

describe("puedeRetroceder", () => {
  const admin: Sesion = { authenticated: true, id: 1, es_admin: true, membresias: [] };
  const responsable: Sesion = { authenticated: true, id: 2, es_admin: false, membresias: [] };

  it("solo el administrador retrocede, y no desde identificada", () => {
    expect(puedeRetroceder(admin, "formalizada")).toBe(true);
    expect(puedeRetroceder(admin, "identificada")).toBe(false);
    expect(puedeRetroceder(responsable, "formalizada")).toBe(false);
    expect(puedeRetroceder(null, "formalizada")).toBe(false);
  });
});

describe("accionesDeMedicion", () => {
  it("un responsable puede enviar un borrador, retirar una enviada y reabrir una rechazada", () => {
    expect(accionesDeMedicion("borrador", true)).toEqual(["enviar"]);
    expect(accionesDeMedicion("enviada", true)).toEqual(["retirar"]);
    expect(accionesDeMedicion("rechazada", true)).toEqual(["reabrir"]);
  });

  it("una medición validada ya no tiene acciones", () => {
    expect(accionesDeMedicion("validada", true)).toEqual([]);
  });

  it("sin permiso de escritura no hay acciones", () => {
    expect(accionesDeMedicion("borrador", false)).toEqual([]);
    expect(accionesDeMedicion("enviada", false)).toEqual([]);
  });
});

describe("puedeModificar", () => {
  it("solo se corrige o elimina un borrador", () => {
    expect(puedeModificar("borrador", true)).toBe(true);
    expect(puedeModificar("enviada", true)).toBe(false);
    expect(puedeModificar("rechazada", true)).toBe(false);
    expect(puedeModificar("validada", true)).toBe(false);
  });

  it("sin permiso de escritura no se modifica", () => {
    expect(puedeModificar("borrador", false)).toBe(false);
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
