export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    super(typeof data === "string" ? data : JSON.stringify(data));
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export function getCookie(nombre: string): string | null {
  const par = document.cookie.split("; ").find((c) => c.startsWith(`${nombre}=`));
  return par ? decodeURIComponent(par.slice(nombre.length + 1)) : null;
}

interface Opciones {
  method?: string;
  body?: unknown;
}

export async function api<T>(ruta: string, opciones: Opciones = {}): Promise<T> {
  const method = opciones.method ?? "GET";
  const headers: Record<string, string> = { Accept: "application/json" };
  let body: BodyInit | undefined;
  if (opciones.body instanceof FormData) {
    body = opciones.body;
  } else if (opciones.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opciones.body);
  }
  if (method !== "GET") {
    const token = getCookie("csrftoken");
    if (token) headers["X-CSRFToken"] = token;
  }

  const respuesta = await fetch(ruta, { method, headers, body, credentials: "same-origin" });
  const texto = await respuesta.text();
  let datos: unknown = null;
  if (texto) {
    try {
      datos = JSON.parse(texto);
    } catch {
      datos = texto;
    }
  }
  if (!respuesta.ok) throw new ApiError(respuesta.status, datos);
  return datos as T;
}

export function mensajeDeError(e: unknown): string {
  if (!(e instanceof ApiError)) return e instanceof Error ? e.message : "Error inesperado";
  const d = e.data;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.join(" ");
  if (d && typeof d === "object") {
    const o = d as Record<string, unknown>;
    if (typeof o.detail === "string") return o.detail;
    return Object.entries(o)
      .map(([campo, v]) => `${campo}: ${Array.isArray(v) ? v.join(" ") : String(v)}`)
      .join(" · ");
  }
  return `Error ${e.status}`;
}
