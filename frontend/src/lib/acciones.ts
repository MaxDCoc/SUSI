import type { Estado, EstadoMedicion, Medicion, Rol, Sesion } from "../api/types";

export type AccionMedicion = "enviar" | "retirar" | "reabrir";

export function accionesDeMedicion(estado: EstadoMedicion, puedeEscribir: boolean): AccionMedicion[] {
  if (!puedeEscribir) return [];
  if (estado === "borrador") return ["enviar"];
  if (estado === "enviada") return ["retirar"]; // mientras nadie la haya revisado
  if (estado === "rechazada") return ["reabrir"];
  return [];
}

// Un borrador todavía no lo vio nadie: se puede corregir o eliminar. Lo ya enviado se retira primero.
export function puedeModificar(estado: EstadoMedicion, puedeEscribir: boolean): boolean {
  return puedeEscribir && estado === "borrador";
}

// La evidencia va antes de la validación: una vez validada, nadie la revisó.
export function puedeAgregarEvidencia(estado: EstadoMedicion, puedeEscribir: boolean): boolean {
  return puedeEscribir && estado !== "validada";
}

export function puedeRetroceder(sesion: Sesion | null, estado: Estado): boolean {
  return !!sesion?.es_admin && estado !== "identificada";
}

export function puedeValidar(
  medicion: Pick<Medicion, "estado" | "facultad_id" | "cargado_por">,
  sesion: Sesion | null,
  tieneRol: (facultadId: number, rol: Rol) => boolean,
): boolean {
  return (
    medicion.estado === "enviada" &&
    !!sesion &&
    tieneRol(medicion.facultad_id, "validador") &&
    medicion.cargado_por !== sesion.id
  );
}
