import { type FormEvent, useState } from "react";

import { api, mensajeDeError } from "../api/client";
import type { Indicador, Medicion } from "../api/types";
import MedicionRow from "./MedicionRow";

interface Props {
  indicador: Indicador;
  mediciones: Medicion[];
  puedeEscribir: boolean;
  onCambio: () => void;
}

export default function IndicadorCard({ indicador, mediciones, puedeEscribir, onCambio }: Props) {
  const [periodo, setPeriodo] = useState("");
  const [valor, setValor] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [editandoMeta, setEditandoMeta] = useState(false);
  const [meta, setMeta] = useState("");

  function empezarEdicionMeta() {
    setError(null);
    setMeta(indicador.meta === null ? "" : String(Number(indicador.meta)));
    setEditandoMeta(true);
  }

  async function guardarMeta(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api(`/api/indicadores/${indicador.id}/`, { method: "PATCH", body: { meta: meta === "" ? null : meta } });
      setEditandoMeta(false);
      onCambio();
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  async function cargar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api("/api/mediciones/", { method: "POST", body: { indicador: indicador.id, periodo, valor } });
      setPeriodo("");
      setValor("");
      onCambio();
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  return (
    <article className="tarjeta">
      <h3>
        {indicador.nombre} <small>({indicador.unidad}, {indicador.periodicidad})</small>
      </h3>
      <p className="nota">{indicador.formula}</p>
      {editandoMeta ? (
        <form onSubmit={guardarMeta} className="fila">
          <label>
            Meta ({indicador.unidad})
            <input type="number" step="any" value={meta} onChange={(e) => setMeta(e.target.value)} />
          </label>
          <button type="submit">Guardar meta</button>
          <button type="button" className="secundario" onClick={() => setEditandoMeta(false)}>
            Cancelar
          </button>
        </form>
      ) : (
        (indicador.meta !== null || puedeEscribir) && (
          <p>
            {indicador.meta !== null ? `Meta: ${Number(indicador.meta)} ${indicador.unidad}` : "Sin meta definida."}{" "}
            {puedeEscribir && (
              <button type="button" className="enlace" onClick={empezarEdicionMeta}>
                {indicador.meta !== null ? "Editar meta" : "Definir meta"}
              </button>
            )}
          </p>
        )
      )}
      {mediciones.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Período</th>
              <th>Valor</th>
              <th>Estado</th>
              <th>Evidencias</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {mediciones.map((m) => (
              <MedicionRow key={m.id} medicion={m} puedeEscribir={puedeEscribir} onCambio={onCambio} />
            ))}
          </tbody>
        </table>
      )}
      {puedeEscribir && (
        <form onSubmit={cargar} className="fila" style={{ marginTop: "0.75rem" }}>
          <label>
            Período
            <input type="month" value={periodo} onChange={(e) => setPeriodo(e.target.value)} required />
          </label>
          <label>
            Valor ({indicador.unidad})
            <input type="number" step="any" value={valor} onChange={(e) => setValor(e.target.value)} required />
          </label>
          <button type="submit">Cargar medición</button>
        </form>
      )}
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </article>
  );
}
