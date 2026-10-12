import type { EstadoMedicion, Medicion, Rol, Sesion } from "../api/types";

export type AccionMedicion = "enviar" | "reabrir";

export function accionesDeMedicion(estado: EstadoMedicion, puedeEscribir: boolean): AccionMedicion[] {
  if (!puedeEscribir) return [];
  if (estado === "borrador") return ["enviar"];
  if (estado === "rechazada") return ["reabrir"];
  return [];
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
