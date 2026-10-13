import type { Estado, EstadoMedicion } from "../api/types";

export function EstadoBadge({ estado }: { estado: Estado }) {
  return (
    <span className={`badge estado-${estado}`}>
      <span className="nivel" aria-hidden="true">
        <i />
        <i />
        <i />
        <i />
      </span>
      {estado}
    </span>
  );
}

export function MedicionBadge({ estado }: { estado: EstadoMedicion }) {
  return <span className={`badge medicion-${estado}`}>{estado}</span>;
}

export function IlustrativoBadge() {
  return (
    <span className="badge ilustrativo" title="Dato de ejemplo: no fue cargado por la facultad">
      Datos ilustrativos
    </span>
  );
}
