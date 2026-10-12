import { afterEach, describe, expect, it, vi } from "vitest";

import { api, ApiError, getCookie, mensajeDeError } from "./client";

afterEach(() => {
  vi.restoreAllMocks();
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
});

function respuesta(cuerpo: unknown, status = 200) {
  return new Response(JSON.stringify(cuerpo), { status });
}

describe("api", () => {
  it("agrega el token CSRF en los métodos que no son GET", async () => {
    document.cookie = "csrftoken=abc123";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(respuesta({ ok: true }));

    await api("/api/x/", { method: "POST", body: { a: 1 } });

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers["X-CSRFToken"]).toBe("abc123");
    expect(headers["Content-Type"]).toBe("application/json");
    expect(init.body).toBe(JSON.stringify({ a: 1 }));
  });

  it("no agrega CSRF en GET", async () => {
    document.cookie = "csrftoken=abc123";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(respuesta({}));

    await api("/api/x/");

    const headers = (fetchMock.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers["X-CSRFToken"]).toBeUndefined();
  });

  it("envía FormData sin forzar Content-Type", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(respuesta({}));
    const datos = new FormData();
    datos.append("tipo", "enlace");

    await api("/api/x/", { method: "POST", body: datos });

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.body).toBe(datos);
    expect((init.headers as Record<string, string>)["Content-Type"]).toBeUndefined();
  });

  it("lanza ApiError con el status y los datos del servidor", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respuesta({ detail: "Falta responsable" }, 400));

    await expect(api("/api/x/")).rejects.toMatchObject({ status: 400, data: { detail: "Falta responsable" } });
  });

  it("tolera respuestas vacías y no JSON", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(null, { status: 204 }));
    expect(await api("/api/x/", { method: "POST" })).toBeNull();

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response("<h1>Error</h1>", { status: 500 }));
    await expect(api("/api/x/")).rejects.toBeInstanceOf(ApiError);
  });
});

describe("mensajeDeError", () => {
  it("aplana los formatos de error de DRF", () => {
    expect(mensajeDeError(new ApiError(400, { detail: "Falta" }))).toBe("Falta");
    expect(mensajeDeError(new ApiError(400, ["Uno", "Dos"]))).toBe("Uno Dos");
    expect(mensajeDeError(new ApiError(400, { periodo: ["Formato inválido"] }))).toBe("periodo: Formato inválido");
    expect(mensajeDeError(new Error("boom"))).toBe("boom");
  });
});

describe("getCookie", () => {
  it("devuelve null si no existe", () => {
    expect(getCookie("no-existe")).toBeNull();
  });
});
