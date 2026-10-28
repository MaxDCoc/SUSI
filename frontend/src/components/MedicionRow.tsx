import { useState } from "react";

import { api, mensajeDeError } from "../api/client";
import type { Medicion } from "../api/types";
import { type AccionMedicion, accionesDeMedicion, puedeAgregarEvidencia } from "../lib/acciones";
import { MedicionBadge } from "./Badge";
import EvidenciaForm from "./EvidenciaForm";

interface Props {
  medicion: Medicion;
  puedeEscribir: boolean;
  onCambio: () => void;
}

const ETIQUETA_ACCION: Record<AccionMedicion, string> = {
  enviar: "Enviar a validación",
  reabrir: "Reabrir",
};

export default function MedicionRow({ medicion, puedeEscribir, onCambio }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [agregando, setAgregando] = useState(false);

  async function ejecutar(accion: AccionMedicion) {
    setError(null);
    try {
      await api(`/api/mediciones/${medicion.id}/${accion}/`, { method: "POST" });
      onCambio();
    } catch (e) {
      setError(mensajeDeError(e));
    }
  }

  return (
    <tr>
      <td>{medicion.periodo}</td>
      <td>
        {Number(medicion.valor)} {medicion.unidad}
      </td>
      <td>
        <MedicionBadge estado={medicion.estado} />
        {medicion.comentario_validacion && <div className="nota">{medicion.comentario_validacion}</div>}
        {medicion.validado_por_nombre && <div className="nota">por {medicion.validado_por_nombre}</div>}
      </td>
      <td>
        <ul className="evidencias">
          {medicion.evidencias.map((ev) => (
            <li key={ev.id}>
              {ev.tipo === "enlace" ? (
                <a href={ev.url} target="_blank" rel="noreferrer noopener">
                  {ev.descripcion || ev.url}
                </a>
              ) : (
                <a href={ev.archivo_descarga ?? "#"}>{ev.descripcion || "Archivo adjunto"}</a>
              )}
            </li>
          ))}
        </ul>
        {puedeAgregarEvidencia(medicion.estado, puedeEscribir) &&
          (agregando ? (
            <EvidenciaForm
              medicionId={medicion.id}
              onCreada={() => {
                setAgregando(false);
                onCambio();
              }}
              onCancelar={() => setAgregando(false)}
            />
          ) : (
            <button type="button" className="enlace" onClick={() => setAgregando(true)}>
              Agregar evidencia
            </button>
          ))}
      </td>
      <td>
        {accionesDeMedicion(medicion.estado, puedeEscribir).map((accion) => (
          <button key={accion} type="button" onClick={() => ejecutar(accion)}>
            {ETIQUETA_ACCION[accion]}
          </button>
        ))}
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
      </td>
    </tr>
  );
}
