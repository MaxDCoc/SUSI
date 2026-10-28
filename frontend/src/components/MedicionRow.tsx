import { type FormEvent, useState } from "react";

import { api, mensajeDeError } from "../api/client";
import type { Medicion } from "../api/types";
import { type AccionMedicion, accionesDeMedicion, puedeAgregarEvidencia, puedeModificar } from "../lib/acciones";
import { MedicionBadge } from "./Badge";
import EvidenciaForm from "./EvidenciaForm";

interface Props {
  medicion: Medicion;
  puedeEscribir: boolean;
  onCambio: () => void;
}

const ETIQUETA_ACCION: Record<AccionMedicion, string> = {
  enviar: "Enviar a validación",
  retirar: "Retirar de validación",
  reabrir: "Reabrir",
};

export default function MedicionRow({ medicion, puedeEscribir, onCambio }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [agregando, setAgregando] = useState(false);
  const [editando, setEditando] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [periodo, setPeriodo] = useState(medicion.periodo);
  const [valor, setValor] = useState("");

  const modificable = puedeModificar(medicion.estado, puedeEscribir);
  // Los campos de edición están en otras celdas de la fila: se asocian al formulario con este id.
  const formulario = `editar-medicion-${medicion.id}`;

  async function ejecutar(accion: AccionMedicion) {
    setError(null);
    try {
      await api(`/api/mediciones/${medicion.id}/${accion}/`, { method: "POST" });
      onCambio();
    } catch (e) {
      setError(mensajeDeError(e));
    }
  }

  function empezarEdicion() {
    setError(null);
    setPeriodo(medicion.periodo);
    setValor(String(Number(medicion.valor)));
    setEditando(true);
  }

  async function guardar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api(`/api/mediciones/${medicion.id}/`, { method: "PATCH", body: { periodo, valor } });
      setEditando(false);
      onCambio();
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  async function eliminar() {
    setError(null);
    try {
      await api(`/api/mediciones/${medicion.id}/`, { method: "DELETE" });
      onCambio();
    } catch (err) {
      setError(mensajeDeError(err));
      setConfirmando(false);
    }
  }

  return (
    <tr>
      <td className="no-corta">
        {editando ? (
          <input type="month" form={formulario} aria-label="Período" value={periodo} onChange={(e) => setPeriodo(e.target.value)} required />
        ) : (
          medicion.periodo
        )}
      </td>
      <td className="no-corta">
        {editando ? (
          <>
            <input type="number" step="any" form={formulario} aria-label="Valor" value={valor} onChange={(e) => setValor(e.target.value)} required />{" "}
            {medicion.unidad}
          </>
        ) : (
          <>
            {Number(medicion.valor)} {medicion.unidad}
          </>
        )}
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
        <div className="acciones">
          {editando ? (
            <form id={formulario} onSubmit={guardar} className="acciones">
              <button type="submit">Guardar cambios</button>
              <button type="button" className="secundario" onClick={() => setEditando(false)}>
                Cancelar
              </button>
            </form>
          ) : confirmando ? (
            <>
              <p className="nota">¿Eliminar esta medición? Se borran también sus evidencias y no se puede deshacer.</p>
              <button type="button" className="peligro firme" onClick={eliminar}>
                Sí, eliminar
              </button>
              <button type="button" className="secundario" onClick={() => setConfirmando(false)}>
                No, conservar
              </button>
            </>
          ) : (
            <>
              {accionesDeMedicion(medicion.estado, puedeEscribir).map((accion) => (
                <button key={accion} type="button" onClick={() => ejecutar(accion)}>
                  {ETIQUETA_ACCION[accion]}
                </button>
              ))}
              {modificable && (
                <>
                  <button type="button" className="secundario" onClick={empezarEdicion}>
                    Editar
                  </button>
                  <button type="button" className="peligro" onClick={() => setConfirmando(true)}>
                    Eliminar
                  </button>
                </>
              )}
            </>
          )}
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
        </div>
      </td>
    </tr>
  );
}
